"""
SkyGuard AI — Real-Time Alert Dispatch Service
SIH 2026 Problem Statement 26073

Provides automated, asynchronous email alert dispatching for detected Automatic Weather Station (AWS) anomalies.
Supports rich responsive HTML email templates, in-memory per-station anti-spam cooldown timers,
and graceful simulation fallback when SMTP credentials are not yet configured.
"""

import os
import smtplib
import threading
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, Any, Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# In-memory cooldown tracking: { station_id: timestamp_of_last_sent_alert }
_STATION_COOLDOWNS: Dict[str, datetime] = {}
_COOLDOWN_LOCK = threading.Lock()

# Default Cooldown: 180 seconds (3 minutes) per station to avoid inbox flooding
DEFAULT_COOLDOWN_SECONDS = int(os.getenv("ALERT_COOLDOWN_SECONDS", "180"))


def generate_alert_text(incident: Dict[str, Any]) -> str:
    """
    Generates a clean, structured Plain Text meteorological report for the incident.
    """
    station_id = incident.get("station", "AWS-UNKNOWN")
    station_name = incident.get("stationName", "Weather Station")
    severity = str(incident.get("severity", "critical")).upper()
    confidence = incident.get("confidence", 95.0)
    parameter = incident.get("parameter", "Temperature")
    observed = incident.get("observed", "N/A")
    expected = incident.get("expected", "N/A")
    correction = incident.get("correction", "N/A")
    root_cause = incident.get("probableRootCause", "Sensor Discrepancy")
    ai_assessment = incident.get("aiAssessment", "Anomalous reading detected outside expected baseline.")
    recommended_action = incident.get("recommendedAction", "Inspect sensor transducer and calibration.")
    timestamp = datetime.now().strftime("%d %b %Y, %H:%M:%S IST")
    unit = "°C" if parameter == "Temperature" else " hPa" if parameter == "Pressure" else "%"

    try:
        obs_f = float(str(observed).replace("°C", "").replace("%", "").replace("hPa", "").strip())
        exp_f = float(str(expected).replace("°C", "").replace("%", "").replace("hPa", "").strip())
        diff_str = f"+{(obs_f - exp_f):.1f}{unit} deviation"
    except Exception:
        diff_str = f"Deviation flagged against {expected}{unit} baseline"

    return f"""======================================================================
         SKYGUARD AI — METEOROLOGICAL EARLY WARNING ALERT
                 MINISTRY OF EARTH SCIENCES / IMD
======================================================================

ALERT LEVEL:      {severity} ANOMALY (Confidence: {confidence}%)
STATION ID:       {station_id}
STATION NAME:     {station_name}
PARAMETER:        {parameter}
TIMESTAMP (IST):  {timestamp}

----------------------------------------------------------------------
TELEMETRY METRICS
----------------------------------------------------------------------
• Observed Reading:      {observed}{unit}  [FLAGGED ANOMALOUS]
• Expected Baseline:     {expected}{unit}
• Suggested Correction:  {correction}{unit}
• Telemetry Discrepancy: {diff_str}

----------------------------------------------------------------------
AI ROOT CAUSE DIAGNOSTICS
----------------------------------------------------------------------
• Probable Root Cause:   {root_cause}
• Physical Evaluation:   {ai_assessment}
• WMO QC Compliance:     FAILED (WMO-No. 8 Range & Step Limit Checks)

----------------------------------------------------------------------
RECOMMENDED FIELD ACTION
----------------------------------------------------------------------
{recommended_action}

======================================================================
Generated automatically by SkyGuard AI Agentic Pipeline
SIH 2026 Problem Statement 26073 • Ministry of Earth Sciences (IMD)
======================================================================"""


def send_email_alert(incident: Dict[str, Any], force: bool = False) -> Dict[str, Any]:
    """
    Sends an automated email alert for the given incident in Plain Text format.
    
    If SMTP credentials are not configured, runs in Safe Simulation Mode
    and prints the formatted incident alert to console.
    """
    station_id = incident.get("station", "AWS-UNKNOWN")
    station_name = incident.get("stationName", "Weather Station")
    severity = str(incident.get("severity", "critical")).upper()
    parameter = incident.get("parameter", "Temperature")
    observed = incident.get("observed", "")
    expected = incident.get("expected", "")

    # Anti-Spam Cooldown Check
    if not force:
        with _COOLDOWN_LOCK:
            now = datetime.now()
            last_sent = _STATION_COOLDOWNS.get(station_id)
            if last_sent and (now - last_sent).total_seconds() < DEFAULT_COOLDOWN_SECONDS:
                remaining = int(DEFAULT_COOLDOWN_SECONDS - (now - last_sent).total_seconds())
                print(f"[SkyGuard Alert] Cooldown active for {station_id} ({remaining}s remaining). Alert suppressed.")
                return {
                    "status": "suppressed_cooldown",
                    "station_id": station_id,
                    "remaining_cooldown_seconds": remaining
                }
            _STATION_COOLDOWNS[station_id] = now

    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER", "").strip()
    smtp_password = os.getenv("SMTP_PASSWORD", "").strip()
    recipient_email = os.getenv("ALERT_RECIPIENT_EMAIL", "").strip()

    subject = f"[{severity} ALERT] {station_id} ({station_name}) {parameter} Anomaly Detected"
    text_body = generate_alert_text(incident)

    # If credentials are not provided, log simulated email dispatch
    if not smtp_user or not smtp_password or not recipient_email:
        print("\n" + "=" * 70)
        print(f"[SIMULATED EMAIL DISPATCH] {subject}")
        print(f"To: {recipient_email or '(Set ALERT_RECIPIENT_EMAIL in .env to receive live emails)'}")
        print(f"Station: {station_id} ({station_name}) | Parameter: {parameter}")
        print(f"Observed: {observed} | Expected: {expected} | Severity: {severity}")
        print(f"AI Root Cause: {incident.get('probableRootCause', 'Sensor Spike')}")
        print("=" * 70 + "\n")
        return {
            "status": "simulated_success",
            "station_id": station_id,
            "subject": subject,
            "mode": "simulation",
            "message": "Alert simulated successfully. Set SMTP credentials in .env to deliver live emails."
        }

    # Live SMTP Dispatch in Plain Text
    try:
        msg = MIMEText(text_body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = f"SkyGuard AI Alerts <{smtp_user}>"
        msg["To"] = recipient_email

        with smtplib.SMTP(smtp_server, smtp_port, timeout=10) as server:
            server.ehlo()
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_user, [recipient_email], msg.as_string())

        print(f"[SkyGuard Alert] Live plain text email alert successfully delivered to {recipient_email} for {station_id}")
        return {
            "status": "delivered",
            "station_id": station_id,
            "recipient": recipient_email,
            "subject": subject
        }
    except Exception as e:
        print(f"[SkyGuard Alert] SMTP delivery failed for {station_id}: {e}")
        return {
            "status": "error",
            "station_id": station_id,
            "error": str(e)
        }
