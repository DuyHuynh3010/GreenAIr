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

let mode = "current";

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
};

const barLimits = {
  co: 1000,
  no2: 80,
  o3: 80,
  so2: 40,
  pm2_5: 150,
  pm10: 200,
  temperature_C: 45,
  "humidity_%": 100,
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
  formModeLabel.textContent = mode === "current" ? "Phan loai hien tai" : "Du bao 1 gio toi";
}

function toneClass(tone) {
  return `tone-${tone || "good"}`;
}

function updateResult(result) {
  const kind = result.kind === "future" ? "Du bao 1 gio toi" : "Chat luong hien tai";
  const time = result.target_time
    ? new Date(result.target_time).toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" })
    : "Bay gio";

  aqiNumber.textContent = result.aqi_label;
  resultKind.textContent = kind;
  resultTitle.textContent = `Muc ${result.aqi_label} - ${result.status}`;
  resultAdvice.textContent = result.advice;
  targetTime.textContent = time;
  resultBand.className = `result-band ${toneClass(result.tone)}`;
  saveHistory(result);
}

function renderBars(values) {
  pollutantBars.innerHTML = "";
  Object.entries(barLimits).forEach(([key, max]) => {
    const value = Number(values[key] || 0);
    const width = Math.max(2, Math.min(100, (value / max) * 100));
    const row = document.createElement("div");
    row.className = "bar-row";
    row.innerHTML = `
      <div class="bar-meta">
        <strong>${key}</strong>
        <span>${value}</span>
      </div>
      <div class="bar-track">
        <div class="bar-fill" style="width:${width}%"></div>
      </div>
    `;
    pollutantBars.appendChild(row);
  });
  sampleStamp.textContent = new Date().toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" });
}

function history() {
  return JSON.parse(localStorage.getItem("greenair-history") || "[]");
}

function saveHistory(result) {
  const next = [
    {
      label: result.aqi_label,
      status: result.status,
      tone: result.tone,
      kind: result.kind,
      time: new Date().toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" }),
    },
    ...history(),
  ].slice(0, 6);
  localStorage.setItem("greenair-history", JSON.stringify(next));
  renderHistory();
}

function renderHistory() {
  const items = history();
  historyList.innerHTML = items.length
    ? ""
    : `<div class="history-item"><div class="history-score tone-good">--</div><div><strong>Chua co mau</strong><span>Dang cho ket qua</span></div></div>`;

  items.forEach((item) => {
    const row = document.createElement("div");
    row.className = "history-item";
    row.innerHTML = `
      <div class="history-score ${toneClass(item.tone)}">${item.label}</div>
      <div>
        <strong>${item.status}</strong>
        <span>${item.kind === "future" ? "+1 gio" : "Hien tai"} - ${item.time}</span>
      </div>
    `;
    historyList.appendChild(row);
  });
}

async function checkHealth() {
  try {
    const response = await fetch("/api/health");
    const health = await response.json();
    currentModelState.textContent = health.current_model_ready ? "San sang" : "Thieu goi/model";
    futureModelState.textContent = health.future_model_ready ? "San sang" : "Thieu goi/model";
    if (health.error) {
      resultTitle.textContent = "Backend chua san sang";
      resultAdvice.textContent = health.error;
    }
  } catch (error) {
    currentModelState.textContent = "Mat ket noi";
    futureModelState.textContent = "Mat ket noi";
  }
}

async function submitPrediction(event) {
  event.preventDefault();
  const values = getFormData();
  renderBars(values);
  form.classList.add("is-loading");

  const endpoint = mode === "future" ? "/api/predict/future" : "/api/predict/current";
  const payload =
    mode === "future"
      ? {
          current: values,
          history: {
            co: Math.max(0, values.co * 0.9),
            o3: Math.max(0, values.o3 * 0.92),
            pm2_5: Math.max(0, values.pm2_5 * 0.88),
            pm10: Math.max(0, values.pm10 * 0.9),
          },
          timestamp: new Date().toISOString(),
        }
      : values;

  try {
    const response = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || "Prediction failed");
    updateResult(result);
  } catch (error) {
    aqiNumber.textContent = "!";
    resultKind.textContent = "Loi";
    resultTitle.textContent = "Chua chay duoc model";
    resultAdvice.textContent = error.message;
    targetTime.textContent = "--";
  } finally {
    form.classList.remove("is-loading");
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
checkHealth();
