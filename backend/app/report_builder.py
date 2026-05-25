from html import escape
from typing import Any, Dict, List

from .config import FIRST_MODULE_NAME, PRODUCT_NAME


def _analysis(scan_response: Dict[str, Any]) -> Dict[str, Any]:
    return scan_response.get("analysis") or {}


def _primary_finding(scan_response: Dict[str, Any]) -> Dict[str, Any]:
    return _analysis(scan_response).get("primary_finding") or {}


def _scan_result(scan_response: Dict[str, Any]) -> Dict[str, Any]:
    return scan_response.get("result") or {}


def _scan_input(scan_response: Dict[str, Any]) -> Dict[str, Any]:
    return _scan_result(scan_response).get("input") or {}


def _first_nonempty(*values: Any) -> Any:
    for value in values:
        if value not in (None, "", []):
            return value
    return None


def _raw_evidence_summary(scan_response: Dict[str, Any]) -> Dict[str, Any]:
    result = _scan_result(scan_response)
    signin_logs = result.get("signin_logs") or {}
    conditional_access = result.get("conditional_access") or {}
    device = result.get("device") or {}
    identity = result.get("identity") or {}
    licenses = result.get("licenses") or {}

    return {
        "identity": {
            "user_exists": identity.get("user_exists"),
            "account_enabled": identity.get("account_enabled"),
            "user_type": identity.get("user_type"),
        },
        "licenses": {
            "has_relevant_license": licenses.get("has_relevant_license"),
            "assigned_skus": licenses.get("assigned_skus", []),
        },
        "signin_logs": {
            "available": signin_logs.get("available"),
            "recent_event_count": len(signin_logs.get("recent_events") or []),
        },
        "conditional_access": {
            "details_available": conditional_access.get("details_available"),
            "policy_count": len(conditional_access.get("policies") or []),
        },
        "device": {
            "evidence_available": device.get("evidence_available"),
            "compliance_state": device.get("compliance_state"),
        },
    }


def build_json_report(scan_response: Dict[str, Any]) -> Dict[str, Any]:
    analysis = _analysis(scan_response)
    primary = _primary_finding(scan_response)
    result = _scan_result(scan_response)
    scan_input = _scan_input(scan_response)
    error = scan_response.get("error") or {}

    return {
        "product": PRODUCT_NAME,
        "module": FIRST_MODULE_NAME,
        "user_principal_name": scan_input.get("user_principal_name"),
        "affected_service": scan_input.get("affected_service"),
        "scenario": _first_nonempty(result.get("scenario_id"), error.get("scenario")),
        "scan_status": scan_response.get("status"),
        "primary_finding": primary.get("rule_id"),
        "severity": primary.get("severity"),
        "confidence": _first_nonempty(primary.get("confidence"), analysis.get("confidence")),
        "likely_cause": primary.get("likely_cause"),
        "evidence": primary.get("evidence", []),
        "next_steps": primary.get("next_steps", []),
        "what_not_to_change_yet": primary.get("what_not_to_change_yet", []),
        "limitations": _first_nonempty(primary.get("limitations"), analysis.get("limitations"), []),
        "summary": analysis.get("summary"),
        "raw_evidence_summary": _raw_evidence_summary(scan_response),
    }


def _html_list(items: List[str]) -> str:
    if not items:
        return "<p>None recorded.</p>"
    return "<ul>" + "".join(f"<li>{escape(str(item))}</li>" for item in items) + "</ul>"


def build_html_report(scan_response: Dict[str, Any]) -> str:
    report = build_json_report(scan_response)
    raw = report["raw_evidence_summary"]

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{escape(report["product"])} - {escape(report["module"])} Report</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 2rem; color: #1f2933; }}
    h1, h2 {{ color: #102a43; }}
    table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
    th, td {{ border: 1px solid #d9e2ec; padding: 0.5rem; text-align: left; }}
    th {{ background: #f0f4f8; }}
    .muted {{ color: #52606d; }}
  </style>
</head>
<body>
  <h1>{escape(report["product"])} Report</h1>
  <p class="muted">{escape(report["module"])}</p>

  <h2>Summary</h2>
  <table>
    <tr><th>User principal name</th><td>{escape(str(report["user_principal_name"]))}</td></tr>
    <tr><th>Affected service</th><td>{escape(str(report["affected_service"]))}</td></tr>
    <tr><th>Scenario</th><td>{escape(str(report["scenario"]))}</td></tr>
    <tr><th>Scan status</th><td>{escape(str(report["scan_status"]))}</td></tr>
    <tr><th>Primary finding</th><td>{escape(str(report["primary_finding"]))}</td></tr>
    <tr><th>Severity</th><td>{escape(str(report["severity"]))}</td></tr>
    <tr><th>Confidence</th><td>{escape(str(report["confidence"]))}</td></tr>
  </table>

  <h2>Likely Cause</h2>
  <p>{escape(str(report["likely_cause"] or report["summary"] or "No likely cause recorded."))}</p>

  <h2>Evidence</h2>
  {_html_list(report["evidence"])}

  <h2>Recommended Next Steps</h2>
  {_html_list(report["next_steps"])}

  <h2>What Not To Change Yet</h2>
  {_html_list(report["what_not_to_change_yet"])}

  <h2>Limitations</h2>
  {_html_list(report["limitations"])}

  <h2>Raw Evidence Summary</h2>
  <table>
    <tr><th>Identity</th><td>{escape(str(raw["identity"]))}</td></tr>
    <tr><th>Licenses</th><td>{escape(str(raw["licenses"]))}</td></tr>
    <tr><th>Sign-in logs</th><td>{escape(str(raw["signin_logs"]))}</td></tr>
    <tr><th>Conditional Access</th><td>{escape(str(raw["conditional_access"]))}</td></tr>
    <tr><th>Device</th><td>{escape(str(raw["device"]))}</td></tr>
  </table>
</body>
</html>"""
