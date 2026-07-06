"""
export_json.py
Converts data/air_quality.csv and data/history.csv into JSON files the
static web/ dashboard fetches client-side. Run this after fetch_data.py
or generate_sample_data.py (the GitHub Actions workflow runs it
automatically after every hourly fetch).

Usage:
    python scripts/export_json.py
"""

import os
import csv
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
LATEST_CSV = os.path.join(DATA_DIR, "air_quality.csv")
HISTORY_CSV = os.path.join(DATA_DIR, "history.csv")

WEB_DATA_DIR = os.path.join(BASE_DIR, "docs", "data")
LATEST_JSON = os.path.join(WEB_DATA_DIR, "latest.json")
HISTORY_JSON = os.path.join(WEB_DATA_DIR, "history.json")

NUMERIC_FIELDS = [
    "lat", "lon", "aqi", "pm2_5", "pm10", "co", "no2", "so2", "o3",
    "temperature", "humidity", "wind_speed", "pressure",
]


def read_csv_as_dicts(path):
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        rows = []
        for row in reader:
            for field in NUMERIC_FIELDS:
                if row.get(field) not in (None, ""):
                    try:
                        row[field] = float(row[field])
                    except ValueError:
                        pass
            rows.append(row)
        return rows


def main():
    os.makedirs(WEB_DATA_DIR, exist_ok=True)

    latest_rows = read_csv_as_dicts(LATEST_CSV)
    with open(LATEST_JSON, "w") as f:
        json.dump(latest_rows, f, indent=2)

    history_rows = read_csv_as_dicts(HISTORY_CSV)
    with open(HISTORY_JSON, "w") as f:
        json.dump(history_rows, f)  # no indent: this file can get large

    print(f"Exported {len(latest_rows)} latest rows -> {LATEST_JSON}")
    print(f"Exported {len(history_rows)} history rows -> {HISTORY_JSON}")


if __name__ == "__main__":
    main()
