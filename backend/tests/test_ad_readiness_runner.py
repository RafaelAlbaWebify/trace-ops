import json
import subprocess
from pathlib import Path
from unittest.mock import patch

from app.collector_runner import build_ad_readiness_command, run_ad_readiness_check
from app.config import AD_READINESS_SCRIPT_PATH


def ad_payload(status="warning"):
    return {
        "status": status,
        "module": "active-directory-readiness",
        "check": "ad_readiness",
        "generated_at": "2026-06-03T11:30:00Z",
        "evidence": {
            "hostname": "TRACE-CLIENT01",
            "domain_joined": True,
            "domain_name": "factory.local",
            "workgroup": None,
            "active_directory_module_available": True,
            "domain_controller": {
                "discovered": True,
                "domain_controller": "dc01.factory.local",
                "method": "nltest",
                "error": None,
            },
            "ldap_probe": {"target": "dc01.factory.local", "port": 389, "reachable": True, "error": None},
            "current_user_context": {"user_domain": "FACTORY", "username": "operator01"},
        },
        "safe_next_steps": [],
        "limitations": [],
        "read_only_boundary": {
            "remediation_performed": False,
            "ad_objects_modified": False,
            "group_membership_changed": False,
            "password_or_account_state_changed": False,
        },
    }


def test_ad_readiness_command_uses_argument_array_and_no_shell_script_writes():
    command = build_ad_readiness_command(readiness_script_path=AD_READINESS_SCRIPT_PATH)

    assert isinstance(command, list)
    assert "-Command" in command
    assert str(AD_READINESS_SCRIPT_PATH) in command[5]
    assert "Set-ADUser" not in command[5]
    assert "Add-ADGroupMember" not in command[5]
    assert "Unlock-ADAccount" not in command[5]


def test_ad_readiness_success_payload_is_returned():
    completed = subprocess.CompletedProcess(args=["powershell"], returncode=0, stdout=json.dumps(ad_payload("ok")), stderr="")

    with patch("app.collector_runner.subprocess.run", return_value=completed) as run_mock:
        result = run_ad_readiness_check()

    assert result["status"] == "ok"
    assert result["result"]["check"] == "ad_readiness"
    assert result["result"]["evidence"]["domain_name"] == "factory.local"
    _, kwargs = run_mock.call_args
    assert kwargs["shell"] is False


def test_ad_readiness_missing_script_is_controlled_error():
    result = run_ad_readiness_check(readiness_script_path=Path("missing-ad-readiness.ps1"))

    assert result["status"] == "error"
    assert result["error"]["code"] == "AD_READINESS_SCRIPT_NOT_FOUND"


def test_ad_readiness_non_zero_exit_is_controlled_error():
    completed = subprocess.CompletedProcess(args=["powershell"], returncode=1, stdout="", stderr="failed")

    with patch("app.collector_runner.subprocess.run", return_value=completed):
        result = run_ad_readiness_check()

    assert result["status"] == "error"
    assert result["error"]["code"] == "AD_READINESS_PROCESS_FAILED"
    assert result["error"]["return_code"] == 1


def test_ad_readiness_invalid_json_is_controlled_error():
    completed = subprocess.CompletedProcess(args=["powershell"], returncode=0, stdout="not json", stderr="")

    with patch("app.collector_runner.subprocess.run", return_value=completed):
        result = run_ad_readiness_check()

    assert result["status"] == "error"
    assert result["error"]["code"] == "INVALID_AD_READINESS_STDOUT"


def test_ad_readiness_rejects_boundary_violation():
    payload = ad_payload()
    payload["read_only_boundary"]["ad_objects_modified"] = True
    completed = subprocess.CompletedProcess(args=["powershell"], returncode=0, stdout=json.dumps(payload), stderr="")

    with patch("app.collector_runner.subprocess.run", return_value=completed):
        result = run_ad_readiness_check()

    assert result["status"] == "error"
    assert result["error"]["code"] == "AD_READINESS_OUTPUT_VALIDATION_FAILED"
