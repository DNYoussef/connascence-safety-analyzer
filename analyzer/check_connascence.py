#!/usr/bin/env python3
"""
Connascence Violation Detection Tool for AIVillage

This tool detects various forms of connascence in Python code, focusing on:
- Static forms: Name, Type, Meaning (magic values), Position, Algorithm
- Dynamic forms: Execution, Timing, Value, Identity

Based on Meilir Page-Jones' connascence theory for reducing coupling.
"""

import argparse
import ast
import collections
from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
import sys
import time
from typing import Any

# Import optimization modules for enhanced performance
try:
    OPTIMIZATION_AVAILABLE = True
except ImportError:
    OPTIMIZATION_AVAILABLE = False


@dataclass
class ConnascenceViolation:
    """Represents a detected connascence violation."""

    type: str
    severity: str  # 'critical', 'high', 'medium', 'low'
    file_path: str
    line_number: int
    column: int
    description: str
    recommendation: str
    code_snippet: str
    context: dict[str, Any]


class ConnascenceDetector(ast.NodeVisitor):
    """AST visitor that detects connascence violations."""

    def __init__(self, file_path: str, source_lines: list[str]):
        self.file_path = file_path
        self.source_lines = source_lines
        self.violations: list[ConnascenceViolation] = []

        # Tracking structures
        self.function_definitions: dict[str, ast.FunctionDef] = {}
        self.class_definitions: dict[str, ast.ClassDef] = {}
        self.imports: set[str] = set()
        self.magic_literals: list[tuple[ast.AST, Any]] = []
        self.global_vars: set[str] = set()
        self.sleep_calls: list[ast.Call] = []
        self.positional_params: list[tuple[ast.FunctionDef, int]] = []

        # Algorithm tracking for duplicate detection
        self.function_hashes: dict[str, list[tuple[str, ast.FunctionDef]]] = collections.defaultdict(list)

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

    def _normalize_function_body(self, node: ast.FunctionDef) -> str:
        """Create normalized hash of function body for duplicate detection."""
        # Extract just the structure, not variable names
        body_parts = []
        for stmt in node.body:
            if isinstance(stmt, ast.Return):
                if stmt.value:
                    body_parts.append(f"return {type(stmt.value).__name__}")
                else:
                    body_parts.append("return")
            elif isinstance(stmt, ast.If):
                body_parts.append("if")
            elif isinstance(stmt, ast.For):
                body_parts.append("for")
            elif isinstance(stmt, ast.While):
                body_parts.append("while")
            elif isinstance(stmt, ast.Assign):
                body_parts.append("assign")
            elif isinstance(stmt, ast.Expr):
                if isinstance(stmt.value, ast.Call):
                    body_parts.append("call")
                else:
                    body_parts.append("expr")

        return "|".join(body_parts)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Detect connascence violations in function definitions."""
        self.function_definitions[node.name] = node

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

        # Check for algorithm duplication
        body_hash = self._normalize_function_body(node)
        if len(node.body) > 3:  # Only check substantial functions
            self.function_hashes[body_hash].append((self.file_path, node))

        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        """Detect God Objects using context-aware analysis."""
        self.class_definitions[node.name] = node

        # Use context-aware analysis for more accurate god object detection
        try:
            from .context_analyzer import ContextAnalyzer
            context_analyzer = ContextAnalyzer()
            class_analysis = context_analyzer.analyze_class_context(node, self.source_lines, self.file_path)

            # Only create violation if context-aware analysis determines it's a god object
            if context_analyzer.is_god_object_with_context(class_analysis):
                self.violations.append(
                    ConnascenceViolation(
                        type="god_object",
                        severity="critical",
                        file_path=self.file_path,
                        line_number=node.lineno,
                        column=node.col_offset,
                        description=f"Class '{node.name}' is a God Object ({class_analysis.context.value} context): {class_analysis.god_object_reason}",
                        recommendation="; ".join(class_analysis.recommendations) if class_analysis.recommendations else "Apply Single Responsibility Principle",
                        code_snippet=self.get_code_snippet(node),
                        context={
                            "method_count": class_analysis.method_count,
                            "estimated_loc": class_analysis.lines_of_code,
                            "class_name": node.name,
                            "context_type": class_analysis.context.value,
                            "cohesion_score": class_analysis.cohesion_score,
                            "responsibilities": [r.value for r in class_analysis.responsibilities],
                            "threshold_used": class_analysis.god_object_threshold
                        },
                    )
                )
        except ImportError:
            # Fallback to original logic if context analyzer not available
            method_count = sum(1 for n in node.body if isinstance(n, ast.FunctionDef))
            if hasattr(node, "end_lineno") and node.end_lineno:
                loc = node.end_lineno - node.lineno
            else:
                loc = len(node.body) * 5

            # Use original thresholds as fallback
            if method_count > 18 or loc > 700:
                self.violations.append(
                    ConnascenceViolation(
                        type="god_object",
                        severity="critical",
                        file_path=self.file_path,
                        line_number=node.lineno,
                        column=node.col_offset,
                        description=f"Class '{node.name}' is a God Object: {method_count} methods, ~{loc} lines",
                        recommendation="Split into smaller, focused classes following Single Responsibility Principle",
                        code_snippet=self.get_code_snippet(node),
                        context={"method_count": method_count, "estimated_loc": loc, "class_name": node.name},
                    )
                )

        self.generic_visit(node)

    def visit_Import(self, node: ast.Import):
        """Track imports for dependency analysis."""
        for alias in node.names:
            self.imports.add(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Track imports for dependency analysis."""
        if node.module:
            for alias in node.names:
                self.imports.add(f"{node.module}.{alias.name}")
        self.generic_visit(node)

    def visit_Global(self, node: ast.Global):
        """Track global variable usage (Connascence of Identity)."""
        for name in node.names:
            self.global_vars.add(name)
        self.generic_visit(node)

    def visit_Constant(self, node: ast.Constant):
        """Detect magic literals using formal grammar analysis with context awareness."""
        # Use the formal grammar analyzer for magic literal detection
        try:
            from .formal_grammar import MagicLiteralDetector

            # Create a specialized detector just for this node's context
            detector = MagicLiteralDetector(self.source_lines)
            detector.current_class = getattr(self, '_current_class', None)
            detector.current_function = getattr(self, '_current_function', None)

            # Check if this constant should be flagged
            if detector._should_ignore_literal(node):
                self.generic_visit(node)
                return

            # Build context and calculate severity
            context = detector._build_context(node)
            severity = detector._calculate_severity(context)

            if severity > 2.0:  # Only flag if severity is above threshold
                self.magic_literals.append((node, node.value, {
                    'context': context,
                    'severity_score': severity,
                    'formal_analysis': True
                }))
        except ImportError:
            # Fallback to original simpler detection
            if isinstance(node.value, (int, float)):
                # Skip common safe numbers
                if node.value not in [0, 1, -1, 2, 10, 100, 1000]:
                    self.magic_literals.append((node, node.value))
            elif isinstance(node.value, str) and len(node.value) > 1:
                # Skip obvious safe strings
                if node.value not in ['', ' ', '\n', '\t', 'utf-8', 'ascii']:
                    self.magic_literals.append((node, node.value))

        self.generic_visit(node)

    def _is_magic_string(self, value: str) -> bool:
        """
        Determine if a string value should be considered a magic literal.

        Returns False (not magic) for:
        - Empty strings and single characters
        - Common Python idioms and built-ins
        - Standard encoding/format strings
        - Common separators and whitespace
        - Documentation strings (handled separately)
        """
        try:
            from .constants import SAFE_STRING_PATTERNS
        except ImportError:
            from constants import SAFE_STRING_PATTERNS

        # Very short strings are usually not magic
        if len(value) <= 1:
            return False

        # Check against comprehensive safe patterns
        if value in SAFE_STRING_PATTERNS:
            return False

        # Additional heuristics for non-magic strings
        # File extensions (common ones)
        if len(value) <= 5 and value.startswith('.') and value[1:].isalnum():
            return False

        # Simple separators or repeated characters
        if len(set(value)) == 1 and value[0] in ' -_=*#':
            return False

        # URLs and paths (basic check)
        if any(pattern in value for pattern in ['http://', 'https://', 'file://', '/', '\\']):
            # Might be a path or URL - could still be magic, but lower priority
            return True  # But will get lower severity

        return True

    def _analyze_numeric_context(self, node: ast.AST) -> dict:
        """
        Analyze the context of a numeric literal to determine appropriate severity.

        Returns context information including:
        - Whether it's in a conditional (higher severity)
        - Detected context type (time, size, network, etc.)
        - Confidence level
        """
        context = {'in_conditional': self._is_in_conditional(node)}

        # Get surrounding code context for analysis
        line_content = self._get_line_content(node)
        variable_context = self._get_variable_context(node)

        # Analyze context keywords in surrounding code
        context_type = self._detect_context_type(line_content + ' ' + variable_context)
        if context_type:
            context['detected_context'] = context_type
            context['confidence'] = 'medium'

        # Check for common patterns that suggest non-magic usage
        if self._is_likely_array_index(node):
            context['likely_array_index'] = True
            context['severity_modifier'] = 'lower'

        if self._is_likely_loop_counter(node):
            context['likely_loop_counter'] = True
            context['severity_modifier'] = 'lower'

        return context

    def _analyze_string_context(self, node: ast.AST) -> dict:
        """Analyze context for string literals."""
        context = {'in_conditional': self._is_in_conditional(node)}

        # Check if it's a format string, path, or other structured string
        line_content = self._get_line_content(node)
        if any(pattern in line_content.lower() for pattern in ['format', 'template', 'path', 'url', 'pattern']):
            context['likely_structured'] = True
            context['severity_modifier'] = 'lower'

        return context

    def _is_in_appropriate_context(self, node: ast.AST, context_type: str) -> bool:
        """
        Check if a contextual number appears in appropriate context.

        For example, port numbers should appear near network-related keywords.
        """
        try:
            from .constants import CONTEXT_KEYWORDS
        except ImportError:
            from constants import CONTEXT_KEYWORDS

        if context_type not in CONTEXT_KEYWORDS:
            return False

        keywords = CONTEXT_KEYWORDS[context_type]
        line_content = self._get_line_content(node).lower()
        variable_context = self._get_variable_context(node).lower()

        # Check if any context keywords appear nearby
        full_context = line_content + ' ' + variable_context
        return any(keyword in full_context for keyword in keywords)

    def _detect_context_type(self, text: str) -> str:
        """Detect the likely context type from surrounding text."""
        try:
            from .constants import CONTEXT_KEYWORDS
        except ImportError:
            from constants import CONTEXT_KEYWORDS

        text_lower = text.lower()
        for context_type, keywords in CONTEXT_KEYWORDS.items():
            if any(keyword in text_lower for keyword in keywords):
                return context_type
        return None

    def _get_line_content(self, node: ast.AST) -> str:
        """Get the full line content containing the node."""
        if not hasattr(node, 'lineno') or node.lineno > len(self.source_lines):
            return ""
        return self.source_lines[node.lineno - 1]

    def _get_variable_context(self, node: ast.AST) -> str:
        """
        Get variable names and assignment context around the node.
        This helps detect if numbers are assigned to meaningfully named variables.
        """
        line_content = self._get_line_content(node)

        # Look for assignment patterns
        if '=' in line_content and not any(op in line_content for op in ['==', '!=', '<=', '>=']):
            # Extract variable name before assignment
            parts = line_content.split('=')[0].strip()
            return parts

        # Look for function parameter names
        parent_line_start = max(0, node.lineno - 2)
        parent_lines = ' '.join(self.source_lines[parent_line_start:node.lineno])

        return parent_lines

    def _is_likely_array_index(self, node: ast.AST) -> bool:
        """Check if the number is likely being used as an array index."""
        line_content = self._get_line_content(node)

        # Look for bracket patterns suggesting indexing
        return '[' in line_content and ']' in line_content

    def _is_likely_loop_counter(self, node: ast.AST) -> bool:
        """Check if the number is likely a loop counter or range parameter."""
        line_content = self._get_line_content(node)

        # Look for loop-related keywords
        return any(pattern in line_content for pattern in ['for ', 'range(', 'range ', 'while ', 'enumerate('])


    def visit_Call(self, node: ast.Call):
        """Detect timing-related calls and other patterns."""
        # Connascence of Timing - sleep() calls
        if (isinstance(node.func, ast.Name) and node.func.id == "sleep") or (
            isinstance(node.func, ast.Attribute) and node.func.attr == "sleep"
        ):
            self.sleep_calls.append(node)
            self.violations.append(
                ConnascenceViolation(
                    type="connascence_of_timing",
                    severity="medium",
                    file_path=self.file_path,
                    line_number=node.lineno,
                    column=node.col_offset,
                    description="Sleep-based timing dependency detected",
                    recommendation="Use proper synchronization primitives, events, or async patterns",
                    code_snippet=self.get_code_snippet(node),
                    context={"call_type": "sleep"},
                )
            )

        self.generic_visit(node)

    def finalize_analysis(self):
        """Perform final analysis that requires complete traversal."""
        # Check for algorithm duplicates
        for body_hash, functions in self.function_hashes.items():
            if len(functions) > 1:
                for file_path, func_node in functions:
                    self.violations.append(
                        ConnascenceViolation(
                            type="connascence_of_algorithm",
                            severity="medium",
                            file_path=file_path,
                            line_number=func_node.lineno,
                            column=func_node.col_offset,
                            description=f"Function '{func_node.name}' appears to duplicate algorithm from other functions",
                            recommendation="Extract common algorithm into shared function or module",
                            code_snippet=self.get_code_snippet(func_node),
                            context={
                                "duplicate_count": len(functions),
                                "function_name": func_node.name,
                                "similar_functions": [f.name for _, f in functions if f != func_node],
                            },
                        )
                    )

        # Analyze magic literals with enhanced formal grammar context processing
        for item in self.magic_literals:
            # Handle different formats: old (node, value), enhanced (node, value, context)
            if len(item) == 2:
                node, value = item
                context_info = {'in_conditional': self._is_in_conditional(node)}
                severity_score = 3.0  # Default fallback severity
            else:
                node, value, context_info = item
                # Check if we have formal grammar analysis context
                if context_info.get('formal_analysis') and 'context' in context_info:
                    formal_context = context_info['context']
                    severity_score = context_info.get('severity_score', 3.0)

                    # Use formal grammar analyzer's severity calculation
                    if severity_score < 2.0:
                        continue  # Skip low-severity items
                    elif severity_score > 8.0:
                        severity = "high"
                    elif severity_score > 5.0:
                        severity = "medium"
                    else:
                        severity = "low"

                    # Generate enhanced description using formal context
                    description = self._create_formal_magic_literal_description(value, formal_context, severity_score)
                    recommendation = self._get_formal_magic_literal_recommendation(formal_context)

                    self.violations.append(
                        ConnascenceViolation(
                            type="connascence_of_meaning",
                            severity=severity,
                            file_path=self.file_path,
                            line_number=node.lineno,
                            column=node.col_offset,
                            description=description,
                            recommendation=recommendation,
                            code_snippet=self.get_code_snippet(node),
                            context={
                                "literal_value": value,
                                "formal_context": {
                                    "in_conditional": formal_context.in_conditional,
                                    "in_assignment": formal_context.in_assignment,
                                    "is_constant": formal_context.is_constant,
                                    "is_configuration": formal_context.is_configuration,
                                    "variable_name": formal_context.variable_name,
                                    "function_name": formal_context.function_name,
                                    "class_name": formal_context.class_name
                                },
                                "severity_score": severity_score,
                                "analysis_type": "formal_grammar"
                            },
                        )
                    )
                    continue

            # Fallback to original processing for non-formal analysis
            severity = self._determine_magic_literal_severity(value, context_info)

            # Skip very low priority items if they have contextual justification
            if severity == "informational" and context_info.get('severity_modifier') == 'lower':
                continue

            # Create appropriate description based on context
            description = self._create_magic_literal_description(value, context_info)

            self.violations.append(
                ConnascenceViolation(
                    type="connascence_of_meaning",
                    severity=severity,
                    file_path=self.file_path,
                    line_number=node.lineno,
                    column=node.col_offset,
                    description=description,
                    recommendation=self._get_magic_literal_recommendation(value, context_info),
                    code_snippet=self.get_code_snippet(node),
                    context={
                        "literal_value": value,
                        "analysis_context": context_info,
                        "in_conditional": context_info.get('in_conditional', False),
                        "analysis_type": "legacy"
                    },
                )
            )

        # Check for excessive global usage
        if len(self.global_vars) > 5:
            # Find a representative location (first global usage)
            for node in ast.walk(ast.parse("".join(self.source_lines))):
                if isinstance(node, ast.Global):
                    self.violations.append(
                        ConnascenceViolation(
                            type="connascence_of_identity",
                            severity="high",
                            file_path=self.file_path,
                            line_number=node.lineno,
                            column=node.col_offset,
                            description=f"Excessive global variable usage: {len(self.global_vars)} globals",
                            recommendation="Use dependency injection, configuration objects, or class attributes",
                            code_snippet=self.get_code_snippet(node),
                            context={"global_count": len(self.global_vars), "global_vars": list(self.global_vars)},
                        )
                    )
                    break

    def _is_in_conditional(self, node: ast.AST) -> bool:
        """Check if node is within a conditional statement."""
        # This is a simplified check - in practice you'd walk up the AST
        line_content = self.source_lines[node.lineno - 1] if node.lineno <= len(self.source_lines) else ""
        return any(keyword in line_content for keyword in ["if ", "elif ", "while ", "assert "])

    def _determine_magic_literal_severity(self, value, context_info: dict) -> str:
        """
        Determine the appropriate severity level for a magic literal violation.

        Severity levels:
        - critical: Never used (reserved for system-breaking issues)
        - high: Magic literals in conditionals, unclear large numbers
        - medium: Most magic literals with clear intent
        - low: Small numbers in appropriate contexts, well-named contexts
        - informational: Very low impact cases
        """
        # Start with base severity
        if context_info.get('in_conditional', False):
            base_severity = "high"  # Conditionals are more critical
        else:
            base_severity = "medium"  # Default for most magic literals

        # Apply context-based modifications
        if context_info.get('severity_modifier') == 'lower':
            # Lower severity for array indices, loop counters, etc.
            if base_severity == "high":
                return "medium"
            elif base_severity == "medium":
                return "low"
            else:
                return "informational"

        # Special handling for contextual numbers
        if context_info.get('context_type'):
            # Contextual numbers in wrong context get medium severity
            return "medium"

        # String-specific severity adjustment
        if isinstance(value, str):
            if context_info.get('likely_structured', False):
                return "low" if base_severity != "high" else "medium"

            # Very long strings are more likely to be legitimate magic
            if len(str(value)) > 50:
                return "medium"

        # Numeric-specific severity adjustment
        if isinstance(value, (int, float)):
            # Large numbers are more suspicious
            abs_value = abs(float(value))
            if abs_value > 10000:
                return "high" if base_severity != "low" else "medium"
            elif abs_value > 1000:
                return base_severity
            else:
                # Small numbers in good context get lower severity
                if context_info.get('detected_context'):
                    return "low" if base_severity != "high" else "medium"

        return base_severity

    def _create_magic_literal_description(self, value, context_info: dict) -> str:
        """Create a contextual description for the magic literal violation."""
        try:
            from .constants import DETECTION_MESSAGES
        except ImportError:
            from constants import DETECTION_MESSAGES

        # Use contextual message if we have context information
        if context_info.get('context_type'):
            return DETECTION_MESSAGES['magic_literal_contextual'].format(
                value=value,
                context=context_info['context_type']
            )
        elif context_info.get('detected_context'):
            return DETECTION_MESSAGES['magic_literal_contextual'].format(
                value=value,
                context=context_info['detected_context'] + " context"
            )
        elif context_info.get('severity_modifier') == 'lower':
            return DETECTION_MESSAGES['magic_literal_safe'].format(value=value)
        else:
            return DETECTION_MESSAGES['magic_literal'].format(value=value)

    def _get_magic_literal_recommendation(self, value, context_info: dict) -> str:
        """Get context-appropriate recommendation for magic literal."""
        base_recommendation = "Replace with a well-named constant or configuration value"

        # Provide specific recommendations based on context
        if context_info.get('context_type') == 'network_port':
            return "Define as a named constant like 'DEFAULT_PORT' or use configuration"
        elif context_info.get('context_type') == 'buffer_size':
            return "Define as a named constant like 'BUFFER_SIZE' or 'CHUNK_SIZE'"
        elif context_info.get('detected_context') == 'time':
            return "Define as a named constant like 'TIMEOUT_SECONDS' or 'DEFAULT_DELAY'"
        elif context_info.get('likely_array_index'):
            return "Consider using meaningful names for array indices or constants for offsets"
        elif context_info.get('likely_loop_counter'):
            return "Consider using named constants for loop limits or range bounds"
        elif isinstance(value, str) and context_info.get('likely_structured'):
            return "Consider using constants for format strings, templates, or structured data"
        else:
            return base_recommendation

    def _create_formal_magic_literal_description(self, value, formal_context, severity_score: float) -> str:
        """Create enhanced description using formal grammar context."""
        context_parts = []

        if formal_context.is_constant:
            context_parts.append("constant assignment")
        elif formal_context.is_configuration:
            context_parts.append("configuration context")
        elif formal_context.in_conditional:
            context_parts.append("conditional statement")
        elif formal_context.in_assignment:
            context_parts.append("variable assignment")

        location_parts = []
        if formal_context.class_name:
            location_parts.append(f"class {formal_context.class_name}")
        if formal_context.function_name:
            location_parts.append(f"function {formal_context.function_name}")

        location_str = " in " + ", ".join(location_parts) if location_parts else ""
        context_str = " (" + ", ".join(context_parts) + ")" if context_parts else ""

        severity_desc = "high-priority" if severity_score > 7.0 else "medium-priority" if severity_score > 4.0 else "low-priority"

        return f"{severity_desc.title()} magic literal '{value}'{context_str}{location_str}"

    def _get_formal_magic_literal_recommendation(self, formal_context) -> str:
        """Get enhanced recommendations using formal grammar context."""
        recommendations = []

        if formal_context.is_constant:
            recommendations.append("Consider better naming or documentation for this constant")
        elif formal_context.is_configuration:
            recommendations.append("Move to configuration file or environment variable")
        else:
            recommendations.append("Extract to a named constant")

        if formal_context.in_conditional:
            recommendations.append("Magic literals in conditionals are error-prone - use named constants")

        if formal_context.variable_name:
            recommendations.append(f"Consider improving variable name '{formal_context.variable_name}' to be more descriptive")

        if isinstance(formal_context.literal_value, str):
            recommendations.append("Consider using enums or string constants for better maintainability")
        elif isinstance(formal_context.literal_value, (int, float)):
            if formal_context.literal_value > 1000:
                recommendations.append("Large numbers should always be named constants")
            else:
                recommendations.append("Use descriptive constant names even for small numbers")

        return "; ".join(recommendations)


class ConnascenceAnalyzer:
    """Main analyzer that orchestrates connascence detection."""

    def __init__(self, exclusions: list[str] | None = None):
        self.exclusions = exclusions or [
            "test_*",
            "tests/",
            "*_test.py",
            "conftest.py",
            "deprecated/",
            "archive/",
            "experimental/",
            "__pycache__/",
            ".git/",
            "build/",
            "dist/",
            "*.egg-info/",
            "venv*/",
            "*env*/",
        ]
        self.violations: list[ConnascenceViolation] = []
        self.file_stats: dict[str, dict] = {}

    def should_analyze_file(self, file_path: Path) -> bool:
        """Check if file should be analyzed based on exclusions and file type."""
        path_str = str(file_path)

        # Check file extension support
        supported_extensions = ['.py', '.js', '.mjs', '.c', '.h', '.cpp', '.cxx', '.cc', '.hpp', '.hxx']
        if not any(path_str.endswith(ext) for ext in supported_extensions):
            return False

        # Skip test files, build artifacts, and large files (but allow our test_packages directory)
        skip_patterns = ["__pycache__", ".git", "node_modules", "dist", "build", ".tox", "venv", ".venv"]
        test_patterns = ["test", "spec"]  # Handle test patterns more carefully

        # Check non-test skip patterns
        if any(part in path_str.lower() for part in skip_patterns):
            return False

        # Check test patterns but exclude our test_packages directory
        if "test_packages" not in path_str.lower() and any(part in path_str.lower() for part in test_patterns):
            return False

        # Skip very large files (> 500KB for better multi-language support)
        try:
            if file_path.stat().st_size > 500 * 1024:
                return False
        except (OSError, FileNotFoundError):
            return False

        # Check user exclusions (but allow test_packages directory)
        for exclusion in self.exclusions:
            if exclusion.endswith("/"):
                if exclusion[:-1] in path_str and "test_packages" not in path_str.lower():
                    return False
            elif "*" in exclusion:
                import fnmatch
                # Skip test_* pattern for our test_packages directory
                if exclusion == "test_*" and "test_packages" in path_str.lower():
                    continue
                if fnmatch.fnmatch(path_str, exclusion):
                    return False
            elif exclusion in path_str and "test_packages" not in path_str.lower():
                return False
        return True

    def analyze_file(self, file_path: Path) -> list[ConnascenceViolation]:
        """Analyze a single file for connascence violations."""

        # Determine file type
        if str(file_path).endswith('.py'):
            return self._analyze_python_file(file_path)
        elif str(file_path).endswith(('.js', '.mjs')):
            return self._analyze_javascript_file(file_path)
        elif str(file_path).endswith(('.c', '.h', '.cpp', '.cxx', '.cc', '.hpp', '.hxx')):
            return self._analyze_c_file(file_path)
        else:
            return []  # Unsupported file type

    def _analyze_python_file(self, file_path: Path) -> list[ConnascenceViolation]:
        """Analyze a Python file using AST."""
        try:
            with open(file_path, encoding="utf-8") as f:
                source = f.read()
                source_lines = source.splitlines()

            tree = ast.parse(source, filename=str(file_path))
            detector = ConnascenceDetector(str(file_path), source_lines)
            detector.visit(tree)
            detector.finalize_analysis()

            # Collect file statistics
            self.file_stats[str(file_path)] = {
                "functions": len(detector.function_definitions),
                "classes": len(detector.class_definitions),
                "imports": len(detector.imports),
                "globals": len(detector.global_vars),
                "magic_literals": len(detector.magic_literals),
                "violations": len(detector.violations),
            }

            return detector.violations

        except (SyntaxError, UnicodeDecodeError) as e:
            # Return a violation for unparseable files
            return [
                ConnascenceViolation(
                    type="syntax_error",
                    severity="critical",
                    file_path=str(file_path),
                    line_number=getattr(e, "lineno", 1),
                    column=getattr(e, "offset", 0) or 0,
                    description=f"File cannot be parsed: {e}",
                    recommendation="Fix syntax errors before analyzing connascence",
                    code_snippet="",
                    context={"error": str(e)},
                )
            ]

    def analyze_directory(self, directory: Path) -> list[ConnascenceViolation]:
        """Analyze all supported files in a directory tree."""
        all_violations = []

        # Support multiple languages using Tree-sitter backend
        file_patterns = ["*.py", "*.js", "*.mjs", "*.c", "*.h", "*.cpp", "*.cxx", "*.cc", "*.hpp", "*.hxx"]

        for pattern in file_patterns:
            for source_file in directory.rglob(pattern):
                if self.should_analyze_file(source_file):
                    try:
                        file_violations = self.analyze_file(source_file)
                        all_violations.extend(file_violations)
                        self.violations.extend(file_violations)
                    except Exception as e:
                        # For non-Python files, create a basic violation if parsing fails
                        if not str(source_file).endswith('.py'):
                            print(f"Note: Could not analyze {source_file} - Tree-sitter not fully integrated yet")
                        else:
                            # Re-raise for Python files
                            raise e

        return all_violations

    def generate_report(self, violations: list[ConnascenceViolation], output_format: str = "text") -> str:
        """Generate a report of connascence violations."""
        if output_format == "json":
            return json.dumps([asdict(v) for v in violations], indent=2)

        # Text report
        report_lines = ["=" * 80, "CONNASCENCE ANALYSIS REPORT", "=" * 80, ""]

        # Summary
        severity_counts = collections.Counter(v.severity for v in violations)
        type_counts = collections.Counter(v.type for v in violations)

        report_lines.extend(
            [
                f"Total violations: {len(violations)}",
                f"Files analyzed: {len(self.file_stats)}",
                "",
                "Severity breakdown:",
                f"  Critical: {severity_counts['critical']:3d}",
                f"  High:     {severity_counts['high']:3d}",
                f"  Medium:   {severity_counts['medium']:3d}",
                f"  Low:      {severity_counts['low']:3d}",
                "",
                "Violation types:",
            ]
        )

        for violation_type, count in type_counts.most_common():
            report_lines.append(f"  {violation_type:30s}: {count:3d}")

        report_lines.extend(["", "=" * 80, "DETAILED VIOLATIONS", "=" * 80, ""])

        # Group violations by severity
        for severity in ["critical", "high", "medium", "low"]:
            severity_violations = [v for v in violations if v.severity == severity]
            if not severity_violations:
                continue

            report_lines.extend([f"\n{severity.upper()} SEVERITY ({len(severity_violations)} violations)", "-" * 40])

            for v in severity_violations:
                report_lines.extend(
                    [
                        f"\n{v.type}: {v.description}",
                        f"File: {v.file_path}:{v.line_number}:{v.column}",
                        f"Recommendation: {v.recommendation}",
                    ]
                )

                if v.code_snippet:
                    report_lines.extend(["Code context:", v.code_snippet, ""])

        # Summary statistics
        if self.file_stats:
            report_lines.extend(["\n" + "=" * 80, "FILE STATISTICS", "=" * 80, ""])

            total_functions = sum(stats["functions"] for stats in self.file_stats.values())
            total_classes = sum(stats["classes"] for stats in self.file_stats.values())
            total_imports = sum(stats["imports"] for stats in self.file_stats.values())

            report_lines.extend(
                [
                    f"Total functions analyzed: {total_functions}",
                    f"Total classes analyzed: {total_classes}",
                    f"Total imports: {total_imports}",
                    "",
                    "Most problematic files:",
                ]
            )

            # Sort files by violation count
            sorted_files = sorted(self.file_stats.items(), key=lambda x: x[1]["violations"], reverse=True)[:10]

            for file_path, stats in sorted_files:
                if stats["violations"] > 0:
                    report_lines.append(f"  {os.path.basename(file_path):30s}: {stats['violations']:3d} violations")

        return "\n".join(report_lines)

    def _analyze_javascript_file(self, file_path: Path) -> list[ConnascenceViolation]:
        """Analyze a JavaScript file using text-based patterns."""
        violations = []

        try:
            with open(file_path, encoding="utf-8") as f:
                source = f.read()
                source_lines = source.splitlines()

            # Basic JavaScript connascence detection using regex patterns
            violations.extend(self._detect_js_magic_literals(file_path, source_lines))
            violations.extend(self._detect_js_god_functions(file_path, source_lines))
            violations.extend(self._detect_js_parameter_coupling(file_path, source_lines))

            return violations

        except (OSError, UnicodeDecodeError) as e:
            return [
                ConnascenceViolation(
                    type="file_error",
                    severity="medium",
                    file_path=str(file_path),
                    line_number=1,
                    column=0,
                    description=f"Could not read JavaScript file: {e}",
                    recommendation="Check file encoding and permissions",
                    code_snippet="",
                    context={"error": str(e)},
                )
            ]

    def _analyze_c_file(self, file_path: Path) -> list[ConnascenceViolation]:
        """Analyze a C/C++ file using text-based patterns."""
        violations = []

        try:
            with open(file_path, encoding="utf-8") as f:
                source = f.read()
                source_lines = source.splitlines()

            # Basic C connascence detection using regex patterns
            violations.extend(self._detect_c_magic_literals(file_path, source_lines))
            violations.extend(self._detect_c_god_functions(file_path, source_lines))
            violations.extend(self._detect_c_parameter_coupling(file_path, source_lines))

            return violations

        except (OSError, UnicodeDecodeError) as e:
            return [
                ConnascenceViolation(
                    type="file_error",
                    severity="medium",
                    file_path=str(file_path),
                    line_number=1,
                    column=0,
                    description=f"Could not read C/C++ file: {e}",
                    recommendation="Check file encoding and permissions",
                    code_snippet="",
                    context={"error": str(e)},
                )
            ]

    def _detect_js_magic_literals(self, file_path: Path, source_lines: list[str]) -> list[ConnascenceViolation]:
        """Detect magic literals in JavaScript code using consolidated strategy."""
        from .language_strategies import JavaScriptStrategy
        strategy = JavaScriptStrategy()
        return strategy.detect_magic_literals(file_path, source_lines)

    def _detect_js_god_functions(self, file_path: Path, source_lines: list[str]) -> list[ConnascenceViolation]:
        """Detect god functions in JavaScript using consolidated strategy."""
        from .language_strategies import JavaScriptStrategy
        strategy = JavaScriptStrategy()
        return strategy.detect_god_functions(file_path, source_lines)

    def _detect_js_parameter_coupling(self, file_path: Path, source_lines: list[str]) -> list[ConnascenceViolation]:
        """Detect parameter coupling in JavaScript using consolidated strategy."""
        from .language_strategies import JavaScriptStrategy
        strategy = JavaScriptStrategy()
        return strategy.detect_parameter_coupling(file_path, source_lines)

    def _detect_c_magic_literals(self, file_path: Path, source_lines: list[str]) -> list[ConnascenceViolation]:
        """Detect magic literals in C/C++ code using consolidated strategy."""
        from .language_strategies import CStrategy
        strategy = CStrategy()
        return strategy.detect_magic_literals(file_path, source_lines)

    def _detect_c_god_functions(self, file_path: Path, source_lines: list[str]) -> list[ConnascenceViolation]:
        """Detect god functions in C/C++ using consolidated strategy."""
        from .language_strategies import CStrategy
        strategy = CStrategy()
        return strategy.detect_god_functions(file_path, source_lines)

    def _detect_c_parameter_coupling(self, file_path: Path, source_lines: list[str]) -> list[ConnascenceViolation]:
        """Detect parameter coupling in C functions using consolidated strategy."""
        from .language_strategies import CStrategy
        strategy = CStrategy()
        return strategy.detect_parameter_coupling(file_path, source_lines)


def main():
    """Main entry point for the connascence checker."""
    parser = argparse.ArgumentParser(
        description="Detect connascence violations in Python code",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  connascence scan .                    # Analyze current directory
  connascence scan src/ --json          # JSON output
  connascence scan . --severity high    # Only high+ severity
  connascence scan . --output report.txt # Save to file

  # Legacy usage (deprecated):
  python check_connascence.py .         # Use 'connascence scan .' instead
        """,
    )

    parser.add_argument("path", help="Path to analyze (file or directory)")
    parser.add_argument("--output", "-o", help="Output file (default: stdout)")
    parser.add_argument(
        "--format", "-f", choices=["text", "json"], default="text", help="Output format (default: text)"
    )
    parser.add_argument(
        "--severity", "-s", choices=["low", "medium", "high", "critical"], help="Minimum severity level to report"
    )
    parser.add_argument("--exclude", "-e", action="append", help="Additional exclusion patterns")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    # Initialize analyzer
    exclusions = None
    if args.exclude:
        exclusions = args.exclude

    analyzer = ConnascenceAnalyzer(exclusions)

    # Analyze path
    target_path = Path(args.path)
    if not target_path.exists():
        print(f"Error: Path '{target_path}' does not exist", file=sys.stderr)
        return 1

    if args.verbose:
        print(f"Analyzing {target_path}...")

    start_time = time.time()

    if target_path.is_file():
        violations = analyzer.analyze_file(target_path)
    else:
        violations = analyzer.analyze_directory(target_path)

    elapsed = time.time() - start_time

    # Filter by severity if requested
    if args.severity:
        severity_order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
        min_level = severity_order[args.severity]
        violations = [v for v in violations if severity_order[v.severity] >= min_level]

    # Generate report
    report = analyzer.generate_report(violations, args.format)

    # Output
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(report)
        if args.verbose:
            print(f"Report saved to {args.output}")
    else:
        # Handle encoding issues on Windows
        try:
            print(report)
        except UnicodeEncodeError:
            print(report.encode("ascii", "replace").decode("ascii"))

    if args.verbose:
        print(f"\nAnalysis completed in {elapsed:.2f} seconds")
        print(f"Found {len(violations)} violations")

    # Check for license validation (exit code 4)
    try:
        from licensing import LicenseValidationResult, LicenseValidator
        license_validator = LicenseValidator()
        project_root = target_path if target_path.is_dir() else target_path.parent

        license_report = license_validator.validate_license(project_root)
        if license_report.validation_result != LicenseValidationResult.VALID:
            if args.verbose:
                print(f"\nLicense validation failed: {license_report.validation_result.value}")
                print("Run with license validation for details")
            return 4  # License error

        if args.verbose:
            print("License validation: PASSED")

    except ImportError:
        if args.verbose:
            print("License validation skipped (module not available)")
    except Exception as e:
        if args.verbose:
            print(f"License validation error: {e}")
        return 4  # License error

    # Exit with error code if critical violations found
    critical_count = sum(1 for v in violations if v.severity == "critical")
    return min(critical_count, 1)  # Return 1 if any critical violations


if __name__ == "__main__":
    sys.exit(main())
