# AGENTS.md — Onboarding for AI / automation

> **Purpose:** Give coding agents enough context to work in this repo without re-deriving architecture. Pair with [`README.md`](README.md) and [`CLAUDE.md`](CLAUDE.md).

**Last updated:** 2026-04-03

---

## What this project is

**Delta Engineer (delta-engineer-lmu)** — FastAPI service + Electron desktop client for **Le Mans Ultimate** telemetry: ingest, sessions, lap analysis, future E3N handoff via `/ingest`.

---

## GitHub tracking

- **Issues:** [Reconnecting18/delta-engineer-lmu/issues](https://github.com/Reconnecting18/delta-engineer-lmu/issues)
- **Projects:** Use the org/repo **Projects** tab when the board is linked to this repository for milestone / kanban work.

---

## Data flow (live capture)

```
LMU (rF2 Shared Memory Map plugin)
    → Windows named mapping "$rFactor2SMMP_Telemetry$"
    → scripts/lmu_capture_bridge.py (spawned by Electron main)
    → POST /telemetry { session_id, frames: [...] }
    → FastAPI + SQLite (TelemetryFrame rows)
```

The **API never opens shared memory**; only the bridge (or other clients) do. Spec: [`docs/telemetry-format.md`](docs/telemetry-format.md).

---

## Key paths

| Area | Path |
|------|------|
| API entry | `src/main.py` |
| Telemetry ingest | `src/api/telemetry.py` |
| rF2 binary → schema | `src/core/parser.py` |
| Shared memory read (Windows) | `src/capture/lmu_shared_memory.py` |
| Live bridge CLI | `scripts/lmu_capture_bridge.py` |
| Electron main + capture spawn | `client/src/main/index.ts`, `client/src/main/capture.ts` |
| Preload bridge | `client/src/preload/index.ts` |
| Live UI | `client/src/renderer/src/pages/LiveCapturePage.tsx` |
| Shared TS types (settings, capture) | `client/src/shared/` |
| UI architecture spec | `docs/ui-architecture.md` |

---

## Environment overrides (capture)

| Variable | Role |
|----------|------|
| `DELTA_PYTHON` | Full path to Python executable for the bridge |
| `DELTA_CAPTURE_SCRIPT` | Full path to `lmu_capture_bridge.py` (packaged or custom layouts) |

---

## Commands (repo root)

```bash
pip install -e ".[dev]"
python -m uvicorn src.main:app --reload
pytest -v
```

```bash
cd client && npm install && npm run dev
```

---

## Conventions

- Python 3.11+, Pydantic v2, SQLAlchemy 2 async.
- Electron: `contextIsolation`, no `nodeIntegration` in renderer; IPC via `window.delta`.
- Prefer **focused diffs**; update **`CHANGELOG.md`** for user-visible changes.
