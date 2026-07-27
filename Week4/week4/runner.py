from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import List, Optional

import typer

from week4.db import ensure_schema, resolve_db_path
from week4.tracer import ExecutionTracer
from week4.ui import Week4App

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

app = typer.Typer(help="Trace Python scripts and inspect execution state.", add_completion=False)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run PyChronicle Week 4 tracing CLI.")
    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser("run", help="Trace a Python script and launch the UI.")
    run_parser.add_argument(
        "script_path",
        nargs="?",
        default="sample_script.py",
        help="Path to the Python script to trace.",
    )
    run_parser.add_argument(
        "--db-path",
        type=str,
        default=None,
        help="Path to the existing SQLite database file.",
    )
    run_parser.add_argument(
        "--no-ui",
        action="store_true",
        help="Run the tracer without launching the Textual UI.",
    )
    run_parser.add_argument(
        "--watch",
        action="append",
        default=[],
        help="Variable name to watch in the UI; repeat the option to track multiple variables.",
    )
    return parser


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    return build_parser().parse_args(argv)


def run_tracer(script_path: Path, db_path: Path) -> None:
    ensure_schema(db_path)
    tracer = ExecutionTracer(db_path=db_path, script_path=script_path)
    tracer.run()


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


@app.command("run")
def run_command(
    script_path: str = typer.Argument("sample_script.py", help="Path to the Python script to trace."),
    db_path: Optional[str] = typer.Option(None, "--db-path", help="Path to the existing SQLite database file."),
    no_ui: bool = typer.Option(False, "--no-ui", help="Run the tracer without launching the Textual UI."),
    watch: Optional[List[str]] = typer.Option(None, "--watch", help="Variable name to track in the UI."),
) -> None:
    logger.info("Starting PyChronicle Week 4 run")
    try:
        resolved_db_path = resolve_db_path(db_path)
        resolved_script_path = _resolve_script_path(script_path)
        if not resolved_script_path.exists():
            raise FileNotFoundError(f"Script '{resolved_script_path}' does not exist.")

        if no_ui:
            run_tracer(script_path=resolved_script_path, db_path=resolved_db_path)
            typer.echo(f"Tracing complete. Records saved to {resolved_db_path}.")
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


def main(argv: Optional[List[str]] = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    if not argv:
        app(prog_name="pychronicle")
        return 0

    parsed = parse_args(argv)
    if parsed.command == "run":
        run_command(
            script_path=parsed.script_path,
            db_path=parsed.db_path,
            no_ui=parsed.no_ui,
            watch=parsed.watch,
        )
        return 0

    app(prog_name="pychronicle")
    return 0


if __name__ == "__main__":
    main()
