# 🌍 Air Quality Intelligence Dashboard

A full-stack air quality monitoring dashboard for Nigerian cities (easily
reconfigurable to any cities worldwide), built with Python, the OpenWeather
APIs, and Streamlit + Plotly + Folium.

![status](https://img.shields.io/badge/status-active-brightgreen)
![python](https://img.shields.io/badge/python-3.10%2B-blue)

## ✨ Features

| # | Feature | Description |
|---|---------|-------------|
| 1 | 🌍 Interactive AQI Map | Color-coded live markers per city (Good → Hazardous), click for full pollutant breakdown |
| 2 | 📈 Live AQI Card | Big current-AQI readout with category and last-updated time |
| 3 | 📊 Pollutant Breakdown | Bar chart of PM2.5, PM10, CO, NO2, SO2, O3 |
| 4 | 📉 AQI History | Line chart over 24h / 7d / all-time |
| 5 | 🌡️ Weather Integration | Temperature, humidity, wind speed, pressure |
| 6 | 📍 City Comparison | Sortable, color-graded comparison table |
| 7 | 🚨 Health Risk Indicator | Status + plain-language recommendation per AQI band |
| 8 | 📅 Historical Trends | Daily / weekly / monthly average AQI |
| 9 | 🚩 Pollution Hotspots | Cities ranked worst → best |
| 10 | 📊 Dashboard KPIs | Current AQI, worst/cleanest city, average AQI, highest PM2.5, highest NO2 |

## 🧱 Tech Stack

- **Python** — data collection & processing
- **OpenWeather Air Pollution API + Weather API** (free tier) — live data
- **US EPA breakpoint formulas** — convert raw concentrations into the
  standard 0–500 AQI scale with Good/Moderate/.../Hazardous categories
- **Streamlit + Plotly + Folium** — interactive web dashboard
- **GitHub** — version control / portfolio hosting

> A Power BI version can be built on top of the same `data/history.csv` —
> import it as a data source and recreate the visuals using the same KPIs.

## 📁 Folder Structure

```
Air-Quality-Dashboard/
│
├── data/
│   ├── air_quality.csv      # latest snapshot per city (overwritten hourly)
│   └── history.csv          # append-only hourly log (used for trends)
│
├── notebooks/                # optional exploration notebooks
│
├── scripts/
│   ├── aqi_utils.py          # EPA AQI formulas, city list, health guidance
│   ├── fetch_data.py         # one-shot live API pull -> CSVs
│   ├── scheduler.py          # runs fetch_data.py every hour, forever
│   └── generate_sample_data.py  # generates a realistic 7-day demo dataset
│
├── dashboard/
│   └── app.py                # Streamlit dashboard (run this)
│
├── images/
├── README.md
└── requirements.txt
```

## 🚀 Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Try it instantly with demo data (no API key needed)
```bash
python scripts/generate_sample_data.py
streamlit run dashboard/app.py
```
This generates a realistic 7-day hourly dataset for 7 Nigerian cities so
every chart, trend, and KPI is populated immediately.

### 3. Switch to live data
Get a free API key at https://openweathermap.org/api/air-pollution
(the same key also unlocks the current Weather API on the free tier).

```bash
export OPENWEATHER_API_KEY="your_key_here"
python scripts/fetch_data.py        # one-time pull
python scripts/scheduler.py         # keeps pulling every hour, forever
```

Run `scheduler.py` in the background (`tmux`/`screen`, a systemd service,
or a scheduled task on a free-tier host like Render or PythonAnywhere) so
`data/history.csv` keeps growing. After a week you'll have enough data for
meaningful daily/weekly trend charts; after a month, monthly trends too.

### 4. Launch the dashboard
```bash
streamlit run dashboard/app.py
```

## 🏙️ Cities Tracked

Lagos, Abuja, Port Harcourt, Kano, Ibadan, Kaduna, and Ogun (Ode-Remo) by
default. Add or change cities in `scripts/aqi_utils.py`:

```python
CITIES = {
    "Your City": (latitude, longitude),
    ...
}
```

## 🔬 How AQI Is Calculated

OpenWeather's Air Pollution API returns raw pollutant concentrations
(µg/m³) plus its own 1–5 qualitative index. To get the globally recognized
0–500 AQI scale (the one with Good/Moderate/Unhealthy/... categories and
green→maroon colors), this project converts each pollutant using the
official **US EPA breakpoint tables**, then takes the **maximum** of the
individual pollutant sub-indices as the overall AQI — the same method
used by WAQI and most national air-quality agencies.

## 🩺 Health Risk Categories

| AQI | Category | Color |
|---|---|---|
| 0–50 | Good | 🟢 |
| 51–100 | Moderate | 🟡 |
| 101–150 | Unhealthy for Sensitive Groups | 🟠 |
| 151–200 | Unhealthy | 🔴 |
| 201–300 | Very Unhealthy | 🟣 |
| 301–500 | Hazardous | 🟤 |

## 📊 Power BI Version (Optional)

1. Import `data/history.csv` into Power BI via **Get Data → Text/CSV**.
2. Set it to refresh from the file on a schedule (or point it at the same
   CSV synced to OneDrive/SharePoint if `scheduler.py` runs on a server).
3. Recreate the KPIs above as cards, the AQI history as a line chart, and
   the city comparison as a matrix/table visual with conditional formatting
   on the AQI column.

## 🗺️ Roadmap Ideas

- Add AQI forecasts (OpenWeather's Air Pollution API includes a forecast endpoint)
- Push alerts (email/SMS/Telegram) when a tracked city crosses "Unhealthy"
- Deploy the Streamlit app to Streamlit Community Cloud or Render for a public link
- Add authentication + saved city preferences for multi-user use

## 📄 License

MIT — free to use, modify, and build on for your own portfolio.
