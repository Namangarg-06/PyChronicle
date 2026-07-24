from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from rich.syntax import Syntax
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal
from textual.message import Message
from textual.widgets import Footer, Header, Static
from textual.widgets._rich_log import RichLog

from week3.db import fetch_execution_records
from week3.tracer import ExecutionTracer


class CodeViewer(Static):
    def __init__(self, script_path: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.script_path = script_path
        self.code_lines = self._load_source()

    def _load_source(self) -> List[str]:
        with open(self.script_path, "r", encoding="utf-8") as source_file:
            return source_file.readlines()

    def highlight_line(self, line_number: int) -> None:
        highlight_lines = {line_number} if line_number else set()
        syntax = Syntax(
            "".join(self.code_lines),
            self.script_path.suffix.lstrip("."),
            line_numbers=True,
            highlight_lines=highlight_lines,
        )
        self.update(syntax)


class VariablesPanel(Static):
    def show_state(self, state: Optional[Dict[str, Any]]) -> None:
        if not state:
            self.update("No variables captured yet.")
            return

        lines = []
        for key, value in sorted(state.items()):
            lines.append(f"{key} = {self._format_value(value)}")
        self.update("\n".join(lines))

    def _format_value(self, value: Any) -> str:
        if isinstance(value, str):
            return repr(value)
        if isinstance(value, (dict, list, tuple, set)):
            return json.dumps(value, indent=2, sort_keys=True)
        return str(value)


class TimelineChanged(Message):
    def __init__(self, index: int) -> None:
        super().__init__()
        self.index = index


class TimelineSlider(Static):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.can_focus = True
        self._steps = 0
        self._value = 0

    def set_steps(self, steps: int) -> None:
        self._steps = max(0, steps)
        self._value = min(self._value, self._steps - 1 if self._steps else 0)
        self.refresh()

    def set_value(self, value: int) -> None:
        self._value = max(0, min(self._steps - 1 if self._steps else 0, value))
        self.refresh()

    def _emit_change(self) -> None:
        self.post_message(TimelineChanged(self._value))

    def on_click(self, event: object) -> None:
        if self._steps <= 1:
            return
        width = max(1, self.size.width - 2)
        ratio = max(0.0, min(1.0, event.x / width))
        self._value = int(ratio * (self._steps - 1))
        self.refresh()
        self._emit_change()

    def on_key(self, event: object) -> None:
        if event.key == "left":
            self._value = max(0, self._value - 1)
            self.refresh()
            self._emit_change()
        elif event.key == "right":
            self._value = min(self._steps - 1 if self._steps else 0, self._value + 1)
            self.refresh()
            self._emit_change()

    def render(self) -> str:
        if self._steps == 0:
            return "Timeline: no execution steps"

        markers = []
        for index in range(self._steps):
            markers.append("●" if index == self._value else "○")
        return f"Timeline [{' '.join(markers)}] step {self._value + 1}/{self._steps}"


class StatusBar(Footer):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.message = "Press q to quit, r to rerun trace."

    def render(self) -> str:
        return self.message


class Week2App(App):
    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("r", "rerun", "Rerun", show=True),
    ]

    CSS = """
    Screen {
        background: black;
    }
    #code-viewer {
        width: 2fr;
        height: 1fr;
        border: round gray;
        padding: 1;
    }
    #variables-panel {
        width: 1fr;
        height: 1fr;
        border: round cyan;
        padding: 1;
    }
    #timeline {
        height: 5;
        border: round green;
        padding: 1;
    }
    #trace-log {
        height: 10;
        border: round magenta;
        padding: 1;
    }
    #status {
        background: gray23;
        color: white;
    }
    """

    def __init__(self, db_path: Path, script_path: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.db_path = db_path
        self.script_path = script_path
        self.code_viewer: CodeViewer | None = None
        self.variables_panel: VariablesPanel | None = None
        self.timeline: TimelineSlider | None = None
        self.trace_log: RichLog | None = None
        self.execution_steps: List[Dict[str, Any]] = []
        self.selected_index = 0
        self.tracer = ExecutionTracer(db_path=self.db_path, script_path=self.script_path)

    def compose(self) -> ComposeResult:
        self.code_viewer = CodeViewer(self.script_path, id="code-viewer")
        self.variables_panel = VariablesPanel(id="variables-panel")
        self.timeline = TimelineSlider(id="timeline")
        self.trace_log = RichLog(id="trace-log", highlight=False, markup=False, wrap=True)

        yield Header(show_clock=True)
        with Container():
            with Horizontal():
                yield self.code_viewer
                yield self.variables_panel
            yield self.timeline
            yield self.trace_log
        yield StatusBar(id="status")

    def on_mount(self) -> None:
        self.load_trace_summary()

    def load_trace_summary(self) -> None:
        records = fetch_execution_records(self.db_path)
        self.execution_steps = self.tracer.build_execution_snapshots(records)
        if self.trace_log is not None:
            self.trace_log.clear()
            for record in records[-20:]:
                self.trace_log.write(
                    f"{record['timestamp']} {Path(record['filename']).name}:{record['function_name']}:{record['line_number']} {record['locals_json']}"
                )

        if self.timeline is not None:
            self.timeline.set_steps(len(self.execution_steps))
        if self.execution_steps:
            self.selected_index = max(0, min(self.selected_index, len(self.execution_steps) - 1))
            self.show_step(self.selected_index)
        else:
            self.show_step(0)

    def show_step(self, index: int) -> None:
        if not self.execution_steps:
            if self.code_viewer is not None:
                self.code_viewer.highlight_line(0)
            if self.variables_panel is not None:
                self.variables_panel.show_state({})
            return

        self.selected_index = max(0, min(index, len(self.execution_steps) - 1))
        step = self.execution_steps[self.selected_index]
        record = step["record"]
        state = step["state"]

        if self.code_viewer is not None:
            self.code_viewer.highlight_line(int(record["line_number"]))
        if self.variables_panel is not None:
            self.variables_panel.show_state(state)
        if self.timeline is not None:
            self.timeline.set_value(self.selected_index)

        status = self.query_one(StatusBar)
        status.message = f"Step {self.selected_index + 1}/{len(self.execution_steps)} — {Path(record['filename']).name}:{record['line_number']}"

    def handle_timeline_changed(self, message: TimelineChanged) -> None:
        self.show_step(message.index)

    def action_rerun(self) -> None:
        status = self.query_one(StatusBar)
        status.message = "Rerunning tracer and refreshing records..."
        if self.trace_log is not None:
            self.trace_log.write("[bold yellow]Rerunning tracer...[/]")
        self.tracer.run()
        self.load_trace_summary()
        status.message = "Trace rerun complete. Press q to quit, r to rerun again."
