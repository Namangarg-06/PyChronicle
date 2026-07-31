import json
import sqlite3
import time
from typing import Any, List, Dict, Optional

def serialize_value(value: Any) -> str:
    """Serializes a Python object to JSON. Falls back to repr() or custom string on failure."""
    try:
        return json.dumps(value, default=repr)
    except Exception:
        return json.dumps("<unserializable>")

def deserialize_value(serialized_str: str) -> Any:
    """Deserializes JSON back to Python structures, falling back to raw string."""
    try:
        return json.loads(serialized_str)
    except Exception:
        return serialized_str

class StateStorage:
    """SQLite wrapper for logging variable states."""
    def __init__(self, db_path: str = ":memory:"):
        self.conn = sqlite3.connect(db_path)
        self._init_db()

    def _init_db(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS state_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp INTEGER NOT NULL,
                line_number INTEGER NOT NULL,
                variable_name TEXT NOT NULL,
                serialized_value TEXT NOT NULL
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON state_log (timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_line_var ON state_log (line_number, variable_name)")
        self.conn.commit()

    def log_state(self, line_number: int, variable_name: str, value: Any, timestamp_ms: Optional[int] = None, auto_commit: bool = False) -> int:
        ts = timestamp_ms or (time.time_ns() // 1_000_000)
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO state_log (timestamp, line_number, variable_name, serialized_value) VALUES (?, ?, ?, ?)",
            (ts, line_number, variable_name, serialize_value(value))
        )
        if auto_commit:
            self.conn.commit()
        return cursor.lastrowid

    def commit(self):
        """Commits pending database transactions."""
        self.conn.commit()

    def get_history(self) -> List[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT timestamp, line_number, variable_name, serialized_value FROM state_log ORDER BY timestamp ASC, id ASC")
        return [
            {
                "timestamp": r[0],
                "line_number": r[1],
                "variable_name": r[2],
                "value": deserialize_value(r[3])
            }
            for r in cursor.fetchall()
        ]

    def get_variables_at_line(self, line_number: int) -> Dict[str, Any]:
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT variable_name, serialized_value FROM state_log 
            WHERE id IN (
                SELECT MAX(id) FROM state_log 
                WHERE line_number <= ? 
                GROUP BY variable_name
            )
        """, (line_number,))
        return {r[0]: deserialize_value(r[1]) for r in cursor.fetchall()}

    def clear(self):
        self.conn.cursor().execute("DELETE FROM state_log")
        self.conn.commit()

    def close(self):
        try:
            self.conn.commit()
        except Exception:
            pass
        self.conn.close()
