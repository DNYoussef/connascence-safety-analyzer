#!/usr/bin/env python3
"""
Script to refactor analyzer/context_analyzer.py _classify_class_context()
from 82 LOC to <=60 LOC.
"""

from pathlib import Path
import sys

# Path to the file
context_analyzer_file = Path(__file__).parent.parent / "analyzer" / "context_analyzer.py"

# Read the file
with open(context_analyzer_file, encoding="utf-8") as f:
    content = f.read()

# Helper functions to insert before _classify_class_context()
helper_functions = '''
    def _score_by_file_path(self, file_path: str, scores: dict):
        """
        Score class context based on file path indicators.

        NASA Rule 4: Function under 60 lines
        """
        path_lower = file_path.lower()
        if any(term in path_lower for term in ["test", "spec"]):
            scores[ClassContext.TEST] += 3
        elif any(term in path_lower for term in ["config", "settings"]):
            scores[ClassContext.CONFIG] += 2
        elif any(term in path_lower for term in ["model", "entity", "dto"]):
            scores[ClassContext.DATA_MODEL] += 2
        elif any(term in path_lower for term in ["api", "controller", "handler", "view"]):
            scores[ClassContext.API_CONTROLLER] += 2
        elif any(term in path_lower for term in ["util", "helper", "tool"]):
            scores[ClassContext.UTILITY] += 2
        elif any(term in path_lower for term in ["db", "database", "persistence", "repository"]):
            scores[ClassContext.INFRASTRUCTURE] += 2

    def _score_by_class_name(self, class_node: ast.ClassDef, scores: dict):
        """
        Score class context based on class name patterns.

        NASA Rule 4: Function under 60 lines
        """
        class_name = class_node.name.lower()
        for context, indicators in [
            (ClassContext.CONFIG, self.config_indicators),
            (ClassContext.DATA_MODEL, self.data_model_indicators),
            (ClassContext.API_CONTROLLER, self.api_controller_indicators),
            (ClassContext.UTILITY, self.utility_indicators),
        ]:
            for pattern in indicators["name_patterns"]:
                if re.match(pattern, class_name):
                    scores[context] += 2
                    break

    def _score_by_base_classes(self, class_node: ast.ClassDef, scores: dict):
        """
        Score class context based on base class inheritance.

        NASA Rule 4: Function under 60 lines
        """
        for base in class_node.bases:
            base_name = ast.unparse(base) if hasattr(ast, "unparse") else str(base)
            for context, indicators in [
                (ClassContext.CONFIG, self.config_indicators),
                (ClassContext.DATA_MODEL, self.data_model_indicators),
                (ClassContext.API_CONTROLLER, self.api_controller_indicators),
                (ClassContext.UTILITY, self.utility_indicators),
            ]:
                if base_name in indicators["base_classes"]:
                    scores[context] += 3

    def _score_by_methods(self, class_node: ast.ClassDef, scores: dict):
        """
        Score class context based on method patterns and characteristics.

        NASA Rule 4: Function under 60 lines
        """
        methods = [node for node in class_node.body if isinstance(node, ast.FunctionDef)]

        # Method pattern analysis
        for method in methods:
            method_name = method.name.lower()
            for context, indicators in [
                (ClassContext.CONFIG, self.config_indicators),
                (ClassContext.DATA_MODEL, self.data_model_indicators),
                (ClassContext.API_CONTROLLER, self.api_controller_indicators),
                (ClassContext.UTILITY, self.utility_indicators),
            ]:
                for pattern in indicators["method_patterns"]:
                    if re.match(pattern, method_name):
                        scores[context] += 1
                        break

        # Static method ratio for utilities
        if methods:
            static_methods = len(
                [
                    m
                    for m in methods
                    if any(isinstance(d, ast.Name) and d.id == "staticmethod" for d in m.decorator_list)
                ]
            )
            static_ratio = static_methods / len(methods)
            if static_ratio >= self.utility_indicators["static_methods_ratio"]:
                scores[ClassContext.UTILITY] += 2

        # Business logic is default for substantial classes with mixed responsibilities
        if max(scores.values()) == 0 and len(methods) > 5:
            scores[ClassContext.BUSINESS_LOGIC] += 1

'''

# New refactored _classify_class_context() function
new_function = '''    def _classify_class_context(
        self, class_node: ast.ClassDef, source_lines: List[str], file_path: str
    ) -> ClassContext:
        """
        Classify the context/domain of a class using multiple indicators.

        Refactored to comply with NASA Rule 4 (<=60 lines per function).
        Helper functions handle file path, class name, base classes, and method analysis.
        """
        scores = dict.fromkeys(ClassContext, 0)

        # Score by different indicators
        self._score_by_file_path(file_path, scores)
        self._score_by_class_name(class_node, scores)
        self._score_by_base_classes(class_node, scores)
        self._score_by_methods(class_node, scores)

        # Return the highest scoring context
        best_context = max(scores.items(), key=lambda x: x[1])
        return best_context[0] if best_context[1] > 0 else ClassContext.UNKNOWN

'''

# Find _classify_class_context() in the file
start_marker = "    def _classify_class_context(\n        self, class_node: ast.ClassDef, source_lines: List[str], file_path: str\n    ) -> ClassContext:"
end_marker = "\n    def _count_methods(self, class_node: ast.ClassDef) -> int:"

start_idx = content.find(start_marker)
end_idx = content.find(end_marker)

if start_idx == -1 or end_idx == -1:
    print("[ERROR] Could not find _classify_class_context() function boundaries")
    print(f"start_idx: {start_idx}, end_idx: {end_idx}")
    sys.exit(1)

# Create new content
new_content = content[:start_idx] + helper_functions + new_function + content[end_idx:]

# Write the refactored file
with open(context_analyzer_file, "w", encoding="utf-8") as f:
    f.write(new_content)

print("[SUCCESS] Refactored _classify_class_context() function!")
print("  Original: ~82 LOC")
print("  Refactored: ~20 LOC")
print("  Helper functions created: 4")
print("    - _score_by_file_path(): ~15 LOC")
print("    - _score_by_class_name(): ~15 LOC")
print("    - _score_by_base_classes(): ~15 LOC")
print("    - _score_by_methods(): ~30 LOC")
print("  Lines saved: ~62 LOC from main function")
