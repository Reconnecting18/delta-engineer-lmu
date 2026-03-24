# Delta Engineer
## LMU Telemetry Analysis API

A standalone service that processes **Le Mans Ultimate** sim racing telemetry data and connects to **E3N** (local AI system) via the `/ingest` endpoint. Covers telemetry parsing, lap/sector analysis, setup correlation, and real-time race engineering alerts.

---

## Overview

This API acts as the data backbone between your sim and your AI race engineer. It captures raw telemetry from Le Mans Ultimate, processes it into structured sessions and laps, runs analysis on driver performance and car setup, and serves real-time alerts — all through a clean REST (and WebSocket) interface.

### How It Fits Together

```
Le Mans Ultimate
    │
    ▼
┌─────────────────────┐
│   Electron Client   │  ← Reads shared memory / UDP telemetry
│   (Capture + UI)    │  ← Displays dashboards, graphs, alerts
└────────┬────────────┘
         │ POST /telemetry
         ▼
┌─────────────────────┐
│   LMU Telemetry API │  ← This project
│                     │  ← Parses, stores, analyzes
└────────┬────────────┘
         │ POST /ingest
         ▼
┌─────────────────────┐
│       E3N           │  ← Local AI system
│  (Anthropic API)    │  ← Natural language race engineering
└─────────────────────┘
```

---

## Features

**Telemetry Ingestion** — Accept raw or pre-parsed telemetry frames via HTTP. Supports single-frame and batch payloads with validation and error reporting.

**Session Management** — Automatically groups telemetry by driver, car, track, and session time. Detects session boundaries from sim state changes or telemetry gaps.

**Lap & Sector Analysis** — Detects lap boundaries, computes sector times, top speed, tire data, fuel consumption, and incident flags. Supports lap-to-lap comparison with delta breakdowns.

**Setup Correlation** — Links car setup parameters (aero, suspension, differential, pressures, etc.) to performance metrics. Identifies which setup changes produced measurable lap time deltas.

**Real-Time Alerts** — Configurable rules engine for race engineering alerts (tire temps, fuel strategy, brake temps, lap degradation). Delivered via REST polling or live WebSocket stream.

**E3N Integration** — Exposes a `/ingest` endpoint for E3N to consume processed telemetry and analysis, enabling AI-driven race engineering insights via the Anthropic API.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| API Framework | TBD (FastAPI / Express) |
| Database | TBD (SQLite / PostgreSQL) |
| Real-Time | WebSockets |
| Client | Electron + React |
| AI Integration | E3N → Anthropic API |
| Language | Python or TypeScript (TBD) |

---

## Project Structure

> **Note:** This structure is planned and will evolve as development progresses.

```
lmu-telemetry-api/
├── src/
│   ├── api/                # Route handlers / endpoints
│   │   ├── telemetry.py    # POST /telemetry
│   │   ├── sessions.py     # /sessions CRUD
│   │   ├── laps.py         # /sessions/{id}/laps, /laps/compare
│   │   ├── setups.py       # /setups CRUD + correlation
│   │   ├── alerts.py       # /alerts + /alerts/rules
│   │   └── ingest.py       # POST /ingest (E3N contract)
│   ├── core/               # Business logic
│   │   ├── parser.py       # Raw telemetry parser (binary → structured)
│   │   ├── lap_detection.py
│   │   ├── lap_analysis.py
│   │   ├── setup_correlation.py
│   │   └── alert_engine.py
│   ├── models/             # Data models / schemas
│   ├── db/                 # Database setup and migrations
│   └── config.py           # Environment and app configuration
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/           # Sample telemetry payloads
├── docs/
│   └── telemetry-format.md # LMU data format reference spec
├── assets/                 # Icons, tray icons
├── .env.example
├── .gitignore
├── README.md
└── package.json / pyproject.toml
```

---

## Getting Started

### Prerequisites

- Python 3.11+ or Node.js 20+ (depending on chosen stack)
- Git

### Installation

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/lmu-telemetry-api.git
cd lmu-telemetry-api

# Install dependencies (Python example)
pip install -r requirements.txt

# Or Node.js example
npm install
```

### Configuration

Copy the example environment file and update values:

```bash
cp .env.example .env
```

Key configuration options:

| Variable | Description | Default |
|----------|-------------|---------|
| `PORT` | API server port | `8000` |
| `DATABASE_URL` | Database connection string | `sqlite:///telemetry.db` |
| `LOG_LEVEL` | Logging verbosity | `info` |
| `E3N_ENABLED` | Enable E3N integration | `false` |
| `E3N_ENDPOINT` | E3N ingest URL | `http://localhost:3000/ingest` |

### Running the API

```bash
# Development
python -m uvicorn src.main:app --reload    # FastAPI
# or
npm run dev                                 # Express

# Production
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000
```

### Health Check

```bash
curl http://localhost:8000/health
# → { "status": "ok", "version": "0.1.0" }
```

---

## API Endpoints

> Full interactive documentation available at `/docs` (Swagger UI) when the server is running.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/telemetry` | Ingest raw/parsed telemetry frames |
| `POST` | `/sessions` | Create a new session |
| `GET` | `/sessions` | List all sessions |
| `GET` | `/sessions/{id}` | Get session detail |
| `GET` | `/sessions/{id}/laps` | Get lap summaries for a session |
| `GET` | `/laps/compare` | Compare laps by ID |
| `POST` | `/setups` | Upload a car setup |
| `GET` | `/setups` | List setups (filterable) |
| `GET` | `/setups/correlate` | Correlate setups to performance |
| `GET` | `/alerts` | Get triggered alerts |
| `POST` | `/alerts/rules` | Create alert rules |
| `GET` | `/alerts/rules` | List active rules |
| `WS` | `/ws/alerts` | Live alert stream |
| `POST` | `/ingest` | E3N integration endpoint |

---

## Roadmap

- [x] Project scaffolding and repo setup
- [ ] **Milestone 1** — Project scaffolding, data models, config management
- [ ] **Milestone 2** — Telemetry ingestion, parsing, session management
- [ ] **Milestone 3** — Lap & sector analysis, lap comparison
- [ ] **Milestone 4** — Setup data model, correlation engine
- [ ] **Milestone 5** — Alert rules engine, WebSocket streaming
- [ ] **Milestone 6** — API hardening, OpenAPI docs, integration tests, E3N `/ingest` contract
- [ ] **Milestone 7** — Electron UI (telemetry dashboard, lap graphs, setup manager, alerts feed)
- [ ] **Milestone 8** — E3N AI integration (natural language race engineering)

---

## Related Projects

- **E3N** — Local AI race engineer system (Electron app, connects to Anthropic API)
- **Le Mans Ultimate** — Official WEC sim racing title by Studio 397

---

## Contributing

This project is in early development. If you'd like to contribute:

1. Check the [Issues](../../issues) tab for open tasks
2. Fork the repo and create a feature branch
3. Submit a pull request with a clear description of what you changed and why

---

## License

TBD

---

## Acknowledgments

Built for the sim racing community. Inspired by tools like Coach Dave Delta, TrackTitan, MoTeC i2, and the broader sim racing data analysis ecosystem.
