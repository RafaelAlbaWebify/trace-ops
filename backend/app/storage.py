import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from .config import HISTORY_DB_PATH


def initialize_database(db_path: Path = HISTORY_DB_PATH) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    try:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS scan_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                module TEXT NOT NULL,
                scenario TEXT NOT NULL,
                user_principal_name TEXT NOT NULL,
                affected_service TEXT NOT NULL,
                status TEXT NOT NULL,
                result_json TEXT NOT NULL
            )
            """
        )
        connection.commit()
    finally:
        connection.close()


def save_scan_record(
    *,
    module: str,
    scenario: str,
    user_principal_name: str,
    affected_service: str,
    status: str,
    result: Dict[str, Any],
    db_path: Path = HISTORY_DB_PATH,
) -> int:
    initialize_database(db_path)
    created_at = datetime.now(timezone.utc).isoformat()
    result_json = json.dumps(result, sort_keys=True)

    connection = sqlite3.connect(db_path)
    try:
        cursor = connection.execute(
            """
            INSERT INTO scan_history (
                created_at,
                module,
                scenario,
                user_principal_name,
                affected_service,
                status,
                result_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                created_at,
                module,
                scenario,
                user_principal_name,
                affected_service,
                status,
                result_json,
            ),
        )
        connection.commit()
        return int(cursor.lastrowid)
    finally:
        connection.close()


def list_scan_history(
    *,
    limit: int = 25,
    db_path: Path = HISTORY_DB_PATH,
) -> List[Dict[str, Any]]:
    initialize_database(db_path)
    connection = sqlite3.connect(db_path)
    try:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT
                id,
                created_at,
                module,
                scenario,
                user_principal_name,
                affected_service,
                status,
                result_json
            FROM scan_history
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    finally:
        connection.close()

    return [
        {
            "id": row["id"],
            "created_at": row["created_at"],
            "module": row["module"],
            "scenario": row["scenario"],
            "user_principal_name": row["user_principal_name"],
            "affected_service": row["affected_service"],
            "status": row["status"],
            "result_json": json.loads(row["result_json"]),
        }
        for row in rows
    ]


def get_scan_history_record(
    history_id: int,
    *,
    db_path: Path = HISTORY_DB_PATH,
) -> Dict[str, Any] | None:
    initialize_database(db_path)
    connection = sqlite3.connect(db_path)
    try:
        connection.row_factory = sqlite3.Row
        row = connection.execute(
            """
            SELECT
                id,
                created_at,
                module,
                scenario,
                user_principal_name,
                affected_service,
                status,
                result_json
            FROM scan_history
            WHERE id = ?
            """,
            (history_id,),
        ).fetchone()
    finally:
        connection.close()

    if row is None:
        return None

    return {
        "id": row["id"],
        "created_at": row["created_at"],
        "module": row["module"],
        "scenario": row["scenario"],
        "user_principal_name": row["user_principal_name"],
        "affected_service": row["affected_service"],
        "status": row["status"],
        "result_json": json.loads(row["result_json"]),
    }
