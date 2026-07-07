from typing import Any, Dict, List, Optional

from .models import CollectorResult


Finding = Dict[str, Any]


EVIDENCE_CONTRACT_VERSION = "TRACE_FINDING_EVIDENCE_V1"
DEFAULT_SOURCE_MODULE = "m365-access-path-analyzer"


def _finding(
    *,
    rule_id: str,
    title: str,
    severity: str,
    confidence: str,
    likely_cause: str,
    evidence: List[str],
    next_steps: List[str],
    what_not_to_change_yet: List[str],
    limitations: List[str],
    evidence_missing: Optional[List[str]] = None,
    source_module: str = DEFAULT_SOURCE_MODULE,
) -> Finding:
    """Build a stable TRACE finding while preserving the older UI/report aliases.

    Phase 2 hardens every finding around an explicit evidence contract.
    The legacy keys (rule_id, evidence, next_steps) intentionally remain so
    the current frontend and reports keep working while newer modules adopt
    finding_id, evidence_used, evidence_missing, safe_next_steps and
    source_module.
    """

    missing = evidence_missing or limitations

    return {
        "finding_id": rule_id,
        "rule_id": rule_id,
        "title": title,
        "severity": severity,
        "confidence": confidence,
        "likely_cause": likely_cause,
        "evidence_used": evidence,
        "evidence_missing": missing,
        "source_module": source_module,
        "safe_next_steps": next_steps,
        "evidence": evidence,
        "next_steps": next_steps,
        "what_not_to_change_yet": what_not_to_change_yet,
        "limitations": limitations,
    }


def _has_recent_ca_failure(result: CollectorResult) -> bool:
    return any(
        event.conditionalAccessStatus == "failure"
        for event in result.signin_logs.recent_events
    )


def _has_recent_signin_failure(result: CollectorResult) -> bool:
    return any(event.status == "failure" for event in result.signin_logs.recent_events)


def _has_failed_compliant_device_policy(result: CollectorResult) -> bool:
    return any(
        policy.result == "failure" and "compliantDevice" in policy.grantControls
        for policy in result.conditional_access.policies
    )


def _has_failed_mfa_policy(result: CollectorResult) -> bool:
    mfa_controls = {"mfa", "multifactorauthentication"}
    return any(
        policy.result == "failure"
        and any(control.lower() in mfa_controls for control in policy.grantControls)
        for policy in result.conditional_access.policies
    )


def _has_mfa_failure_reason(result: CollectorResult) -> bool:
    return any(
        event.status == "failure"
        and event.failureReason is not None
        and "mfa" in event.failureReason.lower()
        for event in result.signin_logs.recent_events
    )



def _is_guest_b2b_user(result: CollectorResult) -> bool:
    return result.identity.user_type.lower() == "guest"


def _has_guest_or_external_failure_reason(result: CollectorResult) -> bool:
    keywords = ("guest", "external", "b2b", "collaboration")
    return any(
        event.status == "failure"
        and event.failureReason is not None
        and any(keyword in event.failureReason.lower() for keyword in keywords)
        for event in result.signin_logs.recent_events
    )


def _has_failed_guest_or_external_policy(result: CollectorResult) -> bool:
    keywords = ("guest", "external", "b2b")
    return any(
        policy.result == "failure"
        and (
            any(keyword in policy.displayName.lower() for keyword in keywords)
            or any(
                keyword in control.lower()
                for control in policy.grantControls
                for keyword in keywords
            )
        )
        for policy in result.conditional_access.policies
    )


def _device_compliance_is_blocking(result: CollectorResult) -> bool:
    return result.device.compliance_state in ("nonCompliant", "unknown")


def _build_findings(result: CollectorResult) -> List[Finding]:
    findings: List[Finding] = []

    if (
        result.identity.user_exists
        and result.identity.account_enabled
        and _is_guest_b2b_user(result)
        and result.signin_logs.available
        and _has_recent_signin_failure(result)
        and (
            _has_guest_or_external_failure_reason(result)
            or _has_failed_guest_or_external_policy(result)
        )
    ):
        findings.append(
            _finding(
                rule_id="GUEST_B2B_ACCESS_FAILURE",
                title="Guest/B2B user access failed",
                severity="high",
                confidence="medium",
                likely_cause=(
                    "The affected identity is a Guest/B2B user and recent access evidence indicates "
                    "the external user path was blocked by policy, collaboration configuration, or resource assignment."
                ),
                evidence=[
                    "identity.user_exists is true.",
                    "identity.account_enabled is true.",
                    "identity.user_type is Guest.",
                    "signin_logs.available is true.",
                    "A recent sign-in failed with a guest/external-user related failure reason or policy.",
                    f"device.compliance_state is {result.device.compliance_state}.",
                ],
                next_steps=[
                    "Confirm the guest invitation was redeemed and the external account is the expected identity.",
                    "Check whether the guest user is assigned to the target app, site, team, or access package.",
                    "Review external collaboration and cross-tenant access settings before changing the user.",
                    "Review the specific Conditional Access policy result for guest or external users.",
                ],
                what_not_to_change_yet=[
                    "Do not convert the guest to a member account just to bypass an access problem.",
                    "Do not disable guest Conditional Access policies globally.",
                    "Do not add the guest to broad groups until the resource owner confirms the access requirement.",
                ],
                limitations=[
                    "Sample-mode evidence does not include invitation redemption state.",
                    "Sample-mode evidence does not include full cross-tenant access settings.",
                    "Sample-mode evidence does not include resource-level assignment details.",
                ],
            )
        )

    if result.identity.user_exists and not result.identity.account_enabled:
        findings.append(
            _finding(
                rule_id="USER_ACCOUNT_DISABLED",
                title="User account is disabled",
                severity="high",
                confidence="high",
                likely_cause="The user cannot access Microsoft 365 because the account is disabled.",
                evidence=[
                    "The user object exists.",
                    "identity.account_enabled is false.",
                ],
                next_steps=[
                    "Confirm whether the account was intentionally disabled.",
                    "Review recent identity administration changes.",
                    "If access is expected, follow normal account re-enable approval procedures.",
                ],
                what_not_to_change_yet=[
                    "Do not change Conditional Access policies before confirming account status.",
                    "Do not change licensing before confirming whether the account should be enabled.",
                ],
                limitations=[
                    "Sample-mode evidence does not include the administrative reason the account was disabled.",
                ],
            )
        )

    if (
        result.identity.user_exists
        and result.identity.account_enabled
        and not result.licenses.has_relevant_license
    ):
        findings.append(
            _finding(
                rule_id="MISSING_RELEVANT_LICENSE",
                title="Relevant service license is missing",
                severity="high",
                confidence="high",
                likely_cause="The user appears enabled but lacks a relevant license for the affected service.",
                evidence=[
                    "The user object exists.",
                    "identity.account_enabled is true.",
                    "licenses.has_relevant_license is false.",
                ],
                next_steps=[
                    "Verify the required service plan for the affected Microsoft 365 workload.",
                    "Check group-based licensing membership and license assignment errors.",
                    "Assign the appropriate license through the normal licensing process if approved.",
                ],
                what_not_to_change_yet=[
                    "Do not change Conditional Access policies for a likely licensing issue.",
                    "Do not reset authentication methods before checking license assignment.",
                ],
                limitations=[
                    "Sample-mode evidence does not include detailed service plan provisioning status.",
                ],
            )
        )

    if (
        result.signin_logs.available
        and _has_recent_ca_failure(result)
        and not result.conditional_access.details_available
    ):
        findings.append(
            _finding(
                rule_id="CONDITIONAL_ACCESS_DETAILS_MISSING",
                title="Conditional Access blocked sign-in but policy details are missing",
                severity="medium",
                confidence="medium",
                likely_cause=(
                    "A recent sign-in failed Conditional Access evaluation, but applied policy details "
                    "were not available in the collected evidence."
                ),
                evidence=[
                    "signin_logs.available is true.",
                    "At least one recent sign-in has conditionalAccessStatus failure.",
                    "conditional_access.details_available is false.",
                ],
                next_steps=[
                    "Confirm the operator has permission to view Conditional Access policy details.",
                    "Review the failed sign-in directly in Entra ID sign-in logs.",
                    "Collect Conditional Access policy details before changing access controls.",
                ],
                what_not_to_change_yet=[
                    "Do not disable Conditional Access globally.",
                    "Do not exclude the user from policies before identifying the specific policy.",
                ],
                limitations=[
                    "Policy name and grant controls were not available, so confidence is reduced.",
                ],
            )
        )

    if (
        result.identity.user_exists
        and result.identity.account_enabled
        and result.licenses.has_relevant_license
        and result.signin_logs.available
        and _has_recent_signin_failure(result)
        and _has_mfa_failure_reason(result)
        and result.conditional_access.details_available
        and _has_failed_mfa_policy(result)
    ):
        findings.append(
            _finding(
                rule_id="MFA_REQUIREMENT_NOT_SATISFIED",
                title="MFA requirement was not satisfied",
                severity="high",
                confidence="high",
                likely_cause=(
                    "The user exists, the account is enabled, licensing is present, and a failed "
                    "Conditional Access policy required MFA that was not completed or satisfied."
                ),
                evidence=[
                    "identity.user_exists is true.",
                    "identity.account_enabled is true.",
                    "licenses.has_relevant_license is true.",
                    "A recent sign-in failed with an MFA-related failure reason.",
                    "conditional_access.details_available is true.",
                    "At least one failed policy includes an MFA-related grant control.",
                    f"device.compliance_state is {result.device.compliance_state}.",
                ],
                next_steps=[
                    "Confirm the user can complete MFA.",
                    "Check registered authentication methods.",
                    "Review sign-in logs and Conditional Access policy result.",
                    "Retest using a known working MFA method.",
                ],
                what_not_to_change_yet=[
                    "Do not disable MFA globally.",
                    "Do not exclude the user from Conditional Access until policy scope and sign-in evidence are reviewed.",
                ],
                limitations=[
                    "Sample-mode evidence does not include live authentication method registration details.",
                ],
            )
        )

    if (
        result.signin_logs.available
        and _has_recent_signin_failure(result)
        and result.conditional_access.details_available
        and _has_failed_compliant_device_policy(result)
        and _device_compliance_is_blocking(result)
    ):
        findings.append(
            _finding(
                rule_id="CA_DEVICE_COMPLIANCE_BLOCK",
                title="Conditional Access requires a compliant device",
                severity="high",
                confidence="high",
                likely_cause=(
                    "A failed Conditional Access policy required a compliant device, and the device "
                    "evidence indicates the device is non-compliant or unknown."
                ),
                evidence=[
                    "signin_logs.available is true.",
                    "A recent sign-in failed.",
                    "conditional_access.details_available is true.",
                    "At least one failed policy includes the compliantDevice grant control.",
                    f"device.compliance_state is {result.device.compliance_state}.",
                ],
                next_steps=[
                    "Check the device compliance policy state in Intune.",
                    "Force a device sync and review recent check-in status.",
                    "Retest from a known-compliant device.",
                ],
                what_not_to_change_yet=[
                    "Do not disable Conditional Access globally.",
                    "Do not remove the compliant device requirement until device evidence is reviewed.",
                ],
                limitations=[
                    "Sample-mode evidence does not include detailed Intune compliance policy failure reasons.",
                ],
            )
        )

    if not result.signin_logs.available or not result.signin_logs.recent_events:
        findings.append(
            _finding(
                rule_id="NO_RECENT_SIGNIN_EVIDENCE",
                title="No recent sign-in evidence is available",
                severity="medium",
                confidence="medium",
                likely_cause=(
                    "There is not enough recent sign-in evidence to confirm whether identity, "
                    "licensing, Conditional Access, or device state caused the access issue."
                ),
                evidence=[
                    f"signin_logs.available is {result.signin_logs.available}.",
                    f"Recent sign-in event count is {len(result.signin_logs.recent_events)}.",
                ],
                next_steps=[
                    "Confirm the user has attempted access during the sign-in log retention window.",
                    "Retest the affected service and collect fresh sign-in evidence.",
                    "Check whether sign-in log permissions or tenant licensing limit evidence collection.",
                ],
                what_not_to_change_yet=[
                    "Do not change policies or licenses based only on missing sign-in evidence.",
                ],
                limitations=[
                    "The absence of recent sign-in events prevents a confident access-path diagnosis.",
                ],
            )
        )

    return findings


def analyze_collector_result(result: CollectorResult) -> Dict[str, Any]:
    findings = _build_findings(result)
    primary_finding: Optional[Finding] = findings[0] if findings else None
    limitations = sorted({item for finding in findings for item in finding["limitations"]})
    source_modules = sorted({finding["source_module"] for finding in findings})

    if primary_finding:
        summary = primary_finding["likely_cause"]
        confidence = primary_finding["confidence"]
        status = "findings"
    else:
        summary = "No blocking evidence was identified in the collected sample data."
        confidence = "medium"
        status = "no_blocking_evidence"

    return {
        "status": status,
        "evidence_contract_version": EVIDENCE_CONTRACT_VERSION,
        "primary_finding": primary_finding,
        "findings": findings,
        "summary": summary,
        "confidence": confidence,
        "limitations": limitations,
        "source_modules": source_modules,
    }
