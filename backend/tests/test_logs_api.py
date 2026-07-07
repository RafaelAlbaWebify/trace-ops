from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_logs_analyze_endpoint_returns_finding():
    response = client.post(
        "/api/logs/analyze",
        json={
            "affected_user": "sample.user@contoso.invalid",
            "affected_service": "SharePoint Online",
            "content": '2026-07-07T09:22:11Z user=sample.user@contoso.invalid app="SharePoint Online" result=failure reason="blocked by ca policy"',
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "findings"
    assert payload["primary_finding"]["rule_id"] == "LOG_PATTERN_CONDITIONAL_ACCESS_BLOCK"
    assert payload["report_markdown"].startswith("# TRACE Access Evidence Analysis Report")


def test_logs_analyze_endpoint_handles_empty_evidence():
    response = client.post(
        "/api/logs/analyze",
        json={"content": "not useful"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "insufficient_evidence"
    assert payload["primary_finding"]["rule_id"] == "LOG_PATTERN_NO_USABLE_EVENTS"
