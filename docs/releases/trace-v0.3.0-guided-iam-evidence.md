# TRACE v0.3.0 - Guided IAM Evidence

Target tag:

```text
trace-v0.3.0-guided-iam-evidence
```

## Release Summary

TRACE v0.3.0 is the guided IAM evidence release.

This release positions TRACE as a local-first, read-only IAM/access evidence workbench for structuring redacted support evidence into findings, missing evidence, safe next checks, non-actions, and support-ready reports.

The release is intended as a finished portfolio artifact for the IAM Engineer / Identity Support / Access Operations path.

## Main Workflows

TRACE v0.3.0 includes the following Access Evidence workflows:

- Generic access log text
- Entra sign-in CSV
- Conditional Access / MFA guided form
- License / Service Plan guided form
- Guest / B2B guided form
- Resource Assignment guided form

## Analyzer Coverage

The release includes deterministic support-pattern analysis for:

- Conditional Access-style block evidence
- MFA challenge or failure evidence
- license or service-plan missing/disabled evidence
- Guest / B2B access blocked or incomplete evidence
- disabled account access attempt evidence
- successful authentication followed by resource access denial
- resource assignment or group membership missing/unconfirmed evidence
- unsupported or insufficient evidence

## Reporting

Each access-evidence run can produce:

- run ID
- parse status
- normalized events
- detected patterns
- primary finding
- confidence
- evidence used
- evidence missing
- safe next steps
- what not to change yet
- limitations
- Markdown report
- local run-history entry

## UI Proof

The final visual audit for this release validates:

- generic access evidence analysis
- Entra CSV analysis
- Conditional Access / MFA guided form and analysis
- License / Service Plan guided form and analysis
- Guest / B2B guided form and analysis
- Resource Assignment guided form and analysis
- analyzer-input copy action
- History navigation
- Overview navigation

Final proof result:

```text
fail_count: 0
warn_count: 0
visual audit status: completed
screenshots: 15
page errors: 0
failed requests: 0
bad HTTP responses: 0
backend cleanup: PASS
frontend cleanup: PASS
```

Final proof ZIP reviewed:

```text
TRACE_UI_VISUAL_AUDIT_20260710_015031.zip
```

## Documentation Included

- `README.md`
- `docs/architecture.md`
- `docs/demo-scenarios.md`
- `docs/safety-boundaries.md`
- `docs/log-analysis-roadmap.md`
- `docs/finished-roadmap.md`
- `docs/iam-scenario-pack-v2.md`

## Safety Boundary

TRACE v0.3.0 remains local-first and read-only.

It is for redacted evidence, sample evidence, support-note generation, and portfolio demonstration. It is not a production change tool, live tenant monitor, SIEM, IAM governance platform, or automatic remediation system.

## Known Limitations

- No default production tenant connection.
- No Microsoft Graph collection in the release path.
- No automatic remediation.
- No credential or token storage.
- No formal compliance reporting.
- Evidence quality depends on what the operator provides.

## Backlog After Release

Future ideas should be treated as backlog, not blockers:

- Enterprise app assignment / app role guided form
- Shared mailbox / distribution list guided form
- PIM / privileged role evidence workflow
- dynamic group rule evidence workflow
- optional read-only collector expansion
- improved screenshot packaging for public README visuals

## Release Decision

Release as:

```text
TRACE v0.3.0 - Guided IAM Evidence Workbench
```

This is the first complete portfolio release for TRACE as an IAM Engineer flagship.
