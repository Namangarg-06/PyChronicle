# PyChronicle Week 2

This Week 2 project builds a Python execution tracer that stores every executed line into an existing SQLite database and exposes a Textual terminal UI.

## Requirements
- Python 3.11+
- An existing Week 1 SQLite database file (for example `pychronicle.db`)
- `pip install -r requirements.txt`

## Usage
1. Place your existing Week 1 database file where the program can find it, or pass it explicitly with `--db-path`.
2. Run the UI from the `Week2` folder:

```bash
python run_week2.py --db-path /path/to/pychronicle.db
```

If `pychronicle.db` is located in the same directory or a parent directory, the application will find it automatically.

## Features
- Uses `sys.settrace()` to capture every executed line.
- Records line number, function name, filename, local variables, and timestamp.
- Stores execution records into the existing SQLite database.
- Provides a Textual terminal UI with:
  - Code viewer
  - Timeline slider placeholder
  - Status bar
  - `q` to quit
  - `r` to rerun tracer

## Project structure
- `run_week2.py`: launcher script.
- `week2/db.py`: database adapter and schema management.
- `week2/tracer.py`: Python execution tracer implementation.
- `week2/ui.py`: Textual terminal UI.
- `week2/runner.py`: command-line entrypoint.
- `sample_script.py`: sample Python script for testing.
