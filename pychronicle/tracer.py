import sys
import os
import copy
from typing import Any, Dict, Optional
from pychronicle.storage import StateStorage

def should_trace_variable(name: str, value: Any) -> bool:
    return not (name.startswith("__") and name.endswith("__")) and not isinstance(value, (type(sys), type)) and not hasattr(value, '__call__')

class Tracer:
    """Traces target script executions and logs variable mutations."""
    def __init__(self, target_path: str, storage: StateStorage):
        self.target_path = os.path.abspath(target_path)
        self.storage = storage
        self.frame_states: Dict[int, Dict[str, Any]] = {}
        self.is_tracing = False

    def trace_callback(self, frame, event, arg):
        if os.path.abspath(frame.f_code.co_filename) != self.target_path:
            return self.trace_callback

        fid = id(frame)
        if fid not in self.frame_states:
            self.frame_states[fid] = {"prev_locals": {}, "prev_line": None}

        state = self.frame_states[fid]

        if event == 'line':
            lineno = frame.f_lineno
            if state["prev_line"] is None:
                self._log_mutations(lineno, frame.f_locals, {})
            else:
                self._log_mutations(state["prev_line"], frame.f_locals, state["prev_locals"])
            state["prev_line"] = lineno
            state["prev_locals"] = self._clone_locals(frame.f_locals)
            
        elif event == 'return':
            self._log_mutations(state["prev_line"], frame.f_locals, state["prev_locals"])
            self.frame_states.pop(fid, None)

        return self.trace_callback

    def _clone_locals(self, locals_dict: Dict[str, Any]) -> Dict[str, Any]:
        cloned = {}
        for k, v in locals_dict.items():
            if should_trace_variable(k, v):
                if isinstance(v, (int, float, str, bool, type(None), bytes, tuple)):
                    cloned[k] = v
                elif isinstance(v, list):
                    cloned[k] = v.copy()
                elif isinstance(v, dict):
                    cloned[k] = v.copy()
                elif isinstance(v, set):
                    cloned[k] = v.copy()
                else:
                    try:
                        cloned[k] = copy.deepcopy(v)
                    except Exception:
                        try:
                            cloned[k] = copy.copy(v)
                        except Exception:
                            cloned[k] = repr(v)
        return cloned

    def _log_mutations(self, line_num: Optional[int], current_locals: Dict[str, Any], prev_locals: Dict[str, Any]):
        if line_num is None:
            return
        for name, value in current_locals.items():
            if should_trace_variable(name, value):
                is_changed = name not in prev_locals
                if not is_changed:
                    try:
                        is_changed = (prev_locals[name] != value)
                    except Exception:
                        is_changed = (repr(prev_locals[name]) != repr(value))
                if is_changed:
                    self.storage.log_state(line_num, name, value)

    def run(self):
        if not os.path.exists(self.target_path):
            raise FileNotFoundError(f"Target script not found: {self.target_path}")

        with open(self.target_path, "r", encoding="utf-8") as f:
            compiled_code = compile(f.read(), self.target_path, "exec")

        globals_dict = {"__file__": self.target_path, "__name__": "__main__", "__doc__": None, "__package__": None}
        self.frame_states.clear()
        
        self.is_tracing = True
        sys.settrace(self.trace_callback)
        try:
            exec(compiled_code, globals_dict)
        finally:
            sys.settrace(None)
            self.is_tracing = False
            self.frame_states.clear()
            self.storage.commit()
