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
Autofix Safety Tier Classification System

Classifies potential autofixes into safety tiers to ensure only safe
transformations are applied automatically while preserving code correctness.

Tier Classification:
- Tier C (Auto-apply): Safe, grammar-preserving, minimal risk transformations
- Tier B (Human review): Moderate complexity changes requiring human oversight
- Tier A (Manual only): Complex architectural changes requiring careful review

Safety Considerations:
- Must preserve NASA Power of Ten compliance
- Must not break existing functionality
- Must maintain test compatibility
- Must preserve semantic meaning
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import re
from typing import Dict, List, Optional, Set


class SafetyTier(Enum):
    """Safety classification for autofix transformations"""

    TIER_C_AUTO = "tier_c_auto"  # Safe for automatic application
    TIER_B_REVIEW = "tier_b_review"  # Requires human review
    TIER_A_MANUAL = "tier_a_manual"  # Manual intervention required
    UNSAFE = "unsafe"  # Not safe for any autofix


@dataclass
class TierClassification:
    """Classification result for a potential autofix"""

    tier: SafetyTier
    confidence: float  # 0.0 to 1.0
    reasoning: str
    risk_factors: List[str]
    safety_checks: List[str]
    nasa_compliance: bool
    estimated_impact: str  # "minimal", "moderate", "significant"


class AutofixTierClassifier:
    """
    Classifies autofix transformations into safety tiers based on
    risk assessment and NASA Power of Ten compliance.
    """

    def __init__(self):
        # Tier C: Safe for auto-application
        self.tier_c_patterns = {
            "magic_literal_extraction": {
                "description": "Extract magic literals to named constants",
                "risk_factors": ["scope_change", "name_collision"],
                "safety_checks": ["const_scope_valid", "name_available", "same_value_type"],
            },
            "simple_parameter_rename": {
                "description": "Rename parameters to improve clarity",
                "risk_factors": ["name_collision", "external_api"],
                "safety_checks": ["local_scope_only", "not_public_api", "descriptive_name"],
            },
            "remove_unused_imports": {
                "description": "Remove demonstrably unused imports",
                "risk_factors": ["dynamic_import", "side_effects"],
                "safety_checks": ["static_analysis_confirms", "no_side_effects", "not_star_import"],
            },
            "add_missing_type_hints": {
                "description": "Add obvious type hints where missing",
                "risk_factors": ["wrong_type_inference", "runtime_behavior"],
                "safety_checks": ["type_clearly_inferrable", "no_dynamic_typing", "not_generic"],
            },
        }

        # Tier B: Requires human review
        self.tier_b_patterns = {
            "parameter_restructuring": {
                "description": "Restructure function parameters (e.g., use parameter object)",
                "risk_factors": ["api_breaking", "caller_impact", "serialization"],
                "safety_checks": ["backward_compatible", "caller_analysis", "test_coverage"],
            },
            "method_extraction": {
                "description": "Extract methods from large functions",
                "risk_factors": ["variable_scope", "side_effects", "return_complexity"],
                "safety_checks": ["scope_analysis", "side_effect_isolation", "single_responsibility"],
            },
            "conditional_simplification": {
                "description": "Simplify complex conditional logic",
                "risk_factors": ["logic_errors", "edge_cases", "boolean_complexity"],
                "safety_checks": ["logical_equivalence", "edge_case_preservation", "readable_result"],
            },
            "loop_optimization": {
                "description": "Optimize loop structures",
                "risk_factors": ["performance_regression", "iteration_behavior", "side_effects"],
                "safety_checks": ["performance_neutral", "behavior_preservation", "no_side_effect_changes"],
            },
        }

        # Tier A: Manual intervention required
        self.tier_a_patterns = {
            "god_object_decomposition": {
                "description": "Break down god objects into smaller classes",
                "risk_factors": ["architectural_impact", "dependency_cascade", "interface_changes"],
                "safety_checks": ["architectural_review", "dependency_analysis", "interface_stability"],
            },
            "inheritance_restructuring": {
                "description": "Restructure class hierarchies",
                "risk_factors": ["polymorphism_breaking", "contract_violation", "subclass_impact"],
                "safety_checks": ["contract_preservation", "polymorphism_safety", "subclass_compatibility"],
            },
            "design_pattern_application": {
                "description": "Apply design patterns to reduce coupling",
                "risk_factors": ["over_engineering", "complexity_increase", "performance_impact"],
                "safety_checks": ["pattern_appropriateness", "complexity_justification", "maintainability_gain"],
            },
            "api_redesign": {
                "description": "Redesign public APIs for better coupling",
                "risk_factors": ["breaking_changes", "client_impact", "version_compatibility"],
                "safety_checks": ["deprecation_strategy", "client_migration", "compatibility_layer"],
            },
        }

        # NASA Power of Ten rule compliance checks
        self.nasa_rule_checks = {
            1: "no_goto_statements",
            2: "bounded_loops_only",
            3: "avoid_heap_allocation",
            4: "limit_function_size",
            5: "minimum_assertion_density",
            6: "restrict_data_scope",
            7: "check_return_values",
            8: "limit_preprocessor",
            9: "pointer_use_restrictions",
            10: "static_analysis_clean",
        }

    def classify_autofix(
        self, violation_type: str, code_context: str, file_path: str, proposed_fix: str
    ) -> TierClassification:
        """
        Classify a proposed autofix into appropriate safety tier.

        Args:
            violation_type: Type of connascence/safety violation
            code_context: Source code context around the violation
            file_path: Path to the file being modified
            proposed_fix: Proposed transformation/fix

        Returns:
            TierClassification with safety assessment
        """

        # Analyze the proposed transformation
        risk_analysis = self._analyze_risks(violation_type, code_context, proposed_fix)
        nasa_compliance = self._check_nasa_compliance(proposed_fix, code_context)
        impact_assessment = self._assess_impact(violation_type, code_context, file_path)

        # Determine tier based on analysis
        tier = self._determine_tier(violation_type, risk_analysis, nasa_compliance, impact_assessment)

        return TierClassification(
            tier=tier,
            confidence=risk_analysis["confidence"],
            reasoning=risk_analysis["reasoning"],
            risk_factors=risk_analysis["risk_factors"],
            safety_checks=risk_analysis["safety_checks"],
            nasa_compliance=nasa_compliance,
            estimated_impact=impact_assessment["level"],
        )

    def _analyze_risks(self, violation_type: str, code_context: str, proposed_fix: str) -> Dict:
        """Analyze risk factors for the proposed fix"""

        # Check if this matches known safe patterns
        if violation_type == "magic_literal" and self._is_simple_literal_extraction(proposed_fix):
            return {
                "confidence": 0.95,
                "reasoning": "Simple magic literal extraction with clear scope",
                "risk_factors": ["name_collision"],
                "safety_checks": ["const_scope_valid", "name_available"],
            }

        if violation_type == "god_object" or ("class" in code_context.lower() and len(code_context.split("\n")) > 100):
            return {
                "confidence": 0.3,
                "reasoning": "Complex class restructuring requires careful review",
                "risk_factors": ["architectural_impact", "dependency_cascade", "interface_changes"],
                "safety_checks": ["architectural_review", "dependency_analysis"],
            }

        # Default to moderate risk
        return {
            "confidence": 0.6,
            "reasoning": "Standard refactoring with moderate complexity",
            "risk_factors": ["logic_change", "scope_impact"],
            "safety_checks": ["behavior_preservation", "test_coverage"],
        }

    def _check_nasa_compliance(self, proposed_fix: str, context: str) -> bool:
        """Check if proposed fix maintains NASA Power of Ten compliance"""

        # Check for potential violations
        violations = []

        # Rule 2: Check for unbounded loops
        if "while" in proposed_fix and "break" not in proposed_fix:
            violations.append("potential_unbounded_loop")

        # Rule 3: Check for dynamic allocation
        if any(keyword in proposed_fix for keyword in ["malloc", "new", "alloc"]):
            violations.append("dynamic_allocation")

        # Rule 4: Check function size (heuristic)
        if proposed_fix.count("\n") > 50:
            violations.append("function_too_large")

        # Rule 6: Check for global scope additions
        if "global" in proposed_fix.lower() and "def " not in context:
            violations.append("global_scope_expansion")

        # Rule 7: Check for unchecked return values
        if re.search(r"[\w_]+\([^)]*\);?\s*$", proposed_fix, re.MULTILINE):
            violations.append("unchecked_return_value")

        return len(violations) == 0

    def _assess_impact(self, violation_type: str, code_context: str, file_path: str) -> Dict:
        """Assess the potential impact of applying the fix"""

        file_size = len(code_context.split("\n"))
        is_test_file = "test" in Path(file_path).name.lower()
        is_public_api = "api" in file_path.lower() or "public" in file_path.lower()

        # Impact scoring
        impact_score = 0

        if violation_type == "god_object":
            impact_score += 3  # High impact
        if file_size > 500:
            impact_score += 2  # Large file changes are higher impact
        if is_public_api:
            impact_score += 2  # API changes have higher impact
        if not is_test_file:
            impact_score += 1  # Production code changes

        if impact_score <= 2:
            level = "minimal"
        elif impact_score <= 4:
            level = "moderate"
        else:
            level = "significant"

        return {
            "score": impact_score,
            "level": level,
            "factors": {"file_size": file_size, "is_test": is_test_file, "is_public_api": is_public_api},
        }

    def _determine_tier(
        self, violation_type: str, risk_analysis: Dict, nasa_compliance: bool, impact_assessment: Dict
    ) -> SafetyTier:
        """Determine the appropriate safety tier based on all factors"""

        # Immediate disqualifiers for auto-apply
        if not nasa_compliance:
            return SafetyTier.UNSAFE

        if impact_assessment["level"] == "significant":
            return SafetyTier.TIER_A_MANUAL

        if risk_analysis["confidence"] < 0.4:
            return SafetyTier.TIER_A_MANUAL

        # Tier C qualifiers (safe for auto-apply)
        if (
            risk_analysis["confidence"] >= 0.9
            and impact_assessment["level"] == "minimal"
            and violation_type in ["magic_literal", "unused_import", "simple_rename"]
        ):
            return SafetyTier.TIER_C_AUTO

        # Tier B qualifiers (human review required)
        if risk_analysis["confidence"] >= 0.6 and impact_assessment["level"] in ["minimal", "moderate"]:
            return SafetyTier.TIER_B_REVIEW

        # Default to manual review for safety
        return SafetyTier.TIER_A_MANUAL

    def _is_simple_literal_extraction(self, proposed_fix: str) -> bool:
        """Check if this is a simple, safe literal extraction"""

        # Look for pattern: CONSTANT_NAME = literal_value
        constant_pattern = r"^[A-Z_][A-Z0-9_]*\s*=\s*[\'\"0-9\[\]{}]"

        lines = proposed_fix.strip().split("\n")
        if len(lines) != 1:
            return False

        return bool(re.match(constant_pattern, lines[0].strip()))

    def get_safe_autofixes(self) -> Set[str]:
        """Get list of violation types safe for Tier C auto-application"""
        return {
            "magic_literal",
            "unused_import",
            "simple_rename",
            "add_type_hint",
            "remove_redundant_else",
            "simplify_boolean_expression",
        }

    def get_autofix_examples(self, violation_type: str) -> Optional[Dict[str, str]]:
        """Get example transformations for a violation type"""

        examples = {
            "magic_literal": {
                "before": "if status == 404:\n    handle_not_found()",
                "after": "HTTP_NOT_FOUND = 404\nif status == HTTP_NOT_FOUND:\n    handle_not_found()",
                "explanation": "Extract magic literal to named constant",
            },
            "god_object": {
                "before": "class UserManager:\n    def validate_user(self): ...\n    def save_to_db(self): ...\n    def send_email(self): ...\n    def generate_report(self): ...",
                "after": "class UserValidator:\n    def validate_user(self): ...\n\nclass UserRepository:\n    def save_to_db(self): ...\n\nclass EmailService:\n    def send_email(self): ...",
                "explanation": "Split god object into single-responsibility classes",
            },
            "parameter_position": {
                "before": "def create_user(name, email, age, role, department, salary): ...",
                "after": "@dataclass\nclass UserConfig:\n    name: str\n    email: str\n    age: int\n    role: str\n    department: str\n    salary: float\n\ndef create_user(config: UserConfig): ...",
                "explanation": "Replace parameter list with configuration object",
            },
        }

        return examples.get(violation_type)


def classify_autofix_safety(
    violation_type: str, code_context: str, file_path: str, proposed_fix: str
) -> TierClassification:
    """
    Convenience function to classify autofix safety tier.

    Args:
        violation_type: Type of violation (e.g., 'magic_literal', 'god_object')
        code_context: Source code context around the violation
        file_path: Path to file being modified
        proposed_fix: Proposed fix/transformation

    Returns:
        TierClassification with safety assessment
    """
    classifier = AutofixTierClassifier()
    return classifier.classify_autofix(violation_type, code_context, file_path, proposed_fix)


# Example usage and testing
if __name__ == "__main__":
    # Test the classifier
    classifier = AutofixTierClassifier()

    # Test Tier C (auto-safe) classification
    magic_literal_fix = "HTTP_NOT_FOUND = 404"
    magic_literal_context = "if response.status_code == 404:\n    return None"

    result = classifier.classify_autofix(
        "magic_literal", magic_literal_context, "src/api/handlers.py", magic_literal_fix
    )

    print(f"Magic literal fix classified as: {result.tier}")
    print(f"Confidence: {result.confidence}")
    print(f"NASA compliant: {result.nasa_compliance}")
    print(f"Reasoning: {result.reasoning}")
    print()

    # Test Tier A (manual only) classification
    god_object_context = """
    class UserManager:
        def __init__(self):
            self.db = Database()
            self.email = EmailService()

        def create_user(self, data):
            # 50+ lines of logic
            pass

        def validate_email(self, email):
            # validation logic
            pass

        def send_welcome_email(self, user):
            # email logic
            pass

        # ... many more methods
    """

    god_object_fix = """
    Extract UserValidator, UserRepository, EmailService classes
    """

    result2 = classifier.classify_autofix("god_object", god_object_context, "src/models/user.py", god_object_fix)

    print(f"God object fix classified as: {result2.tier}")
    print(f"Confidence: {result2.confidence}")
    print(f"NASA compliant: {result2.nasa_compliance}")
    print(f"Reasoning: {result2.reasoning}")
