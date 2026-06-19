import json
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional

from pydantic import BaseModel

from .collector_contract import validate_collector_result
from .config import (
    COLLECTOR_SCRIPT_PATH,
    COLLECTOR_TIMEOUT_SECONDS,
    GRAPH_READINESS_SCRIPT_PATH,
    LOCAL_READINESS_SCRIPT_PATH,
    DNS_DIAGNOSTIC_SCRIPT_PATH,
    AD_READINESS_SCRIPT_PATH,
    AD_USER_ACCESS_SCRIPT_PATH,
    FACTORYOPS_COMPUTER_DIAGNOSTIC_SCRIPT_PATH,
    FACTORYOPS_FILE_SHARE_DIAGNOSTIC_SCRIPT_PATH,
)
from .errors import BackendValidationError
from .models import CollectorErrorResult, CollectorResult


def _model_to_dict(model: BaseModel) -> Dict[str, Any]:
    return model.model_dump()


def _runner_error(
    code: str,
    message: str,
    *,
    return_code: Optional[int] = None,
    stderr: str = "",
    details: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    error: Dict[str, Any] = {
        "code": code,
        "message": message,
    }
    if return_code is not None:
        error["return_code"] = return_code
    if stderr:
        error["stderr"] = stderr
    if details:
        error["details"] = details

    return {
        "status": "error",
        "error": error,
    }


def _quote_powershell_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def build_collector_command(
    *,
    user_principal_name: str,
    affected_service: str,
    scenario: str,
    collector_script_path: Path = COLLECTOR_SCRIPT_PATH,
    powershell_executable: str = "powershell",
) -> list[str]:
    command_script = (
        f"& {_quote_powershell_literal(str(collector_script_path))} "
        f"-UserPrincipalName {_quote_powershell_literal(user_principal_name)} "
        f"-AffectedService {_quote_powershell_literal(affected_service)} "
        f"-Scenario {_quote_powershell_literal(scenario)} "
        "-UseSampleData:$true"
    )

    return [
        powershell_executable,
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-Command",
        command_script,
    ]


def _build_readiness_command(
    *,
    readiness_script_path: Path,
    powershell_executable: str = "powershell",
) -> list[str]:
    command_script = f"& {_quote_powershell_literal(str(readiness_script_path))}"

    return [
        powershell_executable,
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-Command",
        command_script,
    ]


def build_graph_readiness_command(
    *,
    readiness_script_path: Path = GRAPH_READINESS_SCRIPT_PATH,
    powershell_executable: str = "powershell",
) -> list[str]:
    return _build_readiness_command(
        readiness_script_path=readiness_script_path,
        powershell_executable=powershell_executable,
    )


def build_local_readiness_command(
    *,
    readiness_script_path: Path = LOCAL_READINESS_SCRIPT_PATH,
    powershell_executable: str = "powershell",
) -> list[str]:
    return _build_readiness_command(
        readiness_script_path=readiness_script_path,
        powershell_executable=powershell_executable,
    )


def build_ad_readiness_command(
    *,
    readiness_script_path: Path = AD_READINESS_SCRIPT_PATH,
    powershell_executable: str = "powershell",
) -> list[str]:
    return _build_readiness_command(
        readiness_script_path=readiness_script_path,
        powershell_executable=powershell_executable,
    )


def build_dns_diagnostic_command(
    *,
    query: str,
    record_type: str = "A",
    dns_server: Optional[str] = None,
    diagnostic_script_path: Path = DNS_DIAGNOSTIC_SCRIPT_PATH,
    powershell_executable: str = "powershell",
) -> list[str]:
    command_script = (
        f"& {_quote_powershell_literal(str(diagnostic_script_path))} "
        f"-Query {_quote_powershell_literal(query)} "
        f"-RecordType {_quote_powershell_literal(record_type)}"
    )
    if dns_server:
        command_script += f" -DnsServer {_quote_powershell_literal(dns_server)}"

    return [
        powershell_executable,
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-Command",
        command_script,
    ]




def build_ad_user_access_diagnostic_command(
    *,
    user_principal_name: str,
    affected_service: str,
    scenario: str,
    diagnostic_script_path: Path = AD_USER_ACCESS_SCRIPT_PATH,
    powershell_executable: str = "powershell",
) -> list[str]:
    command_script = (
        f"& {_quote_powershell_literal(str(diagnostic_script_path))} "
        f"-UserPrincipalName {_quote_powershell_literal(user_principal_name)} "
        f"-AffectedService {_quote_powershell_literal(affected_service)} "
        f"-Scenario {_quote_powershell_literal(scenario)} "
        "-UseFixtureData:$true"
    )

    return [
        powershell_executable,
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-Command",
        command_script,
    ]




def build_factoryops_computer_diagnostic_command(
    *,
    computer_name: str,
    domain_name: str = "factory.local",
    dns_server: Optional[str] = None,
    expected_ipv4_address: Optional[str] = None,
    diagnostic_script_path: Path = FACTORYOPS_COMPUTER_DIAGNOSTIC_SCRIPT_PATH,
    powershell_executable: str = "powershell",
) -> list[str]:
    command_script = (
        f"& {_quote_powershell_literal(str(diagnostic_script_path))} "
        f"-ComputerName {_quote_powershell_literal(computer_name)} "
        f"-DomainName {_quote_powershell_literal(domain_name)}"
    )
    if dns_server:
        command_script += f" -DnsServer {_quote_powershell_literal(dns_server)}"
    if expected_ipv4_address:
        command_script += f" -ExpectedIpv4Address {_quote_powershell_literal(expected_ipv4_address)}"

    return [
        powershell_executable,
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-Command",
        command_script,
    ]


def build_factoryops_file_share_access_diagnostic_command(
    *,
    share_host: str,
    share_name: str,
    user_sam_account_name: str,
    required_group_sam_account_name: str,
    domain_name: str = "factory.local",
    dns_server: Optional[str] = None,
    observed_access_denied: Optional[bool] = None,
    diagnostic_script_path: Path = FACTORYOPS_FILE_SHARE_DIAGNOSTIC_SCRIPT_PATH,
    powershell_executable: str = "powershell",
) -> list[str]:
    command_script = (
        f"& {_quote_powershell_literal(str(diagnostic_script_path))} "
        f"-ShareHost {_quote_powershell_literal(share_host)} "
        f"-ShareName {_quote_powershell_literal(share_name)} "
        f"-UserSamAccountName {_quote_powershell_literal(user_sam_account_name)} "
        f"-RequiredGroupSamAccountName {_quote_powershell_literal(required_group_sam_account_name)} "
        f"-DomainName {_quote_powershell_literal(domain_name)}"
    )
    if dns_server:
        command_script += f" -DnsServer {_quote_powershell_literal(dns_server)}"
    if observed_access_denied is not None:
        command_script += f" -ObservedAccessDenied:${str(observed_access_denied).lower()}"

    return [
        powershell_executable,
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-Command",
        command_script,
    ]


def _validate_factoryops_computer_diagnostic_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    required_top_level = (
        "status",
        "module",
        "check",
        "input",
        "evidence",
        "findings",
        "safe_next_steps",
        "limitations",
        "read_only_boundary",
    )
    missing = [field for field in required_top_level if field not in payload]
    if missing:
        raise BackendValidationError(
            code="FACTORYOPS_COMPUTER_CONTRACT_INVALID",
            message="The FactoryOps computer diagnostic output is missing required fields.",
            details=[{"missing_fields": missing}],
        )

    if payload["check"] != "factoryops_computer_diagnostic":
        raise BackendValidationError(
            code="FACTORYOPS_COMPUTER_CONTRACT_INVALID",
            message="The FactoryOps computer diagnostic output did not identify the expected check.",
            details=[{"check": payload.get("check")}],
        )

    evidence = payload.get("evidence") or {}
    for required_evidence in ("dns", "active_directory", "reachability"):
        if required_evidence not in evidence:
            raise BackendValidationError(
                code="FACTORYOPS_COMPUTER_CONTRACT_INVALID",
                message="The FactoryOps computer diagnostic output is missing an evidence section.",
                details=[{"missing_evidence_section": required_evidence}],
            )

    boundary = payload.get("read_only_boundary") or {}
    required_false = (
        "remediation_performed",
        "dns_configuration_changed",
        "network_configuration_changed",
        "firewall_configuration_changed",
        "ad_objects_modified",
        "service_control_performed",
        "remote_command_executed",
        "credentials_or_tokens_stored",
    )
    for field in required_false:
        if boundary.get(field) is not False:
            raise BackendValidationError(
                code="FACTORYOPS_COMPUTER_READ_ONLY_BOUNDARY_FAILED",
                message=f"The FactoryOps computer diagnostic did not preserve the {field} boundary.",
            )

    for finding in payload.get("findings") or []:
        required_finding_fields = (
            "finding_id",
            "rule_id",
            "title",
            "severity",
            "confidence",
            "likely_cause",
            "evidence_used",
            "evidence_missing",
            "safe_next_steps",
            "what_not_to_change_yet",
            "limitations",
            "source_module",
        )
        missing_finding = [field for field in required_finding_fields if field not in finding]
        if missing_finding:
            raise BackendValidationError(
                code="FACTORYOPS_COMPUTER_FINDING_CONTRACT_INVALID",
                message="A FactoryOps computer finding is missing required evidence contract fields.",
                details=[{"finding_id": finding.get("finding_id"), "missing_fields": missing_finding}],
            )

    return payload


def _validate_factoryops_file_share_access_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    required_top_level = (
        "status",
        "module",
        "check",
        "input",
        "evidence",
        "findings",
        "safe_next_steps",
        "limitations",
        "read_only_boundary",
    )
    missing = [field for field in required_top_level if field not in payload]
    if missing:
        raise BackendValidationError(
            code="FACTORYOPS_FILE_SHARE_CONTRACT_INVALID",
            message="The FactoryOps file-share access diagnostic output is missing required fields.",
            details=[{"missing_fields": missing}],
        )

    if payload["check"] != "factoryops_file_share_access_diagnostic":
        raise BackendValidationError(
            code="FACTORYOPS_FILE_SHARE_CONTRACT_INVALID",
            message="The FactoryOps file-share access diagnostic output did not identify the expected check.",
            details=[{"check": payload.get("check")}],
        )

    evidence = payload.get("evidence") or {}
    for required_evidence in ("dns", "reachability", "active_directory", "observed_access"):
        if required_evidence not in evidence:
            raise BackendValidationError(
                code="FACTORYOPS_FILE_SHARE_CONTRACT_INVALID",
                message="The FactoryOps file-share access diagnostic output is missing an evidence section.",
                details=[{"missing_evidence_section": required_evidence}],
            )

    boundary = payload.get("read_only_boundary") or {}
    required_false = (
        "remediation_performed",
        "dns_configuration_changed",
        "network_configuration_changed",
        "firewall_configuration_changed",
        "ad_objects_modified",
        "group_membership_changed",
        "ntfs_or_share_permissions_changed",
        "service_control_performed",
        "remote_command_executed",
        "credentials_or_tokens_stored",
        "user_impersonation_performed",
    )
    for field in required_false:
        if boundary.get(field) is not False:
            raise BackendValidationError(
                code="FACTORYOPS_FILE_SHARE_READ_ONLY_BOUNDARY_FAILED",
                message=f"The FactoryOps file-share access diagnostic did not preserve the {field} boundary.",
            )

    for finding in payload.get("findings") or []:
        required_finding_fields = (
            "finding_id",
            "rule_id",
            "title",
            "severity",
            "confidence",
            "likely_cause",
            "evidence_used",
            "evidence_missing",
            "safe_next_steps",
            "what_not_to_change_yet",
            "limitations",
            "source_module",
        )
        missing_finding = [field for field in required_finding_fields if field not in finding]
        if missing_finding:
            raise BackendValidationError(
                code="FACTORYOPS_FILE_SHARE_FINDING_CONTRACT_INVALID",
                message="A FactoryOps file-share access finding is missing required evidence contract fields.",
                details=[{"finding_id": finding.get("finding_id"), "missing_fields": missing_finding}],
            )

    return payload


def _validate_ad_user_access_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    required_top_level = (
        "status",
        "module",
        "check",
        "input",
        "evidence",
        "findings",
        "safe_next_steps",
        "limitations",
        "read_only_boundary",
    )
    missing = [field for field in required_top_level if field not in payload]
    if missing:
        raise BackendValidationError(
            code="AD_USER_ACCESS_CONTRACT_INVALID",
            message="The AD user access diagnostic output is missing required fields.",
            details=[{"missing_fields": missing}],
        )

    if payload["check"] != "ad_user_access_diagnostic":
        raise BackendValidationError(
            code="AD_USER_ACCESS_CONTRACT_INVALID",
            message="The AD user access diagnostic output did not identify the expected check.",
            details=[{"check": payload.get("check")}],
        )

    evidence = payload.get("evidence") or {}
    if evidence.get("fixture_mode") is not True:
        raise BackendValidationError(
            code="AD_USER_ACCESS_CONTRACT_INVALID",
            message="Phase 6 AD user access diagnostics must remain in fixture mode.",
        )
    if evidence.get("real_ad_query_performed") is not False:
        raise BackendValidationError(
            code="AD_USER_ACCESS_REAL_QUERY_BOUNDARY_FAILED",
            message="The AD user access diagnostic did not preserve the no-real-AD-query boundary.",
        )

    boundary = payload.get("read_only_boundary") or {}
    required_false = (
        "remediation_performed",
        "ad_objects_modified",
        "group_membership_changed",
        "password_or_account_state_changed",
        "real_ad_query_performed",
    )
    for field in required_false:
        if boundary.get(field) is not False:
            raise BackendValidationError(
                code="AD_USER_ACCESS_READ_ONLY_BOUNDARY_FAILED",
                message=f"The AD user access diagnostic did not preserve the {field} boundary.",
            )

    for finding in payload.get("findings") or []:
        required_finding_fields = (
            "finding_id",
            "rule_id",
            "title",
            "severity",
            "confidence",
            "likely_cause",
            "evidence_used",
            "evidence_missing",
            "safe_next_steps",
            "what_not_to_change_yet",
            "limitations",
            "source_module",
        )
        missing_finding = [field for field in required_finding_fields if field not in finding]
        if missing_finding:
            raise BackendValidationError(
                code="AD_USER_ACCESS_FINDING_CONTRACT_INVALID",
                message="An AD user access finding is missing required evidence contract fields.",
                details=[{"finding_id": finding.get("finding_id"), "missing_fields": missing_finding}],
            )

    return payload

def _validate_dns_diagnostic_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    required_top_level = (
        "status",
        "module",
        "check",
        "input",
        "evidence",
        "findings",
        "safe_next_steps",
        "limitations",
        "read_only_boundary",
    )
    missing = [field for field in required_top_level if field not in payload]
    if missing:
        raise BackendValidationError(
            code="DNS_DIAGNOSTIC_CONTRACT_INVALID",
            message="The DNS diagnostic output is missing required fields.",
            details=[{"missing_fields": missing}],
        )

    if payload["check"] != "dns_diagnostic":
        raise BackendValidationError(
            code="DNS_DIAGNOSTIC_CONTRACT_INVALID",
            message="The DNS diagnostic output did not identify the expected check.",
            details=[{"check": payload.get("check")}],
        )

    boundary = payload.get("read_only_boundary") or {}
    if boundary.get("remediation_performed") is not False:
        raise BackendValidationError(
            code="DNS_DIAGNOSTIC_READ_ONLY_BOUNDARY_FAILED",
            message="The DNS diagnostic output did not preserve the remediation boundary.",
        )
    if boundary.get("dns_configuration_changed") is not False:
        raise BackendValidationError(
            code="DNS_DIAGNOSTIC_READ_ONLY_BOUNDARY_FAILED",
            message="The DNS diagnostic output did not preserve the no-DNS-change boundary.",
        )
    if boundary.get("network_configuration_changed") is not False:
        raise BackendValidationError(
            code="DNS_DIAGNOSTIC_READ_ONLY_BOUNDARY_FAILED",
            message="The DNS diagnostic output did not preserve the no-network-change boundary.",
        )

    return payload


def _validate_readiness_payload(
    payload: Dict[str, Any],
    *,
    expected_check: str,
    invalid_code: str,
    boundary_failure_code: str,
) -> Dict[str, Any]:
    required_top_level = (
        "status",
        "module",
        "check",
        "evidence",
        "safe_next_steps",
        "limitations",
        "read_only_boundary",
    )
    missing = [field for field in required_top_level if field not in payload]
    if missing:
        raise BackendValidationError(
            code=invalid_code,
            message="The readiness output is missing required fields.",
            details=[{"missing_fields": missing}],
        )

    if payload["check"] != expected_check:
        raise BackendValidationError(
            code=invalid_code,
            message="The readiness output did not identify the expected check.",
            details=[{"check": payload.get("check")}],
        )

    boundary = payload.get("read_only_boundary") or {}
    if boundary.get("remediation_performed") is not False:
        raise BackendValidationError(
            code=boundary_failure_code,
            message="The readiness output did not preserve the remediation boundary.",
        )

    if expected_check == "graph_readiness":
        if "required_scopes" not in payload:
            raise BackendValidationError(
                code=invalid_code,
                message="The Graph readiness output is missing required scopes.",
            )
        if boundary.get("automatic_connection_attempted") is not False:
            raise BackendValidationError(
                code=boundary_failure_code,
                message="The Graph readiness output did not preserve the no-auto-connect boundary.",
            )
        if boundary.get("tenant_wide_scan_performed") is not False:
            raise BackendValidationError(
                code=boundary_failure_code,
                message="The Graph readiness output did not preserve the no-tenant-wide-scan boundary.",
            )

    if expected_check == "local_readiness":
        if boundary.get("network_configuration_changed") is not False:
            raise BackendValidationError(
                code=boundary_failure_code,
                message="The local readiness output did not preserve the no-network-change boundary.",
            )
        if boundary.get("service_control_performed") is not False:
            raise BackendValidationError(
                code=boundary_failure_code,
                message="The local readiness output did not preserve the no-service-control boundary.",
            )

    if expected_check == "ad_readiness":
        if boundary.get("ad_objects_modified") is not False:
            raise BackendValidationError(
                code=boundary_failure_code,
                message="The AD readiness output did not preserve the no-AD-object-change boundary.",
            )
        if boundary.get("group_membership_changed") is not False:
            raise BackendValidationError(
                code=boundary_failure_code,
                message="The AD readiness output did not preserve the no-group-membership-change boundary.",
            )
        if boundary.get("password_or_account_state_changed") is not False:
            raise BackendValidationError(
                code=boundary_failure_code,
                message="The AD readiness output did not preserve the no-password-or-account-state-change boundary.",
            )

    return payload


def _run_readiness_check(
    *,
    readiness_script_path: Path,
    timeout_seconds: int,
    powershell_executable: str,
    missing_code: str,
    timeout_code: str,
    process_failed_code: str,
    invalid_json_code: str,
    validation_failed_code: str,
    expected_check: str,
    invalid_contract_code: str,
    boundary_failure_code: str,
    label: str,
) -> Dict[str, Any]:
    if not readiness_script_path.exists():
        return _runner_error(
            missing_code,
            f"The configured {label} readiness script was not found.",
            details={"readiness_script_path": str(readiness_script_path)},
        )

    command = _build_readiness_command(
        readiness_script_path=readiness_script_path,
        powershell_executable=powershell_executable,
    )

    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            shell=False,
        )
    except subprocess.TimeoutExpired:
        return _runner_error(
            timeout_code,
            f"The {label} readiness process timed out.",
            details={"timeout_seconds": timeout_seconds},
        )

    if completed.returncode != 0:
        return _runner_error(
            process_failed_code,
            f"The {label} readiness process exited with a non-zero status.",
            return_code=completed.returncode,
            stderr=completed.stderr,
        )

    try:
        parsed_stdout = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        return _runner_error(
            invalid_json_code,
            f"The {label} readiness stdout was not valid JSON.",
            stderr=completed.stderr,
            details={"json_error": str(exc)},
        )

    try:
        validated = _validate_readiness_payload(
            parsed_stdout,
            expected_check=expected_check,
            invalid_code=invalid_contract_code,
            boundary_failure_code=boundary_failure_code,
        )
    except BackendValidationError as exc:
        return _runner_error(
            validation_failed_code,
            f"The {label} readiness JSON output failed backend validation.",
            stderr=completed.stderr,
            details=exc.to_dict()["error"],
        )

    return {
        "status": "ok",
        "return_code": completed.returncode,
        "stderr": completed.stderr,
        "result": validated,
    }


def run_graph_readiness_check(
    *,
    readiness_script_path: Path = GRAPH_READINESS_SCRIPT_PATH,
    timeout_seconds: int = COLLECTOR_TIMEOUT_SECONDS,
    powershell_executable: str = "powershell",
) -> Dict[str, Any]:
    return _run_readiness_check(
        readiness_script_path=readiness_script_path,
        timeout_seconds=timeout_seconds,
        powershell_executable=powershell_executable,
        missing_code="GRAPH_READINESS_SCRIPT_NOT_FOUND",
        timeout_code="GRAPH_READINESS_TIMEOUT",
        process_failed_code="GRAPH_READINESS_PROCESS_FAILED",
        invalid_json_code="INVALID_GRAPH_READINESS_STDOUT",
        validation_failed_code="GRAPH_READINESS_OUTPUT_VALIDATION_FAILED",
        expected_check="graph_readiness",
        invalid_contract_code="GRAPH_READINESS_CONTRACT_INVALID",
        boundary_failure_code="GRAPH_READINESS_READ_ONLY_BOUNDARY_FAILED",
        label="Graph",
    )


def run_local_readiness_check(
    *,
    readiness_script_path: Path = LOCAL_READINESS_SCRIPT_PATH,
    timeout_seconds: int = COLLECTOR_TIMEOUT_SECONDS,
    powershell_executable: str = "powershell",
) -> Dict[str, Any]:
    return _run_readiness_check(
        readiness_script_path=readiness_script_path,
        timeout_seconds=timeout_seconds,
        powershell_executable=powershell_executable,
        missing_code="LOCAL_READINESS_SCRIPT_NOT_FOUND",
        timeout_code="LOCAL_READINESS_TIMEOUT",
        process_failed_code="LOCAL_READINESS_PROCESS_FAILED",
        invalid_json_code="INVALID_LOCAL_READINESS_STDOUT",
        validation_failed_code="LOCAL_READINESS_OUTPUT_VALIDATION_FAILED",
        expected_check="local_readiness",
        invalid_contract_code="LOCAL_READINESS_CONTRACT_INVALID",
        boundary_failure_code="LOCAL_READINESS_READ_ONLY_BOUNDARY_FAILED",
        label="local infrastructure",
    )


def run_ad_readiness_check(
    *,
    readiness_script_path: Path = AD_READINESS_SCRIPT_PATH,
    timeout_seconds: int = COLLECTOR_TIMEOUT_SECONDS,
    powershell_executable: str = "powershell",
) -> Dict[str, Any]:
    return _run_readiness_check(
        readiness_script_path=readiness_script_path,
        timeout_seconds=timeout_seconds,
        powershell_executable=powershell_executable,
        missing_code="AD_READINESS_SCRIPT_NOT_FOUND",
        timeout_code="AD_READINESS_TIMEOUT",
        process_failed_code="AD_READINESS_PROCESS_FAILED",
        invalid_json_code="INVALID_AD_READINESS_STDOUT",
        validation_failed_code="AD_READINESS_OUTPUT_VALIDATION_FAILED",
        expected_check="ad_readiness",
        invalid_contract_code="AD_READINESS_CONTRACT_INVALID",
        boundary_failure_code="AD_READINESS_READ_ONLY_BOUNDARY_FAILED",
        label="Active Directory",
    )


def run_dns_diagnostic(
    *,
    query: str,
    record_type: str = "A",
    dns_server: Optional[str] = None,
    diagnostic_script_path: Path = DNS_DIAGNOSTIC_SCRIPT_PATH,
    timeout_seconds: int = COLLECTOR_TIMEOUT_SECONDS,
    powershell_executable: str = "powershell",
) -> Dict[str, Any]:
    if not diagnostic_script_path.exists():
        return _runner_error(
            "DNS_DIAGNOSTIC_SCRIPT_NOT_FOUND",
            "The configured DNS diagnostic script was not found.",
            details={"diagnostic_script_path": str(diagnostic_script_path)},
        )

    command = build_dns_diagnostic_command(
        query=query,
        record_type=record_type,
        dns_server=dns_server,
        diagnostic_script_path=diagnostic_script_path,
        powershell_executable=powershell_executable,
    )

    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            shell=False,
        )
    except subprocess.TimeoutExpired:
        return _runner_error(
            "DNS_DIAGNOSTIC_TIMEOUT",
            "The DNS diagnostic process timed out.",
            details={"timeout_seconds": timeout_seconds},
        )

    if completed.returncode != 0:
        return _runner_error(
            "DNS_DIAGNOSTIC_PROCESS_FAILED",
            "The DNS diagnostic process exited with a non-zero status.",
            return_code=completed.returncode,
            stderr=completed.stderr,
        )

    try:
        parsed_stdout = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        return _runner_error(
            "INVALID_DNS_DIAGNOSTIC_STDOUT",
            "The DNS diagnostic stdout was not valid JSON.",
            stderr=completed.stderr,
            details={"json_error": str(exc)},
        )

    try:
        validated = _validate_dns_diagnostic_payload(parsed_stdout)
    except BackendValidationError as exc:
        return _runner_error(
            "DNS_DIAGNOSTIC_OUTPUT_VALIDATION_FAILED",
            "The DNS diagnostic JSON output failed backend validation.",
            stderr=completed.stderr,
            details=exc.to_dict()["error"],
        )

    return {
        "status": "ok",
        "return_code": completed.returncode,
        "stderr": completed.stderr,
        "result": validated,
    }




def run_factoryops_computer_diagnostic(
    *,
    computer_name: str,
    domain_name: str = "factory.local",
    dns_server: Optional[str] = None,
    expected_ipv4_address: Optional[str] = None,
    diagnostic_script_path: Path = FACTORYOPS_COMPUTER_DIAGNOSTIC_SCRIPT_PATH,
    timeout_seconds: int = COLLECTOR_TIMEOUT_SECONDS,
    powershell_executable: str = "powershell",
) -> Dict[str, Any]:
    if not diagnostic_script_path.exists():
        return _runner_error(
            "FACTORYOPS_COMPUTER_SCRIPT_NOT_FOUND",
            "The configured FactoryOps computer diagnostic script was not found.",
            details={"diagnostic_script_path": str(diagnostic_script_path)},
        )

    command = build_factoryops_computer_diagnostic_command(
        computer_name=computer_name,
        domain_name=domain_name,
        dns_server=dns_server,
        expected_ipv4_address=expected_ipv4_address,
        diagnostic_script_path=diagnostic_script_path,
        powershell_executable=powershell_executable,
    )

    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            shell=False,
        )
    except subprocess.TimeoutExpired:
        return _runner_error(
            "FACTORYOPS_COMPUTER_TIMEOUT",
            "The FactoryOps computer diagnostic process timed out.",
            details={"timeout_seconds": timeout_seconds},
        )

    if completed.returncode != 0:
        return _runner_error(
            "FACTORYOPS_COMPUTER_PROCESS_FAILED",
            "The FactoryOps computer diagnostic process exited with a non-zero status.",
            return_code=completed.returncode,
            stderr=completed.stderr,
        )

    try:
        parsed_stdout = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        return _runner_error(
            "INVALID_FACTORYOPS_COMPUTER_STDOUT",
            "The FactoryOps computer diagnostic stdout was not valid JSON.",
            stderr=completed.stderr,
            details={"json_error": str(exc)},
        )

    try:
        validated = _validate_factoryops_computer_diagnostic_payload(parsed_stdout)
    except BackendValidationError as exc:
        return _runner_error(
            "FACTORYOPS_COMPUTER_OUTPUT_VALIDATION_FAILED",
            "The FactoryOps computer diagnostic JSON output failed backend validation.",
            stderr=completed.stderr,
            details=exc.to_dict()["error"],
        )

    return {
        "status": "ok",
        "return_code": completed.returncode,
        "stderr": completed.stderr,
        "result": validated,
    }


def run_factoryops_file_share_access_diagnostic(
    *,
    share_host: str,
    share_name: str,
    user_sam_account_name: str,
    required_group_sam_account_name: str,
    domain_name: str = "factory.local",
    dns_server: Optional[str] = None,
    observed_access_denied: Optional[bool] = None,
    diagnostic_script_path: Path = FACTORYOPS_FILE_SHARE_DIAGNOSTIC_SCRIPT_PATH,
    timeout_seconds: int = COLLECTOR_TIMEOUT_SECONDS,
    powershell_executable: str = "powershell",
) -> Dict[str, Any]:
    if not diagnostic_script_path.exists():
        return _runner_error(
            "FACTORYOPS_FILE_SHARE_SCRIPT_NOT_FOUND",
            "The configured FactoryOps file-share access diagnostic script was not found.",
            details={"diagnostic_script_path": str(diagnostic_script_path)},
        )

    command = build_factoryops_file_share_access_diagnostic_command(
        share_host=share_host,
        share_name=share_name,
        user_sam_account_name=user_sam_account_name,
        required_group_sam_account_name=required_group_sam_account_name,
        domain_name=domain_name,
        dns_server=dns_server,
        observed_access_denied=observed_access_denied,
        diagnostic_script_path=diagnostic_script_path,
        powershell_executable=powershell_executable,
    )

    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            shell=False,
        )
    except subprocess.TimeoutExpired:
        return _runner_error(
            "FACTORYOPS_FILE_SHARE_TIMEOUT",
            "The FactoryOps file-share access diagnostic process timed out.",
            details={"timeout_seconds": timeout_seconds},
        )

    if completed.returncode != 0:
        return _runner_error(
            "FACTORYOPS_FILE_SHARE_PROCESS_FAILED",
            "The FactoryOps file-share access diagnostic process exited with a non-zero status.",
            return_code=completed.returncode,
            stderr=completed.stderr,
        )

    try:
        parsed_stdout = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        return _runner_error(
            "INVALID_FACTORYOPS_FILE_SHARE_STDOUT",
            "The FactoryOps file-share access diagnostic stdout was not valid JSON.",
            stderr=completed.stderr,
            details={"json_error": str(exc)},
        )

    try:
        validated = _validate_factoryops_file_share_access_payload(parsed_stdout)
    except BackendValidationError as exc:
        return _runner_error(
            "FACTORYOPS_FILE_SHARE_OUTPUT_VALIDATION_FAILED",
            "The FactoryOps file-share access diagnostic JSON output failed backend validation.",
            stderr=completed.stderr,
            details=exc.to_dict()["error"],
        )

    return {
        "status": "ok",
        "return_code": completed.returncode,
        "stderr": completed.stderr,
        "result": validated,
    }


def run_ad_user_access_diagnostic(
    *,
    user_principal_name: str,
    affected_service: str,
    scenario: str,
    diagnostic_script_path: Path = AD_USER_ACCESS_SCRIPT_PATH,
    timeout_seconds: int = COLLECTOR_TIMEOUT_SECONDS,
    powershell_executable: str = "powershell",
) -> Dict[str, Any]:
    if not diagnostic_script_path.exists():
        return _runner_error(
            "AD_USER_ACCESS_SCRIPT_NOT_FOUND",
            "The configured AD user access diagnostic script was not found.",
            details={"diagnostic_script_path": str(diagnostic_script_path)},
        )

    command = build_ad_user_access_diagnostic_command(
        user_principal_name=user_principal_name,
        affected_service=affected_service,
        scenario=scenario,
        diagnostic_script_path=diagnostic_script_path,
        powershell_executable=powershell_executable,
    )

    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            shell=False,
        )
    except subprocess.TimeoutExpired:
        return _runner_error(
            "AD_USER_ACCESS_TIMEOUT",
            "The AD user access diagnostic process timed out.",
            details={"timeout_seconds": timeout_seconds},
        )

    if completed.returncode != 0:
        return _runner_error(
            "AD_USER_ACCESS_PROCESS_FAILED",
            "The AD user access diagnostic process exited with a non-zero status.",
            return_code=completed.returncode,
            stderr=completed.stderr,
        )

    try:
        parsed_stdout = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        return _runner_error(
            "INVALID_AD_USER_ACCESS_STDOUT",
            "The AD user access diagnostic stdout was not valid JSON.",
            stderr=completed.stderr,
            details={"json_error": str(exc)},
        )

    try:
        validated = _validate_ad_user_access_payload(parsed_stdout)
    except BackendValidationError as exc:
        return _runner_error(
            "AD_USER_ACCESS_OUTPUT_VALIDATION_FAILED",
            "The AD user access diagnostic JSON output failed backend validation.",
            stderr=completed.stderr,
            details=exc.to_dict()["error"],
        )

    return {
        "status": "ok",
        "return_code": completed.returncode,
        "stderr": completed.stderr,
        "result": validated,
    }


def run_m365_access_collector(
    *,
    user_principal_name: str,
    affected_service: str,
    scenario: str,
    collector_script_path: Path = COLLECTOR_SCRIPT_PATH,
    timeout_seconds: int = COLLECTOR_TIMEOUT_SECONDS,
    powershell_executable: str = "powershell",
) -> Dict[str, Any]:
    if not collector_script_path.exists():
        return _runner_error(
            "COLLECTOR_SCRIPT_NOT_FOUND",
            "The configured collector script was not found.",
            details={"collector_script_path": str(collector_script_path)},
        )

    command = build_collector_command(
        user_principal_name=user_principal_name,
        affected_service=affected_service,
        scenario=scenario,
        collector_script_path=collector_script_path,
        powershell_executable=powershell_executable,
    )

    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            shell=False,
        )
    except subprocess.TimeoutExpired:
        return _runner_error(
            "COLLECTOR_TIMEOUT",
            "The collector process timed out.",
            details={"timeout_seconds": timeout_seconds},
        )

    if completed.returncode != 0:
        return _runner_error(
            "COLLECTOR_PROCESS_FAILED",
            "The collector process exited with a non-zero status.",
            return_code=completed.returncode,
            stderr=completed.stderr,
        )

    try:
        parsed_stdout = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        return _runner_error(
            "INVALID_COLLECTOR_STDOUT",
            "The collector stdout was not valid JSON.",
            stderr=completed.stderr,
            details={"json_error": str(exc)},
        )

    try:
        validated = validate_collector_result(parsed_stdout)
    except BackendValidationError as exc:
        return _runner_error(
            "COLLECTOR_OUTPUT_VALIDATION_FAILED",
            "The collector JSON output failed backend validation.",
            stderr=completed.stderr,
            details=exc.to_dict()["error"],
        )

    if isinstance(validated, CollectorErrorResult):
        return {
            "status": "collector_error",
            "return_code": completed.returncode,
            "stderr": completed.stderr,
            "collector_error": _model_to_dict(validated),
        }

    if isinstance(validated, CollectorResult):
        return {
            "status": "ok",
            "return_code": completed.returncode,
            "stderr": completed.stderr,
            "result": _model_to_dict(validated),
        }

    return _runner_error(
        "UNEXPECTED_COLLECTOR_VALIDATION_RESULT",
        "Collector validation returned an unexpected result type.",
    )
