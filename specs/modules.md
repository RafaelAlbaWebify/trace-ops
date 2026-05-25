# TRACE Modules

TRACE is a toolkit. The product must support future modules without being hard-coded as a single Microsoft 365 tool.

## Module 1: M365 Access Path Analyzer

Status: v1 priority

Purpose:
Diagnose Microsoft 365 access failures by correlating identity, licensing, authentication, sign-in logs, Conditional Access, and device compliance evidence.

## Candidate future modules

These are not part of v1 unless explicitly moved into scope.

### DNS Health Investigator

Purpose:
Detect stale DNS records, missing PTR records, forward/reverse mismatches, and DNS hygiene issues.

### Endpoint Readiness Checker

Purpose:
Check endpoint readiness signals such as TPM, Secure Boot, BitLocker, BIOS age, and local support history.

### SMTP Auth / Scan-to-Email Investigator

Purpose:
Troubleshoot printers, scanners, SMTP AUTH, mailbox submission, and Exchange Online mail submission issues.

### SharePoint Access Investigator

Purpose:
Diagnose guest access, sharing restrictions, permission inheritance, and collaboration blocks.

### Conditional Access Impact Viewer

Purpose:
Explain which Conditional Access policies may affect users, devices, apps, and locations.

### Mail Flow Path Analyzer

Purpose:
Trace common Microsoft 365 mail flow issues using headers, connectors, accepted domains, and DNS signals.

## Module design rule

Each module should produce findings using the common TRACE finding schema:

- rule_id
- title
- severity
- confidence
- likely_cause
- evidence
- next_steps
- what_not_to_change_yet
- limitations
