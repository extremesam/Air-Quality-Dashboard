/* app.js — Air Quality Intelligence Dashboard (vanilla JS) */

const POLLUTANTS = ["pm2_5", "pm10", "co", "no2", "so2", "o3"];
const POLLUTANT_LABELS = { pm2_5: "PM2.5", pm10: "PM10", co: "CO", no2: "NO2", so2: "SO2", o3: "O3" };

let latestData = [];
let historyData = [];
let selectedCity = null;
let map, markersLayer;
let pollutantChart, historyChart, dailyChart, weeklyChart, monthlyChart;
let currentRange = "7d";

async function loadData() {
  const [latestRes, historyRes] = await Promise.all([
    fetch("data/latest.json"),
    fetch("data/history.json"),
  ]);
  latestData = await latestRes.json();
  historyData = await historyRes.json();
  historyData.forEach(r => r._date = new Date(r.timestamp));
  latestData.sort((a, b) => a.city.localeCompare(b.city));
}

function cityRow(city) {
  return latestData.find(r => r.city === city);
}

function cityHistory(city) {
  return historyData.filter(r => r.city === city).sort((a, b) => a._date - b._date);
}

function fmtTime(ts) {
  const d = new Date(ts);
  return d.toLocaleString(undefined, { hour: "2-digit", minute: "2-digit", month: "short", day: "numeric" });
}

/* ---------------------------------------------------------------------
   City selector
   ------------------------------------------------------------------- */
function populateCitySelect() {
  const select = document.getElementById("city-select");
  select.innerHTML = "";
  latestData.forEach(row => {
    const opt = document.createElement("option");
    opt.value = row.city;
    opt.textContent = row.city;
    select.appendChild(opt);
  });
  select.value = selectedCity;
  select.addEventListener("change", () => {
    selectedCity = select.value;
    renderAll();
  });
}

/* ---------------------------------------------------------------------
   Clarity strip (signature element)
   ------------------------------------------------------------------- */
function updateClarityStrip(aqi) {
  const cat = aqiCategory(aqi);
  const strip = document.getElementById("clarity-strip");
  strip.style.background =
    `linear-gradient(90deg, ${cat.color}55, ${cat.color}CC, ${cat.color}55, ${cat.color}CC)`;
}

/* ---------------------------------------------------------------------
   Hero + live card + health box
   ------------------------------------------------------------------- */
function renderHero() {
  const row = cityRow(selectedCity);
  if (!row) return;
  const cat = aqiCategory(row.aqi);

  document.getElementById("hero-city").textContent = row.city.toUpperCase();
  document.getElementById("hero-aqi").textContent = Math.round(row.aqi);
  document.getElementById("hero-aqi").style.color = cat.color;
  const catEl = document.getElementById("hero-category");
  catEl.textContent = cat.label;
  catEl.style.color = cat.color;
  document.getElementById("hero-recommendation").textContent = healthRecommendation(cat.label);
  document.getElementById("last-updated").textContent = "LAST SYNC " + fmtTime(row.timestamp).toUpperCase();

  document.getElementById("live-aqi").textContent = Math.round(row.aqi);
  document.getElementById("live-aqi").style.color = cat.color;
  document.getElementById("live-label").textContent = cat.label.toUpperCase();
  document.getElementById("live-label").style.color = cat.color;
  document.getElementById("live-timestamp").textContent = "UPDATED " + fmtTime(row.timestamp);

  document.getElementById("health-aqi").textContent = Math.round(row.aqi);
  document.getElementById("health-status").textContent = cat.label;
  document.getElementById("health-status").style.color = cat.color;
  document.getElementById("health-recommendation").textContent = healthRecommendation(cat.label);

  updateClarityStrip(row.aqi);
}

/* ---------------------------------------------------------------------
   KPI row
   ------------------------------------------------------------------- */
function renderKPIs() {
  const worst = latestData.reduce((a, b) => (b.aqi > a.aqi ? b : a));
  const best = latestData.reduce((a, b) => (b.aqi < a.aqi ? b : a));
  const avgAqi = latestData.reduce((s, r) => s + r.aqi, 0) / latestData.length;
  const highestPM25 = latestData.reduce((a, b) => (b.pm2_5 > a.pm2_5 ? b : a));
  const highestNO2 = latestData.reduce((a, b) => (b.no2 > a.no2 ? b : a));
  const current = cityRow(selectedCity);

  const kpis = [
    { label: `Current AQI (${current.city})`, value: Math.round(current.aqi) },
    { label: "Worst City Today", value: worst.city, sub: `AQI ${Math.round(worst.aqi)}` },
    { label: "Cleanest City", value: best.city, sub: `AQI ${Math.round(best.aqi)}` },
    { label: "Average AQI (all cities)", value: avgAqi.toFixed(1) },
    { label: "Highest PM2.5", value: highestPM25.city, sub: `${highestPM25.pm2_5} µg/m³` },
    { label: "Highest NO2", value: highestNO2.city, sub: `${highestNO2.no2} µg/m³` },
  ];

  const row = document.getElementById("kpi-row");
  row.innerHTML = kpis.map(k => `
    <div class="kpi">
      <div class="kpi-label">${k.label}</div>
      <div class="kpi-value">${k.value}</div>
      ${k.sub ? `<div class="kpi-sub">${k.sub}</div>` : ""}
    </div>
  `).join("");
}

/* ---------------------------------------------------------------------
   Map
   ------------------------------------------------------------------- */
function renderMap() {
  if (!map) {
    map = L.map("map", { scrollWheelZoom: false }).setView([9.0, 8.0], 6);
    L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
      attribution: '&copy; OpenStreetMap &copy; CARTO',
      maxZoom: 12,
    }).addTo(map);
    markersLayer = L.layerGroup().addTo(map);
  }
  markersLayer.clearLayers();

  latestData.forEach(row => {
    const cat = aqiCategory(row.aqi);
    const marker = L.circleMarker([row.lat, row.lon], {
      radius: row.city === selectedCity ? 14 : 10,
      color: cat.color,
      fillColor: cat.color,
      fillOpacity: 0.85,
      weight: row.city === selectedCity ? 3 : 1.5,
    }).addTo(markersLayer);

    marker.bindPopup(`
      <b>${row.city}</b><br>
      AQI: ${Math.round(row.aqi)} (${cat.label})<br>
      PM2.5: ${row.pm2_5} µg/m³ · PM10: ${row.pm10} µg/m³<br>
      CO: ${row.co} µg/m³ · NO2: ${row.no2} µg/m³<br>
      SO2: ${row.so2} µg/m³ · O3: ${row.o3} µg/m³
    `);
    marker.on("click", () => {
      selectedCity = row.city;
      document.getElementById("city-select").value = selectedCity;
      renderAll();
    });
  });

  const legend = document.getElementById("legend");
  legend.innerHTML = AQI_CATEGORIES.map(c => `
    <div class="legend-item"><span class="legend-dot" style="background:${c.color}"></span>${c.label} (${c.low}-${c.high})</div>
  `).join("");
}

/* ---------------------------------------------------------------------
   Pollutant breakdown
   ------------------------------------------------------------------- */
function renderPollutantChart() {
  const row = cityRow(selectedCity);
  const values = POLLUTANTS.map(p => row[p]);
  const ctx = document.getElementById("pollutant-chart");

  if (pollutantChart) pollutantChart.destroy();
  pollutantChart = new Chart(ctx, {
    type: "bar",
    data: {
      labels: POLLUTANTS.map(p => POLLUTANT_LABELS[p]),
      datasets: [{
        data: values,
        backgroundColor: "#4FC3D9",
        borderRadius: 2,
        barPercentage: 0.5,
      }],
    },
    options: chartBaseOptions("Concentration (µg/m³)"),
  });
}

/* ---------------------------------------------------------------------
   Weather feed
   ------------------------------------------------------------------- */
function renderWeather() {
  const row = cityRow(selectedCity);
  document.getElementById("w-temp").textContent = `${row.temperature}°C`;
  document.getElementById("w-humidity").textContent = `${row.humidity}%`;
  document.getElementById("w-wind").textContent = `${row.wind_speed} m/s`;
  document.getElementById("w-pressure").textContent = `${row.pressure} hPa`;
}

/* ---------------------------------------------------------------------
   AQI history line chart
   ------------------------------------------------------------------- */
function renderHistoryChart() {
  const hist = cityHistory(selectedCity);
  let filtered = hist;
  const now = hist.length ? hist[hist.length - 1]._date : new Date();

  if (currentRange === "24h") {
    const cutoff = new Date(now - 24 * 3600 * 1000);
    filtered = hist.filter(r => r._date >= cutoff);
  } else if (currentRange === "7d") {
    const cutoff = new Date(now - 7 * 24 * 3600 * 1000);
    filtered = hist.filter(r => r._date >= cutoff);
  }

  const ctx = document.getElementById("history-chart");
  if (historyChart) historyChart.destroy();
  historyChart = new Chart(ctx, {
    type: "line",
    data: {
      labels: filtered.map(r => fmtTime(r.timestamp)),
      datasets: [{
        data: filtered.map(r => r.aqi),
        borderColor: "#4FC3D9",
        backgroundColor: "#4FC3D922",
        fill: true,
        tension: 0.3,
        pointRadius: 0,
        borderWidth: 2,
      }],
    },
    options: chartBaseOptions("AQI", true),
  });
}

/* ---------------------------------------------------------------------
   City comparison table
   ------------------------------------------------------------------- */
function renderCompareTable() {
  const sorted = [...latestData].sort((a, b) => b.aqi - a.aqi);
  const tbody = document.querySelector("#compare-table tbody");
  tbody.innerHTML = sorted.map(row => {
    const cat = aqiCategory(row.aqi);
    return `
      <tr>
        <td>${row.city}</td>
        <td><span class="aqi-cell" style="background:${cat.color}22;color:${cat.color}">${Math.round(row.aqi)}</span></td>
        <td>${row.pm2_5}</td>
        <td>${row.pm10}</td>
        <td>${row.co}</td>
        <td>${row.no2}</td>
        <td>${row.so2}</td>
        <td>${row.o3}</td>
      </tr>
    `;
  }).join("");
}

/* ---------------------------------------------------------------------
   Historical trends: daily / weekly / monthly averages
   ------------------------------------------------------------------- */
function aggregateBy(hist, unit) {
  const buckets = {};
  hist.forEach(r => {
    const d = r._date;
    let key;
    if (unit === "daily") {
      key = d.toISOString().slice(0, 10);
    } else if (unit === "weekly") {
      const weekStart = new Date(d);
      weekStart.setDate(d.getDate() - d.getDay());
      key = weekStart.toISOString().slice(0, 10);
    } else {
      key = d.toISOString().slice(0, 7);
    }
    if (!buckets[key]) buckets[key] = [];
    buckets[key].push(r.aqi);
  });
  const keys = Object.keys(buckets).sort();
  return {
    labels: keys,
    values: keys.map(k => {
      const arr = buckets[k];
      return arr.reduce((s, v) => s + v, 0) / arr.length;
    }),
  };
}

function renderTrendCharts() {
  const hist = cityHistory(selectedCity);

  const daily = aggregateBy(hist, "daily");
  if (dailyChart) dailyChart.destroy();
  dailyChart = new Chart(document.getElementById("daily-chart"), {
    type: "bar",
    data: { labels: daily.labels, datasets: [{ data: daily.values.map(v => v.toFixed(1)), backgroundColor: "#4FC3D9", borderRadius: 2 }] },
    options: chartBaseOptions("Avg AQI"),
  });

  const weekly = aggregateBy(hist, "weekly");
  if (weeklyChart) weeklyChart.destroy();
  weeklyChart = new Chart(document.getElementById("weekly-chart"), {
    type: "bar",
    data: { labels: weekly.labels, datasets: [{ data: weekly.values.map(v => v.toFixed(1)), backgroundColor: "#F0973B", borderRadius: 2 }] },
    options: chartBaseOptions("Avg AQI"),
  });

  const monthly = aggregateBy(hist, "monthly");
  if (monthlyChart) monthlyChart.destroy();
  monthlyChart = new Chart(document.getElementById("monthly-chart"), {
    type: "bar",
    data: { labels: monthly.labels, datasets: [{ data: monthly.values.map(v => v.toFixed(1)), backgroundColor: "#B564D4", borderRadius: 2 }] },
    options: chartBaseOptions("Avg AQI"),
  });
}

/* ---------------------------------------------------------------------
   Pollution hotspots
   ------------------------------------------------------------------- */
function renderHotspots() {
  const sorted = [...latestData].sort((a, b) => b.aqi - a.aqi);
  const maxAqi = sorted[0].aqi;
  const list = document.getElementById("hotspot-list");
  list.innerHTML = sorted.map((row, i) => {
    const cat = aqiCategory(row.aqi);
    const pct = Math.max(6, (row.aqi / maxAqi) * 100);
    return `
      <div class="hotspot-row">
        <div class="hotspot-rank">${i + 1}</div>
        <div class="hotspot-city">${row.city}</div>
        <div class="hotspot-bar-track"><div class="hotspot-bar-fill" style="width:${pct}%;background:${cat.color}"></div></div>
        <div class="hotspot-aqi" style="color:${cat.color}">AQI ${Math.round(row.aqi)}</div>
      </div>
    `;
  }).join("");
}

/* ---------------------------------------------------------------------
   Chart.js shared styling (dark theme, monospace ticks)
   ------------------------------------------------------------------- */
function chartBaseOptions(yLabel, isLine = false) {
  return {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: false } },
    scales: {
      x: {
        ticks: { color: "#7C8798", font: { family: "IBM Plex Mono", size: 10 }, maxRotation: 0, autoSkip: true, maxTicksLimit: 10 },
        grid: { color: "#2A3543" },
      },
      y: {
        title: { display: true, text: yLabel, color: "#7C8798", font: { family: "IBM Plex Mono", size: 10 } },
        ticks: { color: "#7C8798", font: { family: "IBM Plex Mono", size: 10 } },
        grid: { color: "#2A3543" },
      },
    },
  };
}

/* ---------------------------------------------------------------------
   Range toggle + trend tabs event wiring
   ------------------------------------------------------------------- */
function wireControls() {
  document.getElementById("range-toggle").addEventListener("click", e => {
    if (e.target.tagName !== "BUTTON") return;
    document.querySelectorAll("#range-toggle button").forEach(b => b.classList.remove("active"));
    e.target.classList.add("active");
    currentRange = e.target.dataset.range;
    renderHistoryChart();
  });

  document.getElementById("trend-tabs").addEventListener("click", e => {
    if (e.target.tagName !== "BUTTON") return;
    document.querySelectorAll("#trend-tabs button").forEach(b => b.classList.remove("active"));
    document.querySelectorAll(".tab-panel").forEach(p => p.classList.remove("active"));
    e.target.classList.add("active");
    document.getElementById(`trend-${e.target.dataset.trend}`).classList.add("active");
  });
}

/* ---------------------------------------------------------------------
   Master render
   ------------------------------------------------------------------- */
function renderAll() {
  renderHero();
  renderKPIs();
  renderMap();
  renderPollutantChart();
  renderWeather();
  renderHistoryChart();
  renderCompareTable();
  renderTrendCharts();
  renderHotspots();
}

async function init() {
  await loadData();
  if (!latestData.length) {
    document.querySelector("main").innerHTML =
      '<p style="padding:60px 0;color:var(--text-muted);font-family:var(--font-mono);">No data available. Run scripts/generate_sample_data.py and scripts/export_json.py first.</p>';
    return;
  }
  selectedCity = latestData.reduce((a, b) => (b.aqi > a.aqi ? b : a)).city; // default to worst city
  populateCitySelect();
  wireControls();
  renderAll();
}

init();
