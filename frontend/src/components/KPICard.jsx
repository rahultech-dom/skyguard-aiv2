import { useEffect, useState } from "react";
import { ResponsiveContainer, AreaChart, Area } from "recharts";
import { ArrowUpRight, ArrowDownRight, Activity, Radio, AlertTriangle, ShieldCheck } from "lucide-react";

const STATUS_THEMES = {
  good: {
    dot: "bg-emerald-500",
    glow: "shadow-emerald-500/20",
    badge: "bg-emerald-50 border-emerald-200 text-emerald-700",
    stroke: "#10b981",
    fill: "#d1fae5",
    icon: ShieldCheck,
  },
  warn: {
    dot: "bg-amber-500",
    glow: "shadow-amber-500/20",
    badge: "bg-amber-50 border-amber-200 text-amber-700",
    stroke: "#f59e0b",
    fill: "#fef3c7",
    icon: Activity,
  },
  bad: {
    dot: "bg-rose-500",
    glow: "shadow-rose-500/20",
    badge: "bg-rose-50 border-rose-200 text-rose-700",
    stroke: "#f43f5e",
    fill: "#ffe4e6",
    icon: AlertTriangle,
  },
  info: {
    dot: "bg-sky-500",
    glow: "shadow-sky-500/20",
    badge: "bg-sky-50 border-sky-200 text-sky-700",
    stroke: "#0284c7",
    fill: "#e0f2fe",
    icon: Radio,
  },
};

export default function KPICard({
  label,
  value,
  suffix,
  subLabel,
  trend,
  trendDirection = "up",
  status = "good",
  sparkline = [],
  mono = true,
  icon: CustomIcon,
}) {
  const [displayValue, setDisplayValue] = useState(value);
  const theme = STATUS_THEMES[status] || STATUS_THEMES.good;
  const IconComponent = CustomIcon || theme.icon;

  useEffect(() => {
    setDisplayValue(value);
  }, [value]);

  const sparkData = sparkline.map((v, i) => ({ i, v }));
  const trendUp = trendDirection === "up";

  return (
    <div className="group relative overflow-hidden rounded-2xl border border-slate-200/80 bg-white p-5 shadow-xs transition-all duration-300 hover:-translate-y-0.5 hover:border-slate-300 hover:shadow-md">
      {/* Top accent line */}
      <div className={`absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-transparent via-${status === "good" ? "emerald" : status === "bad" ? "rose" : "sky"}-500/40 to-transparent opacity-0 transition-opacity group-hover:opacity-100`} />

      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg border border-slate-100 bg-slate-50 text-slate-600 transition-colors group-hover:border-sky-200 group-hover:bg-sky-50 group-hover:text-sky-700">
            <IconComponent size={14} />
          </div>
          <span className="text-[12px] font-semibold text-slate-600">{label}</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="relative flex h-2 w-2">
            <span className={`absolute inline-flex h-full w-full animate-ping rounded-full ${theme.dot} opacity-60`} />
            <span className={`relative inline-flex h-2 w-2 rounded-full ${theme.dot}`} />
          </span>
        </div>
      </div>

      <div className="mt-3.5 flex items-end justify-between gap-2">
        <div>
          <div className={`flex items-baseline gap-1.5 ${mono ? "font-mono-num" : ""}`}>
            <span className="text-[28px] font-extrabold tracking-tight text-slate-900 tabular">{displayValue}</span>
            {suffix && <span className="text-[12px] font-semibold text-slate-400">{suffix}</span>}
          </div>

          <div className="mt-2 flex flex-wrap items-center gap-1.5">
            {trend && (
              <span
                className={`inline-flex items-center gap-0.5 rounded-md border px-2 py-0.5 text-[11px] font-bold ${
                  trendUp
                    ? "border-emerald-200 bg-emerald-50 text-emerald-700"
                    : "border-rose-200 bg-rose-50 text-rose-700"
                }`}
              >
                {trendUp ? <ArrowUpRight size={12} strokeWidth={2.5} /> : <ArrowDownRight size={12} strokeWidth={2.5} />}
                {trend}
              </span>
            )}
            {subLabel && (
              <span className="text-[11px] font-medium text-slate-400">{subLabel}</span>
            )}
          </div>
        </div>

        {sparkline.length > 0 && (
          <div className="h-10 w-24 opacity-80 transition-opacity group-hover:opacity-100">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={sparkData}>
                <defs>
                  <linearGradient id={`grad-${label.replace(/\s+/g, "")}`} x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={theme.stroke} stopOpacity={0.3} />
                    <stop offset="95%" stopColor={theme.stroke} stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <Area
                  type="monotone"
                  dataKey="v"
                  stroke={theme.stroke}
                  strokeWidth={2}
                  fill={`url(#grad-${label.replace(/\s+/g, "")})`}
                  dot={false}
                  isAnimationActive={false}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>
    </div>
  );
}
