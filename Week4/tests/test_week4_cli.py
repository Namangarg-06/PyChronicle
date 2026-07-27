from pathlib import Path

from week4.runner import build_parser, parse_args


def test_build_parser_supports_cli_options(tmp_path: Path) -> None:
    parser = build_parser()
    args = parser.parse_args(["run", "sample_script.py", "--db-path", str(tmp_path / "pychronicle.db")])

    assert args.command == "run"
    assert args.script_path == "sample_script.py"
    assert args.db_path == str(tmp_path / "pychronicle.db")


def test_parse_args_default_script_name() -> None:
    args = parse_args(["run", "sample_script.py"])
    assert args.command == "run"
    assert args.script_path == "sample_script.py"
