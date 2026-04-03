# GitHub Projects — Delta Engineer (delta-engineer-lmu)

This file gives **humans and AI agents** a stable place to see how work maps to GitHub **Issues** and **Projects**, without opening the GitHub UI.

## Where to track work

- **Issues:** https://github.com/Reconnecting18/delta-engineer-lmu/issues  
- **Projects:** Use the repository **Projects** tab when a board is linked; mirror epics here or in `TODO.md`.

## Recently landed (capture)

| Item | Notes |
|------|--------|
| Live capture (manual `session_id`) | Electron spawns `scripts/lmu_capture_bridge.py` → `POST /telemetry` |
| **Automatic session capture** | Bridge `--auto`: reads `$rFactor2SMMP_Scoring$` for track / car / driver / session type; `POST /telemetry` without `session_id` → API `get_or_create_session` |

## Suggested Project columns

1. **Backlog** — Ideas not committed  
2. **Ready** — Scoped, acceptance criteria clear  
3. **In progress** — Active branch  
4. **In review** — PR open  
5. **Done** — Merged to `main`

## Next capture-adjacent ideas (candidates for Issues)

- Throttled `capture:frame` IPC for a live dashboard (20–30 Hz UI)  
- Match telemetry vehicle index to scoring player by `mID` when index 0 is not player  
- Optional: persist `mEndET` / `mMaxLaps` on `Session` model for richer post-session UX  

_Update this file when capture or milestone scope changes._
