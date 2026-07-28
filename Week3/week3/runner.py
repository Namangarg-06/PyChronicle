import argparse
from pathlib import Path
import sys
# Add project root to the Python path
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
    
from week3.db import ensure_schema, resolve_db_path
from week3.tracer import ExecutionTracer
from week3.ui import TimelineUI


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run PyChronicle Week 3 tracing and timeline viewer.")
    parser.add_argument(
        "--script",
        type=str,
        default="sample_script.py",
        help="Path to the Python script to trace.",
    )
    parser.add_argument(
        "--db-path",
        type=str,
        default=None,
        help="Path to the existing Week 3 SQLite database file.",
    )
    parser.add_argument(
        "--no-ui",
        action="store_true",
        help="Run the tracer without launching the timeline UI.",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run the timeline viewer in demo mode (auto-display all steps).",
    )
    parser.add_argument(
        "--auto",
        action="store_true",
        help="Run the timeline viewer in compact auto mode for pipeline execution (no input() calls).",
    )
    return parser.parse_args()


def run_tracer(script_path: Path, db_path: Path) -> None:
    """Run execution tracer on the target script."""
    ensure_schema(db_path)
    tracer = ExecutionTracer(db_path=db_path, script_path=script_path)
    tracer.run()


def main() -> int:
    args = parse_args()
    db_path = resolve_db_path(args.db_path)
    script_path = Path(args.script).expanduser()
    if args.script == "sample_script.py":
        default_sample = Path(__file__).resolve().parents[1] / "sample_script.py"
        script_path = default_sample
    script_path = script_path.resolve()
    if not script_path.exists():
        print(f"Error: script '{script_path}' does not exist.")
        return 1

    # Run the tracer first
    run_tracer(script_path=script_path, db_path=db_path)

    if args.no_ui:
        print("Tracing complete. Records saved to database.")
        print("Week3 - COMPLETED SUCCESSFULLY!")
        return 0

    # Display timeline (interactive or demo mode)
    print("\nLaunching Timeline Viewer...\n")
    timeline_ui = TimelineUI(db_path=db_path, demo_mode=args.demo, auto_mode=args.auto)
    timeline_ui.run()
    
    print("\nWeek3 - COMPLETED SUCCESSFULLY!")
    return 0
