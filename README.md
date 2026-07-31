# PyChronicle

PyChronicle is an **AST-Powered Time-Travel Debugger** for Python.

Using Python's Abstract Syntax Tree (AST) manipulation and runtime tracing (`sys.settrace`), PyChronicle records the delta state of all local/global variables at every step of execution into an in-memory or file-backed SQLite database. Developers can then use an interactive Terminal User Interface (TUI) to scrub backwards and forwards through time to inspect variable mutations step by step.

---

## Key Features

1. **AST Rewriter & Parser:** Parses Python code using `ast.NodeVisitor` to identify assignments (single, annotated, augmented, walrus `:=`, `for` loop targets, `with` context variables, and starred unpacking `*b`).
2. **Execution Engine:** High-performance Python tracer (`sys.settrace`) capturing variable mutations with sub-0.1ms write latency.
3. **State Storage Engine:** Fast SQLite schema storing chronological variable deltas with point-in-time querying.
4. **Interactive Terminal UI:** Built with Textual. Allows scrubbing backward/forward through steps, viewing source line highlights, inspecting local scope variables, and tracking variable watch histories.

---

## Installation & Quick Start

```bash
# Clone the repository
git clone https://github.com/Namangarg-06/PyChronicle.git
cd PyChronicle

# Install in editable mode
pip install -e .
```

### Running the Debugger

```bash
# Debug a script via CLI
pychronicle run path/to/script.py

# Or run module directly
python -m pychronicle.tui path/to/script.py
```

### Running Tests & Benchmarks

```bash
# Run pytest test suite
pytest

# Run trace validation and storage performance benchmark
python tests/benchmark_audit.py
```

---

## TUI Keyboard Controls

- **Left Arrow (`←`)**: Previous execution step
- **Right Arrow (`→`)**: Next execution step
- **Home**: Jump to first step
- **End**: Jump to final step
- **Page Up / Page Down**: Jump -10 / +10 steps
- **`q`**: Quit PyChronicle

---

## Contributors

- **Tanmay Dhoot** ([@mylifeastanmay-hub](https://github.com/mylifeastanmay-hub)) - *Core Developer & Optimization Lead*
- **Naman Garg** ([@Namangarg-06](https://github.com/Namangarg-06)) - *Project Lead*

For full list of contributions, see [CONTRIBUTORS.md](file:///C:/Users/mylif/.gemini/antigravity/scratch/PyChronicle/CONTRIBUTORS.md).

---

## License

MIT License
