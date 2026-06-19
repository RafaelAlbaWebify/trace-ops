from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_ad_user_access_api_returns_runner_payload(monkeypatch):
    payload = {
        "status": "finding",
        "module": "active-directory-user-access-diagnostic",
        "check": "ad_user_access_diagnostic",
        "input": {
            "user_principal_name": "jane.doe@factory.local",
            "affected_service": "Factory ERP",
            "scenario": "ad-account-disabled",
            "fixture_mode": True,
        },
        "evidence": {"fixture_mode": True, "real_ad_query_performed": False},
        "findings": [{"finding_id": "AD_ACCOUNT_DISABLED", "severity": "high"}],
        "safe_next_steps": ["Verify with read-only AD evidence before making any change."],
        "limitations": ["Fixture-mode diagnostic only."],
        "read_only_boundary": {
            "remediation_performed": False,
            "ad_objects_modified": False,
            "group_membership_changed": False,
            "password_or_account_state_changed": False,
            "real_ad_query_performed": False,
        },
    }

    def fake_runner(**kwargs):
        assert kwargs["user_principal_name"] == "jane.doe@factory.local"
        assert kwargs["affected_service"] == "Factory ERP"
        assert kwargs["scenario"] == "ad-account-disabled"
        return {"status": "ok", "result": payload}

    monkeypatch.setattr("app.diagnostics.run_ad_user_access_diagnostic", fake_runner)

    response = client.post(
        "/api/diagnostics/ad-user-access",
        json={
            "user_principal_name": "jane.doe@factory.local",
            "affected_service": "Factory ERP",
            "scenario": "ad-account-disabled",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "finding"
    assert body["check"] == "ad_user_access_diagnostic"
    assert body["evidence"]["fixture_mode"] is True
    assert body["read_only_boundary"]["real_ad_query_performed"] is False


def test_ad_user_access_api_returns_controlled_error(monkeypatch):
    def fake_runner(**kwargs):
        return {"status": "error", "error": {"code": "AD_USER_ACCESS_SCRIPT_NOT_FOUND", "message": "missing"}}

    monkeypatch.setattr("app.diagnostics.run_ad_user_access_diagnostic", fake_runner)

    response = client.post(
        "/api/diagnostics/ad-user-access",
        json={
            "user_principal_name": "jane.doe@factory.local",
            "affected_service": "Factory ERP",
            "scenario": "ad-account-disabled",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "error"
    assert body["error"]["code"] == "AD_USER_ACCESS_SCRIPT_NOT_FOUND"
    assert body["read_only_boundary"]["ad_objects_modified"] is False
    assert body["read_only_boundary"]["real_ad_query_performed"] is False
