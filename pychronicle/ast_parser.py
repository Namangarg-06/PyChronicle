import ast
from typing import Any, List, Dict

class AssignmentVisitor(ast.NodeVisitor):
    """Scans Python AST to identify variable assignments."""
    def __init__(self, source_lines: List[str]):
        self.source_lines = source_lines
        self.assignments: List[Dict[str, Any]] = []

    def _add_assignment(self, lineno: int, targets: list, node_type: str):
        variables = []
        for t in targets:
            variables.extend(self._extract_names(t))
        seen = set()
        unique_vars = [v for v in variables if not (v in seen or seen.add(v))]
        if unique_vars:
            self.assignments.append({
                "line_number": lineno,
                "variables": unique_vars,
                "type": node_type,
                "code": self.source_lines[lineno - 1].strip() if 0 < lineno <= len(self.source_lines) else ""
            })

    def visit_Assign(self, node: ast.Assign):
        self._add_assignment(node.lineno, node.targets, "Assign")
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign):
        if node.value is not None:
            self._add_assignment(node.lineno, [node.target], "AnnAssign")
        self.generic_visit(node)

    def visit_AugAssign(self, node: ast.AugAssign):
        self._add_assignment(node.lineno, [node.target], "AugAssign")
        self.generic_visit(node)

    def visit_NamedExpr(self, node: ast.NamedExpr):
        self._add_assignment(node.lineno, [node.target], "NamedExpr")
        self.generic_visit(node)

    def visit_For(self, node: ast.For):
        self._add_assignment(node.lineno, [node.target], "For")
        self.generic_visit(node)

    def visit_AsyncFor(self, node: ast.AsyncFor):
        self._add_assignment(node.lineno, [node.target], "AsyncFor")
        self.generic_visit(node)

    def visit_With(self, node: ast.With):
        targets = [item.optional_vars for item in node.items if item.optional_vars is not None]
        if targets:
            self._add_assignment(node.lineno, targets, "With")
        self.generic_visit(node)

    def visit_AsyncWith(self, node: ast.AsyncWith):
        targets = [item.optional_vars for item in node.items if item.optional_vars is not None]
        if targets:
            self._add_assignment(node.lineno, targets, "AsyncWith")
        self.generic_visit(node)

    def _extract_names(self, node: ast.AST) -> List[str]:
        if node is None:
            return []
        if isinstance(node, ast.Name):
            return [node.id]
        if isinstance(node, ast.Starred):
            return self._extract_names(node.value)
        if isinstance(node, (ast.Tuple, ast.List)):
            return [n for elt in node.elts for n in self._extract_names(elt)]
        if isinstance(node, ast.Attribute):
            base = self._extract_names(node.value)
            return [f"{base[0]}.{node.attr}"] if base else [node.attr]
        if isinstance(node, ast.Subscript):
            return self._extract_names(node.value)
        return []

def find_assignments(source_code: str) -> List[Dict[str, Any]]:
    tree = ast.parse(source_code)
    visitor = AssignmentVisitor(source_code.splitlines())
    visitor.visit(tree)
    return visitor.assignments

def parse_file(filepath: str) -> List[Dict[str, Any]]:
    with open(filepath, "r", encoding="utf-8") as f:
        return find_assignments(f.read())
