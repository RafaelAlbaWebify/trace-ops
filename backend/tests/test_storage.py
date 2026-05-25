from app.storage import initialize_database, list_scan_history, save_scan_record


def test_database_initialization_works_in_temporary_path(tmp_path):
    db_path = tmp_path / "nested" / "trace_history.sqlite3"

    initialize_database(db_path)

    assert db_path.exists()


def test_successful_scan_record_can_be_saved(tmp_path):
    db_path = tmp_path / "trace_history.sqlite3"
    result = {
        "status": "ok",
        "result": {
            "scenario_id": "ca-device-noncompliant",
            "module": "m365-access-path-analyzer",
        },
    }

    record_id = save_scan_record(
        module="m365-access-path-analyzer",
        scenario="ca-device-noncompliant",
        user_principal_name="jane.doe@example.com",
        affected_service="Microsoft Teams",
        status="ok",
        result=result,
        db_path=db_path,
    )
    records = list_scan_history(db_path=db_path)

    assert record_id == 1
    assert len(records) == 1
    assert records[0]["status"] == "ok"
    assert records[0]["result_json"] == result


def test_controlled_collector_error_record_can_be_saved(tmp_path):
    db_path = tmp_path / "trace_history.sqlite3"
    result = {
        "status": "collector_error",
        "error": {
            "code": "INVALID_SAMPLE_SCENARIO",
            "message": "The requested sample scenario does not exist.",
            "scenario": "not-a-scenario",
        },
    }

    save_scan_record(
        module="m365-access-path-analyzer",
        scenario="not-a-scenario",
        user_principal_name="jane.doe@example.com",
        affected_service="Microsoft Teams",
        status="collector_error",
        result=result,
        db_path=db_path,
    )
    records = list_scan_history(db_path=db_path)

    assert len(records) == 1
    assert records[0]["status"] == "collector_error"
    assert records[0]["result_json"]["error"]["code"] == "INVALID_SAMPLE_SCENARIO"
