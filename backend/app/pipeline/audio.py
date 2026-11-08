"""Etapa 5: juntar as falas, registrar o início de cada uma e exportar o MP3 (§4.6)."""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf

from app.pipeline.types import AudioResult, Segment
from app.settings import get_settings

log = logging.getLogger(__name__)

PAUSE_S = 0.3
TARGET_LUFS = -16
BITRATE = "64k"
MIN_DURATION_S, MAX_DURATION_S = 100, 150  # 1:40 a 2:30


def find_ffmpeg() -> str:
    found = shutil.which("ffmpeg")
    if found:
        return found
    if os.environ.get("FFMPEG_PATH"):
        return os.environ["FFMPEG_PATH"]
    # winget (Windows): o PATH só atualiza em um terminal novo, então procura direto
    winget = Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WinGet"
    for candidate in [
        winget / "Links" / "ffmpeg.exe",
        *winget.glob("Packages/Gyan.FFmpeg*/*/bin/ffmpeg.exe"),
    ]:
        if candidate.exists():
            return str(candidate)
    raise FileNotFoundError(
        "ffmpeg não encontrado. Instale (winget install Gyan.FFmpeg) e reabra o terminal."
    )


def load_jingle(path: Path, sample_rate: int) -> np.ndarray | None:
    """Decodifica a vinheta para float32 mono na taxa das vozes; None se não existir."""
    if not path.exists():
        return None
    proc = subprocess.run(
        [
            find_ffmpeg(),
            "-v",
            "error",
            "-i",
            str(path),
            "-ac",
            "1",
            "-ar",
            str(sample_rate),
            "-f",
            "f32le",
            "-",
        ],
        capture_output=True,
        check=True,
    )
    return np.frombuffer(proc.stdout, dtype=np.float32)


def concat_segments(
    segments: list[Segment], jingle: np.ndarray | None = None, pause_s: float = PAUSE_S
) -> tuple[np.ndarray, list[float], int]:
    """Função pura: devolve (amostras, início de cada fala em segundos, sample_rate)."""
    if not segments:
        raise ValueError("Nenhum segmento de áudio.")
    sr = segments[0].sample_rate
    pause = np.zeros(int(sr * pause_s), dtype=np.float32)
    parts: list[np.ndarray] = []
    starts: list[float] = []
    cursor = 0
    if jingle is not None and len(jingle):
        parts += [jingle, pause]
        cursor += len(jingle) + len(pause)
    for i, seg in enumerate(segments):
        if i:
            parts.append(pause)
            cursor += len(pause)
        starts.append(round(cursor / sr, 2))
        samples = np.asarray(seg.samples, dtype=np.float32)
        parts.append(samples)
        cursor += len(samples)
    if jingle is not None and len(jingle):
        parts += [pause, jingle]
    return np.concatenate(parts), starts, sr


def export_mp3(samples: np.ndarray, sample_rate: int, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    # loudnorm derruba o ffmpeg (0xC0000409) com silêncio absoluto: só normaliza se houver sinal.
    has_signal = samples.size > 0 and float(np.max(np.abs(samples))) > 1e-4
    filters = ["-af", f"loudnorm=I={TARGET_LUFS}:TP=-1.5:LRA=11"] if has_signal else []
    with tempfile.TemporaryDirectory() as tmp:
        wav = Path(tmp) / "episode.wav"
        sf.write(wav, samples, sample_rate)
        subprocess.run(
            [
                find_ffmpeg(), "-v", "error", "-y", "-i", str(wav),
                *filters,
                "-ac", "1", "-ar", "24000", "-codec:a", "libmp3lame", "-b:a", BITRATE,
                str(out_path),
            ],
            check=True,
            capture_output=True,
        )  # fmt: skip


def assemble(segments: list[Segment], out_path: Path) -> AudioResult:
    sr = segments[0].sample_rate if segments else 24_000
    jingle = load_jingle(get_settings().assets_dir / "vinheta.mp3", sr)
    samples, starts, sr = concat_segments(segments, jingle)
    duration = len(samples) / sr
    if not MIN_DURATION_S <= duration <= MAX_DURATION_S:
        log.warning("duração fora do alvo: %.0fs (esperado %d–%ds)", duration, MIN_DURATION_S, MAX_DURATION_S)
    export_mp3(samples, sr, out_path)
    return AudioResult(path=out_path, duration_s=round(duration, 1), line_starts=starts)
