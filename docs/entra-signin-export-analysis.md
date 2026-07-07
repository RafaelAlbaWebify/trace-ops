# TRACE Entra Sign-in Export Analysis

## Purpose

This is the v0.5 step for TRACE.

It extends the Access Evidence Analyzer so exported Entra sign-in CSV evidence can be analyzed locally without live tenant access.

## Source Type

```text
entra_signin_csv
```

## Operator Flow

```text
export sign-in rows
redact sensitive values
paste the CSV content into TRACE
run /api/logs/analyze
review normalized events, findings, missing evidence, safe next steps, and non-actions
```

## Current Field Mapping

TRACE maps common export columns into normalized access events:

```text
createdDateTime
userPrincipalName
appDisplayName
resourceDisplayName
clientAppUsed
conditionalAccessStatus
authenticationRequirement
status.errorCode
status.failureReason
```

## First Patterns

```text
LOG_PATTERN_CONDITIONAL_ACCESS_BLOCK
LOG_PATTERN_MFA_CHALLENGE_OR_FAILURE
LOG_PATTERN_LEGACY_CLIENT_OR_BASIC_AUTH
LOG_PATTERN_NO_USABLE_EVENTS
```

## Boundary

This feature analyzes exported text only. It does not connect to Microsoft Graph, does not store tokens, and does not modify tenant configuration.
