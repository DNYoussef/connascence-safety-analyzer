#!/usr/bin/env python3
"""
Enhanced God Object Detection with Cohesion-Based Scoring

Implements LCOM5 cohesion metrics and statistical outlier detection instead of 
fixed thresholds to reduce false positives while maintaining detection quality.
"""

import ast
from dataclasses import dataclass, field
from enum import Enum
import math
import statistics
from typing import Dict, List, Optional, Set, Tuple, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ClassRole(Enum):
    """Semantic roles that affect god object scoring."""
    AGGREGATOR = "aggregator"        # Intentionally coordinates many components
    FACADE = "facade"               # Simplifies complex subsystem interface  
    CONTROLLER = "controller"       # Handles user input/orchestration
    DATA_CONTAINER = "data"         # Holds data with minimal behavior
    UTILITY = "utility"             # Collection of related utility functions
    GENERIC = "generic"             # Standard business logic class


@dataclass
class CohesionMetrics:
    """Cohesion metrics for a class."""
    
    lcom5: float = 0.0              # Lack of Cohesion of Methods (v5)
    method_attribute_ratio: float = 0.0  # Methods per attribute
    interface_cohesion: float = 0.0      # Public method consistency
    data_cohesion: float = 0.0           # Attribute usage consistency
    behavioral_cohesion: float = 0.0     # Method collaboration
    
    @property
    def overall_cohesion(self) -> float:
        """Calculate overall cohesion score (0=bad, 1=good)."""
        # Invert LCOM5 (lower is better) and weight with other metrics
        inverted_lcom5 = max(0, 1 - (self.lcom5 / 5.0))  # Normalize LCOM5
        
        weights = [0.3, 0.2, 0.2, 0.15, 0.15]  # LCOM5 gets highest weight
        metrics = [inverted_lcom5, self.interface_cohesion, self.data_cohesion, 
                  self.behavioral_cohesion, min(1.0, self.method_attribute_ratio / 3.0)]
        
        return sum(w * m for w, m in zip(weights, metrics))


@dataclass
class ComplexityMetrics:
    """Complexity metrics for statistical analysis."""
    
    method_count: int = 0
    line_count: int = 0
    attribute_count: int = 0
    public_method_count: int = 0
    cyclomatic_complexity: float = 0.0
    nesting_depth: int = 0
    fan_out: int = 0                    # Dependencies on other classes
    
    def complexity_score(self) -> float:
        """Calculate normalized complexity score."""
        # Z-score based normalization will be applied later
        return (
            self.method_count * 1.0 +
            self.line_count * 0.01 + 
            self.attribute_count * 1.5 +
            self.cyclomatic_complexity * 0.5 +
            self.nesting_depth * 2.0 +
            self.fan_out * 1.2
        )


@dataclass 
class ClassAnalysis:
    """Complete analysis of a class."""
    
    name: str
    file_path: str
    role: ClassRole = ClassRole.GENERIC
    cohesion: CohesionMetrics = field(default_factory=CohesionMetrics)
    complexity: ComplexityMetrics = field(default_factory=ComplexityMetrics)
    centrality: float = 0.0             # Position in dependency graph
    z_score: float = 0.0                # Statistical outlier score
    is_outlier: bool = False
    

@dataclass
class GodObjectFinding:
    """God object detection result with contextual information."""
    
    class_name: str
    file_path: str
    severity: str                       # low, medium, high, critical
    confidence: float                   # 0.0 to 1.0
    god_object_score: float
    cohesion_score: float
    complexity_z_score: float
    role: ClassRole
    
    # Detailed metrics
    method_count: int
    line_count: int
    attribute_count: int
    lcom5: float
    
    # Evidence and suggestions
    evidence: List[str] = field(default_factory=list)
    refactor_suggestions: List[str] = field(default_factory=list)
    
    @property
    def is_god_object(self) -> bool:
        """Determine if this is actually a god object."""
        # Require high complexity AND low cohesion AND outlier status
        return (
            self.complexity_z_score > 2.0 and  # 95th percentile outlier
            self.cohesion_score < 0.4 and      # Poor cohesion
            self.confidence > 0.7 and          # High confidence
            self.role != ClassRole.AGGREGATOR   # Not an intentional aggregator
        )


class CohesionAnalyzer:
    """Analyzes class cohesion using multiple metrics."""
    
    def calculate_lcom5(self, class_node: ast.ClassDef) -> float:
        """Calculate LCOM5 (Lack of Cohesion of Methods version 5)."""
        methods = [n for n in class_node.body if isinstance(n, ast.FunctionDef)]
        
        if len(methods) <= 1:
            return 0.0
        
        # Build method-attribute usage matrix
        method_attributes = {}
        all_attributes = set()
        
        for method in methods:
            attributes = set()
            for node in ast.walk(method):
                if (isinstance(node, ast.Attribute) and 
                    isinstance(node.value, ast.Name) and 
                    node.value.id == 'self'):
                    attributes.add(node.attr)
                    all_attributes.add(node.attr)
            method_attributes[method.name] = attributes
        
        if not all_attributes:
            return 0.0
        
        # Calculate LCOM5: (M - ((Aj))) / (M - 1)
        # Where M = number of methods, (Aj) = number of methods using attribute j
        M = len(methods)
        total_method_attribute_usage = 0
        
        for attr in all_attributes:
            methods_using_attr = sum(1 for attr_set in method_attributes.values() 
                                   if attr in attr_set)
            total_method_attribute_usage += methods_using_attr
        
        if M <= 1:
            return 0.0
            
        lcom5 = (M - (total_method_attribute_usage / len(all_attributes))) / (M - 1)
        return max(0.0, lcom5)  # LCOM5 can be negative, clamp to 0
    
    def calculate_method_attribute_ratio(self, class_node: ast.ClassDef) -> float:
        """Calculate ratio of methods to attributes."""
        methods = [n for n in class_node.body if isinstance(n, ast.FunctionDef)]
        
        # Count unique attributes
        attributes = set()
        for method in methods:
            for node in ast.walk(method):
                if (isinstance(node, ast.Attribute) and 
                    isinstance(node.value, ast.Name) and 
                    node.value.id == 'self'):
                    attributes.add(node.attr)
        
        if not attributes:
            return len(methods)  # All methods, no data = utility class pattern
        
        return len(methods) / len(attributes)
    
    def calculate_interface_cohesion(self, class_node: ast.ClassDef) -> float:
        """Calculate cohesion of public interface."""
        public_methods = [n for n in class_node.body 
                         if isinstance(n, ast.FunctionDef) and not n.name.startswith('_')]
        
        if len(public_methods) <= 1:
            return 1.0
        
        # Analyze parameter and return type consistency
        param_types = []
        return_patterns = []
        
        for method in public_methods:
            # Count parameters (simple heuristic)
            param_count = len(method.args.args) - 1  # Exclude self
            param_types.append(param_count)
            
            # Check for return statements
            has_return = any(isinstance(node, ast.Return) for node in ast.walk(method))
            return_patterns.append(has_return)
        
        # Calculate consistency
        if not param_types:
            return 1.0
        
        param_consistency = 1.0 - (statistics.stdev(param_types) / max(1, statistics.mean(param_types)))
        return_consistency = len(set(return_patterns)) / len(return_patterns)  # 1.0 = all same
        
        return (param_consistency + return_consistency) / 2.0
    
    def calculate_behavioral_cohesion(self, class_node: ast.ClassDef) -> float:
        """Calculate how well methods work together."""
        methods = [n for n in class_node.body if isinstance(n, ast.FunctionDef)]
        
        if len(methods) <= 1:
            return 1.0
        
        # Count method-to-method calls within the class
        method_names = {m.name for m in methods}
        internal_calls = 0
        total_calls = 0
        
        for method in methods:
            for node in ast.walk(method):
                if isinstance(node, ast.Call):
                    total_calls += 1
                    # Check for self.method_name() calls
                    if (isinstance(node.func, ast.Attribute) and
                        isinstance(node.func.value, ast.Name) and
                        node.func.value.id == 'self' and
                        node.func.attr in method_names):
                        internal_calls += 1
        
        if total_calls == 0:
            return 0.5  # Neutral - no method calls at all
        
        return internal_calls / total_calls


class StatisticalGodObjectDetector:
    """God object detector using statistical analysis and cohesion metrics."""
    
    def __init__(self, percentile_threshold: float = 95.0, min_classes_for_stats: int = 10):
        self.percentile_threshold = percentile_threshold
        self.min_classes_for_stats = min_classes_for_stats
        self.cohesion_analyzer = CohesionAnalyzer()
        self.class_analyses: List[ClassAnalysis] = []
        
    def analyze_codebase(self, root_path: Path) -> List[GodObjectFinding]:
        """Analyze entire codebase with statistical approach."""
        self.class_analyses = []
        
        # First pass: collect all classes and metrics
        for py_file in root_path.rglob("*.py"):
            if self._should_skip_file(py_file):
                continue
            
            try:
                self._analyze_file(py_file)
            except Exception as e:
                logger.warning(f"Error analyzing {py_file}: {e}")
        
        # Second pass: calculate statistical thresholds and identify outliers
        return self._identify_god_objects()
    
    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if file should be skipped."""
        skip_patterns = [
            "__pycache__", ".pytest_cache", "node_modules", "venv", ".venv",
            "migrations", "test_", "_test.py", "__init__.py"
        ]
        return any(pattern in str(file_path) for pattern in skip_patterns)
    
    def _analyze_file(self, file_path: Path) -> None:
        """Analyze a single file and collect class metrics."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            lines = content.split('\n')
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    analysis = self._analyze_class(file_path, node, lines, tree)
                    self.class_analyses.append(analysis)
                    
        except Exception as e:
            logger.error(f"Failed to analyze {file_path}: {e}")
    
    def _analyze_class(self, file_path: Path, class_node: ast.ClassDef, 
                       lines: List[str], full_tree: ast.AST) -> ClassAnalysis:
        """Perform complete analysis of a single class."""
        
        # Calculate cohesion metrics
        cohesion = CohesionMetrics()
        cohesion.lcom5 = self.cohesion_analyzer.calculate_lcom5(class_node)
        cohesion.method_attribute_ratio = self.cohesion_analyzer.calculate_method_attribute_ratio(class_node)
        cohesion.interface_cohesion = self.cohesion_analyzer.calculate_interface_cohesion(class_node)
        cohesion.behavioral_cohesion = self.cohesion_analyzer.calculate_behavioral_cohesion(class_node)
        
        # Calculate complexity metrics
        complexity = ComplexityMetrics()
        methods = [n for n in class_node.body if isinstance(n, ast.FunctionDef)]
        complexity.method_count = len(methods)
        complexity.public_method_count = len([m for m in methods if not m.name.startswith('_')])
        
        # Count attributes
        attributes = set()
        for method in methods:
            for node in ast.walk(method):
                if (isinstance(node, ast.Attribute) and 
                    isinstance(node.value, ast.Name) and 
                    node.value.id == 'self'):
                    attributes.add(node.attr)
        complexity.attribute_count = len(attributes)
        
        # Calculate line count
        start_line = class_node.lineno
        end_line = getattr(class_node, 'end_lineno', start_line)
        class_lines = [line for line in lines[start_line-1:end_line] 
                      if line.strip() and not line.strip().startswith('#')]
        complexity.line_count = len(class_lines)
        
        # Calculate cyclomatic complexity
        complexity.cyclomatic_complexity = self._calculate_complexity(class_node)
        
        # Determine class role
        role = self._determine_class_role(class_node, complexity)
        
        return ClassAnalysis(
            name=class_node.name,
            file_path=str(file_path),
            role=role,
            cohesion=cohesion,
            complexity=complexity
        )
    
    def _calculate_complexity(self, node: ast.AST) -> float:
        """Calculate cyclomatic complexity."""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.With)):
                complexity += 1
            elif isinstance(child, ast.Try):
                complexity += len(child.handlers)
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
            elif isinstance(child, ast.comprehension):
                complexity += 1
        
        return float(complexity)
    
    def _determine_class_role(self, class_node: ast.ClassDef, complexity: ComplexityMetrics) -> ClassRole:
        """Determine the semantic role of a class."""
        class_name_lower = class_node.name.lower()
        
        # Check for common patterns in naming
        if any(pattern in class_name_lower for pattern in ['facade', 'proxy', 'adapter']):
            return ClassRole.FACADE
        
        if any(pattern in class_name_lower for pattern in ['controller', 'handler', 'manager']):
            return ClassRole.CONTROLLER
        
        if any(pattern in class_name_lower for pattern in ['data', 'model', 'entity', 'dto']):
            return ClassRole.DATA_CONTAINER
        
        if any(pattern in class_name_lower for pattern in ['util', 'helper', 'tool']):
            return ClassRole.UTILITY
        
        if any(pattern in class_name_lower for pattern in ['coordinator', 'orchestrator', 'aggregator']):
            return ClassRole.AGGREGATOR
        
        # Analyze structure to infer role
        if complexity.method_count > 15 and complexity.attribute_count < 5:
            return ClassRole.UTILITY  # Many methods, little data
        
        if complexity.attribute_count > 10 and complexity.method_count < 5:
            return ClassRole.DATA_CONTAINER  # Lots of data, few methods
        
        return ClassRole.GENERIC
    
    def _identify_god_objects(self) -> List[GodObjectFinding]:
        """Use statistical analysis to identify god objects."""
        if len(self.class_analyses) < self.min_classes_for_stats:
            logger.warning(f"Only {len(self.class_analyses)} classes found, using simple thresholds")
            return self._fallback_detection()
        
        # Calculate z-scores for complexity metrics
        complexity_scores = [analysis.complexity.complexity_score() 
                           for analysis in self.class_analyses]
        
        if len(complexity_scores) < 2:
            return []
        
        mean_complexity = statistics.mean(complexity_scores)
        stdev_complexity = statistics.stdev(complexity_scores) if len(complexity_scores) > 1 else 1.0
        
        # Calculate outlier threshold
        outlier_threshold = statistics.quantiles(complexity_scores, n=100)[int(self.percentile_threshold)-1]
        
        findings = []
        
        for analysis in self.class_analyses:
            complexity_score = analysis.complexity.complexity_score()
            
            # Calculate z-score
            analysis.z_score = (complexity_score - mean_complexity) / max(stdev_complexity, 0.1)
            analysis.is_outlier = complexity_score >= outlier_threshold
            
            # Calculate god object score
            god_score = self._calculate_god_object_score(analysis)
            
            if analysis.is_outlier or god_score > 0.7:
                finding = self._create_finding(analysis, god_score)
                findings.append(finding)
        
        return sorted(findings, key=lambda f: f.god_object_score, reverse=True)
    
    def _calculate_god_object_score(self, analysis: ClassAnalysis) -> float:
        """Calculate comprehensive god object score."""
        # Factors that increase god object likelihood
        complexity_factor = min(1.0, analysis.z_score / 3.0)  # Normalize z-score
        low_cohesion_factor = max(0.0, 1.0 - analysis.cohesion.overall_cohesion)
        
        # Role-based adjustments
        role_multiplier = {
            ClassRole.AGGREGATOR: 0.3,      # Aggregators are allowed to be complex
            ClassRole.FACADE: 0.5,          # Facades coordinate but shouldn't be gods
            ClassRole.CONTROLLER: 0.7,      # Controllers can be complex but should be cohesive
            ClassRole.DATA_CONTAINER: 0.2,  # Data containers should be simple
            ClassRole.UTILITY: 0.6,         # Utilities can have many methods
            ClassRole.GENERIC: 1.0          # No special consideration
        }.get(analysis.role, 1.0)
        
        # Combine factors
        base_score = (complexity_factor * 0.6 + low_cohesion_factor * 0.4)
        adjusted_score = base_score * role_multiplier
        
        return min(1.0, adjusted_score)
    
    def _create_finding(self, analysis: ClassAnalysis, god_score: float) -> GodObjectFinding:
        """Create a god object finding with detailed information."""
        
        # Determine severity
        if god_score >= 0.9:
            severity = "critical"
        elif god_score >= 0.7:
            severity = "high" 
        elif god_score >= 0.5:
            severity = "medium"
        else:
            severity = "low"
        
        # Calculate confidence
        confidence = min(1.0, god_score + (0.2 if analysis.is_outlier else 0.0))
        
        # Generate evidence
        evidence = []
        if analysis.z_score > 2.0:
            evidence.append(f"Complexity z-score: {analysis.z_score:.1f} (95th+ percentile)")
        if analysis.cohesion.overall_cohesion < 0.4:
            evidence.append(f"Low cohesion score: {analysis.cohesion.overall_cohesion:.2f}")
        if analysis.cohesion.lcom5 > 2.0:
            evidence.append(f"High LCOM5: {analysis.cohesion.lcom5:.2f} (methods don't share data)")
        if analysis.complexity.method_count > 20:
            evidence.append(f"High method count: {analysis.complexity.method_count}")
        
        # Generate refactoring suggestions  
        suggestions = self._generate_refactor_suggestions(analysis)
        
        return GodObjectFinding(
            class_name=analysis.name,
            file_path=analysis.file_path,
            severity=severity,
            confidence=confidence,
            god_object_score=god_score,
            cohesion_score=analysis.cohesion.overall_cohesion,
            complexity_z_score=analysis.z_score,
            role=analysis.role,
            method_count=analysis.complexity.method_count,
            line_count=analysis.complexity.line_count,
            attribute_count=analysis.complexity.attribute_count,
            lcom5=analysis.cohesion.lcom5,
            evidence=evidence,
            refactor_suggestions=suggestions
        )
    
    def _generate_refactor_suggestions(self, analysis: ClassAnalysis) -> List[str]:
        """Generate specific refactoring suggestions based on analysis."""
        suggestions = []
        
        if analysis.cohesion.lcom5 > 2.0:
            suggestions.append("Extract Class: Group methods that share attributes")
        
        if analysis.complexity.method_count > 15:
            suggestions.append("Extract Method: Break down complex methods into smaller ones")
        
        if analysis.complexity.attribute_count > 10:
            suggestions.append("Introduce Parameter Object: Group related attributes")
        
        if analysis.cohesion.behavioral_cohesion < 0.3:
            suggestions.append("Move Method: Relocate methods to more appropriate classes")
        
        if analysis.role == ClassRole.CONTROLLER and analysis.complexity.line_count > 300:
            suggestions.append("Command Pattern: Extract request handling into command objects")
        
        if analysis.role == ClassRole.GENERIC and analysis.complexity.method_count > 20:
            suggestions.append("Strategy Pattern: Extract varying algorithms into strategies")
        
        return suggestions
    
    def _fallback_detection(self) -> List[GodObjectFinding]:
        """Fallback detection using simple thresholds when not enough data for statistics."""
        findings = []
        
        for analysis in self.class_analyses:
            # Simple threshold-based detection
            is_god = (
                analysis.complexity.line_count > 500 or
                analysis.complexity.method_count > 20 or
                analysis.cohesion.lcom5 > 3.0
            )
            
            if is_god:
                god_score = min(1.0, (
                    analysis.complexity.line_count / 1000.0 +
                    analysis.complexity.method_count / 30.0 +
                    analysis.cohesion.lcom5 / 5.0
                ) / 3.0)
                
                finding = self._create_finding(analysis, god_score)
                findings.append(finding)
        
        return findings