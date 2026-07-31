from click.testing import CliRunner
from pychronicle.cli import main

def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "PyChronicle: AST-Powered Time-Travel Debugger" in result.output
    assert "run" in result.output

def test_cli_run_invalid_path():
    runner = CliRunner()
    result = runner.invoke(main, ["run", "non_existent_file.py"])
    assert result.exit_code != 0
    assert "does not exist" in result.output
