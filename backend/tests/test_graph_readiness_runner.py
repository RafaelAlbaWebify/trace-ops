import json
import subprocess
from pathlib import Path
from unittest.mock import patch

from app.collector_runner import build_graph_readiness_command, run_graph_readiness_check
from app.config import GRAPH_READINESS_SCRIPT_PATH


def readiness_payload(status="warning"):
    return {
        "status": status,
        "module": "m365-access-path-analyzer",
        "check": "graph_readiness",
        "generated_at": "2026-06-03T10:30:00Z",
        "required_scopes": ["User.Read.All", "AuditLog.Read.All", "LicenseAssignment.Read.All"],
        "evidence": {
            "graph_module_available": True,
            "connected_to_graph": False,
            "tenant_id": None,
            "account": None,
            "available_scopes": [],
            "missing_scopes": ["User.Read.All", "AuditLog.Read.All", "LicenseAssignment.Read.All"],
        },
        "safe_next_steps": ["Sign in explicitly from your own PowerShell session before running real diagnostics."],
        "limitations": ["TRACE did not create a connection automatically."],
        "read_only_boundary": {
            "remediation_performed": False,
            "automatic_connection_attempted": False,
            "tenant_wide_scan_performed": False,
        },
    }


def test_graph_readiness_command_uses_argument_array_and_no_shell_script_writes():
    command = build_graph_readiness_command(readiness_script_path=GRAPH_READINESS_SCRIPT_PATH)

    assert isinstance(command, list)
    assert "-Command" in command
    assert str(GRAPH_READINESS_SCRIPT_PATH) in command[5]
    assert "Connect-MgGraph" not in command[5]
    assert "Set-Mg" not in command[5]
    assert "New-Mg" not in command[5]
    assert "Update-Mg" not in command[5]
    assert "Remove-Mg" not in command[5]


def test_graph_readiness_success_payload_is_returned():
    completed = subprocess.CompletedProcess(
        args=["powershell"],
        returncode=0,
        stdout=json.dumps(readiness_payload()),
        stderr="",
    )

    with patch("app.collector_runner.subprocess.run", return_value=completed) as run_mock:
        result = run_graph_readiness_check()

    assert result["status"] == "ok"
    assert result["result"]["check"] == "graph_readiness"
    assert result["result"]["evidence"]["connected_to_graph"] is False
    _, kwargs = run_mock.call_args
    assert kwargs["shell"] is False


def test_graph_readiness_missing_script_is_controlled_error():
    result = run_graph_readiness_check(readiness_script_path=Path("missing-readiness.ps1"))

    assert result["status"] == "error"
    assert result["error"]["code"] == "GRAPH_READINESS_SCRIPT_NOT_FOUND"


def test_graph_readiness_non_zero_exit_is_controlled_error():
    completed = subprocess.CompletedProcess(args=["powershell"], returncode=1, stdout="", stderr="failed")

    with patch("app.collector_runner.subprocess.run", return_value=completed):
        result = run_graph_readiness_check()

    assert result["status"] == "error"
    assert result["error"]["code"] == "GRAPH_READINESS_PROCESS_FAILED"
    assert result["error"]["return_code"] == 1


def test_graph_readiness_invalid_json_is_controlled_error():
    completed = subprocess.CompletedProcess(args=["powershell"], returncode=0, stdout="not json", stderr="")

    with patch("app.collector_runner.subprocess.run", return_value=completed):
        result = run_graph_readiness_check()

    assert result["status"] == "error"
    assert result["error"]["code"] == "INVALID_GRAPH_READINESS_STDOUT"


def test_graph_readiness_rejects_boundary_violation():
    payload = readiness_payload()
    payload["read_only_boundary"]["automatic_connection_attempted"] = True
    completed = subprocess.CompletedProcess(args=["powershell"], returncode=0, stdout=json.dumps(payload), stderr="")

    with patch("app.collector_runner.subprocess.run", return_value=completed):
        result = run_graph_readiness_check()

    assert result["status"] == "error"
    assert result["error"]["code"] == "GRAPH_READINESS_OUTPUT_VALIDATION_FAILED"
