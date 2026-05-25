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

## Future Microsoft Graph Collection

Future real Microsoft Graph collection must preserve the same normalized output contract used by sample mode. Real collector implementation should replace the evidence source, not the shape of the JSON consumed by the backend analyzer.
