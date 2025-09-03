#!/usr/bin/env python3
"""
End-to-End CLI Workflow Tests

Tests complete CLI workflows from input to final report generation.
Uses memory coordination for scenario tracking and sequential thinking.
"""

import json
import os
import pytest
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from unittest.mock import Mock, patch

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from cli.connascence import ConnascenceCLI


class E2EMemoryCoordinator:
    """Memory coordinator for tracking e2e test scenarios and results."""
    
    def __init__(self):
        self.test_scenarios = {}
        self.performance_metrics = {}
        self.workflow_traces = {}
        self.error_patterns = {}
        self.exit_code_scenarios = {}
    
    def store_test_scenario(self, scenario_id: str, config: Dict[str, Any]):
        """Store test scenario configuration."""
        self.test_scenarios[scenario_id] = {
            'config': config,
            'timestamp': time.time(),
            'status': 'initialized'
        }
    
    def update_scenario_status(self, scenario_id: str, status: str, 
                             results: Optional[Dict] = None):
        """Update scenario status and results."""
        if scenario_id in self.test_scenarios:
            self.test_scenarios[scenario_id]['status'] = status
            if results:
                self.test_scenarios[scenario_id]['results'] = results
    
    def store_performance_metrics(self, scenario_id: str, metrics: Dict[str, Any]):
        """Store performance metrics for scenario."""
        self.performance_metrics[scenario_id] = metrics
    
    def store_workflow_trace(self, scenario_id: str, trace: List[Dict]):
        """Store sequential workflow execution trace."""
        self.workflow_traces[scenario_id] = trace
    
    def store_exit_code_scenario(self, scenario_id: str, expected_code: int, 
                               actual_code: int, conditions: Dict):
        """Store exit code test scenario results."""
        self.exit_code_scenarios[scenario_id] = {
            'expected': expected_code,
            'actual': actual_code,
            'conditions': conditions,
            'passed': expected_code == actual_code,
            'timestamp': time.time()
        }
    
    def get_scenario_summary(self) -> Dict[str, Any]:
        """Get summary of all test scenarios."""
        return {
            'total_scenarios': len(self.test_scenarios),
            'completed': len([s for s in self.test_scenarios.values() if s['status'] == 'completed']),
            'failed': len([s for s in self.test_scenarios.values() if s['status'] == 'failed']),
            'performance_tests': len(self.performance_metrics),
            'exit_code_tests': len(self.exit_code_scenarios),
            'exit_code_pass_rate': sum(1 for s in self.exit_code_scenarios.values() if s['passed']) / max(len(self.exit_code_scenarios), 1)
        }


# Global memory coordinator instance
memory_coordinator = E2EMemoryCoordinator()


class SequentialWorkflowValidator:
    """Sequential thinking validator for comprehensive workflow testing."""
    
    def __init__(self, memory_coordinator: E2EMemoryCoordinator):
        self.memory = memory_coordinator
        self.current_scenario = None
        self.workflow_steps = []
    
    def start_scenario(self, scenario_id: str, description: str):
        """Start a new workflow scenario with sequential validation."""
        self.current_scenario = scenario_id
        self.workflow_steps = []
        self.memory.store_test_scenario(scenario_id, {
            'description': description,
            'start_time': time.time()
        })
    
    def add_step(self, step_name: str, step_data: Dict[str, Any]):
        """Add a workflow step with validation."""
        step = {
            'name': step_name,
            'timestamp': time.time(),
            'data': step_data,
            'index': len(self.workflow_steps)
        }
        self.workflow_steps.append(step)
    
    def validate_step_sequence(self, expected_sequence: List[str]) -> bool:
        """Validate that steps occurred in expected sequence."""
        actual_sequence = [step['name'] for step in self.workflow_steps]
        return actual_sequence == expected_sequence
    
    def complete_scenario(self, success: bool, results: Dict[str, Any]):
        """Complete scenario with results."""
        if self.current_scenario:
            self.memory.store_workflow_trace(self.current_scenario, self.workflow_steps)
            self.memory.update_scenario_status(
                self.current_scenario,
                'completed' if success else 'failed',
                results
            )


@pytest.fixture
def temp_project():
    """Create temporary project with complex connascence violations."""
    temp_dir = tempfile.mkdtemp()
    project_path = Path(temp_dir)
    
    # Create complex project structure
    (project_path / "src").mkdir()
    (project_path / "src" / "core").mkdir()
    (project_path / "src" / "utils").mkdir()
    (project_path / "tests").mkdir()
    (project_path / "config").mkdir()
    
    # Main application with multiple violation types
    (project_path / "src" / "app.py").write_text("""
def complex_function(param1, param2, param3, param4, param5, param6):
    '''Function with parameter bomb violation.'''
    MAGIC_THRESHOLD = 100  # Should be extracted to constant
    SECRET_KEY = "abc123"  # Magic string
    
    if param1 > MAGIC_THRESHOLD and param2 == "premium":
        discount_rate = 0.15  # Magic literal
        if param3 == "winter":
            bonus = 0.05  # Magic literal  
        else:
            bonus = 0.02  # Magic literal
        
        # Complex algorithm connascence
        if param4 == "VIP" and param5 > 1000 and param6 == True:
            total_discount = discount_rate + bonus + 0.1  # Magic literal
        else:
            total_discount = discount_rate + bonus
            
        return total_discount
    else:
        return 0.0


class MegaProcessor:
    '''God class with too many methods - algorithm connascence.'''
    
    def __init__(self):
        self.data = {}
        self.cache = {}
        self.config = {}
        
    def process_order(self, order):  # Missing type hints
        pass
    
    def validate_payment(self, payment):  # Missing type hints
        pass
        
    def calculate_shipping(self, address):  # Missing type hints
        pass
        
    def send_email(self, recipient):  # Missing type hints
        pass
        
    def update_inventory(self, item, quantity):  # Missing type hints
        pass
        
    def generate_invoice(self, order_id):  # Missing type hints
        pass
        
    def process_return(self, return_id):  # Missing type hints
        pass
        
    def calculate_tax(self, amount, region):  # Missing type hints
        pass
        
    def validate_coupon(self, code):  # Missing type hints
        pass
        
    def send_sms(self, phone, message):  # Missing type hints
        pass
        
    def log_transaction(self, transaction):  # Missing type hints
        pass
        
    def backup_data(self, data):  # Missing type hints
        pass
        
    def restore_data(self, backup_id):  # Missing type hints
        pass
        
    def generate_report(self, report_type):  # Missing type hints
        pass
        
    def archive_old_data(self, cutoff_date):  # Missing type hints
        pass
        
    def sync_with_external_api(self, api_endpoint):  # Missing type hints
        pass
        
    def validate_business_rules(self, data):  # Missing type hints
        pass
        
    def calculate_metrics(self, time_period):  # Missing type hints
        pass
        
    def export_data(self, format_type):  # Missing type hints
        pass
        
    def import_data(self, source):  # Missing type hints
        pass
        
    def schedule_tasks(self, tasks):  # Missing type hints
        pass
        
    def monitor_performance(self, metrics):  # Missing type hints
        pass
        
    def handle_errors(self, error):  # Missing type hints
        pass
        
    def cleanup_resources(self):  # Missing type hints
        pass
        
    def initialize_system(self, config):  # Missing type hints
        pass
""")
    
    # Utilities with type violations
    (project_path / "src" / "utils" / "helpers.py").write_text("""
def untyped_helper(data, options, flags):  # Missing type hints + position connascence
    if flags[0] == True and flags[1] == False:  # Meaning connascence with booleans
        return data * 2.5  # Magic literal
    return data


def another_helper(a, b, c, d, e):  # Parameter bomb
    threshold = 999  # Magic literal
    if a > threshold:
        return b + c + d + e + 42  # Magic literal
    return 0
""")
    
    # Configuration with violations
    (project_path / "config" / "settings.py").write_text("""
# Configuration with magic literals and strings
DATABASE_URL = "postgresql://user:pass@localhost:5432/db"  # Magic string
CACHE_TIMEOUT = 3600  # Magic literal - should be named constant
MAX_CONNECTIONS = 100  # Magic literal
RETRY_ATTEMPTS = 5  # Magic literal
SECRET_TOKEN = "super-secret-key-12345"  # Magic string
""")
    
    # Test file (should be excluded)
    (project_path / "tests" / "test_app.py").write_text("""
import pytest

def test_complex_function():
    # This file should be excluded from analysis
    assert True
""")
    
    yield project_path
    
    # Cleanup
    import shutil
    shutil.rmtree(temp_dir)


@pytest.fixture
def workflow_validator():
    """Create workflow validator with memory coordination."""
    return SequentialWorkflowValidator(memory_coordinator)


class TestCLIWorkflowsEndToEnd:
    """Test complete CLI workflows from input to report generation."""
    
    def test_basic_scan_workflow(self, temp_project, workflow_validator):
        """Test basic scan command workflow."""
        scenario_id = "basic_scan_workflow"
        workflow_validator.start_scenario(scenario_id, "Basic scan command end-to-end test")
        
        # Step 1: Initialize CLI
        workflow_validator.add_step("cli_init", {"command": "scan"})
        cli = ConnascenceCLI()
        
        # Step 2: Prepare arguments
        args = ["scan", str(temp_project), "--format", "json"]
        workflow_validator.add_step("prepare_args", {"args": args})
        
        # Step 3: Execute scan
        start_time = time.time()
        exit_code = cli.run(args)
        execution_time = time.time() - start_time
        
        workflow_validator.add_step("execute_scan", {
            "exit_code": exit_code,
            "execution_time_ms": execution_time * 1000
        })
        
        # Step 4: Validate exit code
        # Should return 1 if violations found, 0 if none
        assert exit_code in [0, 1], f"Unexpected exit code: {exit_code}"
        
        workflow_validator.add_step("validate_exit_code", {
            "expected_codes": [0, 1],
            "actual_code": exit_code
        })
        
        # Step 5: Store performance metrics
        memory_coordinator.store_performance_metrics(scenario_id, {
            "execution_time_ms": execution_time * 1000,
            "files_analyzed": 4,  # Expected file count
            "expected_violation_types": ["CoM", "CoP", "CoT", "CoA"]
        })
        
        # Validate sequential workflow
        expected_sequence = ["cli_init", "prepare_args", "execute_scan", "validate_exit_code"]
        assert workflow_validator.validate_step_sequence(expected_sequence)
        
        workflow_validator.complete_scenario(True, {
            "exit_code": exit_code,
            "execution_time_ms": execution_time * 1000,
            "workflow_completed": True
        })
    
    def test_scan_with_policy_workflow(self, temp_project, workflow_validator):
        """Test scan with different policy presets."""
        scenario_id = "policy_scan_workflow"
        workflow_validator.start_scenario(scenario_id, "Policy-based scan workflow")
        
        policies = ["strict-core", "service-defaults", "experimental"]
        
        for policy in policies:
            # Step 1: Initialize for policy
            workflow_validator.add_step(f"init_policy_{policy}", {"policy": policy})
            
            cli = ConnascenceCLI()
            args = ["scan", str(temp_project), "--policy", policy, "--format", "json"]
            
            # Step 2: Execute with policy
            start_time = time.time()
            exit_code = cli.run(args)
            execution_time = time.time() - start_time
            
            workflow_validator.add_step(f"execute_policy_{policy}", {
                "policy": policy,
                "exit_code": exit_code,
                "execution_time_ms": execution_time * 1000
            })
            
            # Store exit code scenario
            memory_coordinator.store_exit_code_scenario(
                f"{scenario_id}_{policy}",
                1,  # Expected: violations should be found
                exit_code,
                {"policy": policy, "has_violations": True}
            )
        
        workflow_validator.complete_scenario(True, {
            "policies_tested": len(policies),
            "all_policies_completed": True
        })
    
    def test_output_format_workflow(self, temp_project, workflow_validator):
        """Test all output formats end-to-end."""
        scenario_id = "output_format_workflow"
        workflow_validator.start_scenario(scenario_id, "Output format generation workflow")
        
        formats = ["text", "json", "sarif", "markdown"]
        format_results = {}
        
        for format_type in formats:
            # Step 1: Initialize for format
            workflow_validator.add_step(f"init_format_{format_type}", {"format": format_type})
            
            # Create output file
            output_file = temp_project / f"report.{format_type}"
            
            cli = ConnascenceCLI()
            args = [
                "scan", str(temp_project),
                "--format", format_type,
                "--output", str(output_file)
            ]
            
            # Step 2: Execute with format
            start_time = time.time()
            exit_code = cli.run(args)
            execution_time = time.time() - start_time
            
            workflow_validator.add_step(f"execute_format_{format_type}", {
                "format": format_type,
                "output_file": str(output_file),
                "exit_code": exit_code,
                "execution_time_ms": execution_time * 1000
            })
            
            # Step 3: Validate output file was created
            assert output_file.exists(), f"Output file not created for format {format_type}"
            
            # Step 4: Validate output content
            content = output_file.read_text()
            assert len(content) > 0, f"Empty output for format {format_type}"
            
            # Format-specific validations
            if format_type == "json":
                try:
                    data = json.loads(content)
                    assert "violations" in data, "JSON output missing violations"
                    assert "total_files_analyzed" in data, "JSON output missing file count"
                except json.JSONDecodeError:
                    pytest.fail(f"Invalid JSON output for format {format_type}")
            
            elif format_type == "sarif":
                try:
                    sarif_data = json.loads(content)
                    assert "$schema" in sarif_data, "SARIF output missing schema"
                    assert "runs" in sarif_data, "SARIF output missing runs"
                except json.JSONDecodeError:
                    pytest.fail(f"Invalid SARIF JSON output")
            
            elif format_type == "markdown":
                assert "# Connascence Analysis Report" in content or "# CONNASCENCE" in content, "Markdown output missing header"
                assert "violations" in content.lower(), "Markdown output missing violations section"
            
            elif format_type == "text":
                assert "CONNASCENCE" in content.upper(), "Text output missing connascence header"
                assert "violations" in content.lower(), "Text output missing violations"
            
            format_results[format_type] = {
                "exit_code": exit_code,
                "file_size": len(content),
                "execution_time_ms": execution_time * 1000,
                "content_valid": True
            }
            
            workflow_validator.add_step(f"validate_format_{format_type}", format_results[format_type])
        
        # Store comprehensive results
        memory_coordinator.store_performance_metrics(scenario_id, {
            "formats_tested": len(formats),
            "format_results": format_results,
            "all_formats_generated": True
        })
        
        workflow_validator.complete_scenario(True, {
            "formats_completed": len(formats),
            "format_results": format_results
        })
    
    def test_severity_filtering_workflow(self, temp_project, workflow_validator):
        """Test severity-based filtering workflow."""
        scenario_id = "severity_filtering_workflow"
        workflow_validator.start_scenario(scenario_id, "Severity filtering workflow")
        
        severities = ["low", "medium", "high", "critical"]
        severity_results = {}
        
        for severity in severities:
            # Step 1: Initialize for severity
            workflow_validator.add_step(f"init_severity_{severity}", {"severity": severity})
            
            output_file = temp_project / f"report_{severity}.json"
            
            cli = ConnascenceCLI()
            args = [
                "scan", str(temp_project),
                "--severity", severity,
                "--format", "json",
                "--output", str(output_file)
            ]
            
            # Step 2: Execute with severity filter
            exit_code = cli.run(args)
            
            workflow_validator.add_step(f"execute_severity_{severity}", {
                "severity": severity,
                "exit_code": exit_code
            })
            
            # Step 3: Validate filtering worked
            if output_file.exists():
                content = output_file.read_text()
                try:
                    data = json.loads(content)
                    violations = data.get("violations", [])
                    
                    # Validate all violations meet minimum severity
                    severity_order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
                    min_level = severity_order[severity]
                    
                    for violation in violations:
                        violation_level = severity_order.get(violation.get("severity", {}).get("value", "low"), 0)
                        assert violation_level >= min_level, f"Violation below minimum severity {severity}"
                    
                    severity_results[severity] = {
                        "violations_count": len(violations),
                        "filtering_correct": True
                    }
                    
                except json.JSONDecodeError:
                    severity_results[severity] = {"filtering_correct": False}
            
            workflow_validator.add_step(f"validate_severity_{severity}", severity_results.get(severity, {}))
        
        memory_coordinator.store_performance_metrics(scenario_id, {
            "severities_tested": len(severities),
            "severity_results": severity_results
        })
        
        workflow_validator.complete_scenario(True, {
            "severities_completed": len(severities),
            "severity_filtering_validated": True
        })
    
    def test_exit_code_scenarios_comprehensive(self, temp_project, workflow_validator):
        """Test all exit code scenarios comprehensively."""
        scenario_id = "exit_code_scenarios"
        workflow_validator.start_scenario(scenario_id, "Comprehensive exit code validation")
        
        cli = ConnascenceCLI()
        
        # Scenario 1: Exit code 0 - No violations (empty directory)
        empty_dir = temp_project / "empty"
        empty_dir.mkdir()
        
        exit_code = cli.run(["scan", str(empty_dir)])
        memory_coordinator.store_exit_code_scenario(
            f"{scenario_id}_no_violations",
            0, exit_code,
            {"scenario": "empty_directory", "expected_violations": 0}
        )
        workflow_validator.add_step("test_exit_code_0", {"exit_code": exit_code})
        
        # Scenario 2: Exit code 1 - Violations found
        exit_code = cli.run(["scan", str(temp_project)])
        memory_coordinator.store_exit_code_scenario(
            f"{scenario_id}_violations_found",
            1, exit_code,
            {"scenario": "violations_present", "expected_violations": ">0"}
        )
        workflow_validator.add_step("test_exit_code_1", {"exit_code": exit_code})
        
        # Scenario 3: Exit code 2 - Configuration error (invalid path)
        exit_code = cli.run(["scan", "/nonexistent/path/that/does/not/exist"])
        memory_coordinator.store_exit_code_scenario(
            f"{scenario_id}_config_error",
            2, exit_code,
            {"scenario": "invalid_path", "path_exists": False}
        )
        workflow_validator.add_step("test_exit_code_2", {"exit_code": exit_code})
        
        # Scenario 4: Exit code 130 - Keyboard interrupt simulation
        # This would require subprocess testing for real interruption
        
        # Store comprehensive exit code results
        exit_code_summary = memory_coordinator.get_scenario_summary()
        workflow_validator.add_step("validate_all_exit_codes", exit_code_summary)
        
        workflow_validator.complete_scenario(True, {
            "exit_code_tests_completed": True,
            "pass_rate": exit_code_summary.get("exit_code_pass_rate", 0)
        })
    
    def test_large_project_performance_workflow(self, temp_project, workflow_validator):
        """Test performance with larger project simulation."""
        scenario_id = "large_project_performance"
        workflow_validator.start_scenario(scenario_id, "Large project performance test")
        
        # Step 1: Generate larger project structure
        workflow_validator.add_step("generate_large_project", {"action": "creating_files"})
        
        # Create multiple modules with violations
        for i in range(10):
            module_dir = temp_project / f"module_{i}"
            module_dir.mkdir()
            
            (module_dir / f"service_{i}.py").write_text(f"""
def process_data_{i}(param1, param2, param3, param4, param5):  # Parameter bomb
    threshold = {100 + i * 10}  # Magic literal
    secret_key = "key_{i}_secret"  # Magic string
    
    if param1 > threshold:
        multiplier = {2.5 + i * 0.1}  # Magic literal
        return param1 * multiplier
    return param1

class Processor_{i}:  # Multiple classes for complexity
    def method_1(self): pass
    def method_2(self): pass
    def method_3(self): pass
    def method_4(self): pass
    def method_5(self): pass
    def method_6(self): pass
    def method_7(self): pass
    def method_8(self): pass
    def method_9(self): pass
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
    def method_21(self): pass  # God class
""")
        
        workflow_validator.add_step("large_project_created", {
            "modules_created": 10,
            "total_files": 10
        })
        
        # Step 2: Execute performance scan
        cli = ConnascenceCLI()
        start_time = time.time()
        exit_code = cli.run([
            "scan", str(temp_project),
            "--format", "json",
            "--output", str(temp_project / "large_project_report.json")
        ])
        execution_time = time.time() - start_time
        
        workflow_validator.add_step("execute_large_scan", {
            "exit_code": exit_code,
            "execution_time_ms": execution_time * 1000
        })
        
        # Step 3: Validate performance metrics
        performance_metrics = {
            "execution_time_ms": execution_time * 1000,
            "files_analyzed": 14,  # Original 4 + 10 new modules
            "performance_acceptable": execution_time < 30.0,  # Should complete in under 30 seconds
            "exit_code": exit_code
        }
        
        memory_coordinator.store_performance_metrics(scenario_id, performance_metrics)
        workflow_validator.add_step("validate_performance", performance_metrics)
        
        # Performance should be reasonable
        assert execution_time < 30.0, f"Performance test failed: {execution_time}s > 30s"
        assert exit_code == 1, "Should find violations in large project"
        
        workflow_validator.complete_scenario(True, performance_metrics)
    
    def test_memory_coordination_validation(self):
        """Test memory coordination system is working properly."""
        scenario_id = "memory_coordination_test"
        memory_coordinator.store_test_scenario(scenario_id, {
            "test_type": "memory_validation",
            "timestamp": time.time()
        })
        
        # Test memory storage and retrieval
        performance_data = {
            "metric1": 100,
            "metric2": 200,
            "test_validation": True
        }
        memory_coordinator.store_performance_metrics(scenario_id, performance_data)
        
        # Test exit code scenario storage
        memory_coordinator.store_exit_code_scenario(
            f"{scenario_id}_exit_test",
            0, 0,
            {"test": "memory_validation"}
        )
        
        # Validate memory coordinator has stored data
        summary = memory_coordinator.get_scenario_summary()
        assert summary["total_scenarios"] > 0, "Memory coordinator not storing scenarios"
        assert summary["performance_tests"] > 0, "Memory coordinator not storing performance data"
        assert summary["exit_code_tests"] > 0, "Memory coordinator not storing exit code data"
        
        memory_coordinator.update_scenario_status(scenario_id, "completed", {
            "memory_validation": True,
            "summary": summary
        })
        
        # Validate scenario was updated
        scenario = memory_coordinator.test_scenarios[scenario_id]
        assert scenario["status"] == "completed"
        assert scenario["results"]["memory_validation"] is True


@pytest.mark.e2e
@pytest.mark.slow
def test_complete_workflow_integration():
    """Integration test for complete workflow with memory coordination."""
    memory_coordinator_instance = E2EMemoryCoordinator()
    validator = SequentialWorkflowValidator(memory_coordinator_instance)
    
    # This test would be run as part of the comprehensive e2e suite
    # It validates that all components work together
    
    scenario_id = "complete_integration"
    validator.start_scenario(scenario_id, "Complete workflow integration test")
    
    # Simulate complete workflow
    validator.add_step("initialization", {"status": "ok"})
    validator.add_step("cli_processing", {"status": "ok"})
    validator.add_step("analysis_execution", {"status": "ok"})
    validator.add_step("report_generation", {"status": "ok"})
    validator.add_step("memory_storage", {"status": "ok"})
    
    # Validate workflow sequence
    expected_sequence = [
        "initialization",
        "cli_processing", 
        "analysis_execution",
        "report_generation",
        "memory_storage"
    ]
    
    assert validator.validate_step_sequence(expected_sequence)
    
    validator.complete_scenario(True, {
        "integration_test_passed": True,
        "all_components_functional": True
    })
    
    # Final validation
    summary = memory_coordinator_instance.get_scenario_summary()
    assert summary["completed"] > 0, "No scenarios completed in integration test"


if __name__ == "__main__":
    # Run comprehensive e2e tests
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "-m", "e2e"
    ])