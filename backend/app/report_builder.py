from datetime import datetime, timezone
from html import escape
from typing import Any, Dict, List

from .config import FIRST_MODULE_NAME, PRODUCT_NAME

REPORT_CONTRACT_VERSION = "TRACE_REPORT_V2"


def _analysis(scan_response: Dict[str, Any]) -> Dict[str, Any]:
    return scan_response.get("analysis") or {}


def _findings(scan_response: Dict[str, Any]) -> List[Dict[str, Any]]:
    findings = _analysis(scan_response).get("findings") or []
    return findings if isinstance(findings, list) else []


def _primary_finding(scan_response: Dict[str, Any]) -> Dict[str, Any]:
    primary = _analysis(scan_response).get("primary_finding") or {}
    if primary:
        return primary
    findings = _findings(scan_response)
    return findings[0] if findings else {}


def _scan_result(scan_response: Dict[str, Any]) -> Dict[str, Any]:
    return scan_response.get("result") or {}


def _scan_input(scan_response: Dict[str, Any]) -> Dict[str, Any]:
    return _scan_result(scan_response).get("input") or {}


def _first_nonempty(*values: Any) -> Any:
    for value in values:
        if value not in (None, "", []):
            return value
    return None


def _as_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _normalise_finding(finding: Dict[str, Any]) -> Dict[str, Any]:
    finding_id = _first_nonempty(finding.get("finding_id"), finding.get("rule_id"), "UNKNOWN_FINDING")
    evidence_used = _as_list(_first_nonempty(finding.get("evidence_used"), finding.get("evidence"), []))
    safe_next_steps = _as_list(_first_nonempty(finding.get("safe_next_steps"), finding.get("next_steps"), []))
    limitations = _as_list(finding.get("limitations"))
    evidence_missing = _as_list(_first_nonempty(finding.get("evidence_missing"), limitations, []))

    return {
        "finding_id": finding_id,
        "rule_id": _first_nonempty(finding.get("rule_id"), finding_id),
        "title": finding.get("title"),
        "severity": finding.get("severity"),
        "confidence": finding.get("confidence"),
        "likely_cause": finding.get("likely_cause"),
        "source_module": finding.get("source_module"),
        "evidence_used": evidence_used,
        "evidence_missing": evidence_missing,
        "safe_next_steps": safe_next_steps,
        "what_not_to_change_yet": _as_list(finding.get("what_not_to_change_yet")),
        "limitations": limitations,
    }


def _normalised_findings(scan_response: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [_normalise_finding(finding) for finding in _findings(scan_response)]


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


def _severity_counts(findings: List[Dict[str, Any]]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for finding in findings:
        severity = str(finding.get("severity") or "unknown")
        counts[severity] = counts.get(severity, 0) + 1
    return counts


def _confidence_counts(findings: List[Dict[str, Any]]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for finding in findings:
        confidence = str(finding.get("confidence") or "unknown")
        counts[confidence] = counts.get(confidence, 0) + 1
    return counts


def _executive_summary(scan_response: Dict[str, Any], findings: List[Dict[str, Any]]) -> Dict[str, Any]:
    analysis = _analysis(scan_response)
    primary = findings[0] if findings else {}
    if findings:
        headline = _first_nonempty(
            primary.get("likely_cause"),
            primary.get("title"),
            analysis.get("summary"),
            "TRACE produced one or more findings that need review.",
        )
    else:
        headline = _first_nonempty(
            analysis.get("summary"),
            "TRACE did not identify an access blocker from the available evidence.",
        )

    return {
        "headline": headline,
        "finding_count": len(findings),
        "primary_finding": primary.get("finding_id"),
        "highest_severity": primary.get("severity"),
        "overall_confidence": _first_nonempty(primary.get("confidence"), analysis.get("confidence")),
        "operator_message": (
            "Review evidence, missing evidence, and safe next steps before making any change."
            if findings
            else "No finding was produced; validate scope and evidence freshness before closing the case."
        ),
    }


def _safety_boundary_summary() -> Dict[str, bool]:
    return {
        "read_only_report": True,
        "remediation_performed": False,
        "credentials_or_tokens_stored": False,
        "tenant_wide_scan_performed": False,
    }


def build_json_report(scan_response: Dict[str, Any]) -> Dict[str, Any]:
    analysis = _analysis(scan_response)
    primary = _normalise_finding(_primary_finding(scan_response)) if _primary_finding(scan_response) else {}
    result = _scan_result(scan_response)
    scan_input = _scan_input(scan_response)
    error = scan_response.get("error") or {}
    findings = _normalised_findings(scan_response)

    primary_finding_id = _first_nonempty(primary.get("finding_id"), primary.get("rule_id"))

    return {
        "product": PRODUCT_NAME,
        "module": FIRST_MODULE_NAME,
        "report_contract_version": REPORT_CONTRACT_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "user_principal_name": scan_input.get("user_principal_name"),
        "affected_service": scan_input.get("affected_service"),
        "scenario": _first_nonempty(result.get("scenario_id"), error.get("scenario")),
        "scan_status": scan_response.get("status"),
        "evidence_contract_version": analysis.get("evidence_contract_version"),
        "executive_summary": _executive_summary(scan_response, findings),
        "finding_count": len(findings),
        "severity_counts": _severity_counts(findings),
        "confidence_counts": _confidence_counts(findings),
        "findings": findings,
        "safety_boundary": _safety_boundary_summary(),
        "primary_finding": primary_finding_id,
        "source_module": primary.get("source_module"),
        "severity": primary.get("severity"),
        "confidence": _first_nonempty(primary.get("confidence"), analysis.get("confidence")),
        "likely_cause": primary.get("likely_cause"),
        "evidence_used": _first_nonempty(primary.get("evidence_used"), []),
        "evidence_missing": _first_nonempty(primary.get("evidence_missing"), []),
        "evidence": _first_nonempty(primary.get("evidence_used"), []),
        "next_steps": _first_nonempty(primary.get("safe_next_steps"), []),
        "what_not_to_change_yet": primary.get("what_not_to_change_yet", []),
        "limitations": _first_nonempty(primary.get("limitations"), analysis.get("limitations"), []),
        "summary": analysis.get("summary"),
        "raw_evidence_summary": _raw_evidence_summary(scan_response),
    }


def _html_list(items: List[Any]) -> str:
    if not items:
        return "<p>None recorded.</p>"
    return "<ul>" + "".join(f"<li>{escape(str(item))}</li>" for item in items) + "</ul>"


def _html_kv_table(values: Dict[str, Any]) -> str:
    rows = "".join(
        f"<tr><th>{escape(str(key).replace('_', ' ').title())}</th><td>{escape(str(value))}</td></tr>"
        for key, value in values.items()
    )
    return f"<table>{rows}</table>"


def _html_findings(findings: List[Dict[str, Any]]) -> str:
    if not findings:
        return "<p>No findings were produced from the available evidence.</p>"

    sections = []
    for index, finding in enumerate(findings, start=1):
        title = _first_nonempty(finding.get("title"), finding.get("finding_id"), f"Finding {index}")
        sections.append(
            f"""
  <section class=\"finding-card\">
    <h3>{index}. {escape(str(title))}</h3>
    {_html_kv_table({
        "finding_id": finding.get("finding_id"),
        "severity": finding.get("severity"),
        "confidence": finding.get("confidence"),
        "source_module": finding.get("source_module"),
        "likely_cause": finding.get("likely_cause"),
    })}
    <h4>Evidence Used</h4>
    {_html_list(finding.get("evidence_used") or [])}
    <h4>Evidence Missing</h4>
    {_html_list(finding.get("evidence_missing") or [])}
    <h4>Safe Next Steps</h4>
    {_html_list(finding.get("safe_next_steps") or [])}
    <h4>What Not To Change Yet</h4>
    {_html_list(finding.get("what_not_to_change_yet") or [])}
  </section>
"""
        )
    return "".join(sections)


def build_html_report(scan_response: Dict[str, Any]) -> str:
    report = build_json_report(scan_response)
    raw = report["raw_evidence_summary"]
    executive = report["executive_summary"]

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{escape(report["product"])} - {escape(report["module"])} Report</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 2rem; color: #1f2933; line-height: 1.45; }}
    h1, h2, h3, h4 {{ color: #102a43; }}
    table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
    th, td {{ border: 1px solid #d9e2ec; padding: 0.5rem; text-align: left; vertical-align: top; }}
    th {{ background: #f0f4f8; width: 28%; }}
    .muted {{ color: #52606d; }}
    .callout {{ border-left: 4px solid #627d98; background: #f8fafc; padding: 1rem; margin: 1rem 0; }}
    .finding-card {{ border: 1px solid #d9e2ec; border-radius: 8px; padding: 1rem; margin: 1rem 0; }}
    .safety {{ border-left: 4px solid #9aa5b1; background: #f5f7fa; padding: 1rem; }}
  </style>
</head>
<body>
  <h1>{escape(report["product"])} Report</h1>
  <p class="muted">{escape(report["module"])} | {escape(report["report_contract_version"])} | Generated {escape(str(report["generated_at"]))}</p>

  <h2>Executive Summary</h2>
  <div class="callout">
    <p><strong>{escape(str(executive["headline"]))}</strong></p>
    <p>{escape(str(executive["operator_message"]))}</p>
  </div>
  {_html_kv_table({
      "finding_count": report["finding_count"],
      "primary_finding": report["primary_finding"],
      "highest_severity": executive.get("highest_severity"),
      "overall_confidence": executive.get("overall_confidence"),
  })}

  <h2>Case Scope</h2>
  {_html_kv_table({
      "user_principal_name": report["user_principal_name"],
      "affected_service": report["affected_service"],
      "scenario": report["scenario"],
      "scan_status": report["scan_status"],
      "evidence_contract_version": report["evidence_contract_version"],
  })}

  <h2>Findings</h2>
  {_html_findings(report["findings"])}

  <h2>Primary Finding Compatibility View</h2>
  <p>This section preserves the earlier report layout for existing workflows.</p>
  {_html_kv_table({
      "primary_finding": report["primary_finding"],
      "source_module": report["source_module"],
      "severity": report["severity"],
      "confidence": report["confidence"],
      "likely_cause": report["likely_cause"] or report["summary"],
  })}

  <h2>Safety Boundary</h2>
  <div class="safety">
    {_html_kv_table(report["safety_boundary"])}
    <p>TRACE reports are read-only evidence summaries. Review safe next steps before making changes in any system.</p>
  </div>

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
