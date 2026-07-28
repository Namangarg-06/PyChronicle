from __future__ import annotations

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


def main() -> int:
    app(prog_name="pychronicle")
    return 0


if __name__ == "__main__":
    main()
