# TRACE Read-Only Boundary

TRACE is designed as a diagnostic tool. It reports findings and safe next steps, but it does not perform remediation.

## Current protected boundaries

TRACE diagnostics must not:

- Modify AD objects.
- Modify group membership.
- Modify DNS records.
- Modify firewall rules.
- Modify network settings.
- Modify NTFS permissions.
- Modify SMB share permissions.
- Restart services.
- Run remote remediation commands.
- Store credentials or tokens.
- Impersonate an affected user.

## Why this matters

Support tools can easily become unsafe if they automatically change permissions, firewall rules, group membership, or endpoint configuration. TRACE deliberately separates diagnosis from remediation.

The intended workflow is:

```text
Collect evidence -> diagnose likely cause -> explain confidence and limitations -> recommend safe next step -> let an authorized human perform approved remediation
```

## Phase 12 boundary proof

The Phase 12 file-share diagnostic output includes a `read_only_boundary` object proving that no remediation or configuration changes were performed during the diagnostic run.
