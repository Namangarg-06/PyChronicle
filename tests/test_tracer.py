import os
import tempfile
import pytest
from pychronicle.storage import StateStorage
from pychronicle.tracer import Tracer

def test_tracer_simple_script():
    # Write a simple script to trace
    code = """
a = 10
b = 20
a = a + b
"""
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w", encoding="utf-8") as f:
        f.write(code)
        temp_path = f.name

    try:
        storage = StateStorage(":memory:")
        tracer = Tracer(temp_path, storage)
        tracer.run()

        history = storage.get_history()
        assert len(history) > 0

        # We should find mutations of 'a' and 'b'
        variables = [h["variable_name"] for h in history]
        assert "a" in variables
        assert "b" in variables

        # Verify correct values logged
        a_mutations = [h for h in history if h["variable_name"] == "a"]
        assert len(a_mutations) == 2
        # First assignment to a (line 2)
        assert a_mutations[0]["value"] == 10
        assert a_mutations[0]["line_number"] == 2
        # Second assignment to a (line 4)
        assert a_mutations[1]["value"] == 30
        assert a_mutations[1]["line_number"] == 4

        b_mutations = [h for h in history if h["variable_name"] == "b"]
        assert len(b_mutations) == 1
        assert b_mutations[0]["value"] == 20
        assert b_mutations[0]["line_number"] == 3

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

def test_tracer_nested_function():
    # Write a script with function calls to trace
    code = """
def add_nums(x, y):
    res = x + y
    return res

val = add_nums(5, 7)
"""
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w", encoding="utf-8") as f:
        f.write(code)
        temp_path = f.name

    try:
        storage = StateStorage(":memory:")
        tracer = Tracer(temp_path, storage)
        tracer.run()

        history = storage.get_history()
        assert len(history) > 0

        # We should capture variables 'x', 'y', 'res' inside the function scope, and 'val' at module scope
        variables = [h["variable_name"] for h in history]
        assert "x" in variables
        assert "y" in variables
        assert "res" in variables
        assert "val" in variables

        # Check 'res' mutation has value 12
        res_mutations = [h for h in history if h["variable_name"] == "res"]
        assert len(res_mutations) == 1
        assert res_mutations[0]["value"] == 12
        # res assignment is line 3
        assert res_mutations[0]["line_number"] == 3

        # Check 'val' mutation has value 12
        val_mutations = [h for h in history if h["variable_name"] == "val"]
        assert len(val_mutations) == 1
        assert val_mutations[0]["value"] == 12
        # val assignment is line 6
        assert val_mutations[0]["line_number"] == 6

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
