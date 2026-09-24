"""
SkyGuard AI — In-Memory Streaming Store & State Manager
SIH 2026 Problem Statement 26073

Maintains in-memory ring buffers for AWS station telemetry, 60-minute sliding windows,
network KPIs, and coordinates the ML Hybrid Engine + LangGraph GenAI pipeline.
"""

import math
import random
import uuid
from collections import deque
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

# Resilient imports for standalone or package execution
try:
    from src.predict import predict_anomaly_with_history
    from src.pipeline.graph import process_flagged_reading
    from src.pipeline.tools import get_station_name
except ImportError:
    try:
        from predict import predict_anomaly_with_history
        from pipeline.graph import process_flagged_reading
        from pipeline.tools import get_station_name
    except ImportError:
        from ml.src.predict import predict_anomaly_with_history
        from ml.src.pipeline.graph import process_flagged_reading
        from ml.src.pipeline.tools import get_station_name

# Initial 12 AWS Stations across India
DEFAULT_STATIONS = [
    {"id": "AWS-DEL-01", "name": "Delhi", "state": "Delhi", "x": 46, "y": 33, "status": "healthy", "temp": 24.6, "pressure": 1012.4, "humidity": 68.0, "health": 98},
    {"id": "AWS-MUM-04", "name": "Mumbai", "state": "Maharashtra", "x": 27, "y": 60, "status": "warning", "temp": 29.8, "pressure": 1008.9, "humidity": 78.0, "health": 82},
    {"id": "AWS-CHE-02", "name": "Chennai", "state": "Tamil Nadu", "x": 47, "y": 82, "status": "healthy", "temp": 31.2, "pressure": 1006.7, "humidity": 74.0, "health": 95},
    {"id": "AWS-KOL-03", "name": "Kolkata", "state": "West Bengal", "x": 68, "y": 52, "status": "healthy", "temp": 30.1, "pressure": 1005.2, "humidity": 81.0, "health": 93},
    {"id": "AWS-BLR-05", "name": "Bengaluru", "state": "Karnataka", "x": 39, "y": 76, "status": "healthy", "temp": 23.9, "pressure": 1013.6, "humidity": 61.0, "health": 97},
    {"id": "AWS-HYD-06", "name": "Hyderabad", "state": "Telangana", "x": 42, "y": 66, "status": "healthy", "temp": 27.4, "pressure": 1010.8, "humidity": 55.0, "health": 96},
    {"id": "AWS-JAI-02", "name": "Jaipur", "state": "Rajasthan", "x": 36, "y": 35, "status": "anomaly", "temp": 24.9, "pressure": 1008.2, "humidity": 41.0, "health": 58},
    {"id": "AWS-LKO-07", "name": "Lucknow", "state": "Uttar Pradesh", "x": 54, "y": 37, "status": "healthy", "temp": 26.3, "pressure": 1011.1, "humidity": 64.0, "health": 94},
    {"id": "AWS-GHY-08", "name": "Guwahati", "state": "Assam", "x": 79, "y": 42, "status": "warning", "temp": 28.7, "pressure": 1004.9, "humidity": 86.0, "health": 79},
    {"id": "AWS-BPL-09", "name": "Bhopal", "state": "Madhya Pradesh", "x": 44, "y": 50, "status": "healthy", "temp": 25.8, "pressure": 1011.9, "humidity": 52.0, "health": 99},
    {"id": "AWS-AMD-10", "name": "Ahmedabad", "state": "Gujarat", "x": 28, "y": 47, "status": "healthy", "temp": 30.6, "pressure": 1009.5, "humidity": 46.0, "health": 92},
    {"id": "AWS-SXR-11", "name": "Srinagar", "state": "Jammu & Kashmir", "x": 38, "y": 12, "status": "healthy", "temp": 14.2, "pressure": 1018.3, "humidity": 58.0, "health": 97},
]

# Baseline historical anomalies for UI bootstrapping
INITIAL_ANOMALIES = [
    {
        "id": "AN-10231",
        "time": "10:41:52",
        "station": "AWS-DEL-01",
        "stationName": "Delhi",
        "parameter": "Temperature",
        "observed": "55.0°C",
        "expected": "24.6°C",
        "severity": "critical",
        "confidence": 96.8,
        "rootCause": "Sensor Spike",
    },
    {
        "id": "AN-10229",
        "time": "10:39:14",
        "station": "AWS-MUM-04",
        "stationName": "Mumbai",
        "parameter": "Humidity",
        "observed": "78.0%",
        "expected": "72.4%",
        "severity": "warning",
        "confidence": 87.2,
        "rootCause": "Calibration Drift",
    },
    {
        "id": "AN-10227",
        "time": "10:37:02",
        "station": "AWS-JAI-02",
        "stationName": "Jaipur",
        "parameter": "Pressure",
        "observed": "1008.2 hPa",
        "expected": "1012.0 hPa",
        "severity": "critical",
        "confidence": 99.1,
        "rootCause": "Communication Failure",
    },
    {
        "id": "AN-10224",
        "time": "10:31:47",
        "station": "AWS-GHY-08",
        "stationName": "Guwahati",
        "parameter": "Humidity",
        "observed": "86.0%",
        "expected": "79.1%",
        "severity": "warning",
        "confidence": 74.6,
        "rootCause": "Calibration Drift",
    },
    {
        "id": "AN-10219",
        "time": "10:22:05",
        "station": "AWS-DEL-01",
        "stationName": "Delhi",
        "parameter": "Temperature",
        "observed": "24.8°C",
        "expected": "24.6°C",
        "severity": "normal",
        "confidence": 34.2,
        "rootCause": "Within Tolerance",
    },
]

class StateStore:
    """
    Central in-memory state store and streaming orchestrator for SkyGuard AI.
    """
    def __init__(self):
        self.stations: Dict[str, Dict[str, Any]] = {
            s["id"]: dict(s) for s in DEFAULT_STATIONS
        }
        # 60-minute sliding window per station (deque of 60 items)
        self.series: Dict[str, deque] = {}
        # Historical buffer for ML diffs and rolling std (last 10 observations)
        self.histories: Dict[str, deque] = {}
        # List of recent anomaly summaries
        self.anomalies: List[Dict[str, Any]] = list(INITIAL_ANOMALIES)
        # Deep LangGraph diagnostic contracts keyed by incident ID
        self.anomaly_details: Dict[str, Dict[str, Any]] = {}
        
        # Network KPI stats (dynamically aligned with actual configured stations)
        self.observations_count = 1284920
        self.active_anomalies = sum(1 for s in self.stations.values() if s.get("status") in ("anomaly", "warning"))
        self.stations_total = len(self.stations)
        self.stations_online = sum(1 for s in self.stations.values() if s.get("status") != "offline")
        self.network_health = round(100.0 - (self.active_anomalies / max(1, self.stations_total) * 15), 1)
        self.sparklines = {
            "stationsOnline": [11, 11, 12, 11, 12, 12, 12, 11, 12, 12],
            "observations": [11, 14, 13, 17, 16, 19, 18, 21, 20, 23],
            "activeAnomalies": [1, 2, 2, 2, 1, 2, 2, 2, 1, 2],
            "networkHealth": [97.8, 97.5, 97.1, 96.9, 96.6, 96.8, 96.5, 96.2, 96.6, 96.4],
        }

        self._initialize_series()
        self._initialize_default_detail()

    def _initialize_series(self):
        """
        Builds initial 60-minute synthetic sliding windows for each station.
        """
        now = datetime.now()
        for s_id, s in self.stations.items():
            dq = deque(maxlen=60)
            hist_dq = deque(maxlen=10)
            base_temp = float(s["temp"])
            base_press = float(s["pressure"])
            base_hum = float(s["humidity"])

            for i in range(59, -1, -1):
                t = now - timedelta(minutes=i)
                label = t.strftime("%H:%M")
                wobble = math.sin(i / 6.0) * 0.5 + (random.random() - 0.5) * 0.3
                temp = round(base_temp + wobble, 1)
                press = round(base_press - (i * 0.003) + (random.random() - 0.5) * 0.15, 1)
                hum = round(max(15.0, min(98.0, base_hum + math.cos(i / 9.0) * 2.0 + (random.random() - 0.5) * 1.0)), 1)
                
                # Injected spike on AWS-DEL-01 at 7 minutes ago for demonstration
                is_anomaly = (s_id == "AWS-DEL-01" and i == 7)
                if is_anomaly:
                    temp = 55.0

                item = {
                    "time": label,
                    "minutesAgo": i,
                    "temp": temp,
                    "pressure": press,
                    "humidity": hum,
                    "anomaly": is_anomaly
                }
                dq.append(item)

                # Keep last 5 for ML historical feature derivation
                hist_dq.append({
                    "station_id": s_id,
                    "temp": temp,
                    "pressure": press,
                    "humidity": hum,
                    "timestamp": t.strftime("%Y-%m-%d %H:%M:%S")
                })

            self.series[s_id] = dq
            self.histories[s_id] = hist_dq

    def _initialize_default_detail(self):
        """
        Seeds initial detailed diagnostic contract for AN-10231.
        """
        self.anomaly_details["AN-10231"] = {
            "id": "AN-10231",
            "station": "AWS-DEL-01",
            "stationName": "Delhi, India",
            "parameter": "Temperature",
            "severity": "critical",
            "confidence": 96.8,
            "observed": 55.0,
            "expected": 24.7,
            "correction": 24.8,
            "correctionMethod": "Temporal interpolation + local station context",
            "correctionConfidence": 91.4,
            "aiAssessment": (
                "Temperature shifted abruptly from expected 24.7°C to observed 55.0°C within one observation interval. "
                "The magnitude and rate of change (Temperature Delta) are inconsistent with recent temporal baselines for Delhi, India."
            ),
            "probableRootCause": "Sensor Spike / Possible Sensor Malfunction",
            "recommendedAction": "Inspect temperature sensor hardware on AWS-DEL-01 and verify calibration against station baseline.",
            "maintenanceRisk": {
                "level": "MEDIUM-HIGH",
                "score": 78,
                "reason": "Repeated temperature anomalies detected in the last 24 hours."
            },
            "zScoreContributions": [
                {"feature": "Temperature Delta", "value": 0.82},
                {"feature": "Rolling Temperature Std", "value": 0.61},
                {"feature": "Temperature", "value": 0.31},
                {"feature": "Humidity", "value": 0.08},
                {"feature": "Pressure", "value": 0.03}
            ],
            "shapContributions": [
                {"feature": "Temperature Delta", "value": 0.82},
                {"feature": "Rolling Temperature Std", "value": 0.61},
                {"feature": "Temperature", "value": 0.31},
                {"feature": "Humidity", "value": 0.08},
                {"feature": "Pressure", "value": 0.03}
            ]
        }

    def get_stations(self) -> List[Dict[str, Any]]:
        """
        Returns all stations with live statuses and telemetry.
        """
        return list(self.stations.values())

    def get_station_series(self, station_id: str) -> List[Dict[str, Any]]:
        """
        Returns 60-minute sliding window time-series for the specified station.
        """
        if station_id not in self.series:
            # Fallback to Delhi if unknown station
            station_id = "AWS-DEL-01"
        return list(self.series.get(station_id, []))

    def get_stats(self) -> Dict[str, Any]:
        """
        Returns network-wide KPI statistics dynamically reflecting current station states.
        """
        online_count = sum(1 for s in self.stations.values() if s.get("status") != "offline")
        total_count = len(self.stations)
        active_anom_count = sum(1 for s in self.stations.values() if s.get("status") in ("anomaly", "warning"))
        return {
            "stationsOnline": online_count,
            "stationsTotal": total_count,
            "observations": self.observations_count,
            "dataQuality": 99.2,
            "activeAnomalies": active_anom_count,
            "networkHealth": round(100.0 - (active_anom_count / max(1, total_count) * 15), 1),
            "sparklines": self.sparklines
        }

    def get_anomalies(self) -> List[Dict[str, Any]]:
        """
        Returns recent anomaly incidents list.
        """
        return self.anomalies

    def get_anomaly_detail(self, anomaly_id: str) -> Optional[Dict[str, Any]]:
        """
        Returns full LangGraph diagnostic detail for a specific anomaly ID.
        """
        if anomaly_id in self.anomaly_details:
            return self.anomaly_details[anomaly_id]
        
        # Fallback: Find summary in anomalies list and return structured baseline
        for a in self.anomalies:
            if a["id"] == anomaly_id:
                s_id = a.get("station", "AWS-DEL-01")
                param = a.get("parameter", "Temperature")
                obs_val = float(str(a.get("observed", "0")).replace("°C", "").replace("%", "").replace(" hPa", "").replace("—", "0"))
                exp_val = float(str(a.get("expected", "0")).replace("°C", "").replace("%", "").replace(" hPa", ""))
                return {
                    "id": anomaly_id,
                    "station": s_id,
                    "stationName": a.get("stationName", get_station_name(s_id)),
                    "parameter": param,
                    "severity": a.get("severity", "warning"),
                    "confidence": a.get("confidence", 85.0),
                    "observed": obs_val,
                    "expected": exp_val,
                    "correction": exp_val,
                    "correctionMethod": "Temporal interpolation + local station context",
                    "correctionConfidence": 90.0,
                    "aiAssessment": f"{param} observation ({obs_val}) diverged from expected baseline ({exp_val}) for {s_id}.",
                    "probableRootCause": a.get("rootCause", "Sensor Anomaly"),
                    "recommendedAction": f"Check {param.lower()} sensor calibration on {s_id}.",
                    "maintenanceRisk": {
                        "level": "MEDIUM",
                        "score": 50,
                        "reason": f"Incident recorded for station {s_id}."
                    },
                    "zScoreContributions": [
                        {"feature": f"{param} Delta", "value": 0.75},
                        {"feature": param, "value": 0.50}
                    ],
                    "shapContributions": [
                        {"feature": f"{param} Delta", "value": 0.75},
                        {"feature": param, "value": 0.50}
                    ]
                }
        return self.anomaly_details.get("AN-10231")

    def ingest_reading(self, reading: Dict[str, Any], force_alert: bool = False) -> Dict[str, Any]:
        """
        Ingests a live weather sensor observation:
        1. Appends reading to sliding window and history buffer.
        2. Executes ML Hybrid Engine (predict_anomaly_with_history).
        3. If anomaly detected, triggers full LangGraph pipeline (process_flagged_reading).
        4. Updates station health and network statistics.
        """
        station_id = reading.get("station_id", "AWS-DEL-01")
        if station_id not in self.stations:
            station_id = "AWS-DEL-01"

        now_str = reading.get("timestamp") or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        temp = float(reading.get("temp", 25.0))
        press = float(reading.get("pressure", 1012.0))
        hum = float(reading.get("humidity", 60.0))

        # Retrieve station's recent historical observations
        history = list(self.histories.get(station_id, []))[-5:]

        # 1. Execute ML Hybrid Engine (Rules + Isolation Forest + SHAP)
        clean_reading = {
            "station_id": station_id,
            "temp": temp,
            "pressure": press,
            "humidity": hum,
            "timestamp": now_str
        }
        
        ml_result = predict_anomaly_with_history(clean_reading, history)
        is_anomaly = (ml_result.get("prediction") == -1)

        # 2. Update In-Memory Buffers
        time_label = datetime.now().strftime("%H:%M")
        series_point = {
            "time": time_label,
            "minutesAgo": 0,
            "temp": temp,
            "pressure": press,
            "humidity": hum,
            "anomaly": is_anomaly
        }
        
        if station_id in self.series:
            # Shift existing minutesAgo
            for pt in self.series[station_id]:
                pt["minutesAgo"] = pt.get("minutesAgo", 0) + 1
            self.series[station_id].append(series_point)
            
        if station_id in self.histories:
            self.histories[station_id].append(clean_reading)

        # Update station current readings
        self.stations[station_id]["temp"] = temp
        self.stations[station_id]["pressure"] = press
        self.stations[station_id]["humidity"] = hum
        self.observations_count += 1

        detail_contract = None

        # 3. If Anomaly, trigger LangGraph Pipeline & Alert Dispatch
        if is_anomaly:
            incident_id = f"AN-{uuid.uuid4().hex[:5].upper()}"
            detail_contract = process_flagged_reading(
                reading=clean_reading,
                ml_output=ml_result,
                history_readings=history,
                incident_id=incident_id,
                force_alert=force_alert
            )

            # Preserve in details cache
            self.anomaly_details[incident_id] = detail_contract

            # Update station status & health
            severity = detail_contract.get("severity", "warning")
            self.stations[station_id]["status"] = "anomaly" if severity == "critical" else "warning"
            self.stations[station_id]["health"] = max(25, self.stations[station_id].get("health", 95) - 8)
            self.active_anomalies += 1

            # Format entry for Recent Anomalies table
            unit = "°C" if detail_contract.get("parameter") == "Temperature" else " hPa" if detail_contract.get("parameter") == "Pressure" else "%"
            table_entry = {
                "id": incident_id,
                "time": datetime.now().strftime("%H:%M:%S"),
                "station": station_id,
                "stationName": detail_contract.get("stationName", get_station_name(station_id)),
                "parameter": detail_contract.get("parameter", "Temperature"),
                "observed": f"{detail_contract.get('observed', temp)}{unit}",
                "expected": f"{detail_contract.get('expected', temp)}{unit}",
                "severity": severity,
                "confidence": detail_contract.get("confidence", 90.0),
                "rootCause": detail_contract.get("probableRootCause", "Sensor Spike")
            }
            self.anomalies.insert(0, table_entry)
            self.anomalies = self.anomalies[:20]  # retain last 20

        return {
            "status": "processed",
            "anomaly": is_anomaly,
            "ml_output": ml_result,
            "detail": detail_contract
        }

    def simulate_anomaly(self, station_id: str = "AWS-DEL-01", anomaly_type: str = "spike") -> Dict[str, Any]:
        """
        Interactive simulation trigger for live hackathon demos.
        Injects an anomaly into the specified station and runs the full ML + LangGraph pipeline.
        """
        if station_id not in self.stations:
            station_id = "AWS-DEL-01"

        station = self.stations[station_id]
        now_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if anomaly_type == "spike":
            # Jump temperature by +30°C
            reading = {
                "station_id": station_id,
                "temp": 55.0,
                "pressure": float(station["pressure"]),
                "humidity": float(station["humidity"]),
                "timestamp": now_ts
            }
        elif anomaly_type == "freeze":
            # Flatline at current temp
            reading = {
                "station_id": station_id,
                "temp": float(station["temp"]),
                "pressure": float(station["pressure"]),
                "humidity": float(station["humidity"]),
                "timestamp": now_ts
            }
        elif anomaly_type == "humidity_spike":
            reading = {
                "station_id": station_id,
                "temp": float(station["temp"]),
                "pressure": float(station["pressure"]),
                "humidity": 99.8,
                "timestamp": now_ts
            }
        else:
            reading = {
                "station_id": station_id,
                "temp": 52.5,
                "pressure": 980.0,
                "humidity": 92.0,
                "timestamp": now_ts
            }

        return self.ingest_reading(reading, force_alert=True)

# Global singleton store instance
STORE = StateStore()
