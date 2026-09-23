import { useState } from "react";
import { Radio, RefreshCw, Skull, Sparkles } from "lucide-react";

export default function LiveFeedBadge({
  isLive = true,
  chaosEnabled = false,
  onToggleChaos,
  onToggleMode,
  faultsInjected = 0,
}) {
  const [toggling, setToggling] = useState(false);

  const handleChaosClick = async () => {
    setToggling(true);
    try {
      if (onToggleChaos) await onToggleChaos();
    } finally {
      setToggling(false);
    }
  };

  return (
    <div className="inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-slate-50/90 p-1 shadow-xs backdrop-blur-xs">
      {/* Mode Switcher: Live Open-Meteo vs Simulation */}
      <button
        onClick={onToggleMode}
        type="button"
        className={`flex items-center gap-1.5 rounded-full px-3 py-1 text-[11px] font-bold transition-all cursor-pointer ${
          isLive
            ? "border border-emerald-300/80 bg-emerald-500 text-white shadow-xs"
            : "border border-slate-200 bg-white text-slate-600 hover:bg-slate-100"
        }`}
        title={isLive ? "Currently polling live Open-Meteo weather API (Click to switch to simulation mode)" : "Simulation Mode active (Click to connect to live Open-Meteo feed)"}
      >
        <Radio size={11} className={isLive ? "animate-pulse" : "text-slate-400"} />
        <span>{isLive ? "LIVE · Open-Meteo" : "SIMULATION MODE"}</span>
      </button>

      {/* Chaos Monkey Toggle */}
      <button
        onClick={handleChaosClick}
        disabled={toggling}
        type="button"
        className={`flex items-center gap-1.5 rounded-full border px-3 py-1 text-[11px] font-bold transition-all cursor-pointer ${
          chaosEnabled
            ? "border-rose-400 bg-rose-500 text-white shadow-xs animate-pulse"
            : "border-slate-200 bg-white text-slate-600 hover:bg-slate-100"
        }`}
        title={
          chaosEnabled
            ? `Chaos Monkey is ACTIVE (${faultsInjected} faults injected into live stream). Click to disable.`
            : "Chaos Monkey is OFF. Click to enable 40% random sensor fault injection."
        }
      >
        <Skull size={11} className={chaosEnabled ? "text-white" : "text-slate-500"} />
        <span>{chaosEnabled ? `CHAOS ON (${faultsInjected})` : "CHAOS OFF"}</span>
      </button>
    </div>
  );
}
