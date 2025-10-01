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
End-to-End Memory Coordination System Tests

Tests the memory coordination infrastructure used across all e2e test modules.
Validates coordination between different test coordinators, data persistence,
cross-module scenario tracking, and comprehensive test result aggregation.
"""

from fixes.phase0.production_safe_assertions import ProductionAssert
import json
from pathlib import Path
import sys
import tempfile
import time
from typing import Any, Dict, List

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.e2e.test_cli_workflows import E2EMemoryCoordinator
from tests.e2e.test_enterprise_scale import EnterpriseScaleCoordinator
from tests.e2e.test_error_handling import ErrorHandlingCoordinator
from tests.e2e.test_exit_codes import ExitCodeCoordinator
from tests.e2e.test_performance import PerformanceBenchmarkCoordinator
from tests.e2e.test_report_generation import ReportGenerationCoordinator
from tests.e2e.test_repository_analysis import RepositoryAnalysisCoordinator


class MasterMemoryCoordinator:
    """Master coordinator that orchestrates all e2e test memory coordinators."""

    def __init__(self):
        # Initialize all specialized coordinators
        self.cli_coordinator = E2EMemoryCoordinator()
        self.repository_coordinator = RepositoryAnalysisCoordinator()
        self.report_coordinator = ReportGenerationCoordinator()
        self.enterprise_coordinator = EnterpriseScaleCoordinator()
        self.error_coordinator = ErrorHandlingCoordinator()
        self.exit_code_coordinator = ExitCodeCoordinator()
        self.performance_coordinator = PerformanceBenchmarkCoordinator()

        # Cross-module tracking
        self.cross_module_scenarios = {}
        self.integration_tests = {}
        self.global_metrics = {}
        self.test_execution_timeline = []

        # Data persistence tracking
        self.persistent_data_stores = {}
        self.data_validation_results = {}

    def register_cross_module_scenario(self, scenario_id: str,
                                     modules_involved: List[str],
                                     scenario_config: Dict[str, Any]):
        """Register a scenario that spans multiple test modules."""
        self.cross_module_scenarios[scenario_id] = {
            'modules_involved': modules_involved,
            'scenario_config': scenario_config,
            'start_time': time.time(),
            'status': 'initialized',
            'module_results': {}
        }

    def update_cross_module_result(self, scenario_id: str, module_name: str,
                                 module_result: Dict[str, Any]):
        """Update result from a specific module for cross-module scenario."""
        if scenario_id in self.cross_module_scenarios:
            self.cross_module_scenarios[scenario_id]['module_results'][module_name] = module_result

            # Check if all modules have reported
            expected_modules = set(self.cross_module_scenarios[scenario_id]['modules_involved'])
            completed_modules = set(self.cross_module_scenarios[scenario_id]['module_results'].keys())

            if expected_modules == completed_modules:
                self.cross_module_scenarios[scenario_id]['status'] = 'completed'
                self.cross_module_scenarios[scenario_id]['completion_time'] = time.time()

    def store_integration_test_result(self, test_id: str, integration_data: Dict[str, Any]):
        """Store integration test results that involve multiple coordinators."""

        ProductionAssert.not_none(test_id, 'test_id')

        ProductionAssert.not_none(integration_data, 'integration_data')
        ProductionAssert.not_none(test_id, 'test_id')

        ProductionAssert.not_none(integration_data, 'integration_data')        self.integration_tests[test_id] = {
            'data': integration_data,
            'timestamp': time.time(),
            'coordinators_involved': self._detect_coordinators_involved(integration_data)
        }

    def record_test_execution_event(self, event_type: str, module: str,
                                  test_name: str, event_data: Dict[str, Any]):
        """Record test execution events for timeline analysis."""
        event = {
            'timestamp': time.time(),
            'event_type': event_type,
            'module': module,
            'test_name': test_name,
            'data': event_data
        }
        self.test_execution_timeline.append(event)

    def validate_data_consistency(self) -> Dict[str, Any]:
        """Validate data consistency across all coordinators."""
        validation_results = {
            'cli_coordinator': self._validate_coordinator_data(self.cli_coordinator),
            'repository_coordinator': self._validate_coordinator_data(self.repository_coordinator),
            'report_coordinator': self._validate_coordinator_data(self.report_coordinator),
            'enterprise_coordinator': self._validate_coordinator_data(self.enterprise_coordinator),
            'error_coordinator': self._validate_coordinator_data(self.error_coordinator),
            'exit_code_coordinator': self._validate_coordinator_data(self.exit_code_coordinator),
            'performance_coordinator': self._validate_coordinator_data(self.performance_coordinator),
            'cross_module_consistency': self._validate_cross_module_consistency(),
            'overall_consistency_score': 0.0
        }

        # Calculate overall consistency score
        individual_scores = [
            v.get('consistency_score', 0.0) for v in validation_results.values()
            if isinstance(v, dict) and 'consistency_score' in v
        ]

        if individual_scores:
            validation_results['overall_consistency_score'] = sum(individual_scores) / len(individual_scores)

        self.data_validation_results = validation_results
        return validation_results

    def generate_comprehensive_summary(self) -> Dict[str, Any]:
        """Generate comprehensive summary across all coordinators."""
        summary = {
            'timestamp': time.time(),
            'coordinator_summaries': {},
            'cross_module_scenarios': len(self.cross_module_scenarios),
            'integration_tests': len(self.integration_tests),
            'test_execution_events': len(self.test_execution_timeline),
            'data_consistency': self.data_validation_results.get('overall_consistency_score', 0.0),
            'global_metrics': self._calculate_global_metrics(),
            'coverage_analysis': self._analyze_test_coverage(),
            'performance_overview': self._generate_performance_overview()
        }

        # Get summaries from each coordinator
        coordinators = {
            'cli': self.cli_coordinator,
            'repository': self.repository_coordinator,
            'report': self.report_coordinator,
            'enterprise': self.enterprise_coordinator,
            'error': self.error_coordinator,
            'exit_code': self.exit_code_coordinator,
            'performance': self.performance_coordinator
        }

        for name, coordinator in coordinators.items():
            try:
                if hasattr(coordinator, 'get_scenario_summary'):
                    summary['coordinator_summaries'][name] = coordinator.get_scenario_summary()
                elif hasattr(coordinator, 'get_enterprise_summary'):
                    summary['coordinator_summaries'][name] = coordinator.get_enterprise_summary()
                elif hasattr(coordinator, 'get_report_summary'):
                    summary['coordinator_summaries'][name] = coordinator.get_report_summary()
                elif hasattr(coordinator, 'get_error_handling_summary'):
                    summary['coordinator_summaries'][name] = coordinator.get_error_handling_summary()
                elif hasattr(coordinator, 'get_exit_code_summary'):
                    summary['coordinator_summaries'][name] = coordinator.get_exit_code_summary()
                elif hasattr(coordinator, 'get_performance_summary'):
                    summary['coordinator_summaries'][name] = coordinator.get_performance_summary()
                else:
                    summary['coordinator_summaries'][name] = {'status': 'summary_method_not_found'}
            except Exception as e:
                summary['coordinator_summaries'][name] = {'error': str(e)}

        return summary

    def export_coordination_data(self, export_path: Path) -> Dict[str, Any]:
        """Export all coordination data to files for analysis."""
        export_results = {
            'export_path': str(export_path),
            'export_timestamp': time.time(),
            'files_created': [],
            'export_summary': {}
        }

        # Ensure export directory exists
        export_path.mkdir(parents=True, exist_ok=True)

        # Export data from each coordinator
        coordinator_exports = {
            'cli_coordinator_data': self._export_coordinator_data(self.cli_coordinator),
            'repository_coordinator_data': self._export_coordinator_data(self.repository_coordinator),
            'report_coordinator_data': self._export_coordinator_data(self.report_coordinator),
            'enterprise_coordinator_data': self._export_coordinator_data(self.enterprise_coordinator),
            'error_coordinator_data': self._export_coordinator_data(self.error_coordinator),
            'exit_code_coordinator_data': self._export_coordinator_data(self.exit_code_coordinator),
            'performance_coordinator_data': self._export_coordinator_data(self.performance_coordinator),
            'cross_module_scenarios': self.cross_module_scenarios,
            'integration_tests': self.integration_tests,
            'test_execution_timeline': self.test_execution_timeline[-100:],  # Last 100 events
            'comprehensive_summary': self.generate_comprehensive_summary()
        }

        # Write each coordinator's data to separate files
        for filename, data in coordinator_exports.items():
            file_path = export_path / f"{filename}.json"
            try:
                with open(file_path, 'w') as f:
                    json.dump(data, f, indent=2, default=str)
                export_results['files_created'].append(str(file_path))
            except Exception as e:
                export_results['export_summary'][filename] = f"Export failed: {str(e)}"

        export_results['export_summary']['total_files_created'] = len(export_results['files_created'])
        export_results['export_summary']['export_successful'] = len(export_results['files_created']) > 0

        return export_results

    # Helper methods
    def _detect_coordinators_involved(self, integration_data: Dict[str, Any]) -> List[str]:
        """Detect which coordinators are involved in integration data."""
        involved = []

        # Check for indicators of different coordinator types
        if any(key in integration_data for key in ['cli_workflow', 'workflow_steps', 'command']):
            involved.append('cli')
        if any(key in integration_data for key in ['repository', 'framework', 'analysis_patterns']):
            involved.append('repository')
        if any(key in integration_data for key in ['report', 'format', 'sarif', 'json']):
            involved.append('report')
        if any(key in integration_data for key in ['enterprise', 'scale', 'microservices']):
            involved.append('enterprise')
        if any(key in integration_data for key in ['error', 'exit_code', 'exception']):
            involved.append('error')
        if any(key in integration_data for key in ['performance', 'benchmark', 'memory']):
            involved.append('performance')

        return involved

    def _validate_coordinator_data(self, coordinator) -> Dict[str, Any]:
        """Validate data consistency within a single coordinator."""
        validation_result = {
            'coordinator_type': type(coordinator).__name__,
            'data_structures_found': [],
            'data_integrity_checks': {},
            'consistency_score': 0.0
        }

        # Check common data structures
        common_attributes = ['test_scenarios', 'scenarios', 'benchmark_results', 'error_scenarios']

        for attr in common_attributes:
            if hasattr(coordinator, attr):
                attr_value = getattr(coordinator, attr)
                validation_result['data_structures_found'].append(attr)

                # Basic integrity checks
                if isinstance(attr_value, dict):
                    validation_result['data_integrity_checks'][attr] = {
                        'is_dict': True,
                        'entry_count': len(attr_value),
                        'has_entries': len(attr_value) > 0,
                        'keys_are_strings': all(isinstance(k, str) for k in attr_value),
                        'values_are_dicts': all(isinstance(v, dict) for v in attr_value.values())
                    }
                else:
                    validation_result['data_integrity_checks'][attr] = {
                        'is_dict': False,
                        'type': type(attr_value).__name__
                    }

        # Calculate consistency score
        integrity_scores = []
        for checks in validation_result['data_integrity_checks'].values():
            if checks.get('is_dict', False):
                score = sum([
                    0.25 if checks.get('has_entries', False) else 0,
                    0.25 if checks.get('keys_are_strings', False) else 0,
                    0.25 if checks.get('values_are_dicts', False) else 0,
                    0.25  # Base score for being a dict
                ])
                integrity_scores.append(score)

        if integrity_scores:
            validation_result['consistency_score'] = sum(integrity_scores) / len(integrity_scores)
        else:
            validation_result['consistency_score'] = 0.5  # Neutral score if no data structures found

        return validation_result

    def _validate_cross_module_consistency(self) -> Dict[str, Any]:
        """Validate consistency across modules."""
        return {
            'cross_module_scenarios_completed': sum(1 for s in self.cross_module_scenarios.values() if s['status'] == 'completed'),
            'total_cross_module_scenarios': len(self.cross_module_scenarios),
            'completion_rate': (sum(1 for s in self.cross_module_scenarios.values() if s['status'] == 'completed') /
                              max(len(self.cross_module_scenarios), 1)),
            'integration_tests_count': len(self.integration_tests),
            'timeline_events_count': len(self.test_execution_timeline),
            'consistency_indicators': {
                'all_scenarios_have_results': all(
                    len(s.get('module_results', {})) > 0
                    for s in self.cross_module_scenarios.values()
                ),
                'timeline_chronological': self._check_timeline_chronology(),
                'integration_tests_complete': len(self.integration_tests) > 0
            }
        }

    def _check_timeline_chronology(self) -> bool:
        """Check if timeline events are in chronological order."""
        if len(self.test_execution_timeline) < 2:
            return True

        timestamps = [event['timestamp'] for event in self.test_execution_timeline]
        return timestamps == sorted(timestamps)

    def _calculate_global_metrics(self) -> Dict[str, Any]:
        """Calculate global metrics across all coordinators."""
        return {
            'total_coordinators': 7,
            'active_coordinators': self._count_active_coordinators(),
            'total_test_scenarios': self._count_total_scenarios(),
            'cross_module_integration': len(self.cross_module_scenarios),
            'data_consistency_score': self.data_validation_results.get('overall_consistency_score', 0.0),
            'test_execution_events': len(self.test_execution_timeline),
            'coverage_completeness': self._calculate_coverage_completeness()
        }

    def _count_active_coordinators(self) -> int:
        """Count coordinators with data."""
        active_count = 0
        coordinators = [
            self.cli_coordinator, self.repository_coordinator, self.report_coordinator,
            self.enterprise_coordinator, self.error_coordinator, self.exit_code_coordinator,
            self.performance_coordinator
        ]

        for coordinator in coordinators:
            # Check if coordinator has any data
            has_data = False
            for attr in dir(coordinator):
                if not attr.startswith('_'):
                    value = getattr(coordinator, attr, None)
                    if isinstance(value, dict) and len(value) > 0:
                        has_data = True
                        break

            if has_data:
                active_count += 1

        return active_count

    def _count_total_scenarios(self) -> int:
        """Count total scenarios across all coordinators."""
        total = 0

        coordinators = [
            self.cli_coordinator, self.repository_coordinator, self.report_coordinator,
            self.enterprise_coordinator, self.error_coordinator, self.exit_code_coordinator,
            self.performance_coordinator
        ]

        for coordinator in coordinators:
            for attr in dir(coordinator):
                if 'scenario' in attr.lower() and not attr.startswith('_'):
                    value = getattr(coordinator, attr, None)
                    if isinstance(value, dict):
                        total += len(value)

        return total

    def _analyze_test_coverage(self) -> Dict[str, Any]:
        """Analyze test coverage across modules."""
        return {
            'modules_with_tests': self._count_modules_with_tests(),
            'test_types_covered': self._identify_covered_test_types(),
            'coverage_gaps': self._identify_coverage_gaps(),
            'coverage_percentage': self._calculate_coverage_percentage()
        }

    def _count_modules_with_tests(self) -> int:
        """Count modules that have test data."""
        return self._count_active_coordinators()

    def _identify_covered_test_types(self) -> List[str]:
        """Identify types of tests covered."""
        covered_types = []

        if self._coordinator_has_data(self.cli_coordinator):
            covered_types.append('cli_workflows')
        if self._coordinator_has_data(self.repository_coordinator):
            covered_types.append('repository_analysis')
        if self._coordinator_has_data(self.report_coordinator):
            covered_types.append('report_generation')
        if self._coordinator_has_data(self.enterprise_coordinator):
            covered_types.append('enterprise_scale')
        if self._coordinator_has_data(self.error_coordinator):
            covered_types.append('error_handling')
        if self._coordinator_has_data(self.exit_code_coordinator):
            covered_types.append('exit_codes')
        if self._coordinator_has_data(self.performance_coordinator):
            covered_types.append('performance')

        return covered_types

    def _coordinator_has_data(self, coordinator) -> bool:
        """Check if coordinator has any test data."""
        for attr in dir(coordinator):
            if not attr.startswith('_'):
                value = getattr(coordinator, attr, None)
                if isinstance(value, dict) and len(value) > 0:
                    return True
        return False

    def _identify_coverage_gaps(self) -> List[str]:
        """Identify gaps in test coverage."""
        expected_types = [
            'cli_workflows', 'repository_analysis', 'report_generation',
            'enterprise_scale', 'error_handling', 'exit_codes', 'performance'
        ]

        covered_types = self._identify_covered_test_types()

        return [t for t in expected_types if t not in covered_types]

    def _calculate_coverage_percentage(self) -> float:
        """Calculate coverage percentage."""
        expected_types = 7  # Total test types
        covered_types = len(self._identify_covered_test_types())

        return (covered_types / expected_types) * 100.0

    def _calculate_coverage_completeness(self) -> float:
        """Calculate overall coverage completeness."""
        return self._calculate_coverage_percentage() / 100.0

    def _generate_performance_overview(self) -> Dict[str, Any]:
        """Generate performance overview from performance coordinator."""
        if hasattr(self.performance_coordinator, 'get_performance_summary'):
            try:
                return self.performance_coordinator.get_performance_summary()
            except Exception as e:
                return {'error': f'Failed to get performance summary: {str(e)}'}

        return {'status': 'performance_coordinator_not_available'}

    def _export_coordinator_data(self, coordinator) -> Dict[str, Any]:
        """Export data from a single coordinator."""
        exported_data = {
            'coordinator_type': type(coordinator).__name__,
            'export_timestamp': time.time(),
            'data': {}
        }

        # Export all non-private attributes that contain data
        for attr_name in dir(coordinator):
            if not attr_name.startswith('_') and not callable(getattr(coordinator, attr_name)):
                attr_value = getattr(coordinator, attr_name)
                if isinstance(attr_value, (dict, list)) and attr_value:
                    exported_data['data'][attr_name] = attr_value

        return exported_data


@pytest.fixture
def master_coordinator():
    """Create master memory coordinator for testing."""
    return MasterMemoryCoordinator()


class TestMemoryCoordinationSystem:
    """Test the memory coordination infrastructure."""

    def test_master_coordinator_initialization(self, master_coordinator):
        """Test master coordinator initialization and setup."""
        # Verify all coordinators are initialized
        assert isinstance(master_coordinator.cli_coordinator, E2EMemoryCoordinator)
        assert isinstance(master_coordinator.repository_coordinator, RepositoryAnalysisCoordinator)
        assert isinstance(master_coordinator.report_coordinator, ReportGenerationCoordinator)
        assert isinstance(master_coordinator.enterprise_coordinator, EnterpriseScaleCoordinator)
        assert isinstance(master_coordinator.error_coordinator, ErrorHandlingCoordinator)
        assert isinstance(master_coordinator.exit_code_coordinator, ExitCodeCoordinator)
        assert isinstance(master_coordinator.performance_coordinator, PerformanceBenchmarkCoordinator)

        # Verify tracking structures are initialized
        assert isinstance(master_coordinator.cross_module_scenarios, dict)
        assert isinstance(master_coordinator.integration_tests, dict)
        assert isinstance(master_coordinator.global_metrics, dict)
        assert isinstance(master_coordinator.test_execution_timeline, list)

    def test_cross_module_scenario_tracking(self, master_coordinator):
        """Test cross-module scenario registration and tracking."""
        scenario_id = "test_cross_module_scenario"
        modules_involved = ["cli", "repository", "report"]
        scenario_config = {
            'test_type': 'integration',
            'description': 'Test cross-module integration'
        }

        # Register cross-module scenario
        master_coordinator.register_cross_module_scenario(
            scenario_id, modules_involved, scenario_config
        )

        # Verify scenario was registered
        assert scenario_id in master_coordinator.cross_module_scenarios
        scenario = master_coordinator.cross_module_scenarios[scenario_id]
        assert scenario['modules_involved'] == modules_involved
        assert scenario['scenario_config'] == scenario_config
        assert scenario['status'] == 'initialized'

        # Update results from modules
        for module in modules_involved:
            module_result = {
                'module': module,
                'status': 'completed',
                'test_result': True,
                'timestamp': time.time()
            }
            master_coordinator.update_cross_module_result(scenario_id, module, module_result)

        # Verify scenario completion
        updated_scenario = master_coordinator.cross_module_scenarios[scenario_id]
        assert updated_scenario['status'] == 'completed'
        assert len(updated_scenario['module_results']) == len(modules_involved)
        assert all(module in updated_scenario['module_results'] for module in modules_involved)

    def test_integration_test_result_storage(self, master_coordinator):
        """Test integration test result storage."""
        test_id = "test_integration_result"
        integration_data = {
            'cli_workflow': True,
            'repository': 'test_repo',
            'report': 'sarif',
            'performance': {'execution_time': 5000},
            'test_passed': True
        }

        # Store integration test result
        master_coordinator.store_integration_test_result(test_id, integration_data)

        # Verify storage
        assert test_id in master_coordinator.integration_tests
        stored_test = master_coordinator.integration_tests[test_id]
        assert stored_test['data'] == integration_data
        assert 'timestamp' in stored_test
        assert 'coordinators_involved' in stored_test

        # Verify coordinator detection
        involved_coordinators = stored_test['coordinators_involved']
        expected_coordinators = ['cli', 'repository', 'report', 'performance']
        assert all(coordinator in involved_coordinators for coordinator in expected_coordinators)

    def test_test_execution_timeline_tracking(self, master_coordinator):
        """Test test execution timeline tracking."""
        # Record multiple events
        events = [
            ('start', 'cli', 'test_scan_workflow', {'status': 'started'}),
            ('progress', 'cli', 'test_scan_workflow', {'step': 'analysis'}),
            ('complete', 'cli', 'test_scan_workflow', {'status': 'completed'}),
            ('start', 'repository', 'test_django_analysis', {'status': 'started'}),
            ('complete', 'repository', 'test_django_analysis', {'status': 'completed'})
        ]

        for event_type, module, test_name, event_data in events:
            master_coordinator.record_test_execution_event(event_type, module, test_name, event_data)

        # Verify timeline tracking
        timeline = master_coordinator.test_execution_timeline
        assert len(timeline) == len(events)

        # Verify event structure
        for i, event in enumerate(timeline):
            assert event['event_type'] == events[i][0]
            assert event['module'] == events[i][1]
            assert event['test_name'] == events[i][2]
            assert event['data'] == events[i][3]
            assert 'timestamp' in event

        # Verify chronological order
        timestamps = [event['timestamp'] for event in timeline]
        assert timestamps == sorted(timestamps)

    def test_individual_coordinator_data_storage(self, master_coordinator):
        """Test data storage in individual coordinators."""
        # Store test data in each coordinator type

        # CLI coordinator
        master_coordinator.cli_coordinator.store_test_scenario("cli_test", {
            'scenario': 'cli_workflow_test'
        })

        # Repository coordinator
        master_coordinator.repository_coordinator.store_repository_profile("repo_test", {
            'type': 'django_project'
        })

        # Report coordinator
        master_coordinator.report_coordinator.store_report_metadata("report_test", {
            'format': 'sarif'
        })

        # Enterprise coordinator
        master_coordinator.enterprise_coordinator.store_enterprise_project("enterprise_test", {
            'scale': 'large'
        })

        # Error coordinator
        master_coordinator.error_coordinator.store_error_scenario("error_test", {
            'error_type': 'configuration'
        })

        # Exit code coordinator
        master_coordinator.exit_code_coordinator.store_exit_code_scenario("exit_test", 1, 1, {
            'scenario': 'violations_found'
        })

        # Performance coordinator
        master_coordinator.performance_coordinator.store_benchmark_result("perf_test", {
            'execution_time_ms': 5000
        })

        # Verify data was stored
        assert "cli_test" in master_coordinator.cli_coordinator.test_scenarios
        assert "repo_test" in master_coordinator.repository_coordinator.repository_profiles
        assert "report_test" in master_coordinator.report_coordinator.report_metadata
        assert "enterprise_test" in master_coordinator.enterprise_coordinator.enterprise_projects
        assert "error_test" in master_coordinator.error_coordinator.error_scenarios
        assert "exit_test" in master_coordinator.exit_code_coordinator.exit_code_scenarios
        assert "perf_test" in master_coordinator.performance_coordinator.benchmark_results

    def test_data_consistency_validation(self, master_coordinator):
        """Test data consistency validation across coordinators."""
        # Add test data to multiple coordinators
        self.test_individual_coordinator_data_storage(master_coordinator)

        # Validate data consistency
        validation_results = master_coordinator.validate_data_consistency()

        # Verify validation structure
        assert 'cli_coordinator' in validation_results
        assert 'repository_coordinator' in validation_results
        assert 'report_coordinator' in validation_results
        assert 'enterprise_coordinator' in validation_results
        assert 'error_coordinator' in validation_results
        assert 'exit_code_coordinator' in validation_results
        assert 'performance_coordinator' in validation_results
        assert 'cross_module_consistency' in validation_results
        assert 'overall_consistency_score' in validation_results

        # Verify consistency scores
        assert 0.0 <= validation_results['overall_consistency_score'] <= 1.0

        # Verify each coordinator validation
        for coordinator_name in ['cli_coordinator', 'repository_coordinator', 'report_coordinator',
                               'enterprise_coordinator', 'error_coordinator', 'exit_code_coordinator',
                               'performance_coordinator']:
            coord_validation = validation_results[coordinator_name]
            assert 'coordinator_type' in coord_validation
            assert 'data_structures_found' in coord_validation
            assert 'data_integrity_checks' in coord_validation
            assert 'consistency_score' in coord_validation
            assert 0.0 <= coord_validation['consistency_score'] <= 1.0

    def test_comprehensive_summary_generation(self, master_coordinator):
        """Test comprehensive summary generation."""
        # Add test data
        self.test_individual_coordinator_data_storage(master_coordinator)
        self.test_cross_module_scenario_tracking(master_coordinator)
        self.test_integration_test_result_storage(master_coordinator)

        # Generate comprehensive summary
        summary = master_coordinator.generate_comprehensive_summary()

        # Verify summary structure
        assert 'timestamp' in summary
        assert 'coordinator_summaries' in summary
        assert 'cross_module_scenarios' in summary
        assert 'integration_tests' in summary
        assert 'test_execution_events' in summary
        assert 'data_consistency' in summary
        assert 'global_metrics' in summary
        assert 'coverage_analysis' in summary
        assert 'performance_overview' in summary

        # Verify coordinator summaries
        coordinator_summaries = summary['coordinator_summaries']
        expected_coordinators = ['cli', 'repository', 'report', 'enterprise', 'error', 'exit_code', 'performance']

        for coordinator_name in expected_coordinators:
            assert coordinator_name in coordinator_summaries
            # Each summary should either have data or an error/status message
            assert isinstance(coordinator_summaries[coordinator_name], dict)

        # Verify global metrics
        global_metrics = summary['global_metrics']
        assert 'total_coordinators' in global_metrics
        assert 'active_coordinators' in global_metrics
        assert 'total_test_scenarios' in global_metrics
        assert global_metrics['total_coordinators'] == 7
        assert global_metrics['active_coordinators'] > 0

        # Verify coverage analysis
        coverage = summary['coverage_analysis']
        assert 'modules_with_tests' in coverage
        assert 'test_types_covered' in coverage
        assert 'coverage_gaps' in coverage
        assert 'coverage_percentage' in coverage
        assert 0.0 <= coverage['coverage_percentage'] <= 100.0

    def test_coordination_data_export(self, master_coordinator):
        """Test coordination data export functionality."""
        # Add test data
        self.test_individual_coordinator_data_storage(master_coordinator)

        # Create temporary export directory
        with tempfile.TemporaryDirectory() as temp_dir:
            export_path = Path(temp_dir) / "coordination_export"

            # Export coordination data
            export_results = master_coordinator.export_coordination_data(export_path)

            # Verify export results structure
            assert 'export_path' in export_results
            assert 'export_timestamp' in export_results
            assert 'files_created' in export_results
            assert 'export_summary' in export_results

            # Verify export path
            assert str(export_path) == export_results['export_path']

            # Verify files were created
            files_created = export_results['files_created']
            assert len(files_created) > 0

            # Verify export summary
            export_summary = export_results['export_summary']
            assert 'total_files_created' in export_summary
            assert 'export_successful' in export_summary
            assert export_summary['export_successful'] is True
            assert export_summary['total_files_created'] == len(files_created)

            # Verify actual files exist and contain data
            for file_path_str in files_created:
                file_path = Path(file_path_str)
                assert file_path.exists()
                assert file_path.stat().st_size > 0

                # Verify JSON content
                with open(file_path) as f:
                    try:
                        data = json.load(f)
                        assert isinstance(data, dict)
                        assert len(data) > 0
                    except json.JSONDecodeError:
                        pytest.fail(f"Invalid JSON in exported file: {file_path}")

    def test_memory_coordination_performance(self, master_coordinator):
        """Test memory coordination system performance."""
        # Test with large amounts of data
        start_time = time.time()

        # Add large amount of test data
        for i in range(100):
            master_coordinator.cli_coordinator.store_test_scenario(f"perf_test_{i}", {
                'scenario': f'performance_test_{i}',
                'data': list(range(100))  # Some data to store
            })

        # Record timeline events
        for i in range(50):
            master_coordinator.record_test_execution_event(
                'test_event', 'performance_module', f'perf_test_{i}',
                {'iteration': i, 'data': list(range(50))}
            )

        # Test cross-module scenarios
        for i in range(20):
            scenario_id = f"cross_perf_test_{i}"
            master_coordinator.register_cross_module_scenario(
                scenario_id, ['cli', 'performance'],
                {'performance_test': True, 'iteration': i}
            )

            # Complete the scenario
            for module in ['cli', 'performance']:
                master_coordinator.update_cross_module_result(
                    scenario_id, module, {'completed': True, 'iteration': i}
                )

        data_creation_time = time.time() - start_time

        # Test summary generation performance
        summary_start = time.time()
        summary = master_coordinator.generate_comprehensive_summary()
        summary_time = time.time() - summary_start

        # Test validation performance
        validation_start = time.time()
        validation_results = master_coordinator.validate_data_consistency()
        validation_time = time.time() - validation_start

        # Performance assertions
        assert data_creation_time < 5.0, f"Data creation took too long: {data_creation_time}s"
        assert summary_time < 2.0, f"Summary generation took too long: {summary_time}s"
        assert validation_time < 3.0, f"Data validation took too long: {validation_time}s"

        # Verify data integrity after performance test
        assert len(master_coordinator.cli_coordinator.test_scenarios) >= 100
        assert len(master_coordinator.test_execution_timeline) >= 50
        assert len(master_coordinator.cross_module_scenarios) >= 20
        assert summary['global_metrics']['total_test_scenarios'] >= 100
        assert validation_results['overall_consistency_score'] > 0.0


@pytest.mark.e2e
@pytest.mark.integration
def test_memory_coordination_integration():
    """Integration test for complete memory coordination system."""
    coordinator = MasterMemoryCoordinator()

    # Test complete memory coordination integration
    # Store data across multiple coordinators
    test_scenarios = [
        ('cli', 'cli_integration_test', {'workflow': 'scan'}),
        ('repository', 'repo_integration_test', {'type': 'django'}),
        ('report', 'report_integration_test', {'format': 'sarif'}),
        ('enterprise', 'enterprise_integration_test', {'scale': 'large'}),
        ('error', 'error_integration_test', {'type': 'exit_code'}),
        ('performance', 'perf_integration_test', {'benchmark': True})
    ]

    for coordinator_type, test_id, test_data in test_scenarios:
        if coordinator_type == 'cli':
            coordinator.cli_coordinator.store_test_scenario(test_id, test_data)
        elif coordinator_type == 'repository':
            coordinator.repository_coordinator.store_repository_profile(test_id, test_data)
        elif coordinator_type == 'report':
            coordinator.report_coordinator.store_report_metadata(test_id, test_data)
        elif coordinator_type == 'enterprise':
            coordinator.enterprise_coordinator.store_enterprise_project(test_id, test_data)
        elif coordinator_type == 'error':
            coordinator.error_coordinator.store_error_scenario(test_id, test_data)
        elif coordinator_type == 'performance':
            coordinator.performance_coordinator.store_benchmark_result(test_id, test_data)

    # Test cross-module integration
    coordinator.register_cross_module_scenario(
        'integration_scenario',
        ['cli', 'repository', 'report', 'performance'],
        {'integration_test': True}
    )

    for module in ['cli', 'repository', 'report', 'performance']:
        coordinator.update_cross_module_result(
            'integration_scenario', module, {'integration_completed': True}
        )

    # Validate integration
    summary = coordinator.generate_comprehensive_summary()
    validation = coordinator.validate_data_consistency()

    assert summary['global_metrics']['active_coordinators'] >= 6
    assert validation['overall_consistency_score'] > 0.8
    assert 'integration_scenario' in coordinator.cross_module_scenarios
    assert coordinator.cross_module_scenarios['integration_scenario']['status'] == 'completed'

    print("Memory coordination integration test completed successfully")


if __name__ == "__main__":
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "-m", "e2e"
    ])
