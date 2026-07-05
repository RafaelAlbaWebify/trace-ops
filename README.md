# TRACE

> Troubleshooting Reports Across Cloud & Endpoints

TRACE is the **IAM / support-diagnostics flagship** in the Rafael Alba Technical Portfolio.

It is a local-first, read-only diagnostic workbench for turning scattered support evidence from identity, endpoint, DNS, network and file-access checks into structured troubleshooting findings with confidence, limitations, safe next steps and explicit non-actions.

TRACE is designed to demonstrate a support engineering workflow: collect evidence, validate inputs, classify likely causes, explain what is still unknown, and produce support-ready output without making unsafe changes to the environment.

## Flagship Area

| Area | Flagship | Target role |
|---|---|---|
| IAM - Identity and Access Management | TRACE | IAM Engineer |

TRACE also supports adjacent Application Support, Infrastructure / Production Operations and Security-aware Support workflows, but its main portfolio role is identity/access diagnostics and evidence-based troubleshooting.

## Problem It Solves

In IT support, the real troubleshooting often starts late because the evidence is spread across user reports, admin portals, device state, DNS checks, group memberships, file/share permissions, previous tickets and assumptions.

TRACE turns that scattered evidence into a clearer diagnostic path:

```text
Support symptom
  -> Evidence collection or public-safe sample evidence
  -> Structured validation
  -> Deterministic diagnostic rule
  -> Finding, confidence, limitations, safe next steps and non-actions
  -> Ticket-ready report or escalation handoff
```

## Who It Is For

TRACE is built for:

- IT Operations and support engineers
- IAM / Identity Support practice
- Microsoft 365 / Entra ID-style access troubleshooting practice
- application and infrastructure support scenarios where identity, DNS, endpoint or access evidence matters
- personal portfolio evidence and future controlled B2B/contract work through Webify Digital Solutions Ltd

## Current Status

Current status: **public sample-mode MVP**.

TRACE public v1 includes:

- Modular React and TypeScript operator shell
- FastAPI backend endpoints for diagnostic workflows
- PowerShell read-only collectors
- Deterministic analyzer rules
- Local JSON and HTML-style report generation paths
- Public-safe sample evidence
- Diagnostic history and report retrieval
- Backend and frontend tests
- Documentation for read-only boundaries and portfolio positioning

Validated baseline before public v1 publication:

- Frontend production build: passed
- Frontend tests: passed, 5/5
- Backend pytest: passed, 106/106
- Responsive shell accepted across desktop, laptop, tablet-width and narrow layouts

## Core Workflow

```text
Operator input
  -> Backend API
  -> Read-only collector or sample evidence
  -> Structured JSON
  -> Backend validation
  -> Deterministic diagnostic rule
  -> Finding, evidence, limitations, safe next steps, non-actions
  -> Local JSON / HTML-style report
```

## Current Diagnostic Workflows

Current public v1 workflows cover:

- Microsoft 365 access-path sample diagnostics
- Local readiness checks
- AD user access readiness checks
- DNS diagnostic evidence
- FactoryOps-style computer readiness checks
- FactoryOps-style file-share access diagnostics
- Diagnostic history and report retrieval

The strongest public-safe scenario today is a file-share access investigation: a user cannot access a department share, but DNS and SMB are healthy. TRACE correlates AD user state, required group membership, observed access denial and safe next steps without modifying anything.

## Example Scenario

**Ticket:** User cannot access a department file share.

TRACE helps structure the investigation:

1. Confirm the symptom and affected user.
2. Check whether DNS and SMB/service reachability appear healthy.
3. Review public-safe user/access evidence.
4. Compare required access group vs observed membership.
5. Produce a finding with confidence and limitations.
6. Recommend safe next steps through the normal approval path.
7. Explicitly state what should not be changed yet.

Example finding:

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

## Architecture

```text
trace-ops/
|-- backend/     Python FastAPI API, validation, analyzer rules, local report paths
|-- collector/   PowerShell read-only collectors and collector tests
|-- frontend/    React, TypeScript, Vite, modular TRACE operator shell
|-- samples/     Public-safe sample evidence
`-- docs/        Release notes, read-only boundaries, portfolio documentation
```

### Frontend Structure

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

### Backend Endpoints

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

## Tech Stack

- Python
- FastAPI
- PowerShell
- React
- TypeScript
- Vite
- JSON / HTML-style local reports
- Public-safe sample data

## Run Locally

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

## Safety and Boundaries

TRACE deliberately does not:

- Change AD users, groups, passwords or memberships
- Change DNS records
- Change firewall rules
- Change NTFS or SMB share permissions
- Restart services or run remote remediation
- Store credentials or tokens
- Impersonate end users
- Perform offensive security testing

TRACE is not a cybersecurity scanner, penetration-testing tool, monitoring platform or automatic remediation tool.

Its output is intended to support a ticket, handoff, escalation or safe troubleshooting decision.

## B2B / Contract Use

TRACE can support future controlled service work through Webify Digital Solutions Ltd, especially around:

- Microsoft 365 / identity access troubleshooting evidence
- access issue documentation
- endpoint/readiness evidence
- DNS and dependency evidence for support cases
- escalation-quality reports and handovers
- small-business identity/access health-check style reviews

This repository is currently a public-safe portfolio MVP. It does not connect to real client tenants or process real customer data.

## Portfolio Value

TRACE demonstrates practical IT Operations, IAM-support and Support Engineering skills:

- Evidence-based troubleshooting
- Identity and access diagnostic thinking
- Read-only diagnostic design
- PowerShell collector design
- FastAPI backend contracts
- React and TypeScript frontend structure
- Structured JSON evidence
- Deterministic diagnostic rules
- Public-safe sample scenarios
- Operator-friendly findings with safe next steps and explicit limitations

The project is intended to be explainable in interviews and contract conversations: it shows how a support engineer can build operational tooling that reduces guesswork without taking unsafe remediation actions.

## Public Release Notes

See:

```text
docs/github_release_notes_v1_draft.md
docs/public_release_checklist.md
docs/read_only_boundary.md
```

## Roadmap

Future work should stay aligned with IAM, IT Operations and Support Engineering:

1. Add a short public demo video.
2. Add more public-safe IAM and access-diagnostic examples.
3. Improve documentation for interview and contract walkthroughs.
4. Add screenshots and workflow visuals to the repository.
5. Add carefully scoped read-only Microsoft Graph integration only when safe.
6. Keep remediation outside TRACE unless a future design explicitly changes that boundary.

## Related Flagships

TRACE is part of the Rafael Alba Technical Portfolio:

- IAM -> TRACE -> IAM Engineer
- ASE -> INFIOS -> Application Support Engineer
- SOC -> CustosOps -> SOC Analyst
- AUTO -> WATCH -> IT Automation Engineer
- IPPO -> OPSCORE -> Infrastructure / Production Operations Engineer
- AIDE -> YTIS -> AI Developer / GenAI Application Developer
