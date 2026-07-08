# TRACE v1.0.0 - Access Evidence Analyzer

## Release Identity

Tag target:

```text
trace-v1.0.0-access-evidence-analyzer
```

Positioning:

```text
A local-first IAM/access evidence analyzer for support engineers.
```

TRACE v1.0 is a professional portfolio release focused on evidence-based IAM and access troubleshooting. It is not a SIEM, SOC platform, EDR, vulnerability scanner, live tenant automation platform, or remediation tool.

## Final v1.0 Scope

TRACE v1.0 supports the Access Evidence Analyzer workflow:

```text
redacted operator evidence
  -> source-type aware analyzer
  -> normalized access events
  -> deterministic pattern rules
  -> primary finding and confidence
  -> evidence used and evidence missing
  -> safe next checks and explicit non-actions
  -> local JSON and Markdown report history
```

## Supported Source Types

```text
generic_access_log_text
entra_signin_csv
resource_assignment_json
```

## Supported Diagnostic Categories

TRACE v1.0 can structure evidence around:

```text
Conditional Access-style blocking evidence
MFA challenge or failure evidence
disabled-account attempt evidence
authentication success followed by resource access denial
exported Entra sign-in CSV evidence
legacy client values in sign-in evidence
resource assignment or group membership missing/unconfirmed evidence
missing or unsupported evidence
```

## Main Operator Workflow

1. Open the Access Evidence workspace.
2. Select the evidence source type.
3. Enter affected user and affected service/resource.
4. Paste redacted evidence.
5. Run the analyzer.
6. Review normalized events, detected patterns, primary finding, confidence, evidence used, evidence missing, safe next checks, non-actions, and limitations.
7. Retrieve the Markdown report or review local history.

## v1.0 Backend Endpoints

```text
GET  /api/health
GET  /api/modules
POST /api/logs/analyze
GET  /api/logs/history
GET  /api/logs/history/{run_id}
GET  /api/logs/reports/{run_id}.md
```

Adjacent legacy endpoints remain available, but v1.0 is judged primarily on the Access Evidence Analyzer path.

## Validation Gates

Release verification is complete only when CI passes:

```text
Backend tests
Frontend typecheck
Frontend production build
PowerShell collector parse check
Collector sample contract
```

Manual smoke path is documented in:

```text
docs/v1-release-checklist.md
```

## Safety Boundaries

TRACE v1.0 does not:

```text
change AD or Entra users, groups, passwords, licenses, devices, policies or memberships
change DNS, firewall, NTFS, SMB or application settings
store credentials, tokens, cookies or secrets
connect to Microsoft Graph by default
upload evidence externally
impersonate end users
perform offensive security testing
perform automatic remediation
claim confirmed root cause when evidence is incomplete
```

## Release Stop Condition

After this release record is merged and CI is green, TRACE should be tagged as:

```text
trace-v1.0.0-access-evidence-analyzer
```

Do not add further features before v1.0 unless they fix a release blocker.

## Recommended Next Work After v1.0

Post-v1.0 work should be treated as a new cycle, not release-blocking work:

```text
optional PDF report export
optional richer timeline UI
optional additional parsers
optional read-only Graph evidence path
optional stronger UI tests
```

These should only be added if they strengthen the core IAM/access evidence analyzer without turning TRACE into a SIEM or live remediation platform.
