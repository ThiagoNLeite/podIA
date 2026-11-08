from __future__ import annotations

import numpy as np
import pytest

from app.pipeline import audio
from app.pipeline.types import Segment

SR = 1000


def seg(seconds: float, voice: str = "dora") -> Segment:
    return Segment(
        voice=voice, text="x", samples=np.ones(int(seconds * SR), dtype=np.float32) * 0.1, sample_rate=SR
    )  # type: ignore[arg-type]


def test_pauses_and_line_starts() -> None:
    samples, starts, sr = audio.concat_segments([seg(1), seg(2, "alex"), seg(1.5)])
    assert sr == SR
    assert starts == [0.0, 1.3, 3.6]
    assert len(samples) == int((1 + 2 + 1.5 + 2 * audio.PAUSE_S) * SR)


def test_jingle_shifts_starts_and_wraps_episode() -> None:
    jingle = np.zeros(2 * SR, dtype=np.float32)
    samples, starts, _ = audio.concat_segments([seg(1), seg(1, "alex")], jingle)
    assert starts == [2.3, 3.6]
    assert len(samples) == round((2 + 0.3 + 1 + 0.3 + 1 + 0.3 + 2) * SR)


def test_missing_jingle_returns_none(tmp_path) -> None:
    assert audio.load_jingle(tmp_path / "nao_existe.mp3", SR) is None


def test_empty_segments_raise() -> None:
    with pytest.raises(ValueError):
        audio.concat_segments([])


def test_assemble_exports_mp3(tmp_path, monkeypatch) -> None:
    try:
        audio.find_ffmpeg()
    except FileNotFoundError:
        pytest.skip("ffmpeg não instalado")
    from app.settings import get_settings

    monkeypatch.setattr(get_settings(), "assets_dir", tmp_path)  # sem vinheta
    sr = 24_000
    tone = (np.sin(np.linspace(0, 2000, sr)) * 0.3).astype(np.float32)
    segs = [Segment("dora", "a", tone, sr), Segment("alex", "b", tone, sr)]
    out = tmp_path / "ep.mp3"
    result = audio.assemble(segs, out)
    assert out.exists() and out.stat().st_size > 1000
    assert result.duration_s == 2.3
    assert result.line_starts == [0.0, 1.3]
