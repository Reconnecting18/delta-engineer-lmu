# CLAUDE.md — Project Context for Claude Code

> **This file is read by Claude Code at the start of every session.**
> It provides full project context so work can resume without re-explanation.
> **Last updated:** (update this date every time you modify this file)

---

## Project Identity

**Name:** LMU Telemetry Analysis API
**Repo:** lmu-telemetry-api
**Purpose:** A standalone service that processes Le Mans Ultimate sim racing telemetry data and connects to E3N (local AI race engineer) via the `/ingest` endpoint.
**Status:** Pre-development — project scaffolding phase

---

## Architecture Overview

```
Le Mans Ultimate (sim)
    │
    ▼
┌─────────────────────┐
│   Electron Client   │  ← Reads shared memory / UDP from LMU
│   (Capture + UI)    │  ← Displays dashboards, graphs, alerts
└────────┬────────────┘
         │ POST /telemetry
         ▼
┌─────────────────────┐
│   LMU Telemetry API │  ← THIS PROJECT
│                     │  ← Parses, stores, analyzes telemetry
└────────┬────────────┘
         │ POST /ingest
         ▼
┌─────────────────────┐
│       E3N           │  ← Separate Electron app (already exists)
│  (Anthropic API)    │  ← AI-powered race engineering insights
└─────────────────────┘
```

**Key relationships:**
- This API is the **data processing layer** between the sim and the AI
- The Electron client is both the telemetry **capture** tool and the **UI dashboard**
- E3N is a separate project — this API feeds it via `/ingest`
- E3N connects to Anthropic's API for AI capabilities

---

## Tech Stack (Decided / TBD)

| Layer | Choice | Status |
|-------|--------|--------|
| API Framework | TBD (FastAPI preferred) | Deciding |
| Language | TBD (Python preferred) | Deciding |
| Database | TBD (SQLite for dev, Postgres for prod) | Deciding |
| Real-Time | WebSockets | Decided |
| Client UI | Electron + React | Decided |
| AI Integration | E3N → Anthropic API | Decided |
| Packaging | electron-builder (NSIS) | Decided |

> **Update this table** as decisions are made.

---

## Current Milestone & Focus

**Current:** Milestone 1 — Project Scaffolding
**Next up:** Milestone 2 — Telemetry Ingestion & Parsing

### What needs to happen right now:
1. Initialize the project structure (framework, linting, CI)
2. Define core telemetry data models
3. Set up config/environment management
4. Get a basic `GET /health` endpoint running

### What is NOT in scope yet:
- UI/Electron work (Milestone 7)
- E3N AI integration (Milestone 8)
- Do not jump ahead to later milestones unless explicitly asked

---

## Milestone Roadmap

| # | Milestone | Status |
|---|-----------|--------|
| 1 | Project scaffolding, data models, config | 🔲 Not started |
| 2 | Telemetry ingestion, parsing, sessions | 🔲 Not started |
| 3 | Lap & sector analysis, lap comparison | 🔲 Not started |
| 4 | Setup data model, correlation engine | 🔲 Not started |
| 5 | Alert rules engine, WebSocket streaming | 🔲 Not started |
| 6 | API hardening, OpenAPI docs, tests, `/ingest` stub | 🔲 Not started |
| 7 | Electron UI (dashboards, graphs, alerts) | 🔲 Not started |
| 8 | E3N AI integration | 🔲 Not started |

> **Update statuses** as milestones progress: 🔲 Not started → 🔨 In progress → ✅ Complete

---

## API Endpoints (Planned)

| Method | Endpoint | Milestone | Status |
|--------|----------|-----------|--------|
| `GET` | `/health` | 1 | 🔲 |
| `POST` | `/telemetry` | 2 | 🔲 |
| `POST` | `/sessions` | 2 | 🔲 |
| `GET` | `/sessions` | 2 | 🔲 |
| `GET` | `/sessions/{id}` | 2 | 🔲 |
| `GET` | `/sessions/{id}/laps` | 3 | 🔲 |
| `GET` | `/laps/compare` | 3 | 🔲 |
| `POST` | `/setups` | 4 | 🔲 |
| `GET` | `/setups` | 4 | 🔲 |
| `GET` | `/setups/correlate` | 4 | 🔲 |
| `GET` | `/alerts` | 5 | 🔲 |
| `POST` | `/alerts/rules` | 5 | 🔲 |
| `GET` | `/alerts/rules` | 5 | 🔲 |
| `WS` | `/ws/alerts` | 5 | 🔲 |
| `POST` | `/ingest` | 6 | 🔲 |

> **Update statuses** as endpoints are implemented: 🔲 → 🔨 → ✅

---

## Project Structure (Target)

```
lmu-telemetry-api/
├── src/
│   ├── api/                # Route handlers / endpoints
│   │   ├── telemetry.py
│   │   ├── sessions.py
│   │   ├── laps.py
│   │   ├── setups.py
│   │   ├── alerts.py
│   │   └── ingest.py
│   ├── core/               # Business logic
│   │   ├── parser.py       # Raw telemetry parser
│   │   ├── lap_detection.py
│   │   ├── lap_analysis.py
│   │   ├── setup_correlation.py
│   │   └── alert_engine.py
│   ├── models/             # Data models / schemas
│   ├── db/                 # Database setup and migrations
│   └── config.py           # Environment and app config
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/           # Sample telemetry payloads
├── docs/
│   └── telemetry-format.md # LMU telemetry format reference
├── assets/                 # App icons, tray icons
├── CLAUDE.md               # ← You are here
├── README.md
├── CONTRIBUTING.md
├── CHANGELOG.md
├── TODO.md
├── .env.example
├── .gitignore
└── package.json / pyproject.toml
```

> **Update this** if the structure changes during development.

---

## Key Design Decisions

Document important decisions here so they don't get re-debated each session.

| Decision | Choice | Rationale | Date |
|----------|--------|-----------|------|
| Client framework | Electron + React | Matches E3N stack, needs local system access for shared memory | — |
| Installer | electron-builder + NSIS | Produces proper Windows installer with Start Menu shortcuts | — |
| System tray | Minimize to tray on close (default on) | App must stay running during sim sessions to capture telemetry | — |
| API ↔ UI separation | Separate processes | API runs as standalone service, Electron is just a client | — |

> **Add rows** when new architectural decisions are made.

---

## Known Constraints & Context

- **LMU telemetry format** has not been fully documented yet — Issue #4 covers research
- **E3N already exists** as a separate Electron app — do not duplicate its functionality
- The **primary user** is a sim racer running LMU on Windows — the API and Electron client run on the same PC as the sim
- The Electron app plays **double duty**: captures telemetry from LMU AND displays the UI dashboard
- This project is being developed by a student, so keep solutions practical and well-documented

---

## Files You Must Keep Updated

### ⚠️ MANDATORY: Update these files when making changes

Every time you complete work in a session, **before finishing**, update the following:

1. **`CLAUDE.md`** (this file)
   - Update "Current Milestone & Focus" if progress was made
   - Update milestone/endpoint status tables
   - Update "Project Structure" if new files/folders were added
   - Add any new design decisions to the decisions table
   - Update the "Last updated" date at the top

2. **`README.md`**
   - Update the roadmap checkboxes if milestones were completed
   - Update the tech stack table if decisions were finalized
   - Update the project structure if it changed
   - Update API endpoints table if new endpoints were implemented

3. **`CHANGELOG.md`**
   - Add an entry for what was done in this session
   - Follow the Keep a Changelog format

4. **`TODO.md`**
   - Check off completed items
   - Add any new tasks that were discovered during development

5. **GitHub Issues** (when applicable)
   - Note which issue(s) the work relates to in commit messages
   - If a task is complete, mention it so the user can close the issue

> **This is not optional.** Keeping these files in sync is how project continuity works across sessions. If you skip this, the next session starts blind.

---

## Commit Message Convention

Use conventional commits:

```
feat: add telemetry ingestion endpoint
fix: correct lap boundary detection at pit entry
docs: update API endpoints table in README
refactor: extract parser into separate module
test: add unit tests for lap analysis
chore: update dependencies
```

Always reference the related issue number:

```
feat: add telemetry ingestion endpoint (#6)
```

---

## How to Start a Session

If you're Claude Code starting a new session, here's your checklist:

1. **Read this file first** — it's your full context
2. **Check `TODO.md`** — see what's next and what's in progress
3. **Check `CHANGELOG.md`** — see what was done last
4. **Ask the user** what they want to focus on if it's not clear
5. **Work within the current milestone** unless told otherwise
6. **Update all docs before ending** — see "Files You Must Keep Updated" above
