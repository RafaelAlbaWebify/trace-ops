from typing import Any, Dict

from fastapi import APIRouter
from fastapi.responses import HTMLResponse, JSONResponse

from .analyzer import analyze_collector_result
from .config import FIRST_MODULE_ID, HISTORY_DB_PATH
from .collector_runner import run_m365_access_collector
from .models import CollectorResult, ScanRequest
from .report_builder import build_html_report, build_json_report
from .storage import get_scan_history_record, list_scan_history, save_scan_record

router = APIRouter(tags=["scan"])


def _scan_error_response(error: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "status": "error",
        "error": {
            "code": error.get("code", "BACKEND_RUNNER_ERROR"),
            "message": error.get("message", "The backend could not complete the sample scan."),
        },
    }


def _save_scan_history(request: ScanRequest, response: Dict[str, Any]) -> Dict[str, Any]:
    try:
        record_id = save_scan_record(
            module=FIRST_MODULE_ID,
            scenario=request.scenario,
            user_principal_name=request.user_principal_name,
            affected_service=request.affected_service,
            status=response["status"],
            result=response,
            db_path=HISTORY_DB_PATH,
        )
    except Exception as exc:
        return {
            "status": "error",
            "error": {
                "code": "HISTORY_SAVE_FAILED",
                "message": "The backend could not save the scan history record.",
            },
            "scan_response": response,
        }

    response["history_id"] = record_id
    return response


@router.post("/api/scan/user-access")
def scan_user_access(request: ScanRequest) -> Dict[str, Any]:
    runner_result = run_m365_access_collector(
        user_principal_name=request.user_principal_name,
        affected_service=request.affected_service,
        scenario=request.scenario,
    )

    if runner_result["status"] == "ok":
        validated_result = CollectorResult(**runner_result["result"])
        return _save_scan_history(request, {
            "status": "ok",
            "result": runner_result["result"],
            "analysis": analyze_collector_result(validated_result),
        })

    if runner_result["status"] == "collector_error":
        collector_error = runner_result["collector_error"]["error"]
        return _save_scan_history(request, {
            "status": "collector_error",
            "error": collector_error,
        })

    return _save_scan_history(request, _scan_error_response(runner_result.get("error", {})))


@router.get("/api/history")
def get_history() -> Dict[str, Any]:
    return {
        "status": "ok",
        "records": list_scan_history(db_path=HISTORY_DB_PATH),
    }


def _missing_history_response(history_id: int) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={
            "status": "error",
            "error": {
                "code": "HISTORY_RECORD_NOT_FOUND",
                "message": "The requested scan history record does not exist.",
                "history_id": history_id,
            },
        },
    )


@router.get("/api/history/{history_id}/report.json")
def get_json_report(history_id: int):
    record = get_scan_history_record(history_id, db_path=HISTORY_DB_PATH)
    if record is None:
        return _missing_history_response(history_id)

    return build_json_report(record["result_json"])


@router.get("/api/history/{history_id}/report.html", response_class=HTMLResponse)
def get_html_report(history_id: int):
    record = get_scan_history_record(history_id, db_path=HISTORY_DB_PATH)
    if record is None:
        return _missing_history_response(history_id)

    return HTMLResponse(content=build_html_report(record["result_json"]))
