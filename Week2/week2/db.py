
from pathlib import Path
from typing import Optional


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
        
        

)