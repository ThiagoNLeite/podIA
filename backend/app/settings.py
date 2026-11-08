"""Configurações lidas do backend/.env (pydantic-settings)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env", env_file_encoding="utf-8", extra="ignore"
    )

    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.5-flash-lite"
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    ollama_url: str = ""

    tts_engine: str = "kokoro"

    admin_key: str = "troque-esta-chave"
    scheduler_enabled: bool = True  # False nos testes
    scheduler_interval_hours: float = 3
    audio_retention_days: int = 7
    tz: str = "America/Cuiaba"
    data_dir: Path = BACKEND_DIR / "data"
    log_level: str = "INFO"

    config_dir: Path = BACKEND_DIR / "config"
    prompts_dir: Path = BACKEND_DIR / "prompts"
    assets_dir: Path = BACKEND_DIR / "assets"

    @property
    def audio_dir(self) -> Path:
        path = self.data_path / "audio"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def data_path(self) -> Path:
        path = self.data_dir if self.data_dir.is_absolute() else BACKEND_DIR / self.data_dir
        path.mkdir(parents=True, exist_ok=True)
        return path


@lru_cache
def get_settings() -> Settings:
    return Settings()
