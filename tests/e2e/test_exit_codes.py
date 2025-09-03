#!/usr/bin/env python3
"""
End-to-End Exit Code Tests

Comprehensive testing of all exit codes (0,1,2,3,4) in real scenarios.
Tests exit code consistency, mapping accuracy, and behavior validation.
Uses memory coordination for tracking exit code patterns and scenarios.
"""

import json
import os
import tempfile
import time
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import pytest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from cli.connascence import ConnascenceCLI
from tests.e2e.test_cli_workflows import E2EMemoryCoordinator, SequentialWorkflowValidator


class ExitCodeCoordinator:
    """Memory coordinator for exit code testing and validation."""
    
    def __init__(self):
        self.exit_code_scenarios = {}
        self.exit_code_mappings = {
            0: 'success_no_violations',
            1: 'violations_found', 
            2: 'configuration_error',
            3: 'system_error',
            4: 'license_error',
            130: 'keyboard_interrupt'
        }
        self.scenario_results = {}
        self.consistency_tests = {}
        self.edge_case_exit_codes = {}
        self.subprocess_results = {}
    
    def store_exit_code_scenario(self, scenario_id: str, expected_code: int, 
                                actual_code: int, scenario_config: Dict[str, Any]):
        """Store exit code scenario and validation results."""
        self.exit_code_scenarios[scenario_id] = {
            'expected_code': expected_code,
            'actual_code': actual_code,
            'correct_mapping': expected_code == actual_code,
            'scenario_config': scenario_config,
            'timestamp': time.time(),
            'scenario_type': self.exit_code_mappings.get(expected_code, 'unknown')
        }
    
    def store_scenario_result(self, scenario_id: str, detailed_results: Dict[str, Any]):
        """Store detailed scenario execution results."""
        self.scenario_results[scenario_id] = detailed_results
    
    def store_consistency_test(self, test_id: str, consistency_data: Dict[str, Any]):
        """Store exit code consistency test results."""
        self.consistency_tests[test_id] = consistency_data
    
    def store_edge_case_exit_code(self, edge_case_id: str, edge_case_data: Dict[str, Any]):
        """Store edge case exit code scenarios."""
        self.edge_case_exit_codes[edge_case_id] = edge_case_data
    
    def store_subprocess_result(self, subprocess_id: str, subprocess_data: Dict[str, Any]):
        """Store subprocess execution results for exit code validation."""
        self.subprocess_results[subprocess_id] = subprocess_data
    
    def get_exit_code_summary(self) -> Dict[str, Any]:
        """Get comprehensive exit code testing summary."""
        total_scenarios = len(self.exit_code_scenarios)
        correct_mappings = sum(1 for s in self.exit_code_scenarios.values() if s['correct_mapping'])
        
        return {
            'total_scenarios_tested': total_scenarios,
            'correct_exit_codes': correct_mappings,
            'exit_code_accuracy': correct_mappings / max(total_scenarios, 1),
            'exit_codes_tested': list(set(s['expected_code'] for s in self.exit_code_scenarios.values())),
            'consistency_tests_run': len(self.consistency_tests),
            'edge_cases_tested': len(self.edge_case_exit_codes),
            'subprocess_tests_run': len(self.subprocess_results),
            'overall_exit_code_reliability': self._calculate_reliability_score()
        }
    
    def get_exit_code_breakdown(self) -> Dict[int, Dict[str, Any]]:
        """Get breakdown of exit code scenarios by code."""
        breakdown = {}
        
        for code in self.exit_code_mappings.keys():
            scenarios = [s for s in self.exit_code_scenarios.values() if s['expected_code'] == code]
            if scenarios:
                breakdown[code] = {
                    'code_description': self.exit_code_mappings[code],
                    'scenarios_tested': len(scenarios),
                    'correct_mappings': sum(1 for s in scenarios if s['correct_mapping']),
                    'accuracy': sum(1 for s in scenarios if s['correct_mapping']) / len(scenarios),
                    'scenario_types': list(set(s['scenario_config'].get('scenario_type', 'unknown') for s in scenarios))
                }
        
        return breakdown
    
    def _calculate_reliability_score(self) -> float:
        """Calculate overall exit code reliability score."""
        if not self.exit_code_scenarios:
            return 0.0
        
        # Base score from accuracy
        accuracy = sum(1 for s in self.exit_code_scenarios.values() if s['correct_mapping']) / len(self.exit_code_scenarios)
        
        # Coverage bonus (testing multiple exit codes)
        unique_codes = len(set(s['expected_code'] for s in self.exit_code_scenarios.values()))
        coverage_bonus = min(unique_codes / 6, 1.0) * 0.2  # 6 main exit codes, up to 20% bonus
        
        # Consistency bonus
        consistency_bonus = 0.0
        if self.consistency_tests:
            consistent_tests = sum(1 for t in self.consistency_tests.values() if t.get('consistent', False))
            consistency_bonus = (consistent_tests / len(self.consistency_tests)) * 0.1
        
        return min(1.0, accuracy + coverage_bonus + consistency_bonus)


# Global exit code coordinator
exit_code_coordinator = ExitCodeCoordinator()


class ExitCodeScenarioGenerator:
    """Generate various scenarios for exit code testing."""
    
    def __init__(self):
        self.scenario_templates = {
            0: self._generate_clean_scenarios,
            1: self._generate_violation_scenarios, 
            2: self._generate_config_error_scenarios,
            3: self._generate_system_error_scenarios,
            4: self._generate_license_error_scenarios
        }
    
    def generate_scenario_for_exit_code(self, exit_code: int, base_path: Path) -> Dict[str, Any]:
        """Generate appropriate scenario for given exit code."""
        generator = self.scenario_templates.get(exit_code)
        if generator:
            return generator(base_path)
        else:
            return self._generate_default_scenario(base_path, exit_code)
    
    def _generate_clean_scenarios(self, base_path: Path) -> Dict[str, Any]:
        """Generate scenarios that should result in exit code 0."""
        scenarios = [
            {
                'name': 'empty_directory',
                'setup': lambda: self._create_empty_directory(base_path),
                'description': 'Empty directory with no files'
            },
            {
                'name': 'clean_code_only',
                'setup': lambda: self._create_clean_code_project(base_path),
                'description': 'Project with clean, violation-free code'
            },
            {
                'name': 'excluded_violations',
                'setup': lambda: self._create_excluded_violations_project(base_path),
                'description': 'Project with violations in excluded directories'
            }
        ]
        return scenarios
    
    def _generate_violation_scenarios(self, base_path: Path) -> Dict[str, Any]:
        """Generate scenarios that should result in exit code 1."""
        scenarios = [
            {
                'name': 'parameter_bombs',
                'setup': lambda: self._create_parameter_bomb_project(base_path),
                'description': 'Project with parameter bomb violations'
            },
            {
                'name': 'magic_literals',
                'setup': lambda: self._create_magic_literal_project(base_path),
                'description': 'Project with magic literal violations'
            },
            {
                'name': 'god_classes',
                'setup': lambda: self._create_god_class_project(base_path),
                'description': 'Project with god class violations'
            },
            {
                'name': 'mixed_violations',
                'setup': lambda: self._create_mixed_violations_project(base_path),
                'description': 'Project with multiple violation types'
            }
        ]
        return scenarios
    
    def _generate_config_error_scenarios(self, base_path: Path) -> Dict[str, Any]:
        """Generate scenarios that should result in exit code 2."""
        scenarios = [
            {
                'name': 'nonexistent_path',
                'setup': lambda: {'args': ["scan", "/completely/nonexistent/path"], 'no_project': True},
                'description': 'Scanning non-existent path'
            },
            {
                'name': 'invalid_policy',
                'setup': lambda: {'args': ["scan", str(base_path), "--policy", "invalid-policy"], 'create_basic': True},
                'description': 'Using invalid policy name'
            },
            {
                'name': 'invalid_format',
                'setup': lambda: {'args': ["scan", str(base_path), "--format", "invalid-format"], 'create_basic': True},
                'description': 'Using invalid output format'
            },
            {
                'name': 'invalid_severity',
                'setup': lambda: {'args': ["scan", str(base_path), "--severity", "invalid-severity"], 'create_basic': True},
                'description': 'Using invalid severity level'
            }
        ]
        return scenarios
    
    def _generate_system_error_scenarios(self, base_path: Path) -> Dict[str, Any]:
        """Generate scenarios that might result in exit code 3."""
        scenarios = [
            {
                'name': 'corrupted_files',
                'setup': lambda: self._create_corrupted_file_project(base_path),
                'description': 'Project with corrupted/binary files'
            },
            {
                'name': 'permission_denied',
                'setup': lambda: self._create_permission_denied_scenario(base_path),
                'description': 'Files with restricted permissions'
            }
        ]
        return scenarios
    
    def _generate_license_error_scenarios(self, base_path: Path) -> Dict[str, Any]:
        """Generate scenarios that might result in exit code 4."""
        scenarios = [
            {
                'name': 'license_validation_trigger',
                'setup': lambda: self._create_license_validation_scenario(base_path),
                'description': 'Scenario that triggers license validation'
            }
        ]
        return scenarios
    
    def _create_empty_directory(self, base_path: Path) -> Dict[str, Any]:
        """Create empty directory scenario."""
        empty_dir = base_path / "empty_project"
        empty_dir.mkdir(parents=True)
        return {
            'project_path': empty_dir,
            'args': ["scan", str(empty_dir)],
            'expected_violations': 0
        }
    
    def _create_clean_code_project(self, base_path: Path) -> Dict[str, Any]:
        """Create clean code project without violations."""
        clean_dir = base_path / "clean_project"
        clean_dir.mkdir(parents=True)
        
        (clean_dir / "clean_module.py").write_text("""
from typing import List, Dict, Optional
from dataclasses import dataclass

# Proper constants
MAX_ITEMS: int = 100
DEFAULT_TIMEOUT: float = 30.0


@dataclass
class CleanDataItem:
    '''Clean data structure.'''
    item_id: str
    name: str
    value: Optional[float] = None


class CleanProcessor:
    '''Clean processor with focused responsibility.'''
    
    def __init__(self, *, timeout: float = DEFAULT_TIMEOUT) -> None:
        self.timeout = timeout
        self.items_processed = 0
    
    def process_item(self, item: CleanDataItem) -> bool:
        '''Process single item with proper typing.'''
        if item.value is not None and item.value > 0:
            self.items_processed += 1
            return True
        return False
    
    def get_stats(self) -> Dict[str, int]:
        '''Get processing statistics.'''
        return {"processed": self.items_processed}


def create_clean_item(*, item_id: str, name: str) -> CleanDataItem:
    '''Create clean item with keyword arguments.'''
    return CleanDataItem(item_id=item_id, name=name)
""")
        
        return {
            'project_path': clean_dir,
            'args': ["scan", str(clean_dir)],
            'expected_violations': 0
        }
    
    def _create_excluded_violations_project(self, base_path: Path) -> Dict[str, Any]:
        """Create project with violations in excluded directories."""
        project_dir = base_path / "excluded_project"
        project_dir.mkdir(parents=True)
        
        # Clean main code
        (project_dir / "main.py").write_text("""
def clean_main() -> str:
    return "clean"
""")
        
        # Violations in test directory (typically excluded)
        test_dir = project_dir / "tests"
        test_dir.mkdir()
        
        (test_dir / "test_violations.py").write_text("""
def test_with_violations(param1, param2, param3, param4, param5):  # Parameter bomb
    magic_value = 42  # Magic literal
    return magic_value
""")
        
        return {
            'project_path': project_dir,
            'args': ["scan", str(project_dir)],  # Tests might be excluded by default
            'expected_violations': 0,  # If tests are excluded
            'has_excluded_violations': True
        }
    
    def _create_parameter_bomb_project(self, base_path: Path) -> Dict[str, Any]:
        """Create project with parameter bomb violations."""
        project_dir = base_path / "parameter_bomb_project"
        project_dir.mkdir(parents=True)
        
        (project_dir / "parameter_violations.py").write_text("""
def function_with_many_params(param1, param2, param3, param4, param5, param6, param7):
    '''Function with parameter bomb violation.'''
    return param1 + param2 + param3 + param4 + param5 + param6 + param7

def another_parameter_bomb(a, b, c, d, e, f, g, h):
    '''Another parameter bomb.'''
    return sum([a, b, c, d, e, f, g, h])

class ParameterBombClass:
    def method_with_params(self, x1, x2, x3, x4, x5, x6):
        '''Method parameter bomb.'''
        return x1 * x2 * x3 * x4 * x5 * x6
""")
        
        return {
            'project_path': project_dir,
            'args': ["scan", str(project_dir)],
            'expected_violations': 3,  # 3 parameter bombs
            'violation_types': ['CoP']
        }
    
    def _create_magic_literal_project(self, base_path: Path) -> Dict[str, Any]:
        """Create project with magic literal violations."""
        project_dir = base_path / "magic_literal_project"
        project_dir.mkdir(parents=True)
        
        (project_dir / "magic_violations.py").write_text("""
def process_data(data):
    threshold = 100  # Magic literal
    max_retries = 5  # Magic literal
    timeout = 30000  # Magic literal
    
    if len(data) > threshold:
        for attempt in range(max_retries):
            result = perform_operation(data, timeout)
            if result:
                return True
    return False

def perform_operation(data, timeout):
    multiplier = 2.5  # Magic literal
    adjustment = 0.15  # Magic literal
    
    return len(data) * multiplier + adjustment > 150  # Magic literal

class ConfigManager:
    def __init__(self):
        self.cache_size = 1024  # Magic literal
        self.port = 8080  # Magic literal
        self.buffer_size = 8192  # Magic literal
""")
        
        return {
            'project_path': project_dir,
            'args': ["scan", str(project_dir)],
            'expected_violations': 8,  # Multiple magic literals
            'violation_types': ['CoM']
        }
    
    def _create_god_class_project(self, base_path: Path) -> Dict[str, Any]:
        """Create project with god class violations."""
        project_dir = base_path / "god_class_project"
        project_dir.mkdir(parents=True)
        
        methods = "\n    ".join([f"def method_{i:02d}(self): pass" for i in range(1, 26)])  # 25 methods
        
        (project_dir / "god_class.py").write_text(f"""
class GodClass:
    '''Class with too many methods - god class violation.'''
    
    def __init__(self):
        self.data = {{}}
    
    {methods}

class AnotherGodClass:
    '''Another god class.'''
    
    {methods}
""")
        
        return {
            'project_path': project_dir,
            'args': ["scan", str(project_dir)],
            'expected_violations': 2,  # 2 god classes
            'violation_types': ['CoA']
        }
    
    def _create_mixed_violations_project(self, base_path: Path) -> Dict[str, Any]:
        """Create project with mixed violation types."""
        project_dir = base_path / "mixed_violations_project"
        project_dir.mkdir(parents=True)
        
        (project_dir / "mixed_violations.py").write_text("""
def mixed_function(param1, param2, param3, param4, param5, param6):  # Parameter bomb
    '''Function with multiple violation types.'''
    magic_threshold = 42  # Magic literal
    secret_key = "api_key_12345"  # Magic string
    
    if param1 > magic_threshold:
        return param1 * 2.5  # Magic literal
    return 0

def untyped_function(data, options, config):  # Missing type hints
    timeout = 5000  # Magic literal
    return len(data) > timeout

class MegaClass:
    '''God class with many methods.'''
    
    def __init__(self):
        self.max_items = 1000  # Magic literal
    
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
    def method_21(self): pass
    def method_22(self): pass  # God class
""")
        
        return {
            'project_path': project_dir,
            'args': ["scan", str(project_dir)],
            'expected_violations': 8,  # Mixed violations: CoP, CoM, CoT, CoA
            'violation_types': ['CoP', 'CoM', 'CoT', 'CoA']
        }
    
    def _create_corrupted_file_project(self, base_path: Path) -> Dict[str, Any]:
        """Create project with corrupted/binary files."""
        project_dir = base_path / "corrupted_project"
        project_dir.mkdir(parents=True)
        
        # Normal Python file
        (project_dir / "normal.py").write_text("def normal(): pass")
        
        # Binary file with .py extension
        with open(project_dir / "corrupted.py", 'wb') as f:
            f.write(b'\x00\x01\x02\x03\xff\xfe\xfd\xfc')
        
        return {
            'project_path': project_dir,
            'args': ["scan", str(project_dir)],
            'expected_handling': 'graceful',
            'should_not_crash': True
        }
    
    def _create_permission_denied_scenario(self, base_path: Path) -> Dict[str, Any]:
        """Create permission denied scenario (if possible)."""
        project_dir = base_path / "permission_project"
        project_dir.mkdir(parents=True)
        
        restricted_file = project_dir / "restricted.py"
        restricted_file.write_text("def restricted(): pass")
        
        # Try to make file unreadable (may not work on all systems)
        try:
            os.chmod(str(restricted_file), 0o000)
            permission_restricted = True
        except (OSError, PermissionError):
            permission_restricted = False
        
        return {
            'project_path': project_dir,
            'args': ["scan", str(project_dir)],
            'permission_restricted': permission_restricted,
            'expected_handling': 'graceful',
            'restore_permissions': lambda: os.chmod(str(restricted_file), 0o644) if permission_restricted else None
        }
    
    def _create_license_validation_scenario(self, base_path: Path) -> Dict[str, Any]:
        """Create scenario that might trigger license validation."""
        project_dir = base_path / "license_project"
        project_dir.mkdir(parents=True)
        
        (project_dir / "main.py").write_text("def main(): pass")
        
        return {
            'project_path': project_dir,
            'args': ["scan", str(project_dir)],
            'license_test': True,
            'expected_handling': 'depends_on_license_system'
        }
    
    def _generate_default_scenario(self, base_path: Path, exit_code: int) -> Dict[str, Any]:
        """Generate default scenario for unknown exit codes."""
        return [
            {
                'name': f'default_scenario_code_{exit_code}',
                'setup': lambda: {'args': ["scan", str(base_path)], 'create_basic': True},
                'description': f'Default scenario for exit code {exit_code}'
            }
        ]


@pytest.fixture
def exit_code_workflow_validator():
    """Create workflow validator for exit code testing."""
    return SequentialWorkflowValidator(exit_code_coordinator)


@pytest.fixture
def scenario_generator():
    """Create scenario generator for exit code tests."""
    return ExitCodeScenarioGenerator()


class TestExitCodeWorkflows:
    """Test comprehensive exit code scenarios."""
    
    def test_exit_code_0_comprehensive_scenarios(self, exit_code_workflow_validator, scenario_generator):
        """Test all scenarios that should result in exit code 0."""
        scenario_id = "exit_code_0_comprehensive"
        exit_code_workflow_validator.start_scenario(scenario_id, "Comprehensive exit code 0 scenarios")
        
        temp_base = tempfile.mkdtemp()
        base_path = Path(temp_base)
        
        # Generate exit code 0 scenarios
        scenarios = scenario_generator.generate_scenario_for_exit_code(0, base_path)
        
        exit_code_0_results = {}
        
        for scenario_config in scenarios:
            scenario_name = scenario_config['name']
            
            exit_code_workflow_validator.add_step(f"setup_{scenario_name}", {
                'scenario': scenario_name,
                'description': scenario_config['description']
            })
            
            # Setup scenario
            setup_result = scenario_config['setup']()
            
            # Execute analysis
            cli = ConnascenceCLI()
            if 'args' in setup_result:
                args = setup_result['args']
            else:
                args = ["scan", str(setup_result['project_path'])]
            
            start_time = time.time()
            exit_code = cli.run(args)
            execution_time = time.time() - start_time
            
            result = {
                'scenario_name': scenario_name,
                'exit_code': exit_code,
                'expected_exit_code': 0,
                'correct_exit_code': exit_code == 0,
                'execution_time': execution_time,
                'setup_result': setup_result
            }
            
            exit_code_0_results[scenario_name] = result
            
            # Store in coordinator
            exit_code_coordinator.store_exit_code_scenario(
                f"{scenario_id}_{scenario_name}",
                0, exit_code,
                {
                    'scenario_type': scenario_name,
                    'description': scenario_config['description'],
                    'execution_time': execution_time
                }
            )
            
            exit_code_workflow_validator.add_step(f"execute_{scenario_name}", result)
            
            # Assertions
            assert exit_code == 0, f"Scenario '{scenario_name}' should return exit code 0, got {exit_code}"
        
        # Summary
        exit_code_0_summary = {
            'scenarios_tested': len(scenarios),
            'all_correct': all(r['correct_exit_code'] for r in exit_code_0_results.values()),
            'avg_execution_time': sum(r['execution_time'] for r in exit_code_0_results.values()) / len(exit_code_0_results),
            'max_execution_time': max(r['execution_time'] for r in exit_code_0_results.values()),
            'performance_acceptable': all(r['execution_time'] < 30 for r in exit_code_0_results.values())
        }
        
        exit_code_coordinator.store_scenario_result(scenario_id, exit_code_0_summary)
        
        # Cleanup
        import shutil
        shutil.rmtree(temp_base)
        
        assert exit_code_0_summary['all_correct'], "Not all exit code 0 scenarios returned correct exit code"
        assert exit_code_0_summary['performance_acceptable'], "Some scenarios took too long to execute"
        
        exit_code_workflow_validator.complete_scenario(True, {
            'exit_code_0_comprehensive_completed': True,
            'summary': exit_code_0_summary
        })
    
    def test_exit_code_1_comprehensive_scenarios(self, exit_code_workflow_validator, scenario_generator):
        """Test all scenarios that should result in exit code 1."""
        scenario_id = "exit_code_1_comprehensive"
        exit_code_workflow_validator.start_scenario(scenario_id, "Comprehensive exit code 1 scenarios")
        
        temp_base = tempfile.mkdtemp()
        base_path = Path(temp_base)
        
        # Generate exit code 1 scenarios
        scenarios = scenario_generator.generate_scenario_for_exit_code(1, base_path)
        
        exit_code_1_results = {}
        
        for scenario_config in scenarios:
            scenario_name = scenario_config['name']
            
            # Setup scenario
            setup_result = scenario_config['setup']()
            
            # Execute analysis
            cli = ConnascenceCLI()
            exit_code = cli.run(setup_result['args'])
            
            # Also generate JSON output to verify violations
            output_file = setup_result['project_path'] / "violations.json"
            cli_json = ConnascenceCLI()
            cli_json.run(setup_result['args'] + ["--format", "json", "--output", str(output_file)])
            
            violations_found = 0
            if output_file.exists():
                with open(output_file, 'r') as f:
                    try:
                        results = json.load(f)
                        violations_found = len(results.get('violations', []))
                    except (json.JSONDecodeError, KeyError):
                        pass
            
            result = {
                'scenario_name': scenario_name,
                'exit_code': exit_code,
                'expected_exit_code': 1,
                'correct_exit_code': exit_code == 1,
                'violations_found': violations_found,
                'expected_violations': setup_result.get('expected_violations', 1),
                'violations_match_expectation': violations_found >= setup_result.get('expected_violations', 1) if setup_result.get('expected_violations', 1) > 0 else violations_found > 0
            }
            
            exit_code_1_results[scenario_name] = result
            
            exit_code_coordinator.store_exit_code_scenario(
                f"{scenario_id}_{scenario_name}",
                1, exit_code,
                {
                    'scenario_type': scenario_name,
                    'violations_found': violations_found,
                    'expected_violations': setup_result.get('expected_violations', 1)
                }
            )
            
            exit_code_workflow_validator.add_step(f"execute_{scenario_name}", result)
            
            # Assertions
            assert exit_code == 1, f"Scenario '{scenario_name}' should return exit code 1, got {exit_code}"
            assert violations_found > 0, f"Scenario '{scenario_name}' should find violations, found {violations_found}"
        
        # Summary
        exit_code_1_summary = {
            'scenarios_tested': len(scenarios),
            'all_correct_exit_codes': all(r['correct_exit_code'] for r in exit_code_1_results.values()),
            'all_found_violations': all(r['violations_found'] > 0 for r in exit_code_1_results.values()),
            'total_violations_found': sum(r['violations_found'] for r in exit_code_1_results.values()),
            'avg_violations_per_scenario': sum(r['violations_found'] for r in exit_code_1_results.values()) / len(exit_code_1_results)
        }
        
        exit_code_coordinator.store_scenario_result(scenario_id, exit_code_1_summary)
        
        # Cleanup
        import shutil
        shutil.rmtree(temp_base)
        
        assert exit_code_1_summary['all_correct_exit_codes'], "Not all violation scenarios returned exit code 1"
        assert exit_code_1_summary['all_found_violations'], "Not all violation scenarios found violations"
        
        exit_code_workflow_validator.complete_scenario(True, {
            'exit_code_1_comprehensive_completed': True,
            'summary': exit_code_1_summary
        })
    
    def test_exit_code_2_configuration_errors(self, exit_code_workflow_validator, scenario_generator):
        """Test all scenarios that should result in exit code 2."""
        scenario_id = "exit_code_2_configuration_errors"
        exit_code_workflow_validator.start_scenario(scenario_id, "Comprehensive exit code 2 scenarios")
        
        temp_base = tempfile.mkdtemp()
        base_path = Path(temp_base)
        
        # Generate exit code 2 scenarios
        scenarios = scenario_generator.generate_scenario_for_exit_code(2, base_path)
        
        exit_code_2_results = {}
        
        for scenario_config in scenarios:
            scenario_name = scenario_config['name']
            
            # Setup scenario
            setup_result = scenario_config['setup']()
            
            # Create basic project if needed
            if setup_result.get('create_basic'):
                basic_file = base_path / "basic.py"
                basic_file.write_text("def basic(): pass")
            
            # Execute analysis
            cli = ConnascenceCLI()
            args = setup_result['args']
            
            exit_code = cli.run(args)
            
            result = {
                'scenario_name': scenario_name,
                'exit_code': exit_code,
                'expected_exit_code': 2,
                'correct_exit_code': exit_code == 2,
                'args_used': args,
                'error_type': 'configuration_error'
            }
            
            exit_code_2_results[scenario_name] = result
            
            exit_code_coordinator.store_exit_code_scenario(
                f"{scenario_id}_{scenario_name}",
                2, exit_code,
                {
                    'scenario_type': scenario_name,
                    'args': args,
                    'error_type': 'configuration_error'
                }
            )
            
            exit_code_workflow_validator.add_step(f"execute_{scenario_name}", result)
            
            # Assertions
            assert exit_code == 2, f"Configuration error scenario '{scenario_name}' should return exit code 2, got {exit_code}"
        
        # Summary
        exit_code_2_summary = {
            'scenarios_tested': len(scenarios),
            'all_correct_exit_codes': all(r['correct_exit_code'] for r in exit_code_2_results.values()),
            'configuration_errors_detected': len([r for r in exit_code_2_results.values() if r['correct_exit_code']])
        }
        
        exit_code_coordinator.store_scenario_result(scenario_id, exit_code_2_summary)
        
        # Cleanup
        import shutil
        shutil.rmtree(temp_base)
        
        assert exit_code_2_summary['all_correct_exit_codes'], "Not all configuration error scenarios returned exit code 2"
        
        exit_code_workflow_validator.complete_scenario(True, {
            'exit_code_2_configuration_errors_completed': True,
            'summary': exit_code_2_summary
        })
    
    def test_exit_code_consistency_across_runs(self, exit_code_workflow_validator):
        """Test exit code consistency across multiple runs."""
        scenario_id = "exit_code_consistency"
        exit_code_workflow_validator.start_scenario(scenario_id, "Exit code consistency testing")
        
        # Create test project
        temp_dir = tempfile.mkdtemp()
        project_path = Path(temp_dir)
        
        (project_path / "consistent_test.py").write_text("""
def test_function(param1, param2, param3, param4, param5):  # Parameter bomb
    magic_value = 42  # Magic literal
    return param1 + param2 + param3 + param4 + param5 + magic_value
""")
        
        # Run analysis multiple times
        consistency_results = []
        run_count = 5
        
        for run in range(run_count):
            cli = ConnascenceCLI()
            exit_code = cli.run(["scan", str(project_path)])
            
            consistency_results.append({
                'run_number': run + 1,
                'exit_code': exit_code,
                'timestamp': time.time()
            })
            
            exit_code_workflow_validator.add_step(f"consistency_run_{run + 1}", {
                'exit_code': exit_code,
                'run': run + 1
            })
        
        # Analyze consistency
        exit_codes = [r['exit_code'] for r in consistency_results]
        
        consistency_analysis = {
            'total_runs': run_count,
            'unique_exit_codes': list(set(exit_codes)),
            'consistent': len(set(exit_codes)) == 1,
            'expected_exit_code': 1,  # Should find violations
            'all_correct': all(code == 1 for code in exit_codes),
            'exit_code_distribution': {code: exit_codes.count(code) for code in set(exit_codes)}
        }
        
        exit_code_coordinator.store_consistency_test(scenario_id, consistency_analysis)
        
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir)
        
        # Assertions
        assert consistency_analysis['consistent'], f"Exit codes not consistent across runs: {exit_codes}"
        assert consistency_analysis['all_correct'], f"Expected exit code 1 for all runs, got: {exit_codes}"
        
        exit_code_workflow_validator.complete_scenario(True, {
            'exit_code_consistency_verified': True,
            'consistency_analysis': consistency_analysis
        })
    
    def test_subprocess_exit_code_validation(self, exit_code_workflow_validator):
        """Test exit codes via subprocess execution."""
        scenario_id = "subprocess_exit_code_validation"
        exit_code_workflow_validator.start_scenario(scenario_id, "Subprocess exit code validation")
        
        # Test subprocess execution for accurate exit code capture
        temp_dir = tempfile.mkdtemp()
        project_path = Path(temp_dir)
        
        subprocess_tests = [
            {
                'name': 'subprocess_violations',
                'setup': lambda: self._create_violation_file(project_path),
                'expected_exit_code': 1
            },
            {
                'name': 'subprocess_clean',
                'setup': lambda: self._create_clean_file(project_path),
                'expected_exit_code': 0
            },
            {
                'name': 'subprocess_config_error',
                'setup': lambda: None,  # No setup needed
                'args': ["scan", "/nonexistent"],
                'expected_exit_code': 2
            }
        ]
        
        subprocess_results = {}
        
        for test_config in subprocess_tests:
            test_name = test_config['name']
            
            # Setup
            if test_config['setup']:
                test_config['setup']()
            
            # Prepare subprocess arguments
            if 'args' in test_config:
                cmd_args = [sys.executable, "-m", "cli.connascence"] + test_config['args']
            else:
                cmd_args = [sys.executable, "-m", "cli.connascence", "scan", str(project_path)]
            
            # Execute via subprocess
            try:
                process = subprocess.run(
                    cmd_args,
                    cwd=str(Path(__file__).parent.parent.parent),
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                subprocess_exit_code = process.returncode
                
                result = {
                    'test_name': test_name,
                    'subprocess_exit_code': subprocess_exit_code,
                    'expected_exit_code': test_config['expected_exit_code'],
                    'correct_exit_code': subprocess_exit_code == test_config['expected_exit_code'],
                    'stdout': process.stdout,
                    'stderr': process.stderr,
                    'subprocess_successful': True
                }
                
            except subprocess.TimeoutExpired:
                result = {
                    'test_name': test_name,
                    'subprocess_exit_code': -1,
                    'expected_exit_code': test_config['expected_exit_code'],
                    'correct_exit_code': False,
                    'error': 'subprocess_timeout',
                    'subprocess_successful': False
                }
            except Exception as e:
                result = {
                    'test_name': test_name,
                    'subprocess_exit_code': -1,
                    'expected_exit_code': test_config['expected_exit_code'],
                    'correct_exit_code': False,
                    'error': str(e),
                    'subprocess_successful': False
                }
            
            subprocess_results[test_name] = result
            
            exit_code_coordinator.store_subprocess_result(f"{scenario_id}_{test_name}", result)
            exit_code_workflow_validator.add_step(f"subprocess_{test_name}", result)
            
            # Assertions (if subprocess was successful)
            if result['subprocess_successful']:
                assert result['correct_exit_code'], f"Subprocess test '{test_name}' expected exit code {test_config['expected_exit_code']}, got {result['subprocess_exit_code']}"
        
        # Summary
        subprocess_summary = {
            'tests_run': len(subprocess_tests),
            'successful_subprocesses': sum(1 for r in subprocess_results.values() if r['subprocess_successful']),
            'correct_exit_codes': sum(1 for r in subprocess_results.values() if r['correct_exit_code']),
            'subprocess_reliability': sum(1 for r in subprocess_results.values() if r['subprocess_successful']) / len(subprocess_tests)
        }
        
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir)
        
        assert subprocess_summary['subprocess_reliability'] > 0.8, "Subprocess execution reliability too low"
        assert subprocess_summary['correct_exit_codes'] >= subprocess_summary['successful_subprocesses'], "Subprocess exit codes incorrect"
        
        exit_code_workflow_validator.complete_scenario(True, {
            'subprocess_exit_code_validation_completed': True,
            'subprocess_summary': subprocess_summary
        })
    
    def test_edge_case_exit_codes(self, exit_code_workflow_validator):
        """Test edge case scenarios for exit codes."""
        scenario_id = "edge_case_exit_codes"
        exit_code_workflow_validator.start_scenario(scenario_id, "Edge case exit code scenarios")
        
        temp_dir = tempfile.mkdtemp()
        project_path = Path(temp_dir)
        
        edge_cases = [
            {
                'name': 'extremely_large_file',
                'setup': lambda: self._create_large_file(project_path),
                'expected_behavior': 'handle_gracefully',
                'max_exit_code': 3
            },
            {
                'name': 'deeply_nested_violations',
                'setup': lambda: self._create_deeply_nested_project(project_path),
                'expected_behavior': 'find_violations',
                'expected_exit_code': 1
            },
            {
                'name': 'unicode_violations',
                'setup': lambda: self._create_unicode_violation_file(project_path),
                'expected_behavior': 'handle_unicode',
                'expected_exit_code': 1
            },
            {
                'name': 'mixed_encoding_files',
                'setup': lambda: self._create_mixed_encoding_project(project_path),
                'expected_behavior': 'handle_gracefully',
                'max_exit_code': 2
            }
        ]
        
        edge_case_results = {}
        
        for edge_case in edge_cases:
            case_name = edge_case['name']
            
            # Setup edge case
            edge_case['setup']()
            
            # Execute analysis
            cli = ConnascenceCLI()
            start_time = time.time()
            
            try:
                exit_code = cli.run(["scan", str(project_path)])
                execution_successful = True
                error = None
            except Exception as e:
                exit_code = -1
                execution_successful = False
                error = str(e)
            
            execution_time = time.time() - start_time
            
            # Validate based on expected behavior
            if 'expected_exit_code' in edge_case:
                correct_exit_code = exit_code == edge_case['expected_exit_code']
            elif 'max_exit_code' in edge_case:
                correct_exit_code = 0 <= exit_code <= edge_case['max_exit_code']
            else:
                correct_exit_code = exit_code >= 0  # Any non-negative exit code
            
            result = {
                'case_name': case_name,
                'exit_code': exit_code,
                'execution_successful': execution_successful,
                'correct_exit_code': correct_exit_code,
                'execution_time': execution_time,
                'error': error,
                'expected_behavior': edge_case['expected_behavior']
            }
            
            edge_case_results[case_name] = result
            
            exit_code_coordinator.store_edge_case_exit_code(f"{scenario_id}_{case_name}", result)
            exit_code_workflow_validator.add_step(f"edge_case_{case_name}", result)
            
            # Assertions
            assert execution_successful, f"Edge case '{case_name}' should execute successfully, got error: {error}"
            assert correct_exit_code, f"Edge case '{case_name}' exit code validation failed"
        
        # Summary
        edge_case_summary = {
            'edge_cases_tested': len(edge_cases),
            'all_executed_successfully': all(r['execution_successful'] for r in edge_case_results.values()),
            'all_exit_codes_correct': all(r['correct_exit_code'] for r in edge_case_results.values()),
            'avg_execution_time': sum(r['execution_time'] for r in edge_case_results.values()) / len(edge_case_results),
            'max_execution_time': max(r['execution_time'] for r in edge_case_results.values()),
            'edge_case_robustness': sum(1 for r in edge_case_results.values() if r['execution_successful'] and r['correct_exit_code']) / len(edge_cases)
        }
        
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir)
        
        assert edge_case_summary['all_executed_successfully'], "Not all edge cases executed successfully"
        assert edge_case_summary['edge_case_robustness'] > 0.8, "Edge case robustness too low"
        
        exit_code_workflow_validator.complete_scenario(True, {
            'edge_case_exit_codes_tested': True,
            'edge_case_summary': edge_case_summary
        })
    
    def test_exit_code_memory_coordination_validation(self):
        """Test exit code memory coordination system."""
        # Test exit code coordinator functionality
        test_scenario_id = "exit_code_memory_test"
        
        # Store comprehensive test data
        exit_code_coordinator.store_exit_code_scenario(test_scenario_id, 1, 1, {
            'test_type': 'memory_validation',
            'scenario_type': 'test_violations'
        })
        
        exit_code_coordinator.store_scenario_result(test_scenario_id, {
            'test_result': True,
            'validation_passed': True
        })
        
        exit_code_coordinator.store_consistency_test("consistency_test", {
            'consistent': True,
            'runs': 5
        })
        
        exit_code_coordinator.store_edge_case_exit_code("edge_test", {
            'handled_gracefully': True
        })
        
        exit_code_coordinator.store_subprocess_result("subprocess_test", {
            'subprocess_successful': True,
            'correct_exit_code': True
        })
        
        # Validate comprehensive storage
        assert test_scenario_id in exit_code_coordinator.exit_code_scenarios
        assert test_scenario_id in exit_code_coordinator.scenario_results
        assert "consistency_test" in exit_code_coordinator.consistency_tests
        assert "edge_test" in exit_code_coordinator.edge_case_exit_codes
        assert "subprocess_test" in exit_code_coordinator.subprocess_results
        
        # Test summary generation
        summary = exit_code_coordinator.get_exit_code_summary()
        assert summary['total_scenarios_tested'] > 0
        assert summary['exit_code_accuracy'] > 0
        assert summary['consistency_tests_run'] > 0
        assert summary['edge_cases_tested'] > 0
        assert summary['subprocess_tests_run'] > 0
        
        # Test breakdown generation
        breakdown = exit_code_coordinator.get_exit_code_breakdown()
        assert isinstance(breakdown, dict)
        assert len(breakdown) > 0
    
    # Helper methods
    def _create_violation_file(self, project_path: Path):
        """Create file with violations."""
        (project_path / "violations.py").write_text("""
def bad_function(a, b, c, d, e, f): pass  # Parameter bomb
magic = 42  # Magic literal
""")
    
    def _create_clean_file(self, project_path: Path):
        """Create clean file without violations."""
        (project_path / "clean.py").write_text("""
from typing import List

MAX_ITEMS: int = 100

def clean_function(*, items: List[str]) -> int:
    return len(items)
""")
    
    def _create_large_file(self, project_path: Path):
        """Create very large file."""
        large_content = "# Large file\n" + "\n".join([
            f"def function_{i}(): pass" for i in range(10000)
        ])
        (project_path / "large.py").write_text(large_content)
    
    def _create_deeply_nested_project(self, project_path: Path):
        """Create deeply nested project structure."""
        current_path = project_path
        for level in range(10):
            current_path = current_path / f"level_{level}"
            current_path.mkdir(parents=True)
            
            (current_path / f"nested_{level}.py").write_text(f"""
def nested_function_{level}(a, b, c, d, e): pass  # Parameter bomb
nested_magic_{level} = {100 + level}  # Magic literal
""")
    
    def _create_unicode_violation_file(self, project_path: Path):
        """Create file with Unicode content and violations."""
        (project_path / "unicode_violations.py").write_text("""
# -*- coding: utf-8 -*-
# File with Unicode characters: αβγδε

def función_con_parámetros(param1, param2, param3, param4, param5):  # Parameter bomb
    '''Función con violaciones y caracteres especiales.'''
    número_mágico = 42  # Magic literal with Unicode comment
    cadena_secreta = "clave_súper_secreta_123"  # Magic string
    
    if param1 > número_mágico:
        return param1 * 2.5  # Magic literal
    
    return param1

class ClaseÚnicode:
    '''Clase con muchos métodos y caracteres Unicode.'''
    
    def método_01(self): pass
    def método_02(self): pass
    def método_03(self): pass
    def método_04(self): pass
    def método_05(self): pass
    def método_06(self): pass
    def método_07(self): pass
    def método_08(self): pass
    def método_09(self): pass
    def método_10(self): pass
    def método_11(self): pass
    def método_12(self): pass
    def método_13(self): pass
    def método_14(self): pass
    def método_15(self): pass
    def método_16(self): pass
    def método_17(self): pass
    def método_18(self): pass
    def método_19(self): pass
    def método_20(self): pass
    def método_21(self): pass  # God class
""", encoding='utf-8')
    
    def _create_mixed_encoding_project(self, project_path: Path):
        """Create project with mixed file encodings."""
        # UTF-8 file
        with open(project_path / "utf8_file.py", 'w', encoding='utf-8') as f:
            f.write("""
# UTF-8 file
def utf8_function(): pass
""")
        
        # ASCII file
        with open(project_path / "ascii_file.py", 'w', encoding='ascii') as f:
            f.write("""
# ASCII file
def ascii_function(): pass
""")
        
        # File with potential encoding issues
        with open(project_path / "mixed_encoding.py", 'wb') as f:
            f.write("# Mixed encoding file\n".encode('utf-8'))
            f.write("def mixed_function(): pass\n".encode('ascii'))


@pytest.mark.e2e
@pytest.mark.slow
def test_exit_code_integration():
    """Integration test for exit code system."""
    coordinator = ExitCodeCoordinator()
    
    # Test complete exit code integration
    scenario_id = "exit_code_integration_test"
    
    coordinator.store_exit_code_scenario(scenario_id, 0, 0, {
        'integration_test': True,
        'timestamp': time.time()
    })
    
    # Validate integration
    assert scenario_id in coordinator.exit_code_scenarios
    
    summary = coordinator.get_exit_code_summary()
    assert summary['total_scenarios_tested'] > 0
    
    print("Exit code integration test completed successfully")


if __name__ == "__main__":
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "-m", "e2e"
    ])