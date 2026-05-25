import json
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional

from pydantic import BaseModel

from .collector_contract import validate_collector_result
from .config import COLLECTOR_SCRIPT_PATH, COLLECTOR_TIMEOUT_SECONDS
from .errors import BackendValidationError
from .models import CollectorErrorResult, CollectorResult


def _model_to_dict(model: BaseModel) -> Dict[str, Any]:
    return model.model_dump()


def _runner_error(
    code: str,
    message: str,
    *,
    return_code: Optional[int] = None,
    stderr: str = "",
    details: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    error: Dict[str, Any] = {
        "code": code,
        "message": message,
    }
    if return_code is not None:
        error["return_code"] = return_code
    if stderr:
        error["stderr"] = stderr
    if details:
        error["details"] = details

    return {
        "status": "error",
        "error": error,
    }


def _quote_powershell_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def build_collector_command(
    *,
    user_principal_name: str,
    affected_service: str,
    scenario: str,
    collector_script_path: Path = COLLECTOR_SCRIPT_PATH,
    powershell_executable: str = "powershell",
) -> list[str]:
    command_script = (
        f"& {_quote_powershell_literal(str(collector_script_path))} "
        f"-UserPrincipalName {_quote_powershell_literal(user_principal_name)} "
        f"-AffectedService {_quote_powershell_literal(affected_service)} "
        f"-Scenario {_quote_powershell_literal(scenario)} "
        "-UseSampleData:$true"
    )

    return [
        powershell_executable,
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-Command",
        command_script,
    ]


def run_m365_access_collector(
    *,
    user_principal_name: str,
    affected_service: str,
    scenario: str,
    collector_script_path: Path = COLLECTOR_SCRIPT_PATH,
    timeout_seconds: int = COLLECTOR_TIMEOUT_SECONDS,
    powershell_executable: str = "powershell",
) -> Dict[str, Any]:
    if not collector_script_path.exists():
        return _runner_error(
            "COLLECTOR_SCRIPT_NOT_FOUND",
            "The configured collector script was not found.",
            details={"collector_script_path": str(collector_script_path)},
        )

    command = build_collector_command(
        user_principal_name=user_principal_name,
        affected_service=affected_service,
        scenario=scenario,
        collector_script_path=collector_script_path,
        powershell_executable=powershell_executable,
    )

    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            shell=False,
        )
    except subprocess.TimeoutExpired:
        return _runner_error(
            "COLLECTOR_TIMEOUT",
            "The collector process timed out.",
            details={"timeout_seconds": timeout_seconds},
        )

    if completed.returncode != 0:
        return _runner_error(
            "COLLECTOR_PROCESS_FAILED",
            "The collector process exited with a non-zero status.",
            return_code=completed.returncode,
            stderr=completed.stderr,
        )

    try:
        parsed_stdout = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        return _runner_error(
            "INVALID_COLLECTOR_STDOUT",
            "The collector stdout was not valid JSON.",
            stderr=completed.stderr,
            details={"json_error": str(exc)},
        )

    try:
        validated = validate_collector_result(parsed_stdout)
    except BackendValidationError as exc:
        return _runner_error(
            "COLLECTOR_OUTPUT_VALIDATION_FAILED",
            "The collector JSON output failed backend validation.",
            stderr=completed.stderr,
            details=exc.to_dict()["error"],
        )

    if isinstance(validated, CollectorErrorResult):
        return {
            "status": "collector_error",
            "return_code": completed.returncode,
            "stderr": completed.stderr,
            "collector_error": _model_to_dict(validated),
        }

    if isinstance(validated, CollectorResult):
        return {
            "status": "ok",
            "return_code": completed.returncode,
            "stderr": completed.stderr,
            "result": _model_to_dict(validated),
        }

    return _runner_error(
        "UNEXPECTED_COLLECTOR_VALIDATION_RESULT",
        "Collector validation returned an unexpected result type.",
    )
