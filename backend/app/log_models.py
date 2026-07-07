from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class LogAnalyzeRequest(BaseModel):
    source_type: str = Field(default="generic_access_log_text")
    affected_user: Optional[str] = None
    affected_service: Optional[str] = None
    content: str
    notes: Optional[str] = None


class NormalizedAccessEvent(BaseModel):
    timestamp: Optional[str] = None
    source_type: str
    event_type: str = "access"
    event_outcome: str = "unknown"
    user_principal_name: Optional[str] = None
    application: Optional[str] = None
    resource: Optional[str] = None
    client_app: Optional[str] = None
    ip_address: Optional[str] = None
    device_name: Optional[str] = None
    device_compliance: Optional[str] = None
    conditional_access_status: Optional[str] = None
    mfa_result: Optional[str] = None
    failure_reason: Optional[str] = None
    raw_message: str
    matched_keywords: List[str] = Field(default_factory=list)


class LogPattern(BaseModel):
    pattern_id: str
    title: str
    severity: str
    confidence: str
    event_indexes: List[int] = Field(default_factory=list)
    evidence: List[str] = Field(default_factory=list)


class LogAnalysisResponse(BaseModel):
    status: str
    source_type: str
    parse_status: str
    normalized_events: List[NormalizedAccessEvent]
    detected_patterns: List[LogPattern]
    primary_finding: Optional[Dict[str, Any]] = None
    findings: List[Dict[str, Any]] = Field(default_factory=list)
    summary: str
    confidence: str
    evidence_used: List[str] = Field(default_factory=list)
    evidence_missing: List[str] = Field(default_factory=list)
    safe_next_steps: List[str] = Field(default_factory=list)
    what_not_to_change_yet: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    report_markdown: str
