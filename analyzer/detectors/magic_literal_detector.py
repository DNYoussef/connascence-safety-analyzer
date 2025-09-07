"""
Magic Literal Detector

Detects Connascence of Meaning violations - magic literals that should be named constants.
"""

import ast
from typing import List, Tuple, Any, Dict

from utils.types import ConnascenceViolation
from base import DetectorBase


class MagicLiteralDetector(DetectorBase):
    """Detects magic literals that should be named constants."""
    
    def __init__(self, file_path: str, source_lines: List[str]):
        super().__init__(file_path, source_lines)
        self.magic_literals: List[Tuple[ast.AST, Any, Dict]] = []
        self.current_class = None
        self.current_function = None
    
    def detect_violations(self, tree: ast.AST) -> List[ConnascenceViolation]:
        """
        Detect magic literals in the AST tree.
        
        Args:
            tree: AST tree to analyze
            
        Returns:
            List of magic literal violations
        """
        self.violations.clear()
        self.magic_literals.clear()
        
        # Walk the tree to find constants
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant):
                self._analyze_constant(node)
        
        # Process collected literals
        self._finalize_magic_literal_analysis()
        
        return self.violations
    
    def _analyze_constant(self, node: ast.Constant) -> None:
        """Analyze a constant node for magic literal patterns."""
        # Use formal grammar analyzer if available, otherwise fallback
        try:
            from analyzer.formal_grammar import MagicLiteralDetector as FormalDetector
            
            detector = FormalDetector(self.source_lines)
            detector.current_class = self.current_class
            detector.current_function = self.current_function
            
            if detector._should_ignore_literal(node):
                return
            
            context = detector._build_context(node)
            severity = detector._calculate_severity(context)
            
            if severity > 2.0:  # Only flag significant literals
                self.magic_literals.append(
                    (node, node.value, {"context": context, "severity_score": severity, "formal_analysis": True})
                )
        except ImportError:
            # Fallback to simple detection
            if self._is_magic_literal(node.value):
                self.magic_literals.append((node, node.value, {}))
    
    def _is_magic_literal(self, value: Any) -> bool:
        """Simple check for whether a value is a magic literal."""
        if isinstance(value, (int, float)):
            # Skip common safe numbers
            return value not in [0, 1, -1, 2, 10, 100, 1000]
        elif isinstance(value, str) and len(value) > 1:
            # Skip obvious safe strings
            return value not in ["", " ", "\n", "\t", "utf-8", "ascii"]
        
        return False
    
    def _finalize_magic_literal_analysis(self) -> None:
        """Process all collected magic literals and create violations."""
        for item in self.magic_literals:
            if len(item) == 3:
                node, value, context_info = item
            else:
                node, value = item[:2]
                context_info = {"in_conditional": self.is_in_conditional(node)}
            
            # Use formal analysis if available
            if context_info.get("formal_analysis") and "context" in context_info:
                self._create_formal_violation(node, value, context_info)
            else:
                self._create_simple_violation(node, value, context_info)
    
    def _create_formal_violation(self, node: ast.AST, value: Any, context_info: Dict) -> None:
        """Create violation using formal grammar analysis."""
        formal_context = context_info["context"]
        severity_score = context_info.get("severity_score", 3.0)
        
        # Skip low-severity items
        if severity_score < 2.0:
            return
        
        # Determine severity level
        if severity_score > 8.0:
            severity = "high"
        elif severity_score > 5.0:
            severity = "medium"
        else:
            severity = "low"
        
        description = self._create_formal_description(value, formal_context, severity_score)
        recommendation = self._get_formal_recommendation(formal_context)
        
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
                        "class_name": formal_context.class_name,
                    },
                    "severity_score": severity_score,
                    "analysis_type": "formal_grammar",
                },
            )
        )
    
    def _create_simple_violation(self, node: ast.AST, value: Any, context_info: Dict) -> None:
        """Create violation using simple analysis."""
        severity = "medium"  # Default severity
        
        if context_info.get("in_conditional", False):
            severity = "high"
        
        description = f"Magic literal '{value}' should be replaced with a named constant"
        recommendation = "Replace with a well-named constant or configuration value"
        
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
                    "analysis_context": context_info,
                    "in_conditional": context_info.get("in_conditional", False),
                    "analysis_type": "simple",
                },
            )
        )
    
    def _create_formal_description(self, value: Any, formal_context, severity_score: float) -> str:
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
    
    def _get_formal_recommendation(self, formal_context) -> str:
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