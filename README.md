[![CI](https://github.com/Namangarg-06/Pychronicle/actions/workflows/ci.yml/badge.svg)](https://github.com/Namangarg-06/Pychronicle/actions)

> This project is available under the MIT License — see the `LICENSE` file.
# PyChronicle

PyChronicle is a Python debugging tool that lets you replay execution step by step instead of debugging only forward in time.

It uses Python's AST and runtime tracing to capture variable changes while a script runs, stores them in SQLite, and shows them in a Textual terminal UI so you can move backward and forward through execution history.

## Core idea


## Features


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


## Development status

This project is a multi-week implementation covering AST parsing, execution tracing, SQLite storage, and a terminal UI for debugging.

## License

MIT

> This project is available under the MIT License — see the `LICENSE` file.
```
╔══════════════════════════════════════════════╗
║        PyChronicle — Time Travel Debugger    ║
╚══════════════════════════════════════════════╝

Program: tests/sample_script.py
Execution completed.

Timeline:
──────────────────────────────────────────────
Step   Line    Variable       Value
──────────────────────────────────────────────
	1      4    x            10
	2      5    name         PyChronicle
	3      8    age          25
	4      9    is_active    True
	5     12    a            1
	6     12    b            2
	7     13    c            3
	8     13    d            4
	9     14    nested_a     10
 10     14    nested_b     20
 11     14    nested_c     30
 12     17    counter      0
 13     18    counter      1
 14     19    multiplier   1
 15     20    multiplier   2
 16     29    items        [1, 2, 3]
 17     30    items        [99, 2, 3]
──────────────────────────────────────────────

Current State:

a = 1
age = 25
b = 2
c = 3
counter = 1
d = 4
is_active = True
items = [99, 2, 3]
multiplier = 2
name = PyChronicle
nested_a = 10
nested_b = 20
nested_c = 30
x = 10

Commands:
	b = Previous State
	f = Next State
	w = Watch Variable
	q = Quit
```