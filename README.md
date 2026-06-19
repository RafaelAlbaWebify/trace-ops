# TRACE

**Troubleshooting Reports Across Cloud & Endpoints**

TRACE is a local-first, read-only IT Operations diagnostic portfolio project. It turns scattered support evidence from identity, endpoint, DNS, network, and file-access checks into structured troubleshooting findings with confidence, limitations, safe next steps, and explicit non-actions.

It is designed to demonstrate a support engineering workflow: collect evidence, validate inputs, classify likely causes, explain what is still unknown, and produce support-ready output without making changes to the environment.

TRACE is not a cybersecurity scanner, penetration-testing tool, monitoring platform, or automatic remediation tool.

## Public v1 status

TRACE public v1 includes:

- A modular React and TypeScript operator shell.
- FastAPI backend endpoints for diagnostic workflows.
- PowerShell read-only collectors.
- Deterministic analyzer rules.
- Local JSON and HTML-style report generation paths.
- Public-safe sample evidence.
- Backend and frontend tests.
- Documentation for read-only boundaries and portfolio positioning.

Validated baseline before public v1 publication:

- Frontend production build: passed.
- Frontend tests: passed, 5/5.
- Backend pytest: passed, 106/106.
- Responsive shell accepted across desktop, laptop, tablet-width, and narrow layouts.

## What TRACE diagnoses today

Current public v1 workflows cover:

- Microsoft 365 access-path sample diagnostics.
- Local readiness checks.
- AD user access readiness checks.
- DNS diagnostic evidence.
- FactoryOps-style computer readiness checks.
- FactoryOps-style file-share access diagnostics.
- Diagnostic history and report retrieval.

The strongest public-safe scenario is a file-share access investigation: a user cannot access a department share, but DNS and SMB are healthy. TRACE correlates AD user state, required group membership, observed access denial, and safe next steps without modifying anything.

## What TRACE does not do

TRACE deliberately does not:

- Change AD users, groups, passwords, or memberships.
- Change DNS records.
- Change firewall rules.
- Change NTFS or SMB share permissions.
- Restart services or run remote remediation.
- Store credentials or tokens.
- Impersonate end users.
- Perform offensive security testing.

Its output is intended to support a ticket, handoff, escalation, or safe troubleshooting decision.

## Architecture overview

```text
trace-ops/
|-- backend/     Python FastAPI API, validation, analyzer rules, local report paths
|-- collector/   PowerShell read-only collectors and collector tests
|-- frontend/    React, TypeScript, Vite, modular TRACE operator shell
|-- samples/     Public-safe sample evidence
`-- docs/        Release notes, read-only boundaries, portfolio documentation
```

Typical diagnostic flow:

```text
Operator input
  -> Backend API
  -> Read-only collector or sample evidence
  -> Structured JSON
  -> Backend validation
  -> Deterministic diagnostic rule
  -> Finding, evidence, limitations, safe next steps, non-actions
```

## Frontend structure

The public v1 frontend is organized around a modular shell:

```text
frontend/src/App.tsx
frontend/src/api/traceApi.ts
frontend/src/api/generatedEndpoints.ts
frontend/src/ui/AppShell.tsx
frontend/src/ui/TopBar.tsx
frontend/src/ui/SidebarNav.tsx
frontend/src/ui/ResultPanel.tsx
frontend/src/modules/registry.ts
frontend/src/modules/overview/OverviewPage.tsx
frontend/src/modules/shareAccess/ShareAccessPage.tsx
frontend/src/modules/dns/DnsLookupPage.tsx
frontend/src/modules/identity/AdUserAccessPage.tsx
frontend/src/modules/readiness/ReadinessPage.tsx
frontend/src/modules/history/HistoryPage.tsx
frontend/src/styles/trace-shell.css
```

## Backend endpoints

Important public v1 endpoints include:

```text
GET  /api/health
GET  /api/modules
POST /api/scan/user-access
POST /api/diagnostics/dns
POST /api/diagnostics/ad-user-access
POST /api/diagnostics/factoryops/computer
POST /api/diagnostics/factoryops/file-share-access
GET  /api/history
GET  /api/history/{history_id}/report.json
GET  /api/history/{history_id}/report.html
```

## Run locally

Backend:

```powershell
cd .\backend
..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Frontend:

```powershell
cd .\frontend
npm install
npm run dev
```

Typical local URLs:

```text
Backend:  http://127.0.0.1:8000
Frontend: http://127.0.0.1:5173
```

## Example finding

A public-safe file-share access diagnostic can return a finding like:

```json
{
  "status": "finding",
  "finding_id": "FACTORYOPS_FILE_SHARE_USER_MISSING_REQUIRED_GROUP",
  "severity": "high",
  "confidence": "high",
  "likely_cause": "The user is not present in the required AD group used to authorize read access to the file share.",
  "safe_next_steps": [
    "Confirm the user should have access with the data owner, then request membership in the required group through the normal approval path.",
    "After membership is changed by an authorized admin, have the user sign out/in or purge tickets before retesting."
  ],
  "what_not_to_change_yet": [
    "Do not broaden Everyone, Domain Users, or Authenticated Users permissions to fix a single access issue.",
    "Do not change firewall, DNS, NTFS, share, or AD permissions from this diagnostic alone."
  ]
}
```

## Portfolio value

TRACE demonstrates practical IT Operations and Support Engineering skills:

- Evidence-based troubleshooting.
- Read-only diagnostic design.
- PowerShell collector design.
- FastAPI backend contracts.
- React and TypeScript frontend structure.
- Structured JSON evidence.
- Deterministic diagnostic rules.
- Public-safe sample scenarios.
- Operator-friendly findings with safe next steps and explicit limitations.

The project is intended to be explainable in interviews: it shows how a support engineer can build operational tooling that reduces guesswork without taking unsafe remediation actions.

## Public release notes

See:

```text
docs/github_release_notes_v1_draft.md
docs/public_release_checklist.md
docs/read_only_boundary.md
```

## Roadmap

Future work should stay aligned with IT Operations and Support Engineering:

1. Add a short public demo video.
2. Add more public-safe diagnostic examples.
3. Improve documentation for interview walkthroughs.
4. Add carefully scoped read-only Microsoft Graph integration only when safe.
5. Keep remediation outside TRACE unless a future design explicitly changes that boundary.
