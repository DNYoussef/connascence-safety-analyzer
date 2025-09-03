#!/usr/bin/env python3
"""
End-to-End Testing Suite for Connascence Analysis

This module provides comprehensive end-to-end testing capabilities for the
connascence analysis system, including:

- CLI workflow testing
- Repository analysis validation  
- Report generation verification
- Enterprise-scale scenario testing
- Error handling and recovery validation
- Exit code correctness verification
- Performance benchmarking and profiling
- Memory coordination and tracking

The e2e tests use memory coordination to track test scenarios, results,
and performance metrics across different test categories.

Test Categories:
- CLI Workflows: Complete command-line interface testing
- Repository Analysis: Real repository testing with various frameworks
- Report Generation: SARIF, JSON, Markdown, and Text output validation
- Enterprise Scale: Large-scale analysis scenarios
- Error Handling: Comprehensive error and edge case testing
- Exit Codes: All exit code scenarios (0,1,2,3,4,130)
- Performance: Benchmarking, profiling, and scalability testing

Usage:
    # Run all e2e tests
    pytest tests/e2e/ -v

    # Run specific test category
    pytest tests/e2e/test_cli_workflows.py -v
    pytest tests/e2e/test_repository_analysis.py -v
    pytest tests/e2e/test_report_generation.py -v
    pytest tests/e2e/test_enterprise_scale.py -v
    pytest tests/e2e/test_error_handling.py -v
    pytest tests/e2e/test_exit_codes.py -v
    pytest tests/e2e/test_performance.py -v

    # Run with markers
    pytest tests/e2e/ -m "e2e" -v
    pytest tests/e2e/ -m "slow" -v
    pytest tests/e2e/ -m "integration" -v

Memory Coordination:
The e2e tests use specialized memory coordinators to track:
- Test scenario execution and results
- Performance metrics and benchmarks
- Error patterns and recovery attempts
- Exit code validation results
- Resource utilization data
- Sequential workflow validation

This provides comprehensive tracking and analysis of test execution
patterns for quality assurance and performance monitoring.
"""

from .test_cli_workflows import E2EMemoryCoordinator, SequentialWorkflowValidator
from .test_repository_analysis import RepositoryAnalysisCoordinator
from .test_report_generation import ReportGenerationCoordinator
from .test_enterprise_scale import EnterpriseScaleCoordinator
from .test_error_handling import ErrorHandlingCoordinator
from .test_exit_codes import ExitCodeCoordinator
from .test_performance import PerformanceBenchmarkCoordinator

__all__ = [
    'E2EMemoryCoordinator',
    'SequentialWorkflowValidator',
    'RepositoryAnalysisCoordinator',
    'ReportGenerationCoordinator', 
    'EnterpriseScaleCoordinator',
    'ErrorHandlingCoordinator',
    'ExitCodeCoordinator',
    'PerformanceBenchmarkCoordinator'
]

__version__ = '1.0.0'
__author__ = 'Connascence E2E Test Suite'
__description__ = 'Comprehensive end-to-end testing with memory coordination'