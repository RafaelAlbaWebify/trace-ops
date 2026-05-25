# TRACE Backend

## Purpose

The backend provides the local FastAPI service for TRACE. It validates collector JSON, runs the sample-mode M365 Access Path Analyzer collector, applies deterministic analyzer rules, stores local scan history in SQLite, and serves JSON/HTML reports from saved history records.

## Current Limitation

The backend is sample-mode only. Scan execution calls the existing PowerShell collector with sample data and does not connect to Microsoft Graph or a real Microsoft 365 tenant.

There are no real Graph calls, tenant connections, remediation actions, attack simulation features, or frontend workflows in the backend today.

## Setup

From the repository root:

```powershell
cd C:\Users\ralba\Documents\GitHub\trace-ops\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Run Tests

```powershell
cd C:\Users\ralba\Documents\GitHub\trace-ops\backend
.\.venv\Scripts\Activate.ps1
python -m pytest
```

## Start The Backend

```powershell
cd C:\Users\ralba\Documents\GitHub\trace-ops\backend
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload
```

Default local URL:

```text
http://127.0.0.1:8000
```

## Existing Endpoints

### GET /api/health

Returns backend health and product metadata.

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/health" -Method Get
```

### GET /api/modules

Returns current TRACE module metadata.

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/modules" -Method Get
```

### POST /api/scan/user-access

Runs the sample-mode M365 Access Path Analyzer flow and saves the response to local SQLite history.

Example request:

```powershell
$body = @{
  user_principal_name = "jane.doe@example.com"
  affected_service = "Microsoft Teams"
  scenario = "ca-device-noncompliant"
} | ConvertTo-Json

Invoke-RestMethod `
  -Uri "http://127.0.0.1:8000/api/scan/user-access" `
  -Method Post `
  -ContentType "application/json" `
  -Body $body
```

Supported sample scenarios:

- `account-disabled`
- `missing-license`
- `ca-details-missing`
- `ca-device-noncompliant`
- `mfa-requirement-not-satisfied`
- `no-recent-signin-evidence`
- `successful-access-baseline`

### GET /api/history

Returns recent saved scan history records.

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/history" -Method Get
```

### GET /api/history/{history_id}/report.json

Returns a JSON report for a saved scan history record.

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/history/1/report.json" -Method Get
```

### GET /api/history/{history_id}/report.html

Returns an HTML report for a saved scan history record.

```powershell
Invoke-WebRequest `
  -Uri "http://127.0.0.1:8000/api/history/1/report.html" `
  -Method Get `
  -UseBasicParsing
```

## Local SQLite History

SQLite history is stored locally at:

```text
backend/data/trace_history.sqlite3
```

Stored history includes scan metadata and response JSON. It must not store access tokens, refresh tokens, passwords, client secrets, or raw credentials.

Ignored local data files:

- `backend/data/`
- `*.sqlite3`
- `*.sqlite`
- `*.db`

## Sample-Mode Collector Contract

The scan endpoint uses the PowerShell collector in sample mode only. The backend expects the normalized collector result contract documented in `../collector/README.md` and validates collector output before analysis.

Future real Microsoft Graph collection must preserve the same normalized output contract so analyzer and reporting behavior remains stable.
