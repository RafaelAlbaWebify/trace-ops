# Permissions Model

## Principle

TRACE v1 is read-only. It must follow least privilege and explain when missing permissions reduce diagnostic confidence.

## Authentication mode

M365 Access Path Analyzer v1 should use delegated interactive authentication through Microsoft Graph PowerShell SDK.

The authenticated user must have appropriate Microsoft Entra roles and Graph permissions for the evidence being collected.

## Required evidence areas

### Basic user lookup

Purpose:

- Confirm user exists.
- Confirm account enabled/disabled.

Potential Graph permissions:

- User.Read.All
- Directory.Read.All only as a broader fallback where tenant/admin context requires it

### Sign-in logs

Purpose:

- Read recent sign-in events for one user.
- Identify failure reason, resource, client app, and Conditional Access status where available.

Potential Graph permissions:

- AuditLog.Read.All

Notes:

- Personal Microsoft accounts are not supported for sign-in log diagnostics.
- Sign-in log availability depends on tenant licensing and retention.
- If sign-in logs are unavailable, the tool must not invent a diagnosis.

### License details

Purpose:

- Read assigned license details for one user.
- Identify missing license indicators relevant to the selected service.

Potential Graph permissions:

- LicenseAssignment.Read.All

### Conditional Access details from sign-ins

Purpose:

- Read applied Conditional Access policies from sign-in log entries where returned.

Potential Graph permissions:

- Policy.Read.ConditionalAccess

Behavior when unavailable:

- Report that sign-in logs were available but Conditional Access policy details were not returned.
- Reduce confidence.
- Suggest checking permissions/roles before changing policies.

### Device and Intune compliance evidence

Purpose:

- Read device identity and compliance state where available.

Potential Graph permissions:

- Device.Read.All
- DeviceManagementManagedDevices.Read.All if Intune managed device data is used

Behavior when unavailable:

- Report missing device evidence.
- Avoid claiming the device is compliant or non-compliant unless evidence exists.

## Missing evidence behavior

The app must show:

- evidence collected
- evidence missing
- likely reason evidence may be missing
- impact on confidence
- suggested next check

## Storage restrictions

TRACE must not store:

- access tokens
- refresh tokens
- passwords
- client secrets
- raw credentials

TRACE may store:

- synthetic samples
- scan metadata
- selected findings
- local report outputs
- local scan history in SQLite

Sensitive tenant data should be minimized in stored reports.

## Planned Phase 5A: Operational read-only Graph permissions

Phase 5A will add an explicit operational mode for authorized tenant diagnostics while keeping sample mode available for demos and automated tests.

Operational mode must be used only by an administrator or support engineer with authorized access to the Microsoft 365 tenant being diagnosed.

Permissions below are proposed for planning and must be verified against current Microsoft documentation before implementation.

### Baseline read-only permissions

#### User.Read.All

Purpose:

- Look up the target user by UPN.
- Confirm that the user exists.
- Read basic user profile details needed for diagnosis.

Verification note: baseline delegated read permission for user lookup in Phase 5A.

#### AuditLog.Read.All

Purpose:

- Read recent sign-in logs for the target user.
- Inspect failure reason, resource, client app, Conditional Access status, and device details returned by sign-in events.

Verification note: least-privileged delegated permission for Microsoft Graph `signIns` API for work/school accounts. Personal Microsoft accounts are not supported for sign-in logs.

#### LicenseAssignment.Read.All

Purpose:

- Read user license details through Microsoft Graph license details APIs.

Verification note: least-privileged delegated work/school permission for Microsoft Graph license details APIs.

### Optional broader/future permissions

#### Directory.Read.All

Purpose:

- Broader fallback for directory properties depending on tenant/admin context or SDK behavior.
- Should not be part of the first baseline if `User.Read.All` and `LicenseAssignment.Read.All` are sufficient.

Status: optional/broader fallback; avoid unless implementation evidence shows it is needed.

#### Policy.Read.All

Purpose:

- Only if later policy definition lookup is added beyond Conditional Access details returned in sign-in logs.

Status: deferred; not part of the Phase 5A baseline.

#### DeviceManagementManagedDevices.Read.All

Purpose:

- Only if a later Intune managed-device compliance deep dive is added.

Status: deferred; not part of the Phase 5A baseline.

### Phase 5A permission boundaries

Phase 5A must not request write scopes and must not perform:

- remediation
- policy edits
- Conditional Access exclusions
- MFA reset
- password reset
- license assignment or removal
- Intune device actions

TRACE must not store Graph access tokens, refresh tokens, passwords, client secrets, or raw credentials.
