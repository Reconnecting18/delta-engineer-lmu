# TODO — Living Task Tracker

> This file tracks what needs to be done, what's in progress, and what's complete.
> It mirrors GitHub Issues but gives Claude Code a quick local reference.
> **Update this file every session.**

---

## ✅ Milestone 1 — Project Scaffolding (Complete)

- [x] **#1** Initialize project repo and tech stack (FastAPI, black, ruff, pytest, health check)
- [x] **#2** Define core data models for telemetry frames (Session, TelemetryFrame, Pydantic schemas)
- [x] **#3** Set up configuration and environment management (pydantic-settings)
- [x] Finalize tech stack decision → **Python + FastAPI**

## ✅ Milestone 2 — Telemetry Ingestion & Parsing (Complete)

- [x] **#4** Research and document LMU shared memory / UDP telemetry format
- [x] **#5** Implement raw telemetry parser (binary → structured)
- [x] **#6** Create `POST /telemetry` ingestion endpoint
- [x] **#7** Implement telemetry session management

## ✅ Milestone 3 — Lap & Sector Analysis (Complete)

- [x] **#8** Implement lap boundary detection
- [x] **#9** Create lap summary computation
- [x] **#10** Create `GET /sessions/{id}/laps` endpoint
- [x] **#11** Implement lap comparison logic

## 🔲 Milestone 4 — Setup Correlation

- [ ] **#12** Define car setup data model
- [ ] **#13** Create `POST /setups` and `GET /setups` endpoints
- [ ] **#14** Implement setup-to-performance correlation

## 🔲 Milestone 5 — Real-Time Alerts

- [ ] **#15** Define alert rules engine schema
- [ ] **#16** Implement alert evaluation pipeline
- [ ] **#17** Create `GET /alerts` and alert configuration endpoints
- [ ] **#18** Add WebSocket support for live alerts

## 🔲 Milestone 6 — API Hardening & Docs

- [ ] **#19** Add request validation and standardized error responses
- [ ] **#20** Generate OpenAPI / Swagger documentation
- [ ] **#21** Add integration test suite
- [ ] **#22** Implement `/ingest` endpoint stub for E3N

## 🔲 Milestone 7 — Electron UI

- [x] **#23** Design UI wireframes and component architecture
- [x] **#24** Scaffold Electron app and connect to API
- [x] **LMU live capture** — `scripts/lmu_capture_bridge.py` + Electron **Live capture** page (`window.delta` IPC)
- [ ] Implement telemetry dashboard view
- [ ] Implement lap comparison graphs
- [ ] Implement setup manager view
- [ ] Implement alerts feed view
- [ ] Electron packaging (installer, Start Menu, desktop shortcut)
- [x] System tray support (minimize to tray on close) — implemented in `client/src/main/index.ts`

## 🔲 Milestone 8 — E3N AI Integration

- [ ] Connect live telemetry stream to E3N via `/ingest`
- [ ] Implement natural language race engineering queries
- [ ] Add AI-generated strategy recommendations
- [ ] End-to-end testing (LMU → API → E3N → response)

---

## ✅ Completed

- [x] Project planning and architecture design
- [x] Created 22 GitHub issues across 6 API milestones
- [x] Comprehensive README.md
- [x] CLAUDE.md (Claude Code context file)
- [x] CHANGELOG.md, TODO.md, CONTRIBUTING.md
- [x] .env.example and .gitignore
- [x] Researched Coach Dave Delta and TrackTitan for reference
- [x] Fixed dotfile naming (gitignore → .gitignore, env.example → .env.example)
- [x] Milestone 1: Full project scaffold with FastAPI, SQLAlchemy, models, config, health endpoint, tests
- [x] Milestone 2: Telemetry format docs, parser, session management, POST /telemetry endpoint (66 tests)
- [x] Milestone 3: Lap boundary detection, summary computation, lap comparison, laps API (103 tests)
- [x] Decided on Electron + React for client UI
- [x] Decided on electron-builder + NSIS for packaging
- [x] Decided on system tray behavior
- [x] GitHub issue for Electron packaging & system tray

---

## 💡 Ideas & Future Considerations

- Voice-based race engineer commands through E3N
- Multi-driver session support (team endurance races)
- Historical performance trends across sessions
- Weather condition impact analysis
- Tire degradation prediction models
- Integration with SimHub for hardware displays
- Export to MoTeC i2 format for compatibility
