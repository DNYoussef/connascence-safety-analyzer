# SPDX-License-Identifier: MIT
"""
AST Traversal Optimizer
========================

Optimized AST traversal algorithms for improved performance
in connascence analysis.
"""

import ast
from collections import defaultdict
from dataclasses import dataclass
import logging
from pathlib import Path
import sys
import time
from typing import Any, Callable, Dict, Iterator, List, Optional, Set, Union

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logger = logging.getLogger(__name__)


@dataclass
class TraversalStats:
    """Statistics for AST traversal performance."""

    nodes_visited: int = 0
    nodes_skipped: int = 0
    traversal_time_ms: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    optimizations_applied: int = 0


class OptimizedASTVisitor(ast.NodeVisitor):
    """
    Optimized AST visitor with performance enhancements:
    - Early termination conditions
    - Node type filtering
    - Cached sub-tree results
    - Pattern-based pruning
    """

    def __init__(
        self,
        target_patterns: Optional[Set[str]] = None,
        skip_patterns: Optional[Set[str]] = None,
        enable_caching: bool = True,
        max_depth: int = 100,
    ):
        """Initialize optimized visitor."""

        self.target_patterns = target_patterns or set()
        self.skip_patterns = skip_patterns or set()
        self.enable_caching = enable_caching
        self.max_depth = max_depth

        # Performance tracking
        self.stats = TraversalStats()
        self.current_depth = 0

        # Caching
        self.node_cache: Dict[str, Any] = {}
        self.subtree_hashes: Dict[int, str] = {}

        # Optimization flags
        self.early_termination_enabled = True
        self.pattern_pruning_enabled = True
        self.depth_limiting_enabled = True

    def visit(self, node: ast.AST) -> Any:
        """Optimized visit method with performance enhancements."""

        start_time = time.time()

        # Depth limiting
        if self.depth_limiting_enabled and self.current_depth > self.max_depth:
            self.stats.nodes_skipped += 1
            return None

        # Pattern-based pruning
        if self.pattern_pruning_enabled and self._should_skip_node(node):
            self.stats.nodes_skipped += 1
            return None

        # Check cache if enabled
        if self.enable_caching:
            cache_key = self._get_node_cache_key(node)
            if cache_key in self.node_cache:
                self.stats.cache_hits += 1
                return self.node_cache[cache_key]
            else:
                self.stats.cache_misses += 1

        # Track depth
        self.current_depth += 1
        self.stats.nodes_visited += 1

        try:
            # Standard AST visit
            result = super().visit(node)

            # Cache result if enabled
            if self.enable_caching and cache_key:
                self.node_cache[cache_key] = result

            return result

        finally:
            self.current_depth -= 1
            self.stats.traversal_time_ms += (time.time() - start_time) * 1000

    def visit_optimized(self, node: ast.AST, target_types: Set[type]) -> Iterator[ast.AST]:
        """
        Optimized traversal that only yields nodes of target types.
        Much faster than full traversal when looking for specific patterns.
        """

        if type(node) in target_types:
            yield node

        # Only traverse children if they might contain target types
        if self._subtree_might_contain_targets(node, target_types):
            for child in ast.iter_child_nodes(node):
                yield from self.visit_optimized(child, target_types)

    def find_patterns_fast(
        self, node: ast.AST, patterns: Dict[str, Callable[[ast.AST], bool]]
    ) -> Dict[str, List[ast.AST]]:
        """
        Fast pattern matching using optimized traversal.
        Returns all nodes matching each pattern.
        """

        results = defaultdict(list)

        # Group patterns by node types they target for optimization
        patterns_by_type = self._group_patterns_by_type(patterns)

        # Use targeted traversal for each node type
        for node_type, type_patterns in patterns_by_type.items():
            for found_node in self.visit_optimized(node, {node_type}):
                for pattern_name, pattern_func in type_patterns.items():
                    try:
                        if pattern_func(found_node):
                            results[pattern_name].append(found_node)
                    except Exception as e:
                        logger.debug(f"Pattern {pattern_name} failed on node: {e}")

        return dict(results)

    def get_statistics(self) -> TraversalStats:
        """Get traversal performance statistics."""
        return self.stats

    def reset_statistics(self):
        """Reset performance statistics."""
        self.stats = TraversalStats()
        self.node_cache.clear()
        self.subtree_hashes.clear()

    # Private optimization methods

    def _should_skip_node(self, node: ast.AST) -> bool:
        """Check if node should be skipped based on patterns."""

        node_type = type(node).__name__

        # Skip if node type is in skip patterns
        if node_type in self.skip_patterns:
            return True

        # Skip if we have target patterns and this node type isn't targeted
        if self.target_patterns and node_type not in self.target_patterns:
            # But don't skip if this node might contain target patterns
            return not self._subtree_might_contain_targets(node, self.target_patterns)

        return False

    def _subtree_might_contain_targets(self, node: ast.AST, targets: Union[Set[str], Set[type]]) -> bool:
        """Check if subtree might contain target node types."""

        # Convert type objects to names if needed
        target_names = {t.__name__ for t in targets} if targets and isinstance(next(iter(targets)), type) else targets

        # Quick heuristics based on node type
        node_type = type(node).__name__

        # These node types commonly contain other statement/expression types
        container_types = {
            "Module",
            "FunctionDef",
            "AsyncFunctionDef",
            "ClassDef",
            "If",
            "For",
            "AsyncFor",
            "While",
            "With",
            "AsyncWith",
            "Try",
            "ExceptHandler",
            "Block",
        }

        # Expression containers
        expr_containers = {
            "Call",
            "Attribute",
            "BinOp",
            "UnaryOp",
            "Compare",
            "ListComp",
            "SetComp",
            "DictComp",
            "GeneratorExp",
        }

        if node_type in container_types:
            return True  # Always traverse structural containers

        if node_type in expr_containers and any(t in target_names for t in ["Call", "Name", "Attribute", "Constant"]):
            return True  # Expression containers might have target expressions

        # If looking for specific types, check if this node could contain them
        if "FunctionDef" in target_names and node_type in {"Module", "ClassDef"}:
            return True

        if "Name" in target_names:  # Names can be anywhere
            return True

        return False

    def _get_node_cache_key(self, node: ast.AST) -> Optional[str]:
        """Generate cache key for node."""

        try:
            # Create key based on node type, location, and key attributes
            key_parts = [type(node).__name__]

            # Add location if available
            if hasattr(node, "lineno"):
                key_parts.append(f"L{node.lineno}")
            if hasattr(node, "col_offset"):
                key_parts.append(f"C{node.col_offset}")

            # Add key attributes based on node type
            if isinstance(node, ast.Name):
                key_parts.append(f"id:{node.id}")
            elif isinstance(node, ast.Attribute):
                key_parts.append(f"attr:{node.attr}")
            elif isinstance(node, ast.FunctionDef):
                key_parts.append(f"name:{node.name}")
            elif isinstance(node, ast.ClassDef):
                key_parts.append(f"name:{node.name}")

            return ":".join(key_parts)

        except Exception:
            return None

    def _group_patterns_by_type(
        self, patterns: Dict[str, Callable[[ast.AST], bool]]
    ) -> Dict[type, Dict[str, Callable]]:
        """Group patterns by the AST node types they target."""

        # This is a simplified grouping - in practice, you'd analyze the patterns
        # to determine which node types they actually check

        type_groups = defaultdict(dict)

        for pattern_name, pattern_func in patterns.items():
            # Heuristic: inspect pattern name to guess target types
            if "function" in pattern_name.lower():
                type_groups[ast.FunctionDef][pattern_name] = pattern_func
            elif "class" in pattern_name.lower():
                type_groups[ast.ClassDef][pattern_name] = pattern_func
            elif "call" in pattern_name.lower():
                type_groups[ast.Call][pattern_name] = pattern_func
            elif "name" in pattern_name.lower() or "variable" in pattern_name.lower():
                type_groups[ast.Name][pattern_name] = pattern_func
            else:
                # Default: could be any expression or statement
                for node_type in [ast.FunctionDef, ast.ClassDef, ast.Call, ast.Name, ast.Attribute]:
                    type_groups[node_type][pattern_name] = pattern_func

        return dict(type_groups)


class ConnascencePatternOptimizer:
    """
    Optimized pattern detection for connascence analysis.
    Uses fast traversal algorithms and pattern-specific optimizations.
    """

    def __init__(self):
        """Initialize pattern optimizer."""

        self.visitor = OptimizedASTVisitor()
        self.pattern_cache = {}

        # Pre-compiled patterns for common connascence types
        self.connascence_patterns = self._build_connascence_patterns()

    def analyze_connascence_fast(self, ast_tree: ast.AST) -> Dict[str, List[Dict[str, Any]]]:
        """
        Fast connascence analysis using optimized traversal.

        Args:
            ast_tree: Parsed AST tree

        Returns:
            Dictionary of connascence violations by type
        """

        start_time = time.time()

        # Reset visitor statistics
        self.visitor.reset_statistics()

        # Use fast pattern matching
        pattern_matches = self.visitor.find_patterns_fast(ast_tree, self.connascence_patterns)

        # Convert matches to violation format
        violations = {}
        for connascence_type, matches in pattern_matches.items():
            violations[connascence_type] = [self._create_violation(match, connascence_type) for match in matches]

        analysis_time = time.time() - start_time
        stats = self.visitor.get_statistics()

        logger.debug(
            f"Fast connascence analysis: {analysis_time*1000:.2f}ms, "
            f"{stats.nodes_visited} nodes visited, {stats.nodes_skipped} skipped"
        )

        return violations

    def find_god_objects_fast(self, ast_tree: ast.AST, method_threshold: int = 20) -> List[Dict[str, Any]]:
        """Fast god object detection."""

        god_objects = []

        # Find all class definitions
        for class_node in self.visitor.visit_optimized(ast_tree, {ast.ClassDef}):
            method_count = 0

            # Count methods in class
            for node in ast.walk(class_node):
                if isinstance(node, ast.FunctionDef) and node != class_node:
                    method_count += 1

            if method_count >= method_threshold:
                god_objects.append(
                    {
                        "type": "god_object",
                        "class_name": class_node.name,
                        "method_count": method_count,
                        "line_number": getattr(class_node, "lineno", 0),
                        "severity": "high" if method_count > 30 else "medium",
                    }
                )

        return god_objects

    def detect_parameter_coupling_fast(self, ast_tree: ast.AST, param_threshold: int = 5) -> List[Dict[str, Any]]:
        """Fast parameter coupling detection."""

        violations = []

        # Find functions with many parameters
        for func_node in self.visitor.visit_optimized(ast_tree, {ast.FunctionDef, ast.AsyncFunctionDef}):
            param_count = len(func_node.args.args)

            if param_count >= param_threshold:
                violations.append(
                    {
                        "type": "parameter_coupling",
                        "function_name": func_node.name,
                        "parameter_count": param_count,
                        "line_number": getattr(func_node, "lineno", 0),
                        "severity": "high" if param_count > 8 else "medium",
                    }
                )

        return violations

    def _build_connascence_patterns(self) -> Dict[str, Callable[[ast.AST], bool]]:
        """Build pattern functions for connascence detection."""

        patterns = {}

        # Connascence of Literal (CoL) - Magic numbers/strings
        def detect_magic_literals(node: ast.AST) -> bool:
            if isinstance(node, ast.Constant):
                value = node.value
                # Check for common magic values
                if isinstance(value, (int, float)):
                    return value not in {0, 1, -1, 2} and not (10 <= value <= 100 and value % 10 == 0)
                elif isinstance(value, str):
                    return len(value) > 3 and not value.isspace()
            return False

        patterns["connascence_of_literal"] = detect_magic_literals

        # Connascence of Name (CoN) - Variable naming dependencies
        def detect_name_coupling(node: ast.AST) -> bool:
            if isinstance(node, ast.Name):
                # Look for variables that might be tightly coupled by name
                return "temp" in node.id.lower() or "tmp" in node.id.lower() or node.id.lower().startswith("var")
            return False

        patterns["connascence_of_name"] = detect_name_coupling

        # Connascence of Position (CoP) - Parameter order dependencies
        def detect_position_coupling(node: ast.AST) -> bool:
            if isinstance(node, ast.Call):
                # Functions with many positional arguments
                positional_args = len([arg for arg in node.args if not isinstance(arg, ast.Starred)])
                return positional_args >= 4
            return False

        patterns["connascence_of_position"] = detect_position_coupling

        # Connascence of Algorithm (CoA) - Algorithmic dependencies
        def detect_algorithm_coupling(node: ast.AST) -> bool:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Look for functions that might have algorithmic coupling
                # This is a simplified heuristic
                body_lines = len(node.body)
                return body_lines > 50  # Long functions often have algorithmic coupling
            return False

        patterns["connascence_of_algorithm"] = detect_algorithm_coupling

        return patterns

    def _create_violation(self, node: ast.AST, connascence_type: str) -> Dict[str, Any]:
        """Create violation dictionary from AST node."""

        return {
            "type": connascence_type,
            "line_number": getattr(node, "lineno", 0),
            "column_number": getattr(node, "col_offset", 0),
            "severity": self._determine_severity(node, connascence_type),
            "description": self._generate_description(node, connascence_type),
            "node_type": type(node).__name__,
        }

    def _determine_severity(self, node: ast.AST, connascence_type: str) -> str:
        """Determine severity of connascence violation."""

        # Simplified severity mapping
        severity_map = {
            "connascence_of_literal": "medium",
            "connascence_of_name": "low",
            "connascence_of_position": "high",
            "connascence_of_algorithm": "high",
        }

        return severity_map.get(connascence_type, "medium")

    def _generate_description(self, node: ast.AST, connascence_type: str) -> str:
        """Generate human-readable description of violation."""

        descriptions = {
            "connascence_of_literal": f"Magic literal detected: {getattr(node, 'value', 'unknown')}",
            "connascence_of_name": f"Name coupling detected: {getattr(node, 'id', 'unknown')}",
            "connascence_of_position": "Position coupling detected in function call",
            "connascence_of_algorithm": f"Algorithm coupling detected in function: {getattr(node, 'name', 'unknown')}",
        }

        return descriptions.get(connascence_type, f"Connascence violation: {connascence_type}")


class PerformanceProfiler:
    """Profile AST traversal performance for optimization."""

    def __init__(self):
        """Initialize profiler."""
        self.profiles = {}
        self.active_profiles = {}

    def start_profile(self, profile_name: str):
        """Start profiling a traversal operation."""
        self.active_profiles[profile_name] = {
            "start_time": time.time(),
            "start_memory": self._get_memory_usage(),
            "nodes_visited": 0,
            "cache_operations": 0,
        }

    def end_profile(self, profile_name: str) -> Dict[str, Any]:
        """End profiling and return results."""

        if profile_name not in self.active_profiles:
            return {}

        profile = self.active_profiles.pop(profile_name)

        end_time = time.time()
        end_memory = self._get_memory_usage()

        result = {
            "duration_ms": (end_time - profile["start_time"]) * 1000,
            "memory_delta_mb": (end_memory - profile["start_memory"]) / (1024 * 1024),
            "nodes_visited": profile["nodes_visited"],
            "cache_operations": profile["cache_operations"],
            "nodes_per_second": profile["nodes_visited"] / max((end_time - profile["start_time"]), 0.001),
        }

        self.profiles[profile_name] = result
        return result

    def get_profile_summary(self) -> Dict[str, Any]:
        """Get summary of all profiles."""

        if not self.profiles:
            return {}

        durations = [p["duration_ms"] for p in self.profiles.values()]
        memory_deltas = [p["memory_delta_mb"] for p in self.profiles.values()]

        return {
            "total_profiles": len(self.profiles),
            "avg_duration_ms": sum(durations) / len(durations),
            "max_duration_ms": max(durations),
            "avg_memory_delta_mb": sum(memory_deltas) / len(memory_deltas),
            "max_memory_delta_mb": max(memory_deltas),
            "detailed_profiles": self.profiles,
        }

    def _get_memory_usage(self) -> int:
        """Get current memory usage in bytes."""

        try:
            import psutil

            process = psutil.Process()
            return process.memory_info().rss
        except ImportError:
            import resource

            return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
        except Exception:
            return 0


# Global instances for easy access
ast_optimizer = ConnascencePatternOptimizer()
performance_profiler = PerformanceProfiler()


def optimize_ast_analysis(ast_tree: ast.AST, target_patterns: Optional[Set[str]] = None) -> Dict[str, Any]:
    """
    Convenience function for optimized AST analysis.

    Args:
        ast_tree: Parsed AST tree
        target_patterns: Optional set of patterns to focus on

    Returns:
        Analysis results with performance metrics
    """

    performance_profiler.start_profile("ast_analysis")

    try:
        # Use optimized connascence analysis
        violations = ast_optimizer.analyze_connascence_fast(ast_tree)

        # Add god object detection
        god_objects = ast_optimizer.find_god_objects_fast(ast_tree)
        violations["god_objects"] = god_objects

        # Add parameter coupling detection
        param_coupling = ast_optimizer.detect_parameter_coupling_fast(ast_tree)
        violations["parameter_coupling"] = param_coupling

        return {
            "violations": violations,
            "total_violations": sum(len(v) for v in violations.values()),
            "performance_optimized": True,
        }

    finally:
        performance_stats = performance_profiler.end_profile("ast_analysis")
        logger.debug(f"AST analysis performance: {performance_stats}")


def get_optimization_statistics() -> Dict[str, Any]:
    """Get AST optimization performance statistics."""

    visitor_stats = ast_optimizer.visitor.get_statistics()
    profiler_summary = performance_profiler.get_profile_summary()

    return {
        "traversal_stats": {
            "nodes_visited": visitor_stats.nodes_visited,
            "nodes_skipped": visitor_stats.nodes_skipped,
            "traversal_time_ms": visitor_stats.traversal_time_ms,
            "cache_hits": visitor_stats.cache_hits,
            "cache_misses": visitor_stats.cache_misses,
            "cache_hit_rate": (visitor_stats.cache_hits / max(visitor_stats.cache_hits + visitor_stats.cache_misses, 1))
            * 100,
        },
        "profiler_summary": profiler_summary,
    }
