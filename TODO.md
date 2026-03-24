# TODO — Living Task Tracker

> This file tracks what needs to be done, what's in progress, and what's complete.
> It mirrors GitHub Issues but gives Claude Code a quick local reference.
> **Update this file every session.**

---

## 🔥 Up Next (Milestone 1 — Project Scaffolding)

- [ ] **#1** Initialize project repo and tech stack (framework, linting, CI, health check)
- [ ] **#2** Define core data models for telemetry frames
- [ ] **#3** Set up configuration and environment management
- [ ] Finalize tech stack decision (FastAPI vs Express, Python vs TypeScript)

## 🔲 Milestone 2 — Telemetry Ingestion & Parsing

- [ ] **#4** Research and document LMU shared memory / UDP telemetry format
- [ ] **#5** Implement raw telemetry parser (binary → structured)
- [ ] **#6** Create `POST /telemetry` ingestion endpoint
- [ ] **#7** Implement telemetry session management

## 🔲 Milestone 3 — Lap & Sector Analysis

- [ ] **#8** Implement lap boundary detection
- [ ] **#9** Create lap summary computation
- [ ] **#10** Create `GET /sessions/{id}/laps` endpoint
- [ ] **#11** Implement lap comparison logic

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

- [ ] **#23** Design UI wireframes and component architecture
- [ ] **#24** Scaffold Electron app and connect to API
- [ ] Implement telemetry dashboard view
- [ ] Implement lap comparison graphs
- [ ] Implement setup manager view
- [ ] Implement alerts feed view
- [ ] Electron packaging (installer, Start Menu, desktop shortcut)
- [ ] System tray support (minimize to tray on close)

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
