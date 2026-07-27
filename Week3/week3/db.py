import shutil
from pathlib import Path
from typing import Optional

from shared.db import (
    DEFAULT_DB_NAME,
    ensure_schema,
    fetch_execution_records,
    insert_execution_record,
)


def resolve_db_path(db_path: Optional[str] = None) -> Path:
    """Resolve the database path for Week 3, reusing the existing Week 2 database when needed."""
    if db_path:
        resolved = Path(db_path).expanduser().resolve()
        if resolved.exists() and resolved.is_file():
            return resolved

        resolved.parent.mkdir(parents=True, exist_ok=True)
        week2_db = Path(__file__).resolve().parents[2] / "Week2" / DEFAULT_DB_NAME
        if week2_db.exists() and week2_db.is_file():
            shutil.copyfile(week2_db, resolved)
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

    week3_dir = Path(__file__).resolve().parents[1]
    week3_db = week3_dir / DEFAULT_DB_NAME
    if not week3_db.exists():
        week2_db = Path(__file__).resolve().parents[2] / "Week2" / DEFAULT_DB_NAME
        if week2_db.exists() and week2_db.is_file():
            shutil.copyfile(week2_db, week3_db)
            return week3_db

    if week3_db.exists() and week3_db.is_file():
        return week3_db

    raise FileNotFoundError(
        f"Could not locate an existing SQLite database file named '{DEFAULT_DB_NAME}'. "
        "Provide --db-path to specify the path explicitly."
    )
