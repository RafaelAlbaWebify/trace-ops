from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_dns_diagnostic_api_returns_runner_payload(monkeypatch):
    payload = {
        "status": "success",
        "module": "dns-diagnostics",
        "check": "dns_diagnostic",
        "input": {"query": "dc01.factory.local", "record_type": "A", "dns_server": "192.168.10.10"},
        "evidence": {"resolved": True, "records": ["192.168.10.10"], "record_count": 1},
        "findings": [],
        "safe_next_steps": ["Continue checking service reachability if the issue persists."],
        "limitations": [],
        "read_only_boundary": {
            "remediation_performed": False,
            "dns_configuration_changed": False,
            "network_configuration_changed": False,
        },
    }

    def fake_runner(**kwargs):
        assert kwargs["query"] == "dc01.factory.local"
        assert kwargs["record_type"] == "A"
        assert kwargs["dns_server"] == "192.168.10.10"
        return {"status": "ok", "result": payload}

    monkeypatch.setattr("app.diagnostics.run_dns_diagnostic", fake_runner)

    response = client.post(
        "/api/diagnostics/dns",
        json={"query": "dc01.factory.local", "record_type": "A", "dns_server": "192.168.10.10"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["check"] == "dns_diagnostic"
    assert body["evidence"]["resolved"] is True


def test_dns_diagnostic_api_returns_controlled_error(monkeypatch):
    def fake_runner(**kwargs):
        return {"status": "error", "error": {"code": "DNS_DIAGNOSTIC_SCRIPT_NOT_FOUND", "message": "missing"}}

    monkeypatch.setattr("app.diagnostics.run_dns_diagnostic", fake_runner)

    response = client.post("/api/diagnostics/dns", json={"query": "dc01.factory.local", "record_type": "A"})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "error"
    assert body["error"]["code"] == "DNS_DIAGNOSTIC_SCRIPT_NOT_FOUND"
    assert body["read_only_boundary"]["dns_configuration_changed"] is False
