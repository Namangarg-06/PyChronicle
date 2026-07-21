from __future__ import annotations

from pathlib import Path
from typing import List

from rich.syntax import Syntax
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal
from textual.widgets import Static, Footer, Header
from textual.widgets._rich_log import RichLog

from week2.db import fetch_execution_records
from week2.tracer import ExecutionTracer


class CodeViewer(Static):
    def __init__(self, script_path: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.script_path = script_path
        self.code_lines = self._load_source()

    def _load_source(self) -> List[str]:
        with open(self.script_path, "r", encoding="utf-8") as source_file:
            return source_file.readlines()

    def compose(self) -> ComposeResult:
        syntax = Syntax("".join(self.code_lines), self.script_path.suffix.lstrip("."), line_numbers=True)
        yield Static(syntax)

    def highlight_line(self, line_number: int) -> None:
        self.update(Syntax("".join(self.code_lines), self.script_path.suffix.lstrip("."), line_numbers=True, highlight_lines={line_number}))


class Timeline(Static):
    def compose(self) -> ComposeResult:
        yield Static("Timeline placeholder — captured events will appear as trace markers.")


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
        height: 1fr;
        border: round gray;
        padding: 1;
    }
    #timeline {
        height: 8;
        border: round green;
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
        self.timeline: Timeline | None = None
        self.trace_log: RichLog | None = None

    def compose(self) -> ComposeResult:
        self.code_viewer = CodeViewer(self.script_path, id="code-viewer")
        self.timeline = Timeline(id="timeline")
        self.trace_log = RichLog(highlight=False, markup=False, wrap=True)

        yield Header(show_clock=True)
        with Container():
            yield self.code_viewer
            with Horizontal():
                yield self.timeline
                yield self.trace_log
        yield StatusBar(id="status")

    def on_mount(self) -> None:
        self.load_trace_summary()

    def load_trace_summary(self) -> None:
        records = fetch_execution_records(self.db_path)
        self.trace_log.clear()
        for record in records[-20:]:
            self.trace_log.write(
                f"{record['timestamp']} {Path(record['filename']).name}:{record['function_name']}:{record['line_number']} {record['locals_json']}"
            )
        if records:
            self.code_viewer.highlight_line(records[-1]["line_number"])

    def action_rerun(self) -> None:
        status = self.query_one(StatusBar)
        status.message = "Rerunning tracer and refreshing records..."
        if self.trace_log is not None:
            self.trace_log.write("[bold yellow]Rerunning tracer...[/]")
        tracer = ExecutionTracer(db_path=self.db_path, script_path=self.script_path)
        tracer.run()
        self.load_trace_summary()
        status.message = "Trace rerun complete. Press q to quit, r to rerun again."
