from typing import Any, Dict, List, Optional

from .analyzer import _finding
from .log_models import LogAnalysisResponse, LogAnalyzeRequest, LogPattern, NormalizedAccessEvent
from .log_parser import SUPPORTED_LOG_SOURCE_TYPES, parse_access_log_content

SOURCE_MODULE = "access-evidence-analyzer"


def _event_text(event: NormalizedAccessEvent) -> str:
    return " ".join([
        event.raw_message,
        event.failure_reason or "",
        event.conditional_access_status or "",
        event.mfa_result or "",
    ]).lower()


def _has(event: NormalizedAccessEvent, *keywords: str) -> bool:
    text = _event_text(event)
    return any(keyword.lower() in text for keyword in keywords)


def _pattern(pattern_id: str, title: str, severity: str, confidence: str, indexes: List[int], evidence: List[str]) -> LogPattern:
    return LogPattern(pattern_id=pattern_id, title=title, severity=severity, confidence=confidence, event_indexes=indexes, evidence=evidence)


def detect_log_patterns(events: List[NormalizedAccessEvent], source_type: str) -> List[LogPattern]:
    if source_type not in SUPPORTED_LOG_SOURCE_TYPES:
        return [_pattern("LOG_PATTERN_UNSUPPORTED_SOURCE_TYPE", "Unsupported log source type", "low", "high", [], [f"Unsupported source_type: {source_type}"])]
    if not events:
        return [_pattern("LOG_PATTERN_NO_USABLE_EVENTS", "No usable access events were found", "medium", "high", [], ["No recognizable access-log evidence was found."])]

    patterns: List[LogPattern] = []
    ca = [i for i, e in enumerate(events) if e.event_outcome == "failure" and (e.conditional_access_status == "failure" or _has(e, "conditional access", "ca policy"))]
    if ca:
        patterns.append(_pattern("LOG_PATTERN_CONDITIONAL_ACCESS_BLOCK", "Conditional Access block pattern detected", "high", "high", ca, ["A failed event references Conditional Access or CA policy evaluation."]))

    mfa = [i for i, e in enumerate(events) if _has(e, "mfa", "multi-factor") and e.event_outcome in {"failure", "unknown"}]
    if mfa:
        patterns.append(_pattern("LOG_PATTERN_MFA_CHALLENGE_OR_FAILURE", "MFA challenge or failure pattern detected", "medium", "medium", mfa, ["An event references MFA or multi-factor authentication."]))

    license_service_plan = [
        i for i, e in enumerate(events)
        if e.event_outcome == "failure" and _has(
            e,
            "not licensed",
            "license missing",
            "no valid license",
            "license disabled",
            "service plan disabled",
            "service plan not enabled",
            "not assigned license",
        )
    ]
    if license_service_plan:
        patterns.append(_pattern("LOG_PATTERN_LICENSE_OR_SERVICE_PLAN_MISSING", "License or service plan evidence detected", "medium", "high", license_service_plan, ["A failed event references missing licensing or a disabled service plan."]))

    disabled = [i for i, e in enumerate(events) if e.event_outcome == "failure" and _has(e, "disabled")]
    if disabled:
        patterns.append(_pattern("LOG_PATTERN_DISABLED_ACCOUNT_ATTEMPT", "Disabled account attempt pattern detected", "high", "high", disabled, ["A failed event references a disabled identity state."]))

    denied = [i for i, e in enumerate(events) if e.event_outcome == "failure" and _has(e, "access denied", "forbidden", "unauthorized", "not assigned")]
    success = [i for i, e in enumerate(events) if e.event_outcome == "success"]
    if denied and success:
        patterns.append(_pattern("LOG_PATTERN_AUTH_SUCCESS_ACCESS_DENIED", "Authentication success followed by resource access denial", "high", "medium", sorted(set(success + denied)), ["Evidence includes successful authentication and a separate resource access denial."]))

    return patterns


def _finding_for(pattern: LogPattern) -> Dict[str, Any]:
    if pattern.pattern_id == "LOG_PATTERN_CONDITIONAL_ACCESS_BLOCK":
        return _finding(
            rule_id=pattern.pattern_id,
            title="Conditional Access appears to be blocking access",
            severity="high",
            confidence=pattern.confidence,
            likely_cause="The supplied access evidence indicates a failed Conditional Access evaluation for the affected access path.",
            evidence=pattern.evidence,
            evidence_missing=["Exact policy name and grant controls may be missing from pasted evidence."],
            next_steps=["Review the matching sign-in event in Entra ID.", "Identify the specific Conditional Access policy involved.", "Compare with a known successful sign-in if needed."],
            what_not_to_change_yet=["Do not disable Conditional Access globally.", "Do not exclude the user before identifying the specific policy and approval path."],
            limitations=["Generic pasted logs may not include full policy detail."],
            source_module=SOURCE_MODULE,
        )

    if pattern.pattern_id == "LOG_PATTERN_AUTH_SUCCESS_ACCESS_DENIED":
        return _finding(
            rule_id=pattern.pattern_id,
            title="Authentication appears successful but resource access is denied",
            severity="high",
            confidence=pattern.confidence,
            likely_cause="The evidence suggests authentication succeeded, but authorization to the target app or resource failed.",
            evidence=pattern.evidence,
            evidence_missing=["Resource assignment, app role, group membership, SharePoint permission, or access package evidence is incomplete."],
            next_steps=["Confirm expected access with the resource owner.", "Check app assignment, SharePoint group, M365 group, security group, access package, or file/share group membership."],
            what_not_to_change_yet=["Do not grant broad admin or owner access.", "Do not weaken Conditional Access when evidence points to resource authorization."],
            limitations=["Generic pasted logs may not include complete resource authorization evidence."],
            source_module=SOURCE_MODULE,
        )

    if pattern.pattern_id == "LOG_PATTERN_LICENSE_OR_SERVICE_PLAN_MISSING":
        return _finding(
            rule_id=pattern.pattern_id,
            title="License or service plan appears missing or disabled",
            severity="medium",
            confidence=pattern.confidence,
            likely_cause="The supplied evidence indicates the user may be missing a required license or service plan for the affected service.",
            evidence=pattern.evidence,
            evidence_missing=["Current license assignment, service-plan status, group-based licensing source, and propagation timing may be incomplete."],
            next_steps=["Confirm the user's assigned license SKU and service-plan status.", "Check whether licensing is direct or group-based.", "Compare with a known-good user who can access the same service.", "Confirm whether license changes are still propagating before escalating."],
            what_not_to_change_yet=["Do not grant broad admin access to work around a licensing issue.", "Do not remove and re-add licenses without confirming group-based licensing ownership and approval path."],
            limitations=["Pasted evidence may indicate a license symptom but may not prove the exact SKU or service-plan source."],
            source_module=SOURCE_MODULE,
        )

    if pattern.pattern_id == "LOG_PATTERN_MFA_CHALLENGE_OR_FAILURE":
        return _finding(
            rule_id=pattern.pattern_id,
            title="MFA challenge or failure appears in the access evidence",
            severity="medium",
            confidence=pattern.confidence,
            likely_cause="The supplied evidence references MFA during the affected access attempt.",
            evidence=pattern.evidence,
            evidence_missing=["Authentication method registration and detailed MFA result may be missing."],
            next_steps=["Confirm whether the user can complete MFA.", "Review the sign-in event MFA requirement and result."],
            what_not_to_change_yet=["Do not disable MFA globally."],
            limitations=["Generic pasted logs may only show that MFA was involved, not why it failed."],
            source_module=SOURCE_MODULE,
        )

    return _finding(
        rule_id=pattern.pattern_id,
        title=pattern.title,
        severity=pattern.severity,
        confidence=pattern.confidence,
        likely_cause="The supplied content does not provide enough usable access evidence for a confident diagnosis." if pattern.pattern_id == "LOG_PATTERN_NO_USABLE_EVENTS" else "The supplied access evidence contains a recognizable access-path pattern.",
        evidence=pattern.evidence,
        evidence_missing=["More complete sign-in, app, device, policy, or resource evidence may be required."],
        next_steps=["Collect fresh evidence for the affected user, service, and time window."],
        what_not_to_change_yet=["Do not make production access changes based only on incomplete evidence."],
        limitations=["The analyzer can only classify evidence that was supplied and parsed."],
        source_module=SOURCE_MODULE,
    )


def _report(request: LogAnalyzeRequest, data: Dict[str, Any]) -> str:
    lines = [
        "# TRACE Access Evidence Analysis Report",
        "",
        f"- Source type: `{request.source_type}`",
        f"- Affected user: `{request.affected_user or 'not provided'}`",
        f"- Affected service: `{request.affected_service or 'not provided'}`",
        f"- Status: `{data['status']}`",
        f"- Confidence: `{data['confidence']}`",
        "",
        "## Summary",
        "",
        data["summary"],
        "",
        "## Safe Next Steps",
        "",
    ]
    lines.extend(f"- {item}" for item in data["safe_next_steps"])
    lines.extend(["", "## What Not To Change Yet", ""])
    lines.extend(f"- {item}" for item in data["what_not_to_change_yet"])
    return "\n".join(lines)


def analyze_log_evidence(request: LogAnalyzeRequest) -> LogAnalysisResponse:
    events = parse_access_log_content(request.source_type, request.content)
    patterns = detect_log_patterns(events, request.source_type)
    findings = [_finding_for(pattern) for pattern in patterns]
    primary: Optional[Dict[str, Any]] = findings[0] if findings else None

    if primary:
        status = "insufficient_evidence" if primary["rule_id"] in {"LOG_PATTERN_NO_USABLE_EVENTS", "LOG_PATTERN_UNSUPPORTED_SOURCE_TYPE"} else "findings"
        data: Dict[str, Any] = {
            "status": status,
            "summary": primary["likely_cause"],
            "confidence": primary["confidence"],
            "evidence_used": primary["evidence_used"],
            "evidence_missing": primary["evidence_missing"],
            "safe_next_steps": primary["safe_next_steps"],
            "what_not_to_change_yet": primary["what_not_to_change_yet"],
            "limitations": primary["limitations"],
        }
    else:
        data = {
            "status": "no_blocking_evidence",
            "summary": "No blocking access pattern was identified in the supplied evidence.",
            "confidence": "medium",
            "evidence_used": [f"Parsed {len(events)} normalized access event(s)."],
            "evidence_missing": ["Additional IAM/access evidence may still be needed."],
            "safe_next_steps": ["Collect more targeted evidence if the user can still reproduce the issue."],
            "what_not_to_change_yet": ["Do not make production changes without a matching finding or additional evidence."],
            "limitations": ["Absence of a detected pattern does not prove that access is healthy."],
        }

    response = {
        **data,
        "source_type": request.source_type,
        "parse_status": "parsed" if events else "no_usable_events",
        "normalized_events": events,
        "detected_patterns": patterns,
        "primary_finding": primary,
        "findings": findings,
    }
    response["report_markdown"] = _report(request, response)
    return LogAnalysisResponse(**response)
