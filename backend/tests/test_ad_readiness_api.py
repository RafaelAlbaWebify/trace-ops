from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_ad_readiness_endpoint_returns_runner_payload(monkeypatch):
    def fake_runner():
        return {
            "status": "ok",
            "result": {
                "status": "ok",
                "module": "active-directory-readiness",
                "check": "ad_readiness",
                "evidence": {
                    "hostname": "TRACE-CLIENT01",
                    "domain_joined": True,
                    "domain_name": "factory.local",
                    "workgroup": None,
                    "active_directory_module_available": True,
                    "domain_controller": {"discovered": True, "domain_controller": "dc01.factory.local"},
                    "ldap_probe": {"target": "dc01.factory.local", "port": 389, "reachable": True},
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
            },
        }

    monkeypatch.setattr("app.readiness.run_ad_readiness_check", fake_runner)

    response = client.get("/api/readiness/ad")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["check"] == "ad_readiness"
    assert body["evidence"]["domain_name"] == "factory.local"
    assert body["read_only_boundary"]["ad_objects_modified"] is False


def test_ad_readiness_endpoint_returns_controlled_backend_error(monkeypatch):
    def fake_runner():
        return {
            "status": "error",
            "error": {
                "code": "INVALID_AD_READINESS_STDOUT",
                "message": "The Active Directory readiness stdout was not valid JSON.",
            },
        }

    monkeypatch.setattr("app.readiness.run_ad_readiness_check", fake_runner)

    response = client.get("/api/readiness/ad")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "error"
    assert body["check"] == "ad_readiness"
    assert body["error"]["code"] == "INVALID_AD_READINESS_STDOUT"
    assert body["read_only_boundary"]["remediation_performed"] is False
