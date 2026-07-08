# TRACE v1.0 Release Checklist

## Purpose

This checklist defines what must be true before TRACE is tagged as a finished professional portfolio release.

Target tag:

```text
trace-v1.0.0-access-evidence-analyzer
```

## Product Identity

TRACE v1.0 must be positioned as:

```text
A local-first IAM/access evidence analyzer for support engineers.
```

It must not be positioned as:

```text
SIEM
SOC platform
EDR
vulnerability scanner
live tenant automation platform
automatic remediation tool
```

## Core Workflow

A v1.0 operator must be able to:

1. Open the Access Evidence workspace.
2. Choose the source type.
3. Enter affected user and service/resource context.
4. Paste redacted evidence.
5. Run the analyzer.
6. Review normalized events, detected patterns and primary finding.
7. Review confidence, evidence used and evidence missing.
8. Review safe next checks and explicit non-actions.
9. Copy or retrieve the Markdown report.
10. Review local history for previous access-evidence runs.

## Required Source Types

The v1.0 baseline must support:

```text
generic_access_log_text
entra_signin_csv
resource_assignment_json
```

## Required Diagnostic Categories

The v1.0 baseline must distinguish:

```text
authentication evidence
authorization / resource assignment evidence
Conditional Access evidence
MFA evidence
disabled account evidence
legacy client evidence
missing or unsupported evidence
```

## Required Outputs

Each access-evidence analysis must return:

```text
run_id
status
source_type
parse_status
normalized_events
detected_patterns
primary_finding
findings
summary
confidence
evidence_used
evidence_missing
safe_next_steps
what_not_to_change_yet
limitations
report_markdown
```

## Required API Endpoints

```text
POST /api/logs/analyze
GET  /api/logs/history
GET  /api/logs/history/{run_id}
GET  /api/logs/reports/{run_id}.md
GET  /api/health
GET  /api/modules
```

Legacy and adjacent diagnostics may remain available, but v1.0 should be judged primarily on the Access Evidence Analyzer path.

## Validation Gates

Before tagging v1.0:

```text
Backend pytest passes in CI
Frontend typecheck passes in CI
Frontend production build passes in CI
PowerShell collector parse check passes in CI
Collector sample contract passes in CI
README matches actual capabilities
Safety boundaries do not overclaim
No real tenant data is committed
No credentials, tokens or secrets are committed
Sample evidence remains public-safe
```

## Manual Local Smoke Path

From the repository root on Rafael's workstation:

```powershell
Set-Location -LiteralPath "C:\Users\ralba\Documents\GitHub\trace-ops"
```

Backend:

```powershell
Set-Location -LiteralPath "C:\Users\ralba\Documents\GitHub\trace-ops\backend"
python -m pytest
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Frontend:

```powershell
Set-Location -LiteralPath "C:\Users\ralba\Documents\GitHub\trace-ops\frontend"
npm test
npm run build
npm run dev
```

Browser:

```text
http://127.0.0.1:5173
```

Smoke test:

1. Open Access Evidence.
2. Analyze the default generic access-log sample.
3. Confirm result panel shows a finding.
4. Confirm backend response includes `run_id`.
5. Open `/api/logs/history`.
6. Open `/api/logs/reports/{run_id}.md`.

## Stop Conditions

Do not add more features before v1.0 unless they fix a release blocker.

After this checklist passes, the next action should be a v1.0 release candidate tag, not another major feature.
