# TRACE — Historical Repository

> [!IMPORTANT]
> **This repository is no longer the maintained TRACE project.**
>
> It preserves the earlier TRACE IT Operations and IAM evidence prototype that was presented publicly during the project's development. The current maintained application is:
>
> **[RafaelAlbaWebify/trace-iam-evidence](https://github.com/RafaelAlbaWebify/trace-iam-evidence)**
>
> The current repository contains the completed local-first IAM evidence investigation workbench, including persisted investigations, evidence provenance, immutable analysis runs, structured findings, timeline, run comparison, reports, the refurbished operational interface, and current automated verification.
>
> This repository is retained only as development history. Do not use it as the current implementation or documentation source.

---

## Historical project description

> Troubleshooting Reports for Access Control Evidence

TRACE began as a **local-first IAM / access evidence workbench** for turning redacted access-ticket evidence into structured findings, missing evidence, safe next checks, explicit non-actions, and support-ready reports.

It was developed as a portfolio project for the **IAM Engineer / Identity Support / Access Operations** path.

## Why This Existed

IAM support tickets often arrive as incomplete fragments: a user message, a sign-in result, a policy note, a license clue, or an access-denied screenshot. This earlier TRACE version explored how to turn that evidence into a structured operator workflow.

```text
redacted evidence
  -> guided intake or parser
  -> normalized access evidence
  -> deterministic finding
  -> evidence used + evidence missing
  -> safe next checks + non-actions
  -> Markdown / JSON support report
```

TRACE did not claim root cause when evidence was incomplete. It showed what was known, what was missing, and what should be checked next.

## Historical Visible Product Scope

This repository was intentionally scoped to IAM/access evidence.

Visible release modules:

```text
Overview
Access evidence
History
```

Non-IAM infrastructure modules such as DNS evidence were moved outside TRACE. Placeholder modules from earlier shell experiments were not part of the visible TRACE product.

## Historical Screenshots

The screenshots below come from the earlier local visual-audit proof package.

![TRACE UI screenshot gallery](docs/screenshots/readme/trace-ui-gallery.svg)

## Historical Workflows

| Workflow | Purpose |
|---|---|
| Generic access log text | Paste redacted access-ticket or log evidence |
| Entra sign-in CSV | Analyze exported sign-in evidence |
| Conditional Access / MFA guided form | Structure policy, MFA, client app, and device evidence |
| License / Service Plan guided form | Separate license/service-plan symptoms from general access problems |
| Guest / B2B guided form | Structure external-user, invitation, tenant-policy, and assignment evidence |
| Resource Assignment guided form | Separate successful authentication from resource authorization failure |

## Historical Analyzer Outcomes

This repository explored classifications for:

- `LOG_PATTERN_CONDITIONAL_ACCESS_BLOCK`
- `LOG_PATTERN_MFA_CHALLENGE_OR_FAILURE`
- `LOG_PATTERN_LICENSE_OR_SERVICE_PLAN_MISSING`
- `LOG_PATTERN_GUEST_B2B_ACCESS_BLOCKED`
- `LOG_PATTERN_DISABLED_ACCOUNT_ATTEMPT`
- `LOG_PATTERN_AUTH_SUCCESS_ACCESS_DENIED`
- resource assignment or group membership missing/unconfirmed evidence
- no usable evidence / unsupported source type

Each run returned a finding, confidence level, evidence used, evidence missing, safe next steps, non-actions, limitations, local history entry, and Markdown report.

## What This Historical Version Was Not

It was not a SIEM, live tenant monitor, production automation platform, governance product, infrastructure operations console, DNS audit tool, or remediation tool.

It was a local read-only IAM evidence structuring prototype for support practice, portfolio proof, and controlled demos using redacted or sample data.

For full boundaries, see [`docs/safety-boundaries.md`](docs/safety-boundaries.md).

## Historical Architecture

```text
trace-ops/
|-- backend/     FastAPI API, IAM analyzers, parsers, local run store, reports
|-- collector/   read-only collector samples and contract tests
|-- frontend/    React, TypeScript, Vite, TRACE operator shell
|-- samples/     Public-safe sample evidence
|-- scripts/     local audit and visual UI audit automation
`-- docs/        architecture, safety boundaries, scenarios, roadmap, release notes
```

## Historical Documentation

- [`docs/architecture.md`](docs/architecture.md)
- [`docs/demo-scenarios.md`](docs/demo-scenarios.md)
- [`docs/safety-boundaries.md`](docs/safety-boundaries.md)
- [`docs/log-analysis-roadmap.md`](docs/log-analysis-roadmap.md)
- [`docs/finished-roadmap.md`](docs/finished-roadmap.md)
- [`docs/iam-scenario-pack-v2.md`](docs/iam-scenario-pack-v2.md)

## Superseded Status

The active project and all current setup, release, workflow, safety, and validation information now live in:

**https://github.com/RafaelAlbaWebify/trace-iam-evidence**
