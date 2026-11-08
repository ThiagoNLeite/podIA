"""Provedores de reserva: Groq (plano gratuito) e Ollama (local)."""

from __future__ import annotations

import httpx

TEMPERATURE = 0.4
TIMEOUT_S = 90


class GroqProvider:
    name = "groq"

    def __init__(self, api_key: str, model: str) -> None:
        self._key = api_key
        self._model = model

    def complete(self, prompt: str) -> str:
        resp = httpx.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {self._key}"},
            json={
                "model": self._model,
                "temperature": TEMPERATURE,
                "response_format": {"type": "json_object"},
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=TIMEOUT_S,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]


class OllamaProvider:
    name = "ollama"

    def __init__(self, base_url: str, model: str = "llama3.1") -> None:
        self._url = base_url.rstrip("/")
        self._model = model

    def complete(self, prompt: str) -> str:
        resp = httpx.post(
            f"{self._url}/api/chat",
            json={
                "model": self._model,
                "format": "json",
                "stream": False,
                "options": {"temperature": TEMPERATURE},
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=TIMEOUT_S * 3,
        )
        resp.raise_for_status()
        return resp.json()["message"]["content"]
