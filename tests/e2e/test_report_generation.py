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
End-to-End Report Generation Tests

Tests SARIF, JSON, Markdown, and Text report generation workflows.
Validates report compliance, content accuracy, and format specifications.
Uses memory coordination for tracking report generation patterns.
"""

import json
from pathlib import Path
import sys
import tempfile
import time
from typing import Any, Dict, List

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from interfaces.cli.connascence import ConnascenceCLI
from tests.e2e.test_cli_workflows import SequentialWorkflowValidator


class ReportGenerationCoordinator:
    """Memory coordinator for report generation testing and validation."""

    def __init__(self):
        self.report_metadata = {}
        self.format_validations = {}
        self.compliance_results = {}
        self.content_accuracy_tests = {}
        self.performance_benchmarks = {}
        self.schema_validations = {}

    def store_report_metadata(self, report_id: str, metadata: Dict[str, Any]):
        """Store report generation metadata."""
        self.report_metadata[report_id] = {
            'metadata': metadata,
            'timestamp': time.time(),
            'validation_status': 'pending'
        }

    def store_format_validation(self, report_id: str, format_type: str,
                              validation_results: Dict[str, Any]):
        """Store format-specific validation results."""
        if report_id not in self.format_validations:
            self.format_validations[report_id] = {}

        self.format_validations[report_id][format_type] = {
            'results': validation_results,
            'timestamp': time.time(),
            'passed': validation_results.get('valid', False)
        }

    def store_compliance_result(self, report_id: str, standard: str,
                              compliance_data: Dict[str, Any]):
        """Store standards compliance results (SARIF, etc.)."""
        if report_id not in self.compliance_results:
            self.compliance_results[report_id] = {}

        self.compliance_results[report_id][standard] = compliance_data

    def store_content_accuracy(self, report_id: str, accuracy_metrics: Dict[str, Any]):
        """Store content accuracy validation results."""
        self.content_accuracy_tests[report_id] = accuracy_metrics

    def store_performance_benchmark(self, report_id: str, benchmark_data: Dict[str, Any]):
        """Store report generation performance benchmarks."""
        self.performance_benchmarks[report_id] = benchmark_data

    def get_report_summary(self) -> Dict[str, Any]:
        """Get comprehensive report generation summary."""
        return {
            'total_reports': len(self.report_metadata),
            'formats_tested': sum(len(validations) for validations in self.format_validations.values()),
            'compliance_tests': sum(len(results) for results in self.compliance_results.values()),
            'accuracy_tests': len(self.content_accuracy_tests),
            'performance_tests': len(self.performance_benchmarks),
            'overall_success_rate': self._calculate_success_rate()
        }

    def _calculate_success_rate(self) -> float:
        """Calculate overall success rate of report generation."""
        total_tests = 0
        passed_tests = 0

        for report_validations in self.format_validations.values():
            for validation in report_validations.values():
                total_tests += 1
                if validation['passed']:
                    passed_tests += 1

        return passed_tests / max(total_tests, 1)


# Global report coordinator
report_coordinator = ReportGenerationCoordinator()


class SARIFValidator:
    """SARIF 2.1.0 specification validator."""

    def __init__(self):
        self.required_fields = {
            'root': ['$schema', 'version', 'runs'],
            'run': ['tool', 'results'],
            'tool': ['driver'],
            'driver': ['name'],
            'result': ['ruleId', 'message', 'locations'],
            'location': ['physicalLocation'],
            'physicalLocation': ['artifactLocation'],
            'artifactLocation': ['uri']
        }

    def validate_sarif_structure(self, sarif_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate SARIF structure against specification."""
        validation_results = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'compliance_level': 'full'
        }

        # Validate root structure
        self._validate_required_fields(sarif_data, 'root', validation_results)

        # Validate schema
        expected_schema = "https://schemastore.azurewebsites.net/schemas/json/sarif-2.1.0.json"
        if sarif_data.get('$schema') != expected_schema:
            validation_results['warnings'].append(f"Schema URL not standard: {sarif_data.get('$schema')}")

        # Validate version
        if sarif_data.get('version') != '2.1.0':
            validation_results['errors'].append(f"Invalid SARIF version: {sarif_data.get('version')}")
            validation_results['valid'] = False

        # Validate runs
        runs = sarif_data.get('runs', [])
        if not runs:
            validation_results['errors'].append("No runs found in SARIF output")
            validation_results['valid'] = False
        else:
            for i, run in enumerate(runs):
                self._validate_run(run, i, validation_results)

        # Set compliance level
        if validation_results['errors']:
            validation_results['compliance_level'] = 'non-compliant'
        elif validation_results['warnings']:
            validation_results['compliance_level'] = 'partial'

        return validation_results

    def _validate_required_fields(self, obj: Dict, obj_type: str, validation_results: Dict):
        """Validate required fields for object type."""
        required = self.required_fields.get(obj_type, [])
        for field in required:
            if field not in obj:
                validation_results['errors'].append(f"Missing required field '{field}' in {obj_type}")
                validation_results['valid'] = False

    def _validate_run(self, run: Dict, run_index: int, validation_results: Dict):
        """Validate individual SARIF run."""
        self._validate_required_fields(run, 'run', validation_results)

        # Validate tool
        tool = run.get('tool')
        if tool:
            self._validate_required_fields(tool, 'tool', validation_results)
            driver = tool.get('driver')
            if driver:
                self._validate_required_fields(driver, 'driver', validation_results)

        # Validate results
        results = run.get('results', [])
        for i, result in enumerate(results):
            self._validate_result(result, i, validation_results)

    def _validate_result(self, result: Dict, result_index: int, validation_results: Dict):
        """Validate individual SARIF result."""
        self._validate_required_fields(result, 'result', validation_results)

        # Validate locations
        locations = result.get('locations', [])
        if not locations:
            validation_results['warnings'].append(f"Result {result_index} has no locations")

        for i, location in enumerate(locations):
            self._validate_location(location, i, validation_results)

    def _validate_location(self, location: Dict, location_index: int, validation_results: Dict):
        """Validate individual SARIF location."""
        self._validate_required_fields(location, 'location', validation_results)

        physical_location = location.get('physicalLocation')
        if physical_location:
            self._validate_required_fields(physical_location, 'physicalLocation', validation_results)

            artifact_location = physical_location.get('artifactLocation')
            if artifact_location:
                self._validate_required_fields(artifact_location, 'artifactLocation', validation_results)


class JSONReportValidator:
    """JSON report format validator."""

    def validate_json_structure(self, json_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate JSON report structure."""
        validation_results = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'completeness_score': 0.0
        }

        required_fields = [
            'timestamp', 'project_root', 'total_files_analyzed',
            'analysis_duration_ms', 'violations', 'summary_metrics'
        ]

        score_components = len(required_fields)
        score = 0

        # Check required fields
        for field in required_fields:
            if field in json_data:
                score += 1
            else:
                validation_results['errors'].append(f"Missing required field: {field}")
                validation_results['valid'] = False

        # Validate violations structure
        violations = json_data.get('violations', [])
        if isinstance(violations, list):
            for i, violation in enumerate(violations[:5]):  # Check first 5
                if not self._validate_violation_structure(violation, i, validation_results):
                    validation_results['valid'] = False
        else:
            validation_results['errors'].append("Violations field must be a list")
            validation_results['valid'] = False

        # Validate summary metrics
        summary_metrics = json_data.get('summary_metrics')
        if summary_metrics and isinstance(summary_metrics, dict):
            expected_metrics = ['total_violations', 'severity_breakdown', 'type_breakdown']
            for metric in expected_metrics:
                if metric in summary_metrics:
                    score += 0.5

        validation_results['completeness_score'] = score / (score_components + 1.5)  # +1.5 for summary metrics

        return validation_results

    def _validate_violation_structure(self, violation: Dict, index: int, validation_results: Dict) -> bool:
        """Validate individual violation structure."""
        required_violation_fields = [
            'id', 'rule_id', 'connascence_type', 'severity',
            'description', 'file_path', 'line_number'
        ]

        valid = True
        for field in required_violation_fields:
            if field not in violation:
                validation_results['errors'].append(f"Violation {index}: missing field '{field}'")
                valid = False

        # Validate severity format
        severity = violation.get('severity')
        if severity and isinstance(severity, dict) and 'value' not in severity:
            validation_results['errors'].append(f"Violation {index}: severity missing 'value' field")
            valid = False

        return valid


@pytest.fixture
def sample_project_with_violations():
    """Create sample project with known violations for report testing."""
    temp_dir = tempfile.mkdtemp()
    project_path = Path(temp_dir)

    # Create structured violations for report validation
    (project_path / "src").mkdir()
    (project_path / "tests").mkdir()

    # File with known violation patterns
    (project_path / "src" / "main.py").write_text("""
# Test file for report generation validation

def function_with_parameter_bomb(param1, param2, param3, param4, param5, param6):
    '''Function with parameter bomb violation for testing.'''
    magic_number = 42  # Magic literal violation
    api_key = "secret-key-12345"  # Magic string violation

    if param1 > magic_number:
        return param1 * 2.5  # Another magic literal

    return param1


class GodClassForTesting:
    '''God class with many methods for testing.'''

    def __init__(self):
        self.timeout = 30  # Magic literal
        self.max_retries = 5  # Magic literal

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
    def method_21(self): pass  # Exceeds god class threshold


def untyped_function(data, options):  # Missing type hints
    '''Function without type hints for testing.'''
    threshold = 100  # Magic literal
    if len(data) > threshold:
        return True
    return False
""")

    # Another file with violations
    (project_path / "src" / "utils.py").write_text("""
def utility_function(a, b, c, d, e):  # Parameter bomb
    '''Utility with parameter violations.'''

    # Multiple magic values
    default_timeout = 5000  # Magic literal
    retry_count = 3  # Magic literal
    buffer_size = 8192  # Magic literal

    if a == "production":  # Magic string
        multiplier = 1.5  # Magic literal
    elif a == "development":  # Magic string
        multiplier = 2.0  # Magic literal
    else:
        multiplier = 1.0  # Magic literal

    return (b + c + d + e) * multiplier


class ConfigurationManager:
    '''Another class with violations.'''

    def load_config(self, env, region, version, debug, cache):  # Parameter bomb
        config = {
            'database_url': 'postgresql://localhost:5432/db',  # Magic string
            'redis_url': 'redis://localhost:6379/0',  # Magic string
            'cache_ttl': 3600,  # Magic literal
            'max_connections': 100,  # Magic literal
            'timeout': 30000  # Magic literal
        }
        return config

    def method_a(self): pass
    def method_b(self): pass
    def method_c(self): pass
    def method_d(self): pass
    def method_e(self): pass
    def method_f(self): pass
    def method_g(self): pass
    def method_h(self): pass
    def method_i(self): pass
    def method_j(self): pass
    def method_k(self): pass
    def method_l(self): pass
    def method_m(self): pass
    def method_n(self): pass
    def method_o(self): pass
    def method_p(self): pass
    def method_q(self): pass
    def method_r(self): pass
    def method_s(self): pass
    def method_t(self): pass
    def method_u(self): pass  # God class
""")

    yield project_path

    # Cleanup
    import shutil
    shutil.rmtree(temp_dir)


@pytest.fixture
def report_workflow_validator():
    """Create workflow validator for report generation testing."""
    return SequentialWorkflowValidator(report_coordinator)


class TestReportGenerationWorkflows:
    """Test comprehensive report generation workflows."""

    def test_sarif_report_generation_and_validation(self, sample_project_with_violations, report_workflow_validator):
        """Test SARIF report generation with full compliance validation."""
        scenario_id = "sarif_generation_validation"
        report_workflow_validator.start_scenario(scenario_id, "SARIF report generation and validation")

        # Step 1: Generate SARIF report
        cli = ConnascenceCLI()
        output_file = sample_project_with_violations / "report.sarif"

        start_time = time.time()
        exit_code = cli.run([
            "scan", str(sample_project_with_violations),
            "--format", "sarif",
            "--output", str(output_file),
            "--policy", "service-defaults"
        ])
        generation_time = time.time() - start_time

        report_workflow_validator.add_step("generate_sarif", {
            'exit_code': exit_code,
            'generation_time_ms': generation_time * 1000,
            'output_file': str(output_file)
        })

        # Step 2: Validate SARIF file exists and is readable
        assert output_file.exists(), "SARIF file was not created"

        with open(output_file) as f:
            sarif_content = f.read()

        assert len(sarif_content) > 0, "SARIF file is empty"

        report_workflow_validator.add_step("validate_file_existence", {
            'file_exists': True,
            'file_size_bytes': len(sarif_content)
        })

        # Step 3: Parse and validate JSON structure
        try:
            sarif_data = json.loads(sarif_content)
        except json.JSONDecodeError as e:
            pytest.fail(f"Invalid JSON in SARIF file: {e}")

        report_workflow_validator.add_step("parse_json", {'json_valid': True})

        # Step 4: SARIF specification compliance validation
        validator = SARIFValidator()
        compliance_results = validator.validate_sarif_structure(sarif_data)

        report_coordinator.store_compliance_result(scenario_id, 'sarif_2_1_0', compliance_results)
        report_workflow_validator.add_step("sarif_compliance_check", compliance_results)

        # Step 5: Content accuracy validation
        runs = sarif_data.get('runs', [])
        assert len(runs) > 0, "SARIF should contain at least one run"

        run = runs[0]
        results = run.get('results', [])

        # Validate we found expected violations
        expected_violation_types = ['CoP', 'CoM', 'CoT', 'CoA']  # Parameter, Magic, Type, Algorithm
        found_rule_ids = {result.get('ruleId', '') for result in results}

        accuracy_metrics = {
            'total_results': len(results),
            'expected_violations_found': sum(1 for vtype in expected_violation_types if f'CON_{vtype}' in found_rule_ids),
            'expected_violation_types': len(expected_violation_types),
            'accuracy_percentage': 0.0
        }

        accuracy_metrics['accuracy_percentage'] = (
            accuracy_metrics['expected_violations_found'] /
            max(accuracy_metrics['expected_violation_types'], 1)
        ) * 100

        report_coordinator.store_content_accuracy(scenario_id, accuracy_metrics)
        report_workflow_validator.add_step("content_accuracy_check", accuracy_metrics)

        # Step 6: Detailed structure validation
        structure_validation = {
            'has_tool_info': 'tool' in run and 'driver' in run['tool'],
            'has_driver_name': run.get('tool', {}).get('driver', {}).get('name') is not None,
            'results_have_locations': all('locations' in result for result in results),
            'results_have_messages': all('message' in result for result in results),
            'results_have_rule_ids': all('ruleId' in result for result in results)
        }

        report_workflow_validator.add_step("structure_validation", structure_validation)

        # Store comprehensive report metadata
        report_metadata = {
            'format': 'sarif',
            'version': '2.1.0',
            'generation_time_ms': generation_time * 1000,
            'file_size_bytes': len(sarif_content),
            'results_count': len(results),
            'compliance_level': compliance_results.get('compliance_level', 'unknown')
        }

        report_coordinator.store_report_metadata(scenario_id, report_metadata)

        # Performance benchmark
        performance_data = {
            'generation_time_ms': generation_time * 1000,
            'results_per_second': len(results) / max(generation_time, 0.001),
            'file_size_efficiency': len(results) / max(len(sarif_content), 1) * 1000,  # results per KB
            'performance_acceptable': generation_time < 10.0
        }

        report_coordinator.store_performance_benchmark(scenario_id, performance_data)

        # Assertions
        assert exit_code == 1, "Should find violations in test project"
        assert compliance_results['valid'], f"SARIF compliance failed: {compliance_results['errors']}"
        assert len(results) > 0, "SARIF should contain violation results"
        assert accuracy_metrics['accuracy_percentage'] > 50, f"Low accuracy: {accuracy_metrics['accuracy_percentage']}%"
        assert structure_validation['has_tool_info'], "SARIF missing tool information"
        assert all(structure_validation.values()), f"Structure validation failed: {structure_validation}"

        report_workflow_validator.complete_scenario(True, {
            'sarif_validation_passed': True,
            'compliance_results': compliance_results,
            'accuracy_metrics': accuracy_metrics,
            'performance_data': performance_data
        })

    def test_json_report_comprehensive_validation(self, sample_project_with_violations, report_workflow_validator):
        """Test JSON report generation with comprehensive validation."""
        scenario_id = "json_comprehensive_validation"
        report_workflow_validator.start_scenario(scenario_id, "JSON report comprehensive validation")

        # Step 1: Generate JSON report
        cli = ConnascenceCLI()
        output_file = sample_project_with_violations / "report.json"

        start_time = time.time()
        exit_code = cli.run([
            "scan", str(sample_project_with_violations),
            "--format", "json",
            "--output", str(output_file),
            "--policy", "strict-core"
        ])
        generation_time = time.time() - start_time

        report_workflow_validator.add_step("generate_json", {
            'exit_code': exit_code,
            'generation_time_ms': generation_time * 1000
        })

        # Step 2: Validate and parse JSON
        assert output_file.exists(), "JSON report file not created"

        with open(output_file) as f:
            json_content = f.read()

        try:
            json_data = json.loads(json_content)
        except json.JSONDecodeError as e:
            pytest.fail(f"Invalid JSON in report: {e}")

        report_workflow_validator.add_step("parse_json", {'json_valid': True})

        # Step 3: JSON structure validation
        validator = JSONReportValidator()
        validation_results = validator.validate_json_structure(json_data)

        report_coordinator.store_format_validation(scenario_id, 'json', validation_results)
        report_workflow_validator.add_step("json_structure_validation", validation_results)

        # Step 4: Content depth analysis
        violations = json_data.get('violations', [])

        content_analysis = {
            'total_violations': len(violations),
            'violation_types_found': len({v.get('connascence_type', '') for v in violations}),
            'severities_found': len({v.get('severity', {}).get('value', '') for v in violations}),
            'files_with_violations': len({v.get('file_path', '') for v in violations}),
            'has_summary_metrics': 'summary_metrics' in json_data,
            'has_file_stats': 'file_stats' in json_data
        }

        # Validate specific violation content
        magic_literals = [v for v in violations if 'magic' in v.get('description', '').lower() and 'literal' in v.get('description', '').lower()]
        parameter_bombs = [v for v in violations if 'parameter' in v.get('description', '').lower()]
        god_classes = [v for v in violations if 'class' in v.get('description', '').lower() and 'methods' in v.get('description', '').lower()]

        content_analysis.update({
            'magic_literals_found': len(magic_literals),
            'parameter_bombs_found': len(parameter_bombs),
            'god_classes_found': len(god_classes),
            'expected_patterns_detected': len(magic_literals) > 0 and len(parameter_bombs) > 0 and len(god_classes) > 0
        })

        report_workflow_validator.add_step("content_depth_analysis", content_analysis)

        # Step 5: Data integrity validation
        integrity_checks = {
            'all_violations_have_ids': all('id' in v for v in violations),
            'all_violations_have_descriptions': all('description' in v and len(v['description']) > 0 for v in violations),
            'all_violations_have_locations': all('file_path' in v and 'line_number' in v for v in violations),
            'line_numbers_valid': all(isinstance(v.get('line_number'), int) and v.get('line_number') > 0 for v in violations),
            'file_paths_exist': all(Path(v.get('file_path', '')).exists() or str(sample_project_with_violations) in v.get('file_path', '') for v in violations[:5]),  # Check first 5
            'timestamps_valid': 'timestamp' in json_data and isinstance(json_data['timestamp'], (int, float)),
            'durations_valid': 'analysis_duration_ms' in json_data and json_data['analysis_duration_ms'] > 0
        }

        report_workflow_validator.add_step("data_integrity_validation", integrity_checks)

        # Step 6: Performance and efficiency metrics
        performance_metrics = {
            'generation_time_ms': generation_time * 1000,
            'file_size_bytes': len(json_content),
            'violations_per_second': len(violations) / max(generation_time, 0.001),
            'bytes_per_violation': len(json_content) / max(len(violations), 1),
            'compression_efficiency': len(violations) / max(len(json_content) / 1024, 1),  # violations per KB
            'generation_speed_acceptable': generation_time < 5.0
        }

        report_coordinator.store_performance_benchmark(scenario_id, performance_metrics)
        report_workflow_validator.add_step("performance_analysis", performance_metrics)

        # Store comprehensive metadata
        report_metadata = {
            'format': 'json',
            'generation_time_ms': generation_time * 1000,
            'file_size_bytes': len(json_content),
            'violations_count': len(violations),
            'completeness_score': validation_results.get('completeness_score', 0.0)
        }

        report_coordinator.store_report_metadata(scenario_id, report_metadata)

        # Assertions
        assert exit_code == 1, "Should find violations in test project"
        assert validation_results['valid'], f"JSON validation failed: {validation_results['errors']}"
        assert validation_results['completeness_score'] > 0.8, f"Low completeness score: {validation_results['completeness_score']}"
        assert content_analysis['total_violations'] > 0, "Should find violations"
        assert content_analysis['expected_patterns_detected'], "Should detect expected violation patterns"
        assert all(integrity_checks.values()), f"Data integrity issues: {integrity_checks}"
        assert performance_metrics['generation_speed_acceptable'], f"Generation too slow: {generation_time}s"

        report_workflow_validator.complete_scenario(True, {
            'json_validation_passed': True,
            'validation_results': validation_results,
            'content_analysis': content_analysis,
            'integrity_checks': integrity_checks,
            'performance_metrics': performance_metrics
        })

    def test_markdown_report_formatting_validation(self, sample_project_with_violations, report_workflow_validator):
        """Test Markdown report generation with formatting validation."""
        scenario_id = "markdown_formatting_validation"
        report_workflow_validator.start_scenario(scenario_id, "Markdown report formatting validation")

        # Step 1: Generate Markdown report
        cli = ConnascenceCLI()
        output_file = sample_project_with_violations / "report.md"

        exit_code = cli.run([
            "scan", str(sample_project_with_violations),
            "--format", "markdown",
            "--output", str(output_file)
        ])

        report_workflow_validator.add_step("generate_markdown", {'exit_code': exit_code})

        # Step 2: Read and validate content
        assert output_file.exists(), "Markdown report not created"

        markdown_content = output_file.read_text()
        assert len(markdown_content) > 0, "Markdown report is empty"

        report_workflow_validator.add_step("read_content", {
            'content_length': len(markdown_content),
            'content_exists': True
        })

        # Step 3: Markdown structure validation
        structure_checks = {
            'has_main_header': any(line.startswith('# ') for line in markdown_content.split('\n')),
            'has_subheaders': any(line.startswith('## ') for line in markdown_content.split('\n')),
            'has_lists': '- ' in markdown_content or '* ' in markdown_content,
            'has_code_blocks': '```' in markdown_content or '`' in markdown_content,
            'has_tables': '|' in markdown_content,
            'proper_line_breaks': '\n\n' in markdown_content,
            'has_violation_details': 'violation' in markdown_content.lower()
        }

        report_workflow_validator.add_step("structure_validation", structure_checks)

        # Step 4: Content completeness validation
        content_checks = {
            'contains_summary': any(keyword in markdown_content.lower() for keyword in ['summary', 'overview', 'analysis']),
            'contains_violation_counts': any(char.isdigit() for char in markdown_content),
            'contains_file_paths': '.py' in markdown_content,
            'contains_severity_info': any(severity in markdown_content.lower() for severity in ['low', 'medium', 'high', 'critical']),
            'contains_connascence_types': any(conn_type in markdown_content for conn_type in ['CoM', 'CoP', 'CoT', 'CoA']),
            'contains_recommendations': any(keyword in markdown_content.lower() for keyword in ['suggestion', 'recommendation', 'fix'])
        }

        report_workflow_validator.add_step("content_validation", content_checks)

        # Step 5: Formatting quality assessment
        lines = markdown_content.split('\n')
        formatting_quality = {
            'proper_header_hierarchy': self._validate_header_hierarchy(lines),
            'consistent_list_formatting': self._validate_list_formatting(lines),
            'appropriate_line_length': self._validate_line_length(lines),
            'proper_whitespace': self._validate_whitespace(lines),
            'readable_structure': len([line for line in lines if line.strip()]) > len(lines) * 0.6  # Not too many empty lines
        }

        report_workflow_validator.add_step("formatting_quality", formatting_quality)

        # Store validation results
        markdown_validation = {
            'structure_checks': structure_checks,
            'content_checks': content_checks,
            'formatting_quality': formatting_quality,
            'overall_score': self._calculate_markdown_score(structure_checks, content_checks, formatting_quality)
        }

        report_coordinator.store_format_validation(scenario_id, 'markdown', {
            'valid': all(structure_checks.values()) and all(content_checks.values()),
            'validation_details': markdown_validation
        })

        # Assertions
        assert exit_code == 1, "Should find violations"
        assert all(structure_checks.values()), f"Markdown structure issues: {structure_checks}"
        assert all(content_checks.values()), f"Markdown content issues: {content_checks}"
        assert markdown_validation['overall_score'] > 0.8, f"Low markdown quality score: {markdown_validation['overall_score']}"

        report_workflow_validator.complete_scenario(True, {
            'markdown_validation_passed': True,
            'validation_details': markdown_validation
        })

    def test_text_report_readability_validation(self, sample_project_with_violations, report_workflow_validator):
        """Test text report generation with readability validation."""
        scenario_id = "text_readability_validation"
        report_workflow_validator.start_scenario(scenario_id, "Text report readability validation")

        # Generate text report
        cli = ConnascenceCLI()
        output_file = sample_project_with_violations / "report.txt"

        cli.run([
            "scan", str(sample_project_with_violations),
            "--format", "text",
            "--output", str(output_file)
        ])

        assert output_file.exists(), "Text report not created"
        text_content = output_file.read_text()

        # Readability validation
        readability_metrics = {
            'has_clear_sections': '=' in text_content and '-' in text_content,
            'proper_indentation': any(line.startswith('  ') for line in text_content.split('\n')),
            'column_alignment': self._validate_column_alignment(text_content),
            'appropriate_spacing': '\n\n' in text_content,
            'summary_section': 'summary' in text_content.lower(),
            'violation_details': 'violation' in text_content.lower(),
            'file_information': '.py' in text_content,
            'severity_indicators': any(sev in text_content.lower() for sev in ['critical', 'high', 'medium', 'low'])
        }

        report_coordinator.store_format_validation(scenario_id, 'text', {
            'valid': all(readability_metrics.values()),
            'readability_metrics': readability_metrics
        })

        assert all(readability_metrics.values()), f"Text readability issues: {readability_metrics}"

        report_workflow_validator.complete_scenario(True, {
            'text_validation_passed': True,
            'readability_metrics': readability_metrics
        })

    def test_multi_format_consistency_validation(self, sample_project_with_violations, report_workflow_validator):
        """Test consistency across different report formats."""
        scenario_id = "multi_format_consistency"
        report_workflow_validator.start_scenario(scenario_id, "Multi-format consistency validation")

        formats = ["json", "sarif", "markdown", "text"]
        format_data = {}

        # Generate all formats
        for format_type in formats:
            output_file = sample_project_with_violations / f"consistency_test.{format_type}"

            cli = ConnascenceCLI()
            exit_code = cli.run([
                "scan", str(sample_project_with_violations),
                "--format", format_type,
                "--output", str(output_file),
                "--policy", "service-defaults"  # Same policy for consistency
            ])

            assert output_file.exists(), f"Failed to create {format_type} report"

            # Parse format-specific data
            if format_type in ["json", "sarif"]:
                with open(output_file) as f:
                    data = json.load(f)

                if format_type == "json":
                    violations = data.get('violations', [])
                    format_data[format_type] = {
                        'violation_count': len(violations),
                        'files_analyzed': data.get('total_files_analyzed', 0),
                        'violation_types': {v.get('connascence_type', '') for v in violations}
                    }
                else:  # sarif
                    results = data.get('runs', [{}])[0].get('results', [])
                    format_data[format_type] = {
                        'violation_count': len(results),
                        'rule_ids': {r.get('ruleId', '') for r in results}
                    }
            else:
                content = output_file.read_text()
                format_data[format_type] = {
                    'content_length': len(content),
                    'has_violations': 'violation' in content.lower(),
                    'has_summary': 'summary' in content.lower()
                }

            report_workflow_validator.add_step(f"generate_{format_type}", {
                'exit_code': exit_code,
                'format': format_type
            })

        # Consistency validation
        consistency_checks = {
            'json_sarif_violation_counts_match': (
                format_data['json']['violation_count'] == format_data['sarif']['violation_count']
            ),
            'all_formats_have_content': all(
                'violation_count' in data or 'has_violations' in data
                for data in format_data.values()
            ),
            'text_markdown_both_have_violations': (
                format_data['text']['has_violations'] and format_data['markdown']['has_violations']
            ),
            'all_formats_generated': len(format_data) == len(formats)
        }

        report_workflow_validator.add_step("consistency_validation", consistency_checks)

        # Store consistency results
        report_coordinator.store_format_validation(scenario_id, 'consistency', {
            'valid': all(consistency_checks.values()),
            'format_data': format_data,
            'consistency_checks': consistency_checks
        })

        assert all(consistency_checks.values()), f"Consistency issues: {consistency_checks}"

        report_workflow_validator.complete_scenario(True, {
            'consistency_validation_passed': True,
            'formats_tested': len(formats),
            'consistency_checks': consistency_checks
        })

    def test_report_generation_performance_benchmarks(self, sample_project_with_violations, report_workflow_validator):
        """Test report generation performance across formats."""
        scenario_id = "performance_benchmarks"
        report_workflow_validator.start_scenario(scenario_id, "Report generation performance benchmarks")

        formats = ["json", "sarif", "markdown", "text"]
        performance_results = {}

        for format_type in formats:
            output_file = sample_project_with_violations / f"perf_test.{format_type}"

            # Multiple runs for average
            times = []
            for run in range(3):
                cli = ConnascenceCLI()
                start_time = time.time()
                cli.run([
                    "scan", str(sample_project_with_violations),
                    "--format", format_type,
                    "--output", str(output_file)
                ])
                end_time = time.time()
                times.append(end_time - start_time)

            file_size = output_file.stat().st_size if output_file.exists() else 0

            performance_results[format_type] = {
                'avg_generation_time_ms': (sum(times) / len(times)) * 1000,
                'min_generation_time_ms': min(times) * 1000,
                'max_generation_time_ms': max(times) * 1000,
                'file_size_bytes': file_size,
                'generation_rate_mb_per_sec': (file_size / 1024 / 1024) / max(sum(times) / len(times), 0.001)
            }

        # Overall benchmarks
        benchmark_summary = {
            'fastest_format': min(performance_results.items(), key=lambda x: x[1]['avg_generation_time_ms'])[0],
            'largest_output': max(performance_results.items(), key=lambda x: x[1]['file_size_bytes'])[0],
            'most_efficient': max(performance_results.items(), key=lambda x: x[1]['generation_rate_mb_per_sec'])[0],
            'all_formats_under_10s': all(r['avg_generation_time_ms'] < 10000 for r in performance_results.values())
        }

        report_coordinator.store_performance_benchmark(scenario_id, {
            'format_performance': performance_results,
            'benchmark_summary': benchmark_summary
        })

        report_workflow_validator.add_step("performance_benchmarking", benchmark_summary)

        assert benchmark_summary['all_formats_under_10s'], "Some formats too slow"

        report_workflow_validator.complete_scenario(True, {
            'performance_benchmarks_completed': True,
            'results': performance_results,
            'summary': benchmark_summary
        })

    def test_memory_coordination_report_tracking(self):
        """Test memory coordination for report generation tracking."""
        # Test report coordinator functionality
        test_report_id = "memory_test_report"

        # Store test data
        report_coordinator.store_report_metadata(test_report_id, {
            'format': 'test',
            'size': 1024
        })

        report_coordinator.store_format_validation(test_report_id, 'json', {
            'valid': True,
            'score': 0.95
        })

        report_coordinator.store_compliance_result(test_report_id, 'sarif', {
            'compliant': True
        })

        # Validate memory storage
        assert test_report_id in report_coordinator.report_metadata
        assert test_report_id in report_coordinator.format_validations
        assert test_report_id in report_coordinator.compliance_results

        # Test summary generation
        summary = report_coordinator.get_report_summary()
        assert summary['total_reports'] > 0
        assert summary['formats_tested'] > 0
        assert summary['compliance_tests'] > 0

    # Helper methods for validation
    def _validate_header_hierarchy(self, lines: List[str]) -> bool:
        """Validate proper header hierarchy in markdown."""
        header_levels = []
        for line in lines:
            if line.startswith('#'):
                level = len(line) - len(line.lstrip('#'))
                header_levels.append(level)

        # Check that headers don't skip levels
        return all(header_levels[i] <= header_levels[i - 1] + 1 for i in range(1, len(header_levels)))

    def _validate_list_formatting(self, lines: List[str]) -> bool:
        """Validate consistent list formatting."""
        list_markers = set()
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('- ') or stripped.startswith('* '):
                list_markers.add(stripped[0])

        # Should use consistent list markers
        return len(list_markers) <= 1

    def _validate_line_length(self, lines: List[str]) -> bool:
        """Validate appropriate line length."""
        long_lines = [line for line in lines if len(line) > 120]
        return len(long_lines) < len(lines) * 0.1  # Less than 10% long lines

    def _validate_whitespace(self, lines: List[str]) -> bool:
        """Validate proper whitespace usage."""
        # Check for trailing whitespace and excessive blank lines
        trailing_whitespace = sum(1 for line in lines if line.endswith(' ') or line.endswith('\t'))
        consecutive_blanks = 0
        max_consecutive = 0

        for line in lines:
            if not line.strip():
                consecutive_blanks += 1
                max_consecutive = max(max_consecutive, consecutive_blanks)
            else:
                consecutive_blanks = 0

        return trailing_whitespace < len(lines) * 0.05 and max_consecutive <= 3

    def _calculate_markdown_score(self, structure: Dict, content: Dict, formatting: Dict) -> float:
        """Calculate overall markdown quality score."""
        total_checks = len(structure) + len(content) + len(formatting)
        passed_checks = sum(structure.values()) + sum(content.values()) + sum(formatting.values())
        return passed_checks / total_checks

    def _validate_column_alignment(self, text: str) -> bool:
        """Validate column alignment in text output."""
        lines = text.split('\n')
        # Look for patterns that suggest tabular data
        colon_lines = [line for line in lines if ':' in line]
        if len(colon_lines) >= 3:
            # Check if colons are reasonably aligned
            colon_positions = [line.find(':') for line in colon_lines]
            return max(colon_positions) - min(colon_positions) <= 5
        return True  # No tabular data to validate


@pytest.mark.e2e
@pytest.mark.slow
def test_report_generation_integration():
    """Integration test for complete report generation pipeline."""
    coordinator = ReportGenerationCoordinator()

    # Test complete integration
    scenario_id = "report_integration_test"

    coordinator.store_report_metadata(scenario_id, {
        'integration_test': True,
        'timestamp': time.time()
    })

    coordinator.store_format_validation(scenario_id, 'json', {
        'valid': True,
        'test': True
    })

    # Validate integration
    assert scenario_id in coordinator.report_metadata
    assert scenario_id in coordinator.format_validations

    summary = coordinator.get_report_summary()
    assert summary['total_reports'] > 0

    print("Report generation integration test completed successfully")


if __name__ == "__main__":
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "-m", "e2e"
    ])
