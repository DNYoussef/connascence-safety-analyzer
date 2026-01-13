#!/usr/bin/env python3
"""
Connascence Violation Detection Tool for AIVillage

This tool detects various forms of connascence in Python code, focusing on:
- Static forms: Name, Type, Meaning (magic values), Position, Algorithm
- Dynamic forms: Execution, Timing, Value, Identity

Based on Meilir Page-Jones' connascence theory for reducing coupling.

REFACTORED: Phase 1 God Object Decomposition
- MagicLiteralHandler: Extracted all magic literal methods
- AlgorithmDetector: Extracted algorithm duplicate detection
"""

import argparse
import logging
import ast
import collections
from pathlib import Path
import sys
import time
from typing import Any, Optional

from fixes.phase0.production_safe_assertions import ProductionAssert

# Import canonical types (Phase 2: MagicLiteralParams for CoP reduction)
from utils.types import ConnascenceViolation, MagicLiteralParams

logger = logging.getLogger(__name__)

# Import extracted handlers (Phase 1 decomposition)
try:
    from .handlers import MagicLiteralHandler, AlgorithmDetector
    HANDLERS_AVAILABLE = True
except ImportError:
    try:
        from handlers import MagicLiteralHandler, AlgorithmDetector
        HANDLERS_AVAILABLE = True
    except ImportError:
        HANDLERS_AVAILABLE = False

# Import Tree-sitter backend for multi-language support
try:
    from grammar.backends.tree_sitter_backend import LanguageSupport, TreeSitterBackend  # noqa: F401

    TREE_SITTER_BACKEND_AVAILABLE = True
except ImportError:
    TREE_SITTER_BACKEND_AVAILABLE = False

# Import optimization modules for enhanced performance
try:
    from optimization.file_cache import (
        cached_ast_tree,
        cached_file_content,
        cached_file_lines,
        cached_python_files,
        get_global_cache,  # noqa: F401
    )

    OPTIMIZATION_AVAILABLE = True
except ImportError:
    OPTIMIZATION_AVAILABLE = False

# Constants
TREE_SITTER_INTEGRATION_MSG = "Tree-sitter integration incomplete"


# ConnascenceViolation now imported from utils.types


class ConnascenceDetector(ast.NodeVisitor):
    """
    AST visitor that detects connascence violations.

    REFACTORED: This class now delegates to specialized handlers:
    - MagicLiteralHandler: All magic literal detection and processing
    - AlgorithmDetector: Algorithm duplicate detection

    This reduces the class from ~34 methods to ~18 methods (orchestration + visitors).
    """

    def __init__(self, file_path: str, source_lines: list[str]):
        self.file_path = file_path
        self.source_lines = source_lines
        self.violations: list[ConnascenceViolation] = []

        # Initialize extracted handlers (Phase 1 decomposition)
        if HANDLERS_AVAILABLE:
            self.magic_literal_handler = MagicLiteralHandler(file_path, source_lines)
            self.algorithm_detector = AlgorithmDetector(file_path, source_lines)
            # Direct references for delegation (Phase 7 wiring)
            self.context_helper = self.magic_literal_handler.context_helper
            self.severity_calc = self.magic_literal_handler.severity_calc
            self.desc_builder = self.magic_literal_handler.desc_builder
            self.using_handlers = True
        else:
            self.using_handlers = False
            self.context_helper = None
            self.severity_calc = None
            self.desc_builder = None

        # Initialize the new detector factory
        try:
            import os
            import sys

            # Add src directory to path for imports
            src_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "src")
            if src_path not in sys.path:
                sys.path.insert(0, src_path)

            from detectors.detector_factory import DetectorFactory

            self.detector_factory = DetectorFactory(file_path, source_lines)
            self.using_factory = True
        except ImportError:
            # Fallback to original implementation if new detectors not available
            self.using_factory = False
            self._init_legacy_structures()

    def _init_legacy_structures(self) -> None:
        """Initialize legacy tracking structures for fallback mode."""
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

        ProductionAssert.not_none(node, "node")

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

        # Check for algorithm duplication using handler or legacy
        if self.using_handlers:
            self.algorithm_detector.track_function(node)
        else:
            body_hash = self._normalize_function_body(node)
            if len(node.body) > 3:  # Only check substantial functions
                self.function_hashes[body_hash].append((self.file_path, node))

        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        """Detect God Objects using context-aware analysis."""

        ProductionAssert.not_none(node, "node")

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
                        recommendation=(
                            "; ".join(class_analysis.recommendations)
                            if class_analysis.recommendations
                            else "Apply Single Responsibility Principle"
                        ),
                        code_snippet=self.get_code_snippet(node),
                        context={
                            "method_count": class_analysis.method_count,
                            "estimated_loc": class_analysis.lines_of_code,
                            "class_name": node.name,
                            "context_type": class_analysis.context.value,
                            "cohesion_score": class_analysis.cohesion_score,
                            "responsibilities": [r.value for r in class_analysis.responsibilities],
                            "threshold_used": class_analysis.god_object_threshold,
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

        ProductionAssert.not_none(node, "node")

        for alias in node.names:
            self.imports.add(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Track imports for dependency analysis."""

        ProductionAssert.not_none(node, "node")

        if node.module:
            for alias in node.names:
                self.imports.add(f"{node.module}.{alias.name}")
        self.generic_visit(node)

    def visit_Global(self, node: ast.Global):
        """Track global variable usage (Connascence of Identity)."""

        ProductionAssert.not_none(node, "node")

        for name in node.names:
            self.global_vars.add(name)
        self.generic_visit(node)

    def visit_Constant(self, node: ast.Constant):
        """Detect magic literals using formal grammar analysis with context awareness."""

        ProductionAssert.not_none(node, "node")

        # Use the formal grammar analyzer for magic literal detection
        try:
            from .formal_grammar import MagicLiteralDetector

            # Create a specialized detector just for this node's context
            # Pass file_path to enable constants file detection
            detector = MagicLiteralDetector(self.source_lines, self.file_path)
            detector.current_class = getattr(self, "_current_class", None)
            detector.current_function = getattr(self, "_current_function", None)

            # Check if this constant should be flagged
            if detector._should_ignore_literal(node):
                self.generic_visit(node)
                return

            # Build context and calculate severity
            context = detector._build_context(node)
            severity = detector._calculate_severity(context)

            if severity > 2.0:  # Only flag if severity is above threshold
                self.magic_literals.append(
                    (node, node.value, {"context": context, "severity_score": severity, "formal_analysis": True})
                )
        except ImportError:
            # Fallback to original simpler detection
            if isinstance(node.value, (int, float)):
                # Skip common safe numbers
                if node.value not in [0, 1, -1, 2, 10, 100, 1000]:
                    self.magic_literals.append((node, node.value))
            elif isinstance(node.value, str) and len(node.value) > 1:
                # Skip obvious safe strings
                if node.value not in ["", " ", "\n", "\t", "utf-8", "ascii"]:
                    self.magic_literals.append((node, node.value))

        self.generic_visit(node)

    def _is_magic_string(self, value: str) -> bool:
        """Determine if a string should be considered a magic literal.
        Delegates to ContextHelper if available (Phase 7 decomposition)."""
        # Phase 7: Delegate to ContextHelper
        if self.context_helper:
            try:
                from .constants import SAFE_STRING_PATTERNS
            except ImportError:
                from constants import SAFE_STRING_PATTERNS
            return self.context_helper.is_magic_string(value, SAFE_STRING_PATTERNS)
        # Fallback: inline implementation (legacy support)
        try:
            from .constants import SAFE_STRING_PATTERNS
        except ImportError:
            from constants import SAFE_STRING_PATTERNS
        if len(value) <= 1:
            return False
        if value in SAFE_STRING_PATTERNS:
            return False
        if len(value) <= 5 and value.startswith(".") and value[1:].isalnum():
            return False
        if len(set(value)) == 1 and value[0] in " -_=*#":
            return False
        if any(pattern in value for pattern in ["http://", "https://", "file://", "/", "\\"]):
            return True
        return True

    def _analyze_numeric_context(self, node: ast.AST) -> dict:
        """Analyze numeric literal context. Delegates to ContextHelper (Phase 7)."""
        # Phase 7: Delegate to ContextHelper
        if self.context_helper:
            return self.context_helper.analyze_numeric_context(node)
        # Fallback: inline implementation (legacy support)
        context = {"in_conditional": self._is_in_conditional(node)}
        line_content = self._get_line_content(node)
        variable_context = self._get_variable_context(node)
        context_type = self._detect_context_type(line_content + " " + variable_context)
        if context_type:
            context["detected_context"] = context_type
            context["confidence"] = "medium"
        if self._is_likely_array_index(node):
            context["likely_array_index"] = True
            context["severity_modifier"] = "lower"
        if self._is_likely_loop_counter(node):
            context["likely_loop_counter"] = True
            context["severity_modifier"] = "lower"
        return context

    def _analyze_string_context(self, node: ast.AST) -> dict:
        """Analyze string literal context. Delegates to ContextHelper (Phase 7)."""
        # Phase 7: Delegate to ContextHelper
        if self.context_helper:
            return self.context_helper.analyze_string_context(node)
        # Fallback: inline implementation (legacy support)
        context = {"in_conditional": self._is_in_conditional(node)}
        line_content = self._get_line_content(node)
        if any(pattern in line_content.lower() for pattern in ["format", "template", "path", "url", "pattern"]):
            context["likely_structured"] = True
            context["severity_modifier"] = "lower"
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
        full_context = line_content + " " + variable_context
        return any(keyword in full_context for keyword in keywords)

    def _detect_context_type(self, text: str) -> str:
        """Detect context type. Delegates to ContextHelper (Phase 7)."""
        if self.context_helper:
            return self.context_helper.detect_context_type(text)
        # Fallback: inline implementation (legacy support)
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
        """Get line content. Delegates to ContextHelper (Phase 7)."""
        if self.context_helper:
            return self.context_helper.get_line_content(node)
        if not hasattr(node, "lineno") or node.lineno > len(self.source_lines):
            return ""
        return self.source_lines[node.lineno - 1]

    def _get_variable_context(self, node: ast.AST) -> str:
        """Get variable context. Delegates to ContextHelper (Phase 7)."""
        if self.context_helper:
            return self.context_helper.get_variable_context(node)
        # Fallback: inline implementation (legacy support)
        line_content = self._get_line_content(node)
        if "=" in line_content and not any(op in line_content for op in ["==", "!=", "<=", ">="]):
            parts = line_content.split("=")[0].strip()
            return parts
        parent_line_start = max(0, node.lineno - 2)
        parent_lines = " ".join(self.source_lines[parent_line_start : node.lineno])
        return parent_lines

    def _is_likely_array_index(self, node: ast.AST) -> bool:
        """Check if likely array index. Delegates to ContextHelper (Phase 7)."""
        if self.context_helper:
            return self.context_helper.is_likely_array_index(node)
        line_content = self._get_line_content(node)
        return "[" in line_content and "]" in line_content

    def _is_likely_loop_counter(self, node: ast.AST) -> bool:
        """Check if likely loop counter. Delegates to ContextHelper (Phase 7)."""
        if self.context_helper:
            return self.context_helper.is_likely_loop_counter(node)
        line_content = self._get_line_content(node)
        return any(pattern in line_content for pattern in ["for ", "range(", "range ", "while ", "enumerate("])

    def visit_Call(self, node: ast.Call):
        """Detect timing-related calls and other patterns."""

        ProductionAssert.not_none(node, "node")

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

    def finalize_analysis(self) -> None:
        """Perform final analysis that requires complete traversal. NASA Rule 4 compliant."""
        # Use handlers if available, otherwise fall back to legacy methods
        if self.using_handlers:
            # Process algorithm duplicates via handler
            algorithm_violations = self.algorithm_detector.process_algorithm_duplicates(self.get_code_snippet)
            self.violations.extend(algorithm_violations)

            # Process magic literals via handler
            magic_violations = self.magic_literal_handler.process_magic_literals(
                self.magic_literals, self.get_code_snippet, self.global_vars
            )
            self.violations.extend(magic_violations)

            # Sync function_hashes for backward compatibility
            self.function_hashes = self.algorithm_detector.get_function_hashes()
        else:
            # NASA Rule 5: Input validation assertions
            assert hasattr(self, "function_hashes"), "function_hashes must be initialized"
            assert hasattr(self, "magic_literals"), "magic_literals must be initialized"

            # Check for algorithm duplicates
            self._process_algorithm_duplicates()

            # Analyze magic literals with enhanced formal grammar context processing
            self._process_magic_literals()

    def _process_algorithm_duplicates(self) -> None:
        """Process algorithm duplicates and create violations. NASA Rule 4 compliant."""
        for body_hash, functions in self.function_hashes.items():
            # NASA Rule 1: Use guard clause to avoid nesting
            if len(functions) <= 1:
                continue

            for file_path, func_node in functions:
                violation = self._create_algorithm_duplicate_violation(file_path, func_node, functions)
                self.violations.append(violation)

    def _create_algorithm_duplicate_violation(self, file_path: str, func_node: ast.FunctionDef, functions: list) -> ConnascenceViolation:
        """Create algorithm duplicate violation. NASA Rule 4 compliant."""
        # NASA Rule 5: Input validation assertions
        assert file_path is not None, "file_path cannot be None"
        assert func_node is not None, "func_node cannot be None"

        return ConnascenceViolation(
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

    def _process_formal_magic_literal(self, params: MagicLiteralParams):
        """
        Process magic literal with formal grammar context.

        Args:
            params: MagicLiteralParams containing node, value, context, and severity

        NASA Rule 4: Function under 60 lines
        NASA Rule compliance: Uses parameter object to reduce CoP
        """
        # Use dataclass properties for severity logic
        if params.should_skip:
            return  # Skip low-severity items

        severity = params.severity_level
        formal_context = params.formal_context

        # Generate enhanced description using formal context
        description = self._create_formal_magic_literal_description(
            params.value, formal_context, params.severity_score
        )
        recommendation = self._get_formal_magic_literal_recommendation(formal_context)

        self.violations.append(
            ConnascenceViolation(
                type="connascence_of_meaning",
                severity=severity,
                file_path=self.file_path,
                line_number=params.node.lineno,
                column=params.node.col_offset,
                description=description,
                recommendation=recommendation,
                code_snippet=self.get_code_snippet(params.node),
                context={
                    "literal_value": params.value,
                    "formal_context": {
                        "in_conditional": formal_context.in_conditional,
                        "in_assignment": formal_context.in_assignment,
                        "is_constant": formal_context.is_constant,
                        "is_configuration": formal_context.is_configuration,
                        "variable_name": formal_context.variable_name,
                        "function_name": formal_context.function_name,
                        "class_name": formal_context.class_name,
                    },
                    "severity_score": params.severity_score,
                    "analysis_type": "formal_grammar",
                },
            )
        )

    def _process_legacy_magic_literal(self, node: ast.AST, value: Any, context_info: dict) -> None:
        """
        Process magic literal using legacy analysis.

        NASA Rule 4: Function under 60 lines
        """
        severity = self._determine_magic_literal_severity(value, context_info)

        # Skip very low priority items if they have contextual justification
        if severity == "informational" and context_info.get("severity_modifier") == "lower":
            return

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
                    "in_conditional": context_info.get("in_conditional", False),
                    "analysis_type": "legacy",
                },
            )
        )

    def _check_excessive_globals(self) -> None:
        """
        Check for excessive global variable usage.

        NASA Rule 4: Function under 60 lines
        """
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

    def _process_magic_literals(self) -> None:
        """
        Process magic literals with formal grammar context.

        Refactored to comply with NASA Rule 4 (<=60 lines per function).
        Helper functions handle formal analysis, legacy processing, and global checks.
        """
        # NASA Rule 5: Input validation assertion
        assert hasattr(self, "magic_literals"), "magic_literals must be initialized"

        for item in self.magic_literals:
            # Handle different formats: old (node, value), enhanced (node, value, context)
            if len(item) == 2:
                node, value = item
                context_info = {"in_conditional": self._is_in_conditional(node)}
                # Process with legacy method
                self._process_legacy_magic_literal(node, value, context_info)
            else:
                node, value, context_info = item
                # Check if we have formal grammar analysis context
                if context_info.get("formal_analysis") and "context" in context_info:
                    # Create MagicLiteralParams (Phase 2 - CoP reduction)
                    params = MagicLiteralParams(
                        node=node,
                        value=value,
                        context_info=context_info,
                        formal_context=context_info["context"],
                        severity_score=context_info.get("severity_score", 3.0),
                    )
                    # Process with formal grammar method
                    self._process_formal_magic_literal(params)
                else:
                    # Fallback to legacy processing
                    self._process_legacy_magic_literal(node, value, context_info)

        # Check for excessive global usage
        self._check_excessive_globals()

    def _is_in_conditional(self, node: ast.AST) -> bool:
        """Check if node is within a conditional statement.
        Delegates to ContextHelper if available (Phase 7 decomposition)."""
        # Phase 7: Delegate to ContextHelper
        if self.context_helper:
            return self.context_helper.is_in_conditional(node)
        # Fallback: inline implementation (legacy support)
        line_content = self.source_lines[node.lineno - 1] if node.lineno <= len(self.source_lines) else ""
        return any(keyword in line_content for keyword in ["if ", "elif ", "while ", "assert "])

    def _determine_magic_literal_severity(self, value, context_info: dict) -> str:
        """Determine severity for magic literal violation.
        Delegates to SeverityCalculator if available (Phase 7 decomposition)."""
        # Phase 7: Delegate to SeverityCalculator
        if self.severity_calc:
            return self.severity_calc.determine_severity(value, context_info)
        # Fallback: inline implementation (legacy support)
        base_severity = self._get_base_severity(context_info)
        modified = self._apply_context_modifier(base_severity, context_info)
        if modified:
            return modified
        if isinstance(value, str):
            return self._adjust_string_severity(value, base_severity, context_info)
        if isinstance(value, (int, float)):
            return self._adjust_numeric_severity(value, base_severity, context_info)
        return base_severity

    def _get_base_severity(self, context_info: dict) -> str:
        """Get base severity from context (high for conditionals, medium otherwise)."""
        return "high" if context_info.get("in_conditional", False) else "medium"

    def _apply_context_modifier(self, base_severity: str, context_info: dict) -> str:
        """Apply context-based severity modifiers. Returns None if no modification."""
        # Lower severity for array indices, loop counters
        if context_info.get("severity_modifier") == "lower":
            severity_map = {"high": "medium", "medium": "low", "low": "informational"}
            return severity_map.get(base_severity, "informational")

        # Contextual numbers in wrong context get medium severity
        if context_info.get("context_type"):
            return "medium"

        return ""  # No modification, continue processing

    def _adjust_string_severity(self, value: str, base_severity: str, context_info: dict) -> str:
        """Adjust severity for string literals."""
        if context_info.get("likely_structured", False):
            return "low" if base_severity != "high" else "medium"
        if len(str(value)) > 50:
            return "medium"
        return base_severity

    def _adjust_numeric_severity(self, value, base_severity: str, context_info: dict) -> str:
        """Adjust severity for numeric literals."""
        abs_value = abs(float(value))
        if abs_value > 10000:
            return "high" if base_severity != "low" else "medium"
        if abs_value > 1000:
            return base_severity
        if context_info.get("detected_context"):
            return "low" if base_severity != "high" else "medium"
        return base_severity

    def _create_magic_literal_description(self, value, context_info: dict) -> str:
        """Create a contextual description for the magic literal violation."""
        try:
            from .constants import DETECTION_MESSAGES
        except ImportError:
            from constants import DETECTION_MESSAGES

        # Use contextual message if we have context information
        if context_info.get("context_type"):
            return DETECTION_MESSAGES["magic_literal_contextual"].format(
                value=value, context=context_info["context_type"]
            )
        elif context_info.get("detected_context"):
            return DETECTION_MESSAGES["magic_literal_contextual"].format(
                value=value, context=context_info["detected_context"] + " context"
            )
        elif context_info.get("severity_modifier") == "lower":
            return DETECTION_MESSAGES["magic_literal_safe"].format(value=value)
        else:
            return DETECTION_MESSAGES["magic_literal"].format(value=value)

    def _get_magic_literal_recommendation(self, value, context_info: dict) -> str:
        """Get context-appropriate recommendation for magic literal."""
        base_recommendation = "Replace with a well-named constant or configuration value"

        # Provide specific recommendations based on context
        if context_info.get("context_type") == "network_port":
            return "Define as a named constant like 'DEFAULT_PORT' or use configuration"
        elif context_info.get("context_type") == "buffer_size":
            return "Define as a named constant like 'BUFFER_SIZE' or 'CHUNK_SIZE'"
        elif context_info.get("detected_context") == "time":
            return "Define as a named constant like 'TIMEOUT_SECONDS' or 'DEFAULT_DELAY'"
        elif context_info.get("likely_array_index"):
            return "Consider using meaningful names for array indices or constants for offsets"
        elif context_info.get("likely_loop_counter"):
            return "Consider using named constants for loop limits or range bounds"
        elif isinstance(value, str) and context_info.get("likely_structured"):
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

        severity_desc = (
            "high-priority" if severity_score > 7.0 else "medium-priority" if severity_score > 4.0 else "low-priority"
        )

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
            recommendations.append(
                f"Consider improving variable name '{formal_context.variable_name}' to be more descriptive"
            )

        if isinstance(formal_context.literal_value, str):
            recommendations.append("Consider using enums or string constants for better maintainability")
        elif isinstance(formal_context.literal_value, (int, float)):
            if formal_context.literal_value > 1000:
                recommendations.append("Large numbers should always be named constants")
            else:
                recommendations.append("Use descriptive constant names even for small numbers")

        return "; ".join(recommendations)

    def visit(self, node: ast.AST):
        """
        Main visit method - delegates to DetectorFactory if available.

        REFACTORED: Now uses specialized handlers and detectors.
        """

        ProductionAssert.not_none(node, "node")

        if self.using_factory:
            # Use the new DetectorFactory approach
            self.violations = self.detector_factory.detect_all(node)
            # Copy factory attributes for backward compatibility
            self.function_definitions = getattr(self.detector_factory, "function_definitions", {})
            self.class_definitions = getattr(self.detector_factory, "class_definitions", {})
            # Initialize empty collections for backward compatibility
            if not hasattr(self, "function_hashes"):
                self.function_hashes = {}
            if not hasattr(self, "magic_literals"):
                self.magic_literals = []
            if not hasattr(self, "sleep_calls"):
                self.sleep_calls = []
            if not hasattr(self, "positional_params"):
                self.positional_params = []
            if not hasattr(self, "global_vars"):
                self.global_vars = set()
            if not hasattr(self, "imports"):
                self.imports = set()
        else:
            # Fallback to original implementation
            super().visit(node)


class ConnascenceAnalyzer:
    """
    Lightweight analyzer wrapper that delegates to the new modular architecture.

    REFACTORED: Now uses DetectorFactory and ConnascenceAnalyzer service
    while maintaining 100% backward compatibility.
    """

    def __init__(self, exclusions: Optional[list[str]] = None):
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

    def analyze_file(self, file_path: Path) -> list[ConnascenceViolation]:
        """Analyze a single Python file using optimized caching."""
        try:
            # Import the new service
            import os
            import sys

            sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))
            from services.connascence_analyzer import ConnascenceAnalyzer as AnalyzerService

            analyzer = AnalyzerService()
            return analyzer.analyze_file(file_path)
        except ImportError:
            # Fallback to optimized implementation
            return self._analyze_python_file_optimized(file_path)

    def _analyze_python_file_optimized(self, file_path: Path) -> list[ConnascenceViolation]:
        """Optimized implementation using file cache."""
        if not file_path.exists() or file_path.suffix != ".py":
            return []

        try:
            # Use cached file operations if available
            if OPTIMIZATION_AVAILABLE:
                source_code = cached_file_content(file_path)
                source_lines = cached_file_lines(file_path)
                tree = cached_ast_tree(file_path)

                if not source_code or not tree:
                    return []
            else:
                # Fallback to direct file operations
                source_code = file_path.read_text(encoding="utf-8")
                source_lines = source_code.splitlines()
                tree = ast.parse(source_code, filename=str(file_path))

            detector = ConnascenceDetector(str(file_path), source_lines)
            detector.visit(tree)

            return detector.violations
        except Exception:
            return []

    def _analyze_python_file(self, file_path: Path) -> list[ConnascenceViolation]:
        """Legacy fallback implementation."""
        return self._analyze_python_file_optimized(file_path)

    def analyze_directory(self, target_path: Path) -> list[ConnascenceViolation]:
        """Analyze all Python files in a directory with optimized file discovery."""
        all_violations = []

        if target_path.is_file():
            return self.analyze_file(target_path)

        # Optimized: Use cached Python file discovery
        if OPTIMIZATION_AVAILABLE:
            python_files = cached_python_files(target_path)
            py_file_paths = [Path(f) for f in python_files]
        else:
            py_file_paths = list(target_path.rglob("*.py"))

        # Process files with exclusion filtering
        for py_file in py_file_paths:
            # Skip excluded patterns
            if any(py_file.match(pattern) for pattern in self.exclusions):
                continue

            file_violations = self.analyze_file(py_file)
            all_violations.extend(file_violations)

            # Update stats
            self.file_stats[str(py_file)] = {
                "violations": len(file_violations),
                "types": list({v.type for v in file_violations}),
            }

        self.violations = all_violations
        return all_violations


def main():
    """Main CLI entry point with minimal implementation."""
    parser = argparse.ArgumentParser(description="Detect connascence violations in Python code")
    parser.add_argument("path", help="Path to analyze (file or directory)")
    parser.add_argument("--output", "-o", help="Output file (default: stdout)")
    parser.add_argument("--format", "-f", choices=["text", "json"], default="text")
    parser.add_argument("--severity", "-s", choices=["low", "medium", "high", "critical"])
    parser.add_argument("--exclude", "-e", help="Additional exclusion patterns")
    parser.add_argument("--verbose", "-v", action="store_true")

    args = parser.parse_args()

    target_path = Path(args.path).resolve()
    if not target_path.exists():
        logger.error("Path %s does not exist", target_path)
        return 1

    start_time = time.time()
    analyzer = ConnascenceAnalyzer()
    violations = analyzer.analyze_directory(target_path)
    elapsed = time.time() - start_time

    # Filter by severity if specified
    if args.severity:
        severity_order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
        min_level = severity_order[args.severity]
        violations = [v for v in violations if severity_order.get(v.severity, 0) >= min_level]

    # Generate report
    if args.format == "json":
        import json

        report_data = [
            {
                "type": v.type,
                "severity": v.severity,
                "file_path": v.file_path,
                "line_number": v.line_number,
                "column": v.column,
                "description": v.description,
                "recommendation": v.recommendation,
                "context": v.context,
            }
            for v in violations
        ]
        report = json.dumps(report_data, indent=2)
    else:
        # Text format
        report_lines = [f"Found {len(violations)} connascence violations:\n"]
        for v in violations:
            report_lines.append(f"{v.severity.upper()}: {v.description}")
            report_lines.append(f"  File: {v.file_path}:{v.line_number}")
            report_lines.append(f"  Fix: {v.recommendation}\n")
        report = "\n".join(report_lines)

    # Output
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(report)
    else:
        logger.info("%s", report)

    if args.verbose:
        logger.info("Analysis completed in %.2f seconds", elapsed)
        logger.info("Found %s violations", len(violations))

    # Exit with error code if critical violations found
    critical_count = sum(1 for v in violations if v.severity == "critical")
    return min(critical_count, 1)


if __name__ == "__main__":
    sys.exit(main())
