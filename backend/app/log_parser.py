import re
import shlex
from typing import Dict, List, Optional

from .log_models import NormalizedAccessEvent


SUPPORTED_LOG_SOURCE_TYPES = {"generic_access_log_text"}

TIMESTAMP_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:Z|[+-]\d{2}:?\d{2})?\b")
UPN_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")

KEYWORDS = (
    "conditional access",
    "mfa",
    "multi-factor",
    "access denied",
    "forbidden",
    "unauthorized",
    "disabled",
    "not licensed",
    "not assigned",
    "non-compliant",
    "noncompliant",
    "failure",
    "failed",
    "blocked",
    "success",
    "succeeded",
)

KEY_ALIASES = {
    "user": "user_principal_name",
    "upn": "user_principal_name",
    "userprincipalname": "user_principal_name",
    "app": "application",
    "application": "application",
    "resource": "resource",
    "client": "client_app",
    "clientapp": "client_app",
    "client_app": "client_app",
    "ip": "ip_address",
    "ipaddress": "ip_address",
    "ip_address": "ip_address",
    "device": "device_name",
    "devicename": "device_name",
    "device_name": "device_name",
    "compliance": "device_compliance",
    "device_compliance": "device_compliance",
    "ca": "conditional_access_status",
    "conditionalaccess": "conditional_access_status",
    "conditional_access": "conditional_access_status",
    "conditionalaccessstatus": "conditional_access_status",
    "mfa": "mfa_result",
    "mfa_result": "mfa_result",
    "result": "event_outcome",
    "status": "event_outcome",
    "outcome": "event_outcome",
    "reason": "failure_reason",
    "failure": "failure_reason",
    "failurereason": "failure_reason",
    "failure_reason": "failure_reason",
}


def _extract_timestamp(line: str) -> Optional[str]:
    match = TIMESTAMP_RE.search(line)
    if match:
        return match.group(0).replace(" ", "T")
    return None


def _extract_key_values(line: str) -> Dict[str, str]:
    values: Dict[str, str] = {}
    try:
        tokens = shlex.split(line)
    except ValueError:
        tokens = line.split()

    for token in tokens:
        if "=" not in token:
            continue
        key, value = token.split("=", 1)
        normalized_key = KEY_ALIASES.get(key.strip().lower().replace("-", "_"))
        if normalized_key and value.strip():
            values[normalized_key] = value.strip().strip('"')
    return values


def _matched_keywords(line: str) -> List[str]:
    lower = line.lower()
    return [keyword for keyword in KEYWORDS if keyword in lower]


def _derive_outcome(line: str, explicit_outcome: Optional[str]) -> str:
    value = (explicit_outcome or "").lower()
    lower = line.lower()

    if value in {"success", "succeeded", "ok"}:
        return "success"
    if value in {"failure", "failed", "error", "denied", "blocked"}:
        return "failure"
    if any(keyword in lower for keyword in ("failure", "failed", "access denied", "forbidden", "unauthorized", "blocked", "disabled", "not licensed", "not assigned")):
        return "failure"
    if any(keyword in lower for keyword in ("success", "succeeded")):
        return "success"
    return "unknown"


def _derive_device_compliance(line: str, explicit_compliance: Optional[str]) -> Optional[str]:
    if explicit_compliance:
        return explicit_compliance
    lower = line.lower()
    if "non-compliant" in lower or "noncompliant" in lower:
        return "nonCompliant"
    if "compliant" in lower:
        return "compliant"
    return None


def _is_usable_line(line: str, key_values: Dict[str, str], matched: List[str]) -> bool:
    return bool(key_values or matched or _extract_timestamp(line) or UPN_RE.search(line))


def parse_generic_access_log_text(content: str, source_type: str = "generic_access_log_text") -> List[NormalizedAccessEvent]:
    events: List[NormalizedAccessEvent] = []

    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        key_values = _extract_key_values(line)
        matched = _matched_keywords(line)
        if not _is_usable_line(line, key_values, matched):
            continue

        upn_match = UPN_RE.search(line)
        outcome = _derive_outcome(line, key_values.get("event_outcome"))
        lower = line.lower()

        conditional_access_status = key_values.get("conditional_access_status")
        if conditional_access_status is None and "conditional access" in lower and outcome == "failure":
            conditional_access_status = "failure"

        mfa_result = key_values.get("mfa_result")
        if mfa_result is None and ("mfa" in lower or "multi-factor" in lower):
            if outcome == "failure":
                mfa_result = "failure"
            elif "satisfied" in lower:
                mfa_result = "satisfied"
            else:
                mfa_result = "required"

        event = NormalizedAccessEvent(
            timestamp=_extract_timestamp(line),
            source_type=source_type,
            event_outcome=outcome,
            user_principal_name=key_values.get("user_principal_name") or (upn_match.group(0) if upn_match else None),
            application=key_values.get("application"),
            resource=key_values.get("resource"),
            client_app=key_values.get("client_app"),
            ip_address=key_values.get("ip_address"),
            device_name=key_values.get("device_name"),
            device_compliance=_derive_device_compliance(line, key_values.get("device_compliance")),
            conditional_access_status=conditional_access_status,
            mfa_result=mfa_result,
            failure_reason=key_values.get("failure_reason"),
            raw_message=line,
            matched_keywords=matched,
        )
        events.append(event)

    return events


def parse_access_log_content(source_type: str, content: str) -> List[NormalizedAccessEvent]:
    if source_type not in SUPPORTED_LOG_SOURCE_TYPES:
        return []
    return parse_generic_access_log_text(content=content, source_type=source_type)
