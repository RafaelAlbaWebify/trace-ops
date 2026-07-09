# TRACE Architecture

TRACE is a local-first IAM/access evidence workbench.

The current architecture focuses on the **Access Evidence** workspace: redacted evidence enters through the UI or API, the backend normalizes and analyzes it, and TRACE returns structured findings, missing evidence, safe next checks, non-actions, and local reports.

## Current High-Level Flow

```text
Browser / React UI
  -> Access Evidence form or guided workflow
  -> FastAPI endpoint POST /api/logs/analyze
  -> source dispatcher
  -> parser or structured analyzer
  -> deterministic findings
  -> local run store
  -> UI result panel + Markdown report
```

## Main Components

```text
trace-ops/
|-- backend/
|   |-- app/
|   |   |-- main.py
|   |   |-- logs.py
|   |   |-- log_models.py
|   |   |-- log_parser.py
|   |   |-- log_analyzer.py
|   |   |-- entra_signin_analyzer.py
|   |   |-- resource_assignment_analyzer.py
|   |   `-- access_run_store.py
|   `-- tests/
|
|-- frontend/
|   |-- src/App.tsx
|   |-- src/api/traceApi.ts
|   |-- src/modules/accessEvidence/AccessEvidencePage.tsx
|   |-- src/ui/ResultPanel.tsx
|   `-- src/styles/trace-shell.css
|
|-- collector/
|   `-- PowerShell read-only collector samples and contract tests
|
|-- scripts/
|   |-- trace-visual-audit-runner.mjs
|   |-- VISUAL_AUDIT_TRACE_LOCAL.bat
|   `-- STOP_TRACE_LOCAL.bat
|
|-- samples/
`-- docs/
```

## Access Evidence API

Primary endpoint:

```text
POST /api/logs/analyze
```

History and report endpoints:

```text
GET /api/logs/history
GET /api/logs/history/{run_id}
GET /api/logs/reports/{run_id}.md
```

## Source Dispatcher

The backend dispatches by `source_type`:

```text
generic_access_log_text
  -> log_parser.py
  -> log_analyzer.py

entra_signin_csv
  -> entra_signin_analyzer.py

resource_assignment_json
  -> resource_assignment_analyzer.py
```

Some frontend guided forms generate analyzer-compatible evidence:

```text
Conditional Access / MFA guided form
  -> generated Entra sign-in CSV
  -> source_type: entra_signin_csv

License / Service Plan guided form
  -> generated generic access evidence
  -> source_type: generic_access_log_text

Guest / B2B guided form
  -> generated generic access evidence
  -> source_type: generic_access_log_text

Resource Assignment guided form
  -> generated structured JSON
  -> source_type: resource_assignment_json
```

## Analyzer Outputs

A successful analysis can include:

- status
- source type
- parse status
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
- run ID

## Local Run Store

Access evidence runs are stored locally as JSON and Markdown.

The default location is:

```text
.trace-runs/access-evidence
```

This store is intended for local demo and portfolio proof. It should contain only public-safe or redacted evidence.

## Frontend Structure

The frontend is organized as a modular operator shell.

The main Access Evidence page supports:

- generic text evidence
- Entra sign-in CSV evidence
- Conditional Access / MFA guided form
- License / Service Plan guided form
- Guest / B2B guided form
- Resource Assignment guided form
- generated analyzer-input preview
- copy analyzer input
- result panel integration

## Visual Audit Architecture

TRACE includes a local visual audit runner that starts the backend and frontend, drives the UI, captures screenshots, records console/page/network errors, and writes a ZIP proof package.

The visual audit covers:

- initial Access Evidence page
- generic access evidence analysis
- Entra CSV analysis
- Conditional Access / MFA guided form and analysis
- License / Service Plan guided form and analysis
- Guest / B2B guided form and analysis
- Resource Assignment guided form and analysis
- copy analyzer input
- History navigation
- Overview navigation

The audit fails when it detects page errors, failed requests, bad HTTP responses, or failed UI interactions.

## Non-Goals

TRACE does not currently include:

- production tenant connection by default
- automatic remediation
- credential storage
- live monitoring
- SIEM or EDR functionality
- formal compliance reporting

Future real data collection should remain read-only and should preserve the same normalized evidence contracts.
