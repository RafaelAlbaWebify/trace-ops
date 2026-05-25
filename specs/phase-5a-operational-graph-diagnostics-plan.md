# Phase 5A: Operational Graph Diagnostics Plan

## A. Objective

Turn TRACE from a local sample-mode portfolio MVP into a real read-only Microsoft 365 access diagnostic tool for authorized tenant use.

Phase 5A must:

- Keep sample mode available for demos, development, and automated tests.
- Add an explicit operational mode for authorized real tenant diagnostics.
- Preserve the existing TRACE evidence contract where possible.
- Keep the product read-only and evidence-based.

Operational mode is for IT administrators and support engineers using their own authorized tenant/admin permissions. It must not be used against tenants where the operator does not have permission.

## B. Primary Operational Use Case

Given `user@company.com`, diagnose why this user may be blocked from Microsoft 365 access.

The first operational workflow should help with:

- Microsoft Teams
- SharePoint Online / OneDrive
- Exchange Online / Outlook
- generic Microsoft 365 access issues

The support engineer should be able to enter a real user principal name, select or type the affected Microsoft 365 service, optionally choose a time window, collect read-only evidence, and receive evidence-based next steps.

## C. First Operational Evidence Scope

Phase 5A should collect only the minimum live evidence needed for access-path diagnosis:

- User lookup by UPN.
- Account enabled / disabled.
- User type.
- Assigned license details.
- Recent sign-in logs for the user.
- Sign-in failure reason.
- Conditional Access status from sign-in logs.
- Failed Conditional Access policy names/details when available from sign-in data.
- Device detail available from the sign-in event.
- Time window filtering.

Intune compliance deep dive is not part of the first operational scope unless the evidence is already present in the sign-in event.

## D. Explicitly Out Of Scope For Phase 5A

Phase 5A must not include:

- Remediation.
- Policy edits.
- Conditional Access exclusions.
- MFA reset.
- Password reset.
- License assignment or removal.
- Intune device compliance deep dive, except device details already visible in sign-in logs.
- Attack simulation.
- Graph token storage.
- Tenant write actions of any kind.

## E. Proposed Collector Design

Keep the current sample-mode collector stable.

Add a separate experimental operational collector:

```text
collector/Invoke-TraceM365AccessGraphScan.ps1
```

Preferred approach:

- Use PowerShell 7 with the Microsoft Graph PowerShell SDK.
- Require the operator to authenticate interactively or already be authenticated with appropriate delegated permissions.
- Do not store tokens.
- Do not request write scopes.
- Normalize live Graph evidence into the existing TRACE evidence contract where possible:
  - `scenario_id` can be replaced or supplemented by an operational scan identifier later.
  - `module`
  - `input`
  - `identity`
  - `licenses`
  - `signin_logs`
  - `conditional_access`
  - `device`
- Return controlled JSON errors for operational failures.

The first operational collector should only perform user lookup and recent sign-in log retrieval. Conditional Access and device evidence should initially come from sign-in log fields where available.

## F. Proposed Backend Integration

Add operational mode separately from sample mode.

Possible backend options:

- Add a separate endpoint such as `POST /api/scan/user-access/graph`.
- Add an explicit mode flag such as `mode: "sample" | "operational"`.

Recommendation for first implementation: use a separate endpoint or clearly isolated runner so sample-mode behavior remains untouched.

Backend rules:

- Do not make operational mode the default.
- Validate live evidence with the same contract validation approach used for sample mode.
- Return controlled backend errors for collector failures.
- Store scan history locally only after clearly documenting privacy implications.
- Keep sample-mode tests and behavior unchanged.

## G. Proposed Frontend Integration

Add frontend support later, after the standalone collector and backend runner are stable.

Planned UI changes:

- Add a mode selector:
  - Sample mode
  - Operational mode
- Operational mode must show a clear warning:

```text
This queries a real Microsoft 365 tenant using your signed-in permissions.
```

- Add a time window selector.
- Allow selecting or typing the affected Microsoft 365 service.
- Keep remediation actions absent.
- Clearly label missing permissions or unavailable evidence.

## H. Error Handling Requirements

Operational mode must return controlled JSON errors for:

- Microsoft Graph PowerShell SDK missing.
- Not authenticated to Graph.
- Insufficient permissions.
- User not found.
- No sign-in logs found.
- Sign-in logs unavailable due to licensing or retention.
- Conditional Access details unavailable.
- Tenant restrictions.
- API throttling or transient Graph errors.

Error responses must avoid secrets and should include:

- stable error code
- human-readable message
- affected evidence area when possible
- impact on diagnostic confidence
- suggested next check

## I. Privacy And Data Handling

TRACE remains local-first.

Operational mode must follow these rules:

- Store data locally only.
- Do not store access tokens, refresh tokens, passwords, client secrets, or raw credentials.
- Warn before saving live tenant evidence to local history.
- Provide redaction guidance for screenshots and exported reports.
- Avoid committing live reports, screenshots, or SQLite history.
- Keep `backend/data/` ignored.
- Keep exported reports clearly user-controlled.
- Minimize tenant data stored in reports.

## J. Proposed Read-Only Permission Model

These permissions are proposed and must be verified against current Microsoft documentation before implementation.

### User.Read.All

Purpose:

- Read user profile details by UPN.
- Confirm that the user exists.

Status: to verify against Microsoft documentation before implementation.

### Directory.Read.All

Purpose:

- Read directory properties that may be needed for account status, user type, and license assignment details.

Status: to verify against Microsoft documentation before implementation.

### AuditLog.Read.All

Purpose:

- Read recent sign-in logs for the target user.
- Inspect failure reasons, resource, client app, Conditional Access status, and device details returned by sign-in events.

Status: to verify against Microsoft documentation before implementation.

### Policy.Read.All

Purpose:

- Only if later policy definition lookup is added beyond details returned in sign-in logs.

Status: deferred; to verify against Microsoft documentation before implementation.

### DeviceManagementManagedDevices.Read.All

Purpose:

- Only if a later Intune compliance deep dive is added.

Status: deferred; to verify against Microsoft documentation before implementation.

## K. Testing Strategy

Testing must not require a real tenant by default.

Phase 5A tests should:

- Keep all sample-mode tests.
- Add mocked Graph response fixtures.
- Validate that mocked live evidence normalizes into the TRACE evidence contract.
- Verify controlled errors for:
  - missing authentication
  - missing permissions
  - user not found
  - no sign-in logs
  - Conditional Access details unavailable
  - transient Graph failures
- Add an optional manual operational checklist for an authorized tenant.

Automated CI and local default test runs must not require Graph authentication or tenant access.

## L. Safety / Rollback Strategy

Operational mode must be easy to disable without affecting sample mode.

Safety controls:

- Operational mode behind an explicit flag or endpoint.
- Sample mode remains the default.
- No write scopes.
- No write cmdlets.
- No remediation actions.
- No policy changes.
- Clear rollback path: disable the operational endpoint/mode and keep sample-mode diagnostics working.

Collector guardrails:

- Search tests should continue to reject write cmdlets and broad remediation patterns.
- Operational collector should fail closed with controlled error JSON when prerequisites are missing.

## M. Implementation Order

Smallest first implementation task:

1. Add standalone operational collector script that only performs user lookup and recent sign-in log retrieval.
2. Add mocked tests for live Graph response normalization and controlled errors.
3. Add backend runner support for the operational collector.
4. Add frontend mode selector later.

Do not start with frontend operational mode. Prove the read-only collector contract first.
