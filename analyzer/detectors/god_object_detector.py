"""
God Object Detector

Detects God Object violations - classes that are too large and violate Single Responsibility Principle.
"""

import ast
from typing import List

from utils.types import ConnascenceViolation
from base import DetectorBase


class GodObjectDetector(DetectorBase):
    """Detects classes that violate Single Responsibility Principle."""
    
    DEFAULT_METHOD_THRESHOLD = 18
    DEFAULT_LOC_THRESHOLD = 700
    
    def detect_violations(self, tree: ast.AST) -> List[ConnascenceViolation]:
        """
        Detect god objects in the AST tree.
        
        Args:
            tree: AST tree to analyze
            
        Returns:
            List of god object violations
        """
        self.violations.clear()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                self._analyze_class(node)
        
        return self.violations
    
    def _analyze_class(self, node: ast.ClassDef) -> None:
        """Analyze a class for god object patterns."""
        # Try context-aware analysis first
        try:
            from analyzer.context_analyzer import ContextAnalyzer
            
            context_analyzer = ContextAnalyzer()
            class_analysis = context_analyzer.analyze_class_context(node, self.source_lines, self.file_path)
            
            # Only create violation if context-aware analysis determines it's a god object
            if context_analyzer.is_god_object_with_context(class_analysis):
                self._create_context_aware_violation(node, class_analysis)
                return
                
        except ImportError:
            # Fallback to basic analysis
            pass
        
        # Basic analysis fallback
        self._basic_god_object_analysis(node)
    
    def _create_context_aware_violation(self, node: ast.ClassDef, class_analysis) -> None:
        """Create violation using context-aware analysis."""
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
    
    def _basic_god_object_analysis(self, node: ast.ClassDef) -> None:
        """Basic god object analysis when context analyzer is unavailable."""
        method_count = sum(1 for n in node.body if isinstance(n, ast.FunctionDef))
        
        # Estimate lines of code
        if hasattr(node, "end_lineno") and node.end_lineno:
            loc = node.end_lineno - node.lineno
        else:
            loc = len(node.body) * 5  # Rough estimate
        
        # Check thresholds
        if method_count > self.DEFAULT_METHOD_THRESHOLD or loc > self.DEFAULT_LOC_THRESHOLD:
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
                    context={
                        "method_count": method_count,
                        "estimated_loc": loc,
                        "class_name": node.name,
                        "analysis_type": "basic",
                        "method_threshold": self.DEFAULT_METHOD_THRESHOLD,
                        "loc_threshold": self.DEFAULT_LOC_THRESHOLD
                    },
                )
            )