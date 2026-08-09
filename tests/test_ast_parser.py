import os
from pychronicle.ast_parser import find_assignments, parse_file

def test_find_assignments_simple():
    code = """
x = 5
y = "hello"
    """
    assignments = find_assignments(code)
    assert len(assignments) == 2
    
    assert assignments[0]["line_number"] == 2
    assert assignments[0]["variables"] == ["x"]
    assert assignments[0]["type"] == "Assign"
    
    assert assignments[1]["line_number"] == 3
    assert assignments[1]["variables"] == ["y"]
    assert assignments[1]["type"] == "Assign"

def test_find_assignments_annotated_and_augmented():
    code = """
age: int = 25
counter += 1
    """
    assignments = find_assignments(code)
    assert len(assignments) == 2
    
    assert assignments[0]["line_number"] == 2
    assert assignments[0]["variables"] == ["age"]
    assert assignments[0]["type"] == "AnnAssign"
    
    assert assignments[1]["line_number"] == 3
    assert assignments[1]["variables"] == ["counter"]
    assert assignments[1]["type"] == "AugAssign"

def test_find_assignments_unpacking():
    code = """
a, b = 1, 2
[c, d] = [3, 4]
nested_a, (nested_b, nested_c) = 1, (2, 3)
    """
    assignments = find_assignments(code)
    assert len(assignments) == 3
    
    assert assignments[0]["variables"] == ["a", "b"]
    assert assignments[1]["variables"] == ["c", "d"]
    assert assignments[2]["variables"] == ["nested_a", "nested_b", "nested_c"]

def test_find_assignments_attributes_subscripts():
    code = """
self.name = "John"
items[0] = 99
    """
    assignments = find_assignments(code)
    assert len(assignments) == 2
    assert assignments[0]["variables"] == ["self.name"]
    assert assignments[1]["variables"] == ["items"]

def test_find_assignments_starred_unpacking():
    code = "first, *rest, last = [1, 2, 3, 4]"
    assignments = find_assignments(code)
    assert len(assignments) == 1
    assert assignments[0]["variables"] == ["first", "rest", "last"]

def test_find_assignments_uninitialized_annassign():
    code = """
x: int
y: str = "hello"
    """
    assignments = find_assignments(code)
    assert len(assignments) == 1
    assert assignments[0]["variables"] == ["y"]

def test_find_assignments_walrus_for_with():
    code = """
if (n := len([1, 2])) > 0:
    pass
for elem in [1, 2, 3]:
    pass
with open("test.txt") as f:
    pass
    """
    assignments = find_assignments(code)
    assert len(assignments) == 3
    assert assignments[0]["variables"] == ["n"]
    assert assignments[0]["type"] == "NamedExpr"
    assert assignments[1]["variables"] == ["elem"]
    assert assignments[1]["type"] == "For"
    assert assignments[2]["variables"] == ["f"]
    assert assignments[2]["type"] == "With"

def test_parse_file():
    # Use the sample script we created
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sample_file_path = os.path.join(current_dir, "sample_script.py")
    
    assert os.path.exists(sample_file_path)
    
    assignments = parse_file(sample_file_path)
    
    # We should have identified multiple assignments
    assert len(assignments) > 0
    
    # Check that basic assignments are identified
    variables_found = []
    for a in assignments:
        variables_found.extend(a["variables"])
        
    assert "x" in variables_found
    assert "name" in variables_found
    assert "age" in variables_found
    assert "is_active" in variables_found
    assert "a" in variables_found
    assert "b" in variables_found
    assert "c" in variables_found
    assert "d" in variables_found
    assert "nested_a" in variables_found
    assert "nested_b" in variables_found
    assert "nested_c" in variables_found
    assert "counter" in variables_found
    assert "self.name" in variables_found
    assert "items" in variables_found
