# PyChronicle

PyChronicle is a Python debugging tool that lets you replay execution step by step instead of debugging only forward in time.

It uses Python's AST and runtime tracing to capture variable changes while a script runs, stores them in SQLite, and shows them in a Textual terminal UI so you can move backward and forward through execution history.

## Core idea

- Parse Python source with the AST.
- Track assignments and variable mutations during execution.
- Save state changes as time-based deltas.
- Inspect the program timeline in a terminal UI.

## Features

- AST-based script analysis
- Runtime tracing via `sys.settrace`
- SQLite-backed execution history
- Timeline scrubbing for previous and next states
- Optional variable watch tracking
- CLI-based workflow for running traced scripts

## Installation

```bash
cd Pychronicle
python -m pip install -e .
```

## Usage

```bash
pychronicle run path/to/script.py
pychronicle run path/to/script.py --no-ui
pychronicle run path/to/script.py --watch x --watch y
```

## Project structure

- `pychronicle/` - main package
- `tests/` - project tests
- `Week2/`, `Week3/`, `Week4/` - week-by-week implementations
- `run_all.py` and `check_all.py` - combined runner scripts

## Development status

This project is a multi-week implementation covering AST parsing, execution tracing, SQLite storage, and a terminal UI for debugging.

## License

MIT
