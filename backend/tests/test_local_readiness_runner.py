import json
import subprocess
from pathlib import Path
from unittest.mock import patch

from app.collector_runner import build_local_readiness_command, run_local_readiness_check
from app.config import LOCAL_READINESS_SCRIPT_PATH


def local_payload(status="warning"):
    return {
        "status": status,
        "module": "local-infrastructure-readiness",
        "check": "local_readiness",
        "generated_at": "2026-06-03T10:30:00Z",
        "evidence": {
            "hostname": "TRACE-CLIENT01",
            "os_description": "Windows 11 Pro",
            "powershell_version": "5.1.19041.1",
            "domain_joined": False,
            "domain_name": None,
            "workgroup": "WORKGROUP",
            "network_adapters": [
                {
                    "name": "Ethernet0",
                    "status": "Up",
                    "interface_description": "VMware virtual adapter",
                    "mac_address": "00-11-22-33-44-55",
                }
            ],
            "ip_configurations": [
                {
                    "interface_alias": "Ethernet0",
                    "ipv4_addresses": ["192.168.10.20"],
                    "dns_servers": ["192.168.10.10"],
                    "default_gateway": "192.168.10.1",
                }
            ],
            "dns_probe": {
                "query": "localhost",
                "succeeded": True,
                "addresses": ["127.0.0.1"],
                "error": None,
            },
            "gateway_probe": {
                "target": "192.168.10.1",
                "reachable": True,
                "error": None,
            },
        },
        "safe_next_steps": ["For AD diagnostics, run TRACE from a domain-joined machine."],
        "limitations": [],
        "read_only_boundary": {
            "remediation_performed": False,
            "network_configuration_changed": False,
            "service_control_performed": False,
        },
    }


def test_local_readiness_command_uses_argument_array_and_no_shell_script_writes():
    command = build_local_readiness_command(readiness_script_path=LOCAL_READINESS_SCRIPT_PATH)

    assert isinstance(command, list)
    assert "-Command" in command
    assert str(LOCAL_READINESS_SCRIPT_PATH) in command[5]
    assert "Set-DnsClientServerAddress" not in command[5]
    assert "New-NetIPAddress" not in command[5]
    assert "Restart-Service" not in command[5]


def test_local_readiness_success_payload_is_returned():
    completed = subprocess.CompletedProcess(
        args=["powershell"],
        returncode=0,
        stdout=json.dumps(local_payload()),
        stderr="",
    )

    with patch("app.collector_runner.subprocess.run", return_value=completed) as run_mock:
        result = run_local_readiness_check()

    assert result["status"] == "ok"
    assert result["result"]["check"] == "local_readiness"
    assert result["result"]["evidence"]["hostname"] == "TRACE-CLIENT01"
    _, kwargs = run_mock.call_args
    assert kwargs["shell"] is False


def test_local_readiness_missing_script_is_controlled_error():
    result = run_local_readiness_check(readiness_script_path=Path("missing-local-readiness.ps1"))

    assert result["status"] == "error"
    assert result["error"]["code"] == "LOCAL_READINESS_SCRIPT_NOT_FOUND"


def test_local_readiness_non_zero_exit_is_controlled_error():
    completed = subprocess.CompletedProcess(args=["powershell"], returncode=1, stdout="", stderr="failed")

    with patch("app.collector_runner.subprocess.run", return_value=completed):
        result = run_local_readiness_check()

    assert result["status"] == "error"
    assert result["error"]["code"] == "LOCAL_READINESS_PROCESS_FAILED"
    assert result["error"]["return_code"] == 1


def test_local_readiness_invalid_json_is_controlled_error():
    completed = subprocess.CompletedProcess(args=["powershell"], returncode=0, stdout="not json", stderr="")

    with patch("app.collector_runner.subprocess.run", return_value=completed):
        result = run_local_readiness_check()

    assert result["status"] == "error"
    assert result["error"]["code"] == "INVALID_LOCAL_READINESS_STDOUT"


def test_local_readiness_rejects_boundary_violation():
    payload = local_payload()
    payload["read_only_boundary"]["network_configuration_changed"] = True
    completed = subprocess.CompletedProcess(args=["powershell"], returncode=0, stdout=json.dumps(payload), stderr="")

    with patch("app.collector_runner.subprocess.run", return_value=completed):
        result = run_local_readiness_check()

    assert result["status"] == "error"
    assert result["error"]["code"] == "LOCAL_READINESS_OUTPUT_VALIDATION_FAILED"
