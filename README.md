# AI-Based Farmer Query Support and Advisory System

Responsive web app with a **Node.js (Express)** front door and a **Python (Flask)** analytics service. The UI matches a clean “trending modules” layout: crop recommendation, yield planning, leaf photo check, tool ideas, and a five-day weather strip (Open-Meteo, no API key).

## Prerequisites

- [Node.js 18+](https://nodejs.org/)
- [Python 3.10+](https://www.python.org/) (tested on Python 3.14 with wheels for Flask and Pillow)

## Run locally (two terminals)

**Terminal 1 — Python API (port 8000)**

```powershell
cd "python-service"
python -m pip install -r requirements.txt
python main.py
```

**Terminal 2 — Node server + static UI (port 3000)**

```powershell
cd ".."
npm install
npm start
```

Open **http://localhost:3000**. The browser calls `/api/...` on the same origin; Express proxies ML routes to Flask at `http://127.0.0.1:8000`.

The `waitress` package is listed for Windows-friendly production serving if you choose to wire it up later; `python main.py` is enough for local demos.

## What each part does

| Area | Stack | Role |
|------|--------|------|
| Farmer Q&A | Node | `POST /api/advisory` — keyword/heuristic answers |
| Crop recommendation | Python | Rules over soil, pH, rainfall, temperature, season |
| Yield estimate | Python | Transparent multipliers on a baseline quintals/acre table |
| Crop health | Python | Pillow image stats (greenness, stress, contrast) — not a certified diagnosis |
| Tools | Python | Task + crop family → implement shortlist |
| Weather | Python | Proxies [Open-Meteo](https://open-meteo.com/) forecast JSON |

## Environment variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `PORT` | `3000` | Express listen port |
| `PYTHON_SERVICE_URL` | `http://127.0.0.1:8000` | Upstream Flask URL for the proxy |
| `PORT` (Python) | `8000` | Set when running `python main.py` (Flask `app.run`) |

## Limitations

Heuristic models are for **demonstration and planning**, not regulatory or certified agronomic advice. Always validate decisions with local extension services and field observations.
