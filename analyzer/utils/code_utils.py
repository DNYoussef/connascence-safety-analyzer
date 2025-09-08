"""
Code utility functions for connascence analysis.

Consolidates common code snippet extraction functionality 
used across multiple detector classes.
"""
import ast
from typing import List


def get_code_snippet_for_node(node: ast.AST, source_lines: List[str], context_lines: int = 2) -> str:
    """
    Extract code snippet around the given AST node.
    
    This function consolidates the duplicate get_code_snippet implementations
    found across multiple detector classes.
    
    Args:
        node: AST node to get snippet for
        source_lines: Source code lines
        context_lines: Number of context lines before/after
    
    Returns:
        Formatted code snippet with line numbers
    """
    if not hasattr(node, "lineno"):
        return ""

    start_line = max(0, node.lineno - context_lines - 1)
    end_line = min(len(source_lines), node.lineno + context_lines)

    lines = []
    for i in range(start_line, end_line):
        marker = ">>>" if i == node.lineno - 1 else "   "
        lines.append(f"{marker} {i+1:3d}: {source_lines[i].rstrip()}")

    return "\n".join(lines)