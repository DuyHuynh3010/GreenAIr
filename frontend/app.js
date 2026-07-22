const form = document.querySelector("#predictionForm");
const currentModelState = document.querySelector("#currentModelState");
const futureModelState = document.querySelector("#futureModelState");
const currentMode = document.querySelector("#currentMode");
const futureMode = document.querySelector("#futureMode");
const formModeLabel = document.querySelector("#formModeLabel");
const resultBand = document.querySelector("#resultBand");
const aqiNumber = document.querySelector("#aqiNumber");
const resultKind = document.querySelector("#resultKind");
const resultTitle = document.querySelector("#resultTitle");
const resultAdvice = document.querySelector("#resultAdvice");
const targetTime = document.querySelector("#targetTime");
const pollutantBars = document.querySelector("#pollutantBars");
const historyList = document.querySelector("#historyList");
const clearHistory = document.querySelector("#clearHistory");
const sampleStamp = document.querySelector("#sampleStamp");
const runButton = document.querySelector("#runButton");
const explanationList = document.querySelector("#explanationList");
const guidanceList = document.querySelector("#guidanceList");
const modelInfo = document.querySelector("#modelInfo");
const aqiTrendChart = document.querySelector("#aqiTrendChart");
const trendSummary = document.querySelector("#trendSummary");
const comparisonGrid = document.querySelector("#comparisonGrid");
const comparisonSummary = document.querySelector("#comparisonSummary");
const liveStatus = document.querySelector("#liveStatus");
const liveTimestamp = document.querySelector("#liveTimestamp");
const stationName = document.querySelector("#stationName");
const fetchLiveButton = document.querySelector("#fetchLiveButton");
const autoLiveButton = document.querySelector("#autoLiveButton");
const stationSelector = document.querySelector("#stationSelector");
const stationScenario = document.querySelector("#stationScenario");
const stationNote = document.querySelector("#stationNote");

let mode = "current";
let modelsReady = { current: false, future: false };
let selectedStationIndex = 0;
let autoLiveTimer = null;
let stationForecast = [];

const presets = {
  clear: {
    co: 300,
    no: 0.4,
    no2: 8,
    o3: 22,
    so2: 3,
    pm2_5: 12,
    pm10: 22,
    nh3: 0.8,
    temperature_C: 29,
    "humidity_%": 68,
    rain_mm: 0,
    wind_speed_kmh: 12,
  },
  busy: {
    co: 650,
    no: 2.4,
    no2: 28,
    o3: 18,
    so2: 12,
    pm2_5: 58,
    pm10: 84,
    nh3: 3.2,
    temperature_C: 32,
    "humidity_%": 78,
    rain_mm: 0,
    wind_speed_kmh: 6,
  },
  alert: {
    co: 950,
    no: 5.5,
    no2: 52,
    o3: 34,
    so2: 24,
    pm2_5: 118,
    pm10: 162,
    nh3: 7.5,
    temperature_C: 34,
    "humidity_%": 82,
    rain_mm: 0,
    wind_speed_kmh: 3,
  },
  rain: {
    co: 360,
    no: 0.8,
    no2: 11,
    o3: 18,
    so2: 4,
    pm2_5: 19,
    pm10: 30,
    nh3: 1.1,
    temperature_C: 27,
    "humidity_%": 92,
    rain_mm: 8,
    wind_speed_kmh: 14,
  },
};

const liveStations = [
  {
    name: "Ben Thanh, District 1",
    scenario: "busy",
    label: "Traffic center",
    note: "A downtown traffic-heavy sample for rush-hour conditions.",
  },
  {
    name: "Saigon Hi-Tech Park, Thu Duc",
    scenario: "clear",
    label: "Open urban area",
    note: "A cleaner morning sample from a more open urban area.",
  },
  {
    name: "Binh Thanh residential area",
    scenario: "rain",
    label: "After rain",
    note: "A humid after-rain sample where particles are lower but humidity is high.",
  },
  {
    name: "Tan Binh airport corridor",
    scenario: "alert",
    label: "Pollution alert",
    note: "A high-risk sample representing dense traffic near the airport corridor.",
  },
];

const barLimits = {
  co: 1000,
  no: 8,
  no2: 80,
  o3: 80,
  so2: 40,
  pm2_5: 150,
  pm10: 200,
  nh3: 10,
  temperature_C: 45,
  "humidity_%": 100,
  rain_mm: 50,
  wind_speed_kmh: 40,
};

const featureLabels = {
  co: "CO",
  no: "NO",
  no2: "NO2",
  o3: "O3",
  so2: "SO2",
  pm2_5: "PM2.5",
  pm10: "PM10",
  nh3: "NH3",
  temperature_C: "Temp",
  "humidity_%": "Humidity",
  rain_mm: "Rain",
  wind_speed_kmh: "Wind",
};

const comparisonKeys = ["pm2_5", "pm10", "co", "no2"];

function getFormData() {
  const data = new FormData(form);
  return Object.fromEntries([...data.entries()].map(([key, value]) => [key, Number(value)]));
}

function fillForm(values) {
  Object.entries(values).forEach(([key, value]) => {
    const input = form.elements.namedItem(key);
    if (input) input.value = value;
  });
  renderBars(getFormData());
}

function jitterValue(value, ratio = 0.06) {
  const offset = value * ratio * (Math.random() - 0.5);
  return Math.max(0, Number((value + offset).toFixed(1)));
}

function buildLiveSample(station) {
  const base = presets[station.scenario];
  return Object.fromEntries(Object.entries(base).map(([key, value]) => [key, jitterValue(value)]));
}

function projectSampleForHour(baseSample, station, hourOffset) {
  const projected = { ...baseSample };
  const trafficRise = station.scenario === "busy" || station.scenario === "alert";
  const rainRelief = station.scenario === "rain";
  const cleanerArea = station.scenario === "clear";
  const drift = hourOffset - 1;

  if (trafficRise) {
    projected.pm2_5 = Number((projected.pm2_5 * (1 + drift * 0.035)).toFixed(1));
    projected.pm10 = Number((projected.pm10 * (1 + drift * 0.03)).toFixed(1));
    projected.co = Number((projected.co * (1 + drift * 0.025)).toFixed(1));
    projected.no2 = Number((projected.no2 * (1 + drift * 0.025)).toFixed(1));
  }

  if (rainRelief) {
    projected.pm2_5 = Number((projected.pm2_5 * Math.max(0.72, 1 - drift * 0.045)).toFixed(1));
    projected.pm10 = Number((projected.pm10 * Math.max(0.74, 1 - drift * 0.04)).toFixed(1));
    projected["humidity_%"] = Math.min(100, Number((projected["humidity_%"] + drift * 0.8).toFixed(1)));
  }

  if (cleanerArea) {
    projected.pm2_5 = Number((projected.pm2_5 * Math.max(0.82, 1 - drift * 0.02)).toFixed(1));
    projected.pm10 = Number((projected.pm10 * Math.max(0.84, 1 - drift * 0.018)).toFixed(1));
  }

  projected.wind_speed_kmh = Math.max(1, Number((projected.wind_speed_kmh + Math.sin(hourOffset) * 1.2).toFixed(1)));
  return projected;
}

function selectStation(index) {
  selectedStationIndex = index;
  const station = liveStations[selectedStationIndex];
  stationName.textContent = station.name;
  stationScenario.textContent = station.label;
  stationNote.textContent = station.note;
  stationForecast = [];
  renderAqiTrend();
  document.querySelectorAll(".station-button").forEach((button, buttonIndex) => {
    button.classList.toggle("active", buttonIndex === selectedStationIndex);
  });
}

function renderStationSelector() {
  stationSelector.innerHTML = "";
  liveStations.forEach((station, index) => {
    const button = document.createElement("button");
    button.className = "station-button";
    button.type = "button";
    button.innerHTML = `<strong>${station.name}</strong><span>${station.label}</span>`;
    button.addEventListener("click", () => selectStation(index));
    stationSelector.appendChild(button);
  });
  selectStation(selectedStationIndex);
}

async function fetchLiveSample({ auto = false } = {}) {
  const ready = mode === "future" ? modelsReady.future : modelsReady.current;
  if (!ready) {
    liveStatus.textContent = "Model offline";
    return;
  }

  const station = liveStations[selectedStationIndex];
  const sample = buildLiveSample(station);

  liveTimestamp.textContent = new Date().toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
  liveStatus.textContent = auto ? `Auto cycling (${mode})` : `Sample loaded (${mode})`;
  fillForm(sample);
  await runPrediction(sample);
  try {
    await generateStationForecast(sample);
  } catch (error) {
    stationForecast = [];
    trendSummary.textContent = "Forecast unavailable";
    aqiTrendChart.innerHTML = `<div class="chart-empty">${error.message}</div>`;
  }
}

function toggleAutoLive() {
  if (autoLiveTimer) {
    clearInterval(autoLiveTimer);
    autoLiveTimer = null;
    autoLiveButton.textContent = "Auto cycle: off";
    liveStatus.textContent = "Manual mode";
    return;
  }

  autoLiveButton.textContent = "Auto cycle: on";
  fetchLiveSample({ auto: true });
  autoLiveTimer = setInterval(() => {
    selectStation((selectedStationIndex + 1) % liveStations.length);
    fetchLiveSample({ auto: true });
  }, 6000);
}

async function generateStationForecast(baseSample) {
  if (!modelsReady.future) {
    stationForecast = [];
    trendSummary.textContent = "Forecast model offline";
    renderAqiTrend();
    return;
  }

  const station = liveStations[selectedStationIndex];
  const now = new Date();
  const samples = [];
  let previousSample = latestFeatureHistory(baseSample);

  trendSummary.textContent = "Forecasting...";
  aqiTrendChart.innerHTML = `<div class="chart-empty">Generating next-hour forecast for ${station.name}...</div>`;

  for (let hour = 1; hour <= 6; hour += 1) {
    const currentSample = projectSampleForHour(baseSample, station, hour);
    const timestamp = new Date(now.getTime() + (hour - 1) * 60 * 60 * 1000).toISOString();
    const response = await fetch("/api/predict/future", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ current: currentSample, history: previousSample, timestamp }),
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || "Forecast failed");
    samples.push({
      label: result.aqi_label,
      status: result.status,
      tone: result.tone,
      hourLabel: `+${hour}h`,
      time: new Date(result.target_time).toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" }),
    });
    previousSample = currentSample;
  }

  stationForecast = samples;
  renderAqiTrend();
}

function setMode(nextMode) {
  mode = nextMode;
  currentMode.classList.toggle("active", mode === "current");
  futureMode.classList.toggle("active", mode === "future");
  formModeLabel.textContent = mode === "current" ? "Current AQI classification" : "Next-hour forecast";
  runButton.disabled = mode === "current" ? !modelsReady.current : !modelsReady.future;
}

function toneClass(tone) {
  return `tone-${tone || "good"}`;
}

function formatTime(value) {
  return new Date(value).toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" });
}

function updateResult(result, submittedFeatures) {
  const kind = result.kind === "future" ? "Next-hour forecast" : "Current air quality";
  const time = result.target_time ? formatTime(result.target_time) : "Now";

  aqiNumber.textContent = result.aqi_label;
  resultKind.textContent = kind;
  resultTitle.textContent = `Level ${result.aqi_label} - ${result.status}`;
  resultAdvice.textContent = result.advice;
  targetTime.textContent = time;
  resultBand.className = `result-band ${toneClass(result.tone)}`;
  renderExplanations(result.explanations || []);
  renderGuidance(result.audience_guidance || []);
  saveHistory(result, submittedFeatures);
}

function renderBars(values) {
  pollutantBars.innerHTML = "";
  Object.entries(barLimits).forEach(([key, max]) => {
    const value = Number(values[key] || 0);
    const ratio = Math.min(1, Math.max(0, value / max));
    const row = document.createElement("div");
    row.className = "bar-row";
    row.innerHTML = `
      <div class="bar-meta">
        <strong>${featureLabels[key] || key}</strong>
        <span>${Number.isInteger(value) ? value : value.toFixed(1)}</span>
      </div>
      <div class="bar-track">
        <div class="bar-fill" style="width:${Math.max(2, ratio * 100)}%"></div>
      </div>
    `;
    pollutantBars.appendChild(row);
  });
  sampleStamp.textContent = new Date().toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" });
}

function renderExplanations(items) {
  explanationList.innerHTML = items.length
    ? ""
    : `<div class="empty-state">Run the model to see the strongest drivers.</div>`;

  items.forEach((item) => {
    const card = document.createElement("article");
    const pct = Math.round((item.score || 0) * 100);
    card.className = "explanation-card";
    card.innerHTML = `
      <div class="explanation-head">
        <strong>${item.label}</strong>
        <span>${pct}% of demo threshold</span>
      </div>
      <p>${item.message}</p>
      <div class="mini-track"><span style="width:${Math.max(3, Math.min(100, pct))}%"></span></div>
    `;
    explanationList.appendChild(card);
  });
}

function renderGuidance(groups) {
  guidanceList.innerHTML = groups.length ? "" : `<div class="empty-state">Audience guidance appears after prediction.</div>`;
  groups.forEach((item) => {
    const card = document.createElement("article");
    card.className = "guidance-card";
    card.innerHTML = `
      <div class="guidance-head">
        <strong>${item.group}</strong>
        <span>${item.priority}</span>
      </div>
      <ul>${item.tips.map((tip) => `<li>${tip}</li>`).join("")}</ul>
    `;
    guidanceList.appendChild(card);
  });
}

function renderModelInfo(info) {
  modelInfo.innerHTML = `
    <div class="model-stat">
      <span>Current model</span>
      <strong>${info.current_model}</strong>
    </div>
    <div class="model-stat">
      <span>Forecast model</span>
      <strong>${info.future_model}</strong>
    </div>
    <div class="model-stat">
      <span>Output</span>
      <strong>${info.output}</strong>
    </div>
    <p>${info.demo_note}</p>
  `;
}

function history() {
  return JSON.parse(localStorage.getItem("greenair-history") || "[]");
}

function saveHistory(result, submittedFeatures) {
  const primaryDriver = result.explanations?.[0];
  const next = [
    {
      label: result.aqi_label,
      status: result.status,
      tone: result.tone,
      kind: result.kind,
      time: new Date().toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" }),
      features: submittedFeatures,
      driver: primaryDriver
        ? {
            label: primaryDriver.label,
            value: primaryDriver.value,
            score: primaryDriver.score,
          }
        : null,
    },
    ...history(),
  ].slice(0, 8);
  localStorage.setItem("greenair-history", JSON.stringify(next));
  renderHistory();
  renderScenarioComparison();
}

function latestFeatureHistory(currentValues) {
  const previous = history().find((item) => item.features)?.features;
  return previous || {
    co: Math.max(0, currentValues.co * 0.9),
    o3: Math.max(0, currentValues.o3 * 0.92),
    pm2_5: Math.max(0, currentValues.pm2_5 * 0.88),
    pm10: Math.max(0, currentValues.pm10 * 0.9),
  };
}

function renderHistory() {
  const items = history();
  historyList.innerHTML = items.length
    ? ""
    : `<div class="history-item"><div class="history-score tone-good">--</div><div><strong>No predictions yet</strong><span>Run a scenario to start</span></div></div>`;

  items.forEach((item) => {
    const row = document.createElement("div");
    row.className = "history-item";
    row.innerHTML = `
      <div class="history-score ${toneClass(item.tone)}">${item.label}</div>
      <div>
        <strong>${item.status}</strong>
        <span>${item.kind === "future" ? "+1 hour" : "Current"} - ${item.time}</span>
        <div class="history-spark" style="--spark:${Math.max(20, item.label * 20)}%"></div>
      </div>
    `;
    historyList.appendChild(row);
  });
}

function trendDirection(samples) {
  if (samples.length < 2) return "Forecast: collecting";
  const first = samples[0].label;
  const last = samples[samples.length - 1].label;
  const delta = last - first;
  if (delta > 0) return `Forecast: up ${delta} level${delta > 1 ? "s" : ""}`;
  if (delta < 0) return `Forecast: down ${Math.abs(delta)} level${Math.abs(delta) > 1 ? "s" : ""}`;
  return "Forecast: stable";
}

function renderAqiTrend() {
  const samples = stationForecast;
  const station = liveStations[selectedStationIndex];
  if (!samples.length) {
    trendSummary.textContent = "Forecast: not loaded";
    aqiTrendChart.innerHTML = `
      <div class="chart-empty">
        Load a station sample to generate the next 6 hourly AQI predictions for ${station.name}.
      </div>
    `;
    return;
  }

  const width = 720;
  const height = 230;
  const pad = { top: 22, right: 22, bottom: 42, left: 44 };
  const plotWidth = width - pad.left - pad.right;
  const plotHeight = height - pad.top - pad.bottom;
  const xFor = (index) => pad.left + (samples.length === 1 ? plotWidth / 2 : (index / (samples.length - 1)) * plotWidth);
  const yFor = (level) => pad.top + ((5 - level) / 4) * plotHeight;
  const points = samples.map((sample, index) => `${xFor(index)},${yFor(sample.label)}`).join(" ");
  const areaPoints = `${pad.left},${pad.top + plotHeight} ${points} ${pad.left + plotWidth},${pad.top + plotHeight}`;

  trendSummary.textContent = trendDirection(samples);
  aqiTrendChart.innerHTML = `
    <svg viewBox="0 0 ${width} ${height}" role="img" aria-label="Next-hour AQI forecast for selected station">
      <defs>
        <linearGradient id="aqiLineGradient" x1="0" x2="1" y1="0" y2="0">
          <stop offset="0%" stop-color="#35e6a6" />
          <stop offset="55%" stop-color="#ffbd4a" />
          <stop offset="100%" stop-color="#ff5964" />
        </linearGradient>
        <linearGradient id="aqiAreaGradient" x1="0" x2="0" y1="0" y2="1">
          <stop offset="0%" stop-color="#35e6a6" stop-opacity="0.26" />
          <stop offset="100%" stop-color="#35e6a6" stop-opacity="0.02" />
        </linearGradient>
        <filter id="aqiGlow">
          <feGaussianBlur stdDeviation="3" result="coloredBlur" />
          <feMerge>
            <feMergeNode in="coloredBlur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>
      ${[1, 2, 3, 4, 5]
        .map((level) => {
          const y = yFor(level);
          return `
            <line class="chart-grid-line" x1="${pad.left}" y1="${y}" x2="${pad.left + plotWidth}" y2="${y}" />
            <text class="chart-axis-label" x="16" y="${y + 4}">${level}</text>
          `;
        })
        .join("")}
      <text class="chart-axis-caption" x="${pad.left}" y="18">AQI level</text>
      <polygon class="chart-area" points="${areaPoints}" />
      <polyline class="chart-line" points="${points}" filter="url(#aqiGlow)" />
      ${samples
        .map((sample, index) => {
          const x = xFor(index);
          const y = yFor(sample.label);
          return `
            <g class="chart-point-group">
              <circle class="chart-point-halo" cx="${x}" cy="${y}" r="13"></circle>
              <circle class="chart-point ${toneClass(sample.tone)}" cx="${x}" cy="${y}" r="7"></circle>
              <text class="chart-point-label" x="${x}" y="${height - 14}">${sample.hourLabel}</text>
            </g>
          `;
        })
        .join("")}
    </svg>
  `;
}

function comparisonDeltaText(item, bestLevel) {
  const delta = item.label - bestLevel;
  if (delta === 0) return "Lowest risk in this comparison";
  return `+${delta} AQI level${delta > 1 ? "s" : ""} vs lowest`;
}

function renderScenarioComparison() {
  const items = history().slice(0, 3);
  if (items.length < 2) {
    comparisonSummary.textContent = "Run at least 2 scenarios";
    comparisonGrid.innerHTML = `
      <div class="chart-empty comparison-empty">
        Run different presets or edit inputs, then click Run AI to compare scenarios here.
      </div>
    `;
    return;
  }

  const bestLevel = Math.min(...items.map((item) => item.label));
  const worstLevel = Math.max(...items.map((item) => item.label));
  comparisonSummary.textContent =
    bestLevel === worstLevel ? "Same AQI level" : `${worstLevel - bestLevel} level spread`;
  comparisonGrid.innerHTML = "";

  items.forEach((item, index) => {
    const features = item.features || {};
    const card = document.createElement("article");
    card.className = "comparison-card";
    card.innerHTML = `
      <div class="comparison-card-head">
        <div>
          <span>Scenario ${items.length - index}</span>
          <strong>${item.kind === "future" ? "Next-hour forecast" : "Current AQI"}</strong>
        </div>
        <div class="comparison-score ${toneClass(item.tone)}">${item.label}</div>
      </div>
      <div class="comparison-status">
        <strong>${item.status}</strong>
        <span>${comparisonDeltaText(item, bestLevel)}</span>
      </div>
      <div class="comparison-driver">
        <span>Top driver</span>
        <strong>${item.driver?.label || "Not available"}</strong>
      </div>
      <div class="comparison-bars">
        ${comparisonKeys
          .map((key) => {
            const value = Number(features[key] || 0);
            const width = Math.max(2, Math.min(100, (value / barLimits[key]) * 100));
            return `
              <div class="comparison-bar-row">
                <span>${featureLabels[key]}</span>
                <div class="comparison-bar-track">
                  <div class="comparison-bar-fill" style="width:${width}%"></div>
                </div>
                <strong>${Number.isInteger(value) ? value : value.toFixed(1)}</strong>
              </div>
            `;
          })
          .join("")}
      </div>
    `;
    comparisonGrid.appendChild(card);
  });
}

async function checkHealth() {
  try {
    const response = await fetch("/api/health");
    const health = await response.json();
    modelsReady = { current: health.current_model_ready, future: health.future_model_ready };
    currentModelState.textContent = health.current_model_ready ? "Ready" : "Missing";
    futureModelState.textContent = health.future_model_ready ? "Ready" : "Missing";
    if (health.model_info) renderModelInfo(health.model_info);
    if (health.error) {
      resultTitle.textContent = "Backend is not ready";
      resultAdvice.textContent = health.error;
    }
  } catch (error) {
    modelsReady = { current: false, future: false };
    currentModelState.textContent = "Offline";
    futureModelState.textContent = "Offline";
    resultTitle.textContent = "Cannot reach local backend";
    resultAdvice.textContent = "Start the server with: .\\venv\\Scripts\\python.exe backend\\server.py";
  } finally {
    setMode(mode);
  }
}

async function submitPrediction(event) {
  event.preventDefault();
  const values = getFormData();
  await runPrediction(values);
}

async function runPrediction(values) {
  renderBars(values);
  form.classList.add("is-loading");
  runButton.textContent = "Running...";

  const endpoint = mode === "future" ? "/api/predict/future" : "/api/predict/current";
  const payload =
    mode === "future"
      ? { current: values, history: latestFeatureHistory(values), timestamp: new Date().toISOString() }
      : values;

  try {
    const response = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || "Prediction failed");
    updateResult(result, values);
  } catch (error) {
    aqiNumber.textContent = "!";
    resultKind.textContent = "Error";
    resultTitle.textContent = "The model could not run";
    resultAdvice.textContent = error.message;
    targetTime.textContent = "--";
  } finally {
    form.classList.remove("is-loading");
    runButton.textContent = "Run AI";
  }
}

document.querySelectorAll(".preset-button").forEach((button) => {
  button.addEventListener("click", () => fillForm(presets[button.dataset.preset]));
});

currentMode.addEventListener("click", () => setMode("current"));
futureMode.addEventListener("click", () => setMode("future"));
form.addEventListener("submit", submitPrediction);
form.addEventListener("input", () => renderBars(getFormData()));
clearHistory.addEventListener("click", () => {
  localStorage.removeItem("greenair-history");
  renderHistory();
  renderScenarioComparison();
});
fetchLiveButton.addEventListener("click", () => fetchLiveSample());
autoLiveButton.addEventListener("click", toggleAutoLive);

fillForm(presets.busy);
renderStationSelector();
renderHistory();
renderAqiTrend();
renderScenarioComparison();
renderExplanations([]);
renderGuidance([]);
checkHealth();
