# TRACE

> Troubleshooting Reports Across Cloud & Endpoints

TRACE is my **IAM / access evidence analysis flagship**.

It is a local-first, read-only workbench for turning redacted access evidence from identity, endpoint, DNS, network, application, file/share and Microsoft 365-style sources into structured troubleshooting findings with confidence, limitations, safe next steps and explicit non-actions.

I use TRACE to demonstrate a support engineering workflow: collect evidence, validate inputs, classify likely causes, explain what is still unknown, and produce support-ready output without making unsafe changes to the environment.

## Flagship Area

| Area | Flagship | Target role |
|---|---|---|
| IAM - Identity and Access Management | TRACE | IAM Engineer |

TRACE also supports adjacent Application Support, Infrastructure / Production Operations and Security-aware Support workflows, but I position it mainly as my identity/access diagnostics and evidence-based troubleshooting flagship.

## Current Status

Current status: **v0.9 professional polish / v1.0 release-candidate path**.

Completed foundations:

- Modular React and TypeScript operator shell
- FastAPI backend endpoints for diagnostic workflows
- PowerShell read-only collectors
- Deterministic analyzer rules
- Public-safe sample evidence
- IAM Scenario Pack v2
- Access Evidence Analyzer backend core
- Entra sign-in CSV export analysis
- Resource assignment / authorization evidence analysis
- Operator UI for access evidence intake
- Local JSON and Markdown run history for access evidence analysis
- GitHub Actions CI for backend, frontend and collector contract checks

## Product Positioning

TRACE is not a SIEM, SOC platform, EDR, vulnerability scanner, tenant automation system or remediation tool.

TRACE is a focused IAM/access troubleshooting workbench:

```text
redacted evidence
  -> parser or structured input
  -> normalized access events
  -> deterministic access-pattern rules
  -> finding, confidence, evidence used, evidence missing
  -> safe next checks, explicit non-actions, support-ready report
```

## Who It Is For

I am building TRACE for:

- IT Operations and support engineering practice
- IAM / Identity Support practice
- Microsoft 365 / Entra ID-style access troubleshooting practice
- application and infrastructure support scenarios where identity, DNS, endpoint or access evidence matters
- my personal portfolio evidence and future controlled B2B/contract work through Webify Digital Solutions Ltd

## Current Access Evidence Analyzer

The practical daily-job workflow is now the **Access Evidence** workspace.

Supported evidence paths through `POST /api/logs/analyze`:

```text
generic_access_log_text
entra_signin_csv
resource_assignment_json
```

The analyzer can currently identify and structure evidence for:

- Conditional Access-style blocking evidence
- MFA challenge or failure evidence
- disabled-account attempt evidence
- authentication success followed by resource access denial
- exported Entra sign-in CSV evidence
- legacy client values in sign-in evidence
- resource assignment or group membership missing/unconfirmed evidence
- missing or unsupported evidence

Each run returns:

- `run_id`
- normalized events
- detected patterns
- primary finding
- confidence
- evidence used
- evidence missing
- safe next steps
- what not to change yet
- limitations
- Markdown report

## Backend Endpoints

```text
GET  /api/health
GET  /api/modules
POST /api/logs/analyze
GET  /api/logs/history
GET  /api/logs/history/{run_id}
GET  /api/logs/reports/{run_id}.md
POST /api/scan/user-access
POST /api/diagnostics/dns
POST /api/diagnostics/ad-user-access
POST /api/diagnostics/factoryops/computer
POST /api/diagnostics/factoryops/file-share-access
GET  /api/history
GET  /api/history/{history_id}/report.json
GET  /api/history/{history_id}/report.html
```

## Architecture

```text
trace-ops/
|-- backend/     Python FastAPI API, validation, analyzer rules, local report paths
|-- collector/   PowerShell read-only collectors and collector tests
|-- frontend/    React, TypeScript, Vite, modular TRACE operator shell
|-- samples/     Public-safe sample evidence
`-- docs/        Release notes, roadmaps, boundaries and portfolio documentation
```

### Key Backend Files

```text
backend/app/logs.py
backend/app/log_models.py
backend/app/log_parser.py
backend/app/log_analyzer.py
backend/app/entra_signin_analyzer.py
backend/app/resource_assignment_analyzer.py
backend/app/access_run_store.py
```

### Key Frontend Files

```text
frontend/src/App.tsx
frontend/src/api/traceApi.ts
frontend/src/modules/accessEvidence/AccessEvidencePage.tsx
frontend/src/modules/registry.ts
frontend/src/ui/ResultPanel.tsx
frontend/src/styles/trace-shell.css
```

## Tech Stack

- Python
- FastAPI
- PowerShell
- React
- TypeScript
- Vite
- JSON / Markdown / HTML-style local reports
- Public-safe sample data

## Run Locally

Backend:

```powershell
Set-Location -LiteralPath "C:\Users\ralba\Documents\GitHub\trace-ops\backend"
..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Frontend:

```powershell
Set-Location -LiteralPath "C:\Users\ralba\Documents\GitHub\trace-ops\frontend"
npm install
npm run dev
```

Typical local URLs:

```text
Backend:  http://127.0.0.1:8000
Frontend: http://127.0.0.1:5173
```

## Validate Locally

```powershell
Set-Location -LiteralPath "C:\Users\ralba\Documents\GitHub\trace-ops\backend"
python -m pytest

Set-Location -LiteralPath "C:\Users\ralba\Documents\GitHub\trace-ops\frontend"
npm test
npm run build
```

## Safety and Boundaries

TRACE deliberately does not:

- Change AD users, groups, passwords or memberships
- Change Entra ID users, groups, licenses, devices or policies
- Change DNS records
- Change firewall rules
- Change NTFS or SMB share permissions
- Restart services or run remote remediation
- Store credentials or tokens
- Impersonate end users
- Upload logs to external services
- Perform offensive security testing
- Claim confirmed root cause when evidence is incomplete

TRACE should be used to structure evidence, support ticket notes, safe next checks and escalation handoffs. It does not replace Microsoft Entra admin tools, Microsoft Sentinel, Splunk, Elastic, Defender, a SOC platform or a production IAM governance system.

## Roadmap Docs

```text
docs/log-analysis-roadmap.md
docs/finished-roadmap.md
docs/iam-scenario-pack-v2.md
```

The v1.0 target is a stable professional portfolio release for local IAM/access evidence analysis, not an endless expansion into a SIEM or live tenant automation platform.
