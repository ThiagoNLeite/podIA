"""Carrega e valida config/themes.yaml."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import BaseModel, Field

from app.settings import get_settings


class Theme(BaseModel):
    id: str
    nome: str
    icone: str
    cor: str
    busca: str
    janela_horas: int = Field(default=24, ge=1, le=72)
    tom: str = "informativo"
    feeds_extras: list[str] = []
    bloqueadas: list[str] = []


def load_themes(path: Path | None = None) -> dict[str, Theme]:
    path = path or get_settings().config_dir / "themes.yaml"
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return {tid: Theme(id=tid, **data) for tid, data in raw.items()}


@lru_cache
def get_themes() -> dict[str, Theme]:
    return load_themes()


def get_theme(theme_id: str) -> Theme:
    themes = get_themes()
    if theme_id not in themes:
        raise KeyError(f"Tema desconhecido: {theme_id}. Opções: {', '.join(themes)}")
    return themes[theme_id]
