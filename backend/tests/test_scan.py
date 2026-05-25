from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_user_access_scan_success(monkeypatch, tmp_path):
    monkeypatch.setattr("app.scan.HISTORY_DB_PATH", tmp_path / "history.sqlite3")

    def fake_runner(user_principal_name, affected_service, scenario):
        return {
            "status": "ok",
            "result": {
                "scenario_id": scenario,
                "module": "m365-access-path-analyzer",
                "input": {
                    "user_principal_name": user_principal_name,
                    "affected_service": affected_service,
                },
                "identity": {
                    "user_exists": True,
                    "account_enabled": True,
                    "user_type": "Member",
                    "display_name": "Jane Doe",
                },
                "licenses": {
                    "has_relevant_license": True,
                    "assigned_skus": ["SPE_E3", "TEAMS1"],
                },
                "signin_logs": {
                    "available": True,
                    "recent_events": [
                        {
                            "createdDateTime": "2026-05-25T11:20:00Z",
                            "status": "failure",
                            "failureReason": "Device does not satisfy the compliant device requirement.",
                            "resourceDisplayName": "Microsoft Teams",
                            "clientAppUsed": "Mobile Apps and Desktop clients",
                            "conditionalAccessStatus": "failure",
                        }
                    ],
                },
                "conditional_access": {
                    "details_available": True,
                    "policies": [
                        {
                            "displayName": "Require compliant device for Microsoft 365",
                            "result": "failure",
                            "grantControls": ["compliantDevice"],
                        }
                    ],
                },
                "device": {
                    "evidence_available": True,
                    "compliance_state": "nonCompliant",
                },
            },
        }

    monkeypatch.setattr("app.scan.run_m365_access_collector", fake_runner)

    response = client.post(
        "/api/scan/user-access",
        json={
            "user_principal_name": "jane.doe@example.com",
            "affected_service": "Microsoft Teams",
            "scenario": "ca-device-noncompliant",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["history_id"] == 1
    assert body["result"]["scenario_id"] == "ca-device-noncompliant"
    assert body["result"]["module"] == "m365-access-path-analyzer"
    assert body["analysis"]["status"] == "findings"
    assert body["analysis"]["findings"][0]["rule_id"] == "CA_DEVICE_COMPLIANCE_BLOCK"


def test_user_access_scan_invalid_scenario_returns_controlled_error(monkeypatch, tmp_path):
    monkeypatch.setattr("app.scan.HISTORY_DB_PATH", tmp_path / "history.sqlite3")

    def fake_runner(user_principal_name, affected_service, scenario):
        return {
            "status": "collector_error",
            "collector_error": {
                "status": "error",
                "module": "m365-access-path-analyzer",
                "error": {
                    "code": "INVALID_SAMPLE_SCENARIO",
                    "message": "The requested sample scenario does not exist.",
                    "scenario": scenario,
                    "known_scenarios": ["ca-device-noncompliant"],
                },
            },
        }

    monkeypatch.setattr("app.scan.run_m365_access_collector", fake_runner)

    response = client.post(
        "/api/scan/user-access",
        json={
            "user_principal_name": "jane.doe@example.com",
            "affected_service": "Microsoft Teams",
            "scenario": "not-a-scenario",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "collector_error"
    assert body["history_id"] == 1
    assert body["error"]["code"] == "INVALID_SAMPLE_SCENARIO"
    assert body["error"]["scenario"] == "not-a-scenario"


def test_user_access_scan_missing_required_fields_fails_validation():
    response = client.post(
        "/api/scan/user-access",
        json={
            "user_principal_name": "jane.doe@example.com",
            "scenario": "ca-device-noncompliant",
        },
    )

    assert response.status_code == 422


def test_history_returns_saved_records(monkeypatch, tmp_path):
    monkeypatch.setattr("app.scan.HISTORY_DB_PATH", tmp_path / "history.sqlite3")

    def fake_runner(user_principal_name, affected_service, scenario):
        return {
            "status": "collector_error",
            "collector_error": {
                "status": "error",
                "module": "m365-access-path-analyzer",
                "error": {
                    "code": "INVALID_SAMPLE_SCENARIO",
                    "message": "The requested sample scenario does not exist.",
                    "scenario": scenario,
                    "known_scenarios": ["ca-device-noncompliant"],
                },
            },
        }

    monkeypatch.setattr("app.scan.run_m365_access_collector", fake_runner)

    client.post(
        "/api/scan/user-access",
        json={
            "user_principal_name": "jane.doe@example.com",
            "affected_service": "Microsoft Teams",
            "scenario": "not-a-scenario",
        },
    )
    response = client.get("/api/history")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert len(body["records"]) == 1
    assert body["records"][0]["status"] == "collector_error"
    assert body["records"][0]["scenario"] == "not-a-scenario"
