import { Link } from "react-router-dom";
import {
  Zap,
  Snowflake,
  WifiOff,
  TrendingDown,
  ArrowDown,
  Radio,
  BrainCircuit,
  ShieldCheck,
  Database,
  Sparkles,
  Search,
  MessageSquareText,
} from "lucide-react";
import Navbar from "../components/Navbar";
import Button from "../components/Button";
import AtmosphericVisual from "../components/AtmosphericVisual";
import { PROBLEM_CARDS, PIPELINE_STEPS, NETWORK_STATS } from "../data/mockData";

const PROBLEM_ICONS = [Zap, Snowflake, WifiOff, TrendingDown];
const PIPELINE_ICONS = [Database, ShieldCheck, Sparkles, BrainCircuit, Search, MessageSquareText, Radio];

function useCounterFormat(n) {
  return n.toLocaleString("en-IN");
}

export default function Landing() {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <Navbar />

      {/* ---------------- HERO ---------------- */}
      <section className="relative overflow-hidden border-b border-slate-200 bg-gradient-to-b from-sky-50/70 via-white to-slate-50">
        <div className="mx-auto grid max-w-7xl gap-12 px-6 pb-20 pt-16 md:grid-cols-2 md:items-center md:pt-24">
          <div className="animate-rise">
            <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-sky-200 bg-sky-50 px-3.5 py-1.5 text-[11px] font-bold tracking-wide text-sky-800 shadow-xs">
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-500 opacity-60" />
                <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-600" />
              </span>
              WMO-NO. 8 & 488 QC COMPLIANT · NATIONAL AWS SURVEILLANCE
            </div>

            <h1 className="text-4xl font-extrabold leading-[1.12] tracking-tight text-slate-900 sm:text-5xl lg:text-[3.2rem]">
              Autonomous Anomaly Detection for{" "}
              <span className="text-sky-600">Automatic Weather Stations.</span>
            </h1>

            <p className="mt-6 max-w-xl text-[16px] leading-relaxed text-slate-600 font-medium">
              Built for India's surface meteorological observation network. SkyGuard AWS continuously
              verifies Temperature, Barometric Pressure, Relative Humidity, Wind, and Rain telemetry—identifying
              RTD sensor spikes, tipping bucket clogs, and calibration drift before bad data corrupts
              national numerical weather models.
            </p>

            <div className="mt-9 flex flex-wrap items-center gap-4">
              <Button as={Link} to="/dashboard" icon>
                Open AWS Command Center
              </Button>
              <Button as="a" href="#how-it-works" variant="secondary">
                WMO QC Pipeline
              </Button>
            </div>

            <div className="mt-12 grid max-w-md grid-cols-3 gap-6 border-t border-slate-200 pt-6">
              <div>
                <div className="font-mono-num text-2xl font-bold text-slate-900">{NETWORK_STATS.stationsTotal} Nodes</div>
                <div className="mt-1 text-[11px] font-semibold text-slate-400">National AWS Grid</div>
              </div>
              <div>
                <div className="font-mono-num text-2xl font-bold text-slate-900">INSAT-3DR</div>
                <div className="mt-1 text-[11px] font-semibold text-slate-400">DCP 402.75 MHz</div>
              </div>
              <div>
                <div className="font-mono-num text-2xl font-bold text-slate-900">IMD / MoES</div>
                <div className="mt-1 text-[11px] font-semibold text-slate-400">SIH PS 26073</div>
              </div>
            </div>
          </div>

          <div className="animate-rise" style={{ animationDelay: "120ms" }}>
            <AtmosphericVisual />
          </div>
        </div>
      </section>

      {/* ---------------- THE PROBLEM ---------------- */}
      <section id="platform" className="border-b border-slate-200 bg-white">
        <div className="mx-auto max-w-7xl px-6 py-20">
          <div className="max-w-xl">
            <span className="text-[11px] font-bold uppercase tracking-[0.18em] text-sky-600">
              Meteorological Hardware Challenges
            </span>
            <h2 className="mt-3 text-3xl font-extrabold tracking-tight text-slate-900">
              Unattended AWS Sensors Fail Silently.
            </h2>
            <p className="mt-4 text-[15px] leading-relaxed text-slate-600 font-medium">
              Automatic Weather Stations operate autonomously in extreme environments—from Rajasthan's 50°C heat
              to coastal monsoon salt spray. Hardware faults rarely declare themselves; they quietly corrupt
              synoptic records until detected by mathematical quality control.
            </p>
          </div>

          <div className="mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {PROBLEM_CARDS.map((card, i) => {
              const Icon = PROBLEM_ICONS[i];
              return (
                <div
                  key={card.title}
                  className="group rounded-xl border border-slate-200 bg-slate-50/70 p-6 transition-all duration-300 hover:border-slate-300 hover:bg-white hover:shadow-md"
                >
                  <div className="mb-5 flex h-10 w-10 items-center justify-center rounded-lg border border-sky-200 bg-sky-50 text-sky-600 transition-colors group-hover:bg-sky-600 group-hover:text-white">
                    <Icon size={18} strokeWidth={2} />
                  </div>
                  <h3 className="text-[15px] font-bold text-slate-900">{card.title}</h3>
                  <p className="mt-2 text-[13px] leading-relaxed text-slate-600">{card.detail}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* ---------------- HOW SKYGUARD THINKS ---------------- */}
      <section id="how-it-works" className="border-b border-slate-200 bg-slate-50/70">
        <div className="mx-auto max-w-7xl px-6 py-20">
          <div className="max-w-xl">
            <span className="text-[11px] font-bold uppercase tracking-[0.18em] text-sky-600">
              WMO Multi-Tier Quality Control Pipeline
            </span>
            <h2 className="mt-3 text-3xl font-extrabold tracking-tight text-slate-900">
              From INSAT Sensor Packets to Explained Actions.
            </h2>
          </div>

          <div className="mt-14 flex flex-col gap-3 lg:flex-row lg:items-stretch lg:gap-2">
            {PIPELINE_STEPS.map((step, i) => {
              const Icon = PIPELINE_ICONS[i];
              return (
                <div key={step.id} className="flex flex-1 items-center lg:flex-col">
                  <div className="group relative flex-1 rounded-xl border border-slate-200 bg-white p-5 shadow-sm transition-all duration-300 hover:-translate-y-0.5 hover:border-sky-300 hover:shadow-md">
                    <div className="mb-4 flex h-8 w-8 items-center justify-center rounded-lg bg-sky-50 border border-sky-200 text-sky-600">
                      <Icon size={16} strokeWidth={2} />
                    </div>
                    <div className="text-[13px] font-bold text-slate-900">{step.title}</div>
                    <p className="mt-2 max-h-0 overflow-hidden text-[12px] leading-relaxed text-slate-600 opacity-0 transition-all duration-300 group-hover:max-h-36 group-hover:opacity-100">
                      {step.detail}
                    </p>
                  </div>
                  {i < PIPELINE_STEPS.length - 1 && (
                    <div className="flex shrink-0 items-center justify-center px-1 py-2 text-slate-400 lg:rotate-0 lg:py-1">
                      <ArrowDown size={14} className="hidden lg:block lg:-rotate-90" />
                      <ArrowDown size={14} className="lg:hidden" />
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* ---------------- INTELLIGENCE ---------------- */}
      <section id="intelligence" className="border-b border-slate-200 bg-white">
        <div className="mx-auto max-w-7xl px-6 py-20">
          <div className="max-w-xl">
            <span className="text-[11px] font-bold uppercase tracking-[0.18em] text-sky-600">
              Meteorological AI & Quality Control
            </span>
            <h2 className="mt-3 text-3xl font-extrabold tracking-tight text-slate-900">
              Detect. Explain. Maintain.
            </h2>
          </div>

          <div className="mt-12 grid gap-5 lg:grid-cols-3">
            <IntelligenceCard
              title="Online Machine Learning (Half-Space Trees)"
              desc="Continuously updates with every live 15-min reading from Open-Meteo, adapting to seasonal microclimate drift across 12 Indian cities without static frozen models."
            >
              <MiniDetectViz />
            </IntelligenceCard>
            <IntelligenceCard
              title="Z-Score Feature Explainability"
              desc="Quantifies real-time statistical deviations across temperature deltas, rolling variance, and barometric tendencies at microsecond latency."
            >
              <MiniExplainViz />
            </IntelligenceCard>
            <IntelligenceCard
              title="LangGraph Agentic Diagnostics & Chaos"
              desc="Grounded multi-node GenAI diagnosis powered by Groq LLMs (openai/gpt-oss-120b & Qwen), stress-tested with automated Chaos Monkey fault injection."
            >
              <MiniRespondViz />
            </IntelligenceCard>
          </div>
        </div>
      </section>

      {/* ---------------- LIVE NETWORK PREVIEW ---------------- */}
      <section id="monitoring" className="border-b border-slate-200 bg-slate-50/80">
        <div className="mx-auto max-w-7xl px-6 py-20">
          <div className="flex flex-col items-start justify-between gap-8 lg:flex-row lg:items-end">
            <div>
              <span className="text-[11px] font-bold uppercase tracking-[0.18em] text-sky-600">
                National Synoptic Overview
              </span>
              <h2 className="mt-3 max-w-lg text-3xl font-extrabold tracking-tight text-slate-900">
                Continuous surveillance of all {NETWORK_STATS.stationsTotal} AWS observation nodes.
              </h2>
            </div>
            <Button as={Link} to="/dashboard" icon>
              Open AWS Command Center
            </Button>
          </div>

          <div className="mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <PreviewStat label="AWS Stations Online" value={`${NETWORK_STATS.stationsOnline}`} suffix={`/ ${NETWORK_STATS.stationsTotal}`} status="good" />
            <PreviewStat label="Observations Analyzed" value={useCounterFormat(NETWORK_STATS.observations)} status="info" />
            <PreviewStat label="WMO Data Quality" value={`${NETWORK_STATS.dataQuality}%`} status="good" />
            <PreviewStat label="Flagged Anomalies" value={`${NETWORK_STATS.activeAnomalies}`} status="warn" />
          </div>
        </div>
      </section>

      {/* ---------------- FOOTER ---------------- */}
      <footer className="bg-white border-t border-slate-200">
        <div className="mx-auto flex max-w-7xl flex-col gap-8 px-6 py-14 md:flex-row md:items-start md:justify-between">
          <div>
            <div className="text-[15px] font-bold tracking-[0.14em] text-slate-900">
              SKYGUARD <span className="text-sky-600">AWS</span>
            </div>
            <p className="mt-2 max-w-sm text-[13px] text-slate-500 font-medium">
              National Automatic Weather Station Telemetry & Anomaly Surveillance System.
            </p>
          </div>
          <div className="flex flex-col gap-1 text-[12px] text-slate-500 font-medium md:items-end">
            <span className="font-bold text-slate-800">Smart India Hackathon 2026 · PS 26073</span>
            <span>Ministry of Earth Sciences (MoES) & India Meteorological Department (IMD)</span>
            <span>WMO-No. 8 & WMO-No. 488 Quality Control Standards</span>
          </div>
        </div>
      </footer>
    </div>
  );
}

function IntelligenceCard({ title, desc, children }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm transition-all duration-300 hover:border-slate-300 hover:shadow-md">
      <div className="mb-6 flex h-28 items-center justify-center rounded-lg border border-slate-200 bg-slate-50">
        {children}
      </div>
      <h3 className="text-[15px] font-bold text-slate-900">{title}</h3>
      <p className="mt-2 text-[13px] leading-relaxed text-slate-600 font-medium">{desc}</p>
    </div>
  );
}

function MiniDetectViz() {
  return (
    <svg viewBox="0 0 200 80" className="h-16 w-full px-4">
      <polyline
        points="0,50 20,48 40,52 60,46 80,50 95,20 110,55 130,48 150,50 170,47 200,49"
        fill="none"
        stroke="#0284c7"
        strokeWidth="2"
      />
      <circle cx="95" cy="20" r="4" fill="#dc2626">
        <animate attributeName="r" values="3;6;3" dur="1.6s" repeatCount="indefinite" />
      </circle>
    </svg>
  );
}

function MiniExplainViz() {
  const bars = [82, 61, 31, 8];
  return (
    <div className="flex w-full flex-col gap-2 px-6">
      {bars.map((v, i) => (
        <div key={i} className="flex items-center gap-2">
          <div className="h-2 flex-1 rounded-full bg-slate-100">
            <div
              className="h-2 rounded-full bg-sky-500"
              style={{ width: `${v}%`, opacity: 1 - i * 0.15 }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}

function MiniRespondViz() {
  return (
    <div className="flex items-center gap-3 px-6">
      <div className="relative flex h-14 w-14 items-center justify-center rounded-full border-2 border-amber-400 bg-amber-50">
        <span className="font-mono-num text-sm font-bold text-amber-800">78</span>
      </div>
      <div className="text-[11px] font-bold leading-tight text-slate-600">
        Maintenance
        <br />
        Risk Score
      </div>
    </div>
  );
}

function PreviewStat({ label, value, suffix, status }) {
  const colors = {
    good: "text-emerald-700",
    warn: "text-amber-700",
    info: "text-sky-700",
  };
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex items-baseline gap-1.5">
        <span className={`font-mono-num text-2xl font-bold ${colors[status]}`}>{value}</span>
        {suffix && <span className="font-mono-num text-sm text-slate-400 font-medium">{suffix}</span>}
      </div>
      <div className="mt-2 text-[12px] text-slate-500 font-medium">{label}</div>
    </div>
  );
}
