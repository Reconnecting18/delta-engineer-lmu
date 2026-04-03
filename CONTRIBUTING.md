# Contributing

Guidelines for developing the LMU Telemetry Analysis API.

---

## Development Setup

### Prerequisites

- Python 3.11+ and Node.js 20+ (Python for the API; Node for the `client/` Electron app)
- Git
- A code editor (VS Code recommended)

### Getting Started

```bash
git clone https://github.com/YOUR_USERNAME/lmu-telemetry-api.git
cd lmu-telemetry-api
cp .env.example .env
# Then install dependencies per the chosen stack
```

---

## Branch Strategy

```
main              ← stable, deployable
  └── dev         ← integration branch
       ├── feat/telemetry-parser
       ├── feat/lap-analysis
       ├── fix/session-boundary-bug
       └── docs/update-readme
```

- **`main`** — always stable, tagged releases
- **`dev`** — integration branch where features merge first
- **Feature branches** — branch off `dev`, merge back via PR

### Branch Naming

```
feat/short-description     # New feature
fix/short-description      # Bug fix
docs/short-description     # Documentation only
refactor/short-description # Code restructuring
test/short-description     # Adding or fixing tests
chore/short-description    # Dependencies, CI, tooling
```

---

## Commit Messages

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>: <short summary> (#issue-number)

[optional body with more detail]
```

### Types

| Type | Use for |
|------|---------|
| `feat` | New feature or endpoint |
| `fix` | Bug fix |
| `docs` | Documentation changes |
| `refactor` | Code change that doesn't fix a bug or add a feature |
| `test` | Adding or updating tests |
| `chore` | Build, CI, dependency updates |
| `style` | Formatting, whitespace (no logic change) |

### Examples

```
feat: add POST /telemetry endpoint (#6)
fix: correct sector split detection for pit laps (#8)
docs: update API endpoints table in README
test: add unit tests for lap boundary detection (#8)
chore: add pytest to dev dependencies
```

---

## Code Style

### General

- Write clear, self-documenting code — favor readability over cleverness
- Add docstrings/comments for non-obvious logic, especially in the parser and analysis modules
- Keep functions focused — one function, one job
- Use type hints (Python) or TypeScript types

### Python Specific

- Follow PEP 8
- Use `black` for formatting, `ruff` for linting
- Use `pydantic` for data validation (if using FastAPI)
- Use `pytest` for testing

### TypeScript/Node Specific

- Use `prettier` for formatting, `eslint` for linting
- Use strict TypeScript (`strict: true` in tsconfig)
- Use `vitest` or `jest` for testing

---

## Testing

### Running Tests

```bash
# Python
pytest

# With coverage
pytest --cov=src --cov-report=term-missing

# Node
npm test
```

### Test Structure

```
tests/
├── unit/              # Isolated function/module tests
│   ├── test_parser.py
│   ├── test_lap_detection.py
│   └── test_alert_engine.py
├── integration/       # API endpoint tests (spin up server)
│   ├── test_telemetry_api.py
│   └── test_sessions_api.py
└── fixtures/          # Sample data
    ├── raw_telemetry_frame.bin
    ├── parsed_telemetry.json
    └── sample_session.json
```

### What to Test

- **Parser:** Feed it known binary payloads, assert structured output
- **Lap detection:** Feed it a session's worth of frames, assert correct lap boundaries
- **Analysis:** Feed it known laps, assert correct computed metrics
- **Endpoints:** HTTP tests against each route with valid and invalid payloads
- **Alerts:** Feed telemetry that should/shouldn't trigger rules, assert correct alerts

---

## Pull Request Process

1. Branch from `dev`
2. Make changes, write tests
3. Update documentation (README, CLAUDE.md, CHANGELOG, TODO)
4. Self-review your diff
5. Open PR against `dev` with a clear description
6. Reference the GitHub issue number in the PR title

### PR Title Format

```
feat: Add telemetry ingestion endpoint (#6)
```

---

## Documentation Updates

When you make changes, always update:

| File | What to update |
|------|---------------|
| `CLAUDE.md` | Milestone status, endpoint status, structure, decisions |
| `README.md` | Roadmap, tech stack, structure, endpoints |
| `CHANGELOG.md` | What changed, in Keep a Changelog format |
| `TODO.md` | Check off completed items, add new tasks |

This is critical for maintaining project continuity across development sessions.

---

## Project Conventions

### API Design

- RESTful endpoints with consistent naming
- All responses return JSON
- Standardized error format:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Human-readable description",
    "details": {}
  }
}
```

- Use appropriate HTTP status codes (200, 201, 400, 404, 422, 500)
- Pagination for list endpoints (`?page=1&limit=20`)
- Filtering via query parameters

### Data Models

- All timestamps in ISO 8601 / UTC
- All telemetry values in SI units where possible (meters, seconds, Celsius, kPa)
- IDs are strings (UUIDs) not integers
