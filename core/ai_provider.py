"""AI provider abstraction for Haji.

The core stays provider-agnostic. Configure an OpenAI-compatible endpoint and
credentials through environment variables; no secret is stored in the repo.
"""
from __future__ import annotations
import base64, json, os, uuid
from dataclasses import dataclass
from urllib.request import Request, urlopen

class AIProvider:
    def chat(self, text: str, image: bytes | None = None) -> str: raise NotImplementedError
    def transcribe(self, audio: bytes, mime_type: str = "audio/m4a") -> str: raise NotImplementedError

@dataclass
class OpenAICompatibleProvider(AIProvider):
    base_url: str
    api_key: str
    model: str = "gpt-4o-mini"
    transcription_model: str = "gpt-4o-mini-transcribe"
    timeout: int = 60

    def _post(self, path: str, payload: dict) -> dict:
        request = Request(self.base_url.rstrip("/") + path, data=json.dumps(payload).encode(), headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}, method="POST")
        with urlopen(request, timeout=self.timeout) as response: return json.loads(response.read().decode())

    def chat(self, text: str, image: bytes | None = None) -> str:
        content = [{"type": "text", "text": text}]
        if image:
            content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64.b64encode(image).decode()}"}})
        result = self._post("/chat/completions", {"model": self.model, "messages": [{"role": "user", "content": content}]})
        return str(result["choices"][0]["message"]["content"])

    def transcribe(self, audio: bytes, mime_type: str = "audio/m4a") -> str:
        boundary = "----Haji" + uuid.uuid4().hex
        filename = "haji-voice.m4a"
        parts = [
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"model\"\r\n\r\n{self.transcription_model}\r\n".encode(),
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{filename}\"\r\nContent-Type: {mime_type}\r\n\r\n".encode() + audio + b"\r\n",
            f"--{boundary}--\r\n".encode(),
        ]
        request = Request(self.base_url.rstrip("/") + "/audio/transcriptions", data=b"".join(parts), headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": f"multipart/form-data; boundary={boundary}"}, method="POST")
        with urlopen(request, timeout=self.timeout) as response:
            result = json.loads(response.read().decode())
        return str(result.get("text", ""))

def provider_from_env() -> AIProvider | None:
    api_key = os.getenv("HAJI_AI_API_KEY", "").strip()
    if not api_key: return None
    return OpenAICompatibleProvider(
        base_url=os.getenv("HAJI_AI_BASE_URL", "https://api.openai.com/v1"),
        api_key=api_key,
        model=os.getenv("HAJI_AI_MODEL", "gpt-4o-mini"),
        transcription_model=os.getenv("HAJI_TRANSCRIPTION_MODEL", "gpt-4o-mini-transcribe"),
    )
