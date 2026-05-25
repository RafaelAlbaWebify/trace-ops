from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_modules_returns_trace_module_metadata():
    response = client.get("/api/modules")

    assert response.status_code == 200
    body = response.json()
    assert body["product"] == "TRACE"
    assert body["product_full_name"] == "Troubleshooting Reports Across Cloud & Endpoints"
    assert len(body["modules"]) == 1

    module = body["modules"][0]
    assert module["id"] == "m365-access-path-analyzer"
    assert module["name"] == "M365 Access Path Analyzer"
    assert "Microsoft Teams" in module["supported_affected_services"]
