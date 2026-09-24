/**
 * SkyGuard AI v2 — API Client Service
 * 
 * v2 changes:
 *   - VITE_API_URL env var used for deployed backend URL
 *   - Added getLiveFeedStatus() → /api/live-feed
 *   - Added toggleChaos()       → /api/chaos/toggle
 */

import {
  STATIONS,
  SENSOR_SERIES,
  NETWORK_STATS,
  KPI_SPARKLINES,
  ANOMALIES,
  ANOMALY_DETAIL,
  getStationDetailData,
} from "../data/mockData";

const API_BASE = import.meta.env?.VITE_API_URL || "http://127.0.0.1:8000";

async function fetchWithTimeout(url, options = {}, timeoutMs = 2500) {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(url, { ...options, signal: controller.signal });
    clearTimeout(id);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    clearTimeout(id);
    throw err;
  }
}

export async function getStations() {
  try {
    const data = await fetchWithTimeout(`${API_BASE}/api/stations`);
    return data;
  } catch (err) {
    console.debug("Backend offline, utilizing stations fallback:", err.message);
    return STATIONS;
  }
}

export async function getStationSeries(stationId) {
  try {
    const data = await fetchWithTimeout(`${API_BASE}/api/stations/${encodeURIComponent(stationId)}/series`);
    return data;
  } catch (err) {
    console.debug(`Backend offline, utilizing series fallback for ${stationId}:`, err.message);
    return SENSOR_SERIES;
  }
}

export async function getNetworkStats() {
  try {
    const data = await fetchWithTimeout(`${API_BASE}/api/stats`);
    return data;
  } catch (err) {
    console.debug("Backend offline, utilizing stats fallback:", err.message);
    return {
      ...NETWORK_STATS,
      sparklines: KPI_SPARKLINES,
    };
  }
}

export async function getAnomalies() {
  try {
    const data = await fetchWithTimeout(`${API_BASE}/api/anomalies`);
    return data;
  } catch (err) {
    console.debug("Backend offline, utilizing anomalies fallback:", err.message);
    return ANOMALIES;
  }
}

export async function getAnomalyDetail(anomalyId) {
  try {
    const data = await fetchWithTimeout(`${API_BASE}/api/anomalies/${encodeURIComponent(anomalyId)}`);
    return data;
  } catch (err) {
    console.debug(`Backend offline, utilizing anomaly detail fallback for ${anomalyId}:`, err.message);
    const matched = ANOMALIES.find((a) => a.id === anomalyId);
    if (matched) {
      return getStationDetailData(matched.station, null, matched);
    }
    return null;
  }
}

export async function triggerSimulateAnomaly(stationId = "AWS-DEL-01", anomalyType = "spike") {
  const isLocal = typeof window !== "undefined" && (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1");
  const netlifyUrl = "/.netlify/functions/simulate-anomaly";
  const localUrl = `${API_BASE}/api/simulate-anomaly`;
  const primaryUrl = isLocal ? localUrl : netlifyUrl;

  try {
    const data = await fetchWithTimeout(primaryUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ station_id: stationId, anomaly_type: anomalyType }),
    }, 8000);
    return data;
  } catch (err) {
    console.debug("Primary anomaly endpoint failed, attempting fallback:", err.message);
    if (!isLocal) {
      try {
        const localData = await fetchWithTimeout(localUrl, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ station_id: stationId, anomaly_type: anomalyType }),
        }, 4000);
        return localData;
      } catch (err2) {
        console.debug("Local backend also unreachable:", err2.message);
      }
    }
  }

  const station = STATIONS.find((s) => s.id === stationId) || STATIONS[0];
  const generatedDetail = getStationDetailData(stationId, { ...station, status: "anomaly", temp: 55.0 });
  return {
    status: "processed",
    anomaly: true,
    detail: generatedDetail,
  };
}

export async function ingestObservation(reading) {
  try {
    const data = await fetchWithTimeout(`${API_BASE}/api/ingest`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(reading),
    });
    return data;
  } catch (err) {
    console.debug("Backend offline, unable to ingest observation:", err.message);
    return { status: "offline_fallback", anomaly: false };
  }
}

// ── v2: Live Feed & Chaos ─────────────────────────────────────────────────────

export async function getLiveFeedStatus() {
  try {
    return await fetchWithTimeout(`${API_BASE}/api/live-feed`, {}, 3000);
  } catch {
    return { source: "offline", enabled: false, last_poll: null, chaos_enabled: false, faults_injected: 0 };
  }
}

export async function toggleChaos(enable = null) {
  try {
    return await fetchWithTimeout(`${API_BASE}/api/chaos/toggle`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(enable !== null ? { enable } : {}),
    }, 3000);
  } catch (err) {
    console.debug("Chaos toggle failed:", err.message);
    return { chaos_enabled: false };
  }
}

// ── Alert Dispatch Status & Test ─────────────────────────────────────────────

export async function getAlertStatus() {
  try {
    return await fetchWithTimeout(`${API_BASE}/api/alerts/status`, {}, 3000);
  } catch (err) {
    console.debug("Alert status unreachable:", err.message);
    return {
      configured: false,
      mode: "simulation",
      sender_email: "Not configured",
      recipient_email: "Not configured",
    };
  }
}

export async function testAlertDispatch(payload = {}) {
  try {
    return await fetchWithTimeout(`${API_BASE}/api/alerts/test`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }, 8000);
  } catch (err) {
    console.debug("Alert test dispatch failed:", err.message);
    return { status: "error", error: err.message };
  }
}

