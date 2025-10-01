"""
Circular Dependency Detector for Python Projects
Identifies circular import patterns in the analyzer module.
"""

import json
from pathlib import Path
import re
from typing import Dict, List, Set


class CircularDependencyDetector:
    """Detects circular dependencies in Python modules."""

    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.imports_graph: Dict[str, Set[str]] = {}
        self.circular_dependencies: List[List[str]] = []

    def extract_imports(self, file_path: Path) -> Set[str]:
        """Extract import statements from a Python file."""
        imports = set()

        try:
            with open(file_path, encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return imports

        # Extract relative imports
        relative_patterns = [
            r"from\s+\.+(\w+(?:\.\w+)*)",  # from .module or from ..module
            r"from\s+(\w+(?:\.\w+)*)\s+import",  # from module import
            r"import\s+(\w+(?:\.\w+)*)",  # import module
        ]

        for pattern in relative_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                # Filter for project-specific modules
                if match.startswith(("analyzer", "mcp", "policy", "integrations")):
                    imports.add(match.split(".")[0])  # Get top-level module

        return imports

    def build_import_graph(self) -> None:
        """Build a graph of module dependencies."""
        print("Building import graph...")

        # Scan all Python files
        for py_file in self.base_path.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue

            # Get module name relative to base path
            relative_path = py_file.relative_to(self.base_path)
            module_parts = list(relative_path.parts[:-1])  # Remove filename

            if module_parts:  # Only process modules (not root files)
                module_name = module_parts[0]  # Get top-level module

                if module_name not in self.imports_graph:
                    self.imports_graph[module_name] = set()

                # Extract imports from this file
                imports = self.extract_imports(py_file)
                self.imports_graph[module_name].update(imports)

        # Clean self-references
        for module in self.imports_graph:
            self.imports_graph[module].discard(module)

    def find_cycles(self) -> None:
        """Find circular dependencies using DFS."""
        print("Searching for circular dependencies...")

        visited = set()
        rec_stack = []

        def dfs(node: str, path: List[str]) -> None:
            if node in rec_stack:
                # Found a cycle
                cycle_start = rec_stack.index(node)
                cycle = rec_stack[cycle_start:] + [node]
                if len(cycle) > 1 and cycle not in self.circular_dependencies:
                    self.circular_dependencies.append(cycle)
                return

            if node in visited:
                return

            visited.add(node)
            rec_stack.append(node)

            for neighbor in self.imports_graph.get(node, []):
                dfs(neighbor, path + [node])

            rec_stack.pop()

        # Start DFS from each unvisited node
        for module in self.imports_graph:
            if module not in visited:
                dfs(module, [])

    def analyze(self) -> Dict:
        """Run the complete analysis."""
        self.build_import_graph()
        self.find_cycles()

        results = {
            "total_modules": len(self.imports_graph),
            "dependencies": {k: list(v) for k, v in self.imports_graph.items()},
            "circular_dependencies": self.circular_dependencies,
            "cycle_count": len(self.circular_dependencies),
        }

        return results

    def print_report(self, results: Dict) -> None:
        """Print a human-readable report."""
        print("\n" + "=" * 70)
        print("CIRCULAR DEPENDENCY ANALYSIS REPORT")
        print("=" * 70)

        print(f"\nTotal modules analyzed: {results['total_modules']}")
        print(f"Circular dependencies found: {results['cycle_count']}")

        if results["circular_dependencies"]:
            print("\nCircular Dependencies Detected:")
            print("-" * 40)
            for i, cycle in enumerate(results["circular_dependencies"], 1):
                cycle_str = " -> ".join(cycle)
                print(f"{i}. {cycle_str}")
        else:
            print("\n✓ No circular dependencies detected!")

        print("\nModule Import Graph:")
        print("-" * 40)
        for module, imports in results["dependencies"].items():
            if imports:  # Only show modules with dependencies
                print(f"{module}: {', '.join(imports)}")


def main():
    """Run circular dependency detection."""
    # Analyze the project
    project_root = r"C:\Users\17175\Desktop\connascence"
    detector = CircularDependencyDetector(project_root)

    print(f"Analyzing project at: {project_root}")
    results = detector.analyze()

    # Print report
    detector.print_report(results)

    # Save results to JSON
    output_file = Path(project_root) / "fixes" / "phase0" / "circular_dependencies.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nResults saved to: {output_file}")

    return results


if __name__ == "__main__":
    main()
