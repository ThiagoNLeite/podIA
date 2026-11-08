"""Interface comum dos motores de voz e a etapa synthesize() do pipeline."""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Protocol

import numpy as np

from app.pipeline.podia_tts.normalize import normalize_text
from app.pipeline.types import Dialogue, Segment, Voice
from app.settings import get_settings

log = logging.getLogger(__name__)


class TTSEngine(Protocol):
    name: str
    sample_rate: int

    def synthesize(self, text: str, voice: Voice) -> np.ndarray:
        """Devolve amostras float32 mono em sample_rate."""
        ...


@lru_cache
def get_engine(name: str | None = None) -> TTSEngine:
    """Carrega o motor uma vez e reutiliza."""
    name = (name or get_settings().tts_engine).lower()
    if name == "kokoro":
        from app.pipeline.podia_tts.kokoro_engine import KokoroEngine

        return KokoroEngine()
    if name == "piper":
        raise NotImplementedError("Piper é só plano B documentado (Kokoro aprovado na Fase 0).")
    raise ValueError(f"TTS_ENGINE desconhecido: {name}")


def synthesize(dialogue: Dialogue, engine: TTSEngine | None = None) -> list[Segment]:
    engine = engine or get_engine()
    segments: list[Segment] = []
    for fala in dialogue.falas:
        spoken = normalize_text(fala.texto)
        log.debug("%s: %s", fala.voz, spoken)
        samples = engine.synthesize(spoken, fala.voz)
        segments.append(
            Segment(voice=fala.voz, text=fala.texto, samples=samples, sample_rate=engine.sample_rate)
        )
    return segments
