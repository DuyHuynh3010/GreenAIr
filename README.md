# GreenAIr

Hackathon demo for formula-based current AQI calculation, LSTM next-hour forecasting, and health alerts in Ho Chi Minh City.

## Goal

Build a local demo website that lets users enter or load prepared air quality indicators, calculates current AQI with fixed sub-index rules, runs a trained LSTM model for future AQI level forecasting, and returns practical health guidance.

## Planned Demo Features

- Current AQI level from a fixed AQI sub-index formula
- Health warning based on predicted AQI level
- Visual dashboard for pollutant values
- Local prediction history
- Optional next-hour forecast using the teammate-provided LSTM model
- Rolling station forecast chart for the next 6 hourly AQI levels
- AI explanation cards for the strongest prediction drivers
- Audience-specific guidance for children, older adults, respiratory risk groups, and commuters
- Model transparency panel with feature and output metadata

## Model Files

The future forecast model files are expected to be placed under `backend/models/`:

- `best_lstm_label_regression_model.keras`
- `scaler_X.pkl`

The current AQI mode does not require a model file. It uses fixed pollutant sub-index breakpoints.

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
- `POST /api/predict/current` returns formula-based current AQI level, AQI score, primary pollutant, explanation drivers, and guidance.
- `POST /api/predict/future` returns next-hour AQI forecasting using a 3-step LSTM input sequence.
