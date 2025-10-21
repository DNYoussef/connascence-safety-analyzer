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
Integration Test Suite - Memory Coordination and Test Result Storage
Provides memory coordination infrastructure for integration test results
"""

from dataclasses import asdict, dataclass
import json
from pathlib import Path
import time
from typing import Any, Dict, List, Optional

from fixes.phase0.production_safe_assertions import ProductionAssert

# Global memory store for integration test coordination
INTEGRATION_TEST_MEMORY = {}


@dataclass
class TestResult:
    """Standard test result structure for memory coordination"""

    test_name: str
    status: str  # 'passed', 'failed', 'skipped', 'error'
    execution_time: float
    timestamp: float
    component: str
    details: Dict[str, Any]
    dependencies: List[str] = None

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


class IntegrationTestMemoryCoordinator:
    """Centralized memory coordination for all integration tests"""

    def __init__(self):
        self.memory_store = INTEGRATION_TEST_MEMORY
        self.session_id = f"integration_session_{int(time.time())}"
        self.test_results = []
        self.component_coverage = set()
        self.integration_chains = {}

    def store_test_result(self, test_result: TestResult):
        """Store test result with memory coordination"""

        ProductionAssert.not_none(test_result, "test_result")

        result_key = f"{self.session_id}_{test_result.test_name}"

        self.memory_store[result_key] = {
            "result": asdict(test_result),
            "stored_at": time.time(),
            "session_id": self.session_id,
        }

        self.test_results.append(test_result)
        self.component_coverage.add(test_result.component)

    def get_test_results(self, component: Optional[str] = None, status: Optional[str] = None) -> List[TestResult]:
        """Retrieve test results with optional filtering"""
        results = self.test_results.copy()

        if component:
            results = [r for r in results if r.component == component]

        if status:
            results = [r for r in results if r.status == status]

        return results

    def calculate_coverage_metrics(self) -> Dict[str, Any]:
        """Calculate comprehensive coverage metrics"""
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r.status == "passed"])
        failed_tests = len([r for r in self.test_results if r.status == "failed"])

        component_results = {}
        for component in self.component_coverage:
            component_tests = [r for r in self.test_results if r.component == component]
            component_results[component] = {
                "total": len(component_tests),
                "passed": len([r for r in component_tests if r.status == "passed"]),
                "pass_rate": (
                    len([r for r in component_tests if r.status == "passed"]) / len(component_tests) * 100
                    if component_tests
                    else 0
                ),
            }

        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "overall_pass_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
            "components_covered": len(self.component_coverage),
            "component_results": component_results,
            "total_execution_time": sum(r.execution_time for r in self.test_results),
            "average_execution_time": (
                sum(r.execution_time for r in self.test_results) / total_tests if total_tests > 0 else 0
            ),
        }

    def export_results(self, output_path: Path):
        """Export test results to file for CI/CD integration"""

        ProductionAssert.not_none(output_path, "output_path")

        metrics = self.calculate_coverage_metrics()

        export_data = {
            "session_id": self.session_id,
            "timestamp": time.time(),
            "metrics": metrics,
            "test_results": [asdict(result) for result in self.test_results],
            "memory_store_keys": list(self.memory_store.keys()),
        }

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(export_data, f, indent=2)

        return export_data

    def create_integration_chain(self, chain_name: str, components: List[str]):
        """Create integration test chain for dependency tracking"""

        ProductionAssert.not_none(chain_name, "chain_name")
        ProductionAssert.not_none(components, "components")

        self.integration_chains[chain_name] = {
            "components": components,
            "tests": [],
            "status": "initialized",
            "created_at": time.time(),
        }

    def add_to_chain(self, chain_name: str, test_result: TestResult):
        """Add test result to integration chain"""

        ProductionAssert.not_none(chain_name, "chain_name")
        ProductionAssert.not_none(test_result, "test_result")

        if chain_name in self.integration_chains:
            self.integration_chains[chain_name]["tests"].append(test_result)

            # Update chain status based on results
            chain_tests = self.integration_chains[chain_name]["tests"]
            if all(t.status == "passed" for t in chain_tests):
                self.integration_chains[chain_name]["status"] = "passed"
            elif any(t.status == "failed" for t in chain_tests):
                self.integration_chains[chain_name]["status"] = "failed"
            else:
                self.integration_chains[chain_name]["status"] = "in_progress"

    def get_chain_status(self, chain_name: str) -> Dict[str, Any]:
        """Get status of integration chain"""
        if chain_name not in self.integration_chains:
            return {"status": "not_found"}

        chain = self.integration_chains[chain_name]
        return {
            "status": chain["status"],
            "components": chain["components"],
            "tests_completed": len(chain["tests"]),
            "tests_passed": len([t for t in chain["tests"] if t.status == "passed"]),
            "chain_complete": len(chain["tests"]) == len(chain["components"]),
        }


# Global coordinator instance
INTEGRATION_COORDINATOR = IntegrationTestMemoryCoordinator()


def store_integration_result(
    test_name: str,
    status: str,
    execution_time: float,
    component: str,
    details: Dict[str, Any],
    dependencies: Optional[List[str]] = None,
):
    """Convenience function to store integration test results"""
    result = TestResult(
        test_name=test_name,
        status=status,
        execution_time=execution_time,
        timestamp=time.time(),
        component=component,
        details=details,
        dependencies=dependencies or [],
    )

    INTEGRATION_COORDINATOR.store_test_result(result)
    return result


def get_integration_metrics() -> Dict[str, Any]:
    """Get current integration test metrics"""
    return INTEGRATION_COORDINATOR.calculate_coverage_metrics()


def export_integration_results(output_dir: Optional[Path] = None) -> Dict[str, Any]:
    """Export integration test results"""
    if output_dir is None:
        output_dir = Path(__file__).parent.parent.parent / "test_results" / "integration"

    output_file = output_dir / "integration_test_results.json"
    return INTEGRATION_COORDINATOR.export_results(output_file)


# Test data and mock utilities
def create_test_workspace(workspace_name: str) -> Path:
    """Create standardized test workspace"""
    import tempfile

    workspace = Path(tempfile.mkdtemp(prefix=f"connascence_test_{workspace_name}_"))

    # Create standard directory structure
    (workspace / "src").mkdir()
    (workspace / "tests").mkdir()
    (workspace / "docs").mkdir()

    return workspace


def create_sample_violations() -> List[Dict[str, Any]]:
    """Create standard sample violations for testing"""
    return [
        {
            "id": "test_cop_001",
            "connascence_type": "CoP",
            "severity": "high",
            "description": "Function has too many positional parameters",
            "file_path": "test.py",
            "line_number": 1,
            "weight": 4.0,
        },
        {
            "id": "test_com_001",
            "connascence_type": "CoM",
            "severity": "medium",
            "description": "Magic literal should be extracted to constant",
            "file_path": "test.py",
            "line_number": 5,
            "weight": 2.5,
        },
        {
            "id": "test_coa_001",
            "connascence_type": "CoA",
            "severity": "critical",
            "description": "Class has too many methods",
            "file_path": "test.py",
            "line_number": 10,
            "weight": 5.0,
        },
        {
            "id": "test_cot_001",
            "connascence_type": "CoT",
            "severity": "medium",
            "description": "Function lacks type hints",
            "file_path": "test.py",
            "line_number": 15,
            "weight": 2.0,
        },
    ]


def create_mock_autofix_results() -> List[Dict[str, Any]]:
    """Create standard mock autofix results"""
    return [
        {
            "id": "fix_001",
            "violation_id": "test_cop_001",
            "fix_type": "parameter_object",
            "confidence": 0.78,
            "safety_level": "moderate",
            "description": "Convert to parameter object",
        },
        {
            "id": "fix_002",
            "violation_id": "test_com_001",
            "fix_type": "extract_constant",
            "confidence": 0.92,
            "safety_level": "safe",
            "description": "Extract magic literal to constant",
        },
        {
            "id": "fix_003",
            "violation_id": "test_cot_001",
            "fix_type": "add_type_hints",
            "confidence": 0.85,
            "safety_level": "safe",
            "description": "Add function type hints",
        },
    ]


# Performance benchmarking utilities
class IntegrationPerformanceBenchmark:
    """Performance benchmarking for integration tests"""

    def __init__(self):
        self.benchmarks = {}

    def start_benchmark(self, benchmark_name: str):
        """Start performance benchmark"""

        ProductionAssert.not_none(benchmark_name, "benchmark_name")

        self.benchmarks[benchmark_name] = {"start_time": time.time(), "end_time": None, "duration": None}

    def end_benchmark(self, benchmark_name: str):
        """End performance benchmark"""

        ProductionAssert.not_none(benchmark_name, "benchmark_name")

        if benchmark_name in self.benchmarks:
            self.benchmarks[benchmark_name]["end_time"] = time.time()
            self.benchmarks[benchmark_name]["duration"] = (
                self.benchmarks[benchmark_name]["end_time"] - self.benchmarks[benchmark_name]["start_time"]
            )

    def get_benchmark_results(self) -> Dict[str, Any]:
        """Get all benchmark results"""
        return self.benchmarks.copy()


# Global benchmark instance
INTEGRATION_BENCHMARK = IntegrationPerformanceBenchmark()


def benchmark_integration_test(test_name: str):
    """Decorator for benchmarking integration tests"""

    ProductionAssert.not_none(test_name, "test_name")

    def decorator(func):
        ProductionAssert.not_none(func, "func")

        def wrapper(*args, **kwargs):
            INTEGRATION_BENCHMARK.start_benchmark(test_name)
            try:
                result = func(*args, **kwargs)
                INTEGRATION_BENCHMARK.end_benchmark(test_name)
                return result
            except Exception as e:
                INTEGRATION_BENCHMARK.end_benchmark(test_name)
                raise e

        return wrapper

    return decorator


# Memory cleanup utilities
def cleanup_test_memory():
    """Clean up test memory after test run"""
    global INTEGRATION_TEST_MEMORY
    INTEGRATION_TEST_MEMORY.clear()

    # Reset coordinator
    global INTEGRATION_COORDINATOR
    INTEGRATION_COORDINATOR = IntegrationTestMemoryCoordinator()


def get_memory_usage_stats() -> Dict[str, Any]:
    """Get memory usage statistics for integration tests"""
    return {
        "total_stored_results": len(INTEGRATION_TEST_MEMORY),
        "memory_keys": list(INTEGRATION_TEST_MEMORY.keys()),
        "coordinator_test_count": len(INTEGRATION_COORDINATOR.test_results),
        "components_covered": len(INTEGRATION_COORDINATOR.component_coverage),
        "integration_chains": len(INTEGRATION_COORDINATOR.integration_chains),
    }


# Export main coordination components
__all__ = [
    "INTEGRATION_COORDINATOR",
    "IntegrationPerformanceBenchmark",
    "IntegrationTestMemoryCoordinator",
    "TestResult",
    "benchmark_integration_test",
    "cleanup_test_memory",
    "create_mock_autofix_results",
    "create_sample_violations",
    "create_test_workspace",
    "export_integration_results",
    "get_integration_metrics",
    "get_memory_usage_stats",
    "store_integration_result",
]
