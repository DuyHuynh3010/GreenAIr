# GreenAIr

Hackathon demo for AI-assisted air quality classification and alerts in Ho Chi Minh City.

## Goal

Build a local demo website that lets users enter air quality indicators, runs a trained machine learning model, and returns an AQI classification with practical health guidance.

## Planned Demo Features

- AQI classification from model inputs
- Health warning based on predicted AQI level
- Visual dashboard for pollutant values
- Local prediction history
- Optional next-hour forecast using lag-based model files

## Model Files

The trained model files are expected to be placed under `backend/models/`:

- `hcmc_rf_model.pkl`
- `hcmc_scaler.pkl`
- `hcmc_aqi_future_model.pkl`
- `hcmc_aqi_future_scaler.pkl`

