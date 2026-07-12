from __future__ import annotations

import json
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

try:
    import joblib
    import pandas as pd
except ImportError:
    joblib = None
    pd = None


ROOT_DIR = Path(__file__).resolve().parents[1]
FRONTEND_DIR = ROOT_DIR / "frontend"
MODELS_DIR = Path(__file__).resolve().parent / "models"

CURRENT_FEATURES = [
    "co",
    "no",
    "no2",
    "o3",
    "so2",
    "pm2_5",
    "pm10",
    "nh3",
    "temperature_C",
    "humidity_%",
    "rain_mm",
    "wind_speed_kmh",
    "is_event_anomaly",
]

FUTURE_FEATURES = [
    "hour",
    "month",
    "dayofweek",
    "co_lag1",
    "no_lag1",
    "no2_lag1",
    "o3_lag1",
    "so2_lag1",
    "pm2_5_lag1",
    "pm10_lag1",
    "nh3_lag1",
    "temperature_C_lag1",
    "humidity_%_lag1",
    "rain_mm_lag1",
    "wind_speed_kmh_lag1",
    "pm2_5_lag2",
    "pm10_lag2",
    "o3_lag2",
    "co_lag2",
]

AQI_LEVELS = {
    1: {
        "label": "Tot",
        "display": "Tot",
        "tone": "good",
        "advice": "Chat luong khong khi on dinh. Co the sinh hoat ngoai troi binh thuong.",
    },
    2: {
        "label": "Trung binh",
        "display": "Trung binh",
        "tone": "moderate",
        "advice": "Chap nhan duoc. Nguoi nhay cam nen theo doi neu hoat dong ngoai troi lau.",
    },
    3: {
        "label": "Kem",
        "display": "Kem",
        "tone": "unhealthy-sensitive",
        "advice": "Nguoi nhay cam nen giam thoi gian ngoai troi va can nhac deo khau trang.",
    },
    4: {
        "label": "Xau",
        "display": "Xau",
        "tone": "unhealthy",
        "advice": "Han che hoat dong ngoai troi. Tre em, nguoi gia va nguoi co benh nen o trong nha.",
    },
    5: {
        "label": "Rat xau / Nguy hai",
        "display": "Rat xau / Nguy hai",
        "tone": "hazardous",
        "advice": "Canh bao suc khoe. Nen o trong nha, dong cua va su dung may loc khong khi neu co.",
    },
}


class ModelStore:
    def __init__(self) -> None:
        self.current_model = None
        self.current_scaler = None
        self.future_model = None
        self.future_scaler = None
        self.error = ""
        self.load()

    def load(self) -> None:
        if joblib is None or pd is None:
            self.error = "Missing Python packages. Install requirements.txt before running model inference."
            return

        try:
            self.current_model = joblib.load(MODELS_DIR / "hcmc_rf_model.pkl")
            self.current_scaler = joblib.load(MODELS_DIR / "hcmc_scaler.pkl")
            future_model_path = MODELS_DIR / "hcmc_aqi_future_model.pkl"
            future_scaler_path = MODELS_DIR / "hcmc_aqi_future_scaler.pkl"
            if future_model_path.exists() and future_scaler_path.exists():
                self.future_model = joblib.load(future_model_path)
                self.future_scaler = joblib.load(future_scaler_path)
        except Exception as exc:  # pragma: no cover - surfaced through /api/health
            self.error = str(exc)

    @property
    def current_ready(self) -> bool:
        return self.current_model is not None and self.current_scaler is not None

    @property
    def future_ready(self) -> bool:
        return self.future_model is not None and self.future_scaler is not None


MODELS = ModelStore()


def to_float(payload: dict[str, Any], key: str, default: float = 0.0) -> float:
    value = payload.get(key, default)
    if value in ("", None):
        return default
    return float(value)


def level_payload(label: int, kind: str) -> dict[str, Any]:
    details = AQI_LEVELS.get(label, AQI_LEVELS[5])
    return {
        "kind": kind,
        "aqi_label": label,
        "status": details["display"],
        "tone": details["tone"],
        "advice": details["advice"],
    }


def build_current_row(payload: dict[str, Any]) -> dict[str, float]:
    return {
        "co": to_float(payload, "co"),
        "no": to_float(payload, "no"),
        "no2": to_float(payload, "no2"),
        "o3": to_float(payload, "o3"),
        "so2": to_float(payload, "so2"),
        "pm2_5": to_float(payload, "pm2_5"),
        "pm10": to_float(payload, "pm10"),
        "nh3": to_float(payload, "nh3"),
        "temperature_C": to_float(payload, "temperature_C", to_float(payload, "temp", 30.0)),
        "humidity_%": to_float(payload, "humidity_%", to_float(payload, "humidity", 70.0)),
        "rain_mm": to_float(payload, "rain_mm", to_float(payload, "rain", 0.0)),
        "wind_speed_kmh": to_float(payload, "wind_speed_kmh", to_float(payload, "wind", 8.0)),
        "is_event_anomaly": to_float(payload, "is_event_anomaly", 0.0),
    }


def predict_current(payload: dict[str, Any]) -> dict[str, Any]:
    if not MODELS.current_ready:
        raise RuntimeError(MODELS.error or "Current AQI model is not ready.")

    row = build_current_row(payload)
    input_df = pd.DataFrame([row], columns=CURRENT_FEATURES)
    scaled = MODELS.current_scaler.transform(input_df)
    label = int(MODELS.current_model.predict(scaled)[0])
    result = level_payload(label, "current")
    result["features"] = row
    return result


def predict_future(payload: dict[str, Any]) -> dict[str, Any]:
    if not MODELS.future_ready:
        raise RuntimeError(MODELS.error or "Future AQI model is not ready.")

    current = payload.get("current") or payload
    history = payload.get("history") or current
    now_text = payload.get("timestamp")
    now = datetime.fromisoformat(now_text) if now_text else datetime.now()
    target = now + timedelta(hours=1)

    row = {
        "hour": target.hour,
        "month": target.month,
        "dayofweek": target.weekday(),
        "co_lag1": to_float(current, "co"),
        "no_lag1": to_float(current, "no"),
        "no2_lag1": to_float(current, "no2"),
        "o3_lag1": to_float(current, "o3"),
        "so2_lag1": to_float(current, "so2"),
        "pm2_5_lag1": to_float(current, "pm2_5"),
        "pm10_lag1": to_float(current, "pm10"),
        "nh3_lag1": to_float(current, "nh3"),
        "temperature_C_lag1": to_float(current, "temperature_C", to_float(current, "temp", 30.0)),
        "humidity_%_lag1": to_float(current, "humidity_%", to_float(current, "humidity", 70.0)),
        "rain_mm_lag1": to_float(current, "rain_mm", to_float(current, "rain", 0.0)),
        "wind_speed_kmh_lag1": to_float(current, "wind_speed_kmh", to_float(current, "wind", 8.0)),
        "pm2_5_lag2": to_float(history, "pm2_5"),
        "pm10_lag2": to_float(history, "pm10"),
        "o3_lag2": to_float(history, "o3"),
        "co_lag2": to_float(history, "co"),
    }

    input_df = pd.DataFrame([row], columns=FUTURE_FEATURES)
    scaled = MODELS.future_scaler.transform(input_df)
    label = int(MODELS.future_model.predict(scaled)[0])
    result = level_payload(label, "future")
    result["target_time"] = target.isoformat(timespec="minutes")
    result["features"] = row
    return result


class GreenAirHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/health":
            self.send_json(
                {
                    "ok": True,
                    "current_model_ready": MODELS.current_ready,
                    "future_model_ready": MODELS.future_ready,
                    "error": MODELS.error,
                }
            )
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
        except Exception as exc:
            self.send_json({"error": str(exc)}, status=400)

    def read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length).decode("utf-8")
        return json.loads(body or "{}")

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
