# TRACE IAM Scenario Pack v2

TRACE IAM Scenario Pack v2 deepens the public sample-mode M365 Access Path Analyzer with IAM-specific access investigations.

## Scenario: Guest/B2B Access Failure

Sample file:

```text
samples/guest-b2b-access-failure.json
```

Analyzer rule:

```text
GUEST_B2B_ACCESS_FAILURE
```

## What the scenario demonstrates

This scenario models a common IAM support case:

```text
External collaborator reports they cannot access a SharePoint resource.
The guest object exists and is enabled.
A recent sign-in failed.
The failure reason and policy evidence point to guest/external-user access controls.
TRACE returns a finding, confidence, limitations, safe next steps, and explicit non-actions.
```

## Evidence used

- `identity.user_exists`
- `identity.account_enabled`
- `identity.user_type`
- recent sign-in status and failure reason
- Conditional Access policy result
- device compliance hint

## Safe next steps

- Confirm the invitation was redeemed by the expected external identity.
- Confirm the guest has resource-level assignment.
- Review external collaboration and cross-tenant access settings.
- Review the specific Conditional Access policy result.

## What not to change yet

- Do not convert the guest into a member account just to bypass the issue.
- Do not disable guest Conditional Access policies globally.
- Do not add broad group access without resource-owner approval.

## Interview explanation

A good short explanation:

> I added a guest/B2B scenario because IAM work is not only about whether a user exists. In real access cases, the user may exist and still be blocked by invitation state, resource assignment, external collaboration settings, cross-tenant policy, or Conditional Access. TRACE keeps this read-only: it shows evidence, confidence, limitations, next checks, and what not to change yet.
