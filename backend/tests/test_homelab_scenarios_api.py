from fastapi.testclient import TestClient

from app.homelab_scenarios import preview_homelab_scenario
from app.main import app

client = TestClient(app)


def _valid_scenario():
    return {
        "scenario_id": "factory-basic-dns-ad",
        "name": "Factory basic DNS and AD preview",
        "description": "Small factory homelab scenario for DNS and AD fixture diagnostics.",
        "environment": {
            "site_name": "FactoryOps Lab",
            "network": {
                "vlans": [
                    {"id": 10, "name": "servers"},
                    {"id": 20, "name": "workstations"},
                ],
                "subnets": ["192.168.10.0/24", "192.168.20.0/24"],
            },
            "dns": {
                "servers": ["192.168.10.10"],
                "records": [
                    {"name": "dc01.factory.local", "type": "A", "value": "192.168.10.10"},
                    {"name": "erp01.factory.local", "type": "A", "value": "192.168.10.20"},
                ],
            },
            "active_directory": {
                "domain_name": "factory.local",
                "users": [{"user_principal_name": "operator01@factory.local"}],
                "groups": [{"name": "Factory ERP Users"}],
            },
            "servers": [{"name": "dc01"}, {"name": "erp01"}],
            "endpoints": [{"name": "ops-client01"}],
        },
        "diagnostics": [
            {"type": "dns", "query": "dc01.factory.local", "record_type": "A"},
            {"type": "ad_user_access_fixture", "user_principal_name": "operator01@factory.local", "scenario": "ad-required-group-missing"},
        ],
        "expected_findings": ["AD_REQUIRED_GROUP_MISSING"],
    }


def test_preview_homelab_scenario_returns_summary_and_plan():
    result = preview_homelab_scenario(_valid_scenario())

    assert result["status"] == "ok"
    assert result["scenario_contract_version"] == "trace-homelab-scenario-preview-v1"
    assert result["preview_summary"]["domain"] == "factory.local"
    assert result["preview_summary"]["dns_record_count"] == 2
    assert result["preview_summary"]["diagnostic_step_count"] == 2
    assert result["diagnostic_plan"][0]["execution_mode"] == "preview_only"
    assert result["read_only_boundary"]["diagnostics_executed"] is False
    assert result["read_only_boundary"]["configuration_changed"] is False


def test_preview_rejects_action_sections():
    scenario = _valid_scenario()
    scenario["actions"] = [{"name": "not allowed in preview contract"}]

    result = preview_homelab_scenario(scenario)

    assert result["status"] == "error"
    assert result["validation"]["status"] == "invalid"
    assert "actions" in result["validation"]["errors"][0]
    assert result["read_only_boundary"]["preview_only"] is True


def test_preview_warns_for_unsupported_diagnostic_type():
    scenario = _valid_scenario()
    scenario["diagnostics"].append({"type": "plc_latency", "target": "plc01"})

    result = preview_homelab_scenario(scenario)

    assert result["status"] == "warning"
    assert result["validation"]["status"] == "valid"
    assert result["diagnostic_plan"][-1]["supported_by_trace_now"] is False


def test_homelab_scenario_preview_api():
    response = client.post("/api/homelab/scenarios/preview", json=_valid_scenario())

    assert response.status_code == 200
    body = response.json()
    assert body["check"] == "homelab_scenario_preview"
    assert body["scenario_id"] == "factory-basic-dns-ad"
    assert body["read_only_boundary"]["diagnostics_executed"] is False
