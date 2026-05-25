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
- Read assigned licenses.

Potential Graph permissions:

- User.Read.All
- Directory.Read.All where required by implemented cmdlets

### Sign-in logs

Purpose:

- Read recent sign-in events for one user.
- Identify failure reason, resource, client app, and Conditional Access status where available.

Potential Graph permissions:

- AuditLog.Read.All

Notes:

- Sign-in log availability depends on tenant licensing and retention.
- If sign-in logs are unavailable, the tool must not invent a diagnosis.

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
