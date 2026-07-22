from __future__ import annotations

from datetime import datetime, timedelta
import os
from pathlib import Path
from typing import Any

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")

try:
    import joblib
    import numpy as np
    import pandas as pd
except ImportError:
    joblib = None
    np = None
    pd = None

try:
    from keras.models import load_model
except ImportError:
    try:
        from tensorflow.keras.models import load_model
    except ImportError:
        load_model = None


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

LSTM_FEATURES = [
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
    "hour",
    "month",
    "dayofweek",
    "o3_was_missing",
]

FEATURE_LABELS = {
    "co": "Carbon monoxide (CO)",
    "no": "Nitric oxide (NO)",
    "no2": "Nitrogen dioxide (NO2)",
    "o3": "Ozone (O3)",
    "so2": "Sulfur dioxide (SO2)",
    "pm2_5": "Fine particles (PM2.5)",
    "pm10": "Coarse particles (PM10)",
    "nh3": "Ammonia (NH3)",
    "temperature_C": "Temperature",
    "humidity_%": "Humidity",
    "rain_mm": "Rainfall",
    "wind_speed_kmh": "Wind speed",
}

FEATURE_LIMITS = {
    "co": 1000.0,
    "no": 8.0,
    "no2": 80.0,
    "o3": 80.0,
    "so2": 40.0,
    "pm2_5": 150.0,
    "pm10": 200.0,
    "nh3": 10.0,
    "temperature_C": 45.0,
    "humidity_%": 100.0,
    "rain_mm": 50.0,
    "wind_speed_kmh": 40.0,
}

AQI_LEVELS = {
    1: {
        "status": "Good",
        "tone": "good",
        "advice": "Air quality looks good right now. It is a comfortable time for normal outdoor activities.",
    },
    2: {
        "status": "Moderate",
        "tone": "moderate",
        "advice": "Air quality is still acceptable. Most people can continue as usual, while sensitive groups may want to take it a little easier outdoors.",
    },
    3: {
        "status": "Unhealthy for Sensitive Groups",
        "tone": "unhealthy-sensitive",
        "advice": "Air quality may start to affect sensitive groups. Consider shortening outdoor activities and wearing a mask in busy traffic areas.",
    },
    4: {
        "status": "Unhealthy",
        "tone": "unhealthy",
        "advice": "Air quality is unhealthy. It is better to reduce outdoor time, avoid intense exercise, and keep children, older adults, and respiratory-risk groups in cleaner indoor spaces when possible.",
    },
    5: {
        "status": "Very Unhealthy / Hazardous",
        "tone": "hazardous",
        "advice": "This is a high-risk air quality condition. Stay indoors if you can, close windows, and use air filtration or a protective mask when going outside is unavoidable.",
    },
}

AUDIENCE_GUIDANCE = {
    "children": [
        "Choose indoor activities when air quality becomes unhealthy.",
        "Keep outdoor play short near heavy traffic routes.",
    ],
    "older_adults": [
        "Keep outdoor trips short and take breaks when needed.",
        "Pay attention to breathing comfort, dizziness, or chest discomfort.",
    ],
    "respiratory": [
        "Keep prescribed medication or an inhaler nearby.",
        "Use a well-fitted mask and avoid peak traffic periods when possible.",
    ],
    "commuters": [
        "Pick less congested routes if your schedule allows.",
        "Consider a mask when PM2.5 or PM10 levels are elevated.",
    ],
}


class InputError(ValueError):
    pass


class ModelStore:
    def __init__(self) -> None:
        self.current_model = None
        self.current_scaler = None
        self.future_model = None
        self.future_scaler = None
        self.future_model_kind = "missing"
        self.error = ""
        self.load()

    def load(self) -> None:
        if joblib is None or pd is None or np is None:
            self.error = "Missing Python packages. Install backend/requirements.txt before running inference."
            return

        try:
            self.current_model = joblib.load(MODELS_DIR / "hcmc_rf_model.pkl")
            self.current_scaler = joblib.load(MODELS_DIR / "hcmc_scaler.pkl")
            lstm_model_path = MODELS_DIR / "best_lstm_label_regression_model.keras"
            lstm_scaler_path = MODELS_DIR / "scaler_X.pkl"
            if lstm_model_path.exists() and lstm_scaler_path.exists():
                self.future_scaler = joblib.load(lstm_scaler_path)
                if load_model is None:
                    self.error = "LSTM model files found, but TensorFlow/Keras is not installed."
                else:
                    self.future_model = load_model(lstm_model_path, compile=False)
                    self.future_model_kind = "lstm"
            else:
                future_model_path = MODELS_DIR / "hcmc_aqi_future_model.pkl"
                future_scaler_path = MODELS_DIR / "hcmc_aqi_future_scaler.pkl"
                if future_model_path.exists() and future_scaler_path.exists():
                    self.future_model = joblib.load(future_model_path)
                    self.future_scaler = joblib.load(future_scaler_path)
                    self.future_model_kind = "random_forest"
        except Exception as exc:
            self.error = str(exc)

    @property
    def current_ready(self) -> bool:
        return self.current_model is not None and self.current_scaler is not None

    @property
    def future_ready(self) -> bool:
        return self.future_model is not None and self.future_scaler is not None

    def health(self) -> dict[str, Any]:
        info = model_info()
        if self.future_model_kind == "random_forest":
            info["future_model"] = "Lag-based RandomForestClassifier for next-hour AQI forecasting"
            info["future_features"] = FUTURE_FEATURES
        elif self.future_model_kind == "missing":
            info["future_model"] = "Future AQI model not loaded"
        return {
            "ok": True,
            "current_model_ready": self.current_ready,
            "future_model_ready": self.future_ready,
            "error": self.error,
            "model_info": info,
        }


MODELS = ModelStore()


def model_info() -> dict[str, Any]:
    return {
        "project": "GreenAIr",
        "current_model": "RandomForestClassifier for current AQI classification",
        "future_model": "Stacked LSTM regression model for next-hour AQI label forecasting",
        "current_features": CURRENT_FEATURES,
        "future_features": LSTM_FEATURES,
        "output": "AQI risk level from 1 to 5",
        "demo_note": "Predictions are generated from teammate-provided trained model files. Presets are sample demo scenarios, not live sensor readings.",
    }


def to_float(payload: dict[str, Any], key: str, default: float = 0.0) -> float:
    value = payload.get(key, default)
    if value in ("", None):
        return default
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise InputError(f"{key} must be a number.") from exc
    if number < 0 and key not in ("temperature_C", "temp"):
        raise InputError(f"{key} cannot be negative.")
    return number


def build_current_row(payload: dict[str, Any]) -> dict[str, float]:
    row = {
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
    if row["humidity_%"] > 100:
        raise InputError("humidity_% cannot be greater than 100.")
    return row


def build_lstm_row(payload: dict[str, Any], moment: datetime) -> dict[str, float]:
    row = build_current_row(payload)
    return {
        "co": row["co"],
        "no": row["no"],
        "no2": row["no2"],
        "o3": row["o3"],
        "so2": row["so2"],
        "pm2_5": row["pm2_5"],
        "pm10": row["pm10"],
        "nh3": row["nh3"],
        "temperature_C": row["temperature_C"],
        "humidity_%": row["humidity_%"],
        "rain_mm": row["rain_mm"],
        "wind_speed_kmh": row["wind_speed_kmh"],
        "is_event_anomaly": row["is_event_anomaly"],
        "hour": float(moment.hour),
        "month": float(moment.month),
        "dayofweek": float(moment.weekday()),
        "o3_was_missing": to_float(payload, "o3_was_missing", 0.0),
    }


def estimate_previous_row(current: dict[str, Any], fallback: dict[str, Any], age_hours: int) -> dict[str, float]:
    source = fallback if fallback else current
    factor = max(0.72, 1 - 0.08 * age_hours)
    return {
        "co": to_float(source, "co", to_float(current, "co") * factor),
        "no": to_float(source, "no", to_float(current, "no") * factor),
        "no2": to_float(source, "no2", to_float(current, "no2") * factor),
        "o3": to_float(source, "o3", to_float(current, "o3") * factor),
        "so2": to_float(source, "so2", to_float(current, "so2") * factor),
        "pm2_5": to_float(source, "pm2_5", to_float(current, "pm2_5") * factor),
        "pm10": to_float(source, "pm10", to_float(current, "pm10") * factor),
        "nh3": to_float(source, "nh3", to_float(current, "nh3") * factor),
        "temperature_C": to_float(
            source,
            "temperature_C",
            to_float(source, "temp", to_float(current, "temperature_C", to_float(current, "temp", 30.0))),
        ),
        "humidity_%": to_float(
            source,
            "humidity_%",
            to_float(source, "humidity", to_float(current, "humidity_%", to_float(current, "humidity", 70.0))),
        ),
        "rain_mm": to_float(source, "rain_mm", to_float(source, "rain", to_float(current, "rain_mm", to_float(current, "rain", 0.0)))),
        "wind_speed_kmh": to_float(
            source,
            "wind_speed_kmh",
            to_float(source, "wind", to_float(current, "wind_speed_kmh", to_float(current, "wind", 8.0))),
        ),
        "is_event_anomaly": to_float(source, "is_event_anomaly", 0.0),
        "o3_was_missing": to_float(source, "o3_was_missing", 0.0),
    }


def coerce_label(raw_prediction: Any) -> int:
    value = float(np.asarray(raw_prediction).reshape(-1)[0])
    if 0.0 <= value <= 1.0:
        value = 1.0 + value * 4.0
    return max(1, min(5, int(round(value))))


def level_payload(label: int, kind: str) -> dict[str, Any]:
    details = AQI_LEVELS.get(label, AQI_LEVELS[5])
    return {
        "kind": kind,
        "aqi_label": label,
        "status": details["status"],
        "tone": details["tone"],
        "advice": details["advice"],
    }


def explain_features(row: dict[str, float], model: Any | None = None) -> list[dict[str, Any]]:
    normalized = []
    for key, limit in FEATURE_LIMITS.items():
        value = row.get(key)
        if value is None:
            continue
        normalized.append(
            {
                "key": key,
                "label": FEATURE_LABELS.get(key, key),
                "value": value,
                "score": min(1.0, abs(value) / limit) if limit else 0.0,
            }
        )

    if model is not None and hasattr(model, "feature_importances_"):
        importances = dict(zip(CURRENT_FEATURES, model.feature_importances_))
        for item in normalized:
            item["importance"] = float(importances.get(item["key"], 0.0))
            item["impact_score"] = item["score"] * (0.65 + item["importance"] * 4)
    else:
        for item in normalized:
            item["importance"] = 0.0
            item["impact_score"] = item["score"]

    top = sorted(normalized, key=lambda item: item["impact_score"], reverse=True)[:4]
    for item in top:
        item["message"] = explanation_message(item["key"], item["value"], item["score"])
    return top


def explanation_message(key: str, value: float, score: float) -> str:
    label = FEATURE_LABELS.get(key, key)
    if score >= 0.75:
        return f"{label} is elevated in this sample and likely raises the predicted risk."
    if score >= 0.45:
        return f"{label} is noticeable and contributes to the overall AQI classification."
    return f"{label} is part of the model input but is not extreme in this sample."


def audience_guidance(label: int) -> list[dict[str, Any]]:
    severity = max(0, label - 2)
    groups = [
        ("Children", "children"),
        ("Older adults", "older_adults"),
        ("Respiratory conditions", "respiratory"),
        ("Commuters", "commuters"),
    ]
    return [
        {
            "group": group,
            "priority": "High" if severity >= 2 else "Watch",
            "tips": AUDIENCE_GUIDANCE[key] if severity else [AUDIENCE_GUIDANCE[key][0]],
        }
        for group, key in groups
    ]


def predict_current(payload: dict[str, Any]) -> dict[str, Any]:
    if not MODELS.current_ready:
        raise RuntimeError(MODELS.error or "Current AQI model is not ready.")
    row = build_current_row(payload)
    input_df = pd.DataFrame([row], columns=CURRENT_FEATURES)
    scaled = MODELS.current_scaler.transform(input_df)
    label = int(MODELS.current_model.predict(scaled)[0])
    result = level_payload(label, "current")
    result["features"] = row
    result["explanations"] = explain_features(row, MODELS.current_model)
    result["audience_guidance"] = audience_guidance(label)
    return result


def predict_future(payload: dict[str, Any]) -> dict[str, Any]:
    if not MODELS.future_ready:
        raise RuntimeError(MODELS.error or "Future AQI model is not ready.")

    current = payload.get("current") or payload
    history = payload.get("history") or current
    now_text = payload.get("timestamp")
    now = datetime.fromisoformat(now_text.replace("Z", "+00:00")) if now_text else datetime.now()
    target = now + timedelta(hours=1)

    if MODELS.future_model_kind == "lstm":
        previous_rows = history if isinstance(history, list) else [history]
        previous_2h = estimate_previous_row(current, previous_rows[0] if previous_rows else current, 2)
        previous_1h = estimate_previous_row(current, previous_rows[-1] if previous_rows else current, 1)
        sequence_rows = [
            build_lstm_row(previous_2h, now - timedelta(hours=2)),
            build_lstm_row(previous_1h, now - timedelta(hours=1)),
            build_lstm_row(current, now),
        ]
        input_df = pd.DataFrame(sequence_rows, columns=LSTM_FEATURES)
        scaled = MODELS.future_scaler.transform(input_df.to_numpy())
        tensor = scaled.reshape(1, 3, len(LSTM_FEATURES))
        label = coerce_label(MODELS.future_model.predict(tensor, verbose=0))
        result = level_payload(label, "future")
        current_row = build_current_row(current)
        result["target_time"] = target.isoformat(timespec="minutes")
        result["features"] = sequence_rows[-1]
        result["sequence_features"] = sequence_rows
        result["explanations"] = explain_features(current_row, MODELS.current_model)
        result["audience_guidance"] = audience_guidance(label)
        return result

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
    current_row = build_current_row(current)
    result["target_time"] = target.isoformat(timespec="minutes")
    result["features"] = row
    result["explanations"] = explain_features(current_row, MODELS.current_model)
    result["audience_guidance"] = audience_guidance(label)
    return result
