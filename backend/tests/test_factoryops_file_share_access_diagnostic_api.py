from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _payload() -> dict:
    return {
        "status": "finding",
        "module": "factoryops-file-share-access-diagnostic",
        "check": "factoryops_file_share_access_diagnostic",
        "input": {
            "share_host": "filesrv01",
            "share_host_fqdn": "filesrv01.factory.local",
            "share_name": "Finance",
            "share_unc_path": "\\\\filesrv01.factory.local\\Finance",
            "user_sam_account_name": "finance.noaccess",
            "required_group_sam_account_name": "GG_FINANCE_SHARE_READ",
            "domain_name": "factory.local",
            "dns_server": "10.40.10.10",
            "observed_access_denied": True,
        },
        "evidence": {
            "dns": {"records": [], "resolved_ipv4_addresses": ["10.40.10.20"], "error": None},
            "reachability": {"target": "filesrv01.factory.local", "smb_tcp_445_reachable": True},
            "active_directory": {
                "module_available": True,
                "user_found": True,
                "user": None,
                "required_group_found": True,
                "required_group": None,
                "membership_proven": False,
                "user_error": None,
                "group_error": None,
            },
            "observed_access": {"access_denied": True, "supplied_by_operator": True},
        },
        "findings": [
            {
                "finding_id": "FACTORYOPS_FILE_SHARE_USER_MISSING_REQUIRED_GROUP",
                "rule_id": "FACTORYOPS_FILE_SHARE_USER_MISSING_REQUIRED_GROUP",
                "title": "User is not a member of the required file-share access group",
                "severity": "high",
                "confidence": "high",
                "likely_cause": "Missing AD group membership.",
                "evidence_used": [],
                "evidence_missing": [],
                "safe_next_steps": [],
                "what_not_to_change_yet": [],
                "limitations": [],
                "source_module": "factoryops-file-share-access-diagnostic",
            }
        ],
        "safe_next_steps": ["Review evidence before changing membership."],
        "limitations": ["Read-only diagnostic."],
        "read_only_boundary": {
            "remediation_performed": False,
            "dns_configuration_changed": False,
            "network_configuration_changed": False,
            "firewall_configuration_changed": False,
            "ad_objects_modified": False,
            "group_membership_changed": False,
            "ntfs_or_share_permissions_changed": False,
            "service_control_performed": False,
            "remote_command_executed": False,
            "credentials_or_tokens_stored": False,
            "user_impersonation_performed": False,
        },
    }


def test_factoryops_file_share_api_returns_runner_result(monkeypatch) -> None:
    def fake_runner(**kwargs):
        assert kwargs["share_host"] == "filesrv01"
        assert kwargs["share_name"] == "Finance"
        assert kwargs["user_sam_account_name"] == "finance.noaccess"
        assert kwargs["required_group_sam_account_name"] == "GG_FINANCE_SHARE_READ"
        assert kwargs["observed_access_denied"] is True
        return {"status": "ok", "result": _payload()}

    monkeypatch.setattr("app.diagnostics.run_factoryops_file_share_access_diagnostic", fake_runner)

    response = client.post(
        "/api/diagnostics/factoryops/file-share-access",
        json={
            "share_host": "filesrv01",
            "share_name": "Finance",
            "user_sam_account_name": "finance.noaccess",
            "required_group_sam_account_name": "GG_FINANCE_SHARE_READ",
            "domain_name": "factory.local",
            "dns_server": "10.40.10.10",
            "observed_access_denied": True,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["check"] == "factoryops_file_share_access_diagnostic"
    assert body["evidence"]["active_directory"]["membership_proven"] is False
    assert body["read_only_boundary"]["group_membership_changed"] is False


def test_factoryops_file_share_api_returns_controlled_error(monkeypatch) -> None:
    def fake_runner(**kwargs):
        return {"status": "error", "error": {"code": "FACTORYOPS_FILE_SHARE_TIMEOUT", "message": "timed out"}}

    monkeypatch.setattr("app.diagnostics.run_factoryops_file_share_access_diagnostic", fake_runner)

    response = client.post(
        "/api/diagnostics/factoryops/file-share-access",
        json={
            "share_host": "filesrv01",
            "share_name": "Finance",
            "user_sam_account_name": "finance.noaccess",
            "required_group_sam_account_name": "GG_FINANCE_SHARE_READ",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "error"
    assert body["error"]["code"] == "FACTORYOPS_FILE_SHARE_TIMEOUT"
    assert body["read_only_boundary"]["ntfs_or_share_permissions_changed"] is False
