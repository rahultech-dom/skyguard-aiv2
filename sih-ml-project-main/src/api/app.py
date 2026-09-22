"""
SkyGuard AI v2 — FastAPI Backend
Adds:
  - Startup warm-up of OnlineAnomalyModel from real historical data
  - Background live-poller task (Open-Meteo, every 15 min)
  - /api/live-feed endpoint
  - /api/chaos/toggle endpoint
"""

import asyncio
import logging
import os
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("skyguard")

# ── Resilient state store import ──────────────────────────────────────────────
try:
    from src.api.state_store import STORE
    from src.api.live_poller import run_poller, POLLER_STATE
    from src.model.online_model import get_model
except ImportError:
    from api.state_store import STORE
    from api.live_poller import run_poller, POLLER_STATE
    from model.online_model import get_model

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="SkyGuard AI v2 — Weather Intelligence API",
    description=(
        "Real-time online anomaly detection (Half-Space Trees) + "
        "LangGraph GenAI pipeline for India's AWS network. "
        "Live data via Open-Meteo. No frozen models."
    ),
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Startup: warm up model, then launch poller ────────────────────────────────
@app.on_event("startup")
async def startup():
    logger.info("SkyGuard v2 starting up...")

    # Warm up the online model from real historical data
    model = get_model()
    csv_candidates = [
        "data/weather_data_real.csv",
        "ml/data/weather_data_real.csv",
        str(Path(__file__).parent.parent.parent / "data" / "weather_data_real.csv"),
    ]
    csv_path = next((p for p in csv_candidates if Path(p).exists()), None)

    if csv_path:
        logger.info(f"Warming up online model from {csv_path} ...")
        await asyncio.get_event_loop().run_in_executor(
            None, model.warm_up_from_csv, csv_path
        )
        logger.info("Model warm-up complete.")
    else:
        logger.warning(
            "weather_data_real.csv not found. "
            "Run: python src/data/fetch_historical.py  to download it. "
            "Model will self-calibrate from live Open-Meteo data."
        )

    # Launch background poller
    asyncio.create_task(run_poller(STORE))
    logger.info("Live Open-Meteo poller launched.")


# ── Request models ────────────────────────────────────────────────────────────
class ObservationIngestRequest(BaseModel):
    station_id: str  = Field(...,    example="AWS-DEL-01")
    temp:       float = Field(...,   example=24.6)
    pressure:   float = Field(...,   example=1012.4)
    humidity:   float = Field(...,   example=68.0)
    timestamp:  Optional[str] = Field(None)

class SimulateAnomalyRequest(BaseModel):
    station_id:   Optional[str] = Field("AWS-DEL-01")
    anomaly_type: Optional[str] = Field("spike")

# ── Endpoints (all original + 2 new) ─────────────────────────────────────────
@app.get("/")
def root():
    return {
        "service": "SkyGuard AI v2 — Real-Time Anomaly Detection",
        "model":   "Half-Space Trees (online learning)",
        "source":  "Open-Meteo Live Weather API",
        "docs":    "/docs",
        "version": "2.0.0",
    }

@app.get("/health")
def health():
    return {
        "status":          "healthy",
        "stations":        len(STORE.stations),
        "live_source":     POLLER_STATE.source,
        "last_poll":       POLLER_STATE.last_poll_time,
        "chaos_enabled":   POLLER_STATE.chaos_enabled,
    }

@app.get("/api/stations")
def get_stations():
    return STORE.get_stations()

@app.get("/api/stations/{station_id}/series")
def get_station_series(station_id: str):
    series = STORE.get_station_series(station_id)
    if not series:
        raise HTTPException(404, f"Station '{station_id}' not found.")
    return series

@app.get("/api/stats")
def get_stats():
    return STORE.get_stats()

@app.get("/api/anomalies")
def get_anomalies():
    return STORE.get_anomalies()

@app.get("/api/anomalies/{anomaly_id}")
def get_anomaly_detail(anomaly_id: str):
    detail = STORE.get_anomaly_detail(anomaly_id)
    if not detail:
        raise HTTPException(404, f"Anomaly '{anomaly_id}' not found.")
    return detail

@app.post("/api/ingest")
def ingest(payload: ObservationIngestRequest):
    return STORE.ingest_reading(payload.model_dump())

@app.post("/api/simulate-anomaly")
def simulate(payload: Optional[SimulateAnomalyRequest] = Body(default=None)):
    station_id   = payload.station_id   if payload else "AWS-DEL-01"
    anomaly_type = payload.anomaly_type if payload else "spike"
    return STORE.simulate_anomaly(station_id=station_id, anomaly_type=anomaly_type)

# ── NEW: Live Feed Status ─────────────────────────────────────────────────────
@app.get("/api/live-feed")
def live_feed_status():
    """Returns current state of the live Open-Meteo poller and Chaos Monkey."""
    return {
        "source":            POLLER_STATE.source,
        "enabled":           POLLER_STATE.enabled,
        "last_poll":         POLLER_STATE.last_poll_time,
        "poll_interval_sec": 900,
        "readings_ingested": POLLER_STATE.readings_ingested,
        "chaos_enabled":     POLLER_STATE.chaos_enabled,
        "faults_injected":   POLLER_STATE.faults_injected,
        "errors":            POLLER_STATE.errors,
    }

# ── NEW: Chaos Toggle ─────────────────────────────────────────────────────────
@app.post("/api/chaos/toggle")
def chaos_toggle(enable: Optional[bool] = Body(default=None, embed=True)):
    """Toggle Chaos Monkey fault injection on/off."""
    if enable is None:
        POLLER_STATE.chaos_enabled = not POLLER_STATE.chaos_enabled
    else:
        POLLER_STATE.chaos_enabled = bool(enable)
    return {
        "chaos_enabled": POLLER_STATE.chaos_enabled,
        "message": f"Chaos Monkey {'ENABLED 🐒' if POLLER_STATE.chaos_enabled else 'DISABLED ✅'}",
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
