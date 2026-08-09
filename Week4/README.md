# Week 4

This week packages the tracer as a CLI and adds a basic interactive UI for stepping through execution history.

## Run

```bash
pychronicle run sample_script.py
```

## Options

```bash
pychronicle run sample_script.py --no-ui
pychronicle run sample_script.py --watch count --watch total
```

The app can trace a script, save execution data, and inspect variable state over time from the terminal UI.
