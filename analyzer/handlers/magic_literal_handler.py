"""
Magic Literal Handler - Refactored with Composition
====================================================

Orchestrates magic literal detection using smaller focused classes:
- SeverityCalculator: Severity determination
- DescriptionBuilder: Description/recommendation generation
- ContextHelper: Context analysis utilities

This reduces the class from 12+ methods to 5 methods (orchestration only).
"""

import ast
from typing import Any, Dict, List, Set, Tuple

from fixes.phase0.production_safe_assertions import ProductionAssert
from utils.types import ConnascenceViolation

from .severity_calculator import SeverityCalculator
from .description_builder import DescriptionBuilder
from .context_helper import ContextHelper


class MagicLiteralHandler:
    """
    Orchestrates magic literal detection and violation creation.

    Refactored to use composition with:
    - SeverityCalculator for severity logic
    - DescriptionBuilder for messages/recommendations
    - ContextHelper for context analysis
    """

    def __init__(self, file_path: str, source_lines: List[str]):
        """Initialize with file context and helper classes."""
        ProductionAssert.not_none(file_path, "file_path")
        ProductionAssert.not_none(source_lines, "source_lines")

        self.file_path = file_path
        self.source_lines = source_lines
        self.violations: List[ConnascenceViolation] = []

        # Initialize helper classes (composition)
        self._load_constants()
        self.severity_calc = SeverityCalculator()
        self.desc_builder = DescriptionBuilder()
        self.context_helper = ContextHelper(source_lines, self.context_keywords)

        # Set custom messages if loaded
        if hasattr(self, 'detection_messages'):
            self.desc_builder.set_messages(self.detection_messages)

    def _load_constants(self):
        """Load safe patterns and context keywords."""
        try:
            from analyzer.constants import SAFE_STRING_PATTERNS, CONTEXT_KEYWORDS, DETECTION_MESSAGES
            self.safe_string_patterns = SAFE_STRING_PATTERNS
            self.context_keywords = CONTEXT_KEYWORDS
            self.detection_messages = DETECTION_MESSAGES
        except ImportError:
            try:
                from constants import SAFE_STRING_PATTERNS, CONTEXT_KEYWORDS, DETECTION_MESSAGES
                self.safe_string_patterns = SAFE_STRING_PATTERNS
                self.context_keywords = CONTEXT_KEYWORDS
                self.detection_messages = DETECTION_MESSAGES
            except ImportError:
                self.safe_string_patterns = {"", " ", "\n", "\t", "utf-8", "ascii"}
                self.context_keywords = {}
                self.detection_messages = {
                    "magic_literal": "Magic literal '{value}' should be a named constant",
                    "magic_literal_contextual": "Magic literal '{value}' in {context}",
                    "magic_literal_safe": "Low-priority magic literal '{value}'",
                }

    def process_magic_literals(
        self, magic_literals: List[Tuple], code_snippet_fn, global_vars: Set
    ) -> List[ConnascenceViolation]:
        """Process magic literals and return violations."""
        ProductionAssert.not_none(magic_literals, "magic_literals")
        self.violations = []

        for item in magic_literals:
            if len(item) == 2:
                node, value = item
                context_info = {"in_conditional": self.context_helper.is_in_conditional(node)}
                self._process_legacy(node, value, context_info, code_snippet_fn)
            else:
                node, value, context_info = item
                if context_info.get("formal_analysis") and "context" in context_info:
                    formal_context = context_info["context"]
                    severity_score = context_info.get("severity_score", 3.0)
                    self._process_formal(node, value, formal_context, severity_score, code_snippet_fn)
                else:
                    self._process_legacy(node, value, context_info, code_snippet_fn)

        self._check_excessive_globals(global_vars, code_snippet_fn)
        return self.violations

    def _process_legacy(self, node, value, context_info: Dict, code_snippet_fn):
        """Process magic literal using legacy analysis."""
        severity = self.severity_calc.determine_severity(value, context_info)

        if severity == "informational" and context_info.get("severity_modifier") == "lower":
            return

        description = self.desc_builder.create_description(value, context_info)
        recommendation = self.desc_builder.get_recommendation(value, context_info)

        self.violations.append(
            ConnascenceViolation(
                type="connascence_of_meaning",
                severity=severity,
                file_path=self.file_path,
                line_number=node.lineno,
                column=node.col_offset,
                description=description,
                recommendation=recommendation,
                code_snippet=code_snippet_fn(node),
                context={
                    "literal_value": value,
                    "analysis_context": context_info,
                    "in_conditional": context_info.get("in_conditional", False),
                    "analysis_type": "legacy",
                },
            )
        )

    def _process_formal(self, node, value, formal_context, severity_score: float, code_snippet_fn):
        """Process magic literal with formal grammar context."""
        severity = self.severity_calc.calculate_formal_severity(severity_score)

        if severity == "skip":
            return

        description = self.desc_builder.create_formal_description(value, formal_context, severity_score)
        recommendation = self.desc_builder.get_formal_recommendation(formal_context)

        self.violations.append(
            ConnascenceViolation(
                type="connascence_of_meaning",
                severity=severity,
                file_path=self.file_path,
                line_number=node.lineno,
                column=node.col_offset,
                description=description,
                recommendation=recommendation,
                code_snippet=code_snippet_fn(node),
                context={
                    "literal_value": value,
                    "formal_context": {
                        "in_conditional": formal_context.in_conditional,
                        "in_assignment": formal_context.in_assignment,
                        "is_constant": formal_context.is_constant,
                        "is_configuration": formal_context.is_configuration,
                        "variable_name": formal_context.variable_name,
                        "function_name": formal_context.function_name,
                        "class_name": formal_context.class_name,
                    },
                    "severity_score": severity_score,
                    "analysis_type": "formal_grammar",
                },
            )
        )

    def _check_excessive_globals(self, global_vars: Set, code_snippet_fn):
        """Check for excessive global variable usage."""
        if len(global_vars) > 5:
            for node in ast.walk(ast.parse("".join(self.source_lines))):
                if isinstance(node, ast.Global):
                    self.violations.append(
                        ConnascenceViolation(
                            type="connascence_of_identity",
                            severity="high",
                            file_path=self.file_path,
                            line_number=node.lineno,
                            column=node.col_offset,
                            description=f"Excessive global variable usage: {len(global_vars)} globals",
                            recommendation="Use dependency injection, configuration objects, or class attributes",
                            code_snippet=code_snippet_fn(node),
                            context={"global_count": len(global_vars), "global_vars": list(global_vars)},
                        )
                    )
                    break

    # Public API methods for backward compatibility
    def is_magic_string(self, value: str) -> bool:
        """Determine if a string value should be considered a magic literal."""
        return self.context_helper.is_magic_string(value, self.safe_string_patterns)

    def analyze_numeric_context(self, node: ast.AST) -> Dict[str, Any]:
        """Analyze the context of a numeric literal."""
        return self.context_helper.analyze_numeric_context(node)

    def analyze_string_context(self, node: ast.AST) -> Dict[str, Any]:
        """Analyze context for string literals."""
        return self.context_helper.analyze_string_context(node)
