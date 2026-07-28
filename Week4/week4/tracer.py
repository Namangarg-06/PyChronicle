import datetime
import json
import logging
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from week4.db import insert_execution_record

logger = logging.getLogger(__name__)


def serialize_locals(locals_dict: Dict[str, Any]) -> str:
    """Serialize locals using JSON-safe fallback for common types."""
    serialized: Dict[str, Any] = {}
    for key, value in locals_dict.items():
        try:
            json.dumps(value)
            serialized[key] = value
        except (TypeError, ValueError):
            try:
                serialized[key] = repr(value)
            except Exception:
                serialized[key] = "<unserializable>"
    return json.dumps(serialized)


class ExecutionTracer:
    """Tracer that records executed lines with timestamps and compact state deltas."""

    def __init__(self, db_path: Path, script_path: Path, globals_obj: Optional[Dict[str, Any]] = None):
        self.db_path = db_path
        self.script_path = script_path.resolve()
        self._root_filename = str(self.script_path)
        self.globals_obj = globals_obj if globals_obj is not None else {}
        self._previous_state: Optional[Dict[str, Any]] = None

    def _serialize_state_payload(self, current_state: Dict[str, Any]) -> str:
        if self._previous_state is None:
            return json.dumps(current_state)

        delta = self._build_delta(self._previous_state, current_state)
        return json.dumps({"__pychronicle_payload__": "delta", "changes": delta})

    def _build_delta(self, previous_state: Optional[Dict[str, Any]], current_state: Dict[str, Any]) -> Dict[str, Any]:
        if previous_state is None:
            return dict(current_state)

        delta: Dict[str, Any] = {}
        for key, value in current_state.items():
            previous_value = previous_state.get(key)
            if previous_value != value:
                delta[key] = value
        return delta

    def _replay_deltas(self, previous_state: Optional[Dict[str, Any]], delta_records: List[Dict[str, Any]]) -> Dict[str, Any]:
        state = dict(previous_state or {})
        for delta in delta_records:
            if not isinstance(delta, dict):
                continue
            for key, value in delta.items():
                state[key] = value
        return state

    def _deserialize_state(self, payload: Any, previous_state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if not isinstance(payload, dict):
            return {}

        if payload.get("__pychronicle_payload__") == "delta":
            return self._replay_deltas(previous_state, [payload.get("changes", {})])

        return dict(payload)

    def build_execution_snapshots(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Reconstruct execution states for each recorded step."""
        snapshots: List[Dict[str, Any]] = []
        previous_state: Optional[Dict[str, Any]] = None
        for record in records:
            payload = json.loads(record.get("locals_json", "{}"))
            state = self._deserialize_state(payload, previous_state)
            snapshots.append({"record": record, "state": state})
            previous_state = state
        return snapshots

    def _trace(self, frame: Any, event: str, arg: Any) -> Optional[Callable]:
        if event != "line":
            return self._trace

        code = frame.f_code
        filename = code.co_filename
        if not filename or filename == "<string>":
            filename = self._root_filename

        if Path(filename).resolve() != self.script_path:
            return self._trace

        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
        current_state = json.loads(serialize_locals(frame.f_locals))
        payload = self._serialize_state_payload(current_state)

        record = {
            "timestamp": timestamp,
            "filename": filename,
            "function_name": code.co_name,
            "line_number": frame.f_lineno,
            "locals_json": payload,
        }

        insert_execution_record(
            timestamp=record["timestamp"],
            filename=record["filename"],
            function_name=record["function_name"],
            line_number=record["line_number"],
            locals_json=record["locals_json"],
            db_path=self.db_path,
        )

        self._previous_state = current_state
        return self._trace

    def run(self) -> None:
        """Run the target script under tracing."""
        self._previous_state = None
        sys.settrace(self._trace)
        try:
            with open(self.script_path, "rb") as script_file:
                compiled_code = compile(script_file.read(), str(self.script_path), "exec")
            exec(compiled_code, self.globals_obj, self.globals_obj)
        except Exception as exc:
            logger.exception("Tracing failed for %s", self.script_path)
            raise RuntimeError(f"Execution of '{self.script_path}' failed") from exc
        finally:
            sys.settrace(None)
