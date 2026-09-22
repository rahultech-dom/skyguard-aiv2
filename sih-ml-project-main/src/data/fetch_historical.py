"""
SkyGuard AI v2 — Historical Data Fetcher
Fetches ~10,000+ real hourly data points per AWS station from
Open-Meteo Historical API (free, WMO-aligned, no API key needed).

Station coverage: All 12 Indian AWS city locations.
Date range: 2022-01-01 → 2023-05-01 (~11,640 hourly observations per station)
Total dataset: ~139,680 rows across 12 stations.

Run: python src/data/fetch_historical.py
"""

import time
import requests
import pandas as pd
from datetime import datetime
from pathlib import Path

# ── 12 AWS station definitions ──────────────────────────────────────────────
STATIONS = [
    {"id": "AWS-DEL-01", "name": "Delhi",      "lat": 28.6139, "lon": 77.2090},
    {"id": "AWS-MUM-04", "name": "Mumbai",     "lat": 19.0760, "lon": 72.8777},
    {"id": "AWS-CHE-02", "name": "Chennai",    "lat": 13.0827, "lon": 80.2707},
    {"id": "AWS-KOL-03", "name": "Kolkata",    "lat": 22.5726, "lon": 88.3639},
    {"id": "AWS-BLR-05", "name": "Bengaluru",  "lat": 12.9716, "lon": 77.5946},
    {"id": "AWS-HYD-06", "name": "Hyderabad",  "lat": 17.3850, "lon": 78.4867},
    {"id": "AWS-JAI-02", "name": "Jaipur",     "lat": 26.9124, "lon": 75.7873},
    {"id": "AWS-LKO-07", "name": "Lucknow",    "lat": 26.8467, "lon": 80.9462},
    {"id": "AWS-GHY-08", "name": "Guwahati",   "lat": 26.1445, "lon": 91.7362},
    {"id": "AWS-BPL-09", "name": "Bhopal",     "lat": 23.2599, "lon": 77.4126},
    {"id": "AWS-AMD-10", "name": "Ahmedabad",  "lat": 23.0225, "lon": 72.5714},
    {"id": "AWS-SXR-11", "name": "Srinagar",   "lat": 34.0837, "lon": 74.7973},
]

# ── Open-Meteo Historical API config ────────────────────────────────────────
BASE_URL = "https://archive-api.open-meteo.com/v1/archive"
START_DATE = "2022-01-01"
END_DATE   = "2023-03-15"   # ~14.5 months = ~10,660 hourly observations

PARAMS = {
    "hourly": "temperature_2m,relative_humidity_2m,surface_pressure",
    "timezone": "Asia/Kolkata",
    "start_date": START_DATE,
    "end_date":   END_DATE,
}


def fetch_station(station: dict) -> pd.DataFrame:
    """Fetch historical hourly data for a single station."""
    params = {
        **PARAMS,
        "latitude":  station["lat"],
        "longitude": station["lon"],
    }

    print(f"  Fetching {station['name']} ({station['id']})...", end=" ", flush=True)
    resp = requests.get(BASE_URL, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    hourly = data.get("hourly", {})
    df = pd.DataFrame({
        "station_id":  station["id"],
        "station_name": station["name"],
        "timestamp":   hourly.get("time", []),
        "temp":        hourly.get("temperature_2m", []),
        "humidity":    hourly.get("relative_humidity_2m", []),
        "pressure":    hourly.get("surface_pressure", []),
    })

    # Drop any rows where Open-Meteo returned NaN (rare missing obs)
    df.dropna(inplace=True)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    print(f"{len(df):,} rows ✓")
    return df


def fetch_all_stations(output_path: str = "data/weather_data_real.csv") -> pd.DataFrame:
    """
    Fetch data for all 12 stations and save to CSV.
    Target: ~10,000+ rows per station.
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    all_dfs = []

    print(f"\n{'='*60}")
    print(f"SkyGuard v2 — Fetching Real Historical Data")
    print(f"  Period: {START_DATE} -> {END_DATE}")
    print(f"  Stations: {len(STATIONS)}")
    print(f"  Expected rows per station: ~10,600")
    print(f"{'='*60}\n")

    for i, station in enumerate(STATIONS):
        try:
            df = fetch_station(station)
            all_dfs.append(df)
        except Exception as e:
            print(f"  ✗ Failed {station['name']}: {e}")

        # Polite rate limiting — Open-Meteo allows ~600 req/min but be considerate
        if i < len(STATIONS) - 1:
            time.sleep(0.4)

    combined = pd.concat(all_dfs, ignore_index=True)
    combined.sort_values(["station_id", "timestamp"], inplace=True)
    combined.reset_index(drop=True, inplace=True)

    combined.to_csv(output_path, index=False)

    print(f"\n{'='*60}")
    print(f"✅ Dataset saved → {output_path}")
    print(f"   Total rows : {len(combined):,}")
    print(f"   Stations   : {combined['station_id'].nunique()}")
    print(f"   Columns    : {combined.columns.tolist()}")
    print(f"   Temp range : {combined['temp'].min():.1f}°C → {combined['temp'].max():.1f}°C")
    print(f"   Date range : {combined['timestamp'].min()} → {combined['timestamp'].max()}")
    print(f"{'='*60}\n")
    return combined


if __name__ == "__main__":
    fetch_all_stations("data/weather_data_real.csv")
