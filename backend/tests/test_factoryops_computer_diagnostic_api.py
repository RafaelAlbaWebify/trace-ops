from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _payload() -> dict:
    return {
        "status": "success",
        "module": "factoryops-computer-diagnostic",
        "check": "factoryops_computer_diagnostic",
        "input": {"computer_name": "office-pc01", "computer_fqdn": "office-pc01.factory.local", "domain_name": "factory.local"},
        "evidence": {
            "dns": {"records": [], "resolved_ipv4_addresses": [], "error": None},
            "active_directory": {"module_available": True, "computer_found": True, "computer": None, "error": None},
            "reachability": {"target": "office-pc01.factory.local", "icmp_reachable": True, "port_probes": []},
        },
        "findings": [],
        "safe_next_steps": ["Review evidence before changing settings."],
        "limitations": ["Read-only diagnostic."],
        "read_only_boundary": {
            "remediation_performed": False,
            "dns_configuration_changed": False,
            "network_configuration_changed": False,
            "firewall_configuration_changed": False,
            "ad_objects_modified": False,
            "service_control_performed": False,
            "remote_command_executed": False,
            "credentials_or_tokens_stored": False,
        },
    }


def test_factoryops_computer_api_returns_runner_result(monkeypatch) -> None:
    def fake_runner(**kwargs):
        assert kwargs["computer_name"] == "office-pc01"
        assert kwargs["dns_server"] == "10.40.10.10"
        return {"status": "ok", "result": _payload()}

    monkeypatch.setattr("app.diagnostics.run_factoryops_computer_diagnostic", fake_runner)

    response = client.post(
        "/api/diagnostics/factoryops/computer",
        json={
            "computer_name": "office-pc01",
            "domain_name": "factory.local",
            "dns_server": "10.40.10.10",
            "expected_ipv4_address": "10.20.10.100",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["check"] == "factoryops_computer_diagnostic"
    assert body["read_only_boundary"]["remote_command_executed"] is False


def test_factoryops_computer_api_returns_controlled_error(monkeypatch) -> None:
    def fake_runner(**kwargs):
        return {"status": "error", "error": {"code": "FACTORYOPS_COMPUTER_TIMEOUT", "message": "timed out"}}

    monkeypatch.setattr("app.diagnostics.run_factoryops_computer_diagnostic", fake_runner)

    response = client.post("/api/diagnostics/factoryops/computer", json={"computer_name": "office-pc01"})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "error"
    assert body["error"]["code"] == "FACTORYOPS_COMPUTER_TIMEOUT"
    assert body["read_only_boundary"]["remediation_performed"] is False
