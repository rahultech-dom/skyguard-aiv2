"""
SkyGuard AI — LangGraph Graph Construction & Entry Points
SIH 2026 Problem Statement 26073
"""

import uuid
from typing import Dict, Any, List, Optional
from langgraph.graph import StateGraph, START, END

from .state import PipelineAgentState, AnomalyFrontendContract
from .nodes import (
    score_calibration_node,
    z_score_explainability_node,
    correction_estimate_node,
    maintenance_risk_node,
    narration_llm_node,
    alert_dispatch_node,
    shap_formatting_node  # backward compatibility
)
from .tools import get_station_name

def build_skyguard_graph() -> StateGraph:
    """
    Constructs the LangGraph state graph for SkyGuard AI with parallel fan-out
    across 4 deterministic/tool nodes merging into the Groq narration node,
    followed by the autonomous alert dispatch node.
    """
    workflow = StateGraph(PipelineAgentState)

    # 1. Add all 6 nodes
    workflow.add_node("score_calibration", score_calibration_node)
    workflow.add_node("z_score_explainability", z_score_explainability_node)
    workflow.add_node("correction_estimate", correction_estimate_node)
    workflow.add_node("maintenance_risk", maintenance_risk_node)
    workflow.add_node("narration", narration_llm_node)
    workflow.add_node("alert_dispatch", alert_dispatch_node)

    # 2. Fan-out: Parallel execution from START to Nodes 1-4
    workflow.add_edge(START, "score_calibration")
    workflow.add_edge(START, "z_score_explainability")
    workflow.add_edge(START, "correction_estimate")
    workflow.add_edge(START, "maintenance_risk")

    # 3. Fan-in: Merge all 4 branches into Node 5 (Narration)
    workflow.add_edge("score_calibration", "narration")
    workflow.add_edge("z_score_explainability", "narration")
    workflow.add_edge("correction_estimate", "narration")
    workflow.add_edge("maintenance_risk", "narration")

    # 4. Action: Narration to Node 6 (Alert Dispatch)
    workflow.add_edge("narration", "alert_dispatch")

    # 5. Exit to END
    workflow.add_edge("alert_dispatch", END)

    return workflow.compile()

# Global compiled graph instance
_COMPILED_GRAPH = None

def get_compiled_graph():
    """
    Lazy initialization of compiled LangGraph workflow.
    """
    global _COMPILED_GRAPH
    if _COMPILED_GRAPH is None:
        _COMPILED_GRAPH = build_skyguard_graph()
    return _COMPILED_GRAPH

def process_flagged_reading(
    reading: Dict[str, Any],
    ml_output: Dict[str, Any],
    history_readings: Optional[List[Dict[str, Any]]] = None,
    incident_id: Optional[str] = None,
    force_alert: bool = False
) -> Dict[str, Any]:
    """
    Primary interface for backend / FastAPI ingestion layer.
    Takes a single flagged weather station reading, historical readings, and the ML model output,
    executes the LangGraph pipeline, and returns the complete frontend contract dictionary.

    Parameters:
    -----------
    reading : dict
        Current observation containing temp, pressure, humidity, timestamp, station_id.
    ml_output : dict
        Output from predict_anomaly_with_history (status, prediction, anomaly_score, rule_violation, z_score_contributions).
    history_readings : list of dicts, optional
        Chronological list of prior readings.
    incident_id : str, optional
        Custom incident identifier (e.g. "AN-10231"). Defaults to generated ID.
    force_alert : bool, optional
        Force email dispatch bypassing 180s cooldown.

    Returns:
    --------
    dict
        Structured anomaly object matching the frontend AnomalyDetail contract.
    """
    graph = get_compiled_graph()
    
    station_id = reading.get("station_id", "AWS-DEL-01")
    station_name = get_station_name(station_id)
    timestamp = str(reading.get("timestamp", ""))
    baseline_stats = ml_output.get("baseline_stats", {})
    
    if not incident_id:
        incident_id = f"AN-{uuid.uuid4().hex[:5].upper()}"

    initial_state: PipelineAgentState = {
        "id": incident_id,
        "station_id": station_id,
        "station_name": station_name,
        "timestamp": timestamp,
        "force_alert": force_alert,
        "current_reading": reading,
        "history_readings": history_readings or [],
        "ml_output": ml_output,
        "baseline_stats": baseline_stats
    }

    # Execute graph synchronously with resilient fallback
    try:
        result_state = graph.invoke(initial_state)
        final_output = result_state.get("final_output", {})
        if final_output:
            return final_output
    except Exception as e:
        import logging
        logging.getLogger("skyguard.pipeline").warning(f"LangGraph execution exception: {e}. Executing fallback path.")

    # Fallback assembly if graph fails or returns empty
    from .nodes import (
        determine_severity_and_confidence,
        calculate_correction,
        compute_maintenance_risk,
    )
    try:
        from src.api.alert_service import send_email_alert
    except ImportError:
        from api.alert_service import send_email_alert

    temp = float(reading.get("temp", 25.0))
    press = float(reading.get("pressure", 1012.0))
    hum = float(reading.get("humidity", 60.0))
    rule_violation = ml_output.get("rule_violation")
    z_contribs = ml_output.get("z_score_contributions") or []

    param = "Temperature" if (rule_violation and "temp" in rule_violation.lower()) or abs(temp - 25.0) > 15 else \
            "Pressure" if (rule_violation and "press" in rule_violation.lower()) or abs(press - 1012.0) > 30 else \
            "Humidity" if (rule_violation and "hum" in rule_violation.lower()) else "Temperature"
    observed_val = temp if param == "Temperature" else press if param == "Pressure" else hum

    conf, sev = determine_severity_and_confidence(ml_output)
    exp, corr, corr_meth, corr_conf = calculate_correction(param, observed_val, baseline_stats, history_readings or [])
    m_level, m_score, m_reason, _ = compute_maintenance_risk(station_id, sev)

    fallback_output: AnomalyFrontendContract = {
        "id": incident_id,
        "station": station_id,
        "stationName": station_name,
        "parameter": param,
        "severity": sev,
        "confidence": conf,
        "observed": observed_val,
        "expected": exp,
        "correction": corr,
        "correctionMethod": corr_meth,
        "correctionConfidence": corr_conf,
        "aiAssessment": rule_violation or f"Telemetry deviation flagged on {station_name} {param.lower()} sensor.",
        "probableRootCause": rule_violation or f"Sensor hardware transducer spike / drift ({param})",
        "recommendedAction": f"Inspect sensor hardware and verify against calibration standard.",
        "maintenanceRisk": {
            "level": m_level,
            "score": m_score,
            "reason": m_reason
        },
        "zScoreContributions": z_contribs,
        "shapContributions": z_contribs,
        "alertDispatched": False,
        "alertStatus": "pending"
    }

    try:
        alert_res = send_email_alert(fallback_output, force=force_alert)
        fallback_output["alertDispatched"] = alert_res.get("status") in ("delivered", "simulated_success")
        fallback_output["alertStatus"] = alert_res.get("status", "unknown")
    except Exception as a_err:
        fallback_output["alertDispatched"] = False
        fallback_output["alertStatus"] = f"error: {a_err}"

    return fallback_output
