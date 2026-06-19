from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_graph_readiness_endpoint_returns_runner_payload(monkeypatch):
    def fake_runner():
        return {
            "status": "ok",
            "result": {
                "status": "warning",
                "module": "m365-access-path-analyzer",
                "check": "graph_readiness",
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
            },
        }

    monkeypatch.setattr("app.readiness.run_graph_readiness_check", fake_runner)

    response = client.get("/api/readiness/graph")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "warning"
    assert body["check"] == "graph_readiness"
    assert body["evidence"]["connected_to_graph"] is False
    assert body["read_only_boundary"]["automatic_connection_attempted"] is False


def test_graph_readiness_endpoint_returns_controlled_backend_error(monkeypatch):
    def fake_runner():
        return {
            "status": "error",
            "error": {
                "code": "INVALID_GRAPH_READINESS_STDOUT",
                "message": "The Graph readiness stdout was not valid JSON.",
            },
        }

    monkeypatch.setattr("app.readiness.run_graph_readiness_check", fake_runner)

    response = client.get("/api/readiness/graph")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "error"
    assert body["check"] == "graph_readiness"
    assert body["error"]["code"] == "INVALID_GRAPH_READINESS_STDOUT"
    assert body["read_only_boundary"]["remediation_performed"] is False
