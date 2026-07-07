from typing import Any, Dict

from fastapi import APIRouter

from .entra_signin_analyzer import SUPPORTED_SOURCE_TYPE as ENTRA_SIGNIN_CSV_SOURCE_TYPE
from .entra_signin_analyzer import analyze_entra_signin_export
from .log_analyzer import analyze_log_evidence
from .log_models import LogAnalysisResponse, LogAnalyzeRequest

router = APIRouter(tags=["logs"])


@router.post("/api/logs/analyze", response_model=LogAnalysisResponse)
def analyze_logs(request: LogAnalyzeRequest) -> Dict[str, Any]:
    if request.source_type == ENTRA_SIGNIN_CSV_SOURCE_TYPE:
        return analyze_entra_signin_export(request).dict()
    return analyze_log_evidence(request).dict()
