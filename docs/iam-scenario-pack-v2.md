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

---

## Scenario: Licensed User But Service Plan Disabled

Sample file:

```text
samples/service-plan-disabled.json
```

Analyzer rule:

```text
SERVICE_PLAN_DISABLED_OR_NOT_PROVISIONED
```

## What the scenario demonstrates

This scenario models another common IAM/Application Support case:

```text
The user exists and is enabled.
The user has a relevant Microsoft 365 license SKU.
The affected workload still fails because required service plans are disabled, pending provisioning, or in error.
TRACE separates a missing-license problem from a service-plan provisioning problem.
```

## Evidence used

- `identity.user_exists`
- `identity.account_enabled`
- `licenses.has_relevant_license`
- `licenses.assigned_skus`
- `licenses.service_plans`
- recent app failure context

## Safe next steps

- Review assigned service plans and provisioning state for the affected workload.
- Check whether group-based licensing disabled or failed the required service plan.
- Confirm whether the service plan should be enabled through the normal licensing process.
- Retest after the service plan reaches a successful provisioning state.

## What not to change yet

- Do not change Conditional Access policies for a likely service-plan issue.
- Do not assign extra licenses before checking existing SKU and service-plan state.
- Do not remove and re-add licenses before confirming the licensing source and approval path.

## Interview explanation

A good short explanation:

> I added the service-plan-disabled scenario because in Microsoft 365 access support, "the user has a license" is not always enough. A SKU can be assigned while a workload-specific service plan is disabled, pending, or failed. TRACE now distinguishes missing license from service-plan provisioning, which is closer to real IAM and application-access troubleshooting.

