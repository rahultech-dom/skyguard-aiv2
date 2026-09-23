"""
SkyGuard AI — LangGraph Node Definitions
SIH 2026 Problem Statement 26073
"""

import os
import json
import numpy as np
from typing import Dict, Any, List
from dotenv import load_dotenv

from .state import PipelineAgentState, AnomalyFrontendContract, MaintenanceRisk
from .tools import query_station_24h_anomaly_count, get_station_name

# Load environment variables
load_dotenv()

# Feature display and parameter mappings
FEATURE_DISPLAY_MAP = {
    "temp": ("Temperature", "Temperature"),
    "temp_diff": ("Temperature Delta", "Temperature"),
    "temp_roll_std_6": ("Rolling Temperature Std", "Temperature"),
    "pressure": ("Pressure", "Pressure"),
    "pressure_diff": ("Pressure Delta", "Pressure"),
    "pressure_roll_std_6": ("Rolling Pressure Std", "Pressure"),
    "humidity": ("Humidity", "Humidity"),
    "humidity_diff": ("Humidity Delta", "Humidity"),
    "humidity_roll_std_6": ("Rolling Humidity Std", "Humidity"),
    "hour": ("Hour of Day", "Temporal"),
    "month": ("Month", "Temporal"),
    "day_of_year": ("Day of Year", "Temporal"),
}

PARAM_KEY_MAP = {
    "Temperature": "temp",
    "Pressure": "pressure",
    "Humidity": "humidity"
}

# ==============================================================================
# NODE 1: Score Calibration (Deterministic, Zero LLM)
# ==============================================================================
def score_calibration_node(state: PipelineAgentState) -> Dict[str, Any]:
    """
    Calibrates raw ML Isolation Forest decision score or rule violation into
    a 0-100% confidence percentage and maps to critical/warning/normal severity tiers.
    """
    ml_output = state.get("ml_output", {})
    rule_violation = ml_output.get("rule_violation")
    engine = ml_output.get("engine", "isolation_forest")
    anomaly_score = ml_output.get("anomaly_score", 0.0)

    # 1. Rule-Based Interceptions: Hard physical boundary/flatline failures
    if rule_violation is not None or engine == "rule_based":
        confidence = 98.5
        severity = "critical"
        return {"confidence": confidence, "severity": severity}

    # 2. Isolation Forest Decision Function Calibration
    # Isolation Forest decision scores: negative = anomalous (e.g. -0.05 to -0.35), positive = normal
    if anomaly_score <= 0.0:
        # Scale anomaly score from [-0.35, 0.0] into [70.0, 99.5] confidence
        abs_score = abs(float(anomaly_score))
        scaled_confidence = 72.0 + (abs_score / 0.25) * 26.0
        confidence = round(min(99.5, max(70.0, scaled_confidence)), 1)
    else:
        # Normal reading: lower anomaly confidence
        scaled_confidence = max(10.0, min(68.0, 50.0 - float(anomaly_score) * 100.0))
        confidence = round(scaled_confidence, 1)

    # 3. Severity Bucketing
    if confidence >= 90.0:
        severity = "critical"
    elif confidence >= 70.0:
        severity = "warning"
    else:
        severity = "normal"

    return {
        "confidence": confidence,
        "severity": severity
    }


# ==============================================================================
# NODE 2: Z-Score Explainability & Parameter Formatting (Deterministic, Zero LLM)
# ==============================================================================
def z_score_explainability_node(state: PipelineAgentState) -> Dict[str, Any]:
    """
    Extracts top feature contribution from online model Z-scores / rate of change,
    maps raw features to human-readable labels, determines the primary anomalous parameter,
    and classifies the root-cause category.
    """
    ml_output = state.get("ml_output", {})
    current_reading = state.get("current_reading", {})
    z_raw = ml_output.get("z_score_contributions") or ml_output.get("shap_contributions", [])
    rule_violation = ml_output.get("rule_violation")

    # 1. Format contributions with display names
    formatted_contributions: List[Dict[str, Any]] = []
    top_feature_key = "temp"
    
    if z_raw and isinstance(z_raw, list):
        for item in z_raw:
            raw_feat = item.get("feature", "")
            val = item.get("value", 0.0)
            display_name, _ = FEATURE_DISPLAY_MAP.get(raw_feat, (raw_feat, "Temperature"))
            formatted_contributions.append({
                "feature": display_name,
                "value": round(float(val), 2)
            })
        if z_raw:
            top_feature_key = z_raw[0].get("feature", "temp")

    # 2. Parameter Detection
    parameter = "Temperature"
    if rule_violation:
        rv_lower = rule_violation.lower()
        if "pressure" in rv_lower:
            parameter = "Pressure"
        elif "humidity" in rv_lower:
            parameter = "Humidity"
        elif "temp" in rv_lower:
            parameter = "Temperature"
    elif z_raw:
        # Map from top feature
        _, detected_param = FEATURE_DISPLAY_MAP.get(top_feature_key, ("Temperature", "Temperature"))
        if detected_param in ["Temperature", "Pressure", "Humidity"]:
            parameter = detected_param
        else:
            # If top feature is temporal, pick the highest meteorological feature
            for item in z_raw:
                f_key = item.get("feature", "")
                _, p = FEATURE_DISPLAY_MAP.get(f_key, ("", ""))
                if p in ["Temperature", "Pressure", "Humidity"]:
                    parameter = p
                    break
    elif "z_scores" in ml_output and isinstance(ml_output["z_scores"], dict):
        z_dict = ml_output["z_scores"]
        scores = {
            "Temperature": z_dict.get("temp", 0),
            "Pressure": z_dict.get("pressure", 0),
            "Humidity": z_dict.get("humidity", 0)
        }
        parameter = max(scores, key=scores.get)

    # 3. Root Cause Classification
    root_cause_category = "Sensor Anomaly"
    if rule_violation:
        rv_lower = rule_violation.lower()
        if "flatline" in rv_lower or "stuck" in rv_lower:
            root_cause_category = "Frozen Sensor"
        elif "extreme" in rv_lower or "leap" in rv_lower or "spike" in rv_lower or "rate" in rv_lower:
            root_cause_category = "Sensor Spike"
        elif "invalid" in rv_lower or "range" in rv_lower or "wmo" in rv_lower:
            root_cause_category = "Out of Bounds Range Violation"
    elif top_feature_key.endswith("_diff"):
        root_cause_category = "Sensor Spike"
    elif top_feature_key.endswith("_roll_std_6") or top_feature_key.endswith("_roll_std"):
        root_cause_category = "Calibration Drift"
    elif top_feature_key in ["temp", "pressure", "humidity"]:
        root_cause_category = "Possible Sensor Drift"

    # 4. Extract Observed Value for the anomalous parameter
    param_key = PARAM_KEY_MAP.get(parameter, "temp")
    observed = float(current_reading.get(param_key, 0.0))

    top_display_feature, _ = FEATURE_DISPLAY_MAP.get(top_feature_key, (top_feature_key, parameter))

    return {
        "parameter": parameter,
        "observed": round(observed, 1),
        "top_feature": top_display_feature,
        "root_cause_category": root_cause_category,
        "z_score_contributions_formatted": formatted_contributions,
        "shap_contributions_formatted": formatted_contributions  # backward compatibility alias
    }

# Backward compatibility alias
shap_formatting_node = z_score_explainability_node


# ==============================================================================
# NODE 3: Correction Estimate (Deterministic, Zero LLM, Grounded in Online Baseline)
# ==============================================================================
def correction_estimate_node(state: PipelineAgentState) -> Dict[str, Any]:
    """
    Computes expected baseline and suggested corrected values via temporal interpolation
    and rolling history stability scoring, strictly grounded in the online model baseline stats.
    """
    current_reading = state.get("current_reading", {})
    history_readings = state.get("history_readings", [])
    ml_output = state.get("ml_output", {})
    baseline_stats = state.get("baseline_stats") or ml_output.get("baseline_stats", {})
    
    # Infer parameter if not already set (runs concurrently with node 2)
    parameter = state.get("parameter")
    if not parameter:
        rule_violation = ml_output.get("rule_violation")
        if rule_violation:
            rv_lower = rule_violation.lower()
            if "pressure" in rv_lower:
                parameter = "Pressure"
            elif "humidity" in rv_lower:
                parameter = "Humidity"
            else:
                parameter = "Temperature"
        elif "z_scores" in ml_output and isinstance(ml_output["z_scores"], dict):
            z_dict = ml_output["z_scores"]
            scores = {
                "Temperature": z_dict.get("temp", 0),
                "Pressure": z_dict.get("pressure", 0),
                "Humidity": z_dict.get("humidity", 0)
            }
            parameter = max(scores, key=scores.get)
        else:
            parameter = "Temperature"

    param_key = PARAM_KEY_MAP.get(parameter, "temp")
    observed = float(current_reading.get(param_key, 0.0))

    # Extract historical readings for this parameter
    hist_vals = [
        float(r[param_key]) 
        for r in history_readings 
        if isinstance(r, dict) and param_key in r and r[param_key] is not None
    ]

    if len(hist_vals) >= 1:
        # Calculate expected baseline from recent chronological window
        expected = round(float(np.mean(hist_vals)), 1)
        correction = expected
        std_val = float(np.std(hist_vals)) if len(hist_vals) > 1 else 0.2
        confidence_calc = 96.0 - (std_val * 6.0)
        correction_confidence = round(min(98.0, max(65.0, confidence_calc)), 1)
        correction_method = "Temporal interpolation + local station history"
    elif baseline_stats and param_key in baseline_stats:
        # Grounded in online model rolling StationBaseline
        stat = baseline_stats[param_key]
        expected = round(float(stat.get("mean", observed)), 1)
        correction = expected
        std_val = float(stat.get("std", 1.0))
        confidence_calc = 95.0 - (std_val * 4.0)
        correction_confidence = round(min(98.0, max(70.0, confidence_calc)), 1)
        correction_method = "Online model adaptive rolling baseline"
    else:
        # Fallback if no history or baseline available
        expected = round(observed, 1)
        correction = round(observed, 1)
        correction_confidence = 50.0
        correction_method = "Baseline fallback (insufficient history)"

    return {
        "expected": expected,
        "correction": correction,
        "correction_method": correction_method,
        "correction_confidence": correction_confidence
    }


# ==============================================================================
# NODE 4: Maintenance Risk (Tool Call / PostgreSQL Query, Zero LLM)
# ==============================================================================
def maintenance_risk_node(state: PipelineAgentState) -> Dict[str, Any]:
    """
    Queries PostgreSQL for 24-hour station incident frequency and calculates
    the maintenance risk gauge score and categorical level.
    """
    station_id = state.get("station_id") or state.get("current_reading", {}).get("station_id", "AWS-DEL-01")
    
    # Execute database query tool (or fallback stub)
    incident_count = query_station_24h_anomaly_count(station_id)
    
    # Map frequency to risk categories
    if incident_count <= 1:
        level = "LOW"
        score = incident_count * 20
    elif incident_count <= 3:
        level = "MEDIUM"
        score = 40 + (incident_count - 2) * 15
    elif incident_count <= 6:
        level = "MEDIUM-HIGH"
        score = 70 + (incident_count - 4) * 4  # e.g., 5 -> 74
    else:
        level = "HIGH"
        score = min(100, 85 + (incident_count - 7) * 2)

    return {
        "maintenance_level": level,
        "maintenance_score": int(score),
        "maintenance_raw_data": {
            "count": incident_count,
            "window_hours": 24
        }
    }


# In-memory diagnostic cache to prevent duplicate LLM calls on repeated anomaly states
_NARRATION_CACHE: Dict[str, Dict[str, str]] = {}

# ==============================================================================
# NODE 5: Grounded Narration (Groq LLM Node with openai/gpt-oss-120b / qwen)
# ==============================================================================
def narration_llm_node(state: PipelineAgentState) -> Dict[str, Any]:
    """
    Generates explainable, grounded narrative fields using Groq LLM (model: openai/gpt-oss-120b / qwen-2.5-32b-instruct).
    Optimized for minimal token usage with prompt compression, semantic signature caching, and strict grounding.
    """
    # Extract merged values
    incident_id = state.get("id", "AN-10231")
    station_id = state.get("station_id") or state.get("current_reading", {}).get("station_id", "AWS-DEL-01")
    station_name = state.get("station_name") or get_station_name(station_id)
    
    parameter = state.get("parameter", "Temperature")
    severity = state.get("severity", "critical")
    confidence = state.get("confidence", 96.8)
    
    # Ensure parameter-aligned observed value
    param_key = PARAM_KEY_MAP.get(parameter, "temp")
    observed = state.get("observed", float(state.get("current_reading", {}).get(param_key, 55.0)))
    expected = state.get("expected", 24.7)
    correction = state.get("correction", expected)
    correction_method = state.get("correction_method", "Temporal interpolation + local station context")
    correction_confidence = state.get("correction_confidence", 91.4)
    
    root_cause_category = state.get("root_cause_category", "Sensor Spike")
    top_feature = state.get("top_feature", "Temperature Delta")
    z_contribs = state.get("z_score_contributions_formatted") or state.get("shap_contributions_formatted", [])
    
    m_level = state.get("maintenance_level", "MEDIUM-HIGH")
    m_score = state.get("maintenance_score", 78)
    m_raw = state.get("maintenance_raw_data", {"count": 5, "window_hours": 24})
    count = m_raw.get("count", 5)
    window_hours = m_raw.get("window_hours", 24)

    unit = "°C" if parameter == "Temperature" else " hPa" if parameter == "Pressure" else "%"

    # Default Deterministic Fallback Template
    fallback_ai_assessment = (
        f"{parameter} shifted abruptly from expected {expected}{unit} to observed {observed}{unit} "
        f"within one observation interval. The magnitude and rate of change ({top_feature}) are "
        f"inconsistent with recent temporal baselines for {station_name}."
    )
    fallback_probable_cause = f"{root_cause_category} / Possible Sensor Malfunction"
    fallback_action = f"Inspect {parameter.lower()} sensor hardware and verify calibration against station baseline."
    fallback_m_reason = f"Repeated {parameter.lower()} anomalies ({count} incidents) detected in the last {window_hours} hours."

    # Check Anomaly Signature Cache (0 Token usage for repeated station faults)
    cache_key = f"{station_id}_{parameter}_{root_cause_category}_{severity}_{round(observed, 0)}_{round(expected, 0)}"
    if cache_key in _NARRATION_CACHE:
        cached = _NARRATION_CACHE[cache_key]
        ai_assessment = cached.get("aiAssessment", fallback_ai_assessment)
        probable_root_cause = cached.get("probableRootCause", fallback_probable_cause)
        recommended_action = cached.get("recommendedAction", fallback_action)
        maintenance_reason = cached.get("maintenanceReason", fallback_m_reason)
    else:
        ai_assessment = fallback_ai_assessment
        probable_root_cause = fallback_probable_cause
        recommended_action = fallback_action
        maintenance_reason = fallback_m_reason

        # Attempt Groq LLM Generation (openai/gpt-oss-120b or qwen-2.5-32b-instruct)
        groq_api_key = os.getenv("GROQ_API_KEY")
        if groq_api_key:
            try:
                from langchain_groq import ChatGroq
                from langchain_core.messages import SystemMessage, HumanMessage

                model_name = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

                llm = ChatGroq(
                    groq_api_key=groq_api_key,
                    model_name=model_name,
                    temperature=0.1,
                    max_tokens=220,  # Token optimization: bounded output length
                    model_kwargs={"response_format": {"type": "json_object"}}
                )

                # Compact System Prompt (~35 tokens)
                system_prompt = (
                    "You are SkyGuard AI, a weather diagnostics expert. "
                    "Produce concise explanations strictly using given metrics. "
                    "Output valid JSON with keys: aiAssessment, probableRootCause, recommendedAction, maintenanceReason."
                )

                # Compact User Prompt (~95 tokens)
                user_prompt = f"""Station: {station_id} ({station_name})
Metric: {parameter} | Obs: {observed}{unit} | Base: {expected}{unit} | Corr: {correction}{unit}
Severity: {severity} ({confidence}%) | Driver: {top_feature} | Cause: {root_cause_category}
Maintenance: {m_level} (Score {m_score}/100, {count} alerts in {window_hours}h)

JSON Output:
{{"aiAssessment": "2 concise sentences on shift & baseline delta", "probableRootCause": "diagnostic phrase for {root_cause_category}", "recommendedAction": "1 field action", "maintenanceReason": "1 sentence on risk level"}}"""

                response = llm.invoke([
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_prompt)
                ])

                content = response.content.strip()
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0]
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0]
                content = content.strip()

                first_brace = content.find('{')
                last_brace = content.rfind('}')
                if first_brace != -1 and last_brace != -1:
                    content = content[first_brace:last_brace+1]

                parsed = json.loads(content)
                ai_assessment = parsed.get("aiAssessment", fallback_ai_assessment)
                probable_root_cause = parsed.get("probableRootCause", fallback_probable_cause)
                recommended_action = parsed.get("recommendedAction", fallback_action)
                maintenance_reason = parsed.get("maintenanceReason", fallback_m_reason)

                # Store in cache
                _NARRATION_CACHE[cache_key] = {
                    "aiAssessment": ai_assessment,
                    "probableRootCause": probable_root_cause,
                    "recommendedAction": recommended_action,
                    "maintenanceReason": maintenance_reason,
                }
            except Exception as e:
                print(f"Notice: Groq LLM call returned ({e}). Utilizing deterministic narration fallback.")

    # Assemble Final Frontend Contract
    final_output: AnomalyFrontendContract = {
        "id": incident_id,
        "station": station_id,
        "stationName": station_name,
        "parameter": parameter,
        "severity": severity,
        "confidence": confidence,
        "observed": observed,
        "expected": expected,
        "correction": correction,
        "correctionMethod": correction_method,
        "correctionConfidence": correction_confidence,
        "aiAssessment": ai_assessment,
        "probableRootCause": probable_root_cause,
        "recommendedAction": recommended_action,
        "maintenanceRisk": {
            "level": m_level,
            "score": m_score,
            "reason": maintenance_reason
        },
        "zScoreContributions": z_contribs,
        "shapContributions": z_contribs
    }

    return {
        "ai_assessment": ai_assessment,
        "probable_root_cause": probable_root_cause,
        "recommended_action": recommended_action,
        "maintenance_reason": maintenance_reason,
        "final_output": final_output
    }
