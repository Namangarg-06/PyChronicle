import sqlite3
import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

DB_SCHEMA = {
    "execution_records": (
        "id INTEGER PRIMARY KEY AUTOINCREMENT,"
        "timestamp TEXT NOT NULL,"
        "filename TEXT NOT NULL,"
        "function_name TEXT NOT NULL,"
        "line_number INTEGER NOT NULL,"
        "locals_json TEXT NOT NULL"
    ),
}

DEFAULT_DB_NAME = "pychronicle.db"


def resolve_db_path(db_path: Optional[str] = None) -> Path:
    """Resolve the database path from the provided value or parent directories."""
    if db_path:
        resolved = Path(db_path).expanduser().resolve()
        if not resolved.exists() or not resolved.is_file():
            raise FileNotFoundError(
                f"Database path '{resolved}' does not exist or is not a file. "
                "Provide an existing Week 1 SQLite database file."
            )
        return resolved

    base = Path.cwd()
    for candidate in [base] + list(base.parents):
        candidate_path = candidate / DEFAULT_DB_NAME
        if candidate_path.exists() and candidate_path.is_file():
            return candidate_path

    raise FileNotFoundError(
        f"Could not locate an existing SQLite database file named '{DEFAULT_DB_NAME}'. "
        "Provide --db-path to specify the path explicitly."
    )


def ensure_schema(db_path: Path) -> None:
    """Ensure the schema required for Week 2 execution tracing exists."""
    conn = sqlite3.connect(str(db_path))
    try:
        cursor = conn.cursor()
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS execution_records (" + DB_SCHEMA["execution_records"] + ")"
        )
        conn.commit()
    finally:
        conn.close()


def insert_execution_record(
    timestamp: str,
    filename: str,
    function_name: str,
    line_number: int,
    locals_json: str,
    db_path: Path,
) -> None:
    """Insert a single execution record into the database."""
    conn = sqlite3.connect(str(db_path))
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO execution_records (timestamp, filename, function_name, line_number, locals_json) VALUES (?, ?, ?, ?, ?)",
            (timestamp, filename, function_name, line_number, locals_json),
        )
        conn.commit()
    finally:
        conn.close()


def fetch_execution_records(db_path: Path) -> List[Dict[str, Any]]:
    """Fetch all recorded execution events."""
    conn = sqlite3.connect(str(db_path))
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, timestamp, filename, function_name, line_number, locals_json FROM execution_records ORDER BY id"
        )
        rows = cursor.fetchall()
        return [
            {
                "id": row[0],
                "timestamp": row[1],
                "filename": row[2],
                "function_name": row[3],
                "line_number": row[4],
                "locals_json": row[5],
            }
            for row in rows
        ]
    finally:
        conn.close()
