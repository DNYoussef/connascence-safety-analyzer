# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2024 Connascence Safety Analyzer Contributors
"""
Architectural Analysis Module

Provides functionality for analyzing code architecture,
detecting architectural violations and dependency issues.
"""

import ast
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


@dataclass
class ModuleInfo:
    """Information about a module in the codebase."""

    name: str
    path: str
    imports: Set[str] = field(default_factory=set)
    exports: Set[str] = field(default_factory=set)
    classes: List[str] = field(default_factory=list)
    functions: List[str] = field(default_factory=list)


@dataclass
class DependencyInfo:
    """Information about module dependencies."""

    source: str
    target: str
    import_type: str  # "absolute", "relative", "from"
    line_number: int = 0


@dataclass
class ArchitecturalViolation:
    """Represents an architectural violation."""

    type: str
    severity: str
    file_path: str
    line_number: int
    description: str
    recommendation: str = ""
    details: Dict[str, Any] = field(default_factory=dict)


class ArchitecturalAnalyzer:
    """
    Analyzes code architecture for violations.

    Detects:
    - Circular dependencies
    - Layer violations
    - Improper imports
    - Module coupling issues
    """

    def __init__(self, root_path: str = "."):
        self.root_path = Path(root_path)
        self.modules: Dict[str, ModuleInfo] = {}
        self.dependencies: List[DependencyInfo] = []
        self.violations: List[ArchitecturalViolation] = []

    def analyze_directory(self, path: Optional[str] = None) -> List[ArchitecturalViolation]:
        """Analyze a directory for architectural violations."""
        target_path = Path(path) if path else self.root_path
        self.violations = []

        # Collect module information
        self._collect_modules(target_path)

        # Analyze for violations
        self._detect_circular_dependencies()
        self._detect_layer_violations()
        self._detect_coupling_issues()

        return self.violations

    def analyze_file(self, file_path: str) -> List[ArchitecturalViolation]:
        """Analyze a single file for architectural violations."""
        self.violations = []
        module_info = self._analyze_module(file_path)
        if module_info:
            self.modules[module_info.name] = module_info
            self._detect_import_violations(module_info)
        return self.violations

    def _collect_modules(self, directory: Path):
        """Recursively collect module information from a directory."""
        for py_file in directory.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            module_info = self._analyze_module(str(py_file))
            if module_info:
                self.modules[module_info.name] = module_info

    def _analyze_module(self, file_path: str) -> Optional[ModuleInfo]:
        """Analyze a Python module and extract information."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                source = f.read()

            tree = ast.parse(source)
            rel_path = os.path.relpath(file_path, self.root_path)
            module_name = rel_path.replace(os.sep, ".").replace(".py", "")

            info = ModuleInfo(name=module_name, path=file_path)

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        info.imports.add(alias.name)
                        self.dependencies.append(
                            DependencyInfo(
                                source=module_name,
                                target=alias.name,
                                import_type="absolute",
                                line_number=node.lineno,
                            )
                        )

                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        info.imports.add(node.module)
                        self.dependencies.append(
                            DependencyInfo(
                                source=module_name,
                                target=node.module,
                                import_type="from",
                                line_number=node.lineno,
                            )
                        )

                elif isinstance(node, ast.ClassDef):
                    info.classes.append(node.name)
                    info.exports.add(node.name)

                elif isinstance(node, ast.FunctionDef):
                    if not node.name.startswith("_"):
                        info.functions.append(node.name)
                        info.exports.add(node.name)

            return info

        except Exception:
            return None

    def _detect_circular_dependencies(self):
        """Detect circular dependencies in the module graph."""
        # Build adjacency list
        graph: Dict[str, Set[str]] = {}
        for dep in self.dependencies:
            if dep.source not in graph:
                graph[dep.source] = set()
            graph[dep.source].add(dep.target)

        # Find cycles using DFS
        visited = set()
        rec_stack = set()

        def dfs(node: str, path: List[str]) -> Optional[List[str]]:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in graph.get(node, []):
                if neighbor in self.modules:  # Only check internal modules
                    if neighbor not in visited:
                        cycle = dfs(neighbor, path)
                        if cycle:
                            return cycle
                    elif neighbor in rec_stack:
                        # Found cycle
                        cycle_start = path.index(neighbor)
                        return path[cycle_start:] + [neighbor]

            path.pop()
            rec_stack.remove(node)
            return None

        for module in self.modules:
            if module not in visited:
                cycle = dfs(module, [])
                if cycle:
                    self.violations.append(
                        ArchitecturalViolation(
                            type="CircularDependency",
                            severity="high",
                            file_path=self.modules[module].path,
                            line_number=0,
                            description=f"Circular dependency detected: {' -> '.join(cycle)}",
                            recommendation="Refactor to break the circular dependency",
                            details={"cycle": cycle},
                        )
                    )

    def _detect_layer_violations(self):
        """Detect layer violations (e.g., UI importing from data layer directly)."""
        # Define layer hierarchy (higher layers can import from lower)
        layers = {
            "presentation": 3,
            "application": 2,
            "domain": 1,
            "infrastructure": 0,
            "ui": 3,
            "api": 2,
            "services": 1,
            "data": 0,
        }

        for dep in self.dependencies:
            source_layer = self._get_module_layer(dep.source, layers)
            target_layer = self._get_module_layer(dep.target, layers)

            if source_layer is not None and target_layer is not None:
                if source_layer < target_layer:
                    self.violations.append(
                        ArchitecturalViolation(
                            type="LayerViolation",
                            severity="medium",
                            file_path=self.modules.get(dep.source, ModuleInfo("", "")).path or "",
                            line_number=dep.line_number,
                            description=f"Layer violation: lower layer '{dep.source}' imports from higher layer '{dep.target}'",
                            recommendation="Refactor to maintain proper layer boundaries",
                        )
                    )

    def _get_module_layer(self, module_name: str, layers: Dict[str, int]) -> Optional[int]:
        """Determine which layer a module belongs to."""
        parts = module_name.lower().split(".")
        for part in parts:
            if part in layers:
                return layers[part]
        return None

    def _detect_coupling_issues(self):
        """Detect modules with excessive coupling."""
        MAX_DEPENDENCIES = 10

        for module_name, module_info in self.modules.items():
            if len(module_info.imports) > MAX_DEPENDENCIES:
                self.violations.append(
                    ArchitecturalViolation(
                        type="HighCoupling",
                        severity="medium",
                        file_path=module_info.path,
                        line_number=0,
                        description=f"Module '{module_name}' has {len(module_info.imports)} dependencies (max: {MAX_DEPENDENCIES})",
                        recommendation="Consider reducing dependencies or splitting the module",
                        details={"dependency_count": len(module_info.imports)},
                    )
                )

    def _detect_import_violations(self, module_info: ModuleInfo):
        """Detect import-related violations in a module."""
        # Check for wildcard imports
        try:
            with open(module_info.path, "r", encoding="utf-8") as f:
                source = f.read()

            tree = ast.parse(source)
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    for alias in node.names:
                        if alias.name == "*":
                            self.violations.append(
                                ArchitecturalViolation(
                                    type="WildcardImport",
                                    severity="low",
                                    file_path=module_info.path,
                                    line_number=node.lineno,
                                    description=f"Wildcard import from '{node.module}'",
                                    recommendation="Use explicit imports instead of wildcard",
                                )
                            )
        except Exception:
            pass

    def get_dependency_graph(self) -> Dict[str, List[str]]:
        """Return the dependency graph as an adjacency list."""
        graph: Dict[str, List[str]] = {}
        for dep in self.dependencies:
            if dep.source not in graph:
                graph[dep.source] = []
            graph[dep.source].append(dep.target)
        return graph


def analyze_architecture(path: str) -> List[ArchitecturalViolation]:
    """
    Convenience function to analyze architecture.

    Args:
        path: Directory or file path to analyze

    Returns:
        List of architectural violations
    """
    analyzer = ArchitecturalAnalyzer(path)
    if os.path.isfile(path):
        return analyzer.analyze_file(path)
    return analyzer.analyze_directory()


__all__ = [
    "ArchitecturalAnalyzer",
    "ArchitecturalViolation",
    "DependencyInfo",
    "ModuleInfo",
    "analyze_architecture",
]
