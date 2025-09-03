"""
Magic Literal Analyzer - Extracted from ConnascenceASTAnalyzer

Specialized analyzer for detecting Connascence of Meaning (CoM) violations.
Focuses specifically on magic literal detection and analysis.
"""

import ast
import re
from typing import Any, List, Set, Dict
from dataclasses import dataclass

from ..helpers.violation_reporter import ConnascenceViolation


@dataclass 
class MagicLiteralConfig:
    """Configuration for magic literal detection."""
    allowed_numbers: Set[Any] = None
    allowed_strings: Set[str] = None
    min_string_length: int = 4
    security_keywords: List[str] = None
    
    def __post_init__(self):
        if self.allowed_numbers is None:
            self.allowed_numbers = {0, 1, -1, 2, 10, 100, 1000}
        
        if self.allowed_strings is None:
            self.allowed_strings = {"", " ", "\n", "\t"}
        
        if self.security_keywords is None:
            self.security_keywords = [
                "password", "secret", "key", "token", "auth", 
                "crypto", "credential", "hash", "salt"
            ]


class MagicLiteralAnalyzer:
    """Specialized analyzer for magic literal detection."""
    
    def __init__(
        self, 
        file_path: str, 
        source_lines: List[str],
        config: MagicLiteralConfig = None
    ):
        self.file_path = file_path
        self.source_lines = source_lines
        self.config = config or MagicLiteralConfig()
    
    def analyze(self, tree: ast.AST) -> List[ConnascenceViolation]:
        """Analyze tree for magic literal violations."""
        violations = []
        magic_literals = self._collect_magic_literals(tree)
        
        for node, value in magic_literals:
            violation = self._create_magic_literal_violation(node, value)
            if violation:
                violations.append(violation)
        
        return violations
    
    def _collect_magic_literals(self, tree: ast.AST) -> List[tuple[ast.AST, Any]]:
        """Collect all magic literals from the AST."""
        magic_literals = []
        
        for node in ast.walk(tree):
            # Handle deprecated AST nodes for compatibility
            if isinstance(node, ast.Num):
                if self._is_magic_number(node.n):
                    magic_literals.append((node, node.n))
            
            elif isinstance(node, ast.Str):
                if self._is_magic_string(node.s):
                    magic_literals.append((node, node.s))
            
            # Handle current AST nodes
            elif isinstance(node, ast.Constant):
                if isinstance(node.value, (int, float)):
                    if self._is_magic_number(node.value):
                        magic_literals.append((node, node.value))
                
                elif isinstance(node.value, str):
                    if self._is_magic_string(node.value):
                        magic_literals.append((node, node.value))
        
        return magic_literals
    
    def _is_magic_number(self, value: Any) -> bool:
        """Check if a numeric value is a magic literal."""
        if not isinstance(value, (int, float)):
            return False
        
        return value not in self.config.allowed_numbers
    
    def _is_magic_string(self, value: str) -> bool:
        """Check if a string value is a magic literal."""
        if value in self.config.allowed_strings:
            return False
        
        if len(value) < self.config.min_string_length:
            return False
        
        # Skip simple alphanumeric strings (likely identifiers)
        if re.match(r"^[a-zA-Z0-9_-]+$", value):
            return False
        
        return True
    
    def _create_magic_literal_violation(
        self, 
        node: ast.AST, 
        literal_value: Any
    ) -> ConnascenceViolation:
        """Create a violation for a magic literal."""
        # Determine severity based on context
        context = self._analyze_literal_context(node, literal_value)
        severity = self._determine_severity(context)
        
        return ConnascenceViolation(
            type="connascence_of_meaning",
            severity=severity,
            file_path=self.file_path,
            line_number=node.lineno,
            column=node.col_offset,
            description=f"Magic literal '{literal_value}' should be a named constant",
            recommendation=self._generate_recommendation(literal_value, context),
            code_snippet=self._get_code_snippet(node),
            context=context
        )
    
    def _analyze_literal_context(self, node: ast.AST, literal_value: Any) -> Dict[str, Any]:
        """Analyze the context where the literal appears."""
        context = {
            "literal_value": literal_value,
            "literal_type": type(literal_value).__name__,
            "in_conditional": self._is_in_conditional(node),
            "in_assignment": self._is_in_assignment(node),
            "in_comparison": self._is_in_comparison(node),
            "in_arithmetic": self._is_in_arithmetic(node),
            "security_related": self._is_security_related(node),
            "surrounding_text": self._get_surrounding_text(node)
        }
        
        return context
    
    def _determine_severity(self, context: Dict[str, Any]) -> str:
        """Determine violation severity based on context."""
        if context["security_related"]:
            return "critical"
        elif context["in_conditional"] or context["in_comparison"]:
            return "high"
        elif context["in_assignment"]:
            return "medium"
        else:
            return "low"
    
    def _generate_recommendation(self, literal_value: Any, context: Dict[str, Any]) -> str:
        """Generate context-specific recommendation."""
        if context["security_related"]:
            return "Move security-related constants to configuration or environment variables"
        
        if isinstance(literal_value, (int, float)):
            if context["in_conditional"]:
                return f"Replace {literal_value} with a named constant (e.g., MAX_VALUE, THRESHOLD)"
            else:
                return f"Replace {literal_value} with a descriptive constant name"
        
        elif isinstance(literal_value, str):
            if context["security_related"]:
                return "Move string to secure configuration"
            else:
                return "Replace string literal with a named constant or configuration value"
        
        return "Replace with a well-named constant or configuration value"
    
    def _is_in_conditional(self, node: ast.AST) -> bool:
        """Check if node is within a conditional statement."""
        if not hasattr(node, "lineno") or node.lineno > len(self.source_lines):
            return False
        
        line_content = self.source_lines[node.lineno - 1]
        return any(keyword in line_content for keyword in ["if ", "elif ", "while ", "assert "])
    
    def _is_in_assignment(self, node: ast.AST) -> bool:
        """Check if node is part of an assignment."""
        if not hasattr(node, "lineno") or node.lineno > len(self.source_lines):
            return False
        
        line_content = self.source_lines[node.lineno - 1]
        return "=" in line_content and not any(op in line_content for op in ["==", "!=", "<=", ">="])
    
    def _is_in_comparison(self, node: ast.AST) -> bool:
        """Check if node is part of a comparison."""
        if not hasattr(node, "lineno") or node.lineno > len(self.source_lines):
            return False
        
        line_content = self.source_lines[node.lineno - 1]
        return any(op in line_content for op in ["==", "!=", "<", ">", "<=", ">="])
    
    def _is_in_arithmetic(self, node: ast.AST) -> bool:
        """Check if node is part of arithmetic operations."""
        if not hasattr(node, "lineno") or node.lineno > len(self.source_lines):
            return False
        
        line_content = self.source_lines[node.lineno - 1]
        return any(op in line_content for op in ["+", "-", "*", "/", "//", "%", "**"])
    
    def _is_security_related(self, node: ast.AST) -> bool:
        """Check if literal appears in security-related context."""
        surrounding_text = self._get_surrounding_text(node, lines=3).lower()
        return any(keyword in surrounding_text for keyword in self.config.security_keywords)
    
    def _get_surrounding_text(self, node: ast.AST, lines: int = 1) -> str:
        """Get surrounding text context."""
        if not hasattr(node, "lineno") or node.lineno > len(self.source_lines):
            return ""
        
        start = max(0, node.lineno - lines - 1)
        end = min(len(self.source_lines), node.lineno + lines)
        
        return "\n".join(self.source_lines[start:end])
    
    def _get_code_snippet(self, node: ast.AST, context_lines: int = 2) -> str:
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