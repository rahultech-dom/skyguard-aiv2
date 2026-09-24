"""
SkyGuard AI v2 — Email Alert Integration Test Suite
SIH 2026 Problem Statement 26073

Verifies:
1. Email plain-text alert generation formatting and required fields
2. Simulation mode fallback when SMTP credentials are unconfigured
3. Per-station anti-spam cooldown suppression & force bypass
4. Live SMTP dispatch using mock SMTP transport
5. Error resiliency: SMTP failures do not crash anomaly detection
6. Pipeline integration: Normal data does NOT trigger alert, anomaly DOES trigger alert
7. Interactive / simulated anomaly trigger execution
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Ensure parent and src directory are in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.api.alert_service import generate_alert_text, send_email_alert, reset_cooldowns
from src.api.state_store import StateStore


class TestEmailAlertFeature(unittest.TestCase):

    def setUp(self):
        reset_cooldowns()
        try:
            from src.model.online_model import get_model
            model = get_model()
            model._histories.clear()
            model._baselines.clear()
            model._hst_models.clear()
        except Exception:
            pass

    def test_alert_text_generation(self):
        """Verifies all required anomaly diagnostic fields appear in the generated email."""
        incident = {
            "id": "AN-TEST-01",
            "station": "AWS-DEL-01",
            "stationName": "Delhi",
            "parameter": "Temperature",
            "severity": "critical",
            "confidence": 98.5,
            "observed": 55.0,
            "expected": 24.6,
            "correction": 24.6,
            "probableRootCause": "Sensor Spike / Hardware Failure",
            "aiAssessment": "Temperature jumped abruptly to 55.0°C exceeding physical rate-of-change limits.",
            "recommendedAction": "Inspect Pt100 RTD sensor cabling and verify calibration against standard."
        }
        text = generate_alert_text(incident)

        self.assertIn("SKYGUARD AI", text)
        self.assertIn("AWS-DEL-01", text)
        self.assertIn("Delhi", text)
        self.assertIn("CRITICAL ANOMALY", text)
        self.assertIn("55.0°C", text)
        self.assertIn("24.6°C", text)
        self.assertIn("Sensor Spike", text)
        self.assertIn("Inspect Pt100 RTD", text)
        self.assertIn("WMO QC Compliance", text)

    def test_simulation_mode_when_credentials_unset(self):
        """When SMTP credentials are missing, system operates in Safe Simulation Mode without crashing."""
        with patch.dict(os.environ, {"SMTP_USER": "", "SMTP_PASSWORD": "", "ALERT_RECIPIENT_EMAIL": ""}, clear=True):
            incident = {
                "station": "AWS-DEL-01",
                "stationName": "Delhi",
                "severity": "critical",
                "parameter": "Temperature",
                "observed": 55.0,
                "expected": 25.0
            }
            result = send_email_alert(incident, force=True)
            self.assertEqual(result.get("status"), "simulated_success")
            self.assertEqual(result.get("mode"), "simulation")

    def test_antispam_cooldown(self):
        """Ensures consecutive anomalies for the same station are throttled to prevent spam."""
        with patch.dict(os.environ, {"SMTP_USER": "", "SMTP_PASSWORD": "", "ALERT_RECIPIENT_EMAIL": ""}, clear=True):
            incident = {
                "station": "AWS-BPL-09",
                "stationName": "Bhopal",
                "severity": "critical",
                "parameter": "Temperature",
                "observed": 52.0,
                "expected": 25.0
            }
            # First alert sends successfully
            res1 = send_email_alert(incident, force=False)
            self.assertEqual(res1.get("status"), "simulated_success")

            # Second immediate alert for same station must be suppressed
            res2 = send_email_alert(incident, force=False)
            self.assertEqual(res2.get("status"), "suppressed_cooldown")
            self.assertIn("remaining_cooldown_seconds", res2)

            # Different station should NOT be suppressed
            incident_diff = dict(incident, station="AWS-KOL-03", stationName="Kolkata")
            res_diff = send_email_alert(incident_diff, force=False)
            self.assertEqual(res_diff.get("status"), "simulated_success")

            # Forced alert should bypass cooldown
            res_forced = send_email_alert(incident, force=True)
            self.assertEqual(res_forced.get("status"), "simulated_success")

    @patch("smtplib.SMTP")
    def test_live_smtp_dispatch(self, mock_smtp_class):
        """Verifies SMTP client connection, TLS handshake, login, and sendmail when credentials exist."""
        mock_server = MagicMock()
        mock_smtp_class.return_value.__enter__.return_value = mock_server

        env_vars = {
            "SMTP_SERVER": "smtp.gmail.com",
            "SMTP_PORT": "587",
            "SMTP_USER": "test_sender@gmail.com",
            "SMTP_PASSWORD": "app_password_123",
            "ALERT_RECIPIENT_EMAIL": "field_crew@domain.com, alerts@domain.com"
        }
        with patch.dict(os.environ, env_vars):
            incident = {
                "station": "AWS-MUM-04",
                "stationName": "Mumbai",
                "severity": "critical",
                "parameter": "Temperature",
                "observed": 49.5,
                "expected": 29.8
            }
            result = send_email_alert(incident, force=True)

            self.assertEqual(result.get("status"), "delivered")
            mock_server.starttls.assert_called_once()
            mock_server.login.assert_called_once_with("test_sender@gmail.com", "app_password_123")
            mock_server.sendmail.assert_called_once()
            args, _ = mock_server.sendmail.call_args
            self.assertEqual(args[0], "test_sender@gmail.com")
            self.assertEqual(args[1], ["field_crew@domain.com", "alerts@domain.com"])

    @patch("smtplib.SMTP")
    def test_smtp_error_does_not_crash(self, mock_smtp_class):
        """Verifies that an SMTP exception does not raise or crash callers."""
        mock_server = MagicMock()
        mock_server.sendmail.side_effect = Exception("SMTP Connection Timed Out")
        mock_smtp_class.return_value.__enter__.return_value = mock_server

        env_vars = {
            "SMTP_SERVER": "smtp.gmail.com",
            "SMTP_PORT": "587",
            "SMTP_USER": "test_sender@gmail.com",
            "SMTP_PASSWORD": "app_password_123",
            "ALERT_RECIPIENT_EMAIL": "field_crew@domain.com"
        }
        with patch.dict(os.environ, env_vars):
            incident = {
                "station": "AWS-MUM-04",
                "stationName": "Mumbai",
                "severity": "critical",
                "parameter": "Temperature",
                "observed": 49.5,
                "expected": 29.8
            }
            result = send_email_alert(incident, force=True)
            self.assertEqual(result.get("status"), "error")
            self.assertIn("error", result)

    def test_pipeline_normal_reading_does_not_trigger_email(self):
        """Verifies that normal, non-anomalous readings do NOT dispatch an email alert."""
        store = StateStore()
        normal_reading = {
            "station_id": "AWS-DEL-01",
            "temp": 24.6,
            "pressure": 1012.4,
            "humidity": 68.0,
            "timestamp": "2026-01-01 12:00:00"
        }
        result = store.ingest_reading(normal_reading)
        self.assertFalse(result.get("anomaly"))
        self.assertIsNone(result.get("detail"))

    def test_pipeline_anomaly_triggers_email_alert(self):
        """Verifies that a detected anomaly triggers the LangGraph alert node and dispatches alert."""
        store = StateStore()
        # Physical limit violation (85°C > 60°C WMO limit) guarantees anomaly detection
        anomalous_reading = {
            "station_id": "AWS-DEL-01",
            "temp": 85.0,
            "pressure": 1012.4,
            "humidity": 68.0,
            "timestamp": "2026-01-01 12:00:00"
        }
        result = store.ingest_reading(anomalous_reading, force_alert=True)
        self.assertTrue(result.get("anomaly"))
        detail = result.get("detail")
        self.assertIsNotNone(detail)
        self.assertTrue(detail.get("alertDispatched"))
        self.assertIn(detail.get("alertStatus"), ("simulated_success", "delivered"))

    def test_simulate_anomaly_trigger(self):
        """Verifies that simulate_anomaly executes end-to-end and dispatches an alert."""
        store = StateStore()
        result = store.simulate_anomaly(station_id="AWS-DEL-01", anomaly_type="spike")
        self.assertTrue(result.get("anomaly"))
        detail = result.get("detail")
        self.assertIsNotNone(detail)
        self.assertTrue(detail.get("alertDispatched"))


if __name__ == "__main__":
    unittest.main()
