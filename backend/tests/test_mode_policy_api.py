from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_mode_policy_returns_modes_and_contract():
    response = client.get("/api/mode-policy")

    assert response.status_code == 200
    body = response.json()

    assert body["status"] == "ok"
    assert body["mode_policy_contract_version"] == "trace-mode-policy-v1"
    assert body["current_default_mode"] == "sample"
    assert body["recommended_next_mode"] == "homelab"

    mode_ids = {mode["mode_id"] for mode in body["modes"]}
    assert {"sample", "homelab", "trial_tenant_ready"}.issubset(mode_ids)


def test_trial_tenant_mode_is_preparation_only_and_guarded():
    response = client.get("/api/mode-policy")
    body = response.json()

    trial_mode = next(mode for mode in body["modes"] if mode["mode_id"] == "trial_tenant_ready")

    assert "Automatic Graph sign-in." in trial_mode["blocked_capabilities"]
    assert "Credential or token storage." in trial_mode["blocked_capabilities"]
    assert "Tenant-wide scans." in trial_mode["blocked_capabilities"]
    assert "Write scopes." in trial_mode["blocked_capabilities"]
    assert "Graph module available." in trial_mode["readiness_required"]
    assert "Single target user provided by operator." in trial_mode["readiness_required"]


def test_global_read_only_boundary_blocks_risky_behavior():
    response = client.get("/api/mode-policy")
    boundary = response.json()["global_read_only_boundary"]

    assert boundary["automatic_connection_attempted"] is False
    assert boundary["credentials_or_tokens_stored"] is False
    assert boundary["tenant_wide_scan_performed"] is False
    assert boundary["write_scopes_requested"] is False
    assert boundary["configuration_changed"] is False
    assert boundary["remediation_performed"] is False


def test_production_mode_is_not_defined_yet():
    response = client.get("/api/mode-policy")
    body = response.json()

    mode_ids = {mode["mode_id"] for mode in body["modes"]}
    assert "production" not in mode_ids
    assert any("Production mode is intentionally not defined" in item for item in body["limitations"])
