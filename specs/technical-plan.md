# Technical Plan

## Architecture

TRACE has three main layers:

1. Collector layer
   - PowerShell 7 scripts
   - Uses Microsoft Graph PowerShell SDK for Microsoft 365 / Entra ID modules
   - Performs read-only queries
   - Outputs structured JSON

2. Backend layer
   - Python FastAPI
   - Runs collector scripts as subprocesses
   - Validates collector JSON
   - Applies deterministic diagnosis rules
   - Stores local scan history in SQLite
   - Generates HTML and JSON reports

3. Frontend layer
   - React + TypeScript + Vite
   - Provides a local GUI
   - Shows modules
   - Displays findings, evidence, confidence, limitations, and next steps
   - Exports HTML and JSON reports

## Initial repository structure

For v1, keep a simple structure:

```text
trace-ops/
|-- AGENTS.md
|-- README.md
|-- specs/
|-- collector/
|-- backend/
|-- frontend/
|-- samples/
|-- reports/
`-- docs/
```

Later, when a second module is added, refactor to:

```text
trace-ops/
|-- modules/
|   |-- m365-access-path-analyzer/
|   |-- dns-health-investigator/
|   `-- endpoint-readiness-checker/
|-- shared/
`-- specs/
```

Do not prematurely build the modules folder unless the specs are updated.

## Data flow for M365 Access Path Analyzer

1. User opens TRACE locally.
2. User selects M365 Access Path Analyzer.
3. User enters User Principal Name and affected service.
4. Frontend sends request to backend.
5. Backend runs PowerShell collector scripts.
6. Collector returns structured JSON.
7. Backend validates collector output.
8. Analyzer applies deterministic rules.
9. Backend stores scan result locally in SQLite.
10. Frontend displays support-ready diagnosis.
11. User exports HTML or JSON report.

## Development mode

Development must begin with synthetic sample data.

All collector scripts should eventually support a sample mode so tests and demos can run without a real tenant.

## Microsoft Graph integration

The first real integration should use delegated interactive authentication through Microsoft Graph PowerShell SDK.

V1 must not store access tokens.

## Analysis engine

Use deterministic rules in v1.

Each rule must specify:

- rule_id
- trigger evidence
- missing evidence behavior
- severity
- confidence
- likely cause
- next steps
- what not to change yet
- limitations

## Initial diagnosis rules

Implement only these in the first analyzer MVP:

1. USER_ACCOUNT_DISABLED
2. MISSING_SERVICE_LICENSE
3. RECENT_SIGNIN_FAILURE
4. CA_FAILURE_DETAILS_MISSING
5. CA_DEVICE_COMPLIANCE_BLOCK
6. NO_RECENT_SIGNIN_EVIDENCE

## Reporting

V1 reports should be HTML and JSON only.

HTML report sections:

- Summary
- Likely cause
- Confidence
- Evidence table
- Technical details
- Recommended next steps
- What not to change yet
- Limitations

PDF can be considered later.
