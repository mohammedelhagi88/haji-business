"""Minimal Haji HTTP API for the mobile client."""
from __future__ import annotations
import json, os
from email.parser import BytesParser
from email.policy import default
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from core.agent import HajiAgent
from core.ai_provider import provider_from_env
from core.persistent_memory import PersistentMemoryStore
from core.runtime import HajiRuntime
from core.tasks import TaskManager

class HajiApp:
    def __init__(self) -> None:
        self.runtime = HajiRuntime(); self.memory = PersistentMemoryStore(os.getenv("HAJI_MEMORY_DB", "haji_memory.sqlite3")); self.tasks = TaskManager(); self.provider = provider_from_env()
        self.agent = HajiAgent(memory=self.memory, tasks=self.tasks, runtime=self.runtime, provider=self.provider); self.runtime.start()
    def message(self, text: str, image: bytes | None = None) -> dict: return self.agent.handle(text=text, image=image)
    def approve(self, approval_id: str) -> dict: return self.agent.approve(approval_id)
app = HajiApp()

class Handler(BaseHTTPRequestHandler):
    def _json(self, status: int, payload: dict) -> None:
        data = json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8"); self.send_response(status); self.send_header("Content-Type", "application/json; charset=utf-8"); self.send_header("Content-Length", str(len(data))); self.send_header("Access-Control-Allow-Origin", "*"); self.end_headers(); self.wfile.write(data)
    def _read_body(self) -> bytes:
        try: length = int(self.headers.get("Content-Length", "0"))
        except ValueError: length = 0
        return self.rfile.read(max(0, length))
    def _parse_multipart(self, raw: bytes, content_type: str) -> dict[str, bytes]:
        header = f"Content-Type: {content_type}\r\nMIME-Version: 1.0\r\n\r\n".encode(); message = BytesParser(policy=default).parsebytes(header + raw); fields = {}
        if message.is_multipart():
            for part in message.iter_parts():
                name = part.get_param("name", header="content-disposition")
                if name: fields[name] = part.get_payload(decode=True) or b""
        return fields
    def do_POST(self) -> None:
        if self.path.startswith("/v1/agent/approval/"):
            self._json(200, app.approve(self.path.rsplit("/", 1)[-1])); return
        if self.path == "/v1/agent/voice":
            raw = self._read_body(); content_type = self.headers.get("Content-Type", "")
            try:
                fields = self._parse_multipart(raw, content_type) if "multipart/form-data" in content_type else {"audio": raw}
                audio = fields.get("audio", b"")
                if not audio: raise ValueError("empty_audio")
                if app.provider is None: self._json(503, {"error": "ai_provider_not_configured", "text": "الصوت وصل، لكن مزود الذكاء مش مفعّل على السيرفر."}); return
                transcript = app.provider.transcribe(audio, "audio/mp4")
                self._json(200, {**app.message(transcript), "transcript": transcript}); return
            except ValueError: self._json(400, {"error": "audio_required"}); return
            except NotImplementedError: self._json(501, {"error": "transcription_not_implemented"}); return
            except Exception as exc: self._json(502, {"error": "transcription_failed", "detail": str(exc)}); return
        if self.path != "/v1/agent/message": self._json(404, {"error": "not_found"}); return
        raw = self._read_body(); content_type = self.headers.get("Content-Type", ""); text = ""; image = None
        if "application/json" in content_type:
            try:
                body = json.loads(raw.decode()); text = str(body.get("text", "")); encoded = body.get("image"); image = str(encoded).encode() if encoded else None
            except (ValueError, UnicodeDecodeError): self._json(400, {"error": "invalid_json"}); return
        elif "multipart/form-data" in content_type:
            try:
                fields = self._parse_multipart(raw, content_type); text = fields.get("text", b"").decode("utf-8", errors="replace"); image = fields.get("image")
            except Exception: self._json(400, {"error": "invalid_multipart"}); return
        else: self._json(415, {"error": "unsupported_content_type"}); return
        self._json(200, app.message(text, image))
    def do_GET(self) -> None:
        if self.path == "/v1/runtime/status": self._json(200, self.server.haji_app.runtime.status()); return
        self._json(404, {"error": "not_found"})
    def do_OPTIONS(self) -> None:
        self.send_response(204); self.send_header("Access-Control-Allow-Origin", "*"); self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS"); self.send_header("Access-Control-Allow-Headers", "Content-Type"); self.end_headers()

def run(host: str = "0.0.0.0", port: int = 8000) -> None:
    print(f"Haji API listening on http://{host}:{port}"); server = ThreadingHTTPServer((host, port), Handler); server.haji_app = app; server.serve_forever()
if __name__ == "__main__": run()
