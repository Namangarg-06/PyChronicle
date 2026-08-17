import sqlite3
import datetime
from typing import List, Dict, Any

DB_NAME = "pychronicle.db"

def init_db(db_path: str = DB_NAME):
    """
    Initializes the SQLite database and creates the variable_states table.
    
    Args:
        db_path (str): Path to the SQLite database file.
    """
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS variable_states (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                line_number INTEGER NOT NULL,
                variable_name TEXT NOT NULL,
                serialized_value TEXT NOT NULL
            )
        """)
        conn.commit()

def insert_variable_state(
    line_number: int, 
    variable_name: str, 
    serialized_value: str, 
    db_path: str = DB_NAME
):
    """
    Inserts a variable assignment state record into the database.
    
    Args:
        line_number (int): Line number where assignment occurred.
        variable_name (str): Name of the variable.
        serialized_value (str): Evaluated or static string representation of the assigned value.
        db_path (str): Path to the SQLite database file.
    """ 
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        timestamp = datetime.datetime.now().isoformat()
        cursor.execute("""
            INSERT INTO variable_states (timestamp, line_number, variable_name, serialized_value)
            VALUES (?, ?, ?, ?)
        """, (timestamp, line_number, variable_name, serialized_value))
        conn.commit()

def get_all_variable_states(db_path: str = DB_NAME) -> List[Dict[str, Any]]:
    """
    Fetches all recorded variable state assignments from the database.
    
    Args:
        db_path (str): Path to the SQLite database file.
        
    Returns:
        List[Dict[str, Any]]: List of dictionary rows containing the stored metadata.
    """
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT id, timestamp, line_number, variable_name, serialized_value FROM variable_states")
        rows = cursor.fetchall()
        
        if rows:
            return [dict(row) for row in rows]
        return []
