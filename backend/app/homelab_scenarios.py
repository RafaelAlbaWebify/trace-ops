from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter

router = APIRouter(tags=["homelab-scenarios"])

SCENARIO_CONTRACT_VERSION = "trace-homelab-scenario-preview-v1"
ALLOWED_DIAGNOSTIC_TYPES = {
    "dns",
    "ad_readiness",
    "ad_user_access_fixture",
    "local_readiness",
    "graph_readiness",
    "factoryops_file_share_access",
}


def _as_list(value: Any) -> List[Any]:
    return value if isinstance(value, list) else []


def _as_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _string_list(values: Any) -> List[str]:
    return [str(item) for item in _as_list(values) if str(item).strip()]


def _count_dict_items(container: Dict[str, Any], key: str) -> int:
    return len(_as_list(container.get(key)))


def _build_diagnostic_plan(diagnostics: List[Any]) -> List[Dict[str, Any]]:
    plan: List[Dict[str, Any]] = []
    for index, raw_step in enumerate(diagnostics, start=1):
        step = _as_dict(raw_step)
        diagnostic_type = str(step.get("type", "unknown")).strip() or "unknown"
        plan.append(
            {
                "step": index,
                "type": diagnostic_type,
                "label": str(step.get("label") or step.get("name") or diagnostic_type),
                "target": step.get("target") or step.get("query") or step.get("user_principal_name"),
                "record_type": step.get("record_type"),
                "scenario": step.get("scenario"),
                "supported_by_trace_now": diagnostic_type in ALLOWED_DIAGNOSTIC_TYPES,
                "execution_mode": "preview_only",
            }
        )
    return plan


def preview_homelab_scenario(scenario: Dict[str, Any]) -> Dict[str, Any]:
    errors: List[str] = []
    warnings: List[str] = []

    scenario_id = str(scenario.get("scenario_id", "")).strip()
    name = str(scenario.get("name", "")).strip()
    environment = _as_dict(scenario.get("environment"))
    diagnostics = _as_list(scenario.get("diagnostics"))

    if not scenario_id:
        errors.append("scenario_id is required.")
    if not name:
        errors.append("name is required.")
    if not environment:
        errors.append("environment object is required.")
    if not diagnostics:
        errors.append("diagnostics list is required.")

    diagnostic_plan = _build_diagnostic_plan(diagnostics)
    unsupported = [step["type"] for step in diagnostic_plan if not step["supported_by_trace_now"]]
    if unsupported:
        warnings.append("Some diagnostic step types are not supported by TRACE yet: " + ", ".join(sorted(set(unsupported))))

    if scenario.get("actions") or scenario.get("remediation") or scenario.get("changes"):
        errors.append("Scenario preview files must not include actions, remediation, or configuration-change sections.")

    ad = _as_dict(environment.get("active_directory"))
    network = _as_dict(environment.get("network"))
    dns = _as_dict(environment.get("dns"))
    endpoints = _as_list(environment.get("endpoints"))
    servers = _as_list(environment.get("servers"))

    preview_summary = {
        "domain": ad.get("domain_name") or environment.get("domain_name"),
        "site_name": environment.get("site_name"),
        "vlan_count": _count_dict_items(network, "vlans"),
        "subnet_count": _count_dict_items(network, "subnets"),
        "dns_server_count": len(_string_list(dns.get("servers"))),
        "dns_record_count": _count_dict_items(dns, "records"),
        "server_count": len(servers),
        "endpoint_count": len(endpoints),
        "ad_user_count": _count_dict_items(ad, "users"),
        "ad_group_count": _count_dict_items(ad, "groups"),
        "diagnostic_step_count": len(diagnostic_plan),
        "expected_finding_count": len(_as_list(scenario.get("expected_findings"))),
    }

    validation_status = "valid" if not errors else "invalid"
    status = "ok" if validation_status == "valid" and not warnings else "warning"
    if errors:
        status = "error"

    return {
        "status": status,
        "module": "homelab-scenario-preview",
        "check": "homelab_scenario_preview",
        "scenario_contract_version": SCENARIO_CONTRACT_VERSION,
        "scenario_id": scenario_id or None,
        "name": name or None,
        "description": scenario.get("description"),
        "validation": {
            "status": validation_status,
            "errors": errors,
            "warnings": warnings,
        },
        "preview_summary": preview_summary,
        "diagnostic_plan": diagnostic_plan,
        "safe_next_steps": [
            "Review the preview and expected findings before connecting it to runnable diagnostics.",
            "Keep homelab scenarios as evidence and intent files; do not include remediation actions in the scenario contract.",
        ],
        "limitations": [
            "Phase 8 previews scenario files only; it does not execute diagnostics from the scenario document.",
            "Imported scenarios are not persisted yet; this endpoint validates and previews the submitted JSON payload only.",
        ],
        "read_only_boundary": {
            "preview_only": True,
            "diagnostics_executed": False,
            "configuration_changed": False,
            "ad_objects_modified": False,
            "dns_records_modified": False,
            "credentials_or_tokens_stored": False,
        },
    }


@router.post("/api/homelab/scenarios/preview")
def post_homelab_scenario_preview(scenario: Dict[str, Any]) -> Dict[str, Any]:
    return preview_homelab_scenario(scenario)
