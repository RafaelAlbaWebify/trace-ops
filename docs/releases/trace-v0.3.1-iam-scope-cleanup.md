# TRACE v0.3.1 - IAM Scope Cleanup

Target tag:

```text
trace-v0.3.1-iam-scope-cleanup
```

## Release Summary

TRACE v0.3.1 cleans up the visible product scope after the v0.3.0 guided IAM evidence release.

The purpose is to keep TRACE focused on the IAM Engineer flagship and avoid showing unfinished or non-IAM placeholder modules in the main UI.

## Scope Decision

TRACE remains:

```text
IAM -> TRACE -> IAM Engineer
```

DNS and infrastructure evidence belong to:

```text
IPPO -> OPSCORE -> DNS Audit Tool / DNS Evidence & Consistency Audit
```

## Visible TRACE Modules

After this cleanup, the visible TRACE UI focuses on:

- Overview
- Access evidence
- History

The Access Evidence workspace contains the completed guided IAM evidence workflows:

- Generic access log text
- Entra sign-in CSV
- Conditional Access / MFA guided form
- License / Service Plan guided form
- Guest / B2B guided form
- Resource Assignment guided form

## Removed From Visible Sidebar

The following earlier shell or placeholder modules are no longer visible in TRACE:

- FactoryOps Share access
- DNS lookup
- AD user access placeholder
- AD readiness placeholder
- Local readiness placeholder
- Cloud readiness placeholder
- M365 sample placeholder

Code may remain for reference or future migration, but these modules are not part of the visible TRACE release scope.

## Why This Matters

This avoids presenting unfinished modules as part of a completed product.

It also keeps the portfolio architecture coherent:

- TRACE is the IAM/access evidence workbench.
- OPSCORE is the infrastructure / production operations workbench.
- DNS Audit Tool remains aligned with OPSCORE, not TRACE.

## Release Boundary

This release is a UI/product-scope cleanup. It does not add new analyzer behavior.

The goal is clarity, honesty, and portfolio coherence.
