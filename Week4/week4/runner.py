from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import typer

from week4.db import ensure_schema, fetch_execution_records, resolve_db_path
from week4.tracer import ExecutionTracer
from week4.ui import Week4App

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

app = typer.Typer(help="Trace Python scripts and inspect execution state.", add_completion=False)


def _safe_text(value: str) -> str:
    """Fallback to ASCII-only output when the active terminal cannot encode Unicode."""
    encoding = (sys.stdout.encoding or "utf-8").lower()
    try:
        value.encode(encoding)
        return value
    except UnicodeEncodeError:
        mapping = {
            "╔": "+",
            "╗": "+",
            "╚": "+",
            "╝": "+",
            "═": "-",
            "║": "|",
            "─": "-",
            "│": "|",
            "←": "<",
            "→": ">",
            "⏩": ">>",
            "⏪": "<<",
            "⏱️": "*",
        }
        return "".join(mapping.get(char, char) for char in value)


def _echo(message: str = "", err: bool = False) -> None:
    typer.echo(_safe_text(message), err=err)


@app.callback(invoke_without_command=True)
def main_callback(ctx: typer.Context) -> None:
    """Show help when the app is invoked without a subcommand."""
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())


def _run_direct_script(script_path: str) -> None:
    resolved_script_path = _resolve_script_path(script_path)
    if not resolved_script_path.exists():
        raise FileNotFoundError(f"Script '{resolved_script_path}' does not exist.")
    resolved_db_path = resolve_db_path(None)
    run_tracer(script_path=resolved_script_path, db_path=resolved_db_path)
    _print_time_travel_debugger(resolved_script_path, resolved_db_path, interactive=True)


def run_tracer(script_path: Path, db_path: Path) -> None:
    ensure_schema(db_path)
    tracer = ExecutionTracer(db_path=db_path, script_path=script_path)
    tracer.run()


def _format_display_value(value: Any) -> str:
    if value is None:
        return "None"
    if isinstance(value, str):
        return value
    if isinstance(value, (dict, list, tuple, set)):
        return json.dumps(value, sort_keys=True)
    return str(value)


def _load_snapshots(script_path: Path, db_path: Path) -> List[Dict[str, Any]]:
    tracer = ExecutionTracer(db_path=db_path, script_path=script_path)
    records = fetch_execution_records(db_path)
    return tracer.build_execution_snapshots(records)


def _build_timeline_rows(snapshots: List[Dict[str, Any]]) -> List[Tuple[int, int, str, str]]:
    rows: List[Tuple[int, int, str, str]] = []
    previous_state: Dict[str, Any] = {}

    for index, snapshot in enumerate(snapshots):
        record = snapshot["record"]
        current_state = snapshot["state"]
        changed_keys = sorted(set(previous_state) | set(current_state))
        for key in changed_keys:
            previous_value = previous_state.get(key)
            current_value = current_state.get(key)
            if previous_value != current_value:
                rows.append((index + 1, int(record["line_number"]), key, _format_display_value(current_value)))
        previous_state = current_state

    return rows


def _print_time_travel_debugger(script_path: Path, db_path: Path, initial_step: Optional[int] = None, interactive: bool = True) -> None:
    snapshots = _load_snapshots(script_path, db_path)
    if not snapshots:
        _echo("No execution trace available for this script.")
        return

    last_index = len(snapshots) - 1
    current_index = last_index if initial_step is None else max(0, min(initial_step, last_index))
    current_state = snapshots[current_index]["state"]
    timeline_rows = _build_timeline_rows(snapshots)

    def render_step(step_index: int) -> None:
        nonlocal current_index, current_state
        current_index = max(0, min(step_index, last_index))
        current_state = snapshots[current_index]["state"]
        _echo()
        _echo("╔══════════════════════════════════════════════╗")
        _echo("║          PyChronicle — Time Travel Debugger ║")
        _echo("╚══════════════════════════════════════════════╝")
        _echo()
        _echo(f"Program: {script_path.name}")
        _echo("Execution completed.")
        _echo()
        _echo("Timeline:")
        _echo("──────────────────────────────────────────────")
        _echo("Step   Line    Variable       Value")
        _echo("──────────────────────────────────────────────")

        if not timeline_rows:
            _echo("No recorded variable mutations.")
        else:
            visible_rows = [row for row in timeline_rows if row[0] <= current_index + 1]
            for step_no, line_no, variable_name, value in visible_rows[-25:]:
                _echo(f"{step_no:<6} {line_no:<7} {variable_name:<14} {value}")
            if len(visible_rows) > 25:
                _echo("...")
        _echo("──────────────────────────────────────────────")
        _echo()
        if initial_step is not None:
            _echo("Current State:")
            _echo("Historical State:")
        elif current_index == last_index:
            _echo("Current State:")
        else:
            _echo("Historical State:")
        for key, value in current_state.items():
            _echo(f"{key} = {_format_display_value(value)}")
        _echo()
        _echo("Commands:")
        _echo("  < Previous State")
        _echo("  > Next State")
        _echo("  w Watch Variable")
        _echo("  q Quit")
        _echo()
        _echo("pychronicle>")

    if not interactive:
        render_step(current_index)
        return

    render_step(current_index)
    while True:
        command = input("pychronicle> ").strip().lower()
        if command in {"q", "quit", "exit"}:
            _echo("Exiting PyChronicle.")
            break
        if command in {"n", "next", "right", ">"}:
            if current_index < last_index:
                current_index += 1
                _echo(f"Moved to Step {current_index + 1}")
                render_step(current_index)
            else:
                _echo("Already at the final step.")
                continue
        elif command in {"b", "back", "prev", "left", "<"}:
            if current_index > 0:
                current_index -= 1
                _echo(f"Moved to Step {current_index + 1}")
                render_step(current_index)
            else:
                _echo("Already at the first recorded step.")
                continue
        elif command in {"w", "watch"}:
            watch_name = input("Variable name: ").strip()
            if not watch_name:
                _echo("No variable name provided.")
                continue
            if watch_name in current_state:
                _echo(f"{watch_name} = {_format_display_value(current_state[watch_name])}")
            else:
                _echo(f"Variable '{watch_name}' not found in this state.")
        elif command.isdigit():
            step_target = int(command) - 1
            if 0 <= step_target <= last_index:
                _echo(f"Jumped to Step {step_target + 1}")
                render_step(step_target)
            else:
                _echo(f"Step must be between 1 and {last_index + 1}.")
        else:
            _echo("Unknown command. Use b, n, w, or q.")


def _resolve_script_path(script_path: str) -> Path:
    candidate = Path(script_path).expanduser()
    if candidate.is_absolute():
        resolved = candidate.resolve()
    else:
        resolved = (Path.cwd() / candidate).resolve()

    if not resolved.exists() and candidate.name == "sample_script.py":
        default_sample = Path(__file__).resolve().parents[1] / "sample_script.py"
        if default_sample.exists():
            resolved = default_sample.resolve()

    return resolved


@app.command("run", help="Trace a Python script and launch the UI.")
def run_command(
    script_path: Optional[str] = typer.Argument(None, help="Path to the Python script to trace."),
    db_path: Optional[str] = typer.Option(None, "--db-path", help="Path to the existing SQLite database file."),
    no_ui: bool = typer.Option(False, "--no-ui", help="Run the tracer without launching the Textual UI."),
    step: Optional[int] = typer.Option(None, "--step", help="Display a specific historical step in the no-UI debugger output."),
    watch: Optional[List[str]] = typer.Option(None, "--watch", help="Variable name to track in the UI."),
) -> None:
    logger.info("Starting PyChronicle Week 4 run")
    try:
        if script_path is None:
            script_path = "sample_script.py"
        resolved_db_path = resolve_db_path(db_path)
        resolved_script_path = _resolve_script_path(script_path)
        if not resolved_script_path.exists():
            raise FileNotFoundError(f"Script '{resolved_script_path}' does not exist.")

        if no_ui:
            run_tracer(script_path=resolved_script_path, db_path=resolved_db_path)
            _print_time_travel_debugger(
                resolved_script_path,
                resolved_db_path,
                initial_step=step,
                interactive=False,
            )
            return

        app_instance = Week4App(
            db_path=resolved_db_path,
            script_path=resolved_script_path,
            watch_variables=list(watch or []),
        )
        app_instance.run()
    except Exception as exc:  # pragma: no cover - CLI safety net
        logger.exception("PyChronicle run failed")
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from exc


def main() -> int:
    raw_args = sys.argv[1:]
    if raw_args and not raw_args[0].startswith("-") and raw_args[0] not in {"run", "--help", "-h"}:
        try:
            _run_direct_script(raw_args[0])
            return 0
        except Exception as exc:
            logger.exception("Direct script execution failed")
            typer.echo(f"Error: {exc}", err=True)
            return 1
    app()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
