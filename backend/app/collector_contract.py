from typing import Any, Dict, Union

from pydantic import ValidationError

from .config import SUPPORTED_SAMPLE_SCENARIOS
from .errors import validation_error
from .models import CollectorErrorResult, CollectorResult
from .sample_loader import load_all_samples

REQUIRED_EVIDENCE_FIELDS = (
    "input",
    "identity",
    "licenses",
    "signin_logs",
    "conditional_access",
    "device",
)


def _normalize_pydantic_errors(error: ValidationError) -> list[Dict[str, Any]]:
    return [
        {
            "field": ".".join(str(part) for part in item.get("loc", ())),
            "message": item.get("msg", "Invalid value."),
            "type": item.get("type", "value_error"),
        }
        for item in error.errors()
    ]


def _missing_required_evidence_fields(data: Dict[str, Any]) -> list[str]:
    return [field for field in REQUIRED_EVIDENCE_FIELDS if field not in data]


def _is_controlled_collector_error(data: Dict[str, Any]) -> bool:
    return data.get("status") == "error" and isinstance(data.get("error"), dict)


def _validate_collector_error_result(data: Dict[str, Any]) -> CollectorErrorResult:
    try:
        return CollectorErrorResult(**data)
    except ValidationError as exc:
        raise validation_error(
            "MALFORMED_COLLECTOR_ERROR",
            "Collector returned an error payload, but it does not match the controlled error contract.",
            scenario=data.get("error", {}).get("scenario") if isinstance(data.get("error"), dict) else None,
            details=_normalize_pydantic_errors(exc),
            category="collector_error",
        ) from exc


def validate_collector_result(data: Dict[str, Any]) -> Union[CollectorResult, CollectorErrorResult]:
    if not isinstance(data, dict):
        raise validation_error(
            "INVALID_COLLECTOR_RESULT",
            "Collector result must be a JSON object.",
            category="malformed_json",
        )

    if _is_controlled_collector_error(data):
        return _validate_collector_error_result(data)

    missing_fields = _missing_required_evidence_fields(data)
    if missing_fields:
        raise validation_error(
            "MISSING_REQUIRED_EVIDENCE",
            "Collector result is missing required normalized evidence fields.",
            scenario=data.get("scenario_id"),
            details=[
                {
                    "field": field,
                    "message": "Required normalized evidence field is missing.",
                    "type": "missing",
                }
                for field in missing_fields
            ],
            category="contract",
        )

    try:
        return CollectorResult(**data)
    except ValidationError as exc:
        raise validation_error(
            "COLLECTOR_CONTRACT_VALIDATION_FAILED",
            "Collector result does not match the normalized evidence contract.",
            scenario=data.get("scenario_id"),
            details=_normalize_pydantic_errors(exc),
            category="contract",
        ) from exc


def validate_sample_scenario(scenario: str) -> CollectorResult:
    if scenario not in SUPPORTED_SAMPLE_SCENARIOS:
        raise validation_error(
            "INVALID_SAMPLE_SCENARIO",
            "The requested sample scenario does not exist.",
            scenario=scenario,
            details=[
                {
                    "field": "scenario",
                    "message": "Use one of the supported synthetic sample scenarios.",
                    "supported_scenarios": list(SUPPORTED_SAMPLE_SCENARIOS),
                }
            ],
        )

    samples = load_all_samples()
    sample = samples.get(scenario)
    if sample is None:
        raise validation_error(
            "SAMPLE_FILE_NOT_FOUND",
            "The configured sample scenario file was not found.",
            scenario=scenario,
        )

    return validate_collector_result(sample)
