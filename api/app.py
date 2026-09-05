"""Minimal Haji HTTP API.

Uses only the Python standard library so the core can be deployed without
forcing a web framework. A framework adapter can be added later.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs

from core.memory import MemoryStore
from core.runtime import HajiRuntime, RuntimeEvent
from core.tasks import TaskManager


class HajiApp:
    def __init__(self) -> None:
        self.runtime = HajiRuntime()
        self.memory = MemoryStore()
        self.tasks = TaskManager()
        self.runtime.start()

    def message(self, text: str, image: str | None = None) -> dict:
        self.runtime.emit(RuntimeEvent("agent.message", {"text": text, "has_image": bool(image)}))
        if image:
            answer = "وصلتني الصورة مع طلبك. جاهز نمررها لمحرك الرؤية للتحليل."
        elif text.strip():
            self.memory.set("last_user_message", text.strip())
            answer = f"تمام، فهمتك: {text.strip()}"
        else:
            answer = "قولّي شن تبي نديرلك."
        return {"text": answer, "requiresApproval": False}


app = HajiApp()


class Handler(BaseHTTPRequestHandler):
    def _json(self, status: int, payload: dict) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self) -> None:
        if self.path != "/v1/agent/message":
            self._json(404, {"error": "not_found"})
            return
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length)
        content_type = self.headers.get("Content-Type", "")
        text = ""
        has_image = False
        if "application/json" in content_type:
            try:
                body = json.loads(raw.decode("utf-8"))
                text = str(body.get("text", ""))
                has_image = bool(body.get("image"))
            except (ValueError, UnicodeDecodeError):
                self._json(400, {"error": "invalid_json"})
                return
        else:
            fields = parse_qs(raw.decode("utf-8", errors="ignore"))
            text = fields.get("text", [""])[0]
            has_image = bool(fields.get("image", [""])[0])
        self._json(200, app.message(text, "image" if has_image else None))

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
