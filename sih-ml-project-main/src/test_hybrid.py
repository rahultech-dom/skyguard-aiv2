import os
import sys

# Ensure parent and src directory are in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from ml.src.predict import predict_anomaly_with_history
except ImportError:
    try:
        from src.predict import predict_anomaly_with_history
    except ImportError:
        from predict import predict_anomaly_with_history

def run_tests():
    print("==================================================")
    print("          Running SkyGuard AI Hybrid Tests       ")
    print("==================================================")
    
    # Baseline history for reference (5 normal readings, stable temperature around 2.5°C)
    normal_history = [
        {"temp": 2.5, "pressure": 1005.0, "humidity": 80.0, "timestamp": "2020-01-01 00:00:00"},
        {"temp": 2.6, "pressure": 1005.1, "humidity": 79.8, "timestamp": "2020-01-01 00:10:00"},
        {"temp": 2.4, "pressure": 1004.9, "humidity": 80.2, "timestamp": "2020-01-01 00:20:00"},
        {"temp": 2.5, "pressure": 1005.0, "humidity": 80.1, "timestamp": "2020-01-01 00:30:00"},
        {"temp": 2.7, "pressure": 1005.2, "humidity": 79.5, "timestamp": "2020-01-01 00:40:00"},
    ]
    
    # ----------------------------------------------------
    # Case 1: Normal Reading
    # ----------------------------------------------------
    current_normal = {"temp": 2.6, "pressure": 1005.1, "humidity": 79.9, "timestamp": "2020-01-01 00:50:00"}
    res_normal = predict_anomaly_with_history(current_normal, normal_history)
    print(f"\n[Case 1: Normal Reading]")
    print(f"  Input: temp={current_normal['temp']}°C, pressure={current_normal['pressure']} hPa, humidity={current_normal['humidity']}%")
    print(f"  Output: status={res_normal['status']}, prediction={res_normal['prediction']}, score={res_normal['anomaly_score']}, engine={res_normal['engine']}")
    assert res_normal['prediction'] == 1, "Failed: Normal case was flagged as anomalous!"
    print("  => PASS")

    # ----------------------------------------------------
    # Case 2: Physical Limits Violation (Extreme Temperature)
    # ----------------------------------------------------
    current_extreme = {"temp": 85.0, "pressure": 1005.1, "humidity": 79.9, "timestamp": "2020-01-01 00:50:00"}
    res_extreme = predict_anomaly_with_history(current_extreme, normal_history)
    print(f"\n[Case 2: Physical Limits (Temp > 60°C)]")
    print(f"  Input: temp={current_extreme['temp']}°C")
    print(f"  Output: status={res_extreme['status']}, prediction={res_extreme['prediction']}, violation='{res_extreme['rule_violation']}', engine={res_extreme['engine']}")
    assert res_extreme['prediction'] == -1 and res_extreme['engine'] in ("rule_based", "rule_engine"), "Failed: Extreme temp did not trigger rule engine!"
    print("  => PASS")

    # ----------------------------------------------------
    # Case 3: Rate of Change Violation (Impossible 10-Min Jump)
    # ----------------------------------------------------
    current_jump = {"temp": 9.5, "pressure": 1005.1, "humidity": 79.9, "timestamp": "2020-01-01 00:50:00"} # Leap of 6.8°C from previous (2.7)
    res_jump = predict_anomaly_with_history(current_jump, normal_history)
    print(f"\n[Case 3: Rate of Change (Temp Jump > 5°C in 10 mins)]")
    print(f"  Input: temp={current_jump['temp']}°C (previous was 2.7°C)")
    print(f"  Output: status={res_jump['status']}, prediction={res_jump['prediction']}, violation='{res_jump['rule_violation']}', engine={res_jump['engine']}")
    assert res_jump['prediction'] == -1 and res_jump['engine'] in ("rule_based", "rule_engine"), "Failed: Rapid leap did not trigger rule engine!"
    print("  => PASS")

    # ----------------------------------------------------
    # Case 4: Flatline Scenario (Sensor-Stuck Check)
    # ----------------------------------------------------
    # We pass a history of 5 identical readings, and a 6th identical reading.
    # Standard deviation over 1 hour will be exactly 0.0, which is highly anomalous.
    flat_history = [
        {"temp": 2.5, "pressure": 1005.0, "humidity": 80.0, "timestamp": "2020-01-01 00:00:00"},
        {"temp": 2.5, "pressure": 1005.0, "humidity": 80.0, "timestamp": "2020-01-01 00:10:00"},
        {"temp": 2.5, "pressure": 1005.0, "humidity": 80.0, "timestamp": "2020-01-01 00:20:00"},
        {"temp": 2.5, "pressure": 1005.0, "humidity": 80.0, "timestamp": "2020-01-01 00:30:00"},
        {"temp": 2.5, "pressure": 1005.0, "humidity": 80.0, "timestamp": "2020-01-01 00:40:00"},
    ]
    current_flat = {"temp": 2.5, "pressure": 1005.0, "humidity": 80.0, "timestamp": "2020-01-01 00:50:00"}
    res_flat = predict_anomaly_with_history(current_flat, flat_history)
    print(f"\n[Case 4: Flatline (Sensor-Stuck Scenario)]")
    print(f"  Input: Temp flatlined at {current_flat['temp']}°C for 1 hour.")
    print(f"  Output: status={res_flat['status']}, prediction={res_flat['prediction']}, score={res_flat['anomaly_score']}, engine={res_flat['engine']}")
    assert res_flat['prediction'] == -1 and res_flat['engine'] in ("rule_based", "rule_engine"), "Failed: Flatline did not trigger Stuck Sensor rule!"
    print("  => PASS")

    print("\n==================================================")
    print("           All Tests Passed Successfully!         ")
    print("==================================================")

if __name__ == "__main__":
    run_tests()
