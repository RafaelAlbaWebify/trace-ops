# TRACE Portfolio Positioning

## One-line description

TRACE is a local-first, read-only IT Operations diagnostic toolkit that turns identity, endpoint, DNS, network, and file-access evidence into support-ready findings.

## Short portfolio summary

TRACE helps support engineers diagnose access and infrastructure issues without guessing or making unsafe changes. It collects read-only evidence, validates it, applies deterministic diagnostic rules, and returns a clear finding with confidence, limitations, safe next steps, and what not to change yet.

## Strongest validated scenario

A user cannot access a department file share.

TRACE proves:

- DNS resolves the file server.
- SMB TCP/445 is reachable.
- The AD user exists and is enabled.
- The required access group exists.
- The blocked user is not a member of the required group.
- The allowed user is a member of the group.
- The blocked user receives access denied.
- No remediation or configuration changes were performed.

## Interview explanation

I built TRACE as an operational troubleshooting tool, not as a scanner or remediation bot. The design principle is evidence over assumptions. For example, in the file-share scenario, TRACE does not simply say "permissions problem." It proves DNS and SMB are healthy, checks the user and group in AD, compares membership, records the observed access-denied condition, and recommends the safe path: confirm business approval before changing group membership.

## Why it is realistic

The FactoryOps lab uses a real local Windows domain with a domain controller, DNS, pfSense routing, a management workstation, a workstation target, and a file server. The Phase 12 file-share diagnostic was validated through both the direct PowerShell collector and the FastAPI backend API.

## What this demonstrates

- Windows Server / Active Directory understanding.
- DNS and SMB troubleshooting.
- PowerShell collector design.
- FastAPI API design.
- JSON evidence contracts.
- Read-only safety boundaries.
- Support-ready reporting.
- Homelab validation discipline.
