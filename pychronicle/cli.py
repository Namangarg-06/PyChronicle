import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List

import click

from pychronicle.storage import StateStorage
from pychronicle.tracer import Tracer


def _build_trace_steps(script_path: str) -> List[Dict[str, Any]]:
    script_file = Path(script_path).resolve()
    fd, db_path = tempfile.mkstemp(prefix="pychronicle_", suffix=".db")
    os.close(fd)

    storage = StateStorage(db_path)
    tracer = Tracer(str(script_file), storage)
    tracer.run()

    history = storage.get_history()
    steps: List[Dict[str, Any]] = []
    state: Dict[str, Any] = {}

    for record in history:
        state[record["variable_name"]] = record["value"]
        steps.append(
            {
                "step": len(steps) + 1,
                "line": record["line_number"],
                "variable": record["variable_name"],
                "value": record["value"],
                "state": dict(state),
            }
        )

    return steps


def _format_value(value: Any) -> str:
    if value is None:
        return "None"
    if isinstance(value, str):
        return value
    return str(value)


def _show_state_block(label: str, state: Dict[str, Any]) -> None:
    print(label)
    if not state:
        print("<no variables recorded>")
        return
    for key in sorted(state):
        print(f"{key} = {_format_value(state[key])}")


def _render_timeline(steps: List[Dict[str, Any]], current_index: int, program_name: str) -> None:
    print("╔══════════════════════════════════════════════╗")
    print("║        PyChronicle — Time Travel Debugger    ║")
    print("╚══════════════════════════════════════════════╝")
    print()
    print(f"Program: {program_name}")
    print("Execution completed.")
    print()
    print("Timeline:")
    print("──────────────────────────────────────────────")
    print("Step   Line    Variable       Value")
    print("──────────────────────────────────────────────")

    for step in steps:
        print(f"{step['step']:>3}   {step['line']:>4}    {step['variable']:<12} { _format_value(step['value']) }")

    print("──────────────────────────────────────────────")
    print()
    print("Current State:")
    state = steps[current_index]["state"] if steps else {}
    _show_state_block("", state)
    print()
    print("Commands:")
    print("  b = Previous State")
    print("  f = Next State")
    print("  w = Watch Variable")
    print("  q = Quit")
    print()


def _interactive_time_travel(script_path: str) -> None:
    steps = _build_trace_steps(script_path)
    if not steps:
        print(f"No execution trace recorded for {script_path}.")
        return

    current_index = len(steps) - 1
    while True:
        _render_timeline(steps, current_index, os.path.basename(script_path))
        choice = input("pychronicle> ").strip().lower()

        if choice in {"q", "quit", "exit"}:
            print("Exiting PyChronicle.")
            break
        if choice in {"b", "back", "previous"}:
            if current_index > 0:
                current_index -= 1
                print(f"\n⏪ Moved to Step {current_index + 1}")
                print("\nHistorical State:")
                _show_state_block("", steps[current_index]["state"])
            else:
                print("Already at the first recorded step.")
        elif choice in {"f", "forward", "next"}:
            if current_index < len(steps) - 1:
                current_index += 1
                print(f"\n⏩ Moved to Step {current_index + 1}")
                print("\nHistorical State:")
                _show_state_block("", steps[current_index]["state"])
            else:
                print("Already at the final recorded step.")
        elif choice in {"w", "watch"}:
            name = input("Variable name: ").strip()
            if not name:
                print("No variable selected.")
                continue
            state = steps[current_index]["state"]
            if name in state:
                print(f"{name} = {_format_value(state[name])}")
            else:
                print(f"Variable '{name}' is not in the current state.")


@click.group(invoke_without_command=True)
@click.argument('script_path', required=False, type=click.Path(exists=True, file_okay=True, dir_okay=False))
@click.pass_context
def main(ctx, script_path):
    """PyChronicle: AST-Powered Time-Travel Debugger."""
    if ctx.invoked_subcommand is None:
        if script_path is None:
            click.echo(ctx.get_help())
            return
        _interactive_time_travel(os.path.abspath(script_path))


@main.command()
@click.argument('script_path', type=click.Path(exists=True, file_okay=True, dir_okay=False))
def run(script_path):
    """Run the real PyChronicle time-travel debugger on a Python script."""
    _interactive_time_travel(os.path.abspath(script_path))


if __name__ == "__main__":
    main()
