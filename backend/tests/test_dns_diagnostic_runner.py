import json
import subprocess
from pathlib import Path
from unittest.mock import patch

from app.collector_runner import build_dns_diagnostic_command, run_dns_diagnostic
from app.config import DNS_DIAGNOSTIC_SCRIPT_PATH


def dns_payload(status="success"):
    return {
        "status": status,
        "module": "dns-diagnostics",
        "check": "dns_diagnostic",
        "generated_at": "2026-06-03T11:00:00Z",
        "input": {"query": "dc01.factory.local", "record_type": "A", "dns_server": "192.168.10.10"},
        "evidence": {
            "query": "dc01.factory.local",
            "record_type": "A",
            "dns_server": "192.168.10.10",
            "resolver": "192.168.10.10",
            "resolved": True,
            "records": ["192.168.10.10"],
            "record_count": 1,
            "error": None,
        },
        "findings": [],
        "safe_next_steps": ["Continue checking service reachability if the issue persists."],
        "limitations": ["DNS diagnostics only verifies name resolution evidence."],
        "read_only_boundary": {
            "remediation_performed": False,
            "dns_configuration_changed": False,
            "network_configuration_changed": False,
        },
    }


def test_dns_diagnostic_command_uses_argument_array_and_no_shell():
    command = build_dns_diagnostic_command(
        query="dc01.factory.local",
        record_type="A",
        dns_server="192.168.10.10",
        diagnostic_script_path=DNS_DIAGNOSTIC_SCRIPT_PATH,
    )

    assert isinstance(command, list)
    assert "-Command" in command
    assert str(DNS_DIAGNOSTIC_SCRIPT_PATH) in command[5]
    assert "dc01.factory.local" in command[5]
    assert "192.168.10.10" in command[5]


def test_dns_diagnostic_success_payload_is_returned():
    completed = subprocess.CompletedProcess(
        args=["powershell"],
        returncode=0,
        stdout=json.dumps(dns_payload()),
        stderr="",
    )

    with patch("app.collector_runner.subprocess.run", return_value=completed) as run_mock:
        result = run_dns_diagnostic(query="dc01.factory.local", record_type="A", dns_server="192.168.10.10")

    assert result["status"] == "ok"
    assert result["result"]["check"] == "dns_diagnostic"
    assert result["result"]["evidence"]["resolved"] is True
    _, kwargs = run_mock.call_args
    assert kwargs["shell"] is False


def test_dns_diagnostic_missing_script_is_controlled_error():
    result = run_dns_diagnostic(query="dc01.factory.local", diagnostic_script_path=Path("missing-dns-diagnostic.ps1"))

    assert result["status"] == "error"
    assert result["error"]["code"] == "DNS_DIAGNOSTIC_SCRIPT_NOT_FOUND"


def test_dns_diagnostic_invalid_json_is_controlled_error():
    completed = subprocess.CompletedProcess(args=["powershell"], returncode=0, stdout="not json", stderr="")

    with patch("app.collector_runner.subprocess.run", return_value=completed):
        result = run_dns_diagnostic(query="dc01.factory.local")

    assert result["status"] == "error"
    assert result["error"]["code"] == "INVALID_DNS_DIAGNOSTIC_STDOUT"


def test_dns_diagnostic_rejects_boundary_violation():
    payload = dns_payload()
    payload["read_only_boundary"]["dns_configuration_changed"] = True
    completed = subprocess.CompletedProcess(args=["powershell"], returncode=0, stdout=json.dumps(payload), stderr="")

    with patch("app.collector_runner.subprocess.run", return_value=completed):
        result = run_dns_diagnostic(query="dc01.factory.local")

    assert result["status"] == "error"
    assert result["error"]["code"] == "DNS_DIAGNOSTIC_OUTPUT_VALIDATION_FAILED"
