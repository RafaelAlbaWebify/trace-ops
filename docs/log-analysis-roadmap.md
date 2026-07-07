# TRACE Log Analysis Roadmap

## Purpose

TRACE should evolve from public-safe sample diagnostics into a practical, local-first IAM and access log evidence analyzer.

The goal is not to build a SIEM, EDR, alerting platform, vulnerability scanner, or automatic remediation tool.

The goal is to help an operator take exported or pasted access evidence, normalize it, detect likely access-path patterns, and produce a structured support-ready diagnostic report.

```text
Exported or pasted evidence
  -> local parser
  -> normalized events
  -> deterministic access-pattern rules
  -> findings, confidence, evidence used, evidence missing
  -> safe next checks, explicit non-actions, ticket-ready report
```

## Product Direction

TRACE should be useful in daily support/IAM work where the operator may have partial evidence from admin portals, tickets, logs, or read-only collector output.

The samples remain useful as public-safe fixtures for tests, CI, documentation, and portfolio demonstration. They should not become the main product experience.

The main product experience should become:

```text
I have evidence from a real access problem.
I can paste or import it locally.
TRACE helps me structure the diagnosis without changing production.
```

## Safety Boundaries

TRACE log analysis must remain local-first and read-only.

TRACE must not:

- store passwords, tokens, secrets, or session cookies
- require tenant administrator privileges for the first log-analysis milestones
- connect to Microsoft Graph by default
- modify Entra ID, AD, Microsoft 365, users, groups, licenses, Conditional Access, devices, DNS, firewall, SMB, NTFS, or application settings
- upload logs to external services
- claim root cause when evidence is incomplete
- act as a SIEM, MDR, vulnerability scanner, or automated remediation platform

TRACE should:

- warn operators to redact personal or sensitive data
- support synthetic/public-safe sample logs for tests
- prefer deterministic rules over opaque AI conclusions
- show evidence used and evidence missing
- separate likely cause from confirmed root cause
- recommend safe next checks through the normal approval path
- include explicit non-actions when a risky change should not be made yet

## Current Baseline

TRACE already has:

- FastAPI backend diagnostic workflows
- deterministic analyzer rules
- PowerShell read-only collectors
- public-safe sample evidence
- backend and frontend tests
- GitHub Actions CI
- IAM Scenario Pack v2 with Guest/B2B and service-plan-disabled evidence cases

This roadmap should build on that baseline instead of replacing it.

## M2A - Log Evidence Analyzer Foundation

### Goal

Add the first backend-only log analysis endpoint.

Proposed endpoint:

```text
POST /api/logs/analyze
```

### Supported input

Initial request shape:

```json
{
  "source_type": "generic_access_log_text",
  "affected_user": "sample.user@contoso.invalid",
  "affected_service": "SharePoint Online",
  "content": "pasted or uploaded log content",
  "notes": "optional operator notes"
}
```

Initial source types:

```text
generic_access_log_text
entra_signin_csv
entra_signin_json
windows_event_json
application_access_log_text
```

M2A does not need to fully support every source type. It should define the model and implement one practical parser first.

### Output

The endpoint should return:

```text
source_type
parse_status
normalized_events
detected_patterns
primary_finding
confidence
evidence_used
evidence_missing
safe_next_steps
what_not_to_change_yet
limitations
report_markdown
```

### First parser

Start with `generic_access_log_text` because it is easiest to test and does not depend on vendor-specific exports.

The parser should detect simple timestamped lines and access keywords such as:

```text
success
failure
access denied
conditional access
mfa
multi-factor
disabled
not licensed
not assigned
forbidden
unauthorized
non-compliant
```

### First rules

Add deterministic pattern rules such as:

```text
LOG_PATTERN_CONDITIONAL_ACCESS_BLOCK
LOG_PATTERN_MFA_CHALLENGE_OR_FAILURE
LOG_PATTERN_DISABLED_ACCOUNT_ATTEMPT
LOG_PATTERN_AUTH_SUCCESS_ACCESS_DENIED
LOG_PATTERN_NO_USABLE_EVENTS
```

### Definition of done

M2A is complete when:

- backend model exists for log analysis input/output
- parser handles generic pasted log text
- endpoint returns normalized events and findings
- tests cover successful parse, no usable events, and at least two finding patterns
- no live tenant or external service is used
- CI passes

## M2B - Entra Sign-in Export Parser

### Goal

Support imported Entra ID sign-in evidence from CSV or JSON export.

This should not require live Graph access.

### Useful fields

Expected evidence fields may include:

```text
createdDateTime
userPrincipalName
appDisplayName
resourceDisplayName
status.errorCode
status.failureReason
conditionalAccessStatus
clientAppUsed
ipAddress
deviceDetail.displayName
deviceDetail.isCompliant
deviceDetail.trustType
riskDetail
riskState
```

### Diagnostic patterns

Rules should identify:

```text
conditional access failure
MFA requirement or repeated challenge pattern
disabled account sign-in attempt
successful authentication followed by resource access denial
legacy client or unexpected client app use
no recent sign-in evidence for the affected user/service
```

### Evidence discipline

The analyzer should avoid claiming license or service-plan root cause from sign-in logs alone unless the exported evidence explicitly shows it.

If the logs do not contain license/service-plan data, the output should say that license evidence is missing.

### Definition of done

M2B is complete when:

- Entra sign-in CSV parser exists
- parser maps source rows into normalized events
- malformed CSV produces safe validation errors
- tests cover CA failure, MFA pattern, no recent evidence, and malformed input
- report explains evidence limitations clearly
- CI passes

## M2C - Authorization / Resource Assignment Evidence

### Goal

Add support for the common daily-job case where authentication succeeds but access to one app, SharePoint site, file share, or internal resource still fails.

### Core distinction

```text
Authentication: the user can prove who they are.
Authorization: the user is allowed to access the specific resource.
```

### Rule direction

Potential rule:

```text
RESOURCE_ASSIGNMENT_OR_GROUP_MEMBERSHIP_MISSING_OR_UNCONFIRMED
```

This rule should trigger when evidence suggests:

- account exists and is enabled
- recent authentication appears successful
- MFA/CA/device evidence does not explain the failure
- access denial is scoped to one resource
- group/resource assignment is missing or not provided

### Safe next steps

The output should recommend:

- confirm expected access with the resource owner
- check app assignment, SharePoint group, M365 group, security group, access package, or file/share group
- request access through the normal approval path
- retest after authorized change and token/session refresh

### What not to change yet

The output should warn:

- do not add broad admin or owner access
- do not add the user to large groups without approval
- do not weaken Conditional Access if the failure is resource-scoped
- do not change DNS, firewall, or service configuration without evidence

### Definition of done

M2C is complete when:

- manual or log-derived authorization evidence can be represented
- analyzer can separate sign-in success from resource authorization failure
- tests cover SharePoint/app-style access denial after successful authentication
- report output is ticket-ready
- CI passes

## M2D - Windows and Application Access Logs

### Goal

Support exported Windows Event and application access evidence relevant to IAM/support work.

This milestone should not become a SOC product.

### Candidate evidence

```text
Windows logon success/failure events
application access denied entries
IIS or web application 401/403 patterns
file/share access evidence
PowerShell collector output
```

### Diagnostic patterns

```text
repeated failed logon pattern
access denied after service reachable
401/403 web access pattern
file/share authorization issue
possible stale session or token refresh needed
```

### Definition of done

M2D is complete when:

- at least one Windows or application log format is parsed
- parser output maps to normalized access events
- analyzer produces practical support findings
- docs clarify that TRACE is not a SOC/SIEM replacement
- CI passes

## M2E - Frontend Log Intake

### Goal

Add a simple operator UI for local log intake.

### UI behavior

The UI should allow the operator to:

- choose source type
- paste redacted log content
- enter affected user and affected service
- run local analysis
- view findings, evidence used, evidence missing, safe next steps, and non-actions
- copy a Markdown ticket note

### UX warnings

The UI should remind the operator:

```text
Do not paste passwords, tokens, secrets, session cookies, personal data, or customer-sensitive content. Redact identifiers when possible.
```

### Definition of done

M2E is complete when:

- frontend form exists
- API integration works locally
- result panel shows finding and report sections clearly
- frontend tests cover the new form path
- CI passes

## M2F - Optional Read-only Graph Evidence Path

### Goal

Only after offline import works, consider a carefully isolated read-only Microsoft Graph evidence path.

This is optional and should not block TRACE's practical value.

### Boundary

Graph integration should remain:

- opt-in
- read-only
- scoped
- explicit about required permissions
- separated from public-safe sample mode
- unable to modify users, groups, licenses, devices, policies, or tenant settings

### Definition of done

M2F is complete only when:

- permissions are documented
- no token or secret is stored by TRACE
- failures are safe and explain missing permissions clearly
- public sample mode remains the default
- CI covers non-Graph paths

## Recommended Build Order

```text
1. M2A - generic pasted log analyzer backend
2. M2B - Entra sign-in CSV parser
3. M2C - authorization/resource assignment evidence
4. M2E - frontend log intake
5. M2D - Windows/application access logs
6. M2F - optional read-only Graph evidence path
```

## Near-term Next Patch

The next build patch should be M2A only.

Do not start with UI, Graph, or many parsers at once.

M2A should add:

- backend log analysis request/response models
- parser for generic pasted log text
- deterministic rules for common access-log patterns
- `POST /api/logs/analyze`
- backend tests
- one public-safe sample log fixture
- documentation update

This keeps TRACE practical and avoids turning it into either a toy simulator or an over-scoped SIEM.
