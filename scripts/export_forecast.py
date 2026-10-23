"""Export the local Keras forecast and StandardScaler for lightweight deployment."""

import json
from pathlib import Path
import sys

import joblib
import keras
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.model_service import LSTM_FEATURES  # noqa: E402

models = ROOT / "backend" / "models"
model = keras.models.load_model(models / "best_lstm_regression_model.h5", compile=False)
model(np.zeros((1, 3, len(LSTM_FEATURES)), dtype=np.float32))
model.export(models / "forecast.onnx", format="onnx", verbose=False)

scaler = joblib.load(models / "scaler_x.pkl")
if scaler.n_features_in_ != len(LSTM_FEATURES):
    raise ValueError("Scaler feature count does not match the model input.")
(models / "forecast_scaler.json").write_text(
    json.dumps(
        {"features": LSTM_FEATURES, "mean": scaler.mean_.tolist(), "scale": scaler.scale_.tolist()},
        separators=(",", ":"),
    ),
    encoding="utf-8",
)
