from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from rich.syntax import Syntax
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal
from textual.message import Message
from textual.widgets import Button, Footer, Header, Input, Label, Static
from textual.widgets._rich_log import RichLog

from .db import fetch_execution_records
from .tracer import ExecutionTracer


class CodeViewer(Static):
    def __init__(self, script_path: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.script_path = script_path
        self.code_lines = self._load_source()

    def _load_source(self) -> List[str]:
        with open(self.script_path, "r", encoding="utf-8") as source_file:
            return source_file.readlines()

    def compose(self) -> ComposeResult:
        language = self.script_path.suffix.lstrip(".") or "python"
        syntax = Syntax("".join(self.code_lines), language, line_numbers=True)
        yield Static(syntax)

    def highlight_line(self, line_number: int) -> None:
        highlight_lines = {line_number} if line_number else set()
        language = self.script_path.suffix.lstrip(".") or "python"
        syntax = Syntax(
            "".join(self.code_lines),
            language,
            line_numbers=True,
            highlight_lines=highlight_lines,
        )
        self.update(syntax)


class WatchVariablesPanel(Container):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.watch_names: List[str] = []
        self.watch_input: Input | None = None
        self.watch_values: Static | None = None

    def compose(self) -> ComposeResult:
        yield Label("Watch Variables")
        self.watch_input = Input(placeholder="Add variable name", id="watch-input")
        yield self.watch_input
        yield Button("Track", id="watch-add")
        self.watch_values = Static("Tracked variables will appear here.", id="watch-values")
        yield self.watch_values

    def add_variable(self, name: str) -> None:
        cleaned = name.strip()
        if not cleaned:
            return
        if cleaned not in self.watch_names:
            self.watch_names.append(cleaned)
        self._refresh_display()

    def remove_variable(self, name: str) -> None:
        if name in self.watch_names:
            self.watch_names.remove(name)
            self._refresh_display()

    def update_state(self, state: Optional[Dict[str, Any]]) -> None:
        self._refresh_display(state)

    def _refresh_display(self, state: Optional[Dict[str, Any]] = None) -> None:
        if self.watch_values is None:
            return
        if not self.watch_names:
            self.watch_values.update("No watched variables yet. Type a variable name and press Enter.")
            return

        if state is None:
            state = {}

        lines = [f"{name}: {self._format_value(state.get(name, '∅'))}" for name in self.watch_names]
        self.watch_values.update("\n".join(lines))

    def _format_value(self, value: Any) -> str:
        if value == "∅":
            return "∅"
        if isinstance(value, str):
            return repr(value)
        if isinstance(value, (dict, list, tuple, set)):
            return json.dumps(value, indent=2, sort_keys=True)
        return str(value)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "watch-add" and self.watch_input is not None:
            self.add_variable(self.watch_input.value)
            self.watch_input.value = ""

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "watch-input":
            self.add_variable(event.value)
            event.input.value = ""


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


class StatusBar(Static):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.message = "Press q to quit, r to rerun, ←/→ to navigate."
        self.update(self.message)

    def set_message(self, message: str) -> None:
        self.message = message
        self.update(message)


class Week4App(App):
    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("r", "rerun", "Rerun", show=True),
        Binding("left", "previous_step", "Prev", show=True),
        Binding("right", "next_step", "Next", show=True),
        Binding("w", "focus_watch", "Watch", show=True),
    ]

    CSS = """
    Screen {
        background: black;
        color: white;
    }
    #code-viewer {
        width: 2fr;
        min-height: 20;
        border: round gray;
        padding: 1;
    }
    #watch-panel {
        width: 1fr;
        min-height: 20;
        border: round cyan;
        padding: 1;
    }
    #timeline {
        height: 3;
        border: round green;
        padding: 1;
    }
    #trace-log {
        height: 8;
        border: round magenta;
        padding: 1;
    }
    #status {
        background: gray23;
        color: white;
        padding: 0 1;
    }
    """

    def __init__(self, db_path: Path, script_path: Path, watch_variables: Optional[List[str]] = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.db_path = db_path
        self.script_path = script_path
        self.watch_variables = watch_variables or []
        self.code_viewer: CodeViewer | None = None
        self.watch_panel: WatchVariablesPanel | None = None
        self.timeline: TimelineSlider | None = None
        self.trace_log: RichLog | None = None
        self.status_bar: StatusBar | None = None
        self.execution_steps: List[Dict[str, Any]] = []
        self.selected_index = 0
        self.tracer = ExecutionTracer(db_path=self.db_path, script_path=self.script_path)

    def compose(self) -> ComposeResult:
        self.code_viewer = CodeViewer(self.script_path, id="code-viewer")
        self.watch_panel = WatchVariablesPanel(id="watch-panel")
        self.timeline = TimelineSlider(id="timeline")
        self.trace_log = RichLog(id="trace-log", highlight=False, markup=False, wrap=True)
        self.status_bar = StatusBar(id="status")

        for variable in self.watch_variables:
            self.watch_panel.add_variable(variable)

        yield Header(show_clock=True)
        with Container():
            with Horizontal():
                yield self.code_viewer
                yield self.watch_panel
            yield self.timeline
            yield self.trace_log
        yield self.status_bar
        yield Footer()

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
            if self.watch_panel is not None:
                self.watch_panel.update_state({})
            self._set_status("No execution steps recorded yet.")
            return

        self.selected_index = max(0, min(index, len(self.execution_steps) - 1))
        step = self.execution_steps[self.selected_index]
        record = step["record"]
        state = step["state"]

        if self.code_viewer is not None:
            self.code_viewer.highlight_line(int(record["line_number"]))
        if self.watch_panel is not None:
            self.watch_panel.update_state(state)
        if self.timeline is not None:
            self.timeline.set_value(self.selected_index)

        self._set_status(
            f"Step {self.selected_index + 1}/{len(self.execution_steps)} — {Path(record['filename']).name}:{record['line_number']}"
        )

    def _set_status(self, message: str) -> None:
        if self.status_bar is not None:
            self.status_bar.set_message(message)

    def on_timeline_changed(self, message: TimelineChanged) -> None:
        self.show_step(message.index)

    def action_previous_step(self) -> None:
        self.show_step(self.selected_index - 1)

    def action_next_step(self) -> None:
        self.show_step(self.selected_index + 1)

    def action_focus_watch(self) -> None:
        if self.watch_panel is not None and self.watch_panel.watch_input is not None:
            self.watch_panel.watch_input.focus()
            self._set_status("Focused the watch variable input.")

    def action_rerun(self) -> None:
        self._set_status("Re-running tracer and refreshing records...")
        if self.trace_log is not None:
            self.trace_log.write("[bold yellow]Re-running tracer...[/]")
        try:
            self.tracer.run()
            self.load_trace_summary()
            self._set_status("Trace rerun complete. Press q to quit, r to rerun again.")
        except Exception as exc:
            self._set_status(f"Trace rerun failed: {exc}")
            if self.trace_log is not None:
                self.trace_log.write(f"[bold red]Error: {exc}[/]")
