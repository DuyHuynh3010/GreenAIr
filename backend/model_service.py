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

AQI_BREAKPOINTS = {
    "pm2_5": [
        (0.0, 12.0, 0, 50),
        (12.1, 35.4, 51, 100),
        (35.5, 55.4, 101, 150),
        (55.5, 150.4, 151, 200),
        (150.5, 250.4, 201, 300),
        (250.5, 500.4, 301, 500),
    ],
    "pm10": [
        (0.0, 54.0, 0, 50),
        (55.0, 154.0, 51, 100),
        (155.0, 254.0, 101, 150),
        (255.0, 354.0, 151, 200),
        (355.0, 424.0, 201, 300),
        (425.0, 604.0, 301, 500),
    ],
    "o3": [
        (0.0, 54.0, 0, 50),
        (55.0, 70.0, 51, 100),
        (71.0, 85.0, 101, 150),
        (86.0, 105.0, 151, 200),
        (106.0, 200.0, 201, 300),
    ],
    "no2": [
        (0.0, 53.0, 0, 50),
        (54.0, 100.0, 51, 100),
        (101.0, 360.0, 101, 150),
        (361.0, 649.0, 151, 200),
        (650.0, 1249.0, 201, 300),
        (1250.0, 2049.0, 301, 500),
    ],
    "so2": [
        (0.0, 35.0, 0, 50),
        (36.0, 75.0, 51, 100),
        (76.0, 185.0, 101, 150),
        (186.0, 304.0, 151, 200),
        (305.0, 604.0, 201, 300),
        (605.0, 1004.0, 301, 500),
    ],
    "co": [
        (0.0, 5000.0, 0, 50),
        (5001.0, 10000.0, 51, 100),
        (10001.0, 15000.0, 101, 150),
        (15001.0, 30000.0, 151, 200),
        (30001.0, 50000.0, 201, 300),
        (50001.0, 90000.0, 301, 500),
    ],
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

        errors = []
        try:
            current_model_path = MODELS_DIR / "hcmc_rf_model.pkl"
            current_scaler_path = MODELS_DIR / "hcmc_scaler.pkl"
            if current_model_path.exists() and current_scaler_path.exists():
                self.current_model = joblib.load(current_model_path)
                self.current_scaler = joblib.load(current_scaler_path)
        except Exception as exc:
            errors.append(f"Optional current model was not loaded: {exc}")

        try:
            lstm_model_path = MODELS_DIR / "best_lstm_regression_model.h5"
            lstm_scaler_path = MODELS_DIR / "scaler_x.pkl"
            if not lstm_model_path.exists():
                lstm_model_path = MODELS_DIR / "best_lstm_label_regression_model.keras"
            if not lstm_scaler_path.exists():
                lstm_scaler_path = MODELS_DIR / "scaler_X.pkl"
            if lstm_model_path.exists() and lstm_scaler_path.exists():
                self.future_scaler = joblib.load(lstm_scaler_path)
                if load_model is None:
                    errors.append("LSTM model files found, but TensorFlow/Keras is not installed.")
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
            errors.append(str(exc))

        self.error = " | ".join(errors)

    @property
    def current_ready(self) -> bool:
        return joblib is not None and pd is not None and np is not None

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
        "current_model": "Fixed AQI sub-index formula for current air quality",
        "future_model": "Stacked LSTM regression model for 3-hour AQI label forecasting",
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
    return max(1, min(5, int(round(coerce_level_value(raw_prediction)))))


def coerce_level_value(raw_prediction: Any) -> float:
    value = float(np.asarray(raw_prediction).reshape(-1)[0])
    if 0.0 <= value <= 1.0:
        value = 1.0 + value * 4.0
    return max(1.0, min(5.0, value))


def coerce_labels(raw_prediction: Any) -> list[int]:
    values = np.asarray(raw_prediction).reshape(-1)
    return [coerce_label(value) for value in values]


def coerce_level_values(raw_prediction: Any) -> list[float]:
    values = np.asarray(raw_prediction).reshape(-1)
    return [round(coerce_level_value(value), 2) for value in values]


def interpolate_aqi(value: float, breakpoints: list[tuple[float, float, int, int]]) -> int:
    for conc_low, conc_high, index_low, index_high in breakpoints:
        if conc_low <= value <= conc_high:
            score = ((index_high - index_low) / (conc_high - conc_low)) * (value - conc_low) + index_low
            return int(round(score))
    if value < breakpoints[0][0]:
        return breakpoints[0][2]
    return breakpoints[-1][3]


def label_from_aqi_score(score: int) -> int:
    if score <= 50:
        return 1
    if score <= 100:
        return 2
    if score <= 150:
        return 3
    if score <= 200:
        return 4
    return 5


def calculate_current_aqi(row: dict[str, float]) -> dict[str, Any]:
    sub_indexes = [
        {
            "key": key,
            "label": FEATURE_LABELS.get(key, key),
            "value": row[key],
            "score": interpolate_aqi(row[key], breakpoints),
        }
        for key, breakpoints in AQI_BREAKPOINTS.items()
        if key in row
    ]
    primary = max(sub_indexes, key=lambda item: item["score"])
    return {
        "score": primary["score"],
        "label": label_from_aqi_score(primary["score"]),
        "primary_pollutant": primary["label"],
        "sub_indexes": sub_indexes,
    }


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
        raise RuntimeError(MODELS.error or "Current AQI calculator is not ready.")
    row = build_current_row(payload)
    formula = calculate_current_aqi(row)
    label = formula["label"]
    result = level_payload(label, "current")
    result["features"] = row
    result["aqi_score"] = formula["score"]
    result["primary_pollutant"] = formula["primary_pollutant"]
    result["sub_indexes"] = formula["sub_indexes"]
    result["explanations"] = explain_features(row)
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
        raw_prediction = MODELS.future_model.predict(tensor, verbose=0)
        labels = coerce_labels(raw_prediction)
        level_values = coerce_level_values(raw_prediction)
        label = labels[0]
        result = level_payload(label, "future")
        current_row = build_current_row(current)
        result["target_time"] = target.isoformat(timespec="minutes")
        result["features"] = sequence_rows[-1]
        result["sequence_features"] = sequence_rows
        result["forecast_points"] = [
            {
                "offset_hours": index + 1,
                "target_time": (now + timedelta(hours=index + 1)).isoformat(timespec="minutes"),
                "aqi_label": future_label,
                "aqi_value": level_values[index],
                "status": AQI_LEVELS[future_label]["status"],
                "tone": AQI_LEVELS[future_label]["tone"],
            }
            for index, future_label in enumerate(labels[:3])
        ]
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
