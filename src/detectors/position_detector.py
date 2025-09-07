"""
Position Detector - Detects Connascence of Position violations.

Extracted from ConnascenceDetector to follow Single Responsibility Principle.
"""
import ast
from typing import List
from utils.types import ConnascenceViolation


class PositionDetector(ast.NodeVisitor):
    """Detects functions with excessive positional parameters (>3)."""
    
    def __init__(self, file_path: str, source_lines: List[str]):
        self.file_path = file_path
        self.source_lines = source_lines
        self.violations: List[ConnascenceViolation] = []
        self.positional_params: List[tuple[ast.FunctionDef, int]] = []
    
    def get_code_snippet(self, node: ast.AST, context_lines: int = 2) -> str:
        """Extract code snippet around the given node."""
        if not hasattr(node, "lineno"):
            return ""

        start_line = max(0, node.lineno - context_lines - 1)
        end_line = min(len(self.source_lines), node.lineno + context_lines)

        lines = []
        for i in range(start_line, end_line):
            marker = ">>>" if i == node.lineno - 1 else "   "
            lines.append(f"{marker} {i+1:3d}: {self.source_lines[i].rstrip()}")

        return "\n".join(lines)
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Detect Connascence of Position violations in function definitions."""
        # Check for Connascence of Position (>3 positional parameters)
        positional_count = sum(1 for arg in node.args.args if not arg.arg.startswith("_"))
        if positional_count > 3:
            self.positional_params.append((node, positional_count))
            self.violations.append(
                ConnascenceViolation(
                    type="connascence_of_position",
                    severity="high",
                    file_path=self.file_path,
                    line_number=node.lineno,
                    column=node.col_offset,
                    description=f"Function '{node.name}' has {positional_count} positional parameters (>3)",
                    recommendation="Consider using keyword arguments, data classes, or parameter objects",
                    code_snippet=self.get_code_snippet(node),
                    context={"parameter_count": positional_count, "function_name": node.name},
                )
            )

        self.generic_visit(node)
    
    def detect(self, tree: ast.AST) -> List[ConnascenceViolation]:
        """Run position detection and return violations."""
        self.visit(tree)
        return self.violations