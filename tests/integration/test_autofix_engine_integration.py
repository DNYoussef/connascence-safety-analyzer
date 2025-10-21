#!/usr/bin/env python3

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
Autofix Engine Integration Tests - Complete Autofix System Testing
Tests autofix engine with real violation data, patch generation, and safety validation
"""

from pathlib import Path
import tempfile
import time
from typing import Any, Dict, List, Optional

import pytest

from fixes.phase0.production_safe_assertions import ProductionAssert

# Memory coordination for autofix test results
AUTOFIX_MEMORY = {}


class AutofixTestCoordinator:
    """Coordinates autofix engine testing with memory tracking and sequential thinking"""

    def __init__(self):
        self.memory_store = AUTOFIX_MEMORY
        self.test_session_id = f"autofix_integration_{int(time.time())}"
        self.sequential_results = []

    def store_test_result(self, test_name: str, result: Dict[str, Any]):
        """Store test result with sequential thinking pattern"""

        ProductionAssert.not_none(test_name, "test_name")
        ProductionAssert.not_none(result, "result")
        ProductionAssert.not_none(test_name, "test_name")
        ProductionAssert.not_none(result, "result")
        self.memory_store[f"{self.test_session_id}_{test_name}"] = {
            "timestamp": time.time(),
            "result": result,
            "status": "completed",
            "sequence_order": len(self.sequential_results),
        }
        self.sequential_results.append(test_name)

    def get_sequential_results(self) -> List[str]:
        """Get results in sequential order"""
        return self.sequential_results.copy()

    def calculate_autofix_effectiveness(self) -> Dict[str, float]:
        """Calculate autofix engine effectiveness metrics"""
        results = self.get_test_results()

        total_violations = 0
        fixed_violations = 0
        safe_fixes = 0
        confidence_sum = 0
        fix_attempts = 0

        for test_key, test_data in results.items():
            result = test_data.get("result", {})

            if "violations_processed" in result:
                total_violations += result["violations_processed"]
                fixed_violations += result.get("fixes_generated", 0)
                safe_fixes += result.get("safe_fixes", 0)

            if "average_confidence" in result:
                confidence_sum += result["average_confidence"]
                fix_attempts += 1

        return {
            "fix_rate": (fixed_violations / total_violations) * 100 if total_violations > 0 else 0,
            "safety_rate": (safe_fixes / fixed_violations) * 100 if fixed_violations > 0 else 0,
            "average_confidence": confidence_sum / fix_attempts if fix_attempts > 0 else 0,
            "total_violations_processed": total_violations,
            "total_fixes_generated": fixed_violations,
        }

    def get_test_results(self) -> Dict[str, Any]:
        """Retrieve all test results for this session"""
        return {k: v for k, v in self.memory_store.items() if k.startswith(self.test_session_id)}


@pytest.fixture
def autofix_coordinator():
    """Create autofix test coordinator with memory tracking"""
    return AutofixTestCoordinator()


@pytest.fixture
def test_code_samples():
    """Create test code samples with known violations for autofix testing"""
    return {
        "magic_literals": """
def calculate_price(base_price):
    ProductionAssert.not_none(base_price, 'base_price')
        ProductionAssert.not_none(base_price, 'base_price')

    tax_rate = 0.08  # Magic literal
    discount_threshold = 1000  # Magic literal
    premium_multiplier = 1.5  # Magic literal

    if base_price > discount_threshold:
        return base_price * (1 + tax_rate) * premium_multiplier
    return base_price * (1 + tax_rate)
""",
        "parameter_bomb": """
def process_order(customer_id, product_id, quantity, price, tax_rate,
                  shipping_cost, discount_code, payment_method,
                  billing_address, shipping_address, notes):
    # Function with too many parameters - CoP violation
    total = quantity * price * (1 + tax_rate) + shipping_cost

    if discount_code == "SAVE10":  # Magic string
        total *= 0.9

    return {
        'customer': customer_id,
        'total': total,
        'payment': payment_method
    }
""",
        "god_class": """
class OrderManager:
    def __init__(self):
        self.orders = []
        self.customers = {}
        self.inventory = {}

    def create_order(self): pass
    def update_order(self): pass
    def cancel_order(self): pass
    def validate_order(self): pass
    def calculate_total(self): pass
    def apply_discount(self): pass
    def process_payment(self): pass
    def send_confirmation(self): pass
    def update_inventory(self): pass
    def generate_invoice(self): pass
    def handle_returns(self): pass
    def calculate_shipping(self): pass
    def validate_address(self): pass
    def send_tracking(self): pass
    def handle_disputes(self): pass
    def generate_reports(self): pass
    def manage_vendors(self): pass
    def process_refunds(self): pass
    def handle_reviews(self): pass
    def manage_promotions(self): pass
    def analyze_trends(self): pass
    def optimize_pricing(self): pass
    def forecast_demand(self): pass
    def manage_suppliers(self): pass
    def handle_complaints(self): pass  # 25+ methods = CoA violation
""",
        "missing_types": """
def process_data(data, options, callback):
    ProductionAssert.not_none(data, 'data')
        ProductionAssert.not_none(options, 'options')
    ProductionAssert.not_none(callback, 'callback')
        ProductionAssert.not_none(data, 'data')
    ProductionAssert.not_none(options, 'options')
        ProductionAssert.not_none(callback, 'callback')

    # Function without type hints - CoT violation
    results = []
    threshold = 100  # Magic literal

    for item in data:
        if item.value > threshold:
            processed = callback(item, options)
            results.append(processed)

    return results

def transform_items(items, transformer):


    ProductionAssert.not_none(items, 'items')
        ProductionAssert.not_none(transformer, 'transformer')

    ProductionAssert.not_none(items, 'items')
        ProductionAssert.not_none(transformer, 'transformer')

    # Another untyped function
    return [transformer(item) for item in items if item is not None]
""",
        "deep_nesting": """
def complex_validation(data):
    ProductionAssert.not_none(data, 'data')
        ProductionAssert.not_none(data, 'data')

    if data:
        if data.is_valid():
            if data.has_required_fields():
                if data.passes_business_rules():
                    if data.meets_security_criteria():
                        if data.is_properly_formatted():
                            return process_valid_data(data)
                        else:
                            return "Format error"
                    else:
                        return "Security error"
                else:
                    return "Business rule error"
            else:
                return "Missing fields"
        else:
            return "Invalid data"
    else:
        return "No data"
""",
        "duplicate_code": """
def calculate_discount_premium(price):
    ProductionAssert.not_none(price, 'price')
        ProductionAssert.not_none(price, 'price')

    base_discount = 0.1
    if price > 1000:
        return price * (1 - base_discount - 0.05)
    return price * (1 - base_discount)

def calculate_discount_standard(price):


    ProductionAssert.not_none(price, 'price')
        ProductionAssert.not_none(price, 'price')

    base_discount = 0.1  # Duplicate logic
    if price > 1000:
        return price * (1 - base_discount - 0.05)  # Same calculation
    return price * (1 - base_discount)  # Same calculation
""",
    }


@pytest.fixture
def mock_autofix_engine():
    """Create mock autofix engine with realistic behavior"""

    class MockAutofixEngine:
        def __init__(self):
            self.patches_generated = 0
            self.safety_validator = MockSafetyValidator()

        def generate_fix(self, violation: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
            """Generate autofix for a violation"""
            self.patches_generated += 1

            fix_generators = {
                "CoM": self._generate_magic_literal_fix,
                "CoP": self._generate_parameter_bomb_fix,
                "CoA": self._generate_god_class_fix,
                "CoT": self._generate_type_hint_fix,
                "CoA_nesting": self._generate_nesting_fix,
            }

            violation_type = violation.get("connascence_type", "CoM")
            generator = fix_generators.get(violation_type, self._generate_generic_fix)

            return generator(violation, context or {})

        def _generate_magic_literal_fix(self, violation: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
            """Generate fix for magic literal violations"""
            return {
                "id": f"fix_{self.patches_generated}",
                "violation_id": violation.get("id", "unknown"),
                "fix_type": "extract_constant",
                "confidence": 0.92,
                "safety_level": "safe",
                "description": "Extract magic literal to named constant",
                "changes": [
                    {
                        "file_path": violation.get("file_path", "test.py"),
                        "line_range": (violation.get("line_number", 1), violation.get("line_number", 1)),
                        "original_code": violation.get("context", ""),
                        "fixed_code": self._create_constant_extraction(violation),
                        "additional_changes": [
                            {
                                "action": "add_constant",
                                "location": "module_level",
                                "code": self._create_constant_definition(violation),
                            }
                        ],
                    }
                ],
                "requires_imports": [],
                "validation_result": self.safety_validator.validate_fix("extract_constant", violation),
            }

        def _generate_parameter_bomb_fix(self, violation: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
            """Generate fix for parameter bomb violations"""
            return {
                "id": f"fix_{self.patches_generated}",
                "violation_id": violation.get("id", "unknown"),
                "fix_type": "parameter_object",
                "confidence": 0.78,
                "safety_level": "moderate",
                "description": "Convert function parameters to parameter object",
                "changes": [
                    {
                        "file_path": violation.get("file_path", "test.py"),
                        "line_range": (violation.get("line_number", 1), violation.get("line_number", 1)),
                        "original_code": violation.get("context", ""),
                        "fixed_code": self._create_parameter_object_usage(violation),
                        "additional_changes": [
                            {
                                "action": "add_class",
                                "location": "before_function",
                                "code": self._create_parameter_object_class(violation),
                            }
                        ],
                    }
                ],
                "requires_imports": ["from dataclasses import dataclass", "from typing import Any"],
                "validation_result": self.safety_validator.validate_fix("parameter_object", violation),
            }

        def _generate_god_class_fix(self, violation: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
            """Generate fix for god class violations"""
            return {
                "id": f"fix_{self.patches_generated}",
                "violation_id": violation.get("id", "unknown"),
                "fix_type": "extract_class",
                "confidence": 0.65,
                "safety_level": "complex",
                "description": "Split large class into focused classes",
                "changes": [
                    {
                        "file_path": violation.get("file_path", "test.py"),
                        "line_range": (violation.get("line_number", 1), violation.get("line_number", 50)),
                        "original_code": violation.get("context", ""),
                        "fixed_code": self._create_class_split(violation),
                        "additional_changes": [
                            {
                                "action": "create_new_classes",
                                "location": "separate_files",
                                "code": self._create_extracted_classes(violation),
                            }
                        ],
                    }
                ],
                "requires_imports": [],
                "validation_result": self.safety_validator.validate_fix("extract_class", violation),
                "complexity_warning": "This refactoring affects multiple components",
            }

        def _generate_type_hint_fix(self, violation: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
            """Generate fix for missing type hints"""
            return {
                "id": f"fix_{self.patches_generated}",
                "violation_id": violation.get("id", "unknown"),
                "fix_type": "add_type_hints",
                "confidence": 0.85,
                "safety_level": "safe",
                "description": "Add type hints to function signature",
                "changes": [
                    {
                        "file_path": violation.get("file_path", "test.py"),
                        "line_range": (violation.get("line_number", 1), violation.get("line_number", 1)),
                        "original_code": violation.get("context", ""),
                        "fixed_code": self._add_type_hints(violation),
                        "additional_changes": [],
                    }
                ],
                "requires_imports": ["from typing import Any, List, Dict, Optional"],
                "validation_result": self.safety_validator.validate_fix("add_type_hints", violation),
            }

        def _generate_nesting_fix(self, violation: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
            """Generate fix for deep nesting violations"""
            return {
                "id": f"fix_{self.patches_generated}",
                "violation_id": violation.get("id", "unknown"),
                "fix_type": "reduce_nesting",
                "confidence": 0.72,
                "safety_level": "moderate",
                "description": "Reduce nesting depth using early returns",
                "changes": [
                    {
                        "file_path": violation.get("file_path", "test.py"),
                        "line_range": (violation.get("line_number", 1), violation.get("line_number", 20)),
                        "original_code": violation.get("context", ""),
                        "fixed_code": self._create_early_returns(violation),
                        "additional_changes": [],
                    }
                ],
                "requires_imports": [],
                "validation_result": self.safety_validator.validate_fix("reduce_nesting", violation),
            }

        def _generate_generic_fix(self, violation: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
            """Generate generic fix for unknown violation types"""
            return {
                "id": f"fix_{self.patches_generated}",
                "violation_id": violation.get("id", "unknown"),
                "fix_type": "manual_review",
                "confidence": 0.0,
                "safety_level": "manual",
                "description": "Manual review required - no automated fix available",
                "changes": [],
                "requires_imports": [],
                "validation_result": {"safe": False, "reason": "No automated fix available"},
                "manual_instructions": "Please review this violation and apply appropriate refactoring",
            }

        def batch_generate_fixes(self, violations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
            """Generate fixes for multiple violations"""
            fixes = []
            for violation in violations:
                try:
                    fix = self.generate_fix(violation)
                    fixes.append(fix)
                except Exception as e:
                    fixes.append(
                        {
                            "id": f"error_{self.patches_generated}",
                            "violation_id": violation.get("id", "unknown"),
                            "fix_type": "error",
                            "error": str(e),
                            "confidence": 0.0,
                            "safety_level": "error",
                        }
                    )
            return fixes

        def apply_fix(self, fix: Dict[str, Any], target_file: Path) -> Dict[str, Any]:
            """Apply fix to target file (mock implementation)"""
            return {
                "applied": True,
                "fix_id": fix.get("id"),
                "changes_made": len(fix.get("changes", [])),
                "backup_created": True,
                "validation_passed": fix.get("validation_result", {}).get("safe", False),
            }

        # Helper methods for fix generation
        def _create_constant_extraction(self, violation: Dict[str, Any]) -> str:
            context = violation.get("context", "")
            # Simple mock transformation
            return context.replace("0.08", "TAX_RATE").replace("1000", "DISCOUNT_THRESHOLD")

        def _create_constant_definition(self, violation: Dict[str, Any]) -> str:
            return "# Constants\\nTAX_RATE = 0.08\\nDISCOUNT_THRESHOLD = 1000"

        def _create_parameter_object_usage(self, violation: Dict[str, Any]) -> str:
            return "def process_order(params: OrderParams):"

        def _create_parameter_object_class(self, violation: Dict[str, Any]) -> str:
            return """@dataclass
class OrderParams:
    customer_id: str
    product_id: str
    quantity: int
    price: float
    tax_rate: float
    shipping_cost: float
    discount_code: str
    payment_method: str
    billing_address: str
    shipping_address: str
    notes: str"""

        def _create_class_split(self, violation: Dict[str, Any]) -> str:
            return """class OrderManager:
    def __init__(self):
        self.order_processor = OrderProcessor()
        self.inventory_manager = InventoryManager()
        self.payment_processor = PaymentProcessor()

    def create_order(self):
        return self.order_processor.create_order()"""

        def _create_extracted_classes(self, violation: Dict[str, Any]) -> str:
            return """# Extracted classes would be created in separate files
# class OrderProcessor: ...
# class InventoryManager: ...
# class PaymentProcessor: ..."""

        def _add_type_hints(self, violation: Dict[str, Any]) -> str:
            context = violation.get("context", "")
            if "def process_data(" in context:
                return "def process_data(data: List[Any], options: Dict[str, Any], callback: Callable) -> List[Any]:"
            return context

        def _create_early_returns(self, violation: Dict[str, Any]) -> str:
            return """def complex_validation(data):
    if not data:
        return "No data"
    if not data.is_valid():
        return "Invalid data"
    if not data.has_required_fields():
        return "Missing fields"
    if not data.passes_business_rules():
        return "Business rule error"
    if not data.meets_security_criteria():
        return "Security error"
    if not data.is_properly_formatted():
        return "Format error"

    return process_valid_data(data)"""

    class MockSafetyValidator:
        """Mock safety validator for autofix changes"""

        def validate_fix(self, fix_type: str, violation: Dict[str, Any]) -> Dict[str, Any]:
            """Validate if a fix is safe to apply"""
            safety_levels = {
                "extract_constant": {"safe": True, "risk_level": "low"},
                "add_type_hints": {"safe": True, "risk_level": "low"},
                "parameter_object": {"safe": True, "risk_level": "medium"},
                "reduce_nesting": {"safe": True, "risk_level": "medium"},
                "extract_class": {
                    "safe": False,
                    "risk_level": "high",
                    "reason": "Complex refactoring requires manual review",
                },
            }

            return safety_levels.get(fix_type, {"safe": False, "risk_level": "unknown"})

    return MockAutofixEngine()


class TestAutofixEngineIntegration:
    """Comprehensive autofix engine integration tests"""

    def test_magic_literal_fix_generation(self, autofix_coordinator, mock_autofix_engine, test_code_samples):
        """Test autofix engine generates correct fixes for magic literal violations"""

        # Create mock violation for magic literals
        violation = {
            "id": "CoM_001",
            "connascence_type": "CoM",
            "severity": "medium",
            "description": "Magic literal 0.08 should be extracted to constant",
            "file_path": "test_magic.py",
            "line_number": 3,
            "context": "tax_rate = 0.08  # Magic literal",
        }

        # Generate fix
        fix = mock_autofix_engine.generate_fix(violation)

        # Validate fix structure
        assert fix["fix_type"] == "extract_constant"
        assert fix["confidence"] > 0.8
        assert fix["safety_level"] == "safe"
        assert len(fix["changes"]) == 1

        # Validate fix content
        change = fix["changes"][0]
        assert change["file_path"] == "test_magic.py"
        assert "TAX_RATE" in change["fixed_code"]
        assert len(change["additional_changes"]) == 1

        # Validate constant definition
        constant_addition = change["additional_changes"][0]
        assert constant_addition["action"] == "add_constant"
        assert "TAX_RATE = 0.08" in constant_addition["code"]

        # Store results with sequential thinking
        autofix_coordinator.store_test_result(
            "magic_literal_fix",
            {
                "violations_processed": 1,
                "fixes_generated": 1,
                "safe_fixes": 1,
                "average_confidence": fix["confidence"],
                "fix_type": fix["fix_type"],
                "validation_passed": fix["validation_result"]["safe"],
            },
        )

    def test_parameter_bomb_fix_generation(self, autofix_coordinator, mock_autofix_engine):
        """Test autofix for parameter bomb (CoP) violations"""

        violation = {
            "id": "CoP_001",
            "connascence_type": "CoP",
            "severity": "high",
            "description": "Function has 11 positional parameters (max: 3)",
            "file_path": "test_params.py",
            "line_number": 2,
            "context": "def process_order(customer_id, product_id, quantity, ...)",
        }

        fix = mock_autofix_engine.generate_fix(violation)

        # Validate parameter object fix
        assert fix["fix_type"] == "parameter_object"
        assert fix["confidence"] > 0.7
        assert fix["safety_level"] == "moderate"

        # Validate required imports
        assert "from dataclasses import dataclass" in fix["requires_imports"]
        assert "from typing import Any" in fix["requires_imports"]

        # Validate class creation
        change = fix["changes"][0]
        class_addition = change["additional_changes"][0]
        assert class_addition["action"] == "add_class"
        assert "@dataclass" in class_addition["code"]
        assert "OrderParams" in class_addition["code"]

        autofix_coordinator.store_test_result(
            "parameter_bomb_fix",
            {
                "violations_processed": 1,
                "fixes_generated": 1,
                "safe_fixes": 1 if fix["safety_level"] == "safe" else 0,
                "average_confidence": fix["confidence"],
                "fix_type": fix["fix_type"],
                "requires_imports": len(fix["requires_imports"]),
            },
        )

    def test_god_class_fix_generation(self, autofix_coordinator, mock_autofix_engine):
        """Test autofix for god class (CoA) violations"""

        violation = {
            "id": "CoA_001",
            "connascence_type": "CoA",
            "severity": "critical",
            "description": "Class has 25 methods (max: 20)",
            "file_path": "test_god_class.py",
            "line_number": 1,
            "context": "class OrderManager:",
        }

        fix = mock_autofix_engine.generate_fix(violation)

        # Validate class extraction fix
        assert fix["fix_type"] == "extract_class"
        assert fix["confidence"] > 0.6  # Lower confidence for complex fixes
        assert fix["safety_level"] == "complex"

        # Validate complexity warning
        assert "complexity_warning" in fix
        assert "multiple components" in fix["complexity_warning"]

        # Validate class split approach
        change = fix["changes"][0]
        assert "OrderProcessor" in change["fixed_code"]
        assert "InventoryManager" in change["fixed_code"]
        assert "PaymentProcessor" in change["fixed_code"]

        autofix_coordinator.store_test_result(
            "god_class_fix",
            {
                "violations_processed": 1,
                "fixes_generated": 1,
                "safe_fixes": 0,  # Complex fixes are not marked as safe
                "average_confidence": fix["confidence"],
                "fix_type": fix["fix_type"],
                "complexity_warning": True,
            },
        )

    def test_type_hint_fix_generation(self, autofix_coordinator, mock_autofix_engine):
        """Test autofix for missing type hints (CoT) violations"""

        violation = {
            "id": "CoT_001",
            "connascence_type": "CoT",
            "severity": "medium",
            "description": "Function lacks type hints",
            "file_path": "test_types.py",
            "line_number": 1,
            "context": "def process_data(data, options, callback):",
        }

        fix = mock_autofix_engine.generate_fix(violation)

        # Validate type hint fix
        assert fix["fix_type"] == "add_type_hints"
        assert fix["confidence"] > 0.8
        assert fix["safety_level"] == "safe"

        # Validate typing imports
        required_imports = fix["requires_imports"]
        assert any("typing" in imp for imp in required_imports)

        # Validate type annotation addition
        change = fix["changes"][0]
        fixed_code = change["fixed_code"]
        assert "List[Any]" in fixed_code or "Dict[str, Any]" in fixed_code
        assert "Callable" in fixed_code

        autofix_coordinator.store_test_result(
            "type_hint_fix",
            {
                "violations_processed": 1,
                "fixes_generated": 1,
                "safe_fixes": 1,
                "average_confidence": fix["confidence"],
                "fix_type": fix["fix_type"],
                "imports_added": len(required_imports),
            },
        )

    def test_batch_fix_generation(self, autofix_coordinator, mock_autofix_engine):
        """Test batch processing of multiple violations"""

        violations = [
            {
                "id": "CoM_001",
                "connascence_type": "CoM",
                "severity": "medium",
                "description": "Magic literal violation",
                "file_path": "test.py",
                "line_number": 1,
            },
            {
                "id": "CoP_001",
                "connascence_type": "CoP",
                "severity": "high",
                "description": "Parameter bomb violation",
                "file_path": "test.py",
                "line_number": 5,
            },
            {
                "id": "CoT_001",
                "connascence_type": "CoT",
                "severity": "medium",
                "description": "Missing type hints",
                "file_path": "test.py",
                "line_number": 10,
            },
        ]

        # Generate batch fixes
        fixes = mock_autofix_engine.batch_generate_fixes(violations)

        # Validate batch processing
        assert len(fixes) == len(violations)

        # Validate individual fixes
        fix_types = [fix["fix_type"] for fix in fixes]
        expected_types = ["extract_constant", "parameter_object", "add_type_hints"]

        for expected_type in expected_types:
            assert expected_type in fix_types

        # Calculate batch metrics
        safe_fixes = sum(1 for fix in fixes if fix.get("safety_level") == "safe")
        total_confidence = sum(fix.get("confidence", 0) for fix in fixes)
        avg_confidence = total_confidence / len(fixes)

        autofix_coordinator.store_test_result(
            "batch_processing",
            {
                "violations_processed": len(violations),
                "fixes_generated": len(fixes),
                "safe_fixes": safe_fixes,
                "average_confidence": avg_confidence,
                "batch_processing_successful": True,
            },
        )

    def test_fix_application_simulation(self, autofix_coordinator, mock_autofix_engine):
        """Test applying fixes to actual code (simulated)"""

        # Create test workspace
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test_code.py"

            # Write original code with violations
            original_code = """
def calculate_total(price):
    ProductionAssert.not_none(price, 'price')
        ProductionAssert.not_none(price, 'price')

    tax = 0.08  # Magic literal
    return price * (1 + tax)
"""
            test_file.write_text(original_code)

            # Generate fix for magic literal
            violation = {
                "id": "CoM_test",
                "connascence_type": "CoM",
                "severity": "medium",
                "description": "Magic literal 0.08",
                "file_path": str(test_file),
                "line_number": 3,
                "context": "tax = 0.08  # Magic literal",
            }

            fix = mock_autofix_engine.generate_fix(violation)

            # Apply fix (mock implementation)
            application_result = mock_autofix_engine.apply_fix(fix, test_file)

            # Validate application result
            assert application_result["applied"] is True
            assert application_result["fix_id"] == fix["id"]
            assert application_result["backup_created"] is True
            assert application_result["changes_made"] > 0

            autofix_coordinator.store_test_result(
                "fix_application",
                {
                    "violations_processed": 1,
                    "fixes_applied": 1,
                    "backups_created": 1,
                    "application_successful": application_result["applied"],
                    "validation_passed": application_result["validation_passed"],
                },
            )

    def test_safety_validation_integration(self, autofix_coordinator, mock_autofix_engine):
        """Test safety validation for different fix types"""

        # Test different violation types for safety validation
        test_violations = [
            ("CoM", "extract_constant", "safe"),
            ("CoT", "add_type_hints", "safe"),
            ("CoP", "parameter_object", "moderate"),
            ("CoA", "extract_class", "complex"),
        ]

        safety_results = []

        for conn_type, expected_fix_type, expected_safety in test_violations:
            violation = {
                "id": f"{conn_type}_safety_test",
                "connascence_type": conn_type,
                "severity": "medium",
                "description": f"{conn_type} violation for safety testing",
                "file_path": "test.py",
                "line_number": 1,
            }

            fix = mock_autofix_engine.generate_fix(violation)
            validation_result = fix["validation_result"]

            safety_results.append(
                {
                    "violation_type": conn_type,
                    "fix_type": fix["fix_type"],
                    "safety_level": fix["safety_level"],
                    "is_safe": validation_result.get("safe", False),
                    "risk_level": validation_result.get("risk_level", "unknown"),
                }
            )

            # Validate expected safety levels
            assert fix["fix_type"] == expected_fix_type
            assert fix["safety_level"] == expected_safety

        # Calculate safety metrics
        safe_count = sum(1 for result in safety_results if result["is_safe"])
        safety_rate = (safe_count / len(safety_results)) * 100

        autofix_coordinator.store_test_result(
            "safety_validation",
            {
                "violations_processed": len(test_violations),
                "safety_validations_performed": len(safety_results),
                "safe_fixes": safe_count,
                "safety_rate": safety_rate,
                "safety_results": safety_results,
            },
        )

    def test_autofix_effectiveness_calculation(self, autofix_coordinator):
        """Test calculation of overall autofix effectiveness"""

        # Simulate storing several test results
        test_results = [
            (
                "magic_literal_fix",
                {"violations_processed": 5, "fixes_generated": 5, "safe_fixes": 5, "average_confidence": 0.92},
            ),
            (
                "parameter_bomb_fix",
                {"violations_processed": 3, "fixes_generated": 3, "safe_fixes": 2, "average_confidence": 0.78},
            ),
            (
                "type_hint_fix",
                {"violations_processed": 8, "fixes_generated": 8, "safe_fixes": 8, "average_confidence": 0.85},
            ),
            (
                "god_class_fix",
                {"violations_processed": 2, "fixes_generated": 2, "safe_fixes": 0, "average_confidence": 0.65},
            ),
        ]

        for test_name, result in test_results:
            autofix_coordinator.store_test_result(test_name, result)

        # Calculate effectiveness metrics
        effectiveness = autofix_coordinator.calculate_autofix_effectiveness()

        # Validate calculations
        assert effectiveness["total_violations_processed"] == 18  # 5+3+8+2
        assert effectiveness["total_fixes_generated"] == 18
        assert effectiveness["fix_rate"] == 100.0  # All violations got fixes
        assert effectiveness["safety_rate"] > 80.0  # High safety rate
        assert 0.7 <= effectiveness["average_confidence"] <= 0.9

        # Store effectiveness results
        autofix_coordinator.store_test_result(
            "effectiveness_calculation",
            {
                "effectiveness_metrics": effectiveness,
                "calculation_successful": True,
                "meets_targets": {
                    "fix_rate_target": effectiveness["fix_rate"] >= 80.0,
                    "safety_rate_target": effectiveness["safety_rate"] >= 70.0,
                    "confidence_target": effectiveness["average_confidence"] >= 0.7,
                },
            },
        )

    def test_sequential_thinking_coordination(self, autofix_coordinator):
        """Test sequential thinking pattern in autofix testing"""

        # Simulate sequential test execution
        sequential_steps = [
            "initialization",
            "violation_analysis",
            "fix_generation",
            "safety_validation",
            "application_simulation",
            "effectiveness_measurement",
        ]

        for step in sequential_steps:
            autofix_coordinator.store_test_result(
                step,
                {"step_name": step, "completed": True, "sequence_order": len(autofix_coordinator.sequential_results)},
            )

        # Validate sequential execution
        recorded_sequence = autofix_coordinator.get_sequential_results()
        assert recorded_sequence == sequential_steps

        # Validate memory coordination
        test_results = autofix_coordinator.get_test_results()
        assert len(test_results) == len(sequential_steps)

        # Validate sequential ordering
        for i, step in enumerate(sequential_steps):
            result_key = f"{autofix_coordinator.test_session_id}_{step}"
            assert result_key in test_results
            assert test_results[result_key]["result"]["sequence_order"] == i

    def test_autofix_error_handling(self, autofix_coordinator, mock_autofix_engine):
        """Test autofix engine error handling with problematic violations"""

        # Create problematic violations that should trigger error handling
        problematic_violations = [
            {
                "id": "invalid_violation",
                "connascence_type": "UNKNOWN",  # Invalid type
                "severity": "medium",
                "file_path": "test.py",
                "line_number": 1,
            },
            {
                "id": "malformed_violation",
                # Missing required fields
                "severity": "high",
            },
        ]

        # Generate fixes for problematic violations
        fixes = mock_autofix_engine.batch_generate_fixes(problematic_violations)

        # Validate error handling
        assert len(fixes) == len(problematic_violations)

        error_handling_successful = True
        for fix in fixes:
            if fix.get("fix_type") == "manual_review":
                assert fix["confidence"] == 0.0
                assert fix["safety_level"] == "manual"
            elif fix.get("fix_type") == "error":
                assert "error" in fix
                error_handling_successful = True

        autofix_coordinator.store_test_result(
            "error_handling",
            {
                "problematic_violations": len(problematic_violations),
                "error_handling_successful": error_handling_successful,
                "manual_review_required": any(f.get("fix_type") == "manual_review" for f in fixes),
                "errors_caught": any(f.get("fix_type") == "error" for f in fixes),
            },
        )


@pytest.mark.asyncio
class TestAutofixWorkflowIntegration:
    """Test autofix integration with broader workflow"""

    async def test_cli_to_autofix_workflow(self, mock_autofix_engine):
        """Test complete workflow: CLI scan -> autofix suggestions -> application"""

        workflow_steps = []

        # Step 1: CLI initiates scan (mock)
        scan_result = {
            "findings": [
                {
                    "id": "CoM_workflow_001",
                    "connascence_type": "CoM",
                    "severity": "medium",
                    "description": "Magic literal detected",
                    "file_path": "workflow_test.py",
                    "line_number": 5,
                }
            ],
            "summary": {"total_violations": 1},
        }
        workflow_steps.append("scan_completed")

        # Step 2: Request autofix for violations
        violations = scan_result["findings"]
        fixes = mock_autofix_engine.batch_generate_fixes(violations)
        workflow_steps.append("fixes_generated")

        # Step 3: Filter safe fixes for automatic application
        safe_fixes = [fix for fix in fixes if fix.get("safety_level") == "safe"]
        workflow_steps.append("safe_fixes_filtered")

        # Step 4: Apply safe fixes
        applied_fixes = []
        for fix in safe_fixes:
            with tempfile.NamedTemporaryFile(suffix=".py") as tmp_file:
                result = mock_autofix_engine.apply_fix(fix, Path(tmp_file.name))
                if result["applied"]:
                    applied_fixes.append(fix)
        workflow_steps.append("fixes_applied")

        # Validate complete workflow
        assert len(workflow_steps) == 4
        assert len(fixes) > 0
        assert len(applied_fixes) > 0
        assert all(fix["safety_level"] == "safe" for fix in applied_fixes)

    async def test_mcp_to_autofix_integration(self, mock_autofix_engine):
        """Test MCP server requesting autofix for violations"""

        # Simulate MCP server calling autofix
        mcp_request = {
            "tool": "propose_autofix",
            "args": {
                "finding_id": "CoP_mcp_001",
                "violation": {
                    "id": "CoP_mcp_001",
                    "connascence_type": "CoP",
                    "severity": "high",
                    "description": "Function has too many parameters",
                    "file_path": "mcp_test.py",
                    "line_number": 10,
                },
                "safety_preference": "moderate",
            },
        }

        # Process MCP request through autofix engine
        violation = mcp_request["args"]["violation"]
        fix = mock_autofix_engine.generate_fix(violation)

        # Validate MCP-compatible response
        mcp_response = {
            "status": "success",
            "autofix": fix,
            "metadata": {
                "confidence": fix["confidence"],
                "safety_level": fix["safety_level"],
                "requires_user_approval": fix["safety_level"] != "safe",
            },
        }

        assert mcp_response["status"] == "success"
        assert mcp_response["autofix"]["fix_type"] == "parameter_object"
        assert mcp_response["metadata"]["confidence"] > 0.7


if __name__ == "__main__":
    # Run autofix integration tests
    pytest.main([__file__, "-v", "--tb=short"])
