# Delta Engineer

**LMU Telemetry Analysis API** — a standalone service that processes [Le Mans Ultimate](https://www.lemansultimate.com/) sim racing telemetry and feeds structured insights to [E3N](https://github.com/Reconnecting18) (AI race engineer) via `/ingest`.

Built with **FastAPI** + **async SQLAlchemy**. Accepts telemetry at ~50 Hz, groups it into sessions, and will eventually provide lap analysis, setup correlation, and real-time race engineering alerts.

---

## Architecture

```
Le Mans Ultimate (sim)
    |
    v
+---------------------+
|   Electron Client   |  <-- Reads shared memory from LMU
|   (Capture + UI)    |  <-- Displays dashboards, graphs, alerts
+---------+-----------+
          | POST /telemetry
          v
+---------------------+
|  Delta Engineer API  |  <-- THIS PROJECT
|                     |  <-- Parses, stores, analyzes
+---------+-----------+
          | POST /ingest
          v
+---------------------+
|        E3N          |  <-- Separate Electron app (already exists)
|   (Anthropic API)   |  <-- AI-powered race engineering insights
+---------------------+
```

**This API is the data processing layer** between the sim and the AI. The Electron client captures telemetry from LMU's shared memory and POSTs it here. E3N is a separate project that consumes the processed output.

---

## Quick Start

```bash
# Clone and install
git clone https://github.com/Reconnecting18/delta-engineer-lmu.git
cd delta-engineer-lmu
pip install -e ".[dev]"

# Configure
cp .env.example .env

# Run
python -m uvicorn src.main:app --reload

# Verify
curl http://localhost:8000/health
# {"status":"ok","version":"0.1.0","environment":"development"}
```

Interactive API docs available at **http://localhost:8000/docs** (Swagger UI).

### Running Tests

```bash
pytest -v              # All tests (66 total)
pytest tests/unit/     # Unit tests only
pytest tests/integration/  # Integration tests only
```

---

## What's Working (Milestones 1-2)

### Telemetry Ingestion

Send telemetry frames via `POST /telemetry`. Supports single frames and batch payloads.

```bash
# Create a session
curl -X POST http://localhost:8000/sessions/ \
  -H "Content-Type: application/json" \
  -d '{
    "track_name": "Le Mans 24h Circuit",
    "car_name": "Toyota GR010 Hybrid",
    "driver_name": "Player",
    "session_type": "practice"
  }'
# {"id":1,"track_name":"Le Mans 24h Circuit",...}

# Ingest telemetry frames
curl -X POST http://localhost:8000/telemetry/ \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": 1,
    "frames": [{
      "timestamp": "2026-03-24T14:30:00Z",
      "lap_number": 3,
      "sector": 2,
      "throttle": 0.85,
      "brake": 0.0,
      "steering": -0.12,
      "gear": 4,
      "speed": 245.6,
      "rpm": 8500.0,
      "fuel_level": 42.5,
      "tire_temps": {"front_left":95.2,"front_right":96.1,"rear_left":98.0,"rear_right":97.5},
      "tire_pressures": {"front_left":172.0,"front_right":173.0,"rear_left":165.0,"rear_right":166.0}
    }]
  }'
# {"session_id":1,"frames_received":1,"frames_stored":1,"frames_failed":0,...}
```

### Session Auto-Detection

Omit `session_id` and provide track/car/driver context instead. The API will automatically find or create the right session, detecting boundaries via time gaps (configurable, default 5 min) and session type changes.

```bash
curl -X POST http://localhost:8000/telemetry/ \
  -H "Content-Type: application/json" \
  -d '{
    "track_name": "Monza",
    "car_name": "Ferrari 499P",
    "session_type": "qualifying",
    "frames": [{"timestamp":"2026-03-24T14:30:00Z","lap_number":1,"throttle":0.9,"brake":0.0,"steering":0.0,"gear":5,"speed":310.2}]
  }'
```

### Session Management

```bash
# List sessions (paginated, filterable)
curl "http://localhost:8000/sessions/?track_name=Monza&session_type=practice&limit=10"

# Get session detail (includes frame count)
curl http://localhost:8000/sessions/1

# End a session
curl -X PATCH http://localhost:8000/sessions/1 \
  -H "Content-Type: application/json" \
  -d '{"ended_at": "2026-03-24T16:00:00Z"}'
```

### rF2 Telemetry Parser

The parser module (`src/core/parser.py`) converts rFactor 2 / LMU native telemetry data to our schema:

- **JSON mapping**: `map_rf2_to_frame()` — converts rF2 field names (`mUnfilteredThrottle`, `mSpeed`, etc.) and units (m/s to km/h, Kelvin to Celsius)
- **Binary parsing**: `parse_telemetry_frame()` / `parse_telemetry_batch()` — reads raw shared memory dumps
- Full format reference in [`docs/telemetry-format.md`](docs/telemetry-format.md)

---

## API Endpoints

| Status | Method | Endpoint | Description |
|--------|--------|----------|-------------|
| Done | `GET` | `/health` | Health check |
| Done | `POST` | `/telemetry` | Ingest telemetry frames (single or batch) |
| Done | `POST` | `/sessions` | Create a new session |
| Done | `GET` | `/sessions` | List sessions (paginated, filterable) |
| Done | `GET` | `/sessions/{id}` | Session detail with frame count |
| Done | `PATCH` | `/sessions/{id}` | Update / end a session |
| Planned | `GET` | `/sessions/{id}/laps` | Lap summaries for a session |
| Planned | `GET` | `/laps/compare` | Compare laps by ID |
| Planned | `POST` | `/setups` | Upload a car setup |
| Planned | `GET` | `/setups` | List setups (filterable) |
| Planned | `GET` | `/setups/correlate` | Correlate setups to performance |
| Planned | `GET` | `/alerts` | Get triggered alerts |
| Planned | `POST` | `/alerts/rules` | Create alert rules |
| Planned | `GET` | `/alerts/rules` | List active rules |
| Planned | `WS` | `/ws/alerts` | Live alert stream |
| Planned | `POST` | `/ingest` | E3N integration endpoint |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| API Framework | FastAPI |
| Language | Python 3.11+ |
| Database | SQLite (dev) / PostgreSQL (prod) |
| ORM | SQLAlchemy 2.0 (async via aiosqlite) |
| Validation | Pydantic v2 + pydantic-settings |
| Real-Time | WebSockets (planned) |
| Client | Electron + React (planned) |
| AI Integration | E3N via Anthropic API |
| Linting | ruff + black |
| Testing | pytest + pytest-asyncio (66 tests) |

---

## Project Structure

```
delta-engineer-lmu/
├── src/
│   ├── main.py                 # FastAPI app entry point (lifespan, routers)
│   ├── config.py               # pydantic-settings configuration
│   ├── api/
│   │   ├── health.py           # GET /health
│   │   ├── sessions.py         # /sessions CRUD + pagination
│   │   └── telemetry.py        # POST /telemetry ingestion
│   ├── core/
│   │   ├── parser.py           # rF2 telemetry parser (JSON + binary)
│   │   └── session_manager.py  # Session boundary auto-detection
│   ├── models/
│   │   ├── base.py             # SQLAlchemy DeclarativeBase
│   │   ├── session.py          # Session ORM model
│   │   ├── telemetry.py        # TelemetryFrame ORM model
│   │   └── schemas.py          # Pydantic request/response schemas
│   └── db/
│       ├── engine.py           # Async engine + session factory
│       └── init_db.py          # Table creation on startup
├── tests/
│   ├── conftest.py             # Shared fixtures, in-memory test DB
│   ├── unit/                   # Parser, session manager, config, model tests
│   ├── integration/            # Full HTTP endpoint tests
│   └── fixtures/               # Sample telemetry payloads
├── docs/
│   └── telemetry-format.md     # rF2/LMU shared memory format reference
├── pyproject.toml              # Dependencies, black/ruff/pytest config
├── .env.example                # Environment variable template
└── CLAUDE.md                   # Claude Code session context
```

---

## Configuration

Copy `.env.example` to `.env`. Key settings:

| Variable | Description | Default |
|----------|-------------|---------|
| `PORT` | API server port | `8000` |
| `DATABASE_URL` | DB connection string | `sqlite+aiosqlite:///telemetry.db` |
| `ENV` | Environment (`development` / `production`) | `development` |
| `LOG_LEVEL` | Logging verbosity | `info` |
| `TELEMETRY_BATCH_SIZE` | Frames per DB flush batch | `100` |
| `MAX_BATCH_SIZE` | Max frames per POST request | `1000` |
| `SESSION_GAP_THRESHOLD_SECONDS` | Time gap that triggers a new session | `300` |
| `E3N_ENABLED` | Enable E3N integration | `false` |
| `E3N_ENDPOINT` | E3N ingest URL | `http://localhost:3000/ingest` |

---

## Roadmap

- [x] **Milestone 1** — Project scaffolding, data models, config management
- [x] **Milestone 2** — Telemetry ingestion, parsing, session management
- [ ] **Milestone 3** — Lap & sector analysis, lap comparison
- [ ] **Milestone 4** — Setup data model, correlation engine
- [ ] **Milestone 5** — Alert rules engine, WebSocket streaming
- [ ] **Milestone 6** — API hardening, OpenAPI docs, E3N `/ingest` contract
- [ ] **Milestone 7** — Electron UI (telemetry dashboard, lap graphs, setup manager)
- [ ] **Milestone 8** — E3N AI integration (natural language race engineering)

---

## Related Projects

- **E3N** — Local AI race engineer (Electron app, Anthropic API)
- **Le Mans Ultimate** — Official WEC sim racing title by Studio 397

---

## Contributing

This project is in active early development. To contribute:

1. Check the [Issues](../../issues) tab for open tasks
2. Fork the repo and create a feature branch
3. Follow [conventional commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `docs:`, etc.)
4. Run `pytest -v` and ensure all tests pass before submitting a PR
5. See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines

---

## License

TBD

---

## Acknowledgments

Built for the sim racing community. Inspired by Coach Dave Delta, TrackTitan, MoTeC i2, and the broader sim racing data analysis ecosystem.
