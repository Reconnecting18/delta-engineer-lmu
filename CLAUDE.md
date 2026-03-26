# CLAUDE.md — Project Context for Claude Code

> **This file is read by Claude Code at the start of every session.**
> It provides full project context so work can resume without re-explanation.
> **Last updated:** 2026-03-26

---

## Project Identity

**Name:** Delta Engineer — LMU Telemetry Analysis API
**Repo:** delta-engineer-lmu
**Purpose:** A standalone service that processes Le Mans Ultimate sim racing telemetry data and connects to E3N (local AI race engineer) via the `/ingest` endpoint.
**Status:** Milestone 3 complete — lap & sector analysis, lap comparison operational

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

**Current:** Milestone 4 — Setup Correlation
**Last completed:** Milestone 3 — Lap & Sector Analysis (2026-03-26)

### What needs to happen next:
1. Define car setup data model (#12)
2. Create `POST /setups` and `GET /setups` endpoints (#13)
3. Implement setup-to-performance correlation (#14)

### What is NOT in scope yet:
- UI/Electron work (Milestone 7)
- E3N AI integration (Milestone 8)
- Do not jump ahead to later milestones unless explicitly asked

---

## Milestone Roadmap

| # | Milestone | Status |
|---|-----------|--------|
| 1 | Project scaffolding, data models, config | ✅ Complete |
| 2 | Telemetry ingestion, parsing, sessions | ✅ Complete |
| 3 | Lap & sector analysis, lap comparison | ✅ Complete |
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
| `POST` | `/telemetry` | 2 | ✅ |
| `POST` | `/sessions` | 2 | ✅ |
| `GET` | `/sessions` | 2 | ✅ |
| `GET` | `/sessions/{id}` | 2 | ✅ |
| `PATCH` | `/sessions/{id}` | 2 | ✅ |
| `GET` | `/sessions/{id}/laps` | 3 | ✅ |
| `POST` | `/sessions/{id}/laps/compute` | 3 | ✅ |
| `GET` | `/laps/compare` | 3 | ✅ |
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
│   │   ├── health.py       # GET /health ✅
│   │   ├── sessions.py     # /sessions CRUD ✅
│   │   ├── telemetry.py    # POST /telemetry ✅
│   │   └── laps.py         # /sessions/{id}/laps, /laps/compare ✅
│   ├── core/               # Business logic
│   │   ├── parser.py       # rF2 telemetry parser ✅
│   │   ├── session_manager.py # Session auto-detection ✅
│   │   └── lap_analyzer.py # Lap detection, summary, comparison ✅
│   ├── models/             # Data models / schemas
│   │   ├── base.py         # SQLAlchemy DeclarativeBase
│   │   ├── session.py      # Session ORM model
│   │   ├── telemetry.py    # TelemetryFrame ORM model
│   │   ├── lap.py          # LapSummary ORM model
│   │   └── schemas.py      # Pydantic v2 request/response schemas
│   └── db/                 # Database setup
│       ├── engine.py       # Async engine + session factory
│       └── init_db.py      # Table creation
├── tests/
│   ├── conftest.py         # Test fixtures, in-memory DB
│   ├── unit/
│   │   ├── test_health.py
│   │   ├── test_config.py
│   │   ├── test_models.py
│   │   ├── test_parser.py
│   │   ├── test_session_manager.py
│   │   └── test_lap_analyzer.py
│   ├── integration/
│   │   ├── test_sessions_api.py
│   │   ├── test_telemetry_api.py
│   │   └── test_laps_api.py
│   └── fixtures/           # Sample telemetry payloads
│       ├── sample_telemetry_frame.json
│       └── sample_telemetry_payload.json
├── docs/
│   └── telemetry-format.md # rF2/LMU telemetry format reference ✅
├── CLAUDE.md               # ← You are here
├── README.md
├── CONTRIBUTING.md
├── CHANGELOG.md
├── TODO.md
├── .env.example
├── .gitignore
└── pyproject.toml
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

- **LMU telemetry format** is documented in `docs/telemetry-format.md` (rF2 shared memory spec)
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

### ⚠️ MANDATORY: Commit, push, and sync GitHub at session end

After updating all files above, you **must** also:

7. **Commit all changes** using conventional commits (see below). Reference issue numbers.
8. **Push to remote** — push the branch to `origin`. If on a feature branch, create a PR if one doesn't exist.
9. **GitHub Issues** (when applicable)
   - Add a comment to each completed issue summarizing what was done
   - Close completed issues with `state_reason: completed`
   - Reference the PR/commit (e.g., "Completed in PR #27")
   - Add appropriate labels (`enhancement`, `bug`, `documentation`, etc.)
10. **GitHub Project Board** (when applicable)
    - Move completed issues to "Done" status
    - Ensure new work items are tracked on the project board
    - Keep issue labels and milestones up to date
    - When creating PRs, use `Closes #N` in the body to auto-link issues

**Do not end a session without committing, pushing, and updating GitHub.** The user expects all work to be persisted and visible on GitHub when a session ends.

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

## How to End a Session

Before finishing, complete **every** step:

1. **Update docs** — CLAUDE.md, README.md, CHANGELOG.md, TODO.md (see above)
2. **Commit** — stage and commit all changes with conventional commit messages referencing issue numbers
3. **Push** — push the branch to origin
4. **GitHub Issues** — close completed issues with summary comments, add labels
5. **GitHub Project Board** — move completed items to "Done"
6. **Create PR** — if on a feature branch and no PR exists, create one with `Closes #N` in the body
