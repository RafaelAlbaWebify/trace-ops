from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_log_analysis_persists_run_and_report(monkeypatch, tmp_path):
    monkeypatch.setenv("TRACE_ACCESS_RUN_STORE", str(tmp_path))

    response = client.post(
        "/api/logs/analyze",
        json={
            "source_type": "generic_access_log_text",
            "affected_user": "sample.user@contoso.invalid",
            "affected_service": "SharePoint Online",
            "content": "2026-07-07T09:22:11Z user=sample.user@contoso.invalid app=SharePoint result=failure reason=ca-policy",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    run_id = payload.get("run_id")
    assert run_id

    history = client.get("/api/logs/history")
    assert history.status_code == 200
    items = history.json()["items"]
    assert len(items) == 1
    assert items[0]["run_id"] == run_id
    assert items[0]["source_type"] == "generic_access_log_text"

    detail = client.get(f"/api/logs/history/{run_id}")
    assert detail.status_code == 200
    assert detail.json()["run_id"] == run_id
    assert detail.json()["response"]["run_id"] == run_id

    report = client.get(f"/api/logs/reports/{run_id}.md")
    assert report.status_code == 200
    assert report.text.startswith("# TRACE Access Evidence Analysis Report")


def test_missing_log_run_returns_404(monkeypatch, tmp_path):
    monkeypatch.setenv("TRACE_ACCESS_RUN_STORE", str(tmp_path))

    response = client.get("/api/logs/history/not-found")

    assert response.status_code == 404


def test_invalid_run_id_is_rejected_without_filesystem_lookup(monkeypatch, tmp_path):
    monkeypatch.setenv("TRACE_ACCESS_RUN_STORE", str(tmp_path))

    detail = client.get("/api/logs/history/not-a-valid-run-id")
    report = client.get("/api/logs/reports/not-a-valid-run-id.md")

    assert detail.status_code == 404
    assert report.status_code == 404
