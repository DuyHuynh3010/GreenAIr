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

let mode = "current";
let modelsReady = { current: false, future: false };

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
  const next = [
    {
      label: result.aqi_label,
      status: result.status,
      tone: result.tone,
      kind: result.kind,
      time: new Date().toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" }),
      features: submittedFeatures,
    },
    ...history(),
  ].slice(0, 8);
  localStorage.setItem("greenair-history", JSON.stringify(next));
  renderHistory();
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
});

fillForm(presets.busy);
renderHistory();
renderExplanations([]);
renderGuidance([]);
checkHealth();
