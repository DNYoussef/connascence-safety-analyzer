"""
Context Helper - Extracted from MagicLiteralHandler
====================================================

Handles context analysis for magic literals (line content, variable context, etc.).
Part of Phase 1.5 to further decompose god objects.
"""

import ast
from typing import Any, Dict, List, Optional, Set


class ContextHelper:
    """
    Analyzes context for magic literal detection.

    Extracted from MagicLiteralHandler to reduce class size.
    """

    def __init__(self, source_lines: List[str], context_keywords: Optional[Dict] = None):
        """Initialize with source lines and optional context keywords."""
        self.source_lines = source_lines
        self.context_keywords = context_keywords or {}

    def get_line_content(self, node: ast.AST) -> str:
        """Get the full line content containing the node."""
        if not hasattr(node, "lineno") or node.lineno > len(self.source_lines):
            return ""
        return self.source_lines[node.lineno - 1]

    def get_variable_context(self, node: ast.AST) -> str:
        """Get variable names and assignment context around the node."""
        line_content = self.get_line_content(node)

        # Look for assignment patterns
        if "=" in line_content and not any(op in line_content for op in ["==", "!=", "<=", ">="]):
            parts = line_content.split("=")[0].strip()
            return parts

        # Look for function parameter names
        parent_line_start = max(0, node.lineno - 2)
        parent_lines = " ".join(self.source_lines[parent_line_start : node.lineno])

        return parent_lines

    def is_in_conditional(self, node: ast.AST) -> bool:
        """Check if node is within a conditional statement."""
        line_content = self.source_lines[node.lineno - 1] if node.lineno <= len(self.source_lines) else ""
        return any(keyword in line_content for keyword in ["if ", "elif ", "while ", "assert "])

    def is_likely_array_index(self, node: ast.AST) -> bool:
        """Check if the number is likely an array index."""
        line_content = self.get_line_content(node)
        return "[" in line_content and "]" in line_content

    def is_likely_loop_counter(self, node: ast.AST) -> bool:
        """Check if the number is likely a loop counter or range parameter."""
        line_content = self.get_line_content(node)
        return any(pattern in line_content for pattern in ["for ", "range(", "range ", "while ", "enumerate("])

    def detect_context_type(self, text: str) -> Optional[str]:
        """Detect the likely context type from surrounding text."""
        text_lower = text.lower()
        for context_type, keywords in self.context_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                return context_type
        return None

    def is_in_appropriate_context(self, node: ast.AST, context_type: str) -> bool:
        """Check if a contextual number appears in appropriate context."""
        if context_type not in self.context_keywords:
            return False

        keywords = self.context_keywords[context_type]
        line_content = self.get_line_content(node).lower()
        variable_context = self.get_variable_context(node).lower()

        full_context = line_content + " " + variable_context
        return any(keyword in full_context for keyword in keywords)

    def analyze_numeric_context(self, node: ast.AST) -> Dict[str, Any]:
        """Analyze the context of a numeric literal to determine severity."""
        context = {"in_conditional": self.is_in_conditional(node)}

        line_content = self.get_line_content(node)
        variable_context = self.get_variable_context(node)

        context_type = self.detect_context_type(line_content + " " + variable_context)
        if context_type:
            context["detected_context"] = context_type
            context["confidence"] = "medium"

        if self.is_likely_array_index(node):
            context["likely_array_index"] = True
            context["severity_modifier"] = "lower"

        if self.is_likely_loop_counter(node):
            context["likely_loop_counter"] = True
            context["severity_modifier"] = "lower"

        return context

    def analyze_string_context(self, node: ast.AST) -> Dict[str, Any]:
        """Analyze context for string literals."""
        context = {"in_conditional": self.is_in_conditional(node)}

        line_content = self.get_line_content(node)
        if any(pattern in line_content.lower() for pattern in ["format", "template", "path", "url", "pattern"]):
            context["likely_structured"] = True
            context["severity_modifier"] = "lower"

        return context

    def is_magic_string(self, value: str, safe_patterns: Set[str]) -> bool:
        """Determine if a string value should be considered a magic literal."""
        # Very short strings are usually not magic
        if len(value) <= 1:
            return False

        # Check against safe patterns
        if value in safe_patterns:
            return False

        # File extensions
        if len(value) <= 5 and value.startswith(".") and value[1:].isalnum():
            return False

        # Simple separators
        if len(set(value)) == 1 and value[0] in " -_=*#":
            return False

        # URLs and paths
        if any(pattern in value for pattern in ["http://", "https://", "file://", "/", "\\"]):
            return True  # Will get lower severity

        return True
