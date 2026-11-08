"""Modelos de resposta da API (§5.2). O app espelha estes tipos em mobile/types/api.ts."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel

AVISO_IA = "Episódio gerado por IA a partir da fonte indicada."
AVISO_LOCAL = "Resumo automático (sem IA) a partir da fonte indicada."


class ThemeOut(BaseModel):
    id: str
    nome: str
    icone: str
    cor: str
    ultimo_episodio_em: datetime | None


class FonteOut(BaseModel):
    veiculo: str | None
    titulo_original: str
    url: str
    publicada_em: datetime | None


class FalaOut(BaseModel):
    voz: Literal["dora", "alex"]
    texto: str
    inicio_s: float


class EpisodeOut(BaseModel):
    id: int
    tema: str
    titulo: str
    gerado_em: datetime
    duracao_s: int | None
    audio_url: str | None  # None quando o áudio expirou pela limpeza
    gerador: str
    fonte: FonteOut
    falas: list[FalaOut]
    aviso: str


class GeneratingOut(BaseModel):
    status: Literal["gerando"] = "gerando"
    tema: str
    tentar_novamente_em_s: int = 5


class ErrorOut(BaseModel):
    erro: str
    mensagem: str


class HealthOut(BaseModel):
    status: Literal["ok"] = "ok"
    motor_voz: str
    motor_voz_carregado: bool
    llm_configurado: bool
    gerando: list[str]
    ultimo_ciclo: dict | None
