"""Minimal Haji HTTP API.

Uses only the Python standard library so the core can be deployed without
forcing a web framework. A framework adapter can be added later.
"""

from __future__ import annotations

import json
from email.parser import BytesParser
from email.policy import default
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from core.agent import HajiAgent
from core.memory import MemoryStore
from core.runtime import HajiRuntime
from core.tasks import TaskManager


class HajiApp:
    def __init__(self) -> None:
        self.runtime = HajiRuntime()
        self.memory = MemoryStore()
        self.tasks = TaskManager()
        self.agent = HajiAgent(
            memory=self.memory,
            tasks=self.tasks,
            runtime=self.runtime,
        )
        self.runtime.start()

    def message(self, text: str, image: bytes | None = None) -> dict:
        return self.agent.handle(text=text, image=image)


app = HajiApp()


class Handler(BaseHTTPRequestHandler):
    def _json(self, status: int, payload: dict) -> None:
        data = json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(data)

    def _read_body(self) -> bytes:
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = 0
        return self.rfile.read(max(0, length))

    def _parse_multipart(self, raw: bytes, content_type: str) -> tuple[str, bytes | None]:
        # email's MIME parser is in the Python standard library and correctly
        # handles the multipart/form-data boundary used by React Native FormData.
        header = f"Content-Type: {content_type}\r\nMIME-Version: 1.0\r\n\r\n".encode()
        message = BytesParser(policy=default).parsebytes(header + raw)
        text = ""
        image: bytes | None = None
        if message.is_multipart():
            for part in message.iter_parts():
                name = part.get_param("name", header="content-disposition")
                payload = part.get_payload(decode=True) or b""
                if name == "text":
                    text = payload.decode("utf-8", errors="replace")
                elif name == "image":
                    image = payload
        return text, image

    def do_POST(self) -> None:
        if self.path != "/v1/agent/message":
            self._json(404, {"error": "not_found"})
            return

        raw = self._read_body()
        content_type = self.headers.get("Content-Type", "")
        text = ""
        image: bytes | None = None

        if "application/json" in content_type:
            try:
                body = json.loads(raw.decode("utf-8"))
                text = str(body.get("text", ""))
                encoded_image = body.get("image")
                if encoded_image:
                    image = str(encoded_image).encode("utf-8")
            except (ValueError, UnicodeDecodeError):
                self._json(400, {"error": "invalid_json"})
                return
        elif "multipart/form-data" in content_type:
            try:
                text, image = self._parse_multipart(raw, content_type)
            except Exception:
                self._json(400, {"error": "invalid_multipart"})
                return
        else:
            self._json(415, {"error": "unsupported_content_type"})
            return

        self._json(200, app.message(text, image))

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()


def run(host: str = "0.0.0.0", port: int = 8000) -> None:
    print(f"Haji API listening on http://{host}:{port}")
    ThreadingHTTPServer((host, port), Handler).serve_forever()


if __name__ == "__main__":
    run()
