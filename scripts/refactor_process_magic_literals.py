#!/usr/bin/env python3
"""
Script to refactor analyzer/check_connascence.py _process_magic_literals()
from 108 LOC to ≤60 LOC.
"""

from pathlib import Path

# Path to the file
check_connascence_file = Path(__file__).parent.parent / "analyzer" / "check_connascence.py"

# Read the file
with open(check_connascence_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Helper functions to insert before _process_magic_literals()
helper_functions = '''
    def _process_formal_magic_literal(self, node, value, context_info, formal_context, severity_score):
        """
        Process magic literal with formal grammar context.

        NASA Rule 4: Function under 60 lines
        """
        # Determine severity based on score
        if severity_score < 2.0:
            return  # Skip low-severity items
        elif severity_score > 8.0:
            severity = "high"
        elif severity_score > 5.0:
            severity = "medium"
        else:
            severity = "low"

        # Generate enhanced description using formal context
        description = self._create_formal_magic_literal_description(value, formal_context, severity_score)
        recommendation = self._get_formal_magic_literal_recommendation(formal_context)

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

    def _process_legacy_magic_literal(self, node, value, context_info):
        """
        Process magic literal using legacy analysis.

        NASA Rule 4: Function under 60 lines
        """
        severity = self._determine_magic_literal_severity(value, context_info)

        # Skip very low priority items if they have contextual justification
        if severity == "informational" and context_info.get("severity_modifier") == "lower":
            return

        # Create appropriate description based on context
        description = self._create_magic_literal_description(value, context_info)

        self.violations.append(
            ConnascenceViolation(
                type="connascence_of_meaning",
                severity=severity,
                file_path=self.file_path,
                line_number=node.lineno,
                column=node.col_offset,
                description=description,
                recommendation=self._get_magic_literal_recommendation(value, context_info),
                code_snippet=self.get_code_snippet(node),
                context={
                    "literal_value": value,
                    "analysis_context": context_info,
                    "in_conditional": context_info.get("in_conditional", False),
                    "analysis_type": "legacy",
                },
            )
        )

    def _check_excessive_globals(self):
        """
        Check for excessive global variable usage.

        NASA Rule 4: Function under 60 lines
        """
        if len(self.global_vars) > 5:
            # Find a representative location (first global usage)
            for node in ast.walk(ast.parse("".join(self.source_lines))):
                if isinstance(node, ast.Global):
                    self.violations.append(
                        ConnascenceViolation(
                            type="connascence_of_identity",
                            severity="high",
                            file_path=self.file_path,
                            line_number=node.lineno,
                            column=node.col_offset,
                            description=f"Excessive global variable usage: {len(self.global_vars)} globals",
                            recommendation="Use dependency injection, configuration objects, or class attributes",
                            code_snippet=self.get_code_snippet(node),
                            context={"global_count": len(self.global_vars), "global_vars": list(self.global_vars)},
                        )
                    )
                    break

'''

# New refactored _process_magic_literals() function
new_function = '''    def _process_magic_literals(self):
        """
        Process magic literals with formal grammar context.

        Refactored to comply with NASA Rule 4 (≤60 lines per function).
        Helper functions handle formal analysis, legacy processing, and global checks.
        """
        # NASA Rule 5: Input validation assertion
        assert hasattr(self, "magic_literals"), "magic_literals must be initialized"

        for item in self.magic_literals:
            # Handle different formats: old (node, value), enhanced (node, value, context)
            if len(item) == 2:
                node, value = item
                context_info = {"in_conditional": self._is_in_conditional(node)}
                # Process with legacy method
                self._process_legacy_magic_literal(node, value, context_info)
            else:
                node, value, context_info = item
                # Check if we have formal grammar analysis context
                if context_info.get("formal_analysis") and "context" in context_info:
                    formal_context = context_info["context"]
                    severity_score = context_info.get("severity_score", 3.0)
                    # Process with formal grammar method
                    self._process_formal_magic_literal(
                        node, value, context_info, formal_context, severity_score
                    )
                else:
                    # Fallback to legacy processing
                    self._process_legacy_magic_literal(node, value, context_info)

        # Check for excessive global usage
        self._check_excessive_globals()

'''

# Find _process_magic_literals() in the file
start_marker = "    def _process_magic_literals(self):"
end_marker = "    def _is_in_conditional(self, node: ast.AST) -> bool:"

start_idx = content.find(start_marker)
end_idx = content.find(end_marker)

if start_idx == -1 or end_idx == -1:
    print("[ERROR] Could not find _process_magic_literals() function boundaries")
    exit(1)

# Create new content
new_content = (
    content[:start_idx] +
    helper_functions +
    new_function +
    content[end_idx:]
)

# Write the refactored file
with open(check_connascence_file, 'w', encoding='utf-8') as f:
    f.write(new_content)

print("[SUCCESS] Refactored _process_magic_literals() function!")
print(f"  Original: ~108 LOC")
print(f"  Refactored: ~35 LOC")
print(f"  Helper functions created: 3")
print(f"    - _process_formal_magic_literal(): ~45 LOC")
print(f"    - _process_legacy_magic_literal(): ~30 LOC")
print(f"    - _check_excessive_globals(): ~20 LOC")
print(f"  Lines saved: ~73 LOC from main function")
