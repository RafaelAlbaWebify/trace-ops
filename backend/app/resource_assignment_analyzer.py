import json
from typing import Any, Dict, List, Optional

from .analyzer import _finding
from .log_models import LogAnalysisResponse, LogAnalyzeRequest, LogPattern, NormalizedAccessEvent

SOURCE_MODULE = "resource-assignment-analyzer"
SUPPORTED_SOURCE_TYPE = "resource_assignment_json"


def _as_bool(value: Any) -> Optional[bool]:
    if isinstance(value, bool):
        return value
    if value is None:
        return None
    text = str(value).strip().lower()
    if text in {"true", "yes", "y", "1", "present", "assigned", "confirmed", "success"}:
        return True
    if text in {"false", "no", "n", "0", "missing", "not_assigned", "unconfirmed", "failure"}:
        return False
    return None


def _load_payload(content: str) -> Dict[str, Any]:
    try:
        parsed = json.loads(content or "{}")
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def parse_resource_assignment_json(content: str) -> List[NormalizedAccessEvent]:
    payload = _load_payload(content)
    if not payload:
        return []

    assignment_present = _as_bool(payload.get("assignment_present"))
    auth_outcome = str(payload.get("authentication_outcome", "unknown")).lower()
    outcome = "success" if auth_outcome in {"success", "succeeded"} else "unknown"
    if assignment_present is False:
        outcome = "failure"

    raw = "; ".join(f"{key}={value}" for key, value in payload.items() if value is not None)
    return [
        NormalizedAccessEvent(
            timestamp=payload.get("timestamp"),
            source_type=SUPPORTED_SOURCE_TYPE,
            event_type="authorization",
            event_outcome=outcome,
            user_principal_name=payload.get("user_principal_name") or payload.get("affected_user"),
            application=payload.get("application"),
            resource=payload.get("resource") or payload.get("affected_resource"),
            client_app=payload.get("client_app"),
            ip_address=None,
            device_name=payload.get("device_name"),
            device_compliance=payload.get("device_compliance"),
            conditional_access_status=payload.get("conditional_access_status"),
            mfa_result=payload.get("mfa_result"),
            failure_reason=payload.get("failure_reason"),
            raw_message=raw,
            matched_keywords=[],
        )
    ]


def _pattern(pattern_id: str, title: str, severity: str, confidence: str, indexes: List[int], evidence: List[str]) -> LogPattern:
    return LogPattern(pattern_id=pattern_id, title=title, severity=severity, confidence=confidence, event_indexes=indexes, evidence=evidence)


def detect_resource_assignment_patterns(payload: Dict[str, Any], events: List[NormalizedAccessEvent]) -> List[LogPattern]:
    if not payload or not events:
        return [_pattern("RESOURCE_ASSIGNMENT_EVIDENCE_MISSING", "Resource assignment evidence is missing", "medium", "high", [], ["No usable resource assignment evidence was provided."])]

    auth_ok = str(payload.get("authentication_outcome", "")).lower() in {"success", "succeeded"}
    assignment_present = _as_bool(payload.get("assignment_present"))
    expected = _as_bool(payload.get("expected_access_confirmed"))
    ca_ok = str(payload.get("conditional_access_status", "")).lower() in {"success", "notapplied", "not_applied", "unknown", ""}

    if auth_ok and assignment_present is False and ca_ok:
        confidence = "high" if expected is True else "medium"
        return [
            _pattern(
                "RESOURCE_ASSIGNMENT_OR_GROUP_MEMBERSHIP_MISSING_OR_UNCONFIRMED",
                "Authentication succeeded but resource assignment is missing or unconfirmed",
                "high",
                confidence,
                [0],
                [
                    "Authentication outcome is success.",
                    "Resource assignment evidence is missing or negative.",
                    "Conditional Access evidence does not explain the resource-scoped failure.",
                ],
            )
        ]

    if auth_ok and assignment_present is None:
        return [
            _pattern(
                "RESOURCE_ASSIGNMENT_EVIDENCE_INCOMPLETE",
                "Authentication succeeded but resource assignment evidence is incomplete",
                "medium",
                "medium",
                [0],
                ["Authentication outcome is success, but assignment evidence was not provided."],
            )
        ]

    return []


def _finding_for(pattern: LogPattern) -> Dict[str, Any]:
    if pattern.pattern_id == "RESOURCE_ASSIGNMENT_OR_GROUP_MEMBERSHIP_MISSING_OR_UNCONFIRMED":
        return _finding(
            rule_id=pattern.pattern_id,
            title="Resource assignment or group membership appears missing or unconfirmed",
            severity="high",
            confidence=pattern.confidence,
            likely_cause="The evidence suggests the user can authenticate, but authorization to the specific resource is missing or unconfirmed.",
            evidence=pattern.evidence,
            evidence_missing=["Nested group, app role, SharePoint permission, access package, or file/share membership evidence may still be incomplete."],
            next_steps=[
                "Confirm expected access with the resource owner.",
                "Check app assignment, SharePoint group, Microsoft 365 group, security group, access package, or file/share group membership.",
                "Use the normal approval path before changing assignment.",
                "Retest after the approved change and a token or session refresh.",
            ],
            what_not_to_change_yet=[
                "Do not grant broad admin or owner access for a scoped resource issue.",
                "Do not weaken Conditional Access if the evidence points to resource authorization.",
                "Do not change DNS, firewall, or service configuration without separate connectivity evidence.",
            ],
            limitations=["Operator-provided assignment evidence may not include nested group expansion or all resource-level permissions."],
            source_module=SOURCE_MODULE,
        )

    return _finding(
        rule_id=pattern.pattern_id,
        title=pattern.title,
        severity=pattern.severity,
        confidence=pattern.confidence,
        likely_cause="The supplied resource assignment evidence is incomplete for a confident authorization diagnosis.",
        evidence=pattern.evidence,
        evidence_missing=["Expected access, assignment source, group membership, app role, or resource owner confirmation may be missing."],
        next_steps=["Collect assignment evidence for the affected resource and confirm expected access."],
        what_not_to_change_yet=["Do not modify permissions or group membership until the access requirement is confirmed."],
        limitations=["TRACE can only classify the resource assignment evidence that was supplied."],
        source_module=SOURCE_MODULE,
    )


def _report(request: LogAnalyzeRequest, data: Dict[str, Any]) -> str:
    lines = [
        "# TRACE Resource Assignment Analysis Report",
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
    return "\n".join(lines)


def analyze_resource_assignment_evidence(request: LogAnalyzeRequest) -> LogAnalysisResponse:
    payload = _load_payload(request.content)
    events = parse_resource_assignment_json(request.content)
    patterns = detect_resource_assignment_patterns(payload, events)
    findings = [_finding_for(pattern) for pattern in patterns]
    primary: Optional[Dict[str, Any]] = findings[0] if findings else None

    if primary:
        status = "insufficient_evidence" if primary["rule_id"] in {"RESOURCE_ASSIGNMENT_EVIDENCE_MISSING", "RESOURCE_ASSIGNMENT_EVIDENCE_INCOMPLETE"} else "findings"
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
            "summary": "No resource assignment blocker was identified in the supplied evidence.",
            "confidence": "medium",
            "evidence_used": ["Resource assignment evidence was parsed."],
            "evidence_missing": ["More context may still be needed if the user can reproduce the issue."],
            "safe_next_steps": ["Retest with fresh sign-in and resource access evidence if the issue continues."],
            "what_not_to_change_yet": ["Do not change permissions without a matching finding or approval."],
            "limitations": ["No detected pattern does not prove the authorization path is healthy."],
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
