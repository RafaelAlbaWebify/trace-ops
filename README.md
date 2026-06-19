# TRACE

**Troubleshooting Reports Across Cloud & Endpoints**

TRACE is a local-first, read-only IT Operations diagnostic toolkit for support engineers. It turns scattered evidence from identity, endpoint, DNS, network, and file-access checks into clear troubleshooting findings with confidence, limitations, safe next steps, and explicit non-actions.

TRACE is not a cybersecurity scanner, penetration-testing tool, or automatic remediation platform. Its purpose is operational diagnosis: explain what evidence points to, what is still unknown, and what should not be changed until the cause is proven.

## Current Status

TRACE has evolved from a sample Microsoft 365 access analyzer into a multi-module IT Ops diagnostic project with a real FactoryOps homelab validation path.

Implemented and validated areas include:

- Synthetic Microsoft 365 access-path sample workflow.
- Real FactoryOps computer diagnostic scenario against a domain-joined workstation.
- Real FactoryOps file-share access diagnostic scenario against a domain-joined file server.
- Backend API validation through FastAPI.
- PowerShell collectors with structured JSON output.
- Read-only evidence contract across modules.
- Local evidence/report capture packages for portfolio and troubleshooting handoff.

## Validated FactoryOps Homelab

TRACE has been tested in a local FactoryOps-style Windows domain lab:

```text
Domain: factory.local

fw01           pfSense router/firewall between lab zones
dc01           Domain Controller, DNS, AD
trace-admin01  TRACE runner / management workstation
office-pc01    domain-joined workstation target
filesrv01      domain-joined file server target
```

Validated network zones:

```text
Management: 10.10.10.0/24
Office:     10.20.10.0/24
Production: 10.30.10.0/24
Servers:    10.40.10.0/24
```

## Real Scenario: File-Share Access Diagnostic

The strongest current TRACE scenario is a real file-share access investigation:

```text
Share:          \\filesrv01.factory.local\Finance
Allowed user:   FACTORY\finance.ok
Blocked user:   FACTORY\finance.noaccess
Required group: FACTORY\GG_FINANCE_SHARE_READ
```

TRACE proves that the network and server path are healthy while the blocked user lacks the required authorization group.

The blocked-user API result returns:

```text
status: finding
finding_id: FACTORYOPS_FILE_SHARE_USER_MISSING_REQUIRED_GROUP
membership_proven: false
observed_access_denied: true
smb_tcp_445_reachable: true
```

The allowed-user API result returns:

```text
status: success
membership_proven: true
findings: []
```

This is a realistic support scenario: a user cannot access a department share, but DNS and SMB are working. TRACE correlates AD user state, required group membership, observed access denial, and safe next steps without modifying anything.

## What TRACE Diagnoses Today

Current modules and scenarios include:

- Microsoft 365 access-path sample diagnostics.
- FactoryOps computer readiness diagnostics.
- FactoryOps DNS and AD readiness evidence checks.
- FactoryOps file-share access diagnostics.
- Read-only evidence boundary verification.

TRACE can distinguish between:

- DNS or name-resolution problems.
- Network/port reachability problems.
- AD user/object readiness problems.
- Group-membership authorization problems.
- A healthy allowed-user path versus a blocked-user access-denied path.

## What TRACE Does Not Do

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

## Architecture Overview

```text
trace-ops/
|-- collector/   PowerShell read-only collectors and tests
|-- backend/     Python FastAPI API, validation, analyzer rules, local reports
|-- frontend/    React + TypeScript + Vite local UI
|-- samples/     Synthetic and public-safe sample scenarios
|-- specs/       Product, technical, permissions, and test plans
`-- docs/        Architecture, demo scripts, evidence notes, and portfolio docs
```

Typical data flow:

```text
Operator input -> Backend API -> PowerShell collector -> Structured JSON
               -> Backend validation -> Deterministic diagnostic rule
               -> Finding, evidence, limitations, safe next steps
```

## Backend Endpoints

Current important endpoints include:

```text
GET  /api/health
GET  /api/modules
POST /api/scan/user-access
POST /api/diagnostics/factoryops/computer
POST /api/diagnostics/factoryops/file-share-access
GET  /api/history
GET  /api/history/{history_id}/report.json
GET  /api/history/{history_id}/report.html
```

## Run Backend

From the repository root:

```powershell
cd .\backend
..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Or, when working from the homelab runtime copy:

```powershell
cd C:\TraceOps\trace-ops\backend
C:\TraceOps\trace-ops\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Backend URL:

```text
http://127.0.0.1:8000
```

## Example API Request: File-Share Access

```powershell
$Body = @{
  share_host = "filesrv01"
  share_name = "Finance"
  user_sam_account_name = "finance.noaccess"
  required_group_sam_account_name = "GG_FINANCE_SHARE_READ"
  domain_name = "factory.local"
  dns_server = "10.40.10.10"
  observed_access_denied = $true
} | ConvertTo-Json -Depth 8

Invoke-RestMethod `
  -Uri "http://127.0.0.1:8000/api/diagnostics/factoryops/file-share-access" `
  -Method Post `
  -ContentType "application/json" `
  -Body $Body
```

## Example Finding

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

## Portfolio Value

TRACE demonstrates practical IT Operations engineering:

- Evidence-based troubleshooting.
- Safe read-only diagnostic design.
- PowerShell collector design.
- FastAPI backend contracts.
- Structured JSON evidence.
- Deterministic diagnostic rules.
- Homelab validation with AD, DNS, pfSense routing, SMB, and Windows Server.
- Operator-friendly findings with safe next steps and explicit limitations.

The project is designed to be explainable in interviews: it shows how a support engineer can build operational tooling that reduces guesswork without taking unsafe remediation actions.

## Roadmap

Recommended next work:

1. Add a frontend UI card for the FactoryOps file-share diagnostic.
2. Add a public-safe sanitized demo mode with screenshots.
3. Add user account readiness diagnostics.
4. Add workstation/domain secure-channel diagnostics.
5. Add DNS stale/wrong-record diagnostics.
6. Prepare a clean public release package.

## Development Approach

This project follows a specs-driven development workflow. Before implementation tasks, read `AGENTS.md` and the relevant files in `specs/`.

Keep TRACE read-only unless a future spec explicitly changes that boundary.

## TRACE v1 Console Release

Milestone 1 reorganizes TRACE around a professional operator dashboard and a reusable diagnostic module registry.

Delivery workflow:

- One milestone = one package.
- One installer.
- One verifier.
- One report ZIP.
- Module registry first.
- Standard diagnostic output contract.
- Golden real-lab scenarios reused for validation.

The goal is to keep future diagnostics faster to add while preserving TRACE's read-only operational boundary.

## Public release checklist

Before publishing public updates, review docs/public_release_checklist.md and keep generated reports, backups, runtime bundles, caches, virtual environments, and private lab evidence out of the public repository.
