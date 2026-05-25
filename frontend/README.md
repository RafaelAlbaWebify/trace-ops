# TRACE Frontend

## Purpose

The frontend is the local React + TypeScript + Vite user interface for TRACE. It provides the working MVP experience for the M365 Access Path Analyzer by calling the local FastAPI backend and presenting scan results in a support-friendly interface.

## Current Limitation

The frontend is sample-mode only. It does not connect to a Microsoft 365 tenant, request Microsoft Graph permissions, authenticate users, or perform remediation.

All scan results come from the backend sample-mode workflow, which uses the PowerShell collector and synthetic JSON files in `../samples`.

## Backend Requirement

Start the backend before using the frontend:

```powershell
cd C:\Users\ralba\Documents\GitHub\trace-ops\backend
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload
```

Backend URL:

```text
http://127.0.0.1:8000
```

The Vite development server proxies `/api` requests to this backend.

## Install Dependencies

From the frontend folder:

```powershell
cd C:\Users\ralba\Documents\GitHub\trace-ops\frontend
npm install
```

## Build

```powershell
cd C:\Users\ralba\Documents\GitHub\trace-ops\frontend
npm run build
```

The build writes production assets to `frontend/dist/`.

## Run Tests

```powershell
cd C:\Users\ralba\Documents\GitHub\trace-ops\frontend
npm run test -- --run
```

Frontend tests use Vitest, jsdom, and React Testing Library. API calls are mocked, so the backend does not need to be running for frontend tests.

## Run Development Server

```powershell
cd C:\Users\ralba\Documents\GitHub\trace-ops\frontend
npm run dev
```

Frontend URL:

```text
http://127.0.0.1:5173
```

## Current UI Support

The current MVP UI supports:

- backend health status
- TRACE product display
- M365 Access Path Analyzer module display
- sample scan form with user principal name, affected service, and scenario selection
- analyzer results including status, primary finding, severity, confidence, likely cause, evidence, next steps, what not to change yet, and limitations
- recent local scan history
- JSON and HTML report links for saved history records

## Not Implemented Yet

The frontend does not currently include:

- tenant connection
- Microsoft Graph authentication or permission consent
- real Graph evidence collection
- remediation controls
- attack simulation workflows

The MVP is intentionally limited to local sample-mode diagnosis.
