# PyChronicle Week 4

This release packages the tracer as a proper CLI utility and improves the Textual UI with watch variables and better navigation.

## Installation

```bash
pip install -e .
```

## Usage

```bash
pychronicle run sample_script.py --db-path /path/to/pychronicle.db
```

Use `--no-ui` to run the tracer without launching the Textual interface and `--watch name` to track selected variables in the UI.
