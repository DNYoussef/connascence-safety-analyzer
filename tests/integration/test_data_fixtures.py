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
Integration Test Data Fixtures and Mock Scenarios
Provides comprehensive test data and mock scenarios for integration testing
"""

import asyncio
from dataclasses import dataclass
import json
from pathlib import Path
import tempfile
import time
from typing import Any, Dict, List
from unittest.mock import Mock

import pytest

# Import memory coordination
from . import store_integration_result


@dataclass
class TestScenario:
    """Standard test scenario structure"""

    name: str
    description: str
    components: List[str]
    test_data: Dict[str, Any]
    expected_results: Dict[str, Any]
    complexity: str  # 'simple', 'moderate', 'complex'


class IntegrationTestDataManager:
    """Manages test data and mock scenarios for integration tests"""

    def __init__(self):
        self.scenarios = {}
        self.test_workspaces = {}
        self.mock_data_cache = {}

    def create_scenario(self, scenario: TestScenario):
        """Create and register a test scenario"""
        self.scenarios[scenario.name] = scenario

    def get_scenario(self, name: str) -> TestScenario:
        """Get test scenario by name"""
        return self.scenarios.get(name)

    def create_test_workspace(self, scenario_name: str) -> Path:
        """Create test workspace for scenario"""
        workspace = Path(tempfile.mkdtemp(prefix=f"integration_test_{scenario_name}_"))
        self.test_workspaces[scenario_name] = workspace
        return workspace

    def populate_workspace_with_violations(self, workspace: Path, violation_types: List[str]):
        """Populate workspace with files containing specific violation types"""

        violation_code_templates = {
            "CoP": '''
def function_with_too_many_params(a, b, c, d, e, f, g, h, i, j):
    """Function with parameter bomb violation"""
    return a + b + c + d + e + f + g + h + i + j
''',
            "CoM": '''
def function_with_magic_literals():
    """Function with magic literal violations"""
    threshold = 100  # Magic number
    rate = 0.08  # Magic number
    timeout = 5000  # Magic number

    if threshold > 50:
        return rate * timeout
    return 0
''',
            "CoA": '''
class GodClass:
    """Class with too many methods - architectural violation"""

    def method_01(self): pass
    def method_02(self): pass
    def method_03(self): pass
    def method_04(self): pass
    def method_05(self): pass
    def method_06(self): pass
    def method_07(self): pass
    def method_08(self): pass
    def method_09(self): pass
    def method_10(self): pass
    def method_11(self): pass
    def method_12(self): pass
    def method_13(self): pass
    def method_14(self): pass
    def method_15(self): pass
    def method_16(self): pass
    def method_17(self): pass
    def method_18(self): pass
    def method_19(self): pass
    def method_20(self): pass
    def method_21(self): pass  # Exceeds threshold
    def method_22(self): pass
    def method_23(self): pass
    def method_24(self): pass
    def method_25(self): pass
''',
            "CoT": '''
def function_without_type_hints(data, options, callback):
    """Function lacking type hints - type violation"""
    result = []

    for item in data:
        if item.is_valid():
            processed = callback(item, options)
            result.append(processed)

    return result

def another_untyped_function(param1, param2):
    """Another function without type hints"""
    return param1 + param2
''',
            "nesting": '''
def deeply_nested_function(data):
    """Function with deep nesting violation"""
    if data:
        if data.is_valid():
            if data.has_content():
                if data.passes_validation():
                    if data.meets_criteria():
                        if data.is_approved():
                            return data.process()
                        else:
                            return None
                    else:
                        return None
                else:
                    return None
            else:
                return None
        else:
            return None
    else:
        return None
''',
            "duplicate": '''
def calculate_discount_premium(price):
    """First implementation - duplicate logic"""
    base_rate = 0.1
    if price > 1000:
        return price * (1 - base_rate - 0.05)
    return price * (1 - base_rate)

def calculate_discount_standard(price):
    """Second implementation - same logic"""
    base_rate = 0.1  # Duplicate
    if price > 1000:  # Same condition
        return price * (1 - base_rate - 0.05)  # Same calculation
    return price * (1 - base_rate)  # Same fallback
''',
        }

        # Create source directory
        src_dir = workspace / "src"
        src_dir.mkdir(exist_ok=True)

        # Create files with requested violations
        for i, violation_type in enumerate(violation_types):
            if violation_type in violation_code_templates:
                filename = f"{violation_type.lower()}_violations.py"
                filepath = src_dir / filename

                code = f'''#!/usr/bin/env python3
"""
Test file containing {violation_type} violations
Generated for integration testing
"""

{violation_code_templates[violation_type]}

# Additional test code
def helper_function():
    """Helper function for testing"""
    return "test"

if __name__ == "__main__":
    print("Integration test file")
'''
                filepath.write_text(code)

        # Create configuration file
        config_file = workspace / "connascence_config.json"
        config_file.write_text(
            json.dumps(
                {
                    "analysis_profile": "integration_test",
                    "thresholds": {
                        "max_positional_params": 3,
                        "god_class_methods": 20,
                        "max_nesting_depth": 4,
                        "max_cyclomatic_complexity": 10,
                    },
                    "budget_limits": {"CoM": 5, "CoP": 3, "CoT": 8, "CoA": 2, "total_violations": 25},
                },
                indent=2,
            )
        )

        return workspace


# Pre-defined test scenarios
TEST_DATA_MANAGER = IntegrationTestDataManager()


def create_standard_scenarios():
    """Create standard integration test scenarios"""

    # Simple MCP Integration Scenario
    TEST_DATA_MANAGER.create_scenario(
        TestScenario(
            name="simple_mcp_integration",
            description="Basic MCP server integration with analyzer",
            components=["analyzer", "mcp_server"],
            test_data={"violation_types": ["CoM", "CoP"], "file_count": 2, "expected_findings": 4},
            expected_results={
                "mcp_response_status": "success",
                "findings_processed": 4,
                "quality_score_range": (70, 85),
            },
            complexity="simple",
        )
    )

    # Moderate Autofix Workflow Scenario
    TEST_DATA_MANAGER.create_scenario(
        TestScenario(
            name="autofix_workflow",
            description="Complete autofix workflow with multiple violation types",
            components=["analyzer", "mcp_server", "autofix"],
            test_data={
                "violation_types": ["CoM", "CoP", "CoT"],
                "file_count": 3,
                "expected_findings": 8,
                "safe_fix_ratio": 0.6,
            },
            expected_results={"fixes_generated": 6, "safe_fixes": 4, "fixes_applied": 4, "quality_improvement": 15.0},
            complexity="moderate",
        )
    )

    # Complex System Integration Scenario
    TEST_DATA_MANAGER.create_scenario(
        TestScenario(
            name="complete_system_integration",
            description="Full system integration with all components",
            components=["security", "cli", "analyzer", "mcp_server", "autofix", "vscode_extension", "grammar_layer"],
            test_data={
                "violation_types": ["CoM", "CoP", "CoA", "CoT", "nesting", "duplicate"],
                "file_count": 6,
                "expected_findings": 15,
                "security_clearance": True,
                "enterprise_mode": True,
            },
            expected_results={
                "all_components_tested": True,
                "security_validation_passed": True,
                "fixes_generated": 12,
                "quality_improvement": 25.0,
                "enterprise_compliance": True,
            },
            complexity="complex",
        )
    )

    # Performance Stress Test Scenario
    TEST_DATA_MANAGER.create_scenario(
        TestScenario(
            name="performance_stress_test",
            description="High-load performance testing across components",
            components=["analyzer", "mcp_server", "autofix"],
            test_data={
                "violation_types": ["CoM", "CoP", "CoA", "CoT", "nesting"],
                "file_count": 20,
                "expected_findings": 50,
                "concurrent_requests": 5,
                "performance_threshold": 10.0,  # seconds
            },
            expected_results={
                "analysis_completed": True,
                "performance_acceptable": True,
                "throughput_target": 5.0,  # violations per second
                "memory_usage_acceptable": True,
            },
            complexity="complex",
        )
    )

    # Error Handling Scenario
    TEST_DATA_MANAGER.create_scenario(
        TestScenario(
            name="error_handling_integration",
            description="Error handling and recovery across components",
            components=["analyzer", "mcp_server", "autofix"],
            test_data={
                "violation_types": ["CoM"],
                "file_count": 1,
                "inject_errors": ["analyzer_failure", "mcp_timeout", "autofix_error"],
                "expected_error_recovery": True,
            },
            expected_results={
                "errors_handled_gracefully": True,
                "system_recovery": True,
                "partial_results_available": True,
            },
            complexity="moderate",
        )
    )


# Initialize standard scenarios
create_standard_scenarios()


@pytest.fixture
def test_data_manager():
    """Provide test data manager for integration tests"""
    return TEST_DATA_MANAGER


@pytest.fixture
def simple_integration_workspace():
    """Create simple integration test workspace"""
    workspace = TEST_DATA_MANAGER.create_test_workspace("simple_integration")
    TEST_DATA_MANAGER.populate_workspace_with_violations(workspace, ["CoM", "CoP"])

    yield workspace

    # Cleanup
    import shutil

    shutil.rmtree(workspace, ignore_errors=True)


@pytest.fixture
def complex_integration_workspace():
    """Create complex integration test workspace"""
    workspace = TEST_DATA_MANAGER.create_test_workspace("complex_integration")
    TEST_DATA_MANAGER.populate_workspace_with_violations(
        workspace, ["CoM", "CoP", "CoA", "CoT", "nesting", "duplicate"]
    )

    yield workspace

    # Cleanup
    import shutil

    shutil.rmtree(workspace, ignore_errors=True)


@pytest.fixture
def performance_test_workspace():
    """Create performance testing workspace with many violations"""
    workspace = TEST_DATA_MANAGER.create_test_workspace("performance_test")

    # Create multiple files with violations for stress testing
    violation_types = ["CoM", "CoP", "CoA", "CoT", "nesting"]

    for i in range(4):  # Create 4 copies of each violation type
        TEST_DATA_MANAGER.populate_workspace_with_violations(
            workspace, [vtype + f"_{i}" if vtype in violation_types else vtype for vtype in violation_types]
        )

    yield workspace

    # Cleanup
    import shutil

    shutil.rmtree(workspace, ignore_errors=True)


class MockComponentFactory:
    """Factory for creating mock components with realistic behavior"""

    @staticmethod
    def create_analyzer_mock(response_delay: float = 0.1, failure_rate: float = 0.0):
        """Create mock analyzer with configurable behavior"""

        async def mock_analyze_path(path: Path, profile: str = "modern_general"):
            await asyncio.sleep(response_delay)

            # Simulate occasional failures
            if failure_rate > 0 and time.time() % 1.0 < failure_rate:
                raise Exception(f"Mock analyzer failure for {path}")

            # Generate realistic findings based on path
            findings = []
            file_count = len(list(path.glob("**/*.py"))) if path.exists() else 1

            for i in range(min(file_count * 2, 10)):  # 2 findings per file, max 10
                findings.append(
                    {
                        "id": f"mock_finding_{i:03d}",
                        "connascence_type": ["CoM", "CoP", "CoA", "CoT"][i % 4],
                        "severity": ["low", "medium", "high", "critical"][i % 4],
                        "description": f"Mock violation {i}",
                        "file_path": str(path / "src" / "test.py"),
                        "line_number": i + 1,
                        "weight": 1.0 + (i % 5),
                    }
                )

            return {
                "status": "success",
                "findings": findings,
                "summary": {
                    "total_violations": len(findings),
                    "quality_score": max(0, 100 - len(findings) * 5),
                    "connascence_index": sum(f["weight"] for f in findings),
                    "files_analyzed": file_count,
                    "analysis_time_ms": int(response_delay * 1000),
                },
            }

        mock = Mock()
        mock.analyze_path = mock_analyze_path
        return mock

    @staticmethod
    def create_mcp_server_mock(response_delay: float = 0.05, failure_rate: float = 0.0):
        """Create mock MCP server with configurable behavior"""

        async def mock_call_tool(tool_name: str, args: Dict[str, Any]):
            await asyncio.sleep(response_delay)

            if failure_rate > 0 and time.time() % 1.0 < failure_rate:
                raise Exception(f"Mock MCP server failure for tool {tool_name}")

            if tool_name == "scan_path":
                findings = args.get("findings", [])
                return {
                    "status": "success",
                    "findings_processed": len(findings),
                    "quality_score": 75.0 + (len(findings) * 2),
                    "mcp_processing_time": response_delay,
                }
            elif tool_name == "propose_autofix":
                return {"status": "success", "fix_available": True, "confidence": 0.85, "fix_type": "extract_constant"}
            elif tool_name == "suggest_refactors":
                return {
                    "status": "success",
                    "suggestions": [
                        {"technique": "Extract Parameter Object", "confidence": 89},
                        {"technique": "Extract Constants", "confidence": 95},
                    ],
                }
            else:
                return {"status": "success", "result": f"mock_result_{tool_name}"}

        mock = Mock()
        mock.call_tool = mock_call_tool
        mock.is_running = True
        return mock

    @staticmethod
    def create_autofix_engine_mock(response_delay: float = 0.2, failure_rate: float = 0.0):
        """Create mock autofix engine with configurable behavior"""

        async def mock_generate_fixes(violations: List[Dict[str, Any]]):
            await asyncio.sleep(response_delay)

            if failure_rate > 0 and time.time() % 1.0 < failure_rate:
                raise Exception("Mock autofix engine failure")

            fixes = []
            for i, violation in enumerate(violations):
                fix_type_mapping = {
                    "CoM": "extract_constant",
                    "CoP": "parameter_object",
                    "CoT": "add_type_hints",
                    "CoA": "extract_class",
                }

                fix_type = fix_type_mapping.get(violation.get("connascence_type", "CoM"), "manual_review")
                confidence = 0.9 if fix_type == "extract_constant" else 0.75
                safety = "safe" if fix_type in ["extract_constant", "add_type_hints"] else "moderate"

                fixes.append(
                    {
                        "id": f"fix_{i:03d}",
                        "violation_id": violation.get("id", f"violation_{i}"),
                        "fix_type": fix_type,
                        "confidence": confidence,
                        "safety_level": safety,
                        "estimated_effort": "low" if safety == "safe" else "medium",
                    }
                )

            return fixes

        async def mock_apply_fixes(fixes: List[Dict[str, Any]], target_path: Path):
            await asyncio.sleep(response_delay * 0.5)

            if failure_rate > 0 and time.time() % 1.0 < failure_rate:
                return {"status": "error", "fixes_applied": 0, "error": "Mock application failure"}

            safe_fixes = [f for f in fixes if f.get("safety_level") == "safe"]

            return {
                "status": "success",
                "fixes_attempted": len(fixes),
                "fixes_applied": len(safe_fixes),
                "fixes_skipped": len(fixes) - len(safe_fixes),
                "success_rate": (len(safe_fixes) / len(fixes)) * 100 if fixes else 0,
            }

        mock = Mock()
        mock.generate_fixes = mock_generate_fixes
        mock.apply_fixes = mock_apply_fixes
        return mock


@pytest.fixture
def mock_component_factory():
    """Provide mock component factory for integration tests"""
    return MockComponentFactory()


@pytest.fixture
def reliable_mock_components(mock_component_factory):
    """Create reliable mock components for standard testing"""
    return {
        "analyzer": mock_component_factory.create_analyzer_mock(response_delay=0.05, failure_rate=0.0),
        "mcp_server": mock_component_factory.create_mcp_server_mock(response_delay=0.03, failure_rate=0.0),
        "autofix_engine": mock_component_factory.create_autofix_engine_mock(response_delay=0.1, failure_rate=0.0),
    }


@pytest.fixture
def unreliable_mock_components(mock_component_factory):
    """Create unreliable mock components for error testing"""
    return {
        "analyzer": mock_component_factory.create_analyzer_mock(response_delay=0.1, failure_rate=0.2),
        "mcp_server": mock_component_factory.create_mcp_server_mock(response_delay=0.05, failure_rate=0.15),
        "autofix_engine": mock_component_factory.create_autofix_engine_mock(response_delay=0.15, failure_rate=0.1),
    }


@pytest.fixture
def slow_mock_components(mock_component_factory):
    """Create slow mock components for performance testing"""
    return {
        "analyzer": mock_component_factory.create_analyzer_mock(response_delay=0.5, failure_rate=0.0),
        "mcp_server": mock_component_factory.create_mcp_server_mock(response_delay=0.3, failure_rate=0.0),
        "autofix_engine": mock_component_factory.create_autofix_engine_mock(response_delay=0.8, failure_rate=0.0),
    }


class IntegrationTestValidator:
    """Validates integration test results against expected outcomes"""

    @staticmethod
    def validate_analyzer_mcp_integration(
        analyzer_result: Dict[str, Any], mcp_result: Dict[str, Any]
    ) -> Dict[str, bool]:
        """Validate analyzer → MCP server integration"""
        return {
            "data_transfer_successful": (
                len(analyzer_result.get("findings", [])) == mcp_result.get("findings_processed", 0)
            ),
            "quality_metrics_consistent": (mcp_result.get("quality_score", 0) > 0),
            "status_successful": (analyzer_result.get("status") == "success" and mcp_result.get("status") == "success"),
        }

    @staticmethod
    def validate_mcp_autofix_integration(mcp_result: Dict[str, Any], autofix_result: Dict[str, Any]) -> Dict[str, bool]:
        """Validate MCP server → autofix engine integration"""
        return {
            "fix_proposals_generated": len(autofix_result.get("fixes", [])) > 0,
            "confidence_scores_present": all("confidence" in fix for fix in autofix_result.get("fixes", [])),
            "safety_levels_assigned": all("safety_level" in fix for fix in autofix_result.get("fixes", [])),
            "mcp_context_preserved": mcp_result.get("status") == "success",
        }

    @staticmethod
    def validate_complete_workflow(workflow_results: Dict[str, Any]) -> Dict[str, bool]:
        """Validate complete workflow integration"""
        return {
            "all_stages_completed": all(stage.get("status") == "success" for stage in workflow_results.values()),
            "quality_improvement_achieved": (
                workflow_results.get("final_quality_score", 0) > workflow_results.get("initial_quality_score", 0)
            ),
            "fixes_successfully_applied": (workflow_results.get("fixes_applied", 0) > 0),
            "performance_acceptable": (workflow_results.get("total_execution_time", 999) < 10.0),
        }


@pytest.fixture
def integration_validator():
    """Provide integration test validator"""
    return IntegrationTestValidator()


# Test scenario runner utility
async def run_integration_scenario(scenario_name: str, components: Dict[str, Any]) -> Dict[str, Any]:
    """Run a complete integration scenario with provided components"""

    scenario = TEST_DATA_MANAGER.get_scenario(scenario_name)
    if not scenario:
        raise ValueError(f"Scenario {scenario_name} not found")

    # Store scenario start
    start_time = time.time()
    store_integration_result(
        f"{scenario_name}_start",
        "in_progress",
        0.0,
        "scenario_runner",
        {"scenario": scenario.name, "components": scenario.components},
    )

    results = {"scenario": scenario.name, "results": {}}

    try:
        # Execute scenario based on components required
        if "analyzer" in scenario.components and "mcp_server" in scenario.components:
            # Run analyzer → MCP integration
            workspace = TEST_DATA_MANAGER.create_test_workspace(f"{scenario_name}_execution")
            TEST_DATA_MANAGER.populate_workspace_with_violations(
                workspace, scenario.test_data.get("violation_types", ["CoM"])
            )

            analyzer_result = await components["analyzer"].analyze_path(workspace)
            mcp_result = await components["mcp_server"].call_tool(
                "scan_path", {"findings": analyzer_result.get("findings", [])}
            )

            results["results"]["analyzer"] = analyzer_result
            results["results"]["mcp_server"] = mcp_result

        if "autofix" in scenario.components:
            # Run autofix workflow
            violations = results["results"].get("analyzer", {}).get("findings", [])
            if violations:
                fixes = await components["autofix"].generate_fixes(violations)
                application_result = await components["autofix"].apply_fixes(fixes, workspace)

                results["results"]["autofix_generation"] = fixes
                results["results"]["autofix_application"] = application_result

        # Calculate execution metrics
        execution_time = time.time() - start_time
        results["execution_time"] = execution_time
        results["success"] = True

        # Store scenario completion
        store_integration_result(f"{scenario_name}_completed", "passed", execution_time, "scenario_runner", results)

        # Cleanup
        import shutil

        if "workspace" in locals():
            shutil.rmtree(workspace, ignore_errors=True)

        return results

    except Exception as e:
        execution_time = time.time() - start_time

        # Store scenario failure
        store_integration_result(
            f"{scenario_name}_failed",
            "failed",
            execution_time,
            "scenario_runner",
            {"error": str(e), "scenario": scenario.name},
        )

        # Cleanup
        import shutil

        if "workspace" in locals():
            shutil.rmtree(workspace, ignore_errors=True)

        raise e


if __name__ == "__main__":
    # Test fixture creation
    print("Integration test data fixtures initialized")
    print(f"Available scenarios: {list(TEST_DATA_MANAGER.scenarios.keys())}")

    # Create sample workspace for verification
    sample_workspace = TEST_DATA_MANAGER.create_test_workspace("sample")
    TEST_DATA_MANAGER.populate_workspace_with_violations(sample_workspace, ["CoM", "CoP"])
    print(f"Sample workspace created at: {sample_workspace}")

    # List created files
    for file_path in sample_workspace.rglob("*.py"):
        print(f"  - {file_path.relative_to(sample_workspace)}")

    # Cleanup sample workspace
    import shutil

    shutil.rmtree(sample_workspace, ignore_errors=True)
    print("Sample workspace cleaned up")
