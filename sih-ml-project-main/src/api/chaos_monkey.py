"""
SkyGuard AI v2 — Chaos Monkey Fault Injector
Randomly corrupts live weather readings before they reach the ML model,
to stress-test anomaly detection accuracy in a controlled way.

Fault types mirror real-world AWS hardware failure modes:
  - Spike       : RTD temperature sensor electrical interference
  - Freeze      : Stuck sensor / frozen telemetry link
  - Humidity=0  : TBRG funnel clog or capacitive sensor failure
  - Pressure    : Barometric sensor membrane rupture / calibration error
  - Drift       : Slow radiation shield heating / sensor calibration drift
"""

import random
from typing import Tuple

# Probability of each fault — must sum to ≤ 1.0 (remainder = no fault)
FAULT_PROBABILITIES = {
    "spike":           0.10,   # temp jumps to 55–65°C
    "freeze":          0.08,   # all values flatline at current reading
    "humidity_zero":   0.08,   # humidity drops to 0 (TBRG clog)
    "pressure_spike":  0.07,   # pressure shoots to 1090–1099 hPa
    "drift":           0.07,   # slow +8°C temp drift (calibration error)
    # remaining 0.60 = no fault → clean reading passes through
}


def inject_fault(reading: dict) -> Tuple[dict, bool]:
    """
    Randomly apply a hardware fault to a live weather reading.

    Parameters:
        reading: dict with keys station_id, temp, pressure, humidity, timestamp

    Returns:
        (modified_reading, fault_was_applied)
    """
    r = random.random()
    cumulative = 0.0
    selected_fault = None

    for fault_name, prob in FAULT_PROBABILITIES.items():
        cumulative += prob
        if r < cumulative:
            selected_fault = fault_name
            break

    if selected_fault is None:
        # No fault — clean reading
        return reading, False

    corrupted = dict(reading)
    station   = reading.get("station_id", "unknown")

    if selected_fault == "spike":
        corrupted["temp"] = round(random.uniform(55.0, 65.0), 1)
        corrupted["_fault"] = f"SPIKE: temp → {corrupted['temp']}°C"

    elif selected_fault == "freeze":
        # Flatline: pretend all values haven't changed (value stays same)
        # The model's rolling std will become 0 → triggers flatline rule
        corrupted["_fault"] = f"FREEZE: sensor flatlined"

    elif selected_fault == "humidity_zero":
        corrupted["humidity"] = 0.0
        corrupted["_fault"] = "HUMIDITY_ZERO: funnel clog"

    elif selected_fault == "pressure_spike":
        corrupted["pressure"] = round(random.uniform(1090.0, 1099.0), 1)
        corrupted["_fault"] = f"PRESSURE_SPIKE: {corrupted['pressure']} hPa"

    elif selected_fault == "drift":
        drift = round(random.uniform(6.0, 10.0), 1)
        corrupted["temp"] = round(reading["temp"] + drift, 1)
        corrupted["_fault"] = f"DRIFT: temp +{drift}°C"

    import logging
    logging.getLogger("skyguard.chaos").info(
        f"[ChaosMonkey] 🐒 {station} → {corrupted.get('_fault', '?')}"
    )

    return corrupted, True
