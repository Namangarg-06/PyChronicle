import json
import sqlite3
from pathlib import Path

from week3.db import ensure_schema, fetch_execution_records, insert_execution_record
from week3.tracer import ExecutionTracer, serialize_locals


def test_delta_serialization_and_replay(tmp_path: Path) -> None:
    db_path = tmp_path / "pychronicle.db"
    ensure_schema(db_path)

    previous = {"counter": 1, "name": "Ada", "flag": False}
    current = {"counter": 2, "name": "Ada", "flag": True, "new_value": "x"}

    previous_json = serialize_locals(previous)
    current_json = serialize_locals(current)

    insert_execution_record(
        timestamp="t1",
        filename="sample.py",
        function_name="main",
        line_number=10,
        locals_json=previous_json,
        db_path=db_path,
    )
    insert_execution_record(
        timestamp="t2",
        filename="sample.py",
        function_name="main",
        line_number=11,
        locals_json=current_json,
        db_path=db_path,
    )

    records = fetch_execution_records(db_path)
    assert len(records) == 2

    previous_state = json.loads(records[0]["locals_json"])
    current_state = json.loads(records[1]["locals_json"])

    assert previous_state["counter"] == 1
    assert current_state["counter"] == 2
    assert current_state["new_value"] == "x"

    tracer = ExecutionTracer(db_path=db_path, script_path=tmp_path / "sample.py")
    assert tracer._build_delta(previous_state, current_state) == {
        "counter": 2,
        "flag": True,
        "new_value": "x",
    }

    replay = tracer._replay_deltas(previous_state, [
        {"counter": 2, "flag": True, "new_value": "x"},
    ])
    assert replay["counter"] == 2
    assert replay["new_value"] == "x"

    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='execution_records'")
        assert cursor.fetchone() is not None
    finally:
        conn.close()
