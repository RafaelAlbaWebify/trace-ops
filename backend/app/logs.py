from typing import Dict, Any

from fastapi import APIRouter

from .log_analyzer import analyze_log_evidence
from .log_models import LogAnalyzeRequest, LogAnalysisResponse

router = APIRouter(tags=["logs"])


@router.post("/api/logs/analyze", response_model=LogAnalysisResponse)
def analyze_logs(request: LogAnalyzeRequest) -> Dict[str, Any]:
    return analyze_log_evidence(request).dict()
