"""
SkyGuard AI v2 — Online Anomaly Detection Model
Replaces static Isolation Forest with river's Half-Space Trees (HST).

Half-Space Trees:
- Updates with EVERY incoming reading (true online learning)
- Never needs retraining — model evolves continuously
- Handles seasonal concept drift automatically
- Starts from zero data, self-calibrates within ~250 readings per station

Per-Station Adaptive Z-Score Baseline:
- Rolling 7-day (168-hour) statistical baseline per station
- Gives immediate, explainable anomaly reason
- Used alongside HST as a second opinion
"""

import os
import math
import joblib
import numpy as np
import pandas as pd
from collections import deque
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# river is the online ML library — pip install river
try:
    from river.anomaly import HalfSpaceTrees
    RIVER_AVAILABLE = True
except ImportError:
    RIVER_AVAILABLE = False
    print("[OnlineModel] WARNING: river not installed. Run: pip install river")
    print("[OnlineModel] Falling back to Z-Score only mode.")


# ── Feature keys fed to HST ──────────────────────────────────────────────────
FEATURE_KEYS = [
    "temp", "pressure", "humidity",
    "temp_diff", "pressure_diff", "humidity_diff",
    "temp_roll_std", "pressure_roll_std", "humidity_roll_std",
    "hour", "month", "day_of_year",
]

# ── WMO-No. 8 Physical Boundaries ───────────────────────────────────────────
WMO_LIMITS = {
    "temp":     (-50.0,  60.0),
    "pressure": (800.0, 1100.0),
    "humidity": (  0.0,  100.0),
}
RATE_LIMITS = {
    "temp_diff":     5.0,   # °C per 10 min
    "pressure_diff": 10.0,  # hPa per 10 min
    "humidity_diff": 30.0,  # % per 10 min
}

MODELS_DIR = Path(__file__).parent.parent.parent / "ml" / "models"


# ── Per-Station Rolling Baseline ─────────────────────────────────────────────
class StationBaseline:
    """
    Maintains a rolling window of the last `window` observations
    for a single AWS station, providing z-score anomaly scoring
    that adapts in real-time as new readings arrive.
    """

    def __init__(self, station_id: str, window: int = 168):
        self.station_id = station_id
        self.window = window  # 168 = 7 days of hourly data
        self._temp     = deque(maxlen=window)
        self._pressure = deque(maxlen=window)
        self._humidity = deque(maxlen=window)

    def update(self, temp: float, pressure: float, humidity: float):
        self._temp.append(temp)
        self._pressure.append(pressure)
        self._humidity.append(humidity)

    def z_score(self, temp: float, pressure: float, humidity: float
                ) -> Tuple[float, float, float]:
        """Return z-scores for each parameter. Higher = more anomalous."""
        def _z(val, hist):
            if len(hist) < 5:
                return 0.0
            mu  = np.mean(hist)
            std = np.std(hist) or 0.1
            return abs(val - mu) / std

        return (
            _z(temp,     self._temp),
            _z(pressure, self._pressure),
            _z(humidity, self._humidity),
        )

    def max_z(self, temp: float, pressure: float, humidity: float) -> float:
        return max(self.z_score(temp, pressure, humidity))

    @property
    def warmed_up(self) -> bool:
        return len(self._temp) >= 10


# ── Core Online Model ─────────────────────────────────────────────────────────
class OnlineAnomalyModel:
    """
    Two-layer online anomaly detection:
      Layer 1: WMO Rule Engine (instant, physics-based)
      Layer 2: Half-Space Trees per station (learns continuously)
      Layer 3: Per-station Z-Score baseline (adaptive, explainable)
    """

    # HST anomaly score threshold (0→1, higher = more anomalous)
    HST_THRESHOLD = 0.7
    # Z-score sigma threshold
    Z_THRESHOLD   = 3.5

    def __init__(self, n_trees: int = 25, height: int = 8, window_size: int = 250):
        self.n_trees     = n_trees
        self.height      = height
        self.window_size = window_size

        # One HST model per station
        self._hst_models: Dict[str, "HalfSpaceTrees"] = {}
        # One baseline tracker per station
        self._baselines: Dict[str, StationBaseline] = {}
        # Per-station reading history for feature engineering
        self._histories: Dict[str, deque] = {}

    # ── internal helpers ──────────────────────────────────────────────────────

    def _get_hst(self, station_id: str) -> Optional["HalfSpaceTrees"]:
        if not RIVER_AVAILABLE:
            return None
        if station_id not in self._hst_models:
            self._hst_models[station_id] = HalfSpaceTrees(
                n_trees=self.n_trees,
                height=self.height,
                window_size=self.window_size,
            )
        return self._hst_models[station_id]

    def _get_baseline(self, station_id: str) -> StationBaseline:
        if station_id not in self._baselines:
            self._baselines[station_id] = StationBaseline(station_id)
        return self._baselines[station_id]

    def _get_history(self, station_id: str) -> deque:
        if station_id not in self._histories:
            self._histories[station_id] = deque(maxlen=10)
        return self._histories[station_id]

    def _engineer_features(self, station_id: str,
                            temp: float, pressure: float, humidity: float,
                            timestamp: str) -> dict:
        """Build the 12-feature vector for this reading."""
        hist = list(self._get_history(station_id))

        # Rate of change vs previous reading
        if hist:
            prev = hist[-1]
            temp_diff     = temp     - prev["temp"]
            pressure_diff = pressure - prev["pressure"]
            humidity_diff = humidity - prev["humidity"]
        else:
            temp_diff = pressure_diff = humidity_diff = 0.0

        # Rolling std over last 6 readings (1 hour at 10-min intervals)
        last6 = hist[-5:] + [{"temp": temp, "pressure": pressure, "humidity": humidity}]
        temps  = [r["temp"]     for r in last6]
        presses= [r["pressure"] for r in last6]
        hums   = [r["humidity"] for r in last6]

        temp_roll_std     = float(np.std(temps))     if len(temps)  > 1 else 0.0
        pressure_roll_std = float(np.std(presses))   if len(presses)> 1 else 0.0
        humidity_roll_std = float(np.std(hums))      if len(hums)   > 1 else 0.0

        ts = pd.Timestamp(timestamp)
        return {
            "temp":             temp,
            "pressure":         pressure,
            "humidity":         humidity,
            "temp_diff":        temp_diff,
            "pressure_diff":    pressure_diff,
            "humidity_diff":    humidity_diff,
            "temp_roll_std":    temp_roll_std,
            "pressure_roll_std":pressure_roll_std,
            "humidity_roll_std":humidity_roll_std,
            "hour":             float(ts.hour),
            "month":            float(ts.month),
            "day_of_year":      float(ts.day_of_year),
        }

    # ── Rule Engine (Layer 1) ─────────────────────────────────────────────────

    @staticmethod
    def check_rules(temp: float, pressure: float, humidity: float,
                    temp_diff: float = 0.0, pressure_diff: float = 0.0,
                    humidity_diff: float = 0.0,
                    temp_roll_std: float = None,
                    pressure_roll_std: float = None,
                    humidity_roll_std: float = None) -> Optional[str]:
        """WMO-No. 8 physical rule checks. Returns violation string or None."""
        # Absolute range limits
        for param, (lo, hi), val in [
            ("Temperature",  WMO_LIMITS["temp"],     temp),
            ("Pressure",     WMO_LIMITS["pressure"], pressure),
            ("Humidity",     WMO_LIMITS["humidity"], humidity),
        ]:
            if not (lo <= val <= hi):
                return f"WMO Range Violation: {param} = {val} (valid: {lo}–{hi})"

        # Rate-of-change limits
        for param, limit, diff in [
            ("Temperature",  RATE_LIMITS["temp_diff"],     temp_diff),
            ("Pressure",     RATE_LIMITS["pressure_diff"], pressure_diff),
            ("Humidity",     RATE_LIMITS["humidity_diff"], humidity_diff),
        ]:
            if abs(diff) > limit:
                return f"Rate-of-Change Violation: {param} Δ={diff:+.1f} (max ±{limit}/10min)"

        # Stuck-sensor flatline
        for param, roll_std, val in [
            ("Temperature", temp_roll_std,     temp),
            ("Pressure",    pressure_roll_std, pressure),
            ("Humidity",    humidity_roll_std, humidity),
        ]:
            if roll_std is not None and roll_std == 0.0:
                return f"Stuck Sensor Flatline: {param} frozen at {val} for 1 hour"

        return None

    # ── Main Predict+Learn ────────────────────────────────────────────────────

    def predict_and_learn(self, station_id: str,
                          temp: float, pressure: float, humidity: float,
                          timestamp: str) -> dict:
        """
        Score a reading for anomaly AND immediately update the model.
        Returns rich result dict with scores, engine used, and explanation.
        """
        features = self._engineer_features(station_id, temp, pressure, humidity, timestamp)

        # ── Layer 1: Rules ───────────────────────────────────────────────────
        rule_violation = self.check_rules(
            temp=temp, pressure=pressure, humidity=humidity,
            temp_diff=features["temp_diff"],
            pressure_diff=features["pressure_diff"],
            humidity_diff=features["humidity_diff"],
            temp_roll_std=features["temp_roll_std"]     if self._get_history(station_id) else None,
            pressure_roll_std=features["pressure_roll_std"] if self._get_history(station_id) else None,
            humidity_roll_std=features["humidity_roll_std"] if self._get_history(station_id) else None,
        )

        if rule_violation:
            # Still learn even from anomalous readings (model should know these exist)
            self._update_state(station_id, temp, pressure, humidity, timestamp, features)
            return {
                "status":         "anomaly",
                "prediction":     -1,
                "anomaly_score":  1.0,
                "confidence":     99.0,
                "engine":         "rule_engine",
                "rule_violation": rule_violation,
                "hst_score":      None,
                "z_scores":       None,
                "features":       features,
            }

        # ── Layer 2: HST ─────────────────────────────────────────────────────
        hst = self._get_hst(station_id)
        hst_score = 0.0
        if hst is not None:
            hst_score = hst.score_one(features)
            hst.learn_one(features)     # ← real-time model update

        # ── Layer 3: Z-Score ─────────────────────────────────────────────────
        baseline = self._get_baseline(station_id)
        z_temp, z_pres, z_hum = baseline.z_score(temp, pressure, humidity)
        max_z = max(z_temp, z_pres, z_hum)
        baseline.update(temp, pressure, humidity)

        # ── Decision ─────────────────────────────────────────────────────────
        hst_flag = hst_score >= self.HST_THRESHOLD and baseline.warmed_up
        z_flag   = max_z    >= self.Z_THRESHOLD    and baseline.warmed_up
        is_anomaly = hst_flag or z_flag

        engine = "half_space_trees+zscore" if hst_flag and z_flag else \
                 "half_space_trees"         if hst_flag else \
                 "zscore"                   if z_flag   else \
                 "none"

        confidence = round(min(99.9, max(hst_score, max_z / 10.0) * 100), 1) if is_anomaly else 0.0

        self._update_state(station_id, temp, pressure, humidity, timestamp, features)

        return {
            "status":         "anomaly" if is_anomaly else "normal",
            "prediction":     -1        if is_anomaly else 1,
            "anomaly_score":  round(hst_score, 4),
            "confidence":     confidence,
            "engine":         engine,
            "rule_violation": None,
            "hst_score":      round(hst_score, 4),
            "z_scores":       {
                "temp":     round(z_temp, 2),
                "pressure": round(z_pres, 2),
                "humidity": round(z_hum, 2),
                "max":      round(max_z,  2),
            },
            "features":       {k: round(v, 4) for k, v in features.items()},
        }

    def _update_state(self, station_id, temp, pressure, humidity, timestamp, features):
        self._get_history(station_id).append({
            "station_id": station_id,
            "temp": temp, "pressure": pressure, "humidity": humidity,
            "timestamp": timestamp,
        })

    # ── Warm-up from historical CSV ───────────────────────────────────────────
    def warm_up_from_csv(self, csv_path: str, max_per_station: int = 10000):
        """
        Pre-train the online model by replaying historical data.
        The HST and baseline adapt to each station's real climate patterns
        before the first live reading arrives.
        """
        path = Path(csv_path)
        if not path.exists():
            print(f"[OnlineModel] Warm-up CSV not found at {csv_path}. Skipping warm-up.")
            return

        print(f"[OnlineModel] Warming up from {csv_path} ...")
        df = pd.read_csv(csv_path, parse_dates=["timestamp"])
        df.sort_values(["station_id", "timestamp"], inplace=True)

        total = 0
        for station_id, grp in df.groupby("station_id"):
            grp = grp.head(max_per_station)
            for _, row in grp.iterrows():
                self.predict_and_learn(
                    station_id=str(row["station_id"]),
                    temp=float(row["temp"]),
                    pressure=float(row["pressure"]),
                    humidity=float(row["humidity"]),
                    timestamp=str(row["timestamp"]),
                )
                total += 1
            print(f"  {station_id}: {len(grp):,} rows replayed ✓")

        print(f"[OnlineModel] Warm-up complete. {total:,} total readings processed.\n")

    # ── Persistence ───────────────────────────────────────────────────────────
    def save(self, path: Optional[str] = None):
        save_path = Path(path or MODELS_DIR / "online_model.pkl")
        save_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, save_path)
        print(f"[OnlineModel] Saved → {save_path}")

    @classmethod
    def load(cls, path: Optional[str] = None) -> "OnlineAnomalyModel":
        load_path = Path(path or MODELS_DIR / "online_model.pkl")
        if not load_path.exists():
            print(f"[OnlineModel] No saved model at {load_path}. Starting fresh.")
            return cls()
        model = joblib.load(load_path)
        print(f"[OnlineModel] Loaded from {load_path}")
        return model


# ── Singleton accessor ────────────────────────────────────────────────────────
_MODEL_INSTANCE: Optional[OnlineAnomalyModel] = None

def get_model() -> OnlineAnomalyModel:
    """Return the global singleton model, loading from disk if available."""
    global _MODEL_INSTANCE
    if _MODEL_INSTANCE is None:
        _MODEL_INSTANCE = OnlineAnomalyModel.load()
    return _MODEL_INSTANCE


# ── CLI: train & save ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    csv = sys.argv[1] if len(sys.argv) > 1 else "data/weather_data_real.csv"
    model = OnlineAnomalyModel()
    model.warm_up_from_csv(csv)
    model.save()
    print("Model ready.")
