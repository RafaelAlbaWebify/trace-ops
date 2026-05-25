# Phase 5B: User Access Health Scanner Plan

## A. Objective

Add a future proactive scanning mode for TRACE: User Access Health Scanner.

The scanner should help IT and support teams identify Microsoft 365 access-readiness risks before they become tickets. It must remain read-only and diagnostic, using evidence to group likely issues and point operators toward safe next checks.

Phase 5B is not a remediation feature.

## B. Relationship To Phase 5A

Phase 5A is single-user operational Microsoft Graph diagnostics.

Phase 5B is scoped multi-user health scanning using the same evidence model and analyzer logic. It should not start until the single-user operational collector is working, tested, and able to normalize live read-only evidence into the TRACE contract.

Phase 5B should reuse:

- operational Graph readiness checks
- read-only collector patterns
- normalized evidence contract
- analyzer rules
- controlled error handling
- local reporting and history patterns

## C. Supported Input Sources

Supported input sources should be introduced in this priority order:

1. CSV list of users.
2. Entra ID group.
3. Filtered cloud users, for example by department, company, or license, later.
4. On-prem AD OU, later and only for hybrid/on-prem environments.

Microsoft 365 / Entra ID does not use classic Active Directory OUs. For the first cloud-first version, CSV input is the safest and most explicit scope. Entra ID group support can follow after the per-user operational scan path is stable.

## D. First Implementation Target

The first Phase 5B implementation target is CSV-based multi-user scanning.

Input CSV columns:

- `user_principal_name`
- `affected_service`, optional

Output should include:

- per-user diagnostic summary
- grouped issue categories
- health status counts
- report links
- exportable JSON/HTML report later

CSV-first scanning gives administrators explicit control over scan scope and avoids accidental tenant-wide collection.

## E. Future Entra ID Group Scan

Future Entra ID group scan should:

- accept group ID or group display name
- resolve group members read-only
- scan members using the same per-user diagnostic logic
- clearly report users that could not be resolved or scanned

Nested groups should be handled later, not in the first Entra group implementation.

## F. Future On-Prem AD OU Scan

On-prem AD OU scanning is later and hybrid/on-prem only.

It would require:

- domain access
- appropriate read permissions
- read-only Active Directory queries
- clear labeling that it is not an Entra ID concept

An AD OU scanner must not modify AD users, groups, attributes, passwords, or membership.

## G. Issue Categories To Detect

The scanner should group users into support-ready issue categories:

- Account disabled.
- Missing relevant license.
- Repeated sign-in failures.
- MFA requirement not satisfied.
- Conditional Access failure.
- Device compliance block from sign-in evidence.
- No recent sign-in evidence.
- Conditional Access details unavailable.
- User not found.
- Insufficient evidence.

Each per-user finding should continue to include TRACE finding fields: rule ID, severity, confidence, likely cause, evidence, next steps, what not to change yet, and limitations.

## H. Visual Mapping Concept

Future UI/reporting can show a visual access map per user:

```text
user -> license state -> sign-in evidence -> Conditional Access result -> device evidence -> finding -> severity -> next step
```

Each row or node should make the access path easy to scan without hiding uncertainty.

Group health summary:

- Healthy
- Warning
- Critical
- Insufficient evidence

The summary should help support teams prioritize follow-up while avoiding claims that TRACE cannot prove from available evidence.

## I. Safety Boundaries

Phase 5B must remain:

- read-only
- scoped by explicit input
- diagnostic

Phase 5B must not include:

- remediation
- MFA reset
- password reset
- license assignment or removal
- Conditional Access edits
- user exclusions
- device actions
- policy changes
- tenant-wide scan by default
- attack simulation

The scanner must require an explicit input scope such as a CSV file or selected group.

## J. Privacy And Data Handling

Phase 5B output is local-only.

Rules:

- Do not store tokens.
- Warn before saving live tenant evidence.
- Redact exports before sharing.
- Do not commit live history, reports, screenshots, or CSV inputs.
- Keep local SQLite history and generated tenant data out of Git.
- Make exported reports clearly user-controlled.

Because multi-user scans can contain more sensitive tenant data than single-user diagnostics, reports should minimize stored details and summarize where possible.

## K. Testing Strategy

Automated tests must not require a real tenant.

Testing approach:

- Mock Graph responses.
- Use synthetic CSV fixtures.
- Keep sample-mode tests unchanged.
- Test invalid CSV rows.
- Test per-user controlled errors.
- Test grouped issue summaries.
- Test no-sign-in-log and insufficient-evidence cases.
- Add an optional manual checklist for authorized tenant validation later.

## L. Implementation Order

Recommended implementation order:

1. Finish Phase 5A single-user Graph collector.
2. Add CSV multi-user scan using mocked Graph fixtures.
3. Add grouped summary report.
4. Add frontend health summary view.
5. Add Entra ID group input.
6. Add visual access map.
7. Consider on-prem AD OU scanner later.

Do not begin with group or OU scanning. Prove CSV scope, per-user diagnostics, and grouped summaries first.
