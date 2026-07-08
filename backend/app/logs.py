from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse

from . import resource_assignment_analyzer as ra
from .access_run_store import get_access_report_markdown, get_access_run, list_access_runs, save_access_run
from .entra_signin_analyzer import SUPPORTED_SOURCE_TYPE as ENTRA_SIGNIN_CSV_SOURCE_TYPE
from .entra_signin_analyzer import analyze_entra_signin_export
from .log_analyzer import analyze_log_evidence
from .log_models import LogAnalysisResponse, LogAnalyzeRequest

router = APIRouter(tags=["logs"])


def _request_payload(request: LogAnalyzeRequest) -> Dict[str, Any]:
    return request.dict()


def _analyze(request: LogAnalyzeRequest) -> Dict[str, Any]:
    if request.source_type == ENTRA_SIGNIN_CSV_SOURCE_TYPE:
        return analyze_entra_signin_export(request).dict()
    if request.source_type == ra.SUPPORTED_SOURCE_TYPE:
        return ra.analyze_resource_assignment_evidence(request).dict()
    return analyze_log_evidence(request).dict()


@router.post("/api/logs/analyze", response_model=LogAnalysisResponse)
def analyze_logs(request: LogAnalyzeRequest) -> Dict[str, Any]:
    result = _analyze(request)
    return save_access_run(_request_payload(request), result)


@router.get("/api/logs/history")
def get_log_history(limit: int = 25) -> Dict[str, Any]:
    safe_limit = max(1, min(limit, 100))
    return {"items": list_access_runs(limit=safe_limit)}


@router.get("/api/logs/history/{run_id}")
def get_log_run(run_id: str) -> Dict[str, Any]:
    record = get_access_run(run_id)
    if not record:
        raise HTTPException(status_code=404, detail="Access evidence run not found")
    return record


@router.get("/api/logs/reports/{run_id}.md", response_class=PlainTextResponse)
def get_log_report_markdown(run_id: str) -> str:
    report = get_access_report_markdown(run_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Access evidence report not found")
    return report
