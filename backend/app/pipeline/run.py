"""Orquestrador: roda o pipeline de um tema, com lock por tema, logs por etapa e gravação no banco."""

from __future__ import annotations

import json
import logging
import threading
import time
from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from sqlmodel import Session, select

from app.db import get_engine, used_urls
from app.models import Episodio, Noticia, utcnow
from app.pipeline import audio, news
from app.pipeline.dialogue.base import generate_dialogue
from app.pipeline.podia_tts import base as tts
from app.pipeline.types import Article
from app.settings import get_settings
from app.themes import Theme, get_theme, get_themes

log = logging.getLogger("podia.pipeline")

# O modelo de voz é um só e não é seguro usar em duas threads ao mesmo tempo.
_TTS_LOCK = threading.Lock()


@dataclass
class GenerationState:
    """Estado em memória: quem está gerando e o último erro de cada tema."""

    locks: dict[str, threading.Lock] = field(default_factory=dict)
    generating: set[str] = field(default_factory=set)
    last_error: dict[str, str] = field(default_factory=dict)
    last_cycle: dict[str, Any] = field(default_factory=dict)
    _mutex: threading.Lock = field(default_factory=threading.Lock)

    def lock_for(self, theme_id: str) -> threading.Lock:
        with self._mutex:
            return self.locks.setdefault(theme_id, threading.Lock())

    def try_mark_generating(self, theme_id: str) -> bool:
        with self._mutex:
            if theme_id in self.generating:
                return False
            self.generating.add(theme_id)
            return True

    def done(self, theme_id: str) -> None:
        with self._mutex:
            self.generating.discard(theme_id)


state = GenerationState()


class StepError(Exception):
    def __init__(self, step: str, exc: Exception) -> None:
        super().__init__(f"{step}: {exc}")
        self.step = step


@contextmanager
def _step(theme_id: str, name: str):
    t0 = time.perf_counter()
    try:
        yield
    except Exception as exc:
        log.error("[%s] etapa=%s falhou em %.1fs: %s", theme_id, name, time.perf_counter() - t0, exc)
        raise StepError(name, exc) from exc
    log.info("[%s] etapa=%s ok em %.1fs", theme_id, name, time.perf_counter() - t0)


def _save_news(session: Session, theme: Theme, article: Article) -> Noticia:
    existing = session.exec(select(Noticia).where(Noticia.url == article.url)).first()
    if existing:
        return existing
    noticia = Noticia(
        tema=theme.id,
        titulo=article.title,
        url=article.url,
        veiculo=article.source,
        publicada_em=article.published.astimezone(UTC),
        texto=article.text,
    )
    session.add(noticia)
    session.commit()
    session.refresh(noticia)
    return noticia


def run_theme(
    theme_id: str,
    force: bool = False,
    find_article: Callable[[Theme, set[str]], Article | None] = news.find_article,
    engine: tts.TTSEngine | None = None,
) -> Episodio | None:
    """Gera um episódio novo para o tema. Sem notícia nova, devolve None (o anterior continua valendo).

    force=True permite reaproveitar uma notícia já usada (gera de novo mesmo sem notícia nova).
    """
    theme = get_theme(theme_id)
    lock = state.lock_for(theme_id)
    if not lock.acquire(blocking=False):
        log.info("[%s] já existe uma geração em andamento", theme_id)
        return None
    t_total = time.perf_counter()
    episodio: Episodio | None = None
    try:
        with Session(get_engine()) as session:
            used = set() if force else used_urls(session, theme_id)
            with _step(theme_id, "noticia"):
                article = find_article(theme, used)
            if article is None:
                log.info("[%s] nenhuma notícia nova; mantém o episódio anterior", theme_id)
                state.last_error.pop(theme_id, None)
                return None
            noticia = _save_news(session, theme, article)

            with _step(theme_id, "dialogo"):
                dialogue = generate_dialogue(theme, article)

            voice = engine or tts.get_engine()
            episodio = Episodio(
                tema=theme_id,
                noticia_id=noticia.id or 0,
                titulo=dialogue.titulo_episodio,
                dialogo_json="{}",
                gerador=dialogue.gerador,
                motor_voz=voice.name,
                status="gerando",
            )
            session.add(episodio)
            session.commit()
            session.refresh(episodio)

            with _step(theme_id, "vozes"), _TTS_LOCK:
                segments = tts.synthesize(dialogue, voice)
            filename = f"{theme_id}_{episodio.id}.mp3"
            with _step(theme_id, "montagem"):
                result = audio.assemble(segments, get_settings().audio_dir / filename)

            episodio.dialogo_json = json.dumps(
                {
                    "falas": [
                        {"voz": f.voz, "texto": f.texto, "inicio_s": s}
                        for f, s in zip(dialogue.falas, result.line_starts, strict=True)
                    ]
                },
                ensure_ascii=False,
            )
            episodio.audio_arquivo = filename
            episodio.duracao_s = round(result.duration_s)
            episodio.status = "pronto"
            episodio.gerado_em = utcnow()
            session.add(episodio)
            session.commit()
            session.refresh(episodio)
            state.last_error.pop(theme_id, None)
            log.info(
                "[%s] episódio %s pronto: %ss de áudio, gerador=%s, total %.0fs",
                theme_id, episodio.id, episodio.duracao_s, episodio.gerador, time.perf_counter() - t_total,
            )  # fmt: skip
            return episodio
    except Exception as exc:
        state.last_error[theme_id] = str(exc)
        if episodio is not None and episodio.id is not None:
            with Session(get_engine()) as session:
                db_ep = session.get(Episodio, episodio.id)
                if db_ep:
                    db_ep.status, db_ep.erro = "erro", str(exc)[:500]
                    session.add(db_ep)
                    session.commit()
        if not isinstance(exc, StepError):
            log.exception("[%s] erro inesperado", theme_id)
        return None
    finally:
        lock.release()


def start_in_background(theme_id: str, force: bool = False) -> bool:
    """Dispara a geração numa thread. False se o tema já está sendo gerado."""
    if not state.try_mark_generating(theme_id):
        return False

    def worker() -> None:
        try:
            run_theme(theme_id, force=force)
        finally:
            state.done(theme_id)

    threading.Thread(target=worker, name=f"gerar-{theme_id}", daemon=True).start()
    return True


def run_all(only_missing: bool = False) -> dict[str, str]:
    """Roda os temas um por vez (sequencial, para não estourar memória nem limite do LLM)."""
    from app.db import latest_episode

    started = datetime.now(UTC)
    results: dict[str, str] = {}
    for theme_id in get_themes():
        if only_missing:
            with Session(get_engine()) as session:
                if latest_episode(session, theme_id):
                    results[theme_id] = "ja_existe"
                    continue
        if not state.try_mark_generating(theme_id):
            results[theme_id] = "ja_gerando"
            continue
        try:
            ep = run_theme(theme_id)
        finally:
            state.done(theme_id)
        if ep:
            results[theme_id] = f"novo:{ep.id}"
        else:
            results[theme_id] = "erro" if theme_id in state.last_error else "sem_noticia_nova"
    state.last_cycle = {
        "inicio": started,
        "fim": datetime.now(UTC),
        "resultados": results,
    }
    log.info("ciclo concluído: %s", results)
    return results
