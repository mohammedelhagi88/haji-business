"""AI provider abstraction for Haji.

The core stays provider-agnostic. Configure an OpenAI-compatible HTTP endpoint
through environment variables; no API key is stored in the repository.
"""

from __future__ import annotations

import base64
import json
import os
from dataclasses import dataclass
from urllib.request import Request, urlopen


class AIProvider:
    """Interface implemented by an external AI service."""

    def chat(self, text: str, image: bytes | None = None) -> str:
        raise NotImplementedError

    def transcribe(self, audio: bytes, mime_type: str = "audio/m4a") -> str:
        raise NotImplementedError


@dataclass
class OpenAICompatibleProvider(AIProvider):
    """Small stdlib-only adapter for OpenAI-compatible chat endpoints."""

    base_url: str
    api_key: str
    model: str = "gpt-4o-mini"
    timeout: int = 60

    def _post(self, path: str, payload: dict) -> dict:
        url = self.base_url.rstrip("/") + path
        request = Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urlopen(request, timeout=self.timeout) as response:
            return json.loads(response.read().decode("utf-8"))

    def chat(self, text: str, image: bytes | None = None) -> str:
        content: list[dict] = [{"type": "text", "text": text}]
        if image:
            encoded = base64.b64encode(image).decode("ascii")
            content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded}"}})
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": content}],
        }
        result = self._post("/chat/completions", payload)
        return str(result["choices"][0]["message"]["content"])

    def transcribe(self, audio: bytes, mime_type: str = "audio/m4a") -> str:
        # Transcription APIs are multipart and intentionally left behind the
        # same provider boundary. Implementations can override this method.
        raise NotImplementedError("This provider does not expose transcription yet")


def provider_from_env() -> AIProvider | None:
    """Build a provider only when credentials are explicitly configured."""
    api_key = os.getenv("HAJI_AI_API_KEY", "").strip()
    if not api_key:
        return None
    return OpenAICompatibleProvider(
        base_url=os.getenv("HAJI_AI_BASE_URL", "https://api.openai.com/v1"),
        api_key=api_key,
        model=os.getenv("HAJI_AI_MODEL", "gpt-4o-mini"),
    )
