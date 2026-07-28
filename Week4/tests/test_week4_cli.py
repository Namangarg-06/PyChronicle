from pathlib import Path

from typer.testing import CliRunner

from week4.runner import app, _resolve_script_path


def test_run_command_help() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["run", "--help"])
    assert result.exit_code == 0
    assert "Trace a Python script and launch the UI." in result.output


def test_resolve_script_path_uses_default_when_not_found() -> None:
    resolved = _resolve_script_path("nonexistent_script.py")
    assert resolved is not None
    assert isinstance(resolved, Path)


def test_resolve_script_path_resolves_given_path(tmp_path: Path) -> None:
    script = tmp_path / "test_script.py"
    script.write_text("x = 1")
    resolved = _resolve_script_path(str(script))
    assert resolved == script.resolve()
