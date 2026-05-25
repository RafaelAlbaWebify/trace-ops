# Test Plan

## Testing principles

- Tests must use synthetic sample data by default.
- Tests must not require a real Microsoft 365 tenant.
- Tests must verify missing-evidence behavior.
- Tests must verify that no remediation behavior exists in v1.

## PowerShell tests

Use Pester to validate:

- collector scripts return valid JSON
- required top-level fields exist
- sample mode works without Microsoft Graph connection
- errors are structured and do not expose secrets

## Backend tests

Use Pytest to validate:

- scan request validation
- collector subprocess success
- collector subprocess failure
- invalid JSON handling
- missing evidence handling
- each deterministic rule
- SQLite scan history write/read
- HTML report generation

## Frontend tests

Use Vitest to validate:

- scan form renders
- affected service selector works
- finding cards render severity/confidence/evidence
- limitations section renders when evidence is missing
- export buttons are shown when result exists

## Initial sample scenarios

1. account-disabled.json
2. missing-license.json
3. ca-details-missing.json
4. ca-device-noncompliant.json
5. mfa-requirement-not-satisfied.json
6. no-recent-signin-evidence.json
7. successful-access-baseline.json
