import json
import subprocess
from pathlib import Path
from unittest.mock import patch

from app.collector_runner import build_factoryops_computer_diagnostic_command, run_factoryops_computer_diagnostic


def _valid_payload() -> dict:
    return {
        "status": "success",
        "module": "factoryops-computer-diagnostic",
        "check": "factoryops_computer_diagnostic",
        "input": {
            "computer_name": "office-pc01",
            "computer_fqdn": "office-pc01.factory.local",
            "domain_name": "factory.local",
            "dns_server": "10.40.10.10",
            "expected_ipv4_address": "10.20.10.100",
        },
        "evidence": {
            "dns": {
                "query": "office-pc01.factory.local",
                "server": "10.40.10.10",
                "records": [{"name": "office-pc01.factory.local", "type": "A", "value": "10.20.10.100"}],
                "resolved_ipv4_addresses": ["10.20.10.100"],
                "reverse_records": [],
                "error": None,
            },
            "active_directory": {
                "module_available": True,
                "computer_found": True,
                "computer": {
                    "name": "OFFICE-PC01",
                    "dns_host_name": "office-pc01.factory.local",
                    "enabled": True,
                    "distinguished_name": "CN=OFFICE-PC01,CN=Computers,DC=factory,DC=local",
                    "operating_system": "Windows Server 2022",
                    "last_logon_date": None,
                    "ipv4_address": "10.20.10.100",
                },
                "error": None,
            },
            "reachability": {
                "target": "office-pc01.factory.local",
                "icmp_reachable": True,
                "port_probes": [
                    {"name": "smb", "port": 445, "reachable": True},
                    {"name": "rdp", "port": 3389, "reachable": False},
                ],
            },
        },
        "findings": [],
        "safe_next_steps": ["Review DNS, AD computer, and connectivity evidence before changing settings."],
        "limitations": ["TRACE collected read-only FactoryOps computer evidence only."],
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


def test_build_factoryops_computer_command_quotes_inputs() -> None:
    command = build_factoryops_computer_diagnostic_command(
        computer_name="office-pc01",
        domain_name="factory.local",
        dns_server="10.40.10.10",
        expected_ipv4_address="10.20.10.100",
        diagnostic_script_path=Path("collector/Invoke-TraceFactoryOpsComputerDiagnostic.ps1"),
    )

    assert command[:4] == ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass"]
    assert "Invoke-TraceFactoryOpsComputerDiagnostic.ps1" in command[5]
    assert "-ComputerName 'office-pc01'" in command[5]
    assert "-DomainName 'factory.local'" in command[5]
    assert "-DnsServer '10.40.10.10'" in command[5]
    assert "-ExpectedIpv4Address '10.20.10.100'" in command[5]


def test_missing_factoryops_computer_script_returns_error(tmp_path: Path) -> None:
    result = run_factoryops_computer_diagnostic(
        computer_name="office-pc01",
        diagnostic_script_path=tmp_path / "missing.ps1",
    )

    assert result["status"] == "error"
    assert result["error"]["code"] == "FACTORYOPS_COMPUTER_SCRIPT_NOT_FOUND"


@patch("app.collector_runner.subprocess.run")
def test_factoryops_computer_success_validates_payload(mock_run, tmp_path: Path) -> None:
    script = tmp_path / "collector.ps1"
    script.write_text("Write-Output '{}'", encoding="utf-8")
    mock_run.return_value = subprocess.CompletedProcess(
        args=[],
        returncode=0,
        stdout=json.dumps(_valid_payload()),
        stderr="",
    )

    result = run_factoryops_computer_diagnostic(
        computer_name="office-pc01",
        domain_name="factory.local",
        dns_server="10.40.10.10",
        expected_ipv4_address="10.20.10.100",
        diagnostic_script_path=script,
    )

    assert result["status"] == "ok"
    assert result["result"]["check"] == "factoryops_computer_diagnostic"
    assert result["result"]["evidence"]["dns"]["resolved_ipv4_addresses"] == ["10.20.10.100"]


@patch("app.collector_runner.subprocess.run")
def test_factoryops_computer_invalid_json_returns_error(mock_run, tmp_path: Path) -> None:
    script = tmp_path / "collector.ps1"
    script.write_text("broken", encoding="utf-8")
    mock_run.return_value = subprocess.CompletedProcess(args=[], returncode=0, stdout="not-json", stderr="")

    result = run_factoryops_computer_diagnostic(computer_name="office-pc01", diagnostic_script_path=script)

    assert result["status"] == "error"
    assert result["error"]["code"] == "INVALID_FACTORYOPS_COMPUTER_STDOUT"


@patch("app.collector_runner.subprocess.run")
def test_factoryops_computer_boundary_is_enforced(mock_run, tmp_path: Path) -> None:
    script = tmp_path / "collector.ps1"
    script.write_text("Write-Output '{}'", encoding="utf-8")
    payload = _valid_payload()
    payload["read_only_boundary"]["ad_objects_modified"] = True
    mock_run.return_value = subprocess.CompletedProcess(args=[], returncode=0, stdout=json.dumps(payload), stderr="")

    result = run_factoryops_computer_diagnostic(computer_name="office-pc01", diagnostic_script_path=script)

    assert result["status"] == "error"
    assert result["error"]["code"] == "FACTORYOPS_COMPUTER_OUTPUT_VALIDATION_FAILED"
