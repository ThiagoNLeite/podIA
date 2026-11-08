"""Tipos de dados que passam entre as etapas do pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel

Voice = Literal["dora", "alex"]


@dataclass
class NewsItem:
    """Item cru do RSS (link ainda pode ser do Google News)."""

    title: str
    link: str
    published: datetime
    source: str
    summary: str = ""


@dataclass
class Article:
    """Notícia escolhida, com URL real e texto extraído."""

    title: str
    url: str
    source: str
    published: datetime
    text: str
    summary: str = ""

    @property
    def word_count(self) -> int:
        return len(self.text.split())


class Line(BaseModel):
    voz: Voice
    texto: str


class Dialogue(BaseModel):
    titulo_episodio: str
    falas: list[Line]
    gerador: str = "desconhecido"

    @property
    def word_count(self) -> int:
        return sum(len(f.texto.split()) for f in self.falas)


@dataclass
class Segment:
    """Áudio de uma fala (amostras float32 mono)."""

    voice: Voice
    text: str
    samples: object  # numpy.ndarray
    sample_rate: int


@dataclass
class AudioResult:
    path: Path
    duration_s: float
    line_starts: list[float] = field(default_factory=list)
