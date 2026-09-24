import { useEffect, useMemo, useRef, useState } from "react";
import { Menu, Zap } from "lucide-react";
import LiveFeedBadge from "../components/LiveFeedBadge";
import Sidebar from "../components/Sidebar";
import KPICard from "../components/KPICard";
import NetworkMap from "../components/NetworkMap";
import StationInspector from "../components/StationInspector";
import SensorChart from "../components/SensorChart";
import AnomalyTable from "../components/AnomalyTable";
import AnomalyDetail from "../components/AnomalyDetail";
import AIInsight from "../components/AIInsight";
import ShapChart from "../components/ShapChart";
import MaintenanceRisk from "../components/MaintenanceRisk";
import Toast from "../components/Toast";
import {
  STATIONS,
  SENSOR_SERIES,
  NETWORK_STATS,
  KPI_SPARKLINES,
  ANOMALIES,
  ANOMALY_DETAIL,
  ANOMALY_STATION_ID,
  SHAP_CONTRIBUTIONS,
  getStationDetailData,
  buildSeries,
} from "../data/mockData";
import {
  getStations,
  getStationSeries,
  getNetworkStats,
  getAnomalies,
  getAnomalyDetail,
  triggerSimulateAnomaly,
  toggleChaos,
} from "../services/api";

function formatClock(d) {
  return d.toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

export default function Dashboard() {
  const [navActive, setNavActive] = useState("overview");
  const [focusedSection, setFocusedSection] = useState(null); // 'overview' | 'stations' | 'monitoring' | 'anomalies' | 'analytics'
  const [mobileSidebar, setMobileSidebar] = useState(false);
  const [selectedStationId, setSelectedStationId] = useState(ANOMALY_STATION_ID);
  const [anomalyList, setAnomalyList] = useState(ANOMALIES);
  const [selectedAnomaly, setSelectedAnomaly] = useState(null);
  const [panelOpen, setPanelOpen] = useState(false);
  const [toasts, setToasts] = useState([]);
  const [clock, setClock] = useState(new Date("2026-08-30T10:42:18"));
  const [observations, setObservations] = useState(NETWORK_STATS.observations);
  const [activeAnomalies, setActiveAnomalies] = useState(NETWORK_STATS.activeAnomalies);
  const [networkHealth, setNetworkHealth] = useState(NETWORK_STATS.networkHealth);
  const [stationsOnline, setStationsOnline] = useState(NETWORK_STATS.stationsOnline);
  const [sparklines, setSparklines] = useState(KPI_SPARKLINES);
  const [loading, setLoading] = useState(true);
  const [stations, setStations] = useState(STATIONS);
  const [stationSeries, setStationSeries] = useState(SENSOR_SERIES);
  const [isSimulating, setIsSimulating] = useState(false);
  const [isLiveMode, setIsLiveMode] = useState(true);
  const [chaosEnabled, setChaosEnabled] = useState(false);
  const [faultsInjected, setFaultsInjected] = useState(0);
  const toastIdRef = useRef(0);

  const selectedStation = stations.find((s) => s.id === selectedStationId) || null;

  // Handle smooth scroll & highlight focus from sidebar
  const handleNavSelect = (key) => {
    setNavActive(key);
    setFocusedSection(key);

    const sectionMap = {
      overview: "section-overview",
      stations: "section-stations",
      monitoring: "section-monitoring",
      anomalies: "section-anomalies",
      analytics: "section-analytics",
    };

    const targetId = sectionMap[key];
    if (targetId) {
      const el = document.getElementById(targetId);
      if (el) {
        el.scrollIntoView({ behavior: "smooth", block: "start" });
      }
    }
  };

  const handleClearFocus = () => {
    setFocusedSection(null);
  };

  // Initial Data Fetch from FastAPI Backend
  useEffect(() => {
    let mounted = true;
    async function loadInitialData() {
      try {
        const [stns, stats, anoms] = await Promise.all([
          getStations(),
          getNetworkStats(),
          getAnomalies(),
        ]);
        if (mounted) {
          if (stns && stns.length > 0) setStations(stns);
          if (stats) {
            if (stats.observations) setObservations(stats.observations);
            if (stats.activeAnomalies !== undefined) setActiveAnomalies(stats.activeAnomalies);
            if (stats.networkHealth !== undefined) setNetworkHealth(stats.networkHealth);
            if (stats.stationsOnline !== undefined) setStationsOnline(stats.stationsOnline);
            if (stats.sparklines) setSparklines(stats.sparklines);
          }
          if (anoms && anoms.length > 0) setAnomalyList(anoms);
          setLoading(false);
        }
      } catch (err) {
        console.debug("Backend initial fetch error, maintaining fallback:", err);
        if (mounted) setLoading(false);
      }
    }
    loadInitialData();
    return () => { mounted = false; };
  }, []);

  // Fetch 60-Minute Sliding Series when selected station changes
  useEffect(() => {
    let mounted = true;
    async function loadSeries() {
      try {
        const series = await getStationSeries(selectedStationId);
        if (mounted && series && series.length > 0) {
          setStationSeries(series);
        }
      } catch (err) {
        console.debug("Station series fetch error:", err);
      }
    }
    loadSeries();
    return () => { mounted = false; };
  }, [selectedStationId]);

  // Clock + observation counter tick
  useEffect(() => {
    const interval = setInterval(() => {
      setClock((c) => new Date(c.getTime() + 1000));
      setObservations((o) => o + Math.floor(Math.random() * 4) + 1);
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  // Live telemetry wobble & Automated Chaos injection if active
  useEffect(() => {
    const interval = setInterval(() => {
      setStations((prev) =>
        prev.map((s) => ({
          ...s,
          temp: Number((s.temp + (Math.random() - 0.5) * 0.2).toFixed(1)),
          humidity: Math.max(20, Math.min(95, Number((s.humidity + (Math.random() - 0.5) * 0.6).toFixed(0)))),
        }))
      );

      // If Chaos Monkey is enabled, randomly perturb a station & dispatch real alert
      if (chaosEnabled && Math.random() > 0.65) {
        const randIdx = Math.floor(Math.random() * stations.length);
        const target = stations[randIdx];
        if (target) {
          const spikeTemp = Number((target.temp + 15 + Math.random() * 12).toFixed(1));
          setStations((prev) =>
            prev.map((s, idx) =>
              idx === randIdx ? { ...s, temp: spikeTemp, status: "anomaly", health: Math.max(20, s.health - 6) } : s
            )
          );
          setFaultsInjected((f) => f + 1);
          setActiveAnomalies((a) => a + 1);
          const newFault = {
            id: `AN-${Math.floor(Math.random() * 90000) + 10000}`,
            time: formatClock(new Date()),
            station: target.id,
            stationName: `${target.name || "Station"}, India`,
            parameter: "Temperature",
            observed: `${spikeTemp}°C`,
            expected: `${target.temp}°C`,
            severity: "critical",
            confidence: 98.2,
            rootCause: "Chaos Monkey Injected Spike",
          };
          setAnomalyList((prev) => [newFault, ...prev.slice(0, 14)]);
        }
      }
    }, 4000);
    return () => clearInterval(interval);
  }, [chaosEnabled, stations]);

  const dismissToast = (id) => setToasts((prev) => prev.filter((t) => t.id !== id));

  const handleToggleChaos = async () => {
    const next = !chaosEnabled;
    setChaosEnabled(next);
    const id = ++toastIdRef.current;

    // Synchronize chaos state with backend API
    toggleChaos(next).catch(() => {});

    setToasts((prev) => [
      ...prev,
      {
        id,
        station: next ? "Chaos Monkey Activated 🐒" : "Chaos Monkey Deactivated ✅",
        parameter: next ? "Injecting 40% random physical faults into telemetry stream" : "Sensor stream normalized to baseline",
        confidence: next ? 99.5 : 100.0,
      },
    ]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 5000);
  };

  const handleToggleMode = () => {
    const next = !isLiveMode;
    setIsLiveMode(next);
    const id = ++toastIdRef.current;
    setToasts((prev) => [
      ...prev,
      {
        id,
        station: next ? "Connected to LIVE Open-Meteo 🛰" : "Switched to Simulation Mode 📊",
        parameter: next ? "Polling 12 synoptic AWS nodes across India" : "Operating on calibrated 60-min sliding ring buffers",
        confidence: 99.0,
      },
    ]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4000);
  };

  // Open Full LangGraph Diagnostic Drawer
  const openAnomalyDetail = async (anomaly) => {
    if (!anomaly) return;
    try {
      const detail = await getAnomalyDetail(anomaly.id);
      if (detail && detail.station === anomaly.station) {
        setSelectedAnomaly(detail);
      } else {
        const stationObj = stations.find((s) => s.id === anomaly.station);
        const stnDetail = getStationDetailData(anomaly.station, stationObj, anomaly);
        setSelectedAnomaly(stnDetail);
      }
    } catch {
      const stationObj = stations.find((s) => s.id === anomaly.station);
      const detail = getStationDetailData(anomaly.station, stationObj, anomaly);
      setSelectedAnomaly(detail);
    }
    setPanelOpen(true);
  };

  // Open diagnostics for the currently selected station from StationInspector
  const openStationDetail = (station) => {
    if (!station) return;
    const existingAnomaly = anomalyList.find((a) => a.station === station.id);
    const detail = getStationDetailData(station.id, station, existingAnomaly);
    setSelectedAnomaly(detail);
    setPanelOpen(true);
  };

  // Interactive Anomaly Simulation
  const handleSimulateAnomaly = async () => {
    setIsSimulating(true);
    try {
      const targetStation = stations.find((s) => s.id === selectedStationId) || stations[0];
      const res = await triggerSimulateAnomaly(targetStation.id, "spike");
      
      const stnName = targetStation.name || "Station";
      const baseExpected = targetStation.temp > 45 ? 14.2 : (targetStation.temp || 24.6);
      const detail = (res?.detail && res.detail.station === targetStation.id)
        ? res.detail
        : getStationDetailData(targetStation.id, { ...targetStation, status: "anomaly", temp: 55.0 });

      const newEntry = {
        id: detail.id || `AN-${Math.floor(Math.random() * 90000) + 10000}`,
        time: formatClock(new Date()),
        station: targetStation.id,
        stationName: `${stnName}, India`,
        parameter: "Temperature",
        observed: "55.0°C",
        expected: `${baseExpected}°C`,
        severity: "critical",
        confidence: 98.5,
        rootCause: "Sensor Spike / Hardware Spike",
      };

      setAnomalyList((prev) => [newEntry, ...prev.filter((a) => a.id !== newEntry.id)].slice(0, 15));
      setActiveAnomalies((n) => n + 1);
      setStations((prev) =>
        prev.map((s) =>
          s.id === targetStation.id
            ? { ...s, status: "anomaly", temp: 55.0, health: Math.max(25, s.health - 8) }
            : s
        )
      );

      // Refresh series to display newly injected spike
      const updatedSeries = await getStationSeries(targetStation.id);
      if (updatedSeries && updatedSeries.length > 0) {
        setStationSeries(updatedSeries);
      }

      const id = ++toastIdRef.current;
      setToasts((prev) => [...prev, { id, station: targetStation.id, parameter: "Temperature Spike Injected", confidence: 98.5 }]);
      setTimeout(() => {
        setToasts((prev) => prev.filter((t) => t.id !== id));
      }, 5000);
    } catch (err) {
      console.error("Simulation error:", err);
    } finally {
      setIsSimulating(false);
    }
  };

  const totalStationsCount = stations.length || NETWORK_STATS.stationsTotal;
  const currentOnlineCount = stationsOnline ?? stations.filter((s) => s.status !== "offline").length;
  const coveragePercent = Math.round((currentOnlineCount / Math.max(1, totalStationsCount)) * 100);

  const kpis = useMemo(
    () => [
      {
        label: "AWS Stations Online",
        value: `${currentOnlineCount}`,
        suffix: `/ ${totalStationsCount} Nodes`,
        subLabel: `${coveragePercent}% Grid Active`,
        trend: "Synoptic Grid Active",
        trendDirection: "up",
        status: "good",
        sparkline: sparklines.stationsOnline,
      },
      {
        label: "Telemetry Packets Ingested",
        value: observations.toLocaleString("en-IN"),
        suffix: "Packets",
        subLabel: "INSAT-3DR 1Hz Stream",
        trend: "+4 pkt/sec Live",
        trendDirection: "up",
        status: "info",
        sparkline: sparklines.observations,
      },
      {
        label: "Flagged Sensor Anomalies",
        value: `${activeAnomalies}`,
        suffix: "Active Faults",
        subLabel: "Z-Score & HST Flags",
        trend: activeAnomalies > 0 ? `${activeAnomalies} Outliers Detected` : "All Stations Nominal",
        trendDirection: activeAnomalies > 0 ? "down" : "up",
        status: activeAnomalies > 0 ? "bad" : "good",
        sparkline: sparklines.activeAnomalies,
      },
      {
        label: "WMO QC & Model Health",
        value: `${networkHealth}%`,
        suffix: "Validated",
        subLabel: "Half-Space Trees Online",
        trend: "WMO-No. 8 Pass",
        trendDirection: "up",
        status: "good",
        sparkline: sparklines.networkHealth,
      },
    ],
    [observations, activeAnomalies, currentOnlineCount, totalStationsCount, coveragePercent, networkHealth, sparklines]
  );

  // Synchronize 60-minute sensor series to live clock and selected station
  const seriesToUse = useMemo(() => {
    const rawSeries = stationSeries && stationSeries.length > 0 ? stationSeries : buildSeries(clock, selectedStation);
    return rawSeries.map((pt, idx) => {
      const minutesAgo = pt.minutesAgo !== undefined ? pt.minutesAgo : (59 - idx);
      const ptTime = new Date(clock.getTime() - minutesAgo * 60000);
      const timeLabel = ptTime.toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit", hour12: false });
      return {
        ...pt,
        time: timeLabel,
      };
    });
  }, [stationSeries, clock, selectedStation]);

  const tempCurrent = seriesToUse[seriesToUse.length - 1]?.temp ?? 24.6;
  const tempMin = Math.min(...seriesToUse.map((d) => d.temp));
  const tempMax = Math.max(...seriesToUse.map((d) => d.temp));
  const pressureCurrent = seriesToUse[seriesToUse.length - 1]?.pressure ?? 1012.4;
  const pressureMin = Math.min(...seriesToUse.map((d) => d.pressure));
  const pressureMax = Math.max(...seriesToUse.map((d) => d.pressure));
  const humidityCurrent = seriesToUse[seriesToUse.length - 1]?.humidity ?? 68.0;
  const humidityMin = Math.min(...seriesToUse.map((d) => d.humidity));
  const humidityMax = Math.max(...seriesToUse.map((d) => d.humidity));

  // Focus Styling Helper for Sections
  const getSectionClass = (sectionKey) => {
    const base = "rounded-xl border transition-all duration-500 p-4 scroll-mt-24";
    if (!focusedSection) {
      return `${base} border-transparent bg-transparent`;
    }
    if (focusedSection === sectionKey) {
      return `${base} border-sky-300 bg-white shadow-lg ring-2 ring-sky-200 opacity-100 scale-[1.005]`;
    }
    return `${base} border-slate-200/40 bg-slate-100/40 opacity-30 blur-[1px] pointer-events-none`;
  };

  return (
    <div className="flex min-h-screen bg-slate-50">
      <Sidebar
        active={navActive}
        onSelect={handleNavSelect}
        mobileOpen={mobileSidebar}
        onCloseMobile={() => setMobileSidebar(false)}
      />

      <div className="flex min-w-0 flex-1 flex-col">
        {/* Streamlined Top Bar */}
        <header className="sticky top-0 z-30 flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 bg-white/95 px-6 py-3.5 backdrop-blur-md">
          <div className="flex items-center gap-3">
            <button
              className="rounded-lg border border-slate-200 p-2 text-slate-500 hover:text-slate-800 lg:hidden"
              onClick={() => setMobileSidebar(true)}
              aria-label="Open menu"
            >
              <Menu size={16} />
            </button>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-[16px] font-bold tracking-tight text-slate-900">
                  National Automatic Weather Station (AWS) Surveillance Center
                </h1>
                <span className="rounded bg-sky-100 border border-sky-200 px-2 py-0.5 text-[10px] font-mono-num font-bold text-sky-700">
                  IMD / MoES NETWORK
                </span>
              </div>
              <p className="text-[12px] text-slate-500 font-medium">
                Operational Surface Synoptic Telemetry, WMO-No. 8 Quality Control & Online Anomaly Surveillance.
              </p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2.5 text-[12px]">
            {/* Unified Telemetry & Chaos Controller */}
            <LiveFeedBadge
              isLive={isLiveMode}
              chaosEnabled={chaosEnabled}
              onToggleChaos={handleToggleChaos}
              onToggleMode={handleToggleMode}
              faultsInjected={faultsInjected}
            />

            {/* Single Interactive Inject Spike Action Button */}
            <button
              onClick={handleSimulateAnomaly}
              disabled={isSimulating}
              type="button"
              className="flex items-center gap-1.5 rounded-full border border-amber-300 bg-amber-50 px-3.5 py-1 text-[11px] font-bold text-amber-800 transition-all hover:bg-amber-100 hover:border-amber-400 focus-visible:outline focus-visible:outline-2 focus-visible:outline-amber-500 disabled:opacity-50 shadow-xs cursor-pointer"
              title="Inject an immediate test sensor spike onto the active station and trigger alert"
            >
              <Zap size={12} className={isSimulating ? "animate-spin text-amber-600" : "text-amber-600 fill-amber-600"} />
              <span>{isSimulating ? "Analyzing..." : "Inject Anomaly Spike"}</span>
            </button>

            {/* Live Clock */}
            <div className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 font-mono-num text-[11px] font-semibold text-slate-600 shadow-xs">
              IST: {formatClock(clock)}
            </div>
          </div>
        </header>

        <main className="flex-1 space-y-6 px-6 py-6">
          {/* Active Focus Pill when an option is chosen */}
          {focusedSection && (
            <div className="sticky top-20 z-20 mx-auto -mt-2 mb-2 flex w-fit items-center gap-3 rounded-full border border-sky-300 bg-white px-4 py-1.5 shadow-lg backdrop-blur-md animate-toast-in text-[12px] text-slate-800">
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-sky-500 opacity-75" />
                <span className="relative inline-flex h-2 w-2 rounded-full bg-sky-600" />
              </span>
              <span>
                Focusing on:{" "}
                <strong className="text-slate-900 capitalize">
                  {focusedSection === "overview"
                    ? "AWS Network Ingestion (KPIs)"
                    : focusedSection === "stations"
                    ? "AWS Surface Station Grid"
                    : focusedSection === "monitoring"
                    ? "Live Sensor Telemetry"
                    : focusedSection === "anomalies"
                    ? "Flagged Sensor Faults"
                    : "WMO & Z-Score Diagnostics"}
                </strong>
              </span>
              <button
                onClick={handleClearFocus}
                className="ml-2 rounded-full bg-slate-100 border border-slate-200 px-2.5 py-0.5 text-[11px] font-semibold text-slate-600 hover:bg-slate-200 transition-all"
              >
                Show All Sections ✕
              </button>
            </div>
          )}

          {/* Section 1: Overview */}
          <section
            id="section-overview"
            className={getSectionClass("overview")}
            onClick={() => {
              if (focusedSection && focusedSection !== "overview") handleNavSelect("overview");
            }}
          >
            {focusedSection === "overview" && (
              <div className="mb-3 flex items-center justify-between border-b border-sky-100 pb-2.5">
                <span className="text-[12px] font-bold uppercase tracking-wider text-sky-700">
                  National AWS Network Ingestion & Telemetry Health
                </span>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleClearFocus();
                  }}
                  className="rounded px-2 py-0.5 text-[11px] font-semibold text-slate-500 hover:bg-slate-100 hover:text-slate-900"
                >
                  Show All ✕
                </button>
              </div>
            )}
            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
              {loading
                ? Array.from({ length: 4 }).map((_, i) => (
                    <div key={i} className="h-[104px] rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
                      <div className="skeleton h-3 w-24 rounded" />
                      <div className="skeleton mt-4 h-6 w-16 rounded" />
                    </div>
                  ))
                : kpis.map((k) => <KPICard key={k.label} {...k} />)}
            </div>
          </section>

          {/* Section 2: Stations */}
          <section
            id="section-stations"
            className={getSectionClass("stations")}
            onClick={() => {
              if (focusedSection && focusedSection !== "stations") handleNavSelect("stations");
            }}
          >
            {focusedSection === "stations" && (
              <div className="mb-3 flex items-center justify-between border-b border-sky-100 pb-2.5">
                <span className="text-[12px] font-bold uppercase tracking-wider text-sky-700">
                  Automatic Weather Station Grid & Hardware Diagnostics
                </span>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleClearFocus();
                  }}
                  className="rounded px-2 py-0.5 text-[11px] font-semibold text-slate-500 hover:bg-slate-100 hover:text-slate-900"
                >
                  Show All ✕
                </button>
              </div>
            )}
            <div className="grid gap-4 lg:grid-cols-[1fr_340px]">
              <div>
                <div className="mb-3 flex items-center justify-between">
                  <h2 className="text-[15px] font-bold text-slate-900">AWS Surface Observation Network (India Grid)</h2>
                  <span className="text-[12px] text-slate-500 font-mono-num font-medium">{stations.length} Synoptic Nodes Active</span>
                </div>
                <NetworkMap stations={stations} selectedId={selectedStationId} onSelect={setSelectedStationId} />
              </div>
              <div>
                <h2 className="mb-3 text-[15px] font-bold text-slate-900">AWS Hardware Diagnostics</h2>
                <div className="h-[460px] lg:h-[520px]">
                  <StationInspector station={selectedStation} onViewDetails={() => openStationDetail(selectedStation)} />
                </div>
              </div>
            </div>
          </section>

          {/* Section 3: Live Monitoring */}
          <section
            id="section-monitoring"
            className={getSectionClass("monitoring")}
            onClick={() => {
              if (focusedSection && focusedSection !== "monitoring") handleNavSelect("monitoring");
            }}
          >
            <div className="mb-3 flex items-center justify-between">
              <div>
                <h2 className="text-[15px] font-bold text-slate-900">
                  Live AWS Sensor Telemetry — {selectedStation?.stationName || selectedStation?.name || selectedStation?.id} {selectedStation?.wmoId ? `(WMO ${selectedStation.wmoId})` : ""}
                </h2>
                <p className="text-[12px] text-slate-500 font-medium">
                  60-Minute Sliding Window · Sampling Frequency 1 Hz · Multi-parameter Time Series
                </p>
              </div>
              {focusedSection === "monitoring" && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleClearFocus();
                  }}
                  className="rounded px-2 py-0.5 text-[11px] font-semibold text-slate-500 hover:bg-slate-100 hover:text-slate-900"
                >
                  Show All ✕
                </button>
              )}
            </div>
            <div className="grid gap-4 lg:grid-cols-3">
              <SensorChart
                title="Air Temperature (Pt100 RTD)"
                data={seriesToUse}
                dataKey="temp"
                unit="°C"
                color="#ea580c"
                min={tempMin}
                max={tempMax}
                current={tempCurrent}
              />
              <SensorChart
                title="Barometric Pressure (PTB330)"
                data={seriesToUse}
                dataKey="pressure"
                unit=" hPa"
                color="#0284c7"
                min={pressureMin}
                max={pressureMax}
                current={pressureCurrent}
              />
              <SensorChart
                title="Relative Humidity (Capacitive)"
                data={seriesToUse}
                dataKey="humidity"
                unit="%"
                color="#0891b2"
                min={humidityMin}
                max={humidityMax}
                current={humidityCurrent}
              />
            </div>
          </section>

          {/* Section 4: Recent Anomalies */}
          <section
            id="section-anomalies"
            className={getSectionClass("anomalies")}
            onClick={() => {
              if (focusedSection && focusedSection !== "anomalies") handleNavSelect("anomalies");
            }}
          >
            <div className="mb-3 flex items-center justify-between">
              <div>
                <h2 className="text-[15px] font-bold text-slate-900">Flagged AWS Sensor Faults & Quality Control Feed</h2>
                <span className="text-[12px] text-slate-500 font-medium">WMO Physical Limits + Online Half-Space Trees ML Detection & Z-Score Attributions</span>
              </div>
              {focusedSection === "anomalies" && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleClearFocus();
                  }}
                  className="rounded px-2 py-0.5 text-[11px] font-semibold text-slate-500 hover:bg-slate-100 hover:text-slate-900"
                >
                  Show All ✕
                </button>
              )}
            </div>
            <AnomalyTable anomalies={anomalyList} onSelect={openAnomalyDetail} />
          </section>

          {/* Section 5: AI Analytics & Diagnostics */}
          <section
            id="section-analytics"
            className={getSectionClass("analytics")}
            onClick={() => {
              if (focusedSection && focusedSection !== "analytics") handleNavSelect("analytics");
            }}
          >
            <div className="mb-3 flex items-center justify-between">
              <div>
                <h2 className="text-[15px] font-bold text-slate-900">WMO Sensor Physics, Z-Score Explainability & Maintenance Risk</h2>
                <span className="text-[12px] text-slate-500 font-medium">Atmospheric thermodynamic consistency check & field maintenance scoring</span>
              </div>
              {focusedSection === "analytics" && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleClearFocus();
                  }}
                  className="rounded px-2 py-0.5 text-[11px] font-semibold text-slate-500 hover:bg-slate-100 hover:text-slate-900"
                >
                  Show All ✕
                </button>
              )}
            </div>
            <div className="grid gap-4 lg:grid-cols-3">
              <AIInsight
                assessment={
                  selectedAnomaly?.aiAssessment ||
                  ANOMALY_DETAIL.aiAssessment ||
                  "Automated sensor telemetry evaluation detected potential deviation in environmental readings."
                }
                rootCause={selectedAnomaly?.probableRootCause || ANOMALY_DETAIL.probableRootCause || "Sensor Drift"}
                action={selectedAnomaly?.recommendedAction || ANOMALY_DETAIL.recommendedAction || "Verify station calibration."}
              />
              <ShapChart
                contributions={selectedAnomaly?.shapContributions || SHAP_CONTRIBUTIONS}
              />
              <MaintenanceRisk
                level={selectedAnomaly?.maintenanceRisk?.level || ANOMALY_DETAIL.maintenanceRisk?.level || "MEDIUM-HIGH"}
                score={selectedAnomaly?.maintenanceRisk?.score || ANOMALY_DETAIL.maintenanceRisk?.score || 78}
                reason={selectedAnomaly?.maintenanceRisk?.reason || ANOMALY_DETAIL.maintenanceRisk?.reason || "Repeated anomalies flagged in recent observation cycles."}
              />
            </div>
          </section>
        </main>
      </div>

      <AnomalyDetail detail={selectedAnomaly} open={panelOpen} onClose={() => setPanelOpen(false)} />
      <Toast toasts={toasts} onDismiss={dismissToast} />
    </div>
  );
}
