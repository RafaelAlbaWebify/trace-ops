from typing import Any, Dict

from fastapi import APIRouter

from .collector_runner import run_ad_readiness_check, run_graph_readiness_check, run_local_readiness_check

router = APIRouter(tags=["readiness"])


def _readiness_error_response(
    error: Dict[str, Any],
    *,
    check: str,
    module: str,
    default_code: str,
    default_message: str,
    safe_next_step: str,
    limitation: str,
    read_only_boundary: Dict[str, bool],
) -> Dict[str, Any]:
    return {
        "status": "error",
        "module": module,
        "check": check,
        "error": {
            "code": error.get("code", default_code),
            "message": error.get("message", default_message),
            **({"details": error["details"]} if "details" in error else {}),
        },
        "safe_next_steps": [safe_next_step],
        "limitations": [limitation],
        "read_only_boundary": read_only_boundary,
    }


@router.get("/api/readiness/graph")
def get_graph_readiness() -> Dict[str, Any]:
    runner_result = run_graph_readiness_check()

    if runner_result["status"] == "ok":
        return runner_result["result"]

    return _readiness_error_response(
        runner_result.get("error", {}),
        check="graph_readiness",
        module="m365-access-path-analyzer",
        default_code="GRAPH_READINESS_RUNNER_ERROR",
        default_message="The backend could not complete the Graph readiness check.",
        safe_next_step="Review the backend readiness error before attempting any real Graph diagnostic.",
        limitation="TRACE did not run a Graph diagnostic. This endpoint only checks local/session readiness.",
        read_only_boundary={
            "remediation_performed": False,
            "automatic_connection_attempted": False,
            "tenant_wide_scan_performed": False,
        },
    )


@router.get("/api/readiness/local")
def get_local_readiness() -> Dict[str, Any]:
    runner_result = run_local_readiness_check()

    if runner_result["status"] == "ok":
        return runner_result["result"]

    return _readiness_error_response(
        runner_result.get("error", {}),
        check="local_readiness",
        module="local-infrastructure-readiness",
        default_code="LOCAL_READINESS_RUNNER_ERROR",
        default_message="The backend could not complete the local readiness check.",
        safe_next_step="Review the backend readiness error before using TRACE against a homelab machine.",
        limitation="TRACE did not run DNS, AD, endpoint, or remediation diagnostics. This endpoint only checks local machine readiness.",
        read_only_boundary={
            "remediation_performed": False,
            "network_configuration_changed": False,
            "service_control_performed": False,
        },
    )


@router.get("/api/readiness/ad")
def get_ad_readiness() -> Dict[str, Any]:
    runner_result = run_ad_readiness_check()

    if runner_result["status"] == "ok":
        return runner_result["result"]

    return _readiness_error_response(
        runner_result.get("error", {}),
        check="ad_readiness",
        module="active-directory-readiness",
        default_code="AD_READINESS_RUNNER_ERROR",
        default_message="The backend could not complete the Active Directory readiness check.",
        safe_next_step="Review the backend readiness error before using TRACE against Active Directory.",
        limitation="TRACE did not query AD users, change AD objects, change group membership, or modify account state. This endpoint only checks AD readiness.",
        read_only_boundary={
            "remediation_performed": False,
            "ad_objects_modified": False,
            "group_membership_changed": False,
            "password_or_account_state_changed": False,
        },
    )
