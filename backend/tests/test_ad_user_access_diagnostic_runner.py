import json
import subprocess
from pathlib import Path
from unittest.mock import patch

from app.collector_runner import build_ad_user_access_diagnostic_command, run_ad_user_access_diagnostic
from app.config import AD_USER_ACCESS_SCRIPT_PATH


def ad_payload(status="finding"):
    return {
        "status": status,
        "module": "active-directory-user-access-diagnostic",
        "check": "ad_user_access_diagnostic",
        "generated_at": "2026-06-03T11:30:00Z",
        "input": {
            "user_principal_name": "jane.doe@factory.local",
            "affected_service": "Factory ERP",
            "scenario": "ad-account-disabled",
            "fixture_mode": True,
        },
        "evidence": {
            "user": {"enabled": False, "locked_out": False, "password_expired": False},
            "group_requirements": [],
            "fixture_mode": True,
            "real_ad_query_performed": False,
        },
        "findings": [
            {
                "finding_id": "AD_ACCOUNT_DISABLED",
                "rule_id": "AD_ACCOUNT_DISABLED",
                "title": "AD account is disabled in fixture evidence",
                "severity": "high",
                "confidence": "high",
                "likely_cause": "Fixture evidence shows the AD account is disabled.",
                "evidence_used": ["fixture.user.enabled = false"],
                "evidence_missing": ["Real AD user properties were not queried."],
                "safe_next_steps": ["Verify account status with approved read-only AD tools."],
                "what_not_to_change_yet": ["Do not change account state based on fixture data."],
                "limitations": ["Fixture-mode diagnostic only."],
                "source_module": "active-directory-user-access-diagnostic",
            }
        ],
        "safe_next_steps": ["Use fixture evidence only to validate workflow."],
        "limitations": ["Fixture-mode diagnostic only."],
        "read_only_boundary": {
            "remediation_performed": False,
            "ad_objects_modified": False,
            "group_membership_changed": False,
            "password_or_account_state_changed": False,
            "real_ad_query_performed": False,
        },
    }


def test_ad_user_access_command_uses_fixture_mode_and_no_shell():
    command = build_ad_user_access_diagnostic_command(
        user_principal_name="jane.doe@factory.local",
        affected_service="Factory ERP",
        scenario="ad-account-disabled",
        diagnostic_script_path=AD_USER_ACCESS_SCRIPT_PATH,
    )

    assert isinstance(command, list)
    assert "-Command" in command
    assert str(AD_USER_ACCESS_SCRIPT_PATH) in command[5]
    assert "jane.doe@factory.local" in command[5]
    assert "ad-account-disabled" in command[5]
    assert "-UseFixtureData:$true" in command[5]


def test_ad_user_access_success_payload_is_returned():
    completed = subprocess.CompletedProcess(
        args=["powershell"],
        returncode=0,
        stdout=json.dumps(ad_payload()),
        stderr="",
    )

    with patch("app.collector_runner.subprocess.run", return_value=completed) as run_mock:
        result = run_ad_user_access_diagnostic(
            user_principal_name="jane.doe@factory.local",
            affected_service="Factory ERP",
            scenario="ad-account-disabled",
        )

    assert result["status"] == "ok"
    assert result["result"]["check"] == "ad_user_access_diagnostic"
    assert result["result"]["evidence"]["fixture_mode"] is True
    assert result["result"]["read_only_boundary"]["real_ad_query_performed"] is False
    _, kwargs = run_mock.call_args
    assert kwargs["shell"] is False


def test_ad_user_access_missing_script_is_controlled_error():
    result = run_ad_user_access_diagnostic(
        user_principal_name="jane.doe@factory.local",
        affected_service="Factory ERP",
        scenario="ad-account-disabled",
        diagnostic_script_path=Path("missing-ad-user-access.ps1"),
    )

    assert result["status"] == "error"
    assert result["error"]["code"] == "AD_USER_ACCESS_SCRIPT_NOT_FOUND"


def test_ad_user_access_invalid_json_is_controlled_error():
    completed = subprocess.CompletedProcess(args=["powershell"], returncode=0, stdout="not json", stderr="")

    with patch("app.collector_runner.subprocess.run", return_value=completed):
        result = run_ad_user_access_diagnostic(
            user_principal_name="jane.doe@factory.local",
            affected_service="Factory ERP",
            scenario="ad-account-disabled",
        )

    assert result["status"] == "error"
    assert result["error"]["code"] == "INVALID_AD_USER_ACCESS_STDOUT"


def test_ad_user_access_rejects_real_query_boundary_violation():
    payload = ad_payload()
    payload["evidence"]["real_ad_query_performed"] = True
    completed = subprocess.CompletedProcess(args=["powershell"], returncode=0, stdout=json.dumps(payload), stderr="")

    with patch("app.collector_runner.subprocess.run", return_value=completed):
        result = run_ad_user_access_diagnostic(
            user_principal_name="jane.doe@factory.local",
            affected_service="Factory ERP",
            scenario="ad-account-disabled",
        )

    assert result["status"] == "error"
    assert result["error"]["code"] == "AD_USER_ACCESS_OUTPUT_VALIDATION_FAILED"


def test_ad_user_access_rejects_incomplete_finding_contract():
    payload = ad_payload()
    del payload["findings"][0]["evidence_missing"]
    completed = subprocess.CompletedProcess(args=["powershell"], returncode=0, stdout=json.dumps(payload), stderr="")

    with patch("app.collector_runner.subprocess.run", return_value=completed):
        result = run_ad_user_access_diagnostic(
            user_principal_name="jane.doe@factory.local",
            affected_service="Factory ERP",
            scenario="ad-account-disabled",
        )

    assert result["status"] == "error"
    assert result["error"]["code"] == "AD_USER_ACCESS_OUTPUT_VALIDATION_FAILED"
