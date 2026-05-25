# TRACE Local MVP Demo Script

This demo shows the verified TRACE local sample-mode MVP for the M365 Access Path Analyzer. It uses synthetic data only.

The demo does not connect to Microsoft Graph, does not connect to a real tenant, and does not perform remediation.

Screenshots of this synthetic demo flow are included in the `Screenshots` section of the repository [README](../README.md#screenshots).

## 1. Start The Backend

From the repository root:

```powershell
cd C:\Users\ralba\Documents\GitHub\trace-ops\backend
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload
```

Backend URL:

```text
http://127.0.0.1:8000
```

## 2. Start The Frontend

Open a second terminal:

```powershell
cd C:\Users\ralba\Documents\GitHub\trace-ops\frontend
npm run dev
```

Frontend URL:

```text
http://127.0.0.1:5173
```

## 3. Open TRACE

Open the frontend URL in a browser.

Confirm the page shows:

- TRACE product name
- M365 Access Path Analyzer module
- sample-mode notice
- backend health status
- sample scan form
- recent history section

## 4. Run A Sample Scan

Use these synthetic demo values:

```text
user_principal_name: jane.doe@example.com
affected_service: SharePoint Online / OneDrive
scenario: ca-device-noncompliant
```

Click **Run scan**.

## 5. Explain The Result

The expected primary diagnosis is that Conditional Access requires a compliant device, but the sign-in device is not compliant.

The UI should show:

- scan status
- history ID
- severity
- confidence
- primary finding
- likely cause
- evidence
- next steps
- what not to change yet
- limitations

## 6. Evidence To Point Out

Explain that TRACE is not guessing from one symptom. It correlates synthetic evidence across the sample collector contract:

- the user account is present and enabled
- the user has relevant licensing
- a recent SharePoint sign-in failed
- Conditional Access details are available
- an applied policy requires a compliant device
- the device compliance state is non-compliant or unknown

This is the support-engineering value: the tool narrows the problem path by showing why the likely cause is more specific than "Microsoft 365 is broken" or "the user cannot sign in."

## 7. Safe Next Steps

Use the displayed next steps to frame an operational response:

- check the device compliance details in Intune
- confirm the device recently checked in
- review the specific compliance policy failure
- retest from a known-compliant device

These are investigation steps, not automatic changes.

## 8. What Not To Change Yet

Call out the safety guidance:

- do not disable Conditional Access globally
- do not remove policy requirements without confirming the affected policy and device evidence
- do not change tenant-wide settings based on one access failure

This demonstrates the TRACE principle of evidence over assumptions.

## 9. Report Links

After the scan saves to local history, use the report links:

- JSON report
- HTML report

Explain that reports are generated locally from saved SQLite scan history and synthetic evidence. They are intended to be support-ready artifacts for handoff, ticket notes, or a troubleshooting record.

## 10. What This Demo Proves

From an IT Operations / Support Engineering perspective, this demo shows that TRACE can:

- preserve a clear boundary between evidence collection, validation, analysis, storage, reporting, and UI
- use synthetic sample data to validate the workflow before real tenant integration
- produce deterministic findings with confidence, limitations, evidence, next steps, and safe non-actions
- store local scan history without tokens or secrets
- present a practical troubleshooting experience instead of raw JSON

The current MVP is intentionally local and sample-mode only. Real Microsoft Graph collection, tenant authentication, permission checks, and production packaging are future work.
