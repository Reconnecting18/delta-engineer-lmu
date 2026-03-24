# CLAUDE.md — Project Context for Claude Code

> **This file is read by Claude Code at the start of every session.**
> It provides full project context so work can resume without re-explanation.
> **Last updated:** 2026-03-24

---

## Project Identity

**Name:** LMU Telemetry Analysis API
**Repo:** lmu-telemetry-api
**Purpose:** A standalone service that processes Le Mans Ultimate sim racing telemetry data and connects to E3N (local AI race engineer) via the `/ingest` endpoint.
**Status:** Milestone 1 complete — scaffolding done, ready for Milestone 2

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

## Tech Stack

| Layer | Choice | Status |
|-------|--------|--------|
| API Framework | FastAPI | Decided |
| Language | Python 3.11+ | Decided |
| Database | SQLite (dev) / PostgreSQL (prod) | Decided |
| ORM | SQLAlchemy 2.0 (async) | Decided |
| Validation | Pydantic v2 + pydantic-settings | Decided |
| Real-Time | WebSockets | Decided |
| Client UI | Electron + React | Decided |
| AI Integration | E3N → Anthropic API | Decided |
| Packaging | electron-builder (NSIS) | Decided |
| Linting | ruff + black | Decided |
| Testing | pytest + pytest-asyncio | Decided |

> **Update this table** as decisions are made.

---

## Current Milestone & Focus

**Current:** Milestone 2 — Telemetry Ingestion & Parsing
**Last completed:** Milestone 1 — Project Scaffolding (2026-03-24)

### What needs to happen next:
1. Research LMU shared memory / UDP telemetry format (#4)
2. Implement raw telemetry parser (#5)
3. Create `POST /telemetry` ingestion endpoint (#6)
4. Implement telemetry session management (#7)

### What is NOT in scope yet:
- UI/Electron work (Milestone 7)
- E3N AI integration (Milestone 8)
- Do not jump ahead to later milestones unless explicitly asked

---

## Milestone Roadmap

| # | Milestone | Status |
|---|-----------|--------|
| 1 | Project scaffolding, data models, config | ✅ Complete |
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
| `GET` | `/health` | 1 | ✅ |
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

## Project Structure

```
delta-engineer-lmu/
├── src/
│   ├── main.py             # FastAPI app entry point
│   ├── config.py           # pydantic-settings config
│   ├── api/                # Route handlers / endpoints
│   │   └── health.py       # GET /health ✅
│   ├── core/               # Business logic (future)
│   ├── models/             # Data models / schemas
│   │   ├── base.py         # SQLAlchemy DeclarativeBase
│   │   ├── session.py      # Session ORM model
│   │   ├── telemetry.py    # TelemetryFrame ORM model
│   │   └── schemas.py      # Pydantic v2 request/response schemas
│   └── db/                 # Database setup
│       ├── engine.py       # Async engine + session factory
│       └── init_db.py      # Table creation
├── tests/
│   ├── unit/
│   │   ├── test_health.py
│   │   ├── test_config.py
│   │   └── test_models.py
│   ├── integration/
│   └── fixtures/           # Sample telemetry payloads
├── docs/
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
| API framework | Python + FastAPI | Async-native, auto OpenAPI docs, great WebSocket support | 2026-03-24 |
| ORM | SQLAlchemy 2.0 async | Modern mapped_column syntax, async support via aiosqlite | 2026-03-24 |
| Tire data storage | JSON columns | Cleaner than 8 separate float columns for [FL,FR,RL,RR] | 2026-03-24 |
| AI scope | E3N handles all AI | This API is data processing only; AI lives in E3N | 2026-03-24 |

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
   - Add a comment to each completed issue summarizing what was done
   - Close completed issues with `state_reason: completed`
   - Reference the PR number in the issue comment (e.g., "Completed in PR #26")

6. **GitHub Project Board** (when applicable)
   - Move completed issues/PRs to the appropriate column (e.g., "Done")
   - Ensure new work items are tracked on the project board
   - Keep issue labels and milestones up to date
   - When creating PRs, use `Closes #N` in the body to auto-link issues

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
