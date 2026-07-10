# TRACE

> Troubleshooting Reports Across Cloud & Endpoints

TRACE is a **local-first IAM / access evidence workbench** for turning redacted access-ticket evidence into structured findings, missing evidence, safe next checks, explicit non-actions, and support-ready reports.

It is my flagship project for the **IAM Engineer / Identity Support / Access Operations** path.

## Why This Exists

IAM support tickets often arrive as incomplete fragments: a user message, a sign-in result, a policy note, a license clue, or an access-denied screenshot. TRACE turns that messy evidence into a structured operator workflow.

```text
redacted evidence
  -> guided intake or parser
  -> normalized access evidence
  -> deterministic finding
  -> evidence used + evidence missing
  -> safe next checks + non-actions
  -> Markdown / JSON support report
```

TRACE does not claim root cause when the evidence is incomplete. It shows what is known, what is missing, and what should be checked next.

## Screenshots

The screenshots below come from the final local visual-audit proof package for `trace-v0.3.0-guided-iam-evidence`.

![TRACE UI screenshot gallery](docs/screenshots/readme/trace-ui-gallery.svg)

The gallery shows the operator dashboard, the Access Evidence intake workflow, and a Guest / B2B analysis result.

## Current Workflows

| Workflow | Purpose |
|---|---|
| Generic access log text | Paste redacted access-ticket or log evidence |
| Entra sign-in CSV | Analyze exported sign-in evidence |
| Conditional Access / MFA guided form | Structure policy, MFA, client app, and device evidence |
| License / Service Plan guided form | Separate license/service-plan symptoms from general access problems |
| Guest / B2B guided form | Structure external-user, invitation, tenant-policy, and assignment evidence |
| Resource Assignment guided form | Separate successful authentication from resource authorization failure |

## Main Analyzer Outcomes

TRACE can classify evidence for:

- `LOG_PATTERN_CONDITIONAL_ACCESS_BLOCK`
- `LOG_PATTERN_MFA_CHALLENGE_OR_FAILURE`
- `LOG_PATTERN_LICENSE_OR_SERVICE_PLAN_MISSING`
- `LOG_PATTERN_GUEST_B2B_ACCESS_BLOCKED`
- `LOG_PATTERN_DISABLED_ACCOUNT_ATTEMPT`
- `LOG_PATTERN_AUTH_SUCCESS_ACCESS_DENIED`
- resource assignment or group membership missing/unconfirmed evidence
- no usable evidence / unsupported source type

Each run returns a finding, confidence level, evidence used, evidence missing, safe next steps, non-actions, limitations, local history entry, and Markdown report.

## What TRACE Is Not

TRACE is not a SIEM, live tenant monitor, production automation platform, governance product, or remediation tool.

It is a local read-only evidence structuring tool for support practice, portfolio proof, and controlled demos using redacted or sample data.

For full boundaries, see [`docs/safety-boundaries.md`](docs/safety-boundaries.md).

## Architecture

```text
trace-ops/
|-- backend/     FastAPI API, analyzers, parsers, local run store, reports
|-- collector/   PowerShell read-only collector samples and contract tests
|-- frontend/    React, TypeScript, Vite, TRACE operator shell
|-- samples/     Public-safe sample evidence
|-- scripts/     local audit and visual UI audit automation
`-- docs/        architecture, safety boundaries, scenarios, roadmap, release notes
```

Key backend files:

```text
backend/app/logs.py
backend/app/log_models.py
backend/app/log_parser.py
backend/app/log_analyzer.py
backend/app/entra_signin_analyzer.py
backend/app/resource_assignment_analyzer.py
backend/app/access_run_store.py
```

Key frontend files:

```text
frontend/src/App.tsx
frontend/src/api/traceApi.ts
frontend/src/modules/accessEvidence/AccessEvidencePage.tsx
frontend/src/ui/ResultPanel.tsx
frontend/src/styles/trace-shell.css
```

## API Endpoints

Primary access-evidence endpoints:

```text
GET  /api/health
GET  /api/modules
POST /api/logs/analyze
GET  /api/logs/history
GET  /api/logs/history/{run_id}
GET  /api/logs/reports/{run_id}.md
```

Legacy/sample diagnostic endpoints are still present for earlier TRACE modules.

## Run Locally

Backend:

```powershell
Set-Location -LiteralPath "C:\Users\ralba\trace-ops\backend"
..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Frontend:

```powershell
Set-Location -LiteralPath "C:\Users\ralba\trace-ops\frontend"
npm install
npm run dev
```

Typical local URLs:

```text
Backend:  http://127.0.0.1:8000
Frontend: http://127.0.0.1:5173
```

## Validate Locally

Backend:

```powershell
Set-Location -LiteralPath "C:\Users\ralba\trace-ops\backend"
python -m pytest
```

Frontend:

```powershell
Set-Location -LiteralPath "C:\Users\ralba\trace-ops\frontend"
npm test
npm run build
```

Full local visual proof:

```powershell
$repo = Join-Path $HOME "trace-ops"
& (Join-Path $repo "VISUAL_AUDIT_TRACE_LOCAL.bat")
```

## Documentation

- [`docs/architecture.md`](docs/architecture.md)
- [`docs/demo-scenarios.md`](docs/demo-scenarios.md)
- [`docs/safety-boundaries.md`](docs/safety-boundaries.md)
- [`docs/log-analysis-roadmap.md`](docs/log-analysis-roadmap.md)
- [`docs/finished-roadmap.md`](docs/finished-roadmap.md)
- [`docs/iam-scenario-pack-v2.md`](docs/iam-scenario-pack-v2.md)

## Release Goal

The next stable release target is:

```text
trace-v0.3.0-guided-iam-evidence
```

The goal is a finished portfolio artifact for local IAM/access evidence analysis, with future ideas moved to backlog instead of blocking release.
