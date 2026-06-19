from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _payload():
    return {
        "case_title": "Factory ERP user cannot sign in",
        "module": "active-directory-user-access-diagnostic",
        "diagnostic_type": "ad_user_access_fixture",
        "target": "jane.doe@factory.local",
        "status": "warning",
        "findings": [
            {
                "finding_id": "AD_ACCOUNT_DISABLED",
                "severity": "high",
                "confidence": "high",
                "likely_cause": "The fixture user account is disabled.",
                "evidence_used": ["Fixture evidence shows enabled=false."],
                "evidence_missing": ["Real AD query was not performed."],
            }
        ],
        "evidence_summary": {"fixture_mode": True, "real_ad_query_performed": False},
        "safe_next_steps": ["Confirm the account state in AD Users and Computers or a read-only AD query."],
        "limitations": ["Fixture mode only."],
        "operator_notes": "Validate in the homelab before using real AD mode.",
    }


def test_operator_runbook_preview_returns_steps_and_contract():
    response = client.post("/api/operator/runbook/preview", json=_payload())

    assert response.status_code == 200
    body = response.json()

    assert body["status"] == "ok"
    assert body["runbook_contract_version"] == "trace-operator-runbook-preview-v1"
    assert body["case"]["target"] == "jane.doe@factory.local"
    assert body["executive_summary"]["finding_count"] == 1
    assert body["executive_summary"]["severity_counts"]["high"] == 1
    assert body["executive_summary"]["recommended_operator_posture"] == "validate-evidence-before-change"
    assert len(body["operator_steps"]) >= 5
    assert body["operator_steps"][0]["title"] == "Confirm case scope"


def test_operator_runbook_preview_is_read_only():
    response = client.post("/api/operator/runbook/preview", json=_payload())
    body = response.json()

    assert body["read_only_boundary"]["preview_only"] is True
    assert body["read_only_boundary"]["diagnostics_executed"] is False
    assert body["read_only_boundary"]["remediation_performed"] is False
    assert body["read_only_boundary"]["configuration_changed"] is False
    assert body["read_only_boundary"]["credentials_or_tokens_stored"] is False
    assert body["read_only_boundary"]["tenant_wide_scan_performed"] is False
    assert "does not execute diagnostics or remediation" in " ".join(body["limitations"])


def test_operator_runbook_preview_handles_no_findings():
    payload = _payload()
    payload["findings"] = []
    payload["status"] = "success"

    response = client.post("/api/operator/runbook/preview", json=payload)
    body = response.json()

    assert body["executive_summary"]["finding_count"] == 0
    assert body["executive_summary"]["primary_finding"] is None
    assert any(step["title"] == "Collect missing diagnostic evidence" for step in body["operator_steps"])


def test_operator_runbook_preview_rejects_missing_case_title():
    payload = _payload()
    payload["case_title"] = ""

    response = client.post("/api/operator/runbook/preview", json=payload)

    assert response.status_code == 422
