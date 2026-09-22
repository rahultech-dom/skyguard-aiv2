# SkyGuard AI v2 🛰️

**Real-time AWS anomaly detection with online learning — SIH 2026 PS-26073**

> ⚠️ This is the **v2 improved branch**. Original project is at `SkyGuard-AI-Integration/`.  
> See [`CHANGES.md`](./CHANGES.md) for a full diff of what changed and why.

---

## What's New in v2

| Feature | v1 | v2 |
|---------|----|----|
| ML Model | Isolation Forest (frozen) | **Half-Space Trees** (online, updates every reading) |
| Training Data | 4K rows, 1 synthetic station | **126,432 rows, 12 real Indian cities** (Open-Meteo) |
| Live Data | None | **Open-Meteo polling every 15 min** |
| Fault Testing | Manual button only | **Chaos Monkey** (auto, 40% rate, toggleable from UI) |
| Deployment | Manual only | **Render + Vercel** one-click deploy |

---

## Quick Start (Local)

```bash
# 1. Clone
git clone <this-repo-url>
cd SkyGuard-AI-v2

# 2. Backend setup
cd sih-ml-project-main
pip install -r requirements.txt

# 3. Download real training data (one-time, ~2 min, ~126K rows)
python src/data/fetch_historical.py

# 4. Start backend (auto warm-up + live poller on startup)
uvicorn src.api.app:app --host 127.0.0.1 --port 8000 --reload

# 5. Frontend (new terminal)
cd ../frontend
npm install
npm run dev
```

Open `http://localhost:5173` — the **LIVE · Open-Meteo** badge appears in the top bar within 15 minutes.

---

## Deploy to the Web (Share with Team)

### Step 1 — Push to GitHub
```bash
git remote add origin https://github.com/YOUR_USERNAME/skyguard-ai-v2.git
git push -u origin main
```

### Step 2 — Deploy Backend on Render
1. Go to [render.com](https://render.com) → **New → Web Service**
2. Connect your GitHub repo
3. Render auto-detects `render.yaml` — no config needed
4. Add env var: `GROQ_API_KEY = your_key` (optional — works without it)
5. Click **Deploy** → get URL like `https://skyguard-ai-v2.onrender.com`

### Step 3 — Deploy Frontend on Vercel
1. Go to [vercel.com](https://vercel.com) → **New Project → Import**
2. Select your repo, set **Root Directory = `frontend`**
3. Add env var: `VITE_API_URL = https://skyguard-ai-v2.onrender.com`
4. Click **Deploy** → get URL like `https://skyguard-ai-v2.vercel.app`

**Send `https://skyguard-ai-v2.vercel.app` to your team. Done. ✅**

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/stations` | GET | All 12 AWS stations with live readings |
| `/api/stations/{id}/series` | GET | 60-min sliding window charts |
| `/api/stats` | GET | Network KPI metrics |
| `/api/anomalies` | GET | Recent flagged faults |
| `/api/anomalies/{id}` | GET | Full LangGraph diagnostic |
| `/api/ingest` | POST | Ingest a live reading through ML pipeline |
| `/api/simulate-anomaly` | POST | Inject a test anomaly |
| `/api/live-feed` | GET | **[NEW]** Live poller status + chaos stats |
| `/api/chaos/toggle` | POST | **[NEW]** Toggle Chaos Monkey on/off |

---

## Architecture

```
Open-Meteo API (every 15 min)
        ↓
  live_poller.py  →  chaos_monkey.py (40% fault injection)
        ↓
  /api/ingest
        ↓
  Rule Engine (WMO-No. 8 physical limits)     ← Layer 1
        ↓ (if passes rules)
  Half-Space Trees per station                 ← Layer 2 (online, self-learning)
  + Per-station Z-Score Baseline               ← Layer 3 (adaptive, explainable)
        ↓ (if anomaly)
  LangGraph Agent (5 nodes: SHAP, LLM, Risk)  ← Layer 4
        ↓
  Dashboard (React + Vite + Tailwind)
```

---

*SkyGuard AI v2 — SIH 2026 PS-26073 | IMD / MoES | WMO-No. 8 Compliant*
