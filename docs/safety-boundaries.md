# TRACE Safety Boundaries

TRACE is designed as a local, read-only evidence workbench for IAM and access-support practice.

Its purpose is to help an operator structure redacted evidence, document what is known, document what is missing, and prepare safer support notes.

## Core Rule

TRACE should help answer:

```text
What evidence do we have?
What pattern does it suggest?
What evidence is missing?
What should be checked next?
What should not be changed yet?
```

TRACE should not be used as a production change tool.

## Data Boundary

Use only public-safe or redacted evidence.

Do not paste:

- passwords
- secrets
- session cookies
- raw tokens
- private customer content
- personal data that is not needed for the demo
- real incident data without approval and redaction

Use sample values such as:

```text
sample.user@contoso.invalid
guest.user@partner.invalid
203.0.113.10
```

## System Boundary

TRACE does not modify:

- users
- groups
- passwords
- licenses
- devices
- Conditional Access policies
- tenant settings
- DNS records
- firewall rules
- file or share permissions
- application roles
- external user objects

TRACE structures evidence and produces support-oriented output. Any real change remains outside TRACE and must follow the normal approval path for the environment.

## Analysis Boundary

TRACE uses deterministic rules and guided forms. It can identify a likely evidence pattern, but it should not overclaim certainty.

A TRACE finding means:

```text
The supplied evidence matches this support pattern.
```

It does not automatically mean:

```text
This is the confirmed root cause.
```

When evidence is incomplete, TRACE should say what is missing.

## Guided Form Boundary

Guided forms are designed to help the technician collect evidence consistently.

They do not replace the source systems. For example:

- Entra sign-in details remain the source for sign-in evidence
- resource owners remain the source for expected access confirmation
- licensing administration remains the source for license assignment evidence
- tenant policy owners remain the source for partner or guest policy evidence

## Report Boundary

TRACE reports are support notes, not official audit reports.

They are useful for:

- ticket summaries
- escalation notes
- evidence tables
- safe next checks
- interview or portfolio demonstrations

They should not be presented as formal compliance evidence unless reviewed and approved by the appropriate owner.

## Portfolio Boundary

TRACE is a portfolio and learning project. It demonstrates:

- evidence handling
- IAM support reasoning
- safe operational thinking
- API and UI implementation
- local reporting
- test and audit discipline

It should not be described as a live tenant monitoring platform, IAM governance product, SIEM, EDR, or automated remediation system.
