from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from model_service import MODELS, InputError, predict_current, predict_future


ROOT_DIR = Path(__file__).resolve().parents[1]
FRONTEND_DIR = ROOT_DIR / "frontend"


class GreenAirHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/health":
            self.send_json(MODELS.health())
            return
        self.serve_static(parsed.path)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        try:
            payload = self.read_json()
            if parsed.path == "/api/predict/current":
                self.send_json(predict_current(payload))
                return
            if parsed.path == "/api/predict/future":
                self.send_json(predict_future(payload))
                return
            self.send_error(404, "API route not found")
        except InputError as exc:
            self.send_json({"error": str(exc)}, status=422)
        except Exception as exc:
            self.send_json({"error": str(exc)}, status=400)

    def read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length).decode("utf-8")
        try:
            payload = json.loads(body or "{}")
        except json.JSONDecodeError as exc:
            raise InputError("Request body must be valid JSON.") from exc
        if not isinstance(payload, dict):
            raise InputError("Request body must be a JSON object.")
        return payload

    def send_json(self, payload: dict[str, Any], status: int = 200) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def serve_static(self, route: str) -> None:
        target = FRONTEND_DIR / "index.html" if route in ("", "/") else FRONTEND_DIR / route.lstrip("/")
        target = target.resolve()
        if not str(target).startswith(str(FRONTEND_DIR.resolve())) or not target.exists():
            self.send_error(404, "File not found")
            return

        content_types = {
            ".html": "text/html; charset=utf-8",
            ".css": "text/css; charset=utf-8",
            ".js": "application/javascript; charset=utf-8",
            ".svg": "image/svg+xml",
        }
        body = target.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_types.get(target.suffix, "application/octet-stream"))
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: Any) -> None:
        print(f"{self.address_string()} - {format % args}")


def run() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 8000), GreenAirHandler)
    print("GreenAIr demo running at http://127.0.0.1:8000")
    server.serve_forever()


if __name__ == "__main__":
    run()
