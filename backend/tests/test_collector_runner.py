import json
import subprocess
from pathlib import Path
from unittest.mock import patch

from app.collector_runner import build_collector_command, run_m365_access_collector
from app.config import COLLECTOR_SCRIPT_PATH


def test_successful_sample_scenario_execution():
    result = run_m365_access_collector(
        user_principal_name="jane.doe@example.com",
        affected_service="Microsoft Teams",
        scenario="ca-device-noncompliant",
    )

    assert result["status"] == "ok"
    assert result["result"]["scenario_id"] == "ca-device-noncompliant"
    assert result["result"]["module"] == "m365-access-path-analyzer"


def test_invalid_scenario_returns_controlled_error():
    result = run_m365_access_collector(
        user_principal_name="jane.doe@example.com",
        affected_service="Microsoft Teams",
        scenario="not-a-scenario",
    )

    assert result["status"] == "collector_error"
    assert result["collector_error"]["error"]["code"] == "INVALID_SAMPLE_SCENARIO"


def test_malformed_json_from_subprocess_is_handled_clearly():
    completed = subprocess.CompletedProcess(
        args=["powershell"],
        returncode=0,
        stdout="not json",
        stderr="",
    )

    with patch("app.collector_runner.subprocess.run", return_value=completed):
        result = run_m365_access_collector(
            user_principal_name="jane.doe@example.com",
            affected_service="Microsoft Teams",
            scenario="account-disabled",
        )

    assert result["status"] == "error"
    assert result["error"]["code"] == "INVALID_COLLECTOR_STDOUT"


def test_non_zero_subprocess_return_code_is_handled_clearly():
    completed = subprocess.CompletedProcess(
        args=["powershell"],
        returncode=1,
        stdout="",
        stderr="collector failed",
    )

    with patch("app.collector_runner.subprocess.run", return_value=completed):
        result = run_m365_access_collector(
            user_principal_name="jane.doe@example.com",
            affected_service="Microsoft Teams",
            scenario="account-disabled",
        )

    assert result["status"] == "error"
    assert result["error"]["code"] == "COLLECTOR_PROCESS_FAILED"
    assert result["error"]["return_code"] == 1
    assert result["error"]["stderr"] == "collector failed"


def test_missing_collector_script_is_handled_clearly():
    result = run_m365_access_collector(
        user_principal_name="jane.doe@example.com",
        affected_service="Microsoft Teams",
        scenario="account-disabled",
        collector_script_path=Path("missing-collector.ps1"),
    )

    assert result["status"] == "error"
    assert result["error"]["code"] == "COLLECTOR_SCRIPT_NOT_FOUND"


def test_command_construction_forces_sample_mode_and_uses_argument_array():
    command = build_collector_command(
        user_principal_name="jane.doe@example.com",
        affected_service="Microsoft Teams",
        scenario="account-disabled",
        collector_script_path=COLLECTOR_SCRIPT_PATH,
    )

    assert isinstance(command, list)
    assert "-UseSampleData:$true" in command[5]
    assert "-Command" in command
    assert str(COLLECTOR_SCRIPT_PATH) in command[5]
    assert "'Microsoft Teams'" in command[5]


def test_subprocess_does_not_use_shell_true():
    completed = subprocess.CompletedProcess(
        args=["powershell"],
        returncode=0,
        stdout=json.dumps(
            {
                "scenario_id": "account-disabled",
                "module": "m365-access-path-analyzer",
                "input": {
                    "user_principal_name": "jane.doe@example.com",
                    "affected_service": "Microsoft Teams",
                },
                "identity": {
                    "user_exists": True,
                    "account_enabled": False,
                    "user_type": "Member",
                    "display_name": "Jane Doe",
                },
                "licenses": {
                    "has_relevant_license": True,
                    "assigned_skus": ["SPE_E3"],
                },
                "signin_logs": {
                    "available": True,
                    "recent_events": [],
                },
                "conditional_access": {
                    "details_available": False,
                    "policies": [],
                },
                "device": {
                    "evidence_available": False,
                },
            }
        ),
        stderr="",
    )

    with patch("app.collector_runner.subprocess.run", return_value=completed) as run_mock:
        result = run_m365_access_collector(
            user_principal_name="jane.doe@example.com",
            affected_service="Microsoft Teams",
            scenario="account-disabled",
        )

    assert result["status"] == "ok"
    _, kwargs = run_mock.call_args
    assert kwargs["shell"] is False
