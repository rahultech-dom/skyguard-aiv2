# SkyGuard AI v2 — Changes Log

> **Original repo:** `SkyGuard-AI-Integration/`  
> **This repo:** `SkyGuard-AI-v2/` — original untouched, all changes here only.

---

## 🆕 New Files Added

### Backend

| File | Purpose |
|------|---------|
| `src/data/fetch_historical.py` | Fetches ~10,600 real hourly data points per station (2022-01-01 → 2023-03-15) from Open-Meteo Historical API for all 12 Indian AWS city locations. Creates `data/weather_data_real.csv` (~127K rows total). |
| `src/model/online_model.py` | **Half-Space Trees** online anomaly detector (river library). Replaces static Isolation Forest. Updates with every incoming reading — never frozen. Also includes per-station Z-score adaptive baseline (rolling 168-hour window). |
| `src/api/live_poller.py` | Async background task that polls Open-Meteo Current Weather API every 15 minutes for all 12 stations and pushes readings through the ML pipeline via `store.ingest_reading()`. |
| `src/api/chaos_monkey.py` | Randomly injects realistic sensor hardware faults (temperature spike, freeze/flatline, humidity=0, pressure spike, calibration drift) into live readings before ML scoring. Fault rate: 40%. |

### Frontend

| File | Purpose |
|------|---------|
| `frontend/src/components/LiveFeedBadge.jsx` | Dashboard top-bar badge showing LIVE/MOCK status, last poll time, and a Chaos ON/OFF toggle button. |

### Deployment

| File | Purpose |
|------|---------|
| `render.yaml` | One-click Render.com deployment config for the FastAPI backend. Build command also runs `fetch_historical.py` to download real data on deploy. |
| `frontend/vercel.json` | Vercel deployment config for the React frontend. SPA rewrite rules included. |
| `.env.example` | Documents all required environment variables. |

---

## ✏️ Modified Files

### Backend

| File | What Changed |
|------|-------------|
| `src/predict.py` | **Completely rewritten.** Now routes to `OnlineAnomalyModel.predict_and_learn()` instead of the frozen Isolation Forest. Same public API signature — backward compatible. |
| `src/api/app.py` | Added `@app.on_event("startup")` that warms up the online model from real CSV data, then launches the live poller as a background asyncio task. Added `GET /api/live-feed` and `POST /api/chaos/toggle` endpoints. |
| `requirements.txt` | Added `river==0.21.2` (online ML), `httpx>=0.27.0` (async HTTP for poller), `requests>=2.31.0` (sync HTTP for historical fetch). |

### Frontend

| File | What Changed |
|------|-------------|
| `frontend/src/services/api.js` | Updated header comment. Added `getLiveFeedStatus()` and `toggleChaos()` functions for the new backend endpoints. `VITE_API_URL` env var already supported — works for deployed backend. |

---

## 🗑️ What Was NOT Changed (Preserved from v1)

- `src/api/state_store.py` — same ring-buffer store, same station list
- `src/pipeline/` — all LangGraph nodes, graph, tools, state unchanged
- `src/data_preprocessing.py` — kept for reference (not used by new model)
- `src/train.py` — kept for reference (not used by new model)
- `src/explain.py` — SHAP explanation still used in LangGraph pipeline
- `src/evaluation.py` — kept
- All frontend pages, components (except api.js + added LiveFeedBadge)
- All mock data in `frontend/src/data/mockData.js`

---

## 🔄 Key Architecture Differences vs v1

| Aspect | v1 (Original) | v2 (This Repo) |
|--------|--------------|----------------|
| ML Model | Isolation Forest (frozen after training) | Half-Space Trees (updates every reading) |
| Training data | 4,000 rows, 1 synthetic station, ~0.7°C temps | ~127,000 rows, 12 real Indian cities, real temps |
| Data source | Synthetic CSV | Open-Meteo Historical API (real WMO data) |
| Live data | None (only simulate button) | Open-Meteo Current Weather, polled every 15 min |
| Model improvement | Never (static) | Continuously, with every new reading |
| Fault injection | Manual button only | Automatic Chaos Monkey (40% rate, toggleable) |
| Deployment | Manual only | Render (backend) + Vercel (frontend) configs included |

---

## 🚀 How to Run Locally

```bash
# Step 1 — Download real training data (one-time, ~2 min)
cd sih-ml-project-main
python src/data/fetch_historical.py

# Step 2 — Install dependencies
pip install -r requirements.txt

# Step 3 — Start backend (model warms up from CSV automatically)
uvicorn src.api.app:app --host 127.0.0.1 --port 8000 --reload

# Step 4 — Start frontend (new terminal)
cd frontend
npm install && npm run dev
```

Visit `http://localhost:5173` — the Live Feed badge will show **LIVE · Open-Meteo** within 15 minutes of the first poll cycle.

---

## 🌐 How to Deploy

### Backend → Render.com
1. Push `SkyGuard-AI-v2` to a GitHub repo
2. Go to [render.com](https://render.com) → New → Web Service
3. Connect your repo → Render auto-detects `render.yaml`
4. Add env var: `GROQ_API_KEY=your_key`
5. Deploy → get URL like `https://skyguard-ai-v2.onrender.com`

### Frontend → Vercel
1. Go to [vercel.com](https://vercel.com) → New Project → Import repo
2. Set **Root Directory** = `frontend`
3. Add env var: `VITE_API_URL=https://skyguard-ai-v2.onrender.com`
4. Deploy → get URL like `https://skyguard-ai-v2.vercel.app`

Share `https://skyguard-ai-v2.vercel.app` with your team. ✅

---

*SkyGuard AI v2 — SIH 2026 PS-26073*
