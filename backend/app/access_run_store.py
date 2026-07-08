import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4


DEFAULT_STORE_DIR = Path(".trace-runs") / "access-evidence"


def _store_dir() -> Path:
    configured = os.getenv("TRACE_ACCESS_RUN_STORE")
    return Path(configured) if configured else DEFAULT_STORE_DIR


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _safe_source(value: str) -> str:
    cleaned = "".join(ch for ch in value.lower() if ch.isalnum() or ch in {"-", "_"})
    return cleaned or "access"


def _run_path(run_id: str) -> Path:
    return _store_dir() / f"{run_id}.json"


def _report_path(run_id: str) -> Path:
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

    _run_path(run_id).write_text(json.dumps(record, indent=2, sort_keys=True), encoding="utf-8")
    _report_path(run_id).write_text(record["report_markdown"], encoding="utf-8")
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
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def get_access_report_markdown(run_id: str) -> Optional[str]:
    report = _report_path(run_id)
    if report.exists():
        return report.read_text(encoding="utf-8")
    record = get_access_run(run_id)
    if record:
        return str(record.get("report_markdown") or "")
    return None
