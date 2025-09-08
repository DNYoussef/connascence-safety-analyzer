"""
God Object Detector - Detects classes that violate Single Responsibility Principle.

Extracted from ConnascenceDetector to follow Single Responsibility Principle.
"""
import ast
from typing import List, Dict
from utils.types import ConnascenceViolation


class GodObjectDetector(ast.NodeVisitor):
    """Detects God Object pattern violations in class definitions."""
    
    def __init__(self, file_path: str, source_lines: List[str]):
        self.file_path = file_path
        self.source_lines = source_lines
        self.violations: List[ConnascenceViolation] = []
        self.class_definitions: Dict[str, ast.ClassDef] = {}
    
    def get_code_snippet(self, node: ast.AST, context_lines: int = 2) -> str:
        """Extract code snippet around the given node. Consolidated implementation."""
        from analyzer.utils.code_utils import get_code_snippet_for_node
        return get_code_snippet_for_node(node, self.source_lines, context_lines)
    
    def _calculate_class_metrics(self, node: ast.ClassDef) -> Dict[str, int]:
        """Calculate metrics for god object detection."""
        method_count = 0
        line_count = 0
        attribute_count = 0
        
        # Count methods and calculate lines
        for child in ast.walk(node):
            if isinstance(child, ast.FunctionDef) and child != node:
                method_count += 1
        
        # Calculate line span
        if hasattr(node, 'end_lineno') and node.end_lineno:
            line_count = node.end_lineno - node.lineno + 1
        else:
            # Fallback: estimate from last method/attribute
            last_line = node.lineno
            for child in ast.walk(node):
                if hasattr(child, 'lineno') and child.lineno > last_line:
                    last_line = child.lineno
            line_count = last_line - node.lineno + 1
        
        # Count class-level attributes (assignments to self)
        for child in ast.walk(node):
            if isinstance(child, ast.Assign):
                for target in child.targets:
                    if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name):
                        if target.value.id == 'self':
                            attribute_count += 1
        
        return {
            'methods': method_count,
            'lines': line_count,
            'attributes': attribute_count
        }
    
    def _is_god_object(self, metrics: Dict[str, int]) -> bool:
        """Determine if class is a god object based on metrics."""
        # God object criteria: >500 lines OR >20 methods OR >15 attributes
        return (
            metrics['lines'] > 500 or 
            metrics['methods'] > 20 or 
            metrics['attributes'] > 15
        )
    
    def visit_ClassDef(self, node: ast.ClassDef):
        """Detect God Objects using context-aware analysis."""
        self.class_definitions[node.name] = node
        
        # Calculate class metrics
        metrics = self._calculate_class_metrics(node)
        
        if self._is_god_object(metrics):
            # Determine severity based on how much it exceeds thresholds
            severity = "medium"
            if metrics['lines'] > 1000 or metrics['methods'] > 40:
                severity = "high"
            elif metrics['lines'] > 2000 or metrics['methods'] > 60:
                severity = "critical"
            
            # Create detailed description
            violations = []
            if metrics['lines'] > 500:
                violations.append(f"{metrics['lines']} lines (>500)")
            if metrics['methods'] > 20:
                violations.append(f"{metrics['methods']} methods (>20)")
            if metrics['attributes'] > 15:
                violations.append(f"{metrics['attributes']} attributes (>15)")
            
            description = f"Class '{node.name}' is a God Object: {', '.join(violations)}"
            
            self.violations.append(
                ConnascenceViolation(
                    type="god_object",
                    severity=severity,
                    file_path=self.file_path,
                    line_number=node.lineno,
                    column=node.col_offset,
                    description=description,
                    recommendation="Consider breaking this class into smaller, focused classes following Single Responsibility Principle",
                    code_snippet=self.get_code_snippet(node),
                    context={
                        "class_name": node.name,
                        "metrics": metrics,
                        "violations": violations
                    }
                )
            )

        self.generic_visit(node)
    
    def detect(self, tree: ast.AST) -> List[ConnascenceViolation]:
        """Run god object detection and return violations."""
        self.visit(tree)
        return self.violations