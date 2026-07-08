import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_STORE_DIR = REPO_ROOT / ".trace-runs" / "access-evidence"
RUN_ID_RE = re.compile(r"^[0-9]{14}-[a-z0-9_-]+-[a-f0-9]{8}$")


def _store_dir() -> Path:
    configured = os.getenv("TRACE_ACCESS_RUN_STORE")
    return Path(configured).resolve() if configured else DEFAULT_STORE_DIR


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _safe_source(value: str) -> str:
    cleaned = "".join(ch for ch in value.lower() if ch.isalnum() or ch in {"-", "_"})
    return cleaned or "access"


def _valid_run_id(run_id: str) -> bool:
    return bool(RUN_ID_RE.fullmatch(run_id))


def _run_path(run_id: str) -> Optional[Path]:
    if not _valid_run_id(run_id):
        return None
    return _store_dir() / f"{run_id}.json"


def _report_path(run_id: str) -> Optional[Path]:
    if not _valid_run_id(run_id):
        return None
    return _store_dir() / f"{run_id}.md"


def save_access_run(request_payload: Dict[str, Any], response_payload: Dict[str, Any]) -> Dict[str, Any]:
    store = _store_dir()
    store.mkdir(parents=True, exist_ok=True)

    source_type = str(response_payload.get("source_type") or request_payload.get("source_type") or "access")
    run_id = f"{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{_safe_source(source_type)}-{uuid4().hex[:8]}"
    created_at = _now()

    response_payload = dict(response_payload)
    response_payload["run_id"] = run_id

    record = {
        "run_id": run_id,
        "created_at": created_at,
        "source_type": source_type,
        "affected_user": request_payload.get("affected_user"),
        "affected_service": request_payload.get("affected_service"),
        "status": response_payload.get("status"),
        "primary_rule_id": (response_payload.get("primary_finding") or {}).get("rule_id"),
        "summary": response_payload.get("summary"),
        "confidence": response_payload.get("confidence"),
        "report_markdown": response_payload.get("report_markdown", ""),
        "response": response_payload,
    }

    run_path = _run_path(run_id)
    report_path = _report_path(run_id)
    if run_path is None or report_path is None:
        raise ValueError("Generated invalid run_id")

    run_path.write_text(json.dumps(record, indent=2, sort_keys=True), encoding="utf-8")
    report_path.write_text(record["report_markdown"], encoding="utf-8")
    return response_payload


def list_access_runs(limit: int = 25) -> List[Dict[str, Any]]:
    store = _store_dir()
    if not store.exists():
        return []

    items: List[Dict[str, Any]] = []
    for path in sorted(store.glob("*.json"), reverse=True):
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if not _valid_run_id(str(record.get("run_id") or "")):
            continue
        items.append(
            {
                "run_id": record.get("run_id"),
                "created_at": record.get("created_at"),
                "source_type": record.get("source_type"),
                "affected_user": record.get("affected_user"),
                "affected_service": record.get("affected_service"),
                "status": record.get("status"),
                "primary_rule_id": record.get("primary_rule_id"),
                "summary": record.get("summary"),
                "confidence": record.get("confidence"),
            }
        )
        if len(items) >= limit:
            break
    return items


def get_access_run(run_id: str) -> Optional[Dict[str, Any]]:
    path = _run_path(run_id)
    if path is None or not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def get_access_report_markdown(run_id: str) -> Optional[str]:
    report = _report_path(run_id)
    if report is not None and report.exists():
        return report.read_text(encoding="utf-8")
    record = get_access_run(run_id)
    if record:
        return str(record.get("report_markdown") or "")
    return None
