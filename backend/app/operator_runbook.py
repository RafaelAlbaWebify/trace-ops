from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(tags=["operator-runbook"])

RUNBOOK_CONTRACT_VERSION = "trace-operator-runbook-preview-v1"


class RunbookPreviewRequest(BaseModel):
    case_title: str = Field(min_length=1, max_length=160)
    module: str = Field(min_length=1, max_length=120)
    diagnostic_type: str = Field(min_length=1, max_length=120)
    target: str = Field(min_length=1, max_length=320)
    status: str = Field(default="unknown", max_length=60)
    findings: List[Dict[str, Any]] = Field(default_factory=list)
    evidence_summary: Dict[str, Any] = Field(default_factory=dict)
    safe_next_steps: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    operator_notes: Optional[str] = Field(default=None, max_length=1000)


def _strings(values: List[Any]) -> List[str]:
    return [str(value) for value in values if str(value).strip()]


def _finding_title(finding: Dict[str, Any]) -> str:
    return str(
        finding.get("finding_id")
        or finding.get("rule_id")
        or finding.get("title")
        or "UNSPECIFIED_FINDING"
    )


def _severity_counts(findings: List[Dict[str, Any]]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for finding in findings:
        severity = str(finding.get("severity") or "unknown").lower()
        counts[severity] = counts.get(severity, 0) + 1
    return counts


def _build_operator_steps(request: RunbookPreviewRequest) -> List[Dict[str, Any]]:
    steps: List[Dict[str, Any]] = [
        {
            "step": 1,
            "title": "Confirm case scope",
            "action": f"Confirm the target '{request.target}' and affected diagnostic area '{request.diagnostic_type}' before taking any action.",
            "evidence_required": ["User/service affected", "Timestamp or business impact", "Current TRACE diagnostic status"],
            "safety_note": "Do not change configuration while the case scope is still ambiguous.",
        },
        {
            "step": 2,
            "title": "Review TRACE evidence",
            "action": "Review findings, evidence used, missing evidence, confidence, and limitations in the generated TRACE report.",
            "evidence_required": ["TRACE finding IDs", "Evidence used", "Evidence missing", "Limitations"],
            "safety_note": "Treat TRACE output as diagnostic guidance, not an automatic remediation instruction.",
        },
    ]

    if request.findings:
        steps.append(
            {
                "step": 3,
                "title": "Validate primary finding externally",
                "action": f"Validate the primary finding '{_finding_title(request.findings[0])}' with the relevant admin console, logs, or homelab evidence.",
                "evidence_required": _strings(request.findings[0].get("evidence_used", [])) or ["Independent confirmation evidence"],
                "safety_note": "Do not remediate from a single signal if required evidence is missing.",
            }
        )
    else:
        steps.append(
            {
                "step": 3,
                "title": "Collect missing diagnostic evidence",
                "action": "No blocking finding was provided. Collect additional evidence before recommending a change.",
                "evidence_required": ["Recent logs", "Current configuration evidence", "Known-good comparison"],
                "safety_note": "No finding means no remediation recommendation.",
            }
        )

    steps.append(
        {
            "step": 4,
            "title": "Apply safe next diagnostic steps",
            "action": "Follow the safe next steps listed by TRACE and document the result of each check.",
            "evidence_required": request.safe_next_steps or ["At least one documented safe diagnostic step"],
            "safety_note": "Safe next steps must remain read-only unless a separate approved remediation workflow exists.",
        }
    )

    steps.append(
        {
            "step": 5,
            "title": "Escalate or close with evidence",
            "action": "Escalate if evidence is incomplete or close the case only when the cause and outcome are documented.",
            "evidence_required": ["Root cause or limitation", "Evidence trail", "Operator notes"],
            "safety_note": "Do not hide limitations; include them in the handoff or closure note.",
        }
    )

    return steps


def preview_operator_runbook(request: RunbookPreviewRequest) -> Dict[str, Any]:
    finding_count = len(request.findings)
    primary_finding = request.findings[0] if request.findings else None

    limitations = list(request.limitations)
    limitations.append("Phase 9 generates an operator runbook preview only; it does not execute diagnostics or remediation.")

    return {
        "status": "ok",
        "module": "operator-runbook-preview",
        "check": "operator_runbook_preview",
        "runbook_contract_version": RUNBOOK_CONTRACT_VERSION,
        "case": {
            "title": request.case_title,
            "source_module": request.module,
            "diagnostic_type": request.diagnostic_type,
            "target": request.target,
            "diagnostic_status": request.status,
            "operator_notes": request.operator_notes,
        },
        "executive_summary": {
            "finding_count": finding_count,
            "severity_counts": _severity_counts(request.findings),
            "primary_finding": _finding_title(primary_finding) if primary_finding else None,
            "recommended_operator_posture": "validate-evidence-before-change",
        },
        "operator_steps": _build_operator_steps(request),
        "safe_next_steps": request.safe_next_steps,
        "limitations": limitations,
        "handoff_template": {
            "summary": f"TRACE reviewed {request.diagnostic_type} for {request.target} with status {request.status}.",
            "evidence_to_attach": ["TRACE JSON report", "TRACE HTML report", "Screenshots or logs from the source system if available"],
            "questions_for_next_team": [
                "Is the missing evidence available in an admin console or log source?",
                "Is there an approved remediation/change workflow for this environment?",
            ],
        },
        "read_only_boundary": {
            "preview_only": True,
            "diagnostics_executed": False,
            "remediation_performed": False,
            "configuration_changed": False,
            "credentials_or_tokens_stored": False,
            "tenant_wide_scan_performed": False,
        },
    }


@router.post("/api/operator/runbook/preview")
def post_operator_runbook_preview(request: RunbookPreviewRequest) -> Dict[str, Any]:
    return preview_operator_runbook(request)
