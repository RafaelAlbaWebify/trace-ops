# TRACE Demo Scenarios

This document describes the main portfolio demos for TRACE as a local IAM/access evidence workbench.

Each demo uses public-safe, redacted-style evidence. The goal is not to modify an environment. The goal is to structure the ticket, identify the likely evidence pattern, show what is still missing, and produce safe next checks.

## Scenario 1 - Conditional Access / MFA evidence

### Situation

A user reports that they cannot open a Microsoft 365 resource. The sign-in evidence shows a failed access attempt and policy-related details.

### TRACE workflow

Use the **Conditional Access / MFA guided form**.

### Evidence captured

- affected user
- affected service or resource
- timestamp or time window
- application
- resource
- client app
- sign-in status
- Conditional Access result
- authentication requirement
- error code
- device-compliance value when available
- failure reason

### Expected TRACE result

`LOG_PATTERN_CONDITIONAL_ACCESS_BLOCK`

### Safe next checks

- review the matching sign-in event
- identify the exact policy result and grant controls
- compare with a known-good sign-in if needed
- confirm whether client app or device state explains the result

### What not to change yet

- do not change broad policy settings from one incomplete ticket
- do not exclude a user before identifying the specific policy and approval path

## Scenario 2 - Resource assignment evidence

### Situation

Authentication appears successful, but the user still receives access denied when opening the target resource.

### TRACE workflow

Use the **Resource Assignment guided form**.

### Evidence captured

- sign-in result
- MFA result
- Conditional Access result
- assignment or membership state
- expected access confirmation
- observed failure text
- evidence checked by the operator

### Expected TRACE result

Resource assignment or group membership missing/unconfirmed evidence.

### Safe next checks

- confirm expected access with the resource owner or ticket
- check the actual access path: group, site, app assignment, or access package
- compare with a known-good user who has the same expected access

### What not to change yet

- do not grant broad owner/admin access as a shortcut
- do not treat successful sign-in as proof of resource authorization

## Scenario 3 - License / Service Plan evidence

### Situation

The user can authenticate, but the target service reports that licensing or a service plan may be missing.

### TRACE workflow

Use the **License / Service Plan guided form**.

### Evidence captured

- license SKU
- service plan
- direct or group-based licensing source
- license assigned / missing state
- service plan enabled / disabled state
- recent license-change uncertainty
- observed service message

### Expected TRACE result

`LOG_PATTERN_LICENSE_OR_SERVICE_PLAN_MISSING`

### Safe next checks

- confirm assigned license SKU and service-plan state
- check whether licensing is direct or group-based
- check whether a recent change is still propagating
- compare with a known-good user

### What not to change yet

- do not remove and re-add licenses before confirming source and approval path
- do not use broad access changes to work around a licensing symptom

## Scenario 4 - Guest / B2B evidence

### Situation

An external guest user cannot open a shared resource. The ticket may involve invitation state, external user object state, tenant policy, or resource assignment.

### TRACE workflow

Use the **Guest / B2B guided form**.

### Evidence captured

- partner tenant
- invitation redemption state
- external user object state
- cross-tenant access state
- tenant restrictions evidence
- guest resource assignment
- observed guest access failure

### Expected TRACE result

`LOG_PATTERN_GUEST_B2B_ACCESS_BLOCKED`

### Safe next checks

- confirm the invitation was redeemed
- confirm the external user object exists in the resource tenant
- check tenant policy evidence with the correct owner
- confirm resource assignment or group membership
- compare with a known-good guest from the same partner tenant if available

### What not to change yet

- do not convert the guest to a member as a shortcut
- do not grant broad access as a workaround
- do not assume the invitation is valid until the redemption and external-user state are checked

## Scenario 5 - Insufficient evidence

### Situation

The ticket contains a vague message such as "user cannot access app" without sign-in, policy, assignment, license, or resource evidence.

### TRACE workflow

Use **Generic access log text** or start with the most relevant guided form and mark unknown fields honestly.

### Expected TRACE result

No usable events, unsupported source type, or low-confidence evidence.

### Safe next checks

- ask for timestamp, affected user, affected service, and exact error
- collect matching sign-in evidence
- confirm whether the user can reproduce the issue
- identify which access path needs to be checked first

### What not to change yet

- do not make production access changes based only on a vague ticket
- do not claim root cause without matching evidence
