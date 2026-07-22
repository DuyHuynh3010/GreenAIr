# GreenAIr

Hackathon demo for AI-assisted air quality classification and alerts in Ho Chi Minh City.

## Goal

Build a local demo website that lets users enter air quality indicators, runs a trained machine learning model, and returns an AQI classification with practical health guidance.

## Planned Demo Features

- AQI classification from model inputs
- Health warning based on predicted AQI level
- Visual dashboard for pollutant values
- Local prediction history
- Optional next-hour forecast using the teammate-provided LSTM model
- AI explanation cards for the strongest prediction drivers
- Audience-specific guidance for children, older adults, respiratory risk groups, and commuters
- Model transparency panel with feature and output metadata

## Model Files

The trained model files are expected to be placed under `backend/models/`:

- `hcmc_rf_model.pkl`
- `hcmc_scaler.pkl`
- `best_lstm_label_regression_model.keras`
- `scaler_X.pkl`

The backend still supports the older lag-based future model files as a fallback:

- `hcmc_aqi_future_model.pkl`
- `hcmc_aqi_future_scaler.pkl`

## Run Locally

```powershell
python -m venv venv
.\venv\Scripts\python.exe -m pip install -r backend\requirements.txt
.\venv\Scripts\python.exe backend\server.py
```

Then open:

```text
http://127.0.0.1:8000
```

## Local API

- `GET /api/health` returns model readiness and model metadata.
- `POST /api/predict/current` returns current AQI classification, explanation drivers, and guidance.
- `POST /api/predict/future` returns next-hour AQI forecasting using a 3-step LSTM input sequence.
