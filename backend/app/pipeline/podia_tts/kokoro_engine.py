"""Motor Kokoro-82M (Apache 2.0), roda em CPU. lang_code 'p' = português brasileiro."""

from __future__ import annotations

import numpy as np

from app.pipeline.types import Voice

VOICES: dict[str, str] = {"dora": "pf_dora", "alex": "pm_alex"}


class KokoroEngine:
    name = "kokoro"
    sample_rate = 24_000

    def __init__(self, speed: float = 1.0) -> None:
        from kokoro import KPipeline

        self._pipeline = KPipeline(lang_code="p", repo_id="hexgrad/Kokoro-82M")
        self._speed = speed

    def synthesize(self, text: str, voice: Voice) -> np.ndarray:
        chunks = [
            np.asarray(audio, dtype=np.float32)
            for _, _, audio in self._pipeline(text, voice=VOICES[voice], speed=self._speed)
            if audio is not None
        ]
        if not chunks:
            return np.zeros(0, dtype=np.float32)
        return np.concatenate(chunks)
