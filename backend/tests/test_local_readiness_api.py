from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_local_readiness_endpoint_returns_runner_payload(monkeypatch):
    def fake_runner():
        return {
            "status": "ok",
            "result": {
                "status": "warning",
                "module": "local-infrastructure-readiness",
                "check": "local_readiness",
                "evidence": {
                    "hostname": "TRACE-CLIENT01",
                    "os_description": "Windows 11 Pro",
                    "powershell_version": "5.1.19041.1",
                    "domain_joined": False,
                    "domain_name": None,
                    "workgroup": "WORKGROUP",
                    "network_adapters": [],
                    "ip_configurations": [],
                    "dns_probe": {"query": "localhost", "succeeded": True, "addresses": ["127.0.0.1"], "error": None},
                    "gateway_probe": {"target": None, "reachable": None, "error": "No default gateway detected."},
                },
                "safe_next_steps": ["For AD diagnostics, run TRACE from a domain-joined machine."],
                "limitations": ["No IPv4 default gateway was detected."],
                "read_only_boundary": {
                    "remediation_performed": False,
                    "network_configuration_changed": False,
                    "service_control_performed": False,
                },
            },
        }

    monkeypatch.setattr("app.readiness.run_local_readiness_check", fake_runner)

    response = client.get("/api/readiness/local")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "warning"
    assert body["check"] == "local_readiness"
    assert body["evidence"]["hostname"] == "TRACE-CLIENT01"
    assert body["read_only_boundary"]["network_configuration_changed"] is False


def test_local_readiness_endpoint_returns_controlled_backend_error(monkeypatch):
    def fake_runner():
        return {
            "status": "error",
            "error": {
                "code": "INVALID_LOCAL_READINESS_STDOUT",
                "message": "The local infrastructure readiness stdout was not valid JSON.",
            },
        }

    monkeypatch.setattr("app.readiness.run_local_readiness_check", fake_runner)

    response = client.get("/api/readiness/local")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "error"
    assert body["check"] == "local_readiness"
    assert body["error"]["code"] == "INVALID_LOCAL_READINESS_STDOUT"
    assert body["read_only_boundary"]["remediation_performed"] is False
