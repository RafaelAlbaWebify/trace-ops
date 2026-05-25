# Product Spec: TRACE

## Product name

TRACE — Troubleshooting Reports Across Cloud & Endpoints

## Summary

TRACE is a local-first IT Operations diagnostic toolkit. It helps support engineers correlate signals from Microsoft 365, Entra ID, endpoints, DNS, mail flow, and infrastructure systems into clear evidence-based troubleshooting reports.

The first module is **M365 Access Path Analyzer**.

## Portfolio goal

TRACE should demonstrate practical IT Operations troubleshooting: connecting identity, endpoint, policy, service, and infrastructure evidence into clear support-ready diagnoses.

The project should support the professional narrative of a Microsoft 365 / Entra ID / infrastructure support engineer who diagnoses cross-system problems rather than simply running checklist scanners.

## Target users

Primary users:

- IT Operations Engineers
- Microsoft 365 Support Engineers
- Systems Administrators
- Technical Support Engineers
- Small MSP technicians

## Product principles

1. Local-first
   - Tenant and diagnostic data should stay on the user's machine.

2. Read-only in v1
   - No automatic tenant changes.
   - No remediation buttons.

3. Evidence-based
   - Every diagnosis must explain what evidence supports it.

4. Honest uncertainty
   - If permissions, licensing, or missing logs limit the diagnosis, say so clearly.

5. Operational language
   - Focus on support-ready troubleshooting, not attack simulation or fear-based security marketing.

## First module: M365 Access Path Analyzer

### Module summary

M365 Access Path Analyzer helps diagnose why a specific user cannot access Microsoft 365 resources by correlating identity, licensing, MFA/authentication, sign-in logs, Conditional Access, and device compliance evidence.

### Core user story

As an IT support engineer, I want to enter a User Principal Name and affected Microsoft 365 service, so that I can understand the likely reason the user cannot access the service and what to check next.

### V1 supported affected services

- Microsoft 365 general access
- Exchange Online / Outlook
- SharePoint Online / OneDrive
- Microsoft Teams

### V1 evidence areas

1. User identity snapshot
   - User exists
   - Account enabled/disabled
   - User type
   - Basic directory properties

2. License snapshot
   - Assigned licenses
   - Missing license indicators relevant to the selected service

3. Authentication/MFA snapshot
   - Available authentication method evidence
   - Missing evidence warnings if data cannot be collected

4. Sign-in snapshot
   - Recent successful and failed sign-ins
   - Failure reason
   - Resource accessed
   - Client app
   - Conditional Access status when available

5. Conditional Access snapshot
   - Applied policies from sign-in logs when available
   - Policy result
   - Grant controls when available

6. Device snapshot
   - Device ID/name from sign-in logs when available
   - Device compliance state when available
   - Last check-in where available

### V1 output

Each scan should produce:

- likely cause
- severity
- confidence
- evidence
- next steps
- what not to change yet
- limitations
- exportable HTML report
- exportable JSON result

## Out of scope for v1

- Automatic remediation
- Tenant-wide security score
- Attack-chain simulation
- Password spraying, phishing, token theft, exploit simulation, or credential collection
- Multi-tenant MSP dashboard
- Cloud-hosted processing
- Full PDF report generation
- Deep Exchange, SharePoint, or Teams administration modules beyond access diagnosis

## Example diagnosis

Input:

- User: jane.doe@example.com
- Affected service: SharePoint Online

Output:

- Likely cause: Conditional Access requires a compliant device, but the sign-in device is marked non-compliant.
- Evidence:
  - User account is enabled.
  - User has a relevant Microsoft 365 license.
  - MFA appears satisfied.
  - Recent SharePoint sign-in failed.
  - Applied Conditional Access policy required a compliant device.
  - Device compliance state is non-compliant.
- Next steps:
  - Check Intune compliance policy failure for the device.
  - Force device sync.
  - Verify BitLocker, Defender, and last check-in.
  - Retest from a known-compliant device.
- What not to change yet:
  - Do not disable Conditional Access globally.
