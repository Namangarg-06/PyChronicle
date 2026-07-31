import os
import sys
from typing import Any, List, Dict
from textual.app import App, ComposeResult
from textual.containers import Container, Vertical
from textual.widgets import Header, Footer, Static, Input
from rich.syntax import Syntax
from rich.table import Table
from rich.panel import Panel

from pychronicle.storage import StateStorage
from pychronicle.tracer import Tracer

class CodeViewer(Static):
    """Displays syntax-highlighted target code with active line highlight."""
    def __init__(self, target_path: str, **kwargs):
        super().__init__(**kwargs)
        self.code_str = ""
        if os.path.exists(target_path):
            with open(target_path, "r", encoding="utf-8") as f:
                self.code_str = f.read()

    def update_highlight(self, active_line: int):
        if not self.code_str:
            self.update("No target source file loaded.")
            return
        self.update(Syntax(
            self.code_str, "python", theme="monokai", line_numbers=True,
            highlight_lines={active_line}, background_color="#0f1419"
        ))

class VariablesInspector(Static):
    """Displays in-scope variable states at current timeline step."""
    def update_variables(self, variables: Dict[str, Any]):
        if not variables:
            self.update(Panel("[italic gray]No variables in scope.[/italic gray]", border_style="dim"))
            return
        table = Table(show_header=True, header_style="bold yellow", expand=True)
        table.add_column("Variable", style="bold green", width=15)
        table.add_column("Value", style="cyan")
        for name, value in sorted(variables.items()):
            table.add_row(name, str(value))
        self.update(Panel(table, title="Local Scope", border_style="cyan"))

class WatchHistory(Static):
    """Displays all historical mutation values of a watched variable."""
    def update_history(self, var_name: str, history: List[Dict[str, Any]], current_step: int):
        if not var_name:
            self.update(Panel("[italic gray]Type a variable name below to watch...[/italic gray]", border_style="dim"))
            return
        table = Table(show_header=True, header_style="bold yellow", expand=True)
        table.add_column("Step", style="bold green", width=6)
        table.add_column("Line", style="bold yellow", width=6)
        table.add_column("Value", style="cyan")
        
        count = 0
        for i, step in enumerate(history):
            if step["variable_name"] == var_name:
                count += 1
                style = "bold white on green" if i == current_step else ("white" if i < current_step else "dim")
                table.add_row(f"{i + 1}", f"{step['line_number']}", str(step['value']), style=style)
                
        if count == 0:
            self.update(Panel(f"[italic red]Variable '{var_name}' never mutated.[/italic red]", border_style="red"))
        else:
            self.update(Panel(table, title=f"Watch History: {var_name}", border_style="green"))

class TimelineBar(Static):
    """Renders text-based execution progress bar."""
    def update_progress(self, current: int, total: int):
        percent = 100 if total <= 0 else int((current / total) * 100)
        filled = 40 if total <= 0 else int(40 * current // total)
        bar = "█" * filled + "░" * (40 - filled)
        self.update(f"Timeline: [bold green]|{bar}|[/bold green] {percent}%")

class PyChronicleApp(App):
    """Time-travel debugger main Textual application."""
    CSS_PATH = "tui.css"
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("left", "prev_step", "Previous Step"),
        ("right", "next_step", "Next Step"),
        ("home", "first_step", "First Step"),
        ("end", "last_step", "Last Step"),
        ("pageup", "prev_10", "Jump -10"),
        ("pagedown", "next_10", "Jump +10")
    ]

    def __init__(self, target_path: str):
        super().__init__()
        self.target_path = os.path.abspath(target_path)
        self.storage = StateStorage(":memory:")
        self.history: List[Dict[str, Any]] = []
        self.current_step = 0

    def on_mount(self) -> None:
        tracer = Tracer(self.target_path, self.storage)
        try:
            tracer.run()
        except Exception as e:
            self.notify(f"Tracer error: {e}", severity="error")

        self.history = self.storage.get_history()
        if self.history:
            self.current_step = 0
            self.update_step(0)
        else:
            self.query_one(CodeViewer).update_highlight(0)
            self.query_one(VariablesInspector).update_variables({})
            self.query_one(TimelineBar).update_progress(0, 0)
            self.query_one(WatchHistory).update_history("", [], 0)

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(id="main-container"):
            yield CodeViewer(target_path=self.target_path, id="code-container")
            with Vertical(id="inspector-container"):
                yield Static("VARIABLE INSPECTOR", classes="panel-title")
                yield VariablesInspector(id="variables-list")
                yield Static("WATCH LIST", classes="panel-title")
                yield WatchHistory(id="watch-history-list")
                yield Input(placeholder="Enter variable name to watch...", id="watch-input")
        with Container(id="controls-container"):
            yield Static("Execution Steps Timeline", id="slider-label")
            yield TimelineBar(id="timeline-bar")
        yield Footer()

    def action_prev_step(self) -> None:
        if self.current_step > 0:
            self.current_step -= 1
            self.update_step(self.current_step)

    def action_next_step(self) -> None:
        if self.current_step < len(self.history) - 1:
            self.current_step += 1
            self.update_step(self.current_step)

    def action_first_step(self) -> None:
        if self.history:
            self.current_step = 0
            self.update_step(self.current_step)

    def action_last_step(self) -> None:
        if self.history:
            self.current_step = len(self.history) - 1
            self.update_step(self.current_step)

    def action_prev_10(self) -> None:
        if self.history:
            self.current_step = max(0, self.current_step - 10)
            self.update_step(self.current_step)

    def action_next_10(self) -> None:
        if self.history:
            self.current_step = min(len(self.history) - 1, self.current_step + 10)
            self.update_step(self.current_step)

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "watch-input":
            self.update_step(self.current_step)

    def update_step(self, step_idx: int):
        if not self.history or step_idx < 0 or step_idx >= len(self.history):
            return
        step_info = self.history[step_idx]
        active_line = step_info["line_number"]
        active_vars = {item["variable_name"]: item["value"] for item in self.history[:step_idx + 1]}

        self.query_one(CodeViewer).update_highlight(active_line)
        self.query_one(VariablesInspector).update_variables(active_vars)
        self.query_one(TimelineBar).update_progress(step_idx, len(self.history) - 1)
        
        watch_var = self.query_one("#watch-input", Input).value.strip()
        self.query_one("#watch-history-list", WatchHistory).update_history(watch_var, self.history, step_idx)

        self.query_one("#slider-label", Static).update(
            f"Step [bold green]{step_idx + 1}[/bold green] of [bold green]{len(self.history)}[/bold green] "
            f"| Executed Line [bold yellow]{active_line}[/bold yellow] "
            f"| Mutated: [bold cyan]{step_info['variable_name']}[/bold cyan]"
        )

    def on_unmount(self) -> None:
        self.storage.close()

def main():
    if len(sys.argv) < 2 or not os.path.exists(sys.argv[1]):
        print("Usage: python -m pychronicle.tui <path_to_python_script>")
        sys.exit(1)
    PyChronicleApp(sys.argv[1]).run()

if __name__ == "__main__":
    main()
