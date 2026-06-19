import json
import subprocess
from pathlib import Path
from unittest.mock import patch

from app.collector_runner import (
    build_factoryops_file_share_access_diagnostic_command,
    run_factoryops_file_share_access_diagnostic,
)


def _valid_payload() -> dict:
    return {
        "status": "finding",
        "module": "factoryops-file-share-access-diagnostic",
        "check": "factoryops_file_share_access_diagnostic",
        "input": {
            "share_host": "filesrv01",
            "share_host_fqdn": "filesrv01.factory.local",
            "share_name": "Finance",
            "share_unc_path": "\\\\filesrv01.factory.local\\Finance",
            "user_sam_account_name": "finance.noaccess",
            "required_group_sam_account_name": "GG_FINANCE_SHARE_READ",
            "domain_name": "factory.local",
            "dns_server": "10.40.10.10",
            "observed_access_denied": True,
        },
        "evidence": {
            "dns": {"records": [], "resolved_ipv4_addresses": ["10.40.10.20"], "error": None},
            "reachability": {"target": "filesrv01.factory.local", "smb_tcp_445_reachable": True},
            "active_directory": {
                "module_available": True,
                "user_found": True,
                "user": None,
                "required_group_found": True,
                "required_group": None,
                "membership_proven": False,
                "user_error": None,
                "group_error": None,
            },
            "observed_access": {"access_denied": True, "supplied_by_operator": True},
        },
        "findings": [],
        "safe_next_steps": ["Review evidence before changing membership."],
        "limitations": ["Read-only diagnostic."],
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


def test_build_factoryops_file_share_command_quotes_inputs() -> None:
    command = build_factoryops_file_share_access_diagnostic_command(
        share_host="filesrv01",
        share_name="Finance",
        user_sam_account_name="finance.noaccess",
        required_group_sam_account_name="GG_FINANCE_SHARE_READ",
        domain_name="factory.local",
        dns_server="10.40.10.10",
        observed_access_denied=True,
        diagnostic_script_path=Path("collector/Invoke-TraceFactoryOpsFileShareAccessDiagnostic.ps1"),
    )

    assert command[:4] == ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass"]
    assert "Invoke-TraceFactoryOpsFileShareAccessDiagnostic.ps1" in command[5]
    assert "-ShareHost 'filesrv01'" in command[5]
    assert "-ShareName 'Finance'" in command[5]
    assert "-UserSamAccountName 'finance.noaccess'" in command[5]
    assert "-RequiredGroupSamAccountName 'GG_FINANCE_SHARE_READ'" in command[5]
    assert "-ObservedAccessDenied:$true" in command[5]


def test_missing_factoryops_file_share_script_returns_error(tmp_path: Path) -> None:
    result = run_factoryops_file_share_access_diagnostic(
        share_host="filesrv01",
        share_name="Finance",
        user_sam_account_name="finance.noaccess",
        required_group_sam_account_name="GG_FINANCE_SHARE_READ",
        diagnostic_script_path=tmp_path / "missing.ps1",
    )

    assert result["status"] == "error"
    assert result["error"]["code"] == "FACTORYOPS_FILE_SHARE_SCRIPT_NOT_FOUND"


@patch("app.collector_runner.subprocess.run")
def test_factoryops_file_share_success_validates_payload(mock_run, tmp_path: Path) -> None:
    script = tmp_path / "collector.ps1"
    script.write_text("Write-Output '{}'", encoding="utf-8")
    mock_run.return_value = subprocess.CompletedProcess(args=[], returncode=0, stdout=json.dumps(_valid_payload()), stderr="")

    result = run_factoryops_file_share_access_diagnostic(
        share_host="filesrv01",
        share_name="Finance",
        user_sam_account_name="finance.noaccess",
        required_group_sam_account_name="GG_FINANCE_SHARE_READ",
        diagnostic_script_path=script,
    )

    assert result["status"] == "ok"
    assert result["result"]["check"] == "factoryops_file_share_access_diagnostic"
    assert result["result"]["evidence"]["reachability"]["smb_tcp_445_reachable"] is True


@patch("app.collector_runner.subprocess.run")
def test_factoryops_file_share_boundary_is_enforced(mock_run, tmp_path: Path) -> None:
    script = tmp_path / "collector.ps1"
    script.write_text("Write-Output '{}'", encoding="utf-8")
    payload = _valid_payload()
    payload["read_only_boundary"]["group_membership_changed"] = True
    mock_run.return_value = subprocess.CompletedProcess(args=[], returncode=0, stdout=json.dumps(payload), stderr="")

    result = run_factoryops_file_share_access_diagnostic(
        share_host="filesrv01",
        share_name="Finance",
        user_sam_account_name="finance.noaccess",
        required_group_sam_account_name="GG_FINANCE_SHARE_READ",
        diagnostic_script_path=script,
    )

    assert result["status"] == "error"
    assert result["error"]["code"] == "FACTORYOPS_FILE_SHARE_OUTPUT_VALIDATION_FAILED"
