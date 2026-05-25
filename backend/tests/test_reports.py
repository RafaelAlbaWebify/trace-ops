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
