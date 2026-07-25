import ast
from typing import List, Dict, Any

class AssignmentVisitor(ast.NodeVisitor):
    """
    AST Visitor to traverse a Python Abstract Syntax Tree and gather 
    information about variable assignments (ast.Assign and ast.AnnAssign).
    """
    def __init__(self):
        self.assignments: List[Dict[str, Any]] = []

    def visit_Assign(self, node: ast.Assign):
        # Handle standard assignments, including chained assignments (e.g., x = y = 42)
        for target in node.targets:
            # We are extracting variables (represented by ast.Name)
            if isinstance(target, ast.Name):
                var_name = target.id
                line_number = node.lineno
                
                # Get the serialized/string representation of the assigned value
                try:
                    # ast.unparse is available in Python 3.9+
                    val_str = ast.unparse(node.value)
                except AttributeError:
                    # Fallback for older python versions
                    if isinstance(node.value, ast.Constant):
                        val_str = str(node.value.value)
                    elif isinstance(node.value, (ast.Num, ast.Str)):
                        val_str = str(getattr(node.value, 'n', getattr(node.value, 's', '')))
                    else:
                        val_str = "<complex expression>"
                
                self.assignments.append({
                    "line_number": line_number,
                    "variable_name": var_name,
                    "value": val_str
                })
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign):
        # Handle annotated assignments (e.g., x: int = 42)
        if isinstance(node.target, ast.Name) and node.value is not None:
            var_name = node.target.id
            line_number = node.lineno
            
            try:
                val_str = ast.unparse(node.value)
            except AttributeError:
                if isinstance(node.value, ast.Constant):
                    val_str = str(node.value.value)
                else:
                    val_str = "<complex expression>"
            
            self.assignments.append({
                "line_number": line_number,
                "variable_name": var_name,
                "value": val_str
            })
        self.generic_visit(node)

def parse_assignments(file_path: str) -> List[Dict[str, Any]]:
    """
    Reads a Python file, parses its AST, and extracts variable assignments.
    
    Args:
        file_path (str): Path to the Python file to be parsed.
        
    Returns:
        List[Dict[str, Any]]: A list of assignments with structure:
                              {"line_number": int, "variable_name": str, "value": str}
    """
    with open(file_path, "r", encoding="utf-8") as f:
        source = f.read()
    
    tree = ast.parse(source, filename=file_path)
    visitor = AssignmentVisitor()
    visitor.visit(tree)
    return visitor.assignments
