# TRACE Finished Roadmap

## Purpose

This document defines what "finished" means for TRACE.

TRACE should not become an endless collection of samples, dashboards, or unrelated diagnostic tools. It should reach a clear v1.0 state as a professional, local-first IAM and access evidence analysis workbench.

Finished means:

```text
An operator can import or paste redacted IAM/access evidence,
TRACE can parse and normalize it,
TRACE can detect common access-path patterns,
TRACE can produce a support-ready diagnostic report,
and TRACE does all of this locally without making production changes.
```

## Final Product Positioning

TRACE v1.0 should be positioned as:

```text
A local-first IAM/access evidence analyzer for support engineers.
```

It should help answer:

```text
Why is this user, guest, device, app, service, or resource access path failing?
```

It should not try to answer:

```text
Is the whole environment under attack?
```

That second question belongs to a SIEM/SOC platform, not TRACE.

## Non-Negotiable Boundaries

TRACE v1.0 must remain:

- local-first
- read-only
- evidence-based
- deterministic where possible
- safe for public-safe sample mode
- useful without live tenant access
- honest about missing evidence
- explicit about what not to change yet

TRACE v1.0 must not:

- claim to be a SIEM
- claim to replace Microsoft Entra admin tools
- claim to replace Sentinel, Splunk, Elastic, Defender, or a SOC platform
- store credentials, secrets, tokens, passwords, or session cookies
- upload logs to external services
- require tenant admin privileges for core functionality
- modify users, groups, licenses, devices, Conditional Access, DNS, firewall, NTFS, SMB, or application settings
- perform automatic remediation
- claim confirmed root cause from incomplete evidence

## Current Baseline

TRACE already has a strong foundation:

- FastAPI backend
- React/TypeScript frontend shell
- PowerShell read-only collectors
- deterministic analyzer rules
- public-safe sample evidence
- IAM Scenario Pack v2
- report/history paths
- backend and frontend tests
- GitHub Actions CI
- explicit read-only/safety positioning

The remaining work should make TRACE more practical, not broader.

## Finished v1.0 Experience

A complete TRACE v1.0 workflow should feel like this:

```text
1. Operator receives an access ticket.
2. Operator gathers exported or pasted evidence from Entra, M365, AD, Windows, app logs, or ticket notes.
3. Operator redacts sensitive values.
4. Operator imports or pastes evidence into TRACE.
5. TRACE parses and normalizes events.
6. TRACE detects access-path patterns.
7. TRACE shows a timeline and primary finding.
8. TRACE explains evidence used, evidence missing, confidence, limitations, and safe next checks.
9. TRACE says what not to change yet.
10. Operator exports a Markdown/JSON/HTML support report.
```

## Release Stages

### v0.1 - Public Sample Diagnostics Baseline

Status: complete.

Purpose:

- establish TRACE identity and safety model
- provide public-safe diagnostic workflows
- demonstrate deterministic findings and support-ready output

Completion criteria:

- README explains purpose and boundaries
- public-safe samples exist
- backend tests pass
- frontend tests/build pass
- collector scripts are read-only
- no credentials or real tenant data are required

### v0.2 - IAM Scenario Pack v2

Status: complete.

Purpose:

- strengthen IAM-specific reasoning
- move beyond generic support diagnostics
- cover guest/B2B and service-plan access evidence

Completion criteria:

- Guest/B2B access failure scenario exists
- service-plan-disabled scenario exists
- analyzer rules distinguish missing license from service-plan issue
- safe next steps and non-actions are documented
- tests and CI pass

### v0.3 - Repository Professionalization

Status: complete.

Purpose:

- make TRACE safer to maintain
- reduce reliance on local-only validation
- make the repo look and behave more professionally

Completion criteria:

- GitHub Actions CI exists
- backend tests run in CI
- frontend tests/build run in CI
- PowerShell collector parse checks run in CI
- sample collector contract checks run in CI
- roadmap documents exist

### v0.4 - Access Evidence Analyzer Core

Status: next required build stage.

Purpose:

- move from scenario selection to real evidence intake
- introduce log parsing and event normalization
- create the first practical daily-job analyzer path

Scope:

- backend first
- no live Graph
- no frontend required yet
- no broad SIEM scope

Deliverables:

- `POST /api/logs/analyze`
- log analysis request/response models
- generic pasted access log parser
- normalized access event model
- deterministic pattern rules
- Markdown report output
- one or more public-safe sample log fixtures
- backend tests

Required rules:

```text
LOG_PATTERN_CONDITIONAL_ACCESS_BLOCK
LOG_PATTERN_MFA_CHALLENGE_OR_FAILURE
LOG_PATTERN_DISABLED_ACCOUNT_ATTEMPT
LOG_PATTERN_AUTH_SUCCESS_ACCESS_DENIED
LOG_PATTERN_NO_USABLE_EVENTS
```

Completion criteria:

- operator can paste generic redacted access log text
- TRACE returns normalized events
- TRACE returns at least one primary finding when evidence supports it
- TRACE returns evidence missing when evidence is incomplete
- TRACE returns safe next steps and non-actions
- tests pass locally and in CI

### v0.5 - Entra Sign-in Export Analysis

Status: planned.

Purpose:

- make TRACE directly useful for IAM/M365 support evidence
- analyze exported Entra sign-in CSV/JSON without live tenant access

Deliverables:

- Entra sign-in CSV parser
- Entra sign-in JSON parser or normalized JSON importer
- mapping from Entra fields to TRACE normalized events
- rules for Conditional Access, MFA, B2B, legacy auth, no-recent-evidence, and successful-auth-access-denied patterns
- malformed export handling
- backend tests with public-safe fixture files

Completion criteria:

- operator can import/paste an Entra sign-in export sample
- TRACE identifies relevant events for affected user/service/time window
- TRACE detects at least Conditional Access, MFA, disabled-account, and no-relevant-event patterns
- TRACE avoids license/service-plan conclusions unless evidence exists
- reports explain limitations clearly
- CI passes

### v0.6 - Authorization and Resource Assignment Analysis

Status: planned.

Purpose:

- cover the daily-job case where authentication works but resource access fails
- separate authentication from authorization

Deliverables:

- representation for app/resource assignment evidence
- representation for group membership/access package evidence
- rule for resource assignment or group membership missing/unconfirmed
- support for SharePoint/app/file-share style access denial after successful authentication
- report output with resource-owner approval path

Completion criteria:

- TRACE can identify successful authentication plus resource-scoped access denial
- TRACE recommends checking app assignment, SharePoint group, M365 group, security group, access package, or file/share group
- TRACE warns against broad access grants
- tests cover at least one app/SharePoint-style case and one file/share-style case
- CI passes

### v0.7 - Operator UI for Evidence Intake

Status: planned.

Purpose:

- make TRACE usable without directly calling the API
- provide a professional operator experience

Deliverables:

- frontend module for Access Evidence Analyzer
- source type selector
- affected user/service fields
- paste/import evidence area
- redaction warning
- result timeline
- finding panel
- evidence used/missing panels
- copyable Markdown ticket note

Completion criteria:

- operator can analyze pasted evidence from the UI
- frontend shows findings and limitations clearly
- frontend tests cover the new workflow
- CI passes

### v0.8 - Reporting, History, and Review Quality

Status: planned.

Purpose:

- make TRACE output useful for real support handoff
- improve repeatability and evidence review

Deliverables:

- local case history for log-analysis runs
- Markdown report export
- JSON report export
- HTML report view
- report includes timeline, finding, confidence, evidence used, evidence missing, limitations, safe next steps, and non-actions
- redaction reminder in report output

Completion criteria:

- every analysis run can be saved locally
- every run can generate a report
- reports are support-ticket ready
- report examples are public-safe
- CI passes

### v0.9 - Professional Polish and Hardening

Status: planned.

Purpose:

- make TRACE feel finished and maintainable
- remove rough edges before v1.0

Deliverables:

- updated README with current capabilities
- architecture documentation
- safety boundaries documentation updated for log analysis
- sample evidence pack documentation
- troubleshooting guide
- consistent terminology across backend, frontend, collectors, and docs
- CI badge or validation section
- final local audit checklist

Completion criteria:

- no obsolete docs contradict current positioning
- no overclaims about SIEM, SOC, live Graph, or automatic remediation
- all tests pass in CI
- public-safe sample data only
- UI workflow is understandable without explanation
- README explains what TRACE can and cannot do

### v1.0 - Finished Professional Portfolio Release

Status: target finish line.

Purpose:

- create a stable, professional release that can be shown as evidence of practical IAM/access troubleshooting capability

TRACE v1.0 is finished when it can:

- analyze pasted generic access log evidence
- analyze imported/pasted Entra sign-in export evidence
- normalize access events into a consistent model
- detect common IAM/access failure patterns
- distinguish authentication, authorization, licensing, MFA, Conditional Access, device, guest/B2B, and missing-evidence categories
- produce a timeline
- produce a primary finding with confidence
- show evidence used and evidence missing
- give safe next checks
- say what not to change yet
- export a support-ready report
- run fully locally with public-safe samples
- pass backend, frontend, and collector CI checks
- avoid live tenant dependency for core functionality
- avoid all automatic remediation

v1.0 should be tagged only after:

```text
backend tests pass
frontend tests/build pass
collector contract checks pass
sample evidence audit passes
public-safe scan passes
README and docs match current capabilities
local demo path works from a fresh clone
```

Suggested tag name:

```text
trace-v1.0.0-access-evidence-analyzer
```

## Optional After v1.0

These are not required for the tool to be considered finished:

- opt-in read-only Microsoft Graph evidence connector
- more log source parsers
- packaged desktop launcher
- PDF report export
- AI-assisted wording for reports
- richer timeline visualizations
- deeper Windows Event parsing
- deeper IIS/application access-log parsing

These should only be added if they strengthen the core IAM/access evidence analyzer and do not turn TRACE into a SIEM or broad security platform.

## Stop Conditions

TRACE should not keep expanding forever.

Stop adding features when:

- the core access evidence workflow is reliable
- reports are ticket-ready
- CI is stable
- sample evidence is public-safe
- README and docs are accurate
- the tool demonstrates practical IAM/access troubleshooting clearly

Do not add features just because other professional tools have them.

## One-Sentence Finish Definition

TRACE is finished when it can locally analyze redacted IAM/access evidence, explain the likely access-path failure with evidence and limitations, and produce a safe support-ready report without changing any system.
