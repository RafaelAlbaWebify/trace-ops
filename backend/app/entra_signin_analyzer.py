import csv
import io
from typing import Any, Dict, List, Optional

from .analyzer import _finding
from .log_models import LogAnalysisResponse, LogAnalyzeRequest, LogPattern, NormalizedAccessEvent

SOURCE_MODULE = "entra-signin-export-analyzer"
SUPPORTED_SOURCE_TYPE = "entra_signin_csv"

FIELD_MAP = {
    "createddatetime": "timestamp",
    "userprincipalname": "user_principal_name",
    "appdisplayname": "application",
    "resourcedisplayname": "resource",
    "clientappused": "client_app",
    "ipaddress": "ip_address",
    "conditionalaccessstatus": "conditional_access_status",
    "authenticationrequirement": "mfa_result",
    "status.failurereason": "failure_reason",
    "failurereason": "failure_reason",
    "status.errorcode": "error_code",
    "errorcode": "error_code",
    "status": "status",
    "devicedetail.displayname": "device_name",
    "devicedetail.iscompliant": "device_compliance",
}


def _key(value: str) -> str:
    return value.strip().lower().replace(" ", "").replace("_", "").replace("-", "")


def _normalize_row(row: Dict[str, str]) -> Dict[str, str]:
    result: Dict[str, str] = {}
    for key, value in row.items():
        target = FIELD_MAP.get(_key(key or ""))
        if target and value is not None and str(value).strip():
            result[target] = str(value).strip()
    return result


def _outcome(values: Dict[str, str]) -> str:
    status = values.get("status", "").lower()
    error_code = values.get("error_code", "").strip()
    reason = values.get("failure_reason", "").strip()
    ca_status = values.get("conditional_access_status", "").lower()

    if status in {"success", "succeeded"}:
        return "success"
    if status in {"failure", "failed", "interrupted"}:
        return "failure"
    if error_code and error_code not in {"0", "none"}:
        return "failure"
    if reason:
        return "failure"
    if ca_status == "failure":
        return "failure"
    if ca_status in {"success", "notapplied"}:
        return "success"
    return "unknown"


def parse_entra_signin_csv(content: str) -> List[NormalizedAccessEvent]:
    reader = csv.DictReader(io.StringIO(content.strip()))
    if not reader.fieldnames:
        return []

    events: List[NormalizedAccessEvent] = []
    for row in reader:
        values = _normalize_row(row)
        if not values:
            continue
        raw = "; ".join(f"{key}={value}" for key, value in values.items())
        events.append(
            NormalizedAccessEvent(
                timestamp=values.get("timestamp"),
                source_type=SUPPORTED_SOURCE_TYPE,
                event_type="signin",
                event_outcome=_outcome(values),
                user_principal_name=values.get("user_principal_name"),
                application=values.get("application"),
                resource=values.get("resource"),
                client_app=values.get("client_app"),
                ip_address=values.get("ip_address"),
                device_name=values.get("device_name"),
                device_compliance=values.get("device_compliance"),
                conditional_access_status=values.get("conditional_access_status"),
                mfa_result=values.get("mfa_result"),
                failure_reason=values.get("failure_reason"),
                raw_message=raw,
                matched_keywords=[],
            )
        )
    return events


def _pattern(pattern_id: str, title: str, severity: str, confidence: str, indexes: List[int], evidence: List[str]) -> LogPattern:
    return LogPattern(pattern_id=pattern_id, title=title, severity=severity, confidence=confidence, event_indexes=indexes, evidence=evidence)


def detect_entra_patterns(events: List[NormalizedAccessEvent]) -> List[LogPattern]:
    if not events:
        return [_pattern("LOG_PATTERN_NO_USABLE_EVENTS", "No usable Entra sign-in rows were found", "medium", "high", [], ["No recognizable Entra sign-in rows were found."])]

    patterns: List[LogPattern] = []
    ca_indexes = [i for i, event in enumerate(events) if event.event_outcome == "failure" and (event.conditional_access_status or "").lower() == "failure"]
    if ca_indexes:
        patterns.append(_pattern("LOG_PATTERN_CONDITIONAL_ACCESS_BLOCK", "Conditional Access failure in Entra sign-in export", "high", "high", ca_indexes, ["At least one exported sign-in row has conditionalAccessStatus=failure."]))

    mfa_indexes = [i for i, event in enumerate(events) if "multi" in (event.mfa_result or "").lower() or "mfa" in (event.mfa_result or "").lower()]
    if mfa_indexes:
        patterns.append(_pattern("LOG_PATTERN_MFA_CHALLENGE_OR_FAILURE", "MFA requirement appears in Entra sign-in export", "medium", "medium", mfa_indexes, ["At least one exported sign-in row includes an MFA authentication requirement."]))

    legacy_clients = {"imap", "pop", "smtp", "other clients"}
    legacy_indexes = [i for i, event in enumerate(events) if (event.client_app or "").strip().lower() in legacy_clients]
    if legacy_indexes:
        patterns.append(_pattern("LOG_PATTERN_LEGACY_CLIENT_OR_BASIC_AUTH", "Legacy client app appears in Entra sign-in export", "medium", "medium", legacy_indexes, ["At least one exported sign-in row uses a legacy client app value."]))

    return patterns


def _finding_for(pattern: LogPattern) -> Dict[str, Any]:
    if pattern.pattern_id == "LOG_PATTERN_CONDITIONAL_ACCESS_BLOCK":
        return _finding(
            rule_id=pattern.pattern_id,
            title="Conditional Access failure appears in Entra sign-in export",
            severity="high",
            confidence=pattern.confidence,
            likely_cause="The exported sign-in evidence indicates a Conditional Access failure for the affected access path.",
            evidence=pattern.evidence,
            evidence_missing=["Policy name and grant controls may require the full sign-in detail view."],
            next_steps=["Open the matching sign-in event in Entra ID.", "Review the policy result and grant/session controls.", "Compare the affected event with a known successful sign-in if needed."],
            what_not_to_change_yet=["Do not disable Conditional Access globally.", "Do not exclude the user before identifying the specific policy and approval path."],
            limitations=["CSV exports may not include every policy detail visible in the portal."],
            source_module=SOURCE_MODULE,
        )

    if pattern.pattern_id == "LOG_PATTERN_LEGACY_CLIENT_OR_BASIC_AUTH":
        return _finding(
            rule_id=pattern.pattern_id,
            title="Legacy client app appears in sign-in evidence",
            severity="medium",
            confidence=pattern.confidence,
            likely_cause="The exported sign-in evidence includes a legacy client app value that may not satisfy modern access requirements.",
            evidence=pattern.evidence,
            evidence_missing=["Client configuration and current access policy scope are not fully confirmed by the export alone."],
            next_steps=["Confirm which client or protocol generated the sign-in.", "Check whether the user should use a modern client for the affected service."],
            what_not_to_change_yet=["Do not weaken access policy controls before confirming the client requirement."],
            limitations=["The export identifies the client category but may not prove the endpoint application configuration."],
            source_module=SOURCE_MODULE,
        )

    return _finding(
        rule_id=pattern.pattern_id,
        title=pattern.title,
        severity=pattern.severity,
        confidence=pattern.confidence,
        likely_cause="The exported sign-in rows do not provide enough evidence for a confident diagnosis." if pattern.pattern_id == "LOG_PATTERN_NO_USABLE_EVENTS" else "The exported sign-in evidence contains a recognizable access-path pattern.",
        evidence=pattern.evidence,
        evidence_missing=["More complete sign-in, device, policy, or resource evidence may be required."],
        next_steps=["Collect a fresh export for the affected user, service, and time window."],
        what_not_to_change_yet=["Do not make access changes based only on incomplete exported evidence."],
        limitations=["The analyzer can only classify exported rows and fields that are present."],
        source_module=SOURCE_MODULE,
    )


def _report(request: LogAnalyzeRequest, data: Dict[str, Any]) -> str:
    return "\n".join([
        "# TRACE Entra Sign-in Export Analysis Report",
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
    ])


def analyze_entra_signin_export(request: LogAnalyzeRequest) -> LogAnalysisResponse:
    events = parse_entra_signin_csv(request.content)
    patterns = detect_entra_patterns(events)
    findings = [_finding_for(pattern) for pattern in patterns]
    primary: Optional[Dict[str, Any]] = findings[0] if findings else None

    if primary:
        status = "insufficient_evidence" if primary["rule_id"] == "LOG_PATTERN_NO_USABLE_EVENTS" else "findings"
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
            "summary": "No blocking Entra sign-in pattern was identified in the supplied export.",
            "confidence": "medium",
            "evidence_used": [f"Parsed {len(events)} Entra sign-in row(s)."],
            "evidence_missing": ["License, service-plan, app assignment, and full policy evidence may still be needed."],
            "safe_next_steps": ["Review adjacent sign-in rows for the same user, app, and time window if the issue continues."],
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
