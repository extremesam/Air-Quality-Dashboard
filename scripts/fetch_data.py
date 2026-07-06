"""
fetch_data.py
Pulls live air pollution + weather data for every city in CITIES from the
OpenWeather APIs, computes standard EPA-style AQI, and writes:
  - data/air_quality.csv  -> latest snapshot per city (overwritten each run)
  - data/history.csv      -> append-only log used for trend charts

Usage:
    export OPENWEATHER_API_KEY="your_key_here"
    python scripts/fetch_data.py

Get a free API key at: https://openweathermap.org/api/air-pollution
(Free tier covers both the Air Pollution API and current Weather API.)
"""

import os
import csv
import sys
import datetime
import requests

sys.path.append(os.path.dirname(__file__))
from aqi_utils import CITIES, overall_aqi, aqi_category  # noqa: E402

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
LATEST_CSV = os.path.join(DATA_DIR, "air_quality.csv")
HISTORY_CSV = os.path.join(DATA_DIR, "history.csv")

AIR_POLLUTION_URL = "https://api.openweathermap.org/data/2.5/air_pollution"
WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"

FIELDNAMES = [
    "timestamp", "city", "lat", "lon",
    "aqi", "category",
    "pm2_5", "pm10", "co", "no2", "so2", "o3",
    "temperature", "humidity", "wind_speed", "pressure",
]


def fetch_city(city, lat, lon, api_key):
    pollution_resp = requests.get(
        AIR_POLLUTION_URL, params={"lat": lat, "lon": lon, "appid": api_key}, timeout=15
    )
    pollution_resp.raise_for_status()
    pollution = pollution_resp.json()["list"][0]["components"]

    weather_resp = requests.get(
        WEATHER_URL,
        params={"lat": lat, "lon": lon, "appid": api_key, "units": "metric"},
        timeout=15,
    )
    weather_resp.raise_for_status()
    weather = weather_resp.json()

    aqi = overall_aqi(
        pm25=pollution.get("pm2_5"),
        pm10=pollution.get("pm10"),
        co=pollution.get("co"),
        no2=pollution.get("no2"),
        so2=pollution.get("so2"),
        o3=pollution.get("o3"),
    )
    label, _, _ = aqi_category(aqi)

    return {
        "timestamp": datetime.datetime.utcnow().isoformat(timespec="seconds"),
        "city": city,
        "lat": lat,
        "lon": lon,
        "aqi": aqi,
        "category": label,
        "pm2_5": pollution.get("pm2_5"),
        "pm10": pollution.get("pm10"),
        "co": pollution.get("co"),
        "no2": pollution.get("no2"),
        "so2": pollution.get("so2"),
        "o3": pollution.get("o3"),
        "temperature": weather.get("main", {}).get("temp"),
        "humidity": weather.get("main", {}).get("humidity"),
        "wind_speed": weather.get("wind", {}).get("speed"),
        "pressure": weather.get("main", {}).get("pressure"),
    }


def write_latest(rows):
    with open(LATEST_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def append_history(rows):
    file_exists = os.path.isfile(HISTORY_CSV)
    with open(HISTORY_CSV, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if not file_exists:
            writer.writeheader()
        writer.writerows(rows)


def main():
    api_key = os.environ.get("OPENWEATHER_API_KEY")
    if not api_key:
        print("ERROR: Set the OPENWEATHER_API_KEY environment variable first.")
        print('  export OPENWEATHER_API_KEY="your_key_here"')
        sys.exit(1)

    os.makedirs(DATA_DIR, exist_ok=True)
    rows = []
    for city, (lat, lon) in CITIES.items():
        try:
            row = fetch_city(city, lat, lon, api_key)
            rows.append(row)
            print(f"[OK] {city}: AQI {row['aqi']} ({row['category']})")
        except Exception as exc:
            print(f"[FAIL] {city}: {exc}")

    if rows:
        write_latest(rows)
        append_history(rows)
        print(f"\nSaved {len(rows)} city readings -> {LATEST_CSV}")
        print(f"Appended to history -> {HISTORY_CSV}")


if __name__ == "__main__":
    main()
