"""
Values Detector - Refactored to Eliminate Connascence Violations

Detects Connascence of Values violations using standardized interfaces
and configuration-driven thresholds to eliminate hardcoded coupling.
"""

import ast
from collections import defaultdict
from typing import Dict, List, Set

from utils.types import ConnascenceViolation

from .base import DetectorBase

# Temporarily disabled broken imports
# from ..interfaces.detector_interface import (
#     StandardDetectorInterface, AnalysisContext, DetectorResult,
#     ConfigurableDetectorMixin, register_detector, ViolationSeverity, ConnascenceType
# )
# Temporarily disabled broken utility imports
# from ..utils.common_patterns import ASTUtils, PatternMatcher, ViolationFactory
# from ..utils.config_manager import get_detector_config


# Removed broken decorator and interfaces
class ValuesDetector(DetectorBase):
    """
    Detects value-based coupling and shared constant dependencies.
    Refactored to eliminate Connascence of Values through configuration externalization.
    """

    def __init__(self, file_path: str, source_lines: List[str]):
        super().__init__(file_path, source_lines)

        # Simplified settings (avoiding broken config system)
        self.config = get_detector_config("values_detector")
        self.config_keywords = set(self.config.config_keywords)

        # Track shared values across different contexts
        self.string_literals: Dict[str, List[ast.AST]] = defaultdict(list)
        self.numeric_literals: Dict[str, List[ast.AST]] = defaultdict(list)
        self.constant_assignments: Dict[str, ast.AST] = {}
        self.configuration_patterns: List[ast.AST] = []

    def detect_violations(self, tree: ast.AST) -> List[ConnascenceViolation]:
        """
        Detect value coupling violations in the AST tree using standardized interface.

        Args:
            tree: AST tree to analyze

        Returns:
            DetectorResult with violations and metadata
        """
        import time

        start_time = time.time()

        self.violations.clear()

        # Use common pattern utilities instead of duplicating logic
        literals = PatternMatcher.extract_literal_values(tree)

        # Process string literals
        for node, value in literals["strings"]:
            if not self.is_excluded_value(value, "common_strings"):
                self._track_literal_value(node, value, "string")

        # Process numeric literals
        for node, value in literals["numbers"]:
            if not self.is_excluded_value(value, "common_numbers"):
                self._track_literal_value(node, value, "numeric")

        # Find assignments and configuration patterns
        assignments = ASTUtils.find_nodes_by_type(tree, ast.Assign)
        for node in assignments:
            self._track_assignment(node)

        names = ASTUtils.find_nodes_by_type(tree, ast.Name)
        for node in names:
            self._check_configuration_usage(node)

        # Analyze for violations using configuration-driven thresholds
        self._check_duplicate_literals()
        self._check_configuration_coupling()
        self._check_hardcoded_values_in_logic(tree)

        end_time = time.time()
        processing_time = int((end_time - start_time) * 1000)

        return DetectorResult(
            violations=self.violations,
            metadata={
                "detector_type": "values",
                "strings_analyzed": len(literals["strings"]),
                "numbers_analyzed": len(literals["numbers"]),
                "config_patterns": len(self.configuration_patterns),
            },
            processing_time_ms=processing_time,
        )

    def _track_literal_value(self, node: ast.AST, value, literal_type: str) -> None:
        """Track literal values using configuration-driven exclusions."""
        if literal_type == "string":
            if PatternMatcher.is_magic_string(value, set(self.get_exclusions("common_strings"))):
                self.string_literals[value].append(node)
        elif literal_type == "numeric":
            if PatternMatcher.is_magic_number(value, set(self.get_exclusions("common_numbers"))):
                value_str = str(value)
                self.numeric_literals[value_str].append(node)

    def _track_assignment(self, node: ast.Assign) -> None:
        """Track variable assignments that might be constants or configuration."""
        for target in node.targets:
            if isinstance(target, ast.Name):
                var_name = target.id

                # Track uppercase variables as potential constants
                if var_name.isupper():
                    self.constant_assignments[var_name] = node

                # Track configuration-like assignments
                if any(keyword in var_name.lower() for keyword in self.config_keywords):
                    self.configuration_patterns.append(node)

    def _check_configuration_usage(self, node: ast.Name) -> None:
        """Check for configuration variable usage patterns using centralized logic."""
        if isinstance(node.ctx, ast.Load):  # Variable being read
            if PatternMatcher.detect_configuration_patterns(node, self.config_keywords):
                self.configuration_patterns.append(node)

    def _check_duplicate_literals(self) -> None:
        """Check for duplicate literals using configuration-driven thresholds."""
        min_occurrences = self.get_threshold("duplicate_literal_minimum", 3)

        # Check string literals
        for literal_value, nodes in self.string_literals.items():
            if len(nodes) >= min_occurrences:
                contexts = self._get_usage_contexts(nodes)
                if len(contexts) >= 2:
                    self._create_duplicate_literal_violation(nodes[0], literal_value, "string", len(nodes), contexts)

        # Check numeric literals
        for literal_value, nodes in self.numeric_literals.items():
            if len(nodes) >= min_occurrences:
                contexts = self._get_usage_contexts(nodes)
                if len(contexts) >= 2:
                    self._create_duplicate_literal_violation(nodes[0], literal_value, "numeric", len(nodes), contexts)

    def _check_configuration_coupling(self) -> None:
        """Check for excessive configuration coupling using configurable thresholds."""
        coupling_limit = self.get_threshold("configuration_coupling_limit", 10)
        line_spread_limit = self.get_threshold("configuration_line_spread", 5)

        if len(self.configuration_patterns) > coupling_limit:
            # Group by line to avoid duplicate reporting
            config_lines = set(getattr(node, "lineno", 0) for node in self.configuration_patterns)

            if len(config_lines) > line_spread_limit:
                representative_node = self.configuration_patterns[0]
                self._create_configuration_coupling_violation(
                    representative_node, len(self.configuration_patterns), len(config_lines)
                )

    def _check_hardcoded_values_in_logic(self, tree: ast.AST) -> None:
        """Check for hardcoded values in conditional logic using common patterns."""
        conditionals = ASTUtils.find_nodes_by_type(tree, (ast.If, ast.While))

        for node in conditionals:
            if hasattr(node, "test"):
                hardcoded_values = self._find_hardcoded_in_condition(node.test)
                if hardcoded_values:
                    self._create_hardcoded_logic_violation(node, hardcoded_values)

    def _find_hardcoded_in_condition(self, condition_node: ast.AST) -> List[ast.Constant]:
        """Find hardcoded constant values in conditional expressions."""
        hardcoded = []

        for node in ast.walk(condition_node):
            if isinstance(node, ast.Constant):
                value = node.value
                # Flag interesting hardcoded values (not 0, 1, True, False, None)
                if (isinstance(value, (int, float)) and value not in [0, 1, -1]) or (
                    isinstance(value, str) and len(value) > 1
                ):
                    hardcoded.append(node)

        return hardcoded

    def _get_usage_contexts(self, nodes: List[ast.AST]) -> Set[str]:
        """Get different usage contexts for nodes (function, class, module level)."""
        contexts = set()

        for node in nodes:
            # Simple context detection based on line content
            line_content = self.get_line_content(node).strip()

            if "def " in line_content:
                contexts.add("function")
            elif "class " in line_content:
                contexts.add("class")
            elif "=" in line_content:
                contexts.add("assignment")
            elif "if " in line_content or "elif " in line_content:
                contexts.add("conditional")
            elif "return " in line_content:
                contexts.add("return")
            else:
                contexts.add("expression")

        return contexts

    def _create_duplicate_literal_violation(
        self, node: ast.AST, value: str, value_type: str, usage_count: int, contexts: Set[str]
    ) -> None:
        """Create violation using standardized violation creation."""
        severity = ViolationSeverity.MEDIUM if usage_count >= 5 else ViolationSeverity.LOW
        location = ASTUtils.get_node_location(node, self.context.file_path)
        code_snippet = ASTUtils.extract_code_snippet(self.context.source_lines, node)

        violation = ViolationFactory.create_violation(
            violation_type=ConnascenceType.VALUES,
            severity=severity,
            location=location,
            description=f"Duplicate {value_type} literal '{value}' used {usage_count} times",
            recommendation=f"Extract '{value}' to a named constant to reduce value coupling",
            code_snippet=code_snippet,
            context={
                "violation_type": "duplicate_literal",
                "value": value,
                "value_type": value_type,
                "usage_count": usage_count,
                "contexts": list(contexts),
            },
        )
        self.violations.append(violation)

    def _create_configuration_coupling_violation(self, node: ast.AST, config_count: int, line_count: int) -> None:
        """Create violation for excessive configuration coupling using standardized creation."""
        location = ASTUtils.get_node_location(node, self.context.file_path)
        code_snippet = ASTUtils.extract_code_snippet(self.context.source_lines, node)

        violation = ViolationFactory.create_violation(
            violation_type=ConnascenceType.VALUES,
            severity=ViolationSeverity.HIGH,
            location=location,
            description=f"Excessive configuration coupling: {config_count} config items across {line_count} locations",
            recommendation="Consider using configuration objects or dependency injection",
            code_snippet=code_snippet,
            context={
                "violation_type": "configuration_coupling",
                "config_count": config_count,
                "line_count": line_count,
                "coupling_level": "high",
            },
        )
        self.violations.append(violation)

    def _create_hardcoded_logic_violation(self, node: ast.AST, hardcoded_values: List[ast.Constant]) -> None:
        """Create violation for hardcoded values in logic using standardized creation."""
        values = [str(const.value) for const in hardcoded_values]
        location = ASTUtils.get_node_location(node, self.context.file_path)
        code_snippet = ASTUtils.extract_code_snippet(self.context.source_lines, node)

        violation = ViolationFactory.create_violation(
            violation_type=ConnascenceType.VALUES,
            severity=ViolationSeverity.MEDIUM,
            location=location,
            description=f"Hardcoded values in conditional logic: {', '.join(values)}",
            recommendation="Extract hardcoded values to constants or configuration",
            code_snippet=code_snippet,
            context={
                "violation_type": "hardcoded_logic",
                "hardcoded_values": values,
                "condition_type": type(node).__name__,
            },
        )
        self.violations.append(violation)

    def get_supported_violation_types(self) -> List[str]:
        """Get list of violation types this detector can find."""
        return [ConnascenceType.VALUES]
