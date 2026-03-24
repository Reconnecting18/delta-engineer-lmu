# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [Unreleased]

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
