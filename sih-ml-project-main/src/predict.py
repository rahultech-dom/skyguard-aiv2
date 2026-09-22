"""
SkyGuard AI v2 — Unified Predict Interface
Bridges the existing API contract to the new OnlineAnomalyModel.
Old signature preserved for backward compatibility.
"""

from src.model.online_model import get_model


def predict_anomaly_with_history(current_reading: dict,
                                  history_readings=None) -> dict:
    """
    Main prediction entry point — identical signature to v1 predict.py
    but now uses Half-Space Trees + per-station Z-score instead of
    frozen Isolation Forest.

    The model learns from this reading automatically after scoring it.
    """
    model = get_model()
    station_id = current_reading.get("station_id", "AWS-DEL-01")
    temp       = float(current_reading.get("temp",      25.0))
    pressure   = float(current_reading.get("pressure", 1010.0))
    humidity   = float(current_reading.get("humidity",   60.0))
    timestamp  = str(current_reading.get("timestamp",  "2026-01-01 00:00:00"))

    return model.predict_and_learn(
        station_id=station_id,
        temp=temp,
        pressure=pressure,
        humidity=humidity,
        timestamp=timestamp,
    )


def predict_anomaly(temp: float, pressure: float, humidity: float,
                    timestamp=None) -> dict:
    """Simple 3-param wrapper for backward compatibility."""
    import pandas as pd
    ts = str(timestamp) if timestamp is not None else str(pd.Timestamp.now())
    return predict_anomaly_with_history({
        "station_id": "AWS-DEL-01",
        "temp": temp,
        "pressure": pressure,
        "humidity": humidity,
        "timestamp": ts,
    })
