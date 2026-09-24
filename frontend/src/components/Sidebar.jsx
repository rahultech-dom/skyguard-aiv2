import { Link } from "react-router-dom";
import {
  LayoutGrid,
  Radio,
  AlertTriangle,
  MapPin,
  BarChart3,
  UserCircle2,
  X,
} from "lucide-react";

const NAV = [
  { id: "overview", label: "Network Overview", icon: LayoutGrid },
  { id: "stations", label: "AWS Station Grid", icon: MapPin },
  { id: "monitoring", label: "Sensor Telemetry", icon: Radio },
  { id: "anomalies", label: "QC Anomaly Alerts", icon: AlertTriangle },
  { id: "analytics", label: "WMO & Z-Score Diagnostics", icon: BarChart3 },
];

export default function Sidebar({ active, onSelect, mobileOpen, onCloseMobile }) {
  return (
    <>
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm lg:hidden"
          onClick={onCloseMobile}
        />
      )}
      <aside
        className={`fixed inset-y-0 left-0 z-50 flex w-64 shrink-0 flex-col border-r border-slate-200 bg-white transition-transform duration-300 lg:sticky lg:top-0 lg:h-screen lg:translate-x-0 ${
          mobileOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="flex h-16 items-center justify-between border-b border-slate-200 px-5">
          <Link to="/" className="flex items-center gap-2.5">
            <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-sky-500 text-white shadow-sm">
              <Radio size={16} />
            </span>
            <div>
              <div className="flex items-center gap-1">
                <span className="text-[13px] font-bold tracking-tight text-slate-900">
                  SKYGUARD
                </span>
                <span className="rounded bg-sky-100 px-1 py-0.2 text-[9px] font-bold text-sky-700">
                  AWS
                </span>
              </div>
              <div className="text-[10px] font-medium text-slate-500">
                IMD Synoptic Grid
              </div>
            </div>
          </Link>
          <button className="text-slate-500 hover:text-slate-700 lg:hidden" onClick={onCloseMobile} aria-label="Close menu">
            <X size={18} />
          </button>
        </div>

        <nav className="flex-1 space-y-1 px-3 py-5">
          {NAV.map((item) => {
            const Icon = item.icon;
            const isActive = active === item.id;
            return (
              <button
                key={item.id}
                onClick={() => {
                  onSelect(item.id);
                  onCloseMobile?.();
                }}
                className={`flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-[13px] font-medium transition-all focus-visible:outline focus-visible:outline-2 focus-visible:outline-sky-500 ${
                  isActive
                    ? "bg-sky-50 text-sky-700 font-semibold shadow-xs"
                    : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
                }`}
              >
                <Icon size={17} strokeWidth={isActive ? 2.2 : 1.8} className={isActive ? "text-sky-600" : "text-slate-500"} />
                {item.label}
                {isActive && <span className="ml-auto h-2 w-2 rounded-full bg-sky-600" />}
              </button>
            );
          })}
        </nav>

        <div className="border-t border-slate-200 px-4 py-4">
          <div className="rounded-lg border border-emerald-200 bg-emerald-50/70 p-3">
            <div className="flex items-center justify-between text-[11px]">
              <span className="flex items-center gap-1.5 font-medium text-emerald-900">
                <span className="relative flex h-2 w-2">
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-500 opacity-60" />
                  <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-600" />
                </span>
                INSAT-3DR Telemetry
              </span>
              <span className="font-mono-num text-[10px] text-emerald-700 font-bold">ONLINE</span>
            </div>
            <div className="mt-1 text-[10px] text-emerald-700/80">
              Uplink: 402.75 MHz · 15m Burst
            </div>
          </div>

          <div className="mt-3 flex items-center gap-2.5 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2.5">
            <UserCircle2 size={24} className="text-slate-500" />
            <div className="leading-tight">
              <div className="text-[12px] font-semibold text-slate-800">Station Supervisor</div>
              <div className="text-[10px] text-slate-500">IMD · Surface Met Division</div>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
}
