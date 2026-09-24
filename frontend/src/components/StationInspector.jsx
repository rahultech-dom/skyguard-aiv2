import {
  Thermometer,
  Gauge,
  Droplets,
  HeartPulse,
  Clock,
  Radio,
  BatteryCharging,
  Wind,
  ShieldCheck,
  AlertOctagon,
  Cpu,
} from "lucide-react";
import StatusBadge from "./StatusBadge";

export default function StationInspector({ station, onViewDetails }) {
  if (!station) {
    return (
      <div className="flex h-full flex-col items-center justify-center rounded-xl border border-slate-200 bg-white p-8 text-center shadow-sm">
        <div className="mb-3 flex h-11 w-11 items-center justify-center rounded-full bg-slate-100 text-slate-400">
          <Gauge size={18} />
        </div>
        <p className="text-[13px] font-medium text-slate-500">Select an Automatic Weather Station on the map to inspect telemetry.</p>
      </div>
    );
  }

  const statusKey = station.status === "warning" ? "warn" : station.status === "anomaly" ? "critical" : "healthy";

  return (
    <div className="flex h-full flex-col overflow-y-auto rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      {/* Header */}
      <div className="flex items-start justify-between border-b border-slate-100 pb-3">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="font-mono-num text-[16px] font-bold text-slate-900">{station.id}</h3>
            {station.wmoId && (
              <span className="rounded bg-sky-50 border border-sky-200 px-1.5 py-0.5 text-[10px] font-mono-num font-bold text-sky-700">
                WMO {station.wmoId}
              </span>
            )}
          </div>
          <p className="mt-0.5 text-[13px] font-semibold text-slate-800">
            {station.stationName || `${station.name} Observatory`}
          </p>
          <div className="text-[11px] text-slate-500 font-medium">
            {station.state} · Lat {station.lat?.toFixed(2) ?? "28.61"}°N, Lon {station.lng?.toFixed(2) ?? "77.21"}°E
          </div>
        </div>
        <StatusBadge status={statusKey} pulse={station.status !== "healthy"} />
      </div>

      {/* Hardware & Telemetry Link strip */}
      <div className="mt-3 rounded-xl border border-slate-200 bg-slate-50/80 p-2.5 text-[11px]">
        <div className="flex items-center justify-between text-slate-600">
          <span className="flex items-center gap-1.5 font-medium">
            <Cpu size={13} className="text-sky-600" />
            <span className="text-slate-900 font-mono-num font-semibold">{station.loggerModel || "CR1000X Logger"}</span>
          </span>
          <span className="flex items-center gap-1 text-emerald-700 font-medium">
            <Radio size={12} className="text-emerald-600" />
            <span>INSAT-3DR DCP</span>
          </span>
        </div>
        <div className="mt-1.5 flex items-center justify-between text-[10px] text-slate-500 font-mono-num font-medium">
          <span className="flex items-center gap-1">
            <BatteryCharging size={12} className="text-emerald-600" />
            {station.batteryVolt ?? 12.8}V DC ({station.solarWatts ?? 38}W PV)
          </span>
          <span>Tower: {station.mastHeight || "10m Mast"}</span>
        </div>
      </div>

      {/* Atmospheric Telemetry Grid */}
      <div className="mt-3 grid grid-cols-2 gap-2.5">
        <Metric icon={Thermometer} label="Air Temp (1.5m)" value={`${station.temp} °C`} color="text-amber-600" />
        <Metric icon={Gauge} label="MSL Pressure" value={`${station.pressure} hPa`} color="text-sky-600" />
        <Metric icon={Droplets} label="Humidity (RH)" value={`${station.humidity}%`} color="text-cyan-600" subtext={`Td: ${station.dewPoint ?? 18.2}°C`} />
        <Metric icon={Wind} label="Wind (10m AGL)" value={`${station.windSpeed ?? 3.8} m/s`} color="text-emerald-600" subtext={station.windDir?.split(" ")[0] || "WSW"} />
      </div>

      {/* WMO Quality Control (QC) status flags */}
      <div className="mt-3 rounded-xl border border-slate-200 bg-slate-50/60 p-2.5 text-[11px]">
        <div className="text-[10px] uppercase tracking-wider text-slate-500 font-bold mb-1.5">
          WMO-No. 8 Real-Time Quality Control (QC)
        </div>
        <div className="space-y-1">
          <div className="flex items-center justify-between">
            <span className="text-slate-600 font-medium">QC-1 Physical Range Check</span>
            <span className="flex items-center gap-1 font-mono-num text-[10px] text-emerald-700 font-bold">
              <ShieldCheck size={12} /> PASSED
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-slate-600 font-medium">QC-2 Step / Rate Check</span>
            <span className={`flex items-center gap-1 font-mono-num text-[10px] font-bold ${
              station.status === "anomaly" ? "text-rose-700" : "text-emerald-700"
            }`}>
              {station.status === "anomaly" ? (
                <>
                  <AlertOctagon size={12} /> FAILED
                </>
              ) : (
                <>
                  <ShieldCheck size={12} /> PASSED
                </>
              )}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-slate-600 font-medium">QC-3 Spatial Consistency</span>
            <span className={`flex items-center gap-1 font-mono-num text-[10px] font-bold ${
              station.status === "anomaly" ? "text-amber-700" : "text-emerald-700"
            }`}>
              {station.status === "anomaly" ? "SUSPECT" : "NOMINAL"}
            </span>
          </div>
        </div>
      </div>

      {/* Footer Info & Action */}
      <div className="mt-3 flex items-center justify-between text-[10px] text-slate-500 font-mono-num font-medium">
        <span className="flex items-center gap-1">
          <Clock size={11} /> Synoptic Packet 10:42:18 IST
        </span>
        <span className="flex items-center gap-1 text-emerald-700 font-bold">
          <HeartPulse size={11} /> Sensor Health {station.health}%
        </span>
      </div>

      <button
        onClick={onViewDetails}
        className="mt-3 w-full rounded-lg border border-sky-300 bg-sky-50 py-2 text-[12px] font-semibold text-sky-700 transition-colors hover:bg-sky-100 hover:border-sky-400 focus-visible:outline focus-visible:outline-2 focus-visible:outline-sky-500"
      >
        View Full WMO Diagnostic & Z-Score Analysis
      </button>
    </div>
  );
}

function Metric({ icon: Icon, label, value, color = "text-slate-900", subtext }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-slate-50/80 p-2.5">
      <div className="flex items-center justify-between text-[10px] text-slate-500 font-medium">
        <span className="flex items-center gap-1">
          <Icon size={12} className={color} />
          {label}
        </span>
        {subtext && <span className="font-mono-num text-slate-600">{subtext}</span>}
      </div>
      <div className="mt-1 font-mono-num text-[16px] font-bold text-slate-900">{value}</div>
    </div>
  );
}
