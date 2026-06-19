from fastapi.testclient import TestClient

from app.analyzer import analyze_collector_result
from app.collector_contract import validate_sample_scenario
from app.main import app
from app.storage import save_scan_record


client = TestClient(app)


def _ca_device_scan_response():
    result = validate_sample_scenario("ca-device-noncompliant")
    result_dict = result.model_dump()
    return {
        "status": "ok",
        "result": result_dict,
        "analysis": analyze_collector_result(result),
    }


def _save_ca_device_history(db_path):
    scan_response = _ca_device_scan_response()
    return save_scan_record(
        module="m365-access-path-analyzer",
        scenario="ca-device-noncompliant",
        user_principal_name="jane.doe@example.com",
        affected_service="Microsoft Teams",
        status="ok",
        result=scan_response,
        db_path=db_path,
    )


def test_json_report_builds_for_ca_device_history_record(monkeypatch, tmp_path):
    db_path = tmp_path / "history.sqlite3"
    monkeypatch.setattr("app.scan.HISTORY_DB_PATH", db_path)
    history_id = _save_ca_device_history(db_path)

    response = client.get(f"/api/history/{history_id}/report.json")

    assert response.status_code == 200
    body = response.json()
    assert body["product"] == "TRACE"
    assert body["module"] == "M365 Access Path Analyzer"
    assert body["user_principal_name"] == "jane.doe@example.com"
    assert body["affected_service"] == "Microsoft Teams"
    assert body["scenario"] == "ca-device-noncompliant"
    assert body["primary_finding"] == "CA_DEVICE_COMPLIANCE_BLOCK"
    assert body["severity"] == "high"
    assert body["confidence"] == "high"
    assert body["raw_evidence_summary"]["device"]["compliance_state"] == "nonCompliant"


def test_html_report_builds_for_ca_device_history_record(monkeypatch, tmp_path):
    db_path = tmp_path / "history.sqlite3"
    monkeypatch.setattr("app.scan.HISTORY_DB_PATH", db_path)
    history_id = _save_ca_device_history(db_path)

    response = client.get(f"/api/history/{history_id}/report.html")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "TRACE Report" in response.text
    assert "M365 Access Path Analyzer" in response.text
    assert "CA_DEVICE_COMPLIANCE_BLOCK" in response.text
    assert "Do not disable Conditional Access globally." in response.text


def test_missing_history_id_returns_controlled_404(monkeypatch, tmp_path):
    monkeypatch.setattr("app.scan.HISTORY_DB_PATH", tmp_path / "history.sqlite3")

    response = client.get("/api/history/404/report.json")

    assert response.status_code == 404
    body = response.json()
    assert body["status"] == "error"
    assert body["error"]["code"] == "HISTORY_RECORD_NOT_FOUND"


def test_json_report_includes_phase2_evidence_contract_fields(monkeypatch, tmp_path):
    db_path = tmp_path / "history.sqlite3"
    monkeypatch.setattr("app.scan.HISTORY_DB_PATH", db_path)
    history_id = _save_ca_device_history(db_path)

    response = client.get(f"/api/history/{history_id}/report.json")

    assert response.status_code == 200
    body = response.json()
    assert body["evidence_contract_version"] == "TRACE_FINDING_EVIDENCE_V1"
    assert body["primary_finding"] == "CA_DEVICE_COMPLIANCE_BLOCK"
    assert body["source_module"] == "m365-access-path-analyzer"
    assert body["evidence_used"]
    assert body["evidence_missing"]
    assert body["next_steps"]


def test_json_report_includes_phase7_report_quality_fields(monkeypatch, tmp_path):
    db_path = tmp_path / "history.sqlite3"
    monkeypatch.setattr("app.scan.HISTORY_DB_PATH", db_path)
    history_id = _save_ca_device_history(db_path)

    response = client.get(f"/api/history/{history_id}/report.json")

    assert response.status_code == 200
    body = response.json()
    assert body["report_contract_version"] == "TRACE_REPORT_V2"
    assert body["generated_at"]
    assert body["finding_count"] >= 1
    assert body["findings"]
    assert body["findings"][0]["finding_id"] == "CA_DEVICE_COMPLIANCE_BLOCK"
    assert body["findings"][0]["evidence_used"]
    assert body["findings"][0]["safe_next_steps"]
    assert body["executive_summary"]["primary_finding"] == "CA_DEVICE_COMPLIANCE_BLOCK"
    assert body["executive_summary"]["operator_message"]
    assert body["safety_boundary"] == {
        "read_only_report": True,
        "remediation_performed": False,
        "credentials_or_tokens_stored": False,
        "tenant_wide_scan_performed": False,
    }


def test_html_report_includes_phase7_sections(monkeypatch, tmp_path):
    db_path = tmp_path / "history.sqlite3"
    monkeypatch.setattr("app.scan.HISTORY_DB_PATH", db_path)
    history_id = _save_ca_device_history(db_path)

    response = client.get(f"/api/history/{history_id}/report.html")

    assert response.status_code == 200
    assert "Executive Summary" in response.text
    assert "Case Scope" in response.text
    assert "Safety Boundary" in response.text
    assert "TRACE_REPORT_V2" in response.text
    assert "CA_DEVICE_COMPLIANCE_BLOCK" in response.text
    assert "Review evidence, missing evidence, and safe next steps" in response.text
