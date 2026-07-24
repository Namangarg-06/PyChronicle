import sys
import json
import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from week2.db import insert_execution_record


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
    """Tracer that records executed lines with timestamp and locals."""

    def __init__(self, db_path: Path, script_path: Path, globals_obj: Optional[Dict[str, Any]] = None):
        self.db_path = db_path
        self.script_path = script_path.resolve()
        self._root_filename = str(self.script_path)
        self.globals_obj = globals_obj if globals_obj is not None else {}
        self._should_stop = False

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
        record = {
            "timestamp": timestamp,
            "filename": filename,
            "function_name": code.co_name,
            "line_number": frame.f_lineno,
            "locals_json": serialize_locals(frame.f_locals),
        }

        insert_execution_record(
            timestamp=record["timestamp"],
            filename=record["filename"],
            function_name=record["function_name"],
            line_number=record["line_number"],
            locals_json=record["locals_json"],
            db_path=self.db_path,
        )

        return self._trace

    def run(self) -> None:
        """Run the target script under tracing."""
        sys.settrace(self._trace)
        try:
            with open(self.script_path, "rb") as script_file:
                compiled_code = compile(script_file.read(), str(self.script_path), "exec")
            exec(compiled_code, self.globals_obj, self.globals_obj)
        finally:
            sys.settrace(None)
