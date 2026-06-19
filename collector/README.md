# TRACE Collector

## Purpose

The collector layer gathers evidence for TRACE modules and writes structured JSON to stdout. For the M365 Access Path Analyzer, the collector is shaped around future Microsoft 365 / Entra ID evidence boundaries: identity, licensing, sign-in logs, Conditional Access, and device compliance.

Collector scripts are read-only by design. They do not remediate tenant settings or change endpoint, identity, policy, or service configuration.

## Current Limitation

Phase 1 is sample-mode only. Collector scripts load existing synthetic JSON from `../samples` and do not connect to Microsoft Graph or any real tenant.

`UseSampleData` defaults to `true`. Passing `UseSampleData:$false` returns controlled error JSON with code `REAL_COLLECTION_NOT_IMPLEMENTED`.

## Main Entry Point

`Invoke-TraceM365AccessScan.ps1` is the main collector entry point for the M365 Access Path Analyzer.

It accepts:

- `UserPrincipalName`
- `AffectedService`
- `Scenario`
- `UseSampleData`

It returns the normalized scan JSON contract used by the future backend:

- `scenario_id`
- `module`
- `input`
- `identity`
- `licenses`
- `signin_logs`
- `conditional_access`
- `device`

## Snapshot Scripts

The main collector assembles output from these sample-backed snapshot scripts:

- `Get-TraceUserIdentitySnapshot.ps1`
- `Get-TraceLicenseSnapshot.ps1`
- `Get-TraceSignInSnapshot.ps1`
- `Get-TraceConditionalAccessSnapshot.ps1`
- `Get-TraceDeviceComplianceSnapshot.ps1`

Each snapshot script accepts:

- `Scenario`
- `UseSampleData`

Each snapshot script returns structured JSON for its evidence area, controlled error JSON for invalid scenarios, and controlled limitation JSON if a selected sample does not contain that evidence area.

## Supported Sample Scenarios

- `account-disabled`
- `missing-license`
- `ca-details-missing`
- `ca-device-noncompliant`
- `mfa-requirement-not-satisfied`
- `no-recent-signin-evidence`
- `successful-access-baseline`

## Invalid Scenarios

If `Scenario` does not map to an existing sample, scripts return controlled error JSON:

```json
{
  "status": "error",
  "module": "m365-access-path-analyzer",
  "error": {
    "code": "INVALID_SAMPLE_SCENARIO"
  }
}
```

## UseSampleData False

Real collection is intentionally not implemented in Phase 1. If `UseSampleData:$false` is passed, scripts return controlled error JSON:

```json
{
  "status": "error",
  "module": "m365-access-path-analyzer",
  "error": {
    "code": "REAL_COLLECTION_NOT_IMPLEMENTED"
  }
}
```

## Operational Graph Readiness Preflight

`Test-TraceGraphReadiness.ps1` checks whether the local PowerShell session appears ready for future read-only Microsoft Graph operational diagnostics.

The preflight script:

- returns JSON only
- checks whether Microsoft Graph PowerShell cmdlets are available
- checks whether the current session appears connected to Microsoft Graph when context is available
- checks for planned read-only scopes when scope information is available
- does not connect automatically
- does not request write scopes
- does not run write cmdlets
- does not store tokens
- does not remediate tenant settings

Run the preflight:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\collector\Test-TraceGraphReadiness.ps1
```

If Graph connection is needed, connect manually with planned read-only scopes:

```powershell
Connect-MgGraph -Scopes "User.Read.All","AuditLog.Read.All","LicenseAssignment.Read.All"
```

Tenant admin consent may be required before these scopes are usable.

`Directory.Read.All` is broader than the baseline preflight scope set. Keep it as a fallback only if tenant policy, role design, or implementation evidence shows it is required.

## Experimental Operational Graph Collector

`Invoke-TraceM365AccessGraphScan.ps1` is the first standalone Phase 5A operational collector skeleton for single-user Microsoft 365 access diagnostics.

This collector is experimental and intentionally isolated from the current sample-mode backend workflow.

It:

- is read-only
- supports one user at a time
- requires an existing Microsoft Graph PowerShell session
- does not authenticate automatically
- does not call `Connect-MgGraph`
- does not store tokens
- does not remediate tenant settings
- does not scan all tenant users

It requires a work/school Microsoft 365 tenant account with approved read-only delegated scopes. Personal Microsoft accounts are not sufficient for sign-in log diagnostics.

Run the readiness preflight first:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\collector\Test-TraceGraphReadiness.ps1
```

If Graph connection is needed, connect manually with the verified Phase 5A baseline read-only scopes:

```powershell
Connect-MgGraph -Scopes "User.Read.All","AuditLog.Read.All","LicenseAssignment.Read.All"
```

Run the operational collector for one authorized tenant user:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\collector\Invoke-TraceM365AccessGraphScan.ps1 -UserPrincipalName user@company.com -AffectedService "Teams" -LookbackHours 24
```

The collector returns structured JSON with identity, license, sign-in, Conditional Access summary, and device summary evidence where available. Conditional Access and device evidence are currently summarized from sign-in log fields only.

## Manual Test Commands

Run the main collector:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\collector\Invoke-TraceM365AccessScan.ps1 -UserPrincipalName jane.doe@example.com -AffectedService "Microsoft Teams" -Scenario ca-device-noncompliant
```

Run snapshot scripts:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\collector\Get-TraceUserIdentitySnapshot.ps1 -Scenario ca-device-noncompliant
powershell -NoProfile -ExecutionPolicy Bypass -File .\collector\Get-TraceLicenseSnapshot.ps1 -Scenario ca-device-noncompliant
powershell -NoProfile -ExecutionPolicy Bypass -File .\collector\Get-TraceSignInSnapshot.ps1 -Scenario ca-device-noncompliant
powershell -NoProfile -ExecutionPolicy Bypass -File .\collector\Get-TraceConditionalAccessSnapshot.ps1 -Scenario ca-device-noncompliant
powershell -NoProfile -ExecutionPolicy Bypass -File .\collector\Get-TraceDeviceComplianceSnapshot.ps1 -Scenario ca-device-noncompliant
```

Test invalid scenario handling:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\collector\Invoke-TraceM365AccessScan.ps1 -UserPrincipalName jane.doe@example.com -AffectedService "Microsoft Teams" -Scenario not-a-scenario
```

Test real collection guardrail:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\collector\Invoke-TraceM365AccessScan.ps1 -UserPrincipalName jane.doe@example.com -AffectedService "Microsoft Teams" -Scenario ca-device-noncompliant -UseSampleData:$false
```

## Pester Tests

Run all collector tests:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -Command "Invoke-Pester -Script .\collector\tests\Invoke-TraceM365AccessScan.Tests.ps1"
```

Run the Graph readiness preflight tests:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -Command "Invoke-Pester -Script .\collector\tests\Test-TraceGraphReadiness.Tests.ps1"
```

Run the operational Graph collector tests:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -Command "Invoke-Pester -Script .\collector\tests\Invoke-TraceM365AccessGraphScan.Tests.ps1"
```

## Future Microsoft Graph Collection

Future real Microsoft Graph collection must preserve the same normalized output contract used by sample mode. Real collector implementation should replace the evidence source, not the shape of the JSON consumed by the backend analyzer.
