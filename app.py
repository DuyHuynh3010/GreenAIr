from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import unquote

from backend.model_service import MODELS, InputError, predict_current, predict_future


FRONTEND_DIR = Path(__file__).resolve().parent / "frontend"
CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".svg": "image/svg+xml",
}


def respond(start_response, status, body, content_type):
    start_response(status, [("Content-Type", content_type), ("Content-Length", str(len(body)))])
    return [body]


def json_response(start_response, status, data):
    body = json.dumps(data).encode("utf-8")
    return respond(start_response, status, body, "application/json; charset=utf-8")


def app(environ, start_response):
    method = environ.get("REQUEST_METHOD", "GET")
    path = unquote(environ.get("PATH_INFO", "/"))

    if path == "/api/health" and method == "GET":
        return json_response(start_response, "200 OK", MODELS.health())

    if path.startswith("/api/"):
        if method != "POST" or path not in ("/api/predict/current", "/api/predict/future"):
            return json_response(start_response, "404 Not Found", {"error": "API route not found"})
        try:
            length = int(environ.get("CONTENT_LENGTH") or 0)
            payload = json.loads(environ["wsgi.input"].read(length) or b"{}")
            if not isinstance(payload, dict):
                raise InputError("Request body must be a JSON object.")
            prediction = predict_current(payload) if path.endswith("/current") else predict_future(payload)
            return json_response(start_response, "200 OK", prediction)
        except (ValueError, InputError) as exc:
            return json_response(start_response, "422 Unprocessable Entity", {"error": str(exc)})
        except Exception as exc:
            return json_response(start_response, "400 Bad Request", {"error": str(exc)})

    if method != "GET":
        return respond(start_response, "405 Method Not Allowed", b"Method not allowed", "text/plain")
    target = (FRONTEND_DIR / (path.lstrip("/") or "index.html")).resolve()
    if not target.is_relative_to(FRONTEND_DIR) or not target.is_file():
        return respond(start_response, "404 Not Found", b"File not found", "text/plain")
    return respond(start_response, "200 OK", target.read_bytes(), CONTENT_TYPES.get(target.suffix, "application/octet-stream"))
