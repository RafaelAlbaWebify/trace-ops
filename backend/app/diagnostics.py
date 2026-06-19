from typing import Any, Dict, Literal, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from .collector_runner import (
    run_ad_user_access_diagnostic,
    run_dns_diagnostic,
    run_factoryops_computer_diagnostic,
    run_factoryops_file_share_access_diagnostic,
)

router = APIRouter(tags=["diagnostics"])


class DnsDiagnosticRequest(BaseModel):
    query: str = Field(min_length=1, max_length=253)
    record_type: Literal["A", "AAAA", "CNAME", "MX", "TXT", "PTR"] = "A"
    dns_server: Optional[str] = None



class FactoryOpsComputerDiagnosticRequest(BaseModel):
    computer_name: str = Field(min_length=1, max_length=253)
    domain_name: str = Field(default="factory.local", min_length=1, max_length=253)
    dns_server: Optional[str] = None
    expected_ipv4_address: Optional[str] = None


class FactoryOpsFileShareAccessDiagnosticRequest(BaseModel):
    share_host: str = Field(min_length=1, max_length=253)
    share_name: str = Field(min_length=1, max_length=120)
    user_sam_account_name: str = Field(min_length=1, max_length=120)
    required_group_sam_account_name: str = Field(min_length=1, max_length=120)
    domain_name: str = Field(default="factory.local", min_length=1, max_length=253)
    dns_server: Optional[str] = None
    observed_access_denied: Optional[bool] = None


class AdUserAccessDiagnosticRequest(BaseModel):
    user_principal_name: str = Field(min_length=3, max_length=320)
    affected_service: str = Field(min_length=1, max_length=120)
    scenario: Literal[
        "ad-account-disabled",
        "ad-account-locked",
        "ad-password-expired",
        "ad-required-group-missing",
        "ad-successful-baseline",
    ] = "ad-account-disabled"


def _dns_error_response(error: Dict[str, Any], request: DnsDiagnosticRequest) -> Dict[str, Any]:
    return {
        "status": "error",
        "module": "dns-diagnostics",
        "check": "dns_diagnostic",
        "input": request.model_dump(),
        "error": {
            "code": error.get("code", "DNS_DIAGNOSTIC_RUNNER_ERROR"),
            "message": error.get("message", "The backend could not complete the DNS diagnostic."),
            **({"details": error["details"]} if "details" in error else {}),
        },
        "evidence": {
            "query": request.query,
            "record_type": request.record_type,
            "dns_server": request.dns_server,
            "resolved": False,
            "records": [],
            "record_count": 0,
            "error": error.get("message", "DNS diagnostic runner error."),
        },
        "findings": [],
        "safe_next_steps": ["Review the backend DNS diagnostic error before changing any DNS or network settings."],
        "limitations": ["TRACE did not change DNS, IP, service, AD, or endpoint configuration."],
        "read_only_boundary": {
            "remediation_performed": False,
            "dns_configuration_changed": False,
            "network_configuration_changed": False,
        },
    }




def _factoryops_computer_error_response(error: Dict[str, Any], request: FactoryOpsComputerDiagnosticRequest) -> Dict[str, Any]:
    computer_fqdn = request.computer_name if "." in request.computer_name else f"{request.computer_name}.{request.domain_name}"
    return {
        "status": "error",
        "module": "factoryops-computer-diagnostic",
        "check": "factoryops_computer_diagnostic",
        "input": {
            **request.model_dump(),
            "computer_fqdn": computer_fqdn.lower(),
        },
        "error": {
            "code": error.get("code", "FACTORYOPS_COMPUTER_RUNNER_ERROR"),
            "message": error.get("message", "The backend could not complete the FactoryOps computer diagnostic."),
            **({"details": error["details"]} if "details" in error else {}),
        },
        "evidence": {
            "dns": {"records": [], "resolved_ipv4_addresses": [], "error": error.get("message")},
            "active_directory": {"module_available": None, "computer_found": False, "computer": None, "error": error.get("message")},
            "reachability": {"target": computer_fqdn.lower(), "icmp_reachable": None, "port_probes": []},
        },
        "findings": [],
        "safe_next_steps": ["Review the backend FactoryOps computer diagnostic error before changing DNS, firewall, endpoint, or AD settings."],
        "limitations": ["TRACE did not change DNS, IP, firewall, AD, service, endpoint, credential, or token configuration."],
        "read_only_boundary": {
            "remediation_performed": False,
            "dns_configuration_changed": False,
            "network_configuration_changed": False,
            "firewall_configuration_changed": False,
            "ad_objects_modified": False,
            "service_control_performed": False,
            "remote_command_executed": False,
            "credentials_or_tokens_stored": False,
        },
    }

def _factoryops_file_share_error_response(error: Dict[str, Any], request: FactoryOpsFileShareAccessDiagnosticRequest) -> Dict[str, Any]:
    share_host_fqdn = request.share_host if "." in request.share_host else f"{request.share_host}.{request.domain_name}"
    share_unc_path = "\\" + share_host_fqdn.lower() + "\\" + request.share_name
    return {
        "status": "error",
        "module": "factoryops-file-share-access-diagnostic",
        "check": "factoryops_file_share_access_diagnostic",
        "input": {
            **request.model_dump(),
            "share_host_fqdn": share_host_fqdn.lower(),
            "share_unc_path": share_unc_path,
        },
        "error": {
            "code": error.get("code", "FACTORYOPS_FILE_SHARE_RUNNER_ERROR"),
            "message": error.get("message", "The backend could not complete the FactoryOps file-share access diagnostic."),
            **({"details": error["details"]} if "details" in error else {}),
        },
        "evidence": {
            "dns": {"records": [], "resolved_ipv4_addresses": [], "error": error.get("message")},
            "reachability": {"target": share_host_fqdn.lower(), "smb_tcp_445_reachable": None},
            "active_directory": {
                "module_available": None,
                "user_found": False,
                "user": None,
                "required_group_found": False,
                "required_group": None,
                "membership_proven": None,
                "user_error": error.get("message"),
                "group_error": error.get("message"),
            },
            "observed_access": {"access_denied": request.observed_access_denied, "supplied_by_operator": request.observed_access_denied is not None},
        },
        "findings": [],
        "safe_next_steps": ["Review the backend FactoryOps file-share diagnostic error before changing AD, SMB, DNS, firewall, NTFS, or share permissions."],
        "limitations": ["TRACE did not change DNS, SMB, firewall, AD, NTFS, share permissions, credentials, or tokens."],
        "read_only_boundary": {
            "remediation_performed": False,
            "dns_configuration_changed": False,
            "network_configuration_changed": False,
            "firewall_configuration_changed": False,
            "ad_objects_modified": False,
            "group_membership_changed": False,
            "ntfs_or_share_permissions_changed": False,
            "service_control_performed": False,
            "remote_command_executed": False,
            "credentials_or_tokens_stored": False,
            "user_impersonation_performed": False,
        },
    }


def _ad_user_error_response(error: Dict[str, Any], request: AdUserAccessDiagnosticRequest) -> Dict[str, Any]:
    return {
        "status": "error",
        "module": "active-directory-user-access-diagnostic",
        "check": "ad_user_access_diagnostic",
        "input": {
            **request.model_dump(),
            "fixture_mode": True,
        },
        "error": {
            "code": error.get("code", "AD_USER_ACCESS_RUNNER_ERROR"),
            "message": error.get("message", "The backend could not complete the AD user access diagnostic."),
            **({"details": error["details"]} if "details" in error else {}),
        },
        "evidence": {
            "user": None,
            "group_requirements": [],
            "fixture_mode": True,
            "real_ad_query_performed": False,
        },
        "findings": [],
        "safe_next_steps": ["Review the backend AD user access diagnostic error before changing any AD, DNS, endpoint, or service setting."],
        "limitations": ["TRACE stayed in fixture mode and did not query or modify Active Directory."],
        "read_only_boundary": {
            "remediation_performed": False,
            "ad_objects_modified": False,
            "group_membership_changed": False,
            "password_or_account_state_changed": False,
            "real_ad_query_performed": False,
        },
    }


@router.post("/api/diagnostics/dns")
def post_dns_diagnostic(request: DnsDiagnosticRequest) -> Dict[str, Any]:
    runner_result = run_dns_diagnostic(
        query=request.query,
        record_type=request.record_type,
        dns_server=request.dns_server,
    )

    if runner_result["status"] == "ok":
        return runner_result["result"]

    return _dns_error_response(runner_result.get("error", {}), request)




@router.post("/api/diagnostics/factoryops/computer")
def post_factoryops_computer_diagnostic(request: FactoryOpsComputerDiagnosticRequest) -> Dict[str, Any]:
    runner_result = run_factoryops_computer_diagnostic(
        computer_name=request.computer_name,
        domain_name=request.domain_name,
        dns_server=request.dns_server,
        expected_ipv4_address=request.expected_ipv4_address,
    )

    if runner_result["status"] == "ok":
        return runner_result["result"]

    return _factoryops_computer_error_response(runner_result.get("error", {}), request)


@router.post("/api/diagnostics/factoryops/file-share-access")
def post_factoryops_file_share_access_diagnostic(request: FactoryOpsFileShareAccessDiagnosticRequest) -> Dict[str, Any]:
    runner_result = run_factoryops_file_share_access_diagnostic(
        share_host=request.share_host,
        share_name=request.share_name,
        user_sam_account_name=request.user_sam_account_name,
        required_group_sam_account_name=request.required_group_sam_account_name,
        domain_name=request.domain_name,
        dns_server=request.dns_server,
        observed_access_denied=request.observed_access_denied,
    )

    if runner_result["status"] == "ok":
        return runner_result["result"]

    return _factoryops_file_share_error_response(runner_result.get("error", {}), request)


@router.post("/api/diagnostics/ad-user-access")
def post_ad_user_access_diagnostic(request: AdUserAccessDiagnosticRequest) -> Dict[str, Any]:
    runner_result = run_ad_user_access_diagnostic(
        user_principal_name=request.user_principal_name,
        affected_service=request.affected_service,
        scenario=request.scenario,
    )

    if runner_result["status"] == "ok":
        return runner_result["result"]

    return _ad_user_error_response(runner_result.get("error", {}), request)
