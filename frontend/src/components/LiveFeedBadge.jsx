/**
 * SkyGuard AI v2 — LiveFeedBadge Component
 * Shows real-time status of the Open-Meteo live poller and Chaos Monkey toggle.
 * Displayed in the Dashboard top bar.
 */

import { useEffect, useState } from "react";
import { Wifi, WifiOff, Skull } from "lucide-react";
import { getLiveFeedStatus, toggleChaos } from "../services/api";

export default function LiveFeedBadge() {
  const [feed, setFeed] = useState(null);
  const [togglingChaos, setTogglingChaos] = useState(false);

  useEffect(() => {
    // Fetch live-feed status on mount and every 30s
    const refresh = async () => {
      try {
        const data = await getLiveFeedStatus();
        setFeed(data);
      } catch {
        setFeed(null);
      }
    };
    refresh();
    const interval = setInterval(refresh, 30_000);
    return () => clearInterval(interval);
  }, []);

  const handleChaosToggle = async () => {
    setTogglingChaos(true);
    try {
      const result = await toggleChaos();
      setFeed((prev) => prev ? { ...prev, chaos_enabled: result.chaos_enabled } : prev);
    } finally {
      setTogglingChaos(false);
    }
  };

  const isLive = feed?.source === "open-meteo" && feed?.last_poll;

  return (
    <div className="flex items-center gap-2">
      {/* Live / Mock indicator */}
      <div
        className={`flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] font-bold shadow-xs
          ${isLive
            ? "border-emerald-200 bg-emerald-50 text-emerald-800"
            : "border-slate-200 bg-slate-100 text-slate-500"}`}
        title={isLive ? `Last poll: ${feed.last_poll}` : "Offline — using mock data"}
      >
        {isLive ? <Wifi size={11} /> : <WifiOff size={11} />}
        {isLive ? "LIVE · Open-Meteo" : "MOCK DATA"}
      </div>

      {/* Chaos Monkey toggle */}
      {feed && (
        <button
          onClick={handleChaosToggle}
          disabled={togglingChaos}
          title={feed.chaos_enabled
            ? `Chaos ON — ${feed.faults_injected} faults injected. Click to disable.`
            : "Chaos OFF — Click to enable fault injection"}
          className={`flex items-center gap-1 rounded-full border px-2.5 py-1 text-[11px] font-bold shadow-xs transition-all
            ${feed.chaos_enabled
              ? "border-rose-300 bg-rose-50 text-rose-700 hover:bg-rose-100"
              : "border-slate-200 bg-white text-slate-500 hover:bg-slate-50"}`}
        >
          <Skull size={11} />
          {feed.chaos_enabled ? `CHAOS ON (${feed.faults_injected})` : "CHAOS OFF"}
        </button>
      )}
    </div>
  );
}
