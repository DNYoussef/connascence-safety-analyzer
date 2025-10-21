# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2024 Connascence Safety Analyzer Contributors
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

"""
AST-Safe Refactoring Engine

Provides refactoring operations that guarantee syntactic correctness by
working directly with AST structures and validating results through grammar.
Integrates with Refactoring.Guru techniques for systematic code improvements.
"""

from dataclasses import dataclass
from enum import Enum
import re
from typing import Any, Dict, List, Optional

from .backends.tree_sitter_backend import LanguageSupport, NodeInfo, TreeSitterBackend
from .overlay_manager import OverlayManager


class RefactoringTechnique(Enum):
    """Canonical refactoring techniques from Refactoring.Guru."""

    # Composing Methods
    EXTRACT_METHOD = "extract_method"
    INLINE_METHOD = "inline_method"
    EXTRACT_VARIABLE = "extract_variable"
    INLINE_VARIABLE = "inline_variable"
    REPLACE_TEMP_WITH_QUERY = "replace_temp_with_query"

    # Moving Features Between Objects
    MOVE_METHOD = "move_method"
    MOVE_FIELD = "move_field"
    EXTRACT_CLASS = "extract_class"
    INLINE_CLASS = "inline_class"

    # Organizing Data
    REPLACE_MAGIC_NUMBER_WITH_SYMBOLIC_CONSTANT = "replace_magic_number"
    ENCAPSULATE_FIELD = "encapsulate_field"
    REPLACE_TYPE_CODE_WITH_CLASS = "replace_type_code_with_class"

    # Simplifying Conditional Expressions
    DECOMPOSE_CONDITIONAL = "decompose_conditional"
    CONSOLIDATE_CONDITIONAL_EXPRESSION = "consolidate_conditional"
    REPLACE_CONDITIONAL_WITH_POLYMORPHISM = "replace_conditional_with_polymorphism"

    # Simplifying Method Calls
    RENAME_METHOD = "rename_method"
    SEPARATE_QUERY_FROM_MODIFIER = "separate_query_from_modifier"
    PARAMETERIZE_METHOD = "parameterize_method"
    INTRODUCE_PARAMETER_OBJECT = "introduce_parameter_object"
    PRESERVE_WHOLE_OBJECT = "preserve_whole_object"

    # Dealing with Generalization
    PULL_UP_METHOD = "pull_up_method"
    PUSH_DOWN_METHOD = "push_down_method"
    EXTRACT_SUPERCLASS = "extract_superclass"
    SUBSTITUTE_ALGORITHM = "substitute_algorithm"

    # General Safety/Safety Specific
    INTRODUCE_ASSERTION = "introduce_assertion"
    REPLACE_RECURSION_WITH_ITERATION = "replace_recursion_with_iteration"
    REPLACE_CONSTRUCTOR_WITH_FACTORY = "replace_constructor_with_factory"


@dataclass
class RefactoringCandidate:
    """A candidate location for refactoring."""

    technique: RefactoringTechnique
    file_path: str
    start_line: int
    end_line: int
    description: str
    rationale: str
    estimated_effort: str  # "low", "medium", "high"
    safety_impact: str  # "none", "low", "medium", "high"
    connascence_improvement: str  # CoM -> CoN, etc.
    ast_nodes: List[NodeInfo] = None

    def __post_init__(self):
        if self.ast_nodes is None:
            self.ast_nodes = []


@dataclass
class RefactoringResult:
    """Result of applying a refactoring."""

    success: bool
    technique: RefactoringTechnique
    original_code: str
    refactored_code: str
    changes_applied: List[str] = None
    validation_errors: List[str] = None
    warnings: List[str] = None

    def __post_init__(self):
        if self.changes_applied is None:
            self.changes_applied = []
        if self.validation_errors is None:
            self.validation_errors = []
        if self.warnings is None:
            self.warnings = []


class ASTSafeRefactoring:
    """AST-safe refactoring engine with grammar validation."""

    def __init__(self, backend: TreeSitterBackend, overlay_manager: OverlayManager):
        self.backend = backend
        self.overlay_manager = overlay_manager
        self._technique_handlers = {}

        # Initialize technique handlers
        self._initialize_handlers()

    def find_refactoring_opportunities(
        self, code: str, language: LanguageSupport, target_connascence: Optional[List[str]] = None
    ) -> List[RefactoringCandidate]:
        """Find opportunities for refactoring in code."""
        parse_result = self.backend.parse(code, language)
        if not parse_result.success:
            return []

        opportunities = []

        # Extract functions for analysis
        functions = self.backend.extract_functions(parse_result.ast, language)

        # Find magic number opportunities
        magic_candidates = self._find_magic_number_candidates(code, functions)
        opportunities.extend(magic_candidates)

        # Find long parameter list opportunities
        param_candidates = self._find_parameter_object_candidates(functions)
        opportunities.extend(param_candidates)

        # Find large function opportunities
        large_function_candidates = self._find_extract_method_candidates(functions)
        opportunities.extend(large_function_candidates)

        # Find algorithm duplication opportunities
        duplication_candidates = self._find_algorithm_duplication_candidates(functions, code)
        opportunities.extend(duplication_candidates)

        # Find General Safety-specific opportunities
        nasa_candidates = self._find_nasa_safety_opportunities(parse_result.ast, code, language)
        opportunities.extend(nasa_candidates)

        # Filter by target connascence types if specified
        if target_connascence:
            opportunities = [
                opp for opp in opportunities if any(conn in opp.connascence_improvement for conn in target_connascence)
            ]

        return opportunities

    def apply_refactoring(
        self, candidate: RefactoringCandidate, code: str, language: LanguageSupport, validate_safety: bool = True
    ) -> RefactoringResult:
        """Apply a refactoring technique to code."""
        if candidate.technique not in self._technique_handlers:
            return RefactoringResult(
                success=False,
                technique=candidate.technique,
                original_code=code,
                refactored_code=code,
                validation_errors=[f"Technique {candidate.technique.value} not implemented"],
            )

        # Apply the refactoring
        handler = self._technique_handlers[candidate.technique]
        try:
            refactored_code = handler(code, candidate, language)
        except Exception as e:
            return RefactoringResult(
                success=False,
                technique=candidate.technique,
                original_code=code,
                refactored_code=code,
                validation_errors=[f"Refactoring failed: {e!s}"],
            )

        # Validate the result
        validation_result = self._validate_refactoring_result(code, refactored_code, language, validate_safety)

        return RefactoringResult(
            success=validation_result["success"],
            technique=candidate.technique,
            original_code=code,
            refactored_code=refactored_code if validation_result["success"] else code,
            changes_applied=validation_result.get("changes", []),
            validation_errors=validation_result.get("errors", []),
            warnings=validation_result.get("warnings", []),
        )

    def preview_refactoring(self, candidate: RefactoringCandidate, code: str, language: LanguageSupport) -> str:
        """Generate a preview of what the refactoring would look like."""
        # Apply refactoring without validation for preview
        if candidate.technique not in self._technique_handlers:
            return code

        handler = self._technique_handlers[candidate.technique]
        try:
            return handler(code, candidate, language)
        except Exception:
            return code

    def batch_apply_refactorings(
        self, candidates: List[RefactoringCandidate], code: str, language: LanguageSupport
    ) -> RefactoringResult:
        """Apply multiple refactorings in dependency order."""
        current_code = code
        all_changes = []
        all_warnings = []

        # Sort candidates by dependency and safety impact
        sorted_candidates = self._sort_candidates_by_dependency(candidates)

        for candidate in sorted_candidates:
            result = self.apply_refactoring(candidate, current_code, language)

            if result.success:
                current_code = result.refactored_code
                all_changes.extend(result.changes_applied)
                all_warnings.extend(result.warnings)
            else:
                # Stop on first failure to maintain consistency
                return RefactoringResult(
                    success=False,
                    technique=candidate.technique,
                    original_code=code,
                    refactored_code=current_code,
                    changes_applied=all_changes,
                    validation_errors=result.validation_errors,
                    warnings=all_warnings,
                )

        return RefactoringResult(
            success=True,
            technique=RefactoringTechnique.EXTRACT_METHOD,  # Representative
            original_code=code,
            refactored_code=current_code,
            changes_applied=all_changes,
            warnings=all_warnings,
        )

    def _initialize_handlers(self):
        """Initialize refactoring technique handlers."""
        self._technique_handlers = {
            RefactoringTechnique.REPLACE_MAGIC_NUMBER_WITH_SYMBOLIC_CONSTANT: self._handle_replace_magic_number,
            RefactoringTechnique.EXTRACT_METHOD: self._handle_extract_method,
            RefactoringTechnique.INTRODUCE_PARAMETER_OBJECT: self._handle_introduce_parameter_object,
            RefactoringTechnique.SUBSTITUTE_ALGORITHM: self._handle_substitute_algorithm,
            RefactoringTechnique.INTRODUCE_ASSERTION: self._handle_introduce_assertion,
            RefactoringTechnique.REPLACE_RECURSION_WITH_ITERATION: self._handle_replace_recursion_with_iteration,
        }

    def _find_magic_number_candidates(self, code: str, functions: List[Dict]) -> List[RefactoringCandidate]:
        """Find magic number refactoring opportunities."""
        candidates = []

        # Look for numeric literals that appear multiple times
        numeric_pattern = r"\b(\d+(?:\.\d+)?)\b"
        matches = re.finditer(numeric_pattern, code)

        number_locations = {}
        for match in matches:
            number = match.group(1)
            # Skip common numbers that are rarely magic
            if number in ["0", "1", "2", "10", "100"]:
                continue

            line_num = code[: match.start()].count("\n") + 1
            if number not in number_locations:
                number_locations[number] = []
            number_locations[number].append(line_num)

        # Create candidates for numbers that appear multiple times
        for number, locations in number_locations.items():
            if len(locations) >= 2:
                candidates.append(
                    RefactoringCandidate(
                        technique=RefactoringTechnique.REPLACE_MAGIC_NUMBER_WITH_SYMBOLIC_CONSTANT,
                        file_path="current_file",
                        start_line=min(locations),
                        end_line=max(locations),
                        description=f"Replace magic number {number} with named constant",
                        rationale=f"Number {number} appears {len(locations)} times, should be a named constant",
                        estimated_effort="low",
                        safety_impact="low",
                        connascence_improvement="CoM -> CoN",
                    )
                )

        return candidates

    def _find_parameter_object_candidates(self, functions: List[Dict]) -> List[RefactoringCandidate]:
        """Find opportunities to introduce parameter objects."""
        candidates = []

        for func in functions:
            # This is a simplified check - real implementation would analyze parameter patterns
            param_count = len(func.get("parameters", []))

            if param_count >= 4:  # General Safety/connascence threshold
                candidates.append(
                    RefactoringCandidate(
                        technique=RefactoringTechnique.INTRODUCE_PARAMETER_OBJECT,
                        file_path="current_file",
                        start_line=func.get("line_start", 1),
                        end_line=func.get("line_end", 1),
                        description=f"Introduce parameter object for {func['name']}",
                        rationale=f"Function {func['name']} has {param_count} parameters",
                        estimated_effort="medium",
                        safety_impact="low",
                        connascence_improvement="CoP -> CoN",
                    )
                )

        return candidates

    def _find_extract_method_candidates(self, functions: List[Dict]) -> List[RefactoringCandidate]:
        """Find opportunities to extract methods from large functions."""
        candidates = []

        for func in functions:
            if func.get("body_lines", 0) > 60:  # General Safety Rule 4
                candidates.append(
                    RefactoringCandidate(
                        technique=RefactoringTechnique.EXTRACT_METHOD,
                        file_path="current_file",
                        start_line=func.get("line_start", 1),
                        end_line=func.get("line_end", 1),
                        description=f"Extract methods from large function {func['name']}",
                        rationale=f"Function {func['name']} has {func['body_lines']} lines, exceeds General Safety Rule 4 limit",
                        estimated_effort="high",
                        safety_impact="medium",
                        connascence_improvement="CoA -> CoN",
                    )
                )

        return candidates

    def _find_algorithm_duplication_candidates(self, functions: List[Dict], code: str) -> List[RefactoringCandidate]:
        """Find duplicated algorithm patterns."""
        candidates = []

        # This is a simplified implementation
        # Real implementation would use AST similarity analysis

        # Look for similar function patterns (basic heuristic)
        function_patterns = {}
        for func in functions:
            # Create a simple pattern based on function structure
            pattern = self._create_function_pattern(func)
            if pattern not in function_patterns:
                function_patterns[pattern] = []
            function_patterns[pattern].append(func)

        # Find patterns with multiple instances
        for pattern, funcs in function_patterns.items():
            if len(funcs) >= 2:
                candidates.append(
                    RefactoringCandidate(
                        technique=RefactoringTechnique.SUBSTITUTE_ALGORITHM,
                        file_path="current_file",
                        start_line=min(f.get("line_start", 1) for f in funcs),
                        end_line=max(f.get("line_end", 1) for f in funcs),
                        description=f"Extract common algorithm from {len(funcs)} similar functions",
                        rationale=f"Functions {[f['name'] for f in funcs]} have similar patterns",
                        estimated_effort="medium",
                        safety_impact="medium",
                        connascence_improvement="CoA -> CoN",
                    )
                )

        return candidates

    def _find_nasa_safety_opportunities(self, ast, code: str, language: LanguageSupport) -> List[RefactoringCandidate]:
        """Find General Safety safety-specific refactoring opportunities."""
        candidates = []

        # Look for recursion that could be converted to iteration
        if language == LanguageSupport.C:
            # Find recursive calls
            functions = self.backend.extract_functions(ast, language)
            for func in functions:
                if self._contains_recursion(func, code):
                    candidates.append(
                        RefactoringCandidate(
                            technique=RefactoringTechnique.REPLACE_RECURSION_WITH_ITERATION,
                            file_path="current_file",
                            start_line=func.get("line_start", 1),
                            end_line=func.get("line_end", 1),
                            description=f"Replace recursion in {func['name']} with iteration",
                            rationale="General Safety Rule 1: Avoid recursion in safety-critical code",
                            estimated_effort="high",
                            safety_impact="high",
                            connascence_improvement="CoE -> CoN",
                        )
                    )

        # Look for assertion opportunities
        for func in functions:
            if self._needs_more_assertions(func, code):
                candidates.append(
                    RefactoringCandidate(
                        technique=RefactoringTechnique.INTRODUCE_ASSERTION,
                        file_path="current_file",
                        start_line=func.get("line_start", 1),
                        end_line=func.get("line_end", 1),
                        description=f"Add runtime assertions to {func['name']}",
                        rationale="General Safety Rule 5: Use at least 2 runtime assertions per function",
                        estimated_effort="low",
                        safety_impact="high",
                        connascence_improvement="CoE -> Explicit Contracts",
                    )
                )

        return candidates

    def _handle_replace_magic_number(
        self, code: str, candidate: RefactoringCandidate, language: LanguageSupport
    ) -> str:
        """Handle replace magic number with symbolic constant refactoring."""
        # Extract the magic number from the candidate description
        match = re.search(r"Replace magic number (\d+(?:\.\d+)?)", candidate.description)
        if not match:
            return code

        magic_number = match.group(1)

        # Generate a constant name
        constant_name = f"CONSTANT_{magic_number.replace('.', '_')}"

        # Add constant declaration at the top
        if language == LanguageSupport.C:
            constant_declaration = f"#define {constant_name} {magic_number}\n"
        elif language == LanguageSupport.PYTHON:
            constant_declaration = f"{constant_name} = {magic_number}\n"
        else:
            constant_declaration = f"const {constant_name} = {magic_number};\n"

        # Replace all occurrences of the magic number
        # Use word boundaries to avoid partial replacements
        pattern = r"\b" + re.escape(magic_number) + r"\b"
        refactored_code = re.sub(pattern, constant_name, code)

        # Add the constant declaration
        if language == LanguageSupport.C:
            # Add after includes or at the beginning
            if "#include" in refactored_code:
                last_include = refactored_code.rfind("#include")
                end_of_line = refactored_code.find("\n", last_include)
                refactored_code = (
                    refactored_code[: end_of_line + 1] + constant_declaration + refactored_code[end_of_line + 1 :]
                )
            else:
                refactored_code = constant_declaration + refactored_code
        else:
            # Python and others - add at the beginning
            refactored_code = constant_declaration + "\n" + refactored_code

        return refactored_code

    def _handle_extract_method(self, code: str, candidate: RefactoringCandidate, language: LanguageSupport) -> str:
        """Handle extract method refactoring."""
        # This is a simplified implementation
        # Real implementation would analyze AST to find good extraction points

        lines = code.split("\n")
        start_idx = candidate.start_line - 1
        end_idx = candidate.end_line

        if start_idx >= len(lines) or end_idx >= len(lines):
            return code

        # Find a good extraction point (middle of the function)
        function_lines = lines[start_idx:end_idx]
        if len(function_lines) < 10:
            return code  # Too small to extract

        # Extract middle portion
        extract_start = len(function_lines) // 3
        extract_end = 2 * len(function_lines) // 3
        extracted_lines = function_lines[extract_start:extract_end]

        # Generate new method name
        new_method_name = "extracted_method"

        # Create the extracted method
        if language == LanguageSupport.PYTHON:
            extracted_method = f"def {new_method_name}(self):\n"
            for line in extracted_lines:
                extracted_method += f"    {line}\n"
            extracted_method += "\n"
        elif language == LanguageSupport.C:
            extracted_method = f"void {new_method_name}() {{\n"
            for line in extracted_lines:
                extracted_method += f"    {line}\n"
            extracted_method += "}\n\n"
        else:
            return code  # Not implemented for this language

        # Replace extracted lines with method call
        if language == LanguageSupport.PYTHON:
            call_line = f"    self.{new_method_name}()"
        elif language == LanguageSupport.C:
            call_line = f"    {new_method_name}();"

        # Reconstruct the code
        new_lines = [*lines[: start_idx + extract_start], call_line, *lines[start_idx + extract_end :]]

        # Add the extracted method before the original function
        method_lines = extracted_method.split("\n")
        new_lines = lines[:start_idx] + method_lines + [""] + new_lines[start_idx:]

        return "\n".join(new_lines)

    def _handle_introduce_parameter_object(
        self, code: str, candidate: RefactoringCandidate, language: LanguageSupport
    ) -> str:
        """Handle introduce parameter object refactoring."""
        # This is a simplified implementation
        # Real implementation would analyze parameter usage patterns

        if language == LanguageSupport.PYTHON:
            # Add a simple dataclass for parameters
            parameter_class = """@dataclass
class FunctionParameters:
    param1: Any
    param2: Any
    param3: Any
    param4: Any

"""
            return parameter_class + code

        return code  # Not fully implemented for other languages

    def _handle_substitute_algorithm(
        self, code: str, candidate: RefactoringCandidate, language: LanguageSupport
    ) -> str:
        """Handle substitute algorithm refactoring."""
        # This would implement algorithm substitution
        # For now, just return original code
        return code

    def _handle_introduce_assertion(self, code: str, candidate: RefactoringCandidate, language: LanguageSupport) -> str:
        """Handle introduce assertion refactoring."""
        lines = code.split("\n")
        start_idx = candidate.start_line - 1

        # Find function definition
        for i in range(start_idx, min(len(lines), start_idx + 10)):
            if "def " in lines[i] or "function" in lines[i]:
                # Add assertions after function definition
                if language == LanguageSupport.PYTHON:
                    assertion = "    assert param is not None, 'Parameter must not be None'"
                elif language == LanguageSupport.C:
                    assertion = "    assert(param != NULL);"
                else:
                    assertion = "    // TODO: Add assertion here"

                lines.insert(i + 1, assertion)
                break

        return "\n".join(lines)

    def _handle_replace_recursion_with_iteration(
        self, code: str, candidate: RefactoringCandidate, language: LanguageSupport
    ) -> str:
        """Handle replace recursion with iteration refactoring."""
        # This is a complex transformation that would require
        # sophisticated analysis. For now, add a TODO comment.

        lines = code.split("\n")
        start_idx = candidate.start_line - 1

        if start_idx < len(lines):
            lines.insert(start_idx, "// TODO: Convert recursion to iteration for General Safety Rule 1 compliance")

        return "\n".join(lines)

    def _validate_refactoring_result(
        self, original: str, refactored: str, language: LanguageSupport, validate_safety: bool
    ) -> Dict[str, Any]:
        """Validate that refactoring maintained syntactic correctness."""
        # Parse both versions
        original_parse = self.backend.parse(original, language)
        refactored_parse = self.backend.parse(refactored, language)

        errors = []
        warnings = []
        changes = []

        # Check if refactored code parses correctly
        if not refactored_parse.success:
            errors.extend([f"Syntax error: {err['message']}" for err in refactored_parse.errors])
            return {"success": False, "errors": errors, "warnings": warnings, "changes": changes}

        # Check for major structural changes (simplified)
        original_functions = self.backend.extract_functions(original_parse.ast, language)
        refactored_functions = self.backend.extract_functions(refactored_parse.ast, language)

        if len(refactored_functions) != len(original_functions):
            changes.append(f"Function count changed from {len(original_functions)} to {len(refactored_functions)}")

        # Safety validation if requested
        if validate_safety and self.overlay_manager:
            # Check against safety overlays
            for overlay_id in ["nasa_c_safety", "nasa_python_safety"]:
                overlay = self.overlay_manager.get_overlay(overlay_id)
                if overlay and overlay.language == language:
                    violations = self.overlay_manager.validate_code_against_overlay([refactored_parse.ast], overlay_id)
                    if violations:
                        warnings.extend([f"Safety warning: {v.get('message', '')}" for v in violations])

        return {"success": True, "errors": errors, "warnings": warnings, "changes": changes}

    def _sort_candidates_by_dependency(self, candidates: List[RefactoringCandidate]) -> List[RefactoringCandidate]:
        """Sort refactoring candidates by dependency order."""
        # Simple sorting by safety impact and effort
        return sorted(
            candidates,
            key=lambda c: (
                {"high": 3, "medium": 2, "low": 1, "none": 0}.get(c.safety_impact, 0),
                {"low": 1, "medium": 2, "high": 3}.get(c.estimated_effort, 2),
            ),
        )

    def _create_function_pattern(self, func: Dict) -> str:
        """Create a simple pattern representation of a function."""
        # Very simplified pattern - real implementation would use AST structure
        return f"lines:{func.get('body_lines', 0)//10}0_params:{len(func.get('parameters', []))}"

    def _contains_recursion(self, func: Dict, code: str) -> bool:
        """Check if function contains recursive calls."""
        # Simplified check - look for function calling itself
        func_name = func.get("name", "")
        if not func_name:
            return False

        # Extract function body (very simplified)
        start_line = func.get("line_start", 1)
        end_line = func.get("line_end", 1)
        lines = code.split("\n")[start_line:end_line]
        func_body = "\n".join(lines)

        # Look for self-calls
        return f"{func_name}(" in func_body

    def _needs_more_assertions(self, func: Dict, code: str) -> bool:
        """Check if function needs more assertions (General Safety Rule 5)."""
        # Extract function body and count assertions
        start_line = func.get("line_start", 1)
        end_line = func.get("line_end", 1)
        lines = code.split("\n")[start_line:end_line]
        func_body = "\n".join(lines)

        # Count existing assertions
        assertion_count = func_body.count("assert") + func_body.count("ASSERT")

        return assertion_count < 2  # General Safety Rule 5
