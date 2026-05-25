# AGENTS.md

## Project identity

This repository is TRACE: Troubleshooting Reports Across Cloud & Endpoints.

TRACE is a local-first IT Operations diagnostic toolkit. It helps support engineers correlate evidence from Microsoft 365, Entra ID, endpoints, DNS, mail flow, and infrastructure systems into clear troubleshooting reports.

The first module is M365 Access Path Analyzer. It diagnoses Microsoft 365 access failures by correlating identity status, licensing, MFA/authentication signals, sign-in logs, Conditional Access results, and device compliance evidence.

## Product principles

- Local-first: no tenant data leaves the user's machine.
- Read-only by default.
- No automatic remediation in v1.
- Evidence over assumptions.
- Every finding must include confidence and limitations.
- Use operational troubleshooting language, not offensive security language.
- The product is a toolkit with modules. Do not hard-code the entire product as only an M365 tool.

## Technology stack

- Collector: PowerShell 7 using Microsoft Graph PowerShell SDK for Microsoft 365 / Entra ID modules.
- Backend: Python FastAPI.
- Frontend: React + TypeScript + Vite.
- Local storage: SQLite.
- Reporting: HTML and JSON in v1.
- Tests: Pester for PowerShell, Pytest for Python, Vitest for frontend.

## Coding rules

- Keep collector scripts read-only unless a future spec explicitly says otherwise.
- All collector scripts must output structured JSON.
- Backend must validate collector output before analysis.
- Frontend must present a clear user experience, not raw JSON as the main interface.
- Use synthetic sample data for development and tests before real tenant integration.
- Do not add extra frameworks or services unless specs are updated first.

## Finding schema

All findings must include:

- rule_id
- title
- severity
- confidence
- likely_cause
- evidence
- next_steps
- what_not_to_change_yet
- limitations

## Security rules

- Never store access tokens.
- Never log secrets.
- Never request broader Microsoft Graph permissions than required.
- Prefer least-privilege permissions.
- Document permissions and role requirements.
- Any sample data must be synthetic.
- Do not build malware, phishing, password spraying, exploit simulation, credential collection, or token theft functionality.

## Done definition

A task is done only when:

- Code is implemented.
- Tests are added or updated where relevant.
- Documentation is updated if behavior changed.
- Sample JSON exists if the feature depends on external data.
- The implementation respects read-only/local-first constraints.
