# GreenAIr

Hackathon demo for formula-based current AQI calculation, LSTM 3-hour forecasting, and health alerts in Ho Chi Minh City.

## Goal

Build a local demo website that lets users enter or load prepared air quality indicators, calculates current AQI with fixed sub-index rules, automatically runs a trained LSTM model for 3-hour AQI level forecasting, and returns practical health guidance.

## Planned Demo Features

- Current AQI level from a fixed AQI sub-index formula
- Health warning based on predicted AQI level
- Visual dashboard for pollutant values
- Local prediction history
- Automatic 3-hour forecast using the teammate-provided LSTM model
- Station forecast chart with `-2h`, `-1h`, `Now`, `+1h`, `+2h`, and `+3h`
- AI explanation cards for the strongest prediction drivers
- Audience-specific guidance for children, older adults, respiratory risk groups, and commuters
- Model transparency panel with feature and output metadata

## Model Files

The future forecast model files are expected to be placed under `backend/models/`:

- `best_lstm_regression_model.h5`
- `scaler_x.pkl`

The current AQI mode does not require a model file. It uses fixed pollutant sub-index breakpoints.

The backend still supports the older lag-based next-hour model files as a fallback:

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

## Deploy on Vercel

The repository exports `app:app` from the root `app.py` as a WSGI entrypoint. Vercel reads `pyproject.toml` for the entrypoint and the root `requirements.txt` for dependencies. Leave the Vercel project Root Directory at the repository root, with no custom build command or output directory.

The trained model files are ignored by Git, so a GitHub deployment does not include them. `/api/predict/current` works without model files, but the 3-hour forecast requires `backend/models/best_lstm_regression_model.h5` and `backend/models/scaler_x.pkl` to be available in the deployed function. Arrange private model delivery before relying on the forecast in production. TensorFlow and the model files also count toward Vercel's Python Function bundle size limit; check the deployment build and runtime logs after adding them.

The local development server remains `backend/server.py`; Vercel uses the root WSGI entrypoint.

## Local API

- `GET /api/health` returns model readiness and model metadata.
- `POST /api/predict/current` returns formula-based current AQI level, AQI score, primary pollutant, explanation drivers, and guidance.
- `POST /api/predict/future` returns 3-hour AQI forecasting using a 3-step LSTM input sequence.
