"""
SkyGuard AI — LangGraph Pipeline State Definition
SIH 2026 Problem Statement 26073
"""

from typing import TypedDict, Optional, List, Dict, Any

class ZScoreContribution(TypedDict):
    feature: str
    value: float

# Backward compatibility alias
ShapContribution = ZScoreContribution

class MaintenanceRawData(TypedDict):
    count: int
    window_hours: int

class MaintenanceRisk(TypedDict):
    level: str
    score: int
    reason: str

class AnomalyFrontendContract(TypedDict):
    id: str
    station: str
    stationName: str
    parameter: str
    severity: str
    confidence: float
    observed: float
    expected: float
    correction: float
    correctionMethod: str
    correctionConfidence: float
    aiAssessment: str
    probableRootCause: str
    recommendedAction: str
    maintenanceRisk: MaintenanceRisk
    zScoreContributions: Optional[List[Dict[str, Any]]]
    shapContributions: Optional[List[Dict[str, Any]]]

class PipelineAgentState(TypedDict, total=False):
    # ----------------------------------------------------
    # 1. Inputs to Graph
    # ----------------------------------------------------
    id: str
    station_id: str
    station_name: str
    timestamp: str
    current_reading: Dict[str, Any]
    history_readings: List[Dict[str, Any]]
    ml_output: Dict[str, Any]
    baseline_stats: Dict[str, Any]

    # ----------------------------------------------------
    # 2. Node 1: Score Calibration Outputs
    # ----------------------------------------------------
    confidence: float
    severity: str

    # ----------------------------------------------------
    # 3. Node 2: Z-Score Explainability & Parameter Formatting Outputs
    # ----------------------------------------------------
    parameter: str
    observed: float
    top_feature: str
    root_cause_category: str
    z_score_contributions_formatted: List[Dict[str, Any]]
    shap_contributions_formatted: List[Dict[str, Any]]

    # ----------------------------------------------------
    # 4. Node 3: Correction Estimation Outputs
    # ----------------------------------------------------
    expected: float
    correction: float
    correction_method: str
    correction_confidence: float

    # ----------------------------------------------------
    # 5. Node 4: Maintenance Risk Outputs
    # ----------------------------------------------------
    maintenance_level: str
    maintenance_score: int
    maintenance_raw_data: Dict[str, Any]

    # ----------------------------------------------------
    # 6. Node 5: Narration LLM Outputs
    # ----------------------------------------------------
    ai_assessment: str
    probable_root_cause: str
    recommended_action: str
    maintenance_reason: str

    # ----------------------------------------------------
    # 7. Final Assembled Frontend Contract
    # ----------------------------------------------------
    final_output: AnomalyFrontendContract
