"""Provedor Gemini (plano gratuito do Google AI Studio)."""

from __future__ import annotations

TEMPERATURE = 0.4


class GeminiProvider:
    name = "gemini"

    def __init__(self, api_key: str, model: str) -> None:
        from google import genai

        self._client = genai.Client(api_key=api_key)
        self._model = model

    def complete(self, prompt: str) -> str:
        from google.genai import types

        resp = self._client.models.generate_content(
            model=self._model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=TEMPERATURE, response_mime_type="application/json"
            ),
        )
        return resp.text or ""
