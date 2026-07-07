# TRACE Access Evidence Analyzer

## Purpose

The Access Evidence Analyzer is the v0.4 backend foundation for TRACE.

It moves TRACE from sample-only IAM diagnostics toward practical daily-job evidence analysis.

```text
pasted redacted access evidence
  -> parser
  -> normalized access events
  -> deterministic pattern rules
  -> finding, confidence, evidence used, evidence missing
  -> safe next steps and non-actions
  -> Markdown report
```

## Current Scope

The first implementation supports:

```text
generic_access_log_text
```

It is intentionally backend-first and local-first.

## Endpoint

```text
POST /api/logs/analyze
```

## First Pattern Rules

```text
LOG_PATTERN_CONDITIONAL_ACCESS_BLOCK
LOG_PATTERN_MFA_CHALLENGE_OR_FAILURE
LOG_PATTERN_DISABLED_ACCOUNT_ATTEMPT
LOG_PATTERN_AUTH_SUCCESS_ACCESS_DENIED
LOG_PATTERN_NO_USABLE_EVENTS
LOG_PATTERN_UNSUPPORTED_SOURCE_TYPE
```

## Operator Guidance

Operators should redact sensitive values before pasting evidence.

TRACE should be used to structure evidence and next checks, not to bypass approval processes or make direct production changes.

## Next Improvement

The next likely improvement is an Entra sign-in CSV parser that maps exported sign-in rows into the same normalized access event model.
