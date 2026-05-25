import pytest

from app.collector_contract import validate_collector_result, validate_sample_scenario
from app.config import SUPPORTED_SAMPLE_SCENARIOS
from app.errors import BackendValidationError


def test_all_known_sample_scenarios_validate_successfully():
    for scenario in SUPPORTED_SAMPLE_SCENARIOS:
        result = validate_sample_scenario(scenario)

        assert result.scenario_id == scenario
        assert result.module == "m365-access-path-analyzer"


def test_invalid_scenario_returns_controlled_error():
    with pytest.raises(BackendValidationError) as exc_info:
        validate_sample_scenario("not-a-scenario")

    error = exc_info.value.to_dict()
    assert error["status"] == "error"
    assert error["error"]["code"] == "INVALID_SAMPLE_SCENARIO"
    assert error["error"]["scenario"] == "not-a-scenario"


def test_controlled_collector_error_json_validates_as_error_result():
    result = validate_collector_result(
        {
            "status": "error",
            "module": "m365-access-path-analyzer",
            "error": {
                "code": "REAL_COLLECTION_NOT_IMPLEMENTED",
                "message": "TRACE collector MVP only supports sample data.",
                "scenario": "account-disabled",
            },
        }
    )

    assert result.status == "error"
    assert result.module == "m365-access-path-analyzer"
    assert result.error.code == "REAL_COLLECTION_NOT_IMPLEMENTED"
    assert result.error.scenario == "account-disabled"


def test_controlled_collector_error_with_known_scenarios_validates():
    result = validate_collector_result(
        {
            "status": "error",
            "module": "m365-access-path-analyzer",
            "error": {
                "code": "INVALID_SAMPLE_SCENARIO",
                "message": "The requested sample scenario does not exist.",
                "scenario": "not-a-scenario",
                "known_scenarios": list(SUPPORTED_SAMPLE_SCENARIOS),
            },
        }
    )

    assert result.status == "error"
    assert result.error.code == "INVALID_SAMPLE_SCENARIO"
    assert set(result.error.known_scenarios) == set(SUPPORTED_SAMPLE_SCENARIOS)


def test_malformed_collector_error_json_fails_clearly():
    with pytest.raises(BackendValidationError) as exc_info:
        validate_collector_result(
            {
                "status": "error",
                "module": "m365-access-path-analyzer",
                "error": {
                    "message": "Missing code should not validate.",
                },
            }
        )

    error = exc_info.value.to_dict()
    assert error["error"]["code"] == "MALFORMED_COLLECTOR_ERROR"
    assert error["error"]["category"] == "collector_error"


def test_malformed_collector_json_fails_validation_clearly():
    with pytest.raises(BackendValidationError) as exc_info:
        validate_collector_result(["not", "an", "object"])

    error = exc_info.value.to_dict()
    assert error["error"]["code"] == "INVALID_COLLECTOR_RESULT"
    assert error["error"]["category"] == "malformed_json"
    assert "JSON object" in error["error"]["message"]


def test_missing_required_top_level_fields_fail_validation_clearly():
    with pytest.raises(BackendValidationError) as exc_info:
        validate_collector_result(
            {
                "scenario_id": "malformed",
                "module": "m365-access-path-analyzer",
            }
        )

    error = exc_info.value.to_dict()
    missing_fields = {detail["field"] for detail in error["error"]["details"]}

    assert error["error"]["code"] == "MISSING_REQUIRED_EVIDENCE"
    assert error["error"]["category"] == "contract"
    assert "input" in missing_fields
    assert "identity" in missing_fields
    assert "licenses" in missing_fields
    assert "signin_logs" in missing_fields
    assert "conditional_access" in missing_fields
    assert "device" in missing_fields
