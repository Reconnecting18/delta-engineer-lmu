# Delta Engineer — Electron client

Desktop UI for the LMU telemetry API. Stack: **Electron** + **electron-vite** + **React** + **TypeScript**.

## Scripts

| Command | Description |
|--------|---------------|
| `npm install` | Install dependencies |
| `npm run dev` | Dev mode (Vite + Electron) |
| `npm run build` | Production build → `out/` |

Run the FastAPI server first (`python -m uvicorn src.main:app --reload` from repo root). Default API URL is `http://127.0.0.1:8000` (change via the API pill in the top bar).

## Layout

- `src/main` — Browser window, tray, settings persistence, IPC handlers, **spawns** `scripts/lmu_capture_bridge.py` for LMU capture
- `src/preload` — `contextBridge` → `window.delta` (settings + capture API)
- `src/renderer` — React app (HashRouter, TanStack Query)
- `src/shared` — Shared TypeScript types (`app-settings`, `capture-types`)

**Live capture:** Sidebar → **Live capture**. Default **automatic session** uses scoring memory for track/car/session type; uncheck for a fixed session id. Requires Windows, LMU + rF2 plugin (telemetry + scoring), Python on `PATH`, and the API. See [README.md](../README.md) § Live LMU capture and [`.github/PROJECTS.md`](../.github/PROJECTS.md).

See [docs/ui-architecture.md](../docs/ui-architecture.md) for the full design.
