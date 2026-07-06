"""
generate_sample_data.py
Generates a realistic 7-day, hourly synthetic dataset so the dashboard
can be demoed immediately without waiting on a live API / scheduler.
Run this once to populate data/history.csv and data/air_quality.csv.

    python scripts/generate_sample_data.py

Once you have a real OPENWEATHER_API_KEY, run scripts/scheduler.py and
it will keep appending real rows to the same history.csv.
"""

import os
import csv
import random
import datetime
import sys

sys.path.append(os.path.dirname(__file__))
from aqi_utils import CITIES, overall_aqi, aqi_category  # noqa: E402

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
LATEST_CSV = os.path.join(DATA_DIR, "air_quality.csv")
HISTORY_CSV = os.path.join(DATA_DIR, "history.csv")

FIELDNAMES = [
    "timestamp", "city", "lat", "lon",
    "aqi", "category",
    "pm2_5", "pm10", "co", "no2", "so2", "o3",
    "temperature", "humidity", "wind_speed", "pressure",
]

# Rough baseline pollution levels per city (ug/m3 for PM2.5), used as a
# random-walk anchor so each city has a distinct, plausible personality.
CITY_BASELINES = {
    "Lagos": 32,
    "Abuja": 18,
    "Port Harcourt": 45,
    "Kano": 28,
    "Ibadan": 24,
    "Kaduna": 26,
    "Ogun (Ode-Remo)": 20,
}

random.seed(42)


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def generate_series(city, lat, lon, hours=24 * 7):
    rows = []
    baseline = CITY_BASELINES.get(city, 25)
    pm25 = baseline
    now = datetime.datetime.utcnow()
    start = now - datetime.timedelta(hours=hours)

    for h in range(hours):
        ts = start + datetime.timedelta(hours=h)
        hour_of_day = ts.hour

        # Traffic-driven diurnal pattern: peaks ~8am and ~7pm
        rush_boost = 8 * (
            max(0, 1 - abs(hour_of_day - 8) / 3) + max(0, 1 - abs(hour_of_day - 19) / 3)
        )
        # Slow random walk + daily rush pattern + small noise
        pm25 += random.uniform(-2.5, 2.5)
        pm25 = clamp(0.6 * pm25 + 0.4 * baseline, 5, 180)
        pm25_reading = clamp(pm25 + rush_boost + random.uniform(-3, 3), 3, 220)

        pm10_reading = clamp(pm25_reading * random.uniform(1.4, 1.9), 5, 350)
        co_reading = clamp(300 + pm25_reading * random.uniform(8, 14), 100, 6000)
        no2_reading = clamp(10 + pm25_reading * random.uniform(0.6, 1.1), 2, 200)
        so2_reading = clamp(5 + pm25_reading * random.uniform(0.2, 0.5), 1, 120)
        o3_reading = clamp(40 + random.uniform(-15, 25) - pm25_reading * 0.1, 5, 160)

        aqi = overall_aqi(
            pm25=pm25_reading, pm10=pm10_reading, co=co_reading,
            no2=no2_reading, so2=so2_reading, o3=o3_reading,
        )
        label, _, _ = aqi_category(aqi)

        temp = 27 + 5 * random.random() - 2 * (abs(hour_of_day - 15) / 12)
        humidity = clamp(60 + random.uniform(-15, 20), 30, 95)
        wind = clamp(random.uniform(1, 6), 0.5, 12)
        pressure = clamp(1010 + random.uniform(-4, 4), 995, 1025)

        rows.append({
            "timestamp": ts.isoformat(timespec="seconds"),
            "city": city,
            "lat": lat,
            "lon": lon,
            "aqi": aqi,
            "category": label,
            "pm2_5": round(pm25_reading, 1),
            "pm10": round(pm10_reading, 1),
            "co": round(co_reading, 1),
            "no2": round(no2_reading, 1),
            "so2": round(so2_reading, 1),
            "o3": round(o3_reading, 1),
            "temperature": round(temp, 1),
            "humidity": round(humidity, 1),
            "wind_speed": round(wind, 1),
            "pressure": round(pressure, 1),
        })
    return rows


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    all_rows = []
    for city, (lat, lon) in CITIES.items():
        all_rows.extend(generate_series(city, lat, lon))

    all_rows.sort(key=lambda r: r["timestamp"])

    with open(HISTORY_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(all_rows)

    # Latest snapshot = last row per city
    latest_by_city = {}
    for row in all_rows:
        latest_by_city[row["city"]] = row
    with open(LATEST_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(latest_by_city.values())

    print(f"Generated {len(all_rows)} rows across {len(CITIES)} cities.")
    print(f"-> {HISTORY_CSV}")
    print(f"-> {LATEST_CSV}")


if __name__ == "__main__":
    main()
