"""Rotas da API (§5)."""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from typing import Annotated
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse
from sqlmodel import Session

from app.db import get_session, latest_episode
from app.models import Episodio, Noticia
from app.pipeline import run
from app.pipeline.podia_tts import base as tts
from app.schemas import (
    AVISO_IA,
    AVISO_LOCAL,
    EpisodeOut,
    ErrorOut,
    FalaOut,
    FonteOut,
    GeneratingOut,
    HealthOut,
    ThemeOut,
)
from app.settings import get_settings
from app.themes import get_themes

router = APIRouter()
SessionDep = Annotated[Session, Depends(get_session)]
ERRORS = {404: {"model": ErrorOut}, 401: {"model": ErrorOut}, 503: {"model": ErrorOut}}


class ApiError(HTTPException):
    def __init__(self, status: int, code: str, message: str) -> None:
        super().__init__(status_code=status, detail={"erro": code, "mensagem": message})


def local_time(dt: datetime | None) -> datetime | None:
    """Banco guarda UTC; a API responde em ISO 8601 no fuso configurado (TZ)."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(ZoneInfo(get_settings().tz)).replace(microsecond=0)


def _check_theme(theme: str) -> None:
    if theme not in get_themes():
        raise ApiError(404, "tema_inexistente", f"Tema '{theme}' não existe.")


def episode_out(ep: Episodio, noticia: Noticia | None) -> EpisodeOut:
    data = json.loads(ep.dialogo_json or "{}")
    return EpisodeOut(
        id=ep.id or 0,
        tema=ep.tema,
        titulo=ep.titulo,
        gerado_em=local_time(ep.gerado_em),  # type: ignore[arg-type]
        duracao_s=ep.duracao_s,
        audio_url=f"/audio/{ep.audio_arquivo}" if ep.audio_arquivo else None,
        gerador=ep.gerador,
        fonte=FonteOut(
            veiculo=noticia.veiculo if noticia else None,
            titulo_original=noticia.titulo if noticia else "",
            url=noticia.url if noticia else "",
            publicada_em=local_time(noticia.publicada_em) if noticia else None,
        ),
        falas=[FalaOut(**f) for f in data.get("falas", [])],
        aviso=AVISO_LOCAL if ep.gerador == "local" else AVISO_IA,
    )


@router.get("/themes", response_model=list[ThemeOut], tags=["temas"])
def list_themes(session: SessionDep) -> list[ThemeOut]:
    out = []
    for t in get_themes().values():
        ep = latest_episode(session, t.id)
        out.append(
            ThemeOut(
                id=t.id,
                nome=t.nome,
                icone=t.icone,
                cor=t.cor,
                ultimo_episodio_em=local_time(ep.gerado_em) if ep else None,
            )
        )
    return out


@router.get(
    "/episodes/latest",
    response_model=EpisodeOut,
    responses={202: {"model": GeneratingOut}, **ERRORS},
    tags=["episódios"],
)
def get_latest(session: SessionDep, theme: Annotated[str, Query()]) -> EpisodeOut | JSONResponse:
    _check_theme(theme)
    ep = latest_episode(session, theme)
    if ep:
        return episode_out(ep, session.get(Noticia, ep.noticia_id))
    if theme not in run.state.generating:
        # Falhou na última tentativa e não há episódio: devolve 503 uma vez.
        # O "Tentar de novo" do app chama de novo e dispara outra geração.
        error = run.state.last_error.pop(theme, None)
        if error:
            raise ApiError(503, "geracao_falhou", f"Não foi possível gerar o episódio: {error}")
        run.start_in_background(theme)
    return JSONResponse(status_code=202, content=GeneratingOut(tema=theme).model_dump())


@router.get("/episodes/{episode_id}", response_model=EpisodeOut, responses=ERRORS, tags=["episódios"])
def get_episode(session: SessionDep, episode_id: int) -> EpisodeOut:
    ep = session.get(Episodio, episode_id)
    if not ep or ep.status != "pronto":
        raise ApiError(404, "episodio_inexistente", f"Episódio {episode_id} não existe.")
    return episode_out(ep, session.get(Noticia, ep.noticia_id))


@router.get("/audio/{filename}", responses=ERRORS, tags=["áudio"], response_class=FileResponse)
def get_audio(filename: str) -> FileResponse:
    """MP3 do episódio. FileResponse responde a cabeçalhos Range (avançar/voltar no player)."""
    if not re.fullmatch(r"[a-z0-9_-]+\.mp3", filename):
        raise ApiError(404, "audio_inexistente", "Arquivo inválido.")
    path = get_settings().audio_dir / filename
    if not path.is_file():
        raise ApiError(404, "audio_inexistente", "Áudio não encontrado ou expirado.")
    return FileResponse(path, media_type="audio/mpeg")


@router.post(
    "/admin/generate",
    status_code=202,
    response_model=GeneratingOut,
    responses=ERRORS,
    tags=["admin"],
)
def admin_generate(
    theme: Annotated[str, Query()],
    x_admin_key: Annotated[str | None, Header()] = None,
) -> GeneratingOut:
    """Força a geração de um novo episódio (pode reaproveitar a notícia mais recente)."""
    if x_admin_key != get_settings().admin_key:
        raise ApiError(401, "nao_autorizado", "Chave de admin ausente ou errada.")
    _check_theme(theme)
    run.start_in_background(theme, force=True)
    return GeneratingOut(tema=theme)


@router.get("/health", response_model=HealthOut, tags=["status"])
def health() -> HealthOut:
    s = get_settings()
    cycle = run.state.last_cycle
    return HealthOut(
        motor_voz=s.tts_engine,
        motor_voz_carregado=tts.get_engine.cache_info().currsize > 0,
        llm_configurado=bool(s.gemini_api_key or s.groq_api_key or s.ollama_url),
        gerando=sorted(run.state.generating),
        ultimo_ciclo={
            "inicio": local_time(cycle["inicio"]),
            "fim": local_time(cycle["fim"]),
            "resultados": cycle["resultados"],
        }
        if cycle
        else None,
    )
