# Security Policy

## About This Project

LMU Telemetry API is a **local-only development tool** for processing Le Mans Ultimate sim racing telemetry. It runs on the same machine as the sim and is not designed to be exposed to the public internet.

## Supported Versions

| Version | Supported |
|---------|-----------|
| Latest `main` | Yes |
| Feature branches | No |

Only the latest code on the `main` branch is actively maintained.

## Reporting a Vulnerability

If you discover a security issue in this project:

1. **Open a GitHub Issue** describing the vulnerability (for non-sensitive issues)
2. **For sensitive issues** (e.g., credential exposure, injection vulnerabilities), please reach out via the repository owner's GitHub profile rather than opening a public issue

### What to include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if you have one)

### Response timeline:
- **Acknowledgment:** Within 7 days
- **Assessment:** Within 14 days
- **Fix (if applicable):** Best effort, depending on severity

## Security Considerations

Since this API is designed to run locally:

- **Do not expose** the API to the public internet without additional authentication and TLS
- **Do not commit** `.env` files, API keys, or credentials to the repository
- The `.gitignore` is configured to exclude sensitive files (`.env`, `*.db`, etc.)
- Database files (`telemetry.db`) contain session data and should be treated as private

## Branch Protection

This repository uses branch rulesets to protect the `main` branch:

- Direct pushes to `main` are blocked
- All changes must go through pull requests
- Force pushes are not allowed
- Branch deletion is restricted
