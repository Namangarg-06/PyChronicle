
import shutil
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

DEFAULT_DB_NAME = "pychronicle.db"


def resolve_db_path(db_path: Optional[str] = None) -> Path:
    """Resolve the database path from the provided value or parent directories."""
    if db_path:
        resolved = Path(db_path).expanduser().resolve()
        if resolved.exists() and resolved.is_file():
            return resolved

        resolved.parent.mkdir(parents=True, exist_ok=True)
        week1_db = Path(__file__).resolve().parents[2] / "pychoweek1" / DEFAULT_DB_NAME
        if week1_db.exists() and week1_db.is_file():
            shutil.copyfile(week1_db, resolved)
            return resolved

        raise FileNotFoundError(
            f"Database path '{resolved}' does not exist or is not a file. "
            "Provide an existing Week 1 SQLite database file."
        )

    base = Path.cwd()
    for candidate in [base] + list(base.parents):
        candidate_path = candidate / DEFAULT_DB_NAME
        if candidate_path.exists() and candidate_path.is_file():
            return candidate_path

    week2_dir = Path(__file__).resolve().parents[1]
    week2_db = week2_dir / DEFAULT_DB_NAME
    if not week2_db.exists():
        week1_db = Path(__file__).resolve().parents[2] / "pychoweek1" / DEFAULT_DB_NAME
        if week1_db.exists() and week1_db.is_file():
            shutil.copyfile(week1_db, week2_db)
            return week2_db

    if week2_db.exists() and week2_db.is_file():
        return week2_db

    raise FileNotFoundError(
        f"Could not locate an existing SQLite database file named '{DEFAULT_DB_NAME}'. "
        "Provide --db-path to specify the path explicitly."
    )


def ensure_schema(db_path: Path) -> None:
    """Create the execution_records table if it doesn't exist."""
    conn = sqlite3.connect(str(db_path))
    try:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS execution_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                filename TEXT NOT NULL,
                function_name TEXT NOT NULL,
                line_number INTEGER NOT NULL,
                locals_json TEXT NOT NULL
            )
        """)
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
    """Insert a new execution record into the database."""
    conn = sqlite3.connect(str(db_path))
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO execution_records (timestamp, filename, function_name, line_number, locals_json)
            VALUES (?, ?, ?, ?, ?)
        """, (timestamp, filename, function_name, line_number, locals_json))
        conn.commit()
    finally:
        conn.close()


def fetch_execution_records(db_path: Path) -> List[Dict[str, Any]]:
    """Fetch all execution records from the database, ordered by ID."""
    conn = sqlite3.connect(str(db_path))
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, timestamp, filename, function_name, line_number, locals_json
            FROM execution_records
            ORDER BY id ASC
        """)
        rows = cursor.fetchall()
        records = []
        for row in rows:
            records.append({
                "id": row[0],
                "timestamp": row[1],
                "filename": row[2],
                "function_name": row[3],
                "line_number": row[4],
                "locals_json": row[5],
            })
        return records
    finally:
        conn.close()
