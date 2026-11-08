"""Tabelas do SQLite (§6). Datas gravadas em UTC; a API converte para o TZ configurado."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import Column, Index, Text
from sqlmodel import Field, SQLModel


def utcnow() -> datetime:
    return datetime.now(UTC)


class Noticia(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    tema: str = Field(index=True)
    titulo: str
    url: str = Field(unique=True)  # URL real (já resolvida); evita repetir notícia
    veiculo: str | None = None
    publicada_em: datetime | None = None
    texto: str | None = Field(default=None, sa_column=Column(Text))  # só para gerar o diálogo
    coletada_em: datetime = Field(default_factory=utcnow)


class Episodio(SQLModel, table=True):
    __table_args__ = (Index("idx_episodio_tema_data", "tema", "gerado_em"),)

    id: int | None = Field(default=None, primary_key=True)
    tema: str
    noticia_id: int = Field(foreign_key="noticia.id")
    titulo: str
    dialogo_json: str = Field(sa_column=Column(Text, nullable=False))  # falas + inicio_s
    gerador: str  # gemini | groq | ollama | local
    motor_voz: str  # kokoro | piper
    audio_arquivo: str | None = None  # NULL quando expirado pela limpeza
    duracao_s: int | None = None
    status: str = "pronto"  # gerando | pronto | erro
    erro: str | None = None  # etapa e mensagem, se status = erro
    gerado_em: datetime = Field(default_factory=utcnow)
