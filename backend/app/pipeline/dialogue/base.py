"""Interface dos provedores de diálogo, validação e cadeia de tentativas (§4.4)."""

from __future__ import annotations

import json
import logging
import re
import time
from collections.abc import Callable
from typing import Protocol

from pydantic import ValidationError

from app.pipeline.types import Article, Dialogue
from app.settings import get_settings
from app.themes import Theme

log = logging.getLogger(__name__)

MIN_LINES, MAX_LINES = 8, 12
MIN_WORDS, MAX_WORDS = 260, 330
# Se todas as tentativas falharem SÓ pelo tamanho, aceita a mais longa a partir deste mínimo
# (um diálogo de IA de ~240 palavras é bem melhor que o gerador local).
TOLERATED_MIN_WORDS = 220
MAX_TITLE = 90
MAX_INPUT_WORDS = 1500
EXTRA_ATTEMPTS = 2

# Palavras comuns que só existem com acento: se aparecem sem, o modelo "tirou os acentos".
UNACCENTED = {
    "nao", "voce", "entao", "materia", "noticia", "proxima", "tambem", "ja", "ate",
    "politica", "publica", "republica", "relacao", "posicao", "situacao", "decisao", "governanca",
    "historia", "historico", "ultima", "ultimo", "unico", "possivel", "proprio", "apos", "alem",
}  # fmt: skip
URL_RE = re.compile(r"https?://|www\.|\.com\b|\.br\b", re.I)
MARKDOWN_RE = re.compile(r"[*_#`\[\]<>|]")
EMOJI_RE = re.compile(
    "[\U0001f300-\U0001faff\U00002600-\U000027bf\U0001f000-\U0001f2ff\U00002b00-\U00002bff]"
)


class DialogueError(Exception):
    """Resposta do provedor inválida (o texto vai de volta no prompt da nova tentativa)."""


class DialogueProvider(Protocol):
    name: str

    def complete(self, prompt: str) -> str:
        """Envia o prompt e devolve o texto cru (JSON) do modelo."""
        ...


def build_prompt(theme: Theme, article: Article) -> str:
    template = (get_settings().prompts_dir / "dialogo.md").read_text(encoding="utf-8")
    words = article.text.split()
    texto = " ".join(words[:MAX_INPUT_WORDS])
    return template.format(
        tema=theme.nome, tom=theme.tom, veiculo=article.source, titulo=article.title, texto=texto
    )


def _strip_code_fence(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```[a-zA-Z]*\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
    return raw


def parse_and_validate(raw: str, strict_length: bool = True) -> Dialogue:
    try:
        data = json.loads(_strip_code_fence(raw))
    except json.JSONDecodeError as exc:
        raise DialogueError(f"A resposta não é JSON válido: {exc}") from exc
    try:
        dialogue = Dialogue.model_validate(data)
    except ValidationError as exc:
        raise DialogueError(f"JSON fora do esquema: {exc.errors()[:3]}") from exc

    problems: list[str] = []
    if not dialogue.falas:
        raise DialogueError("Nenhuma fala.")
    if dialogue.falas[0].voz != "dora":
        problems.append("A primeira fala deve ser da Dora.")
    if not dialogue.titulo_episodio.strip():
        problems.append("titulo_episodio vazio.")
    if len(dialogue.titulo_episodio) > MAX_TITLE:
        problems.append(f"titulo_episodio tem {len(dialogue.titulo_episodio)} caracteres (máx. {MAX_TITLE}).")
    if strict_length:
        n = len(dialogue.falas)
        if not MIN_LINES <= n <= MAX_LINES:
            problems.append(f"Há {n} falas; devem ser entre {MIN_LINES} e {MAX_LINES}.")
        w = dialogue.word_count
        if w < MIN_WORDS:
            problems.append(
                f"O total é {w} palavras; faltam pelo menos {MIN_WORDS - w + 10}. "
                "Deixe as falas da Dora (3, 5, 7 e 9) mais longas, com mais detalhes da matéria."
            )
        elif w > MAX_WORDS:
            problems.append(f"O total é {w} palavras; corte pelo menos {w - MAX_WORDS + 10}.")
    all_words = re.findall(r"\w+", " ".join(f.texto.lower() for f in dialogue.falas))
    unaccented = [w for w in all_words if w in UNACCENTED]
    if len(unaccented) >= 2:
        examples = ", ".join(sorted(set(unaccented))[:5])
        problems.append(f"Faltam acentos ({examples}). Use a acentuação correta do português.")
    for i, fala in enumerate(dialogue.falas, 1):
        if URL_RE.search(fala.texto):
            problems.append(f"Fala {i} contém URL.")
        if EMOJI_RE.search(fala.texto):
            problems.append(f"Fala {i} contém emoji.")
        if MARKDOWN_RE.search(fala.texto):
            problems.append(f"Fala {i} contém marcação (Markdown/símbolos).")
        if not fala.texto.strip():
            problems.append(f"Fala {i} está vazia.")
    if problems:
        raise DialogueError(" ".join(problems))
    return dialogue


TRANSIENT_MARKERS = ("429", "500", "502", "503", "504", "UNAVAILABLE", "RESOURCE_EXHAUSTED", "timed out")
BACKOFF_S = (5, 15)


def is_transient(exc: Exception) -> bool:
    return isinstance(exc, TimeoutError) or any(m in str(exc) for m in TRANSIENT_MARKERS)


def call_with_backoff(
    provider: DialogueProvider, prompt: str, sleep: Callable[[float], None] = time.sleep
) -> str:
    """Erros temporários (limite, servidor ocupado) ganham novas chamadas com espera."""
    for wait in (*BACKOFF_S, None):
        try:
            return provider.complete(prompt)
        except Exception as exc:
            if wait is None or not is_transient(exc):
                raise
            log.warning("[%s] erro temporário, nova chamada em %ss: %s", provider.name, wait, exc)
            sleep(wait)
    raise AssertionError("inalcançável")


def generate_with(
    provider: DialogueProvider, prompt: str, sleep: Callable[[float], None] = time.sleep
) -> Dialogue:
    """1 tentativa + até 2 novas tentativas com o erro anexado ao prompt."""
    attempt_prompt = prompt
    last_error: Exception | None = None
    best_short: Dialogue | None = None
    for attempt in range(1 + EXTRA_ATTEMPTS):
        raw = call_with_backoff(provider, attempt_prompt, sleep)
        try:
            dialogue = parse_and_validate(raw)
        except DialogueError as exc:
            last_error = exc
            log.warning("[%s] tentativa %d inválida: %s", provider.name, attempt + 1, exc)
            best_short = _keep_if_only_length_problem(raw, best_short)
            attempt_prompt = (
                f"{prompt}\n\n## Correção necessária\nSua resposta anterior foi rejeitada: {exc}\n"
                f"Resposta anterior:\n{raw}\n\nGere novamente o JSON completo corrigindo esses pontos."
            )
            continue
        dialogue.gerador = provider.name
        return dialogue
    if best_short is not None:
        log.warning(
            "[%s] aceitando a tentativa mais longa (%d palavras) fora da faixa ideal",
            provider.name,
            best_short.word_count,
        )
        best_short.gerador = provider.name
        return best_short
    raise DialogueError(f"{provider.name}: respostas inválidas após novas tentativas ({last_error})")


def _keep_if_only_length_problem(raw: str, best: Dialogue | None) -> Dialogue | None:
    """Guarda a resposta se o único problema for o tamanho e ela tiver ≥ TOLERATED_MIN_WORDS."""
    try:
        candidate = parse_and_validate(raw, strict_length=False)
    except DialogueError:
        return best
    if not TOLERATED_MIN_WORDS <= candidate.word_count <= MAX_WORDS or len(candidate.falas) < MIN_LINES:
        return best
    if best is None or candidate.word_count > best.word_count:
        return candidate
    return best


def default_providers() -> list[DialogueProvider]:
    from app.pipeline.dialogue.gemini import GeminiProvider
    from app.pipeline.dialogue.openai_compat import GroqProvider, OllamaProvider

    s = get_settings()
    providers: list[DialogueProvider] = []
    if s.gemini_api_key:
        providers.append(GeminiProvider(s.gemini_api_key, s.gemini_model))
    if s.groq_api_key:
        providers.append(GroqProvider(s.groq_api_key, s.groq_model))
    if s.ollama_url:
        providers.append(OllamaProvider(s.ollama_url))
    return providers


def generate_dialogue(
    theme: Theme, article: Article, providers: list[DialogueProvider] | None = None
) -> Dialogue:
    """Tenta cada provedor em ordem; se todos falharem, usa o gerador local (sem IA)."""
    from app.pipeline.dialogue.local import generate_local

    providers = default_providers() if providers is None else providers
    prompt = build_prompt(theme, article)
    for provider in providers:
        try:
            return generate_with(provider, prompt)
        except Exception as exc:  # noqa: BLE001 — limite (429), rede, JSON inválido...
            log.warning("[%s] provedor %s falhou: %s", theme.id, provider.name, exc)
    log.warning("[%s] usando gerador local (sem IA)", theme.id)
    return generate_local(theme, article)
