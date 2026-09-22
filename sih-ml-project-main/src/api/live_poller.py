"""
SkyGuard AI v2 — Live Open-Meteo Poller
Polls Open-Meteo Current Weather API every 15 minutes for all 12 AWS stations
and feeds readings directly into the ML pipeline via /api/ingest.

Runs as an asyncio background task started at FastAPI server startup.
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional

import httpx

logger = logging.getLogger("skyguard.poller")

# ── Station registry ──────────────────────────────────────────────────────────
STATION_COORDS = [
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

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
POLL_INTERVAL  = 15 * 60   # 15 minutes in seconds


# ── Global poller state ───────────────────────────────────────────────────────
class PollerState:
    def __init__(self):
        self.enabled         : bool              = True
        self.chaos_enabled   : bool              = False
        self.last_poll_time  : Optional[str]     = None
        self.readings_ingested: int              = 0
        self.faults_injected : int               = 0
        self.source          : str               = "open-meteo"
        self.errors          : int               = 0

POLLER_STATE = PollerState()


async def fetch_station_current(client: httpx.AsyncClient, station: dict) -> Optional[dict]:
    """Fetch current conditions for one station from Open-Meteo."""
    params = {
        "latitude":  station["lat"],
        "longitude": station["lon"],
        "current":   "temperature_2m,relative_humidity_2m,surface_pressure",
        "timezone":  "Asia/Kolkata",
    }
    try:
        resp = await client.get(OPEN_METEO_URL, params=params, timeout=10.0)
        resp.raise_for_status()
        data = resp.json()
        curr = data.get("current", {})
        return {
            "station_id": station["id"],
            "temp":       float(curr.get("temperature_2m",       25.0)),
            "pressure":   float(curr.get("surface_pressure",   1010.0)),
            "humidity":   float(curr.get("relative_humidity_2m", 60.0)),
            "timestamp":  datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
    except Exception as e:
        logger.warning(f"[Poller] Failed to fetch {station['name']}: {e}")
        return None


async def poll_once(store) -> int:
    """
    One full poll cycle: fetch all 12 stations → apply chaos → ingest.
    Returns number of readings successfully ingested.
    """
    from src.api.chaos_monkey import inject_fault   # lazy import

    ingested = 0
    async with httpx.AsyncClient() as client:
        for station in STATION_COORDS:
            reading = await fetch_station_current(client, station)
            if reading is None:
                POLLER_STATE.errors += 1
                continue

            # Apply Chaos Monkey if enabled
            if POLLER_STATE.chaos_enabled:
                reading, fault_applied = inject_fault(reading)
                if fault_applied:
                    POLLER_STATE.faults_injected += 1

            # Push through the ML pipeline
            try:
                result = store.ingest_reading(reading)
                ingested += 1
                if result.get("anomaly"):
                    logger.info(
                        f"[Poller] 🚨 Anomaly on {reading['station_id']}: "
                        f"T={reading['temp']}°C  confidence={result.get('ml_output', {}).get('confidence', '?')}%"
                    )
            except Exception as e:
                logger.error(f"[Poller] Ingest error for {reading['station_id']}: {e}")
                POLLER_STATE.errors += 1

    return ingested


async def run_poller(store):
    """
    Background asyncio loop — polls Open-Meteo every POLL_INTERVAL seconds.
    Designed to be launched at FastAPI startup.
    """
    logger.info("[Poller] 🛰  Live Open-Meteo poller started (interval=15 min).")

    while True:
        if POLLER_STATE.enabled:
            try:
                n = await poll_once(store)
                POLLER_STATE.readings_ingested += n
                POLLER_STATE.last_poll_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S IST")
                logger.info(f"[Poller] ✅ Cycle complete — {n}/12 stations ingested.")
            except Exception as e:
                logger.error(f"[Poller] Cycle error: {e}")
                POLLER_STATE.errors += 1

        await asyncio.sleep(POLL_INTERVAL)
