# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [Unreleased]

#### Added
- `client/` — Electron + Vite + React + TypeScript app: app shell, `window.delta` settings IPC, React Query, read-only Sessions + Lap summaries views, placeholders for Live/Setups/Alerts (GitHub #24)
- FastAPI `CORSMiddleware` (`allow_origins=["*"]`) so the Electron renderer can call the local API from dev and packaged builds (no API auth; local use only)
- `docs/ui-architecture.md` — Electron UI information architecture, per-view wireframes, IPC channel map, React component map, and view→API matrix (GitHub #23)

### Milestone 3 — Lap & Sector Analysis (2026-03-26)

#### Added
- `src/models/lap.py` — `LapSummary` ORM model (timing, speed, tires, fuel, validity)
- `src/core/lap_analyzer.py` — Lap boundary detection, summary computation, and comparison logic
- `src/api/laps.py` — Lap analysis endpoints:
  - `GET /sessions/{id}/laps` — List lap summaries (paginated, filterable, sortable)
  - `POST /sessions/{id}/laps/compute` — Trigger lap computation from telemetry frames
  - `GET /laps/compare?ids=A,B` — Full delta analysis between two laps
- New schemas: `LapSummaryResponse`, `LapComparisonResult`, `SectorDelta`, `SpeedTracePoint`, `InputTracePoint`
- Lap validity detection (pit laps, unrealistically short laps)
- Sector time computation from sector boundary detection
- Speed trace and input (throttle/brake) trace comparison with configurable sample points
- 36 new tests (20 lap analyzer unit, 17 laps API integration) — **102 total**
- `best_lap_time` now computed from valid lap summaries when session ends

#### Changed
- `session_manager._compute_session_stats()` now queries `LapSummary` for `best_lap_time`
- Session model gains `laps` relationship to `LapSummary`

### Milestone 2 — Telemetry Ingestion & Parsing (2026-03-24)

#### Added
- `docs/telemetry-format.md` — rF2/LMU shared memory telemetry format reference
- `src/core/parser.py` — Raw telemetry parser with rF2 field mapping and unit conversions
- `src/core/session_manager.py` — Session boundary detection and auto-creation logic
- `src/api/sessions.py` — Session CRUD endpoints (POST/GET/PATCH /sessions)
- `src/api/telemetry.py` — `POST /telemetry` ingestion endpoint with batch support
- `src/models/schemas.py` — New schemas: `SessionUpdate`, `SessionDetailResponse`, `PaginatedResponse`, `TelemetryIngestRequest`, `TelemetryIngestResponse`, `FrameError`
- Pagination support with generic `PaginatedResponse[T]` wrapper
- Session auto-detection from track/car/driver context with configurable gap threshold
- 40 new tests (26 parser unit, 8 session manager unit, 10 session API integration, 10 telemetry API integration)
- `tests/fixtures/` — Sample telemetry frame and payload fixtures
- Config: `session_gap_threshold_seconds`, `max_batch_size` settings

#### Changed
- `TelemetryFrameCreate.session_id` is now optional (set at endpoint level, not per-frame)
- `tests/conftest.py` — Added in-memory SQLite test database with per-test isolation

### Milestone 1 — Project Scaffolding (2026-03-24)

#### Added
- FastAPI application with async SQLAlchemy 2.0 and SQLite (via aiosqlite)
- `pyproject.toml` with all dependencies, black/ruff/pytest config
- `src/config.py` — pydantic-settings based configuration loading from `.env`
- `src/models/session.py` — Session ORM model (track, car, driver, session type)
- `src/models/telemetry.py` — TelemetryFrame ORM model (inputs, vehicle state, tires, fuel, weather)
- `src/models/schemas.py` — Pydantic v2 schemas for API request/response validation
- `src/db/engine.py` — Async SQLAlchemy engine and session factory
- `src/db/init_db.py` — Database table creation on startup
- `src/api/health.py` — `GET /health` endpoint
- `src/main.py` — FastAPI app entry point with lifespan events
- Unit tests for health endpoint, config, and model schemas (7 tests)

#### Fixed
- Renamed `gitignore` → `.gitignore` and `env.example` → `.env.example`

### Planning Phase
- Defined project architecture (API ↔ Electron client ↔ E3N pipeline)
- Created 22 GitHub issues across 6 milestones covering the full API build-out
- Planned additional milestones for Electron UI (Milestone 7) and E3N AI integration (Milestone 8)
- Researched comparable tools (Coach Dave Delta, TrackTitan) for UI/UX reference
- Decided on Electron + React for client (matches E3N stack)
- Decided on electron-builder with NSIS for Windows packaging
- Decided on system tray behavior (minimize to tray on close, default on)

### Added
- `README.md` — comprehensive project documentation
- `CLAUDE.md` — Claude Code session context file
- `CHANGELOG.md` — this file
- `TODO.md` — living task tracker
- `CONTRIBUTING.md` — development guidelines and conventions
- `.env.example` — environment configuration template
- `.gitignore` — standard ignores for the project
- GitHub issue: Electron app packaging & system tray support
