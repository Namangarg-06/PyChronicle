import shutil
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

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
    """Resolve an existing PyChronicle SQLite database path for Week 4."""
    if db_path:
        resolved = Path(db_path).expanduser().resolve()
        if resolved.exists() and resolved.is_file():
            return resolved

        resolved.parent.mkdir(parents=True, exist_ok=True)
        week2_db = Path(__file__).resolve().parents[2] / "Week2" / DEFAULT_DB_NAME
        week3_db = Path(__file__).resolve().parents[2] / "Week3" / DEFAULT_DB_NAME
        for candidate in (week2_db, week3_db):
            if candidate.exists() and candidate.is_file():
                shutil.copyfile(candidate, resolved)
                return resolved

        raise FileNotFoundError(
            f"Database path '{resolved}' does not exist or is not a file. "
            "Provide an existing Week 1/2/3 SQLite database file."
        )

    base = Path.cwd()
    for candidate in [base] + list(base.parents):
        candidate_path = candidate / DEFAULT_DB_NAME
        if candidate_path.exists() and candidate_path.is_file():
            return candidate_path

    week4_dir = Path(__file__).resolve().parents[1]
    week4_db = week4_dir / DEFAULT_DB_NAME
    if not week4_db.exists():
        for candidate in (
            Path(__file__).resolve().parents[2] / "Week2" / DEFAULT_DB_NAME,
            Path(__file__).resolve().parents[2] / "Week3" / DEFAULT_DB_NAME,
        ):
            if candidate.exists() and candidate.is_file():
                shutil.copyfile(candidate, week4_db)
                return week4_db

    if week4_db.exists() and week4_db.is_file():
        return week4_db

    raise FileNotFoundError(
        f"Could not locate an existing SQLite database file named '{DEFAULT_DB_NAME}'. "
        "Provide --db-path to specify the path explicitly."
    )


def ensure_schema(db_path: Path) -> None:
    """Ensure the execution_records table exists."""
    with sqlite3.connect(str(db_path)) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS execution_records (" + DB_SCHEMA["execution_records"] + ")"
        )
        conn.commit()


def insert_execution_record(
    timestamp: str,
    filename: str,
    function_name: str,
    line_number: int,
    locals_json: str,
    db_path: Path,
) -> None:
    """Insert a single execution record into the database."""
    ensure_schema(db_path)
    with sqlite3.connect(str(db_path)) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO execution_records (timestamp, filename, function_name, line_number, locals_json) VALUES (?, ?, ?, ?, ?)",
            (timestamp, filename, function_name, line_number, locals_json),
        )
        conn.commit()


def fetch_execution_records(db_path: Path) -> List[Dict[str, Any]]:
    """Fetch all recorded execution events."""
    with sqlite3.connect(str(db_path)) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, timestamp, filename, function_name, line_number, locals_json FROM execution_records ORDER BY id"
        )
        rows = cursor.fetchall()
        if rows:
            return [dict(row) for row in rows]
    return []
