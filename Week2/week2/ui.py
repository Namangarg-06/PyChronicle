from __future__ import annotations

from pathlib import Path
import threading
from typing import List

from rich.syntax import Syntax
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal
from textual.widgets import Static, Header
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
        language = self.script_path.suffix.lstrip(".") or "python"
        syntax = Syntax("".join(self.code_lines), language, line_numbers=True)
        yield Static(syntax)

    def highlight_line(self, line_number: int) -> None:
        language = self.script_path.suffix.lstrip(".") or "python"
        self.update(Syntax("".join(self.code_lines), language, line_numbers=True, highlight_lines={line_number}))


class Timeline(Static):
    def compose(self) -> ComposeResult:
        yield Static("Timeline placeholder — captured events will appear as trace markers.")


class StatusBar(Static):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.message = "Press q to quit, r to rerun trace."

    def render(self) -> str:
        return self.message
    
    def set_message(self, message: str) -> None:
        self.message = message
        self.refresh()


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

    def _run_tracer_in_background(self) -> None:
        """Helper to run the tracer in a separate thread."""
        try:
            tracer = ExecutionTracer(db_path=self.db_path, script_path=self.script_path)
            tracer.run()
            self.call_from_thread(self.load_trace_summary) # Refresh UI with new data
            self.call_from_thread(getattr(self.query_one(StatusBar), 'set_message', lambda _: None), "Trace rerun complete. Press q to quit, r to rerun again.")
        except Exception as e:
            self.call_from_thread(self.trace_log.write, f"[bold red]Error during rerun: {e}[/]")
            self.call_from_thread(getattr(self.query_one(StatusBar), 'set_message', lambda _: None), f"Error during rerun: {e}")

    def action_rerun(self) -> None:
        status = self.query_one(StatusBar)
        status.set_message("Rerunning tracer and refreshing records...")
        if self.trace_log is not None:
            self.trace_log.write("[bold yellow]Rerunning tracer...[/]")
        
        # Run the tracer in a separate thread to prevent UI freeze
        threading.Thread(target=self._run_tracer_in_background, daemon=True).start()
