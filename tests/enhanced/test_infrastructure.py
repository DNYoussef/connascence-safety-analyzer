# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2024 Connascence Safety Analyzer Contributors

"""
Enhanced Pipeline Test Infrastructure
====================================

Comprehensive test utilities and fixtures for testing enhanced pipeline integration
across all interfaces (VSCode, MCP Server, Web Dashboard, CLI).

This module provides:
- Enhanced test datasets with known connascence patterns
- Mock enhanced analyzer for controlled testing
- Data validation utilities for cross-phase correlations
- Performance measurement and profiling utilities
"""

from dataclasses import asdict, dataclass
from pathlib import Path
import time
from typing import Any, Dict, List, Optional, Tuple

import psutil
import pytest


@dataclass
class MockCorrelation:
    """Mock cross-phase correlation for testing."""

    analyzer1: str
    analyzer2: str
    correlation_type: str
    correlation_score: float
    description: str
    priority: str
    affected_files: Optional[List[str]] = None
    remediation_impact: Optional[str] = None


@dataclass
class MockSmartRecommendation:
    """Mock smart recommendation for testing."""

    id: str
    category: str
    description: str
    priority: str
    impact: str
    effort: str
    rationale: Optional[str] = None
    implementation_notes: Optional[str] = None

    @property
    def title(self) -> str:
        """Generate title from id for backward compatibility."""
        return self.description.split('.')[0] if '.' in self.description else self.description

    @property
    def affected_files(self) -> List[str]:
        """Return empty list for backward compatibility."""
        return []

    @property
    def implementation_guide(self) -> str:
        """Return implementation notes for backward compatibility."""
        return self.implementation_notes or ""


@dataclass
class MockAuditTrailEntry:
    """Mock audit trail entry for testing."""

    phase: str
    started: str
    completed: str
    violations_found: int
    clusters_found: int
    correlations_found: Optional[int] = None


class EnhancedTestDatasets:
    """Predefined test datasets with known connascence patterns."""

    @staticmethod
    def get_connascence_sample_code() -> str:
        """Sample code with multiple connascence types for testing."""
        return """
# Multiple connascence violations for comprehensive testing
class UserProcessor:
    def __init__(self):
        self.status = 1  # CoLiteral - magic number
        self.max_users = 100  # CoLiteral - magic number
        self.format_types = ["json", "xml", "csv"]  # CoPosition + CoLiteral

    def process_users(self, users, format, timeout, retries, debug, validate):
        # CoPosition - parameter order dependency
        if self.status == 1:  # CoLiteral - magic comparison
            return self._process_active(users, format, timeout, retries, debug, validate)
        elif self.status == 2:  # CoLiteral - magic comparison
            return []

    def _process_active(self, users, format, timeout, retries, debug, validate):
        # CoAlgorithm - duplicated processing logic
        results = []
        for i in range(100):  # CoLiteral - magic number
            if i % 10 == 0:  # CoLiteral - magic numbers
                user = self._transform_user(users[i], format)
                if len(user) > 50:  # CoLiteral - magic number
                    results.append(user)
        return results

    def _transform_user(self, user, format):
        # CoAlgorithm + CoLiteral - algorithm duplication with magic strings
        if format == "json":  # CoLiteral - string literal
            return user.strip().lower()
        elif format == "xml":  # CoLiteral - string literal
            return user.strip().upper()
        return user.strip()  # CoAlgorithm - duplicated .strip() calls

    def validate_user(self, user, format, timeout):
        # CoPosition + CoAlgorithm - parameter coupling + algorithm duplication
        if format == "json":  # CoLiteral - duplicated string check
            return user.strip().lower()  # CoAlgorithm - more duplication
        return user.strip()  # CoAlgorithm - more duplication

# CoType - type dependency across classes
class UserValidator:
    def __init__(self):
        self.processor = UserProcessor()  # CoType - class coupling

    def validate_batch(self, users, format="json", timeout=30):
        # CoLiteral + CoPosition - default value coupling
        return self.processor.process_users(users, format, timeout, 3, False, True)
        """

    @staticmethod
    def get_expected_correlations() -> List[MockCorrelation]:
        """Expected cross-phase correlations for the sample code."""
        return [
            MockCorrelation(
                analyzer1="ast_analyzer",
                analyzer2="mece_analyzer",
                correlation_type="algorithm_duplication_overlap",
                correlation_score=0.85,
                description="AST connascence violations overlap with MECE algorithm duplications in transform methods",
                priority="high",
                affected_files=["test_sample.py"],
                remediation_impact="Fixing algorithm duplication will reduce CoAlgorithm violations",
            ),
            MockCorrelation(
                analyzer1="ast_analyzer",
                analyzer2="nasa_analyzer",
                correlation_type="complexity_safety_violation",
                correlation_score=0.72,
                description="High parameter count correlates with NASA Power of Ten violations",
                priority="medium",
                affected_files=["test_sample.py"],
                remediation_impact="Reducing parameters will improve NASA compliance",
            ),
            MockCorrelation(
                analyzer1="mece_analyzer",
                analyzer2="smart_integration",
                correlation_type="duplication_hotspot_correlation",
                correlation_score=0.91,
                description="MECE duplication clusters align with smart integration hotspot detection",
                priority="high",
                affected_files=["test_sample.py"],
                remediation_impact="Hotspot remediation will eliminate duplication clusters",
            ),
            MockCorrelation(
                analyzer1="ast_analyzer",
                analyzer2="smart_integration",
                correlation_type="literal_constant_correlation",
                correlation_score=0.78,
                description="CoLiteral violations correlate with constant extraction recommendations",
                priority="medium",
                affected_files=["test_sample.py"],
                remediation_impact="Extracting constants will reduce literal coupling",
            ),
            MockCorrelation(
                analyzer1="mece_analyzer",
                analyzer2="nasa_analyzer",
                correlation_type="duplication_complexity_correlation",
                correlation_score=0.81,
                description="Code duplication increases cyclomatic complexity",
                priority="high",
                affected_files=["test_sample.py"],
                remediation_impact="Reducing duplication improves complexity metrics",
            ),
        ]

    @staticmethod
    def get_expected_smart_recommendations() -> List[MockSmartRecommendation]:
        """Expected smart recommendations for the sample code."""
        return [
            MockSmartRecommendation(
                id="rec_001",
                category="Architectural Patterns",
                description="Extract constants for magic numbers to eliminate CoLiteral violations",
                priority="high",
                impact="high",
                effort="low",
                rationale="Multiple magic numbers detected across methods",
                implementation_notes="Create Constants class with STATUS_ACTIVE, MAX_USERS, BATCH_SIZE",
            ),
            MockSmartRecommendation(
                id="rec_002",
                category="Method Refactoring",
                description="Reduce parameter count using configuration object pattern",
                priority="medium",
                impact="medium",
                effort="medium",
                rationale="Process methods have excessive parameter coupling",
                implementation_notes="Create ProcessConfig dataclass to encapsulate parameters",
            ),
            MockSmartRecommendation(
                id="rec_003",
                category="Algorithm Optimization",
                description="Eliminate algorithm duplication through strategy pattern",
                priority="high",
                impact="high",
                effort="medium",
                rationale="Transform logic duplicated across multiple methods",
                implementation_notes="Create FormatStrategy interface with JsonStrategy, XmlStrategy implementations",
            ),
            MockSmartRecommendation(
                id="rec_004",
                category="Type Safety",
                description="Introduce enum for format types to reduce CoLiteral violations",
                priority="medium",
                impact="medium",
                effort="low",
                rationale="String literals for format types repeated throughout codebase",
                implementation_notes="Create FormatType enum with JSON, XML, CSV values",
            ),
            MockSmartRecommendation(
                id="rec_005",
                category="Code Organization",
                description="Extract validation logic to separate validator class",
                priority="low",
                impact="medium",
                effort="low",
                rationale="Validation logic scattered across multiple methods",
                implementation_notes="Create UserValidator class with dedicated validation methods",
            ),
        ]

    @staticmethod
    def get_expected_audit_trail() -> List[MockAuditTrailEntry]:
        """Expected audit trail for enhanced analysis."""
        return [
            MockAuditTrailEntry(
                phase="analysis",
                started="2024-01-15T10:00:00.000Z",
                completed="2024-01-15T10:00:02.500Z",
                violations_found=15,
                clusters_found=0,
                correlations_found=0,
            ),
            MockAuditTrailEntry(
                phase="analysis",
                started="2024-01-15T10:00:02.500Z",
                completed="2024-01-15T10:00:04.200Z",
                violations_found=0,
                clusters_found=4,
                correlations_found=0,
            ),
            MockAuditTrailEntry(
                phase="analysis",
                started="2024-01-15T10:00:04.200Z",
                completed="2024-01-15T10:00:05.100Z",
                violations_found=3,
                clusters_found=0,
                correlations_found=0,
            ),
            MockAuditTrailEntry(
                phase="recommendation",
                started="2024-01-15T10:00:05.100Z",
                completed="2024-01-15T10:00:07.800Z",
                violations_found=0,
                clusters_found=0,
                correlations_found=3,
            ),
            MockAuditTrailEntry(
                phase="correlation",
                started="2024-01-15T10:00:07.800Z",
                completed="2024-01-15T10:00:08.900Z",
                violations_found=0,
                clusters_found=0,
                correlations_found=3,
            ),
        ]


class MockEnhancedAnalyzer:
    """Mock enhanced analyzer for controlled testing."""

    def __init__(self, test_mode: str = "success"):
        self.test_mode = test_mode
        self.call_count = 0

    def analyze_path(self, path: str, **kwargs) -> Dict[str, Any]:
        """Mock analysis that returns controlled test data."""
        self.call_count += 1

        # Handle error modes that return error/warning information
        if self.test_mode == "encoding_error":
            return {
                "success": True,
                "findings": [],
                "violations": [],
                "errors": [
                    {"type": "encoding_error", "message": "Failed to decode file with UTF-8", "file": "invalid_utf8.py"},
                    {"type": "encoding_error", "message": "Latin-1 encoding detected", "file": "latin1_file.py"}
                ],
                "warnings": [
                    {"type": "encoding_fallback", "message": "Using fallback encoding detection"}
                ],
                "correlations": [],
                "smart_recommendations": [],
                "audit_trail": [],
                "canonical_policy": "standard",
                "cross_phase_analysis": False,
            }
        elif self.test_mode == "syntax_error":
            return {
                "success": True,
                "findings": [],
                "violations": [],
                "errors": [
                    {"type": "syntax_error", "message": "Missing closing parenthesis", "file": "syntax_error_1.py"},
                    {"type": "syntax_error", "message": "Missing colon after class declaration", "file": "syntax_error_2.py"},
                    {"type": "syntax_error", "message": "Invalid indentation", "file": "syntax_error_3.py"}
                ],
                "correlations": [],
                "smart_recommendations": [],
                "audit_trail": [],
                "canonical_policy": "standard",
                "cross_phase_analysis": False,
            }
        elif self.test_mode == "permission_denied":
            return {
                "success": True,
                "findings": [],
                "violations": [],
                "errors": [
                    {"type": "permission_error", "message": "Permission denied: permission_test.py"}
                ],
                "warnings": [
                    {"type": "permission_warning", "message": "Skipping file due to insufficient permissions"}
                ],
                "correlations": [],
                "smart_recommendations": [],
                "audit_trail": [],
                "canonical_policy": "standard",
                "cross_phase_analysis": False,
            }
        elif self.test_mode == "memory_exhaustion":
            return {
                "success": True,
                "findings": [],
                "violations": [],
                "warnings": [
                    {"type": "memory_warning", "message": "High memory usage detected during analysis"}
                ],
                "correlations": [],
                "smart_recommendations": [],
                "audit_trail": [],
                "canonical_policy": "standard",
                "cross_phase_analysis": False,
            }
        elif self.test_mode == "timeout":
            # Return partial results with timeout indicator
            return {
                "success": True,
                "findings": [],
                "violations": [],
                "partial_results": True,
                "errors": [
                    {"type": "timeout", "message": "Analysis timed out, returning partial results"}
                ],
                "correlations": [],
                "smart_recommendations": [],
                "audit_trail": [],
                "canonical_policy": "standard",
                "cross_phase_analysis": False,
            }
        elif self.test_mode == "empty_project":
            return {
                "success": True,
                "findings": [],
                "violations": [],
                "correlations": [],
                "smart_recommendations": [],
                "audit_trail": [],
                "canonical_policy": "standard",
                "cross_phase_analysis": False,
                "analysis_completed": True,
            }
        elif self.test_mode == "failure":
            raise Exception("Simulated analysis failure")
        elif self.test_mode == "partial_failure":
            return {
                "success": True,
                "findings": [],
                "violations": [],
                "correlations": [],  # Missing correlations
                "smart_recommendations": [asdict(r) for r in EnhancedTestDatasets.get_expected_smart_recommendations()],
                "audit_trail": [asdict(a) for a in EnhancedTestDatasets.get_expected_audit_trail()[:2]],  # Partial audit
                "canonical_policy": "standard",
                "cross_phase_analysis": False,  # Disabled feature
            }

        # Success mode - return complete enhanced results
        # Generate realistic findings count based on path complexity
        violations = self._get_mock_violations()
        correlations_list = [asdict(c) for c in EnhancedTestDatasets.get_expected_correlations()]
        recommendations_list = [asdict(r) for r in EnhancedTestDatasets.get_expected_smart_recommendations()]
        audit_trail_list = [asdict(a) for a in EnhancedTestDatasets.get_expected_audit_trail()]

        return {
            "success": True,
            "findings": violations,  # For compatibility with tests that check findings
            "violations": violations,
            "correlations": correlations_list if kwargs.get("enable_cross_phase_correlation", True) else [],
            "smart_recommendations": recommendations_list if kwargs.get("enable_smart_recommendations", True) else [],
            "audit_trail": audit_trail_list if kwargs.get("enable_audit_trail", True) else [],
            "canonical_policy": kwargs.get("policy", "standard"),
            "cross_phase_analysis": kwargs.get("enable_cross_phase_correlation", False),
            "components_used": {
                "ast_analyzer": True,
                "mece_analyzer": kwargs.get("include_duplication", True),
                "nasa_analyzer": kwargs.get("nasa_validation", False),
                "smart_integration": kwargs.get("enable_smart_recommendations", False),
            },
            "policy_config": {
                "violation_threshold": 0.8,
                "correlation_threshold": kwargs.get("correlation_threshold", 0.7),
                "smart_recommendations_enabled": kwargs.get("enable_smart_recommendations", False),
            },
        }

    def _get_mock_violations(self) -> List[Dict[str, Any]]:
        """Generate mock violations for testing."""
        return [
            {
                "id": "viol_001",
                "type": "connascence_of_identity",
                "severity": "medium",
                "message": "Relying on external database connection state",
                "file": "user_service.py",
                "line": 4,
                "column": 15,
                "description": "Identity coupling to database connection",
            },
            {
                "id": "viol_002",
                "type": "connascence_of_position",
                "severity": "low",
                "message": "Parameter order dependency in get_user method",
                "file": "user_service.py",
                "line": 9,
                "column": 8,
                "description": "Method relies on parameter position",
            },
            {
                "id": "viol_003",
                "type": "connascence_of_type",
                "severity": "high",
                "message": "Tight coupling to UserService implementation",
                "file": "order_service.py",
                "line": 6,
                "column": 12,
                "description": "Type coupling creates maintenance burden",
            },
            {
                "id": "viol_004",
                "type": "connascence_of_algorithm",
                "severity": "medium",
                "message": "Must call get_user before creating order",
                "file": "order_service.py",
                "line": 10,
                "column": 15,
                "description": "Algorithm dependency on service method",
            },
            {
                "id": "viol_005",
                "type": "connascence_of_meaning",
                "severity": "medium",
                "message": "Channel values have implicit meaning",
                "file": "notification_service.py",
                "line": 10,
                "column": 12,
                "description": "Magic strings for channel types",
            },
        ]


class EnhancedTestUtilities:
    """Utility functions for enhanced pipeline testing."""

    @staticmethod
    def validate_enhanced_result(result: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate enhanced analysis result structure and content."""
        errors = []

        # Check required fields
        required_fields = [
            "success",
            "violations",
            "correlations",
            "smart_recommendations",
            "audit_trail",
            "canonical_policy",
            "cross_phase_analysis",
        ]

        for field in required_fields:
            if field not in result:
                errors.append(f"Missing required field: {field}")

        # Validate correlations structure
        if result.get("correlations"):
            for i, corr in enumerate(result["correlations"]):
                required_corr_fields = ["analyzer1", "analyzer2", "correlation_score", "description"]
                for field in required_corr_fields:
                    if field not in corr:
                        errors.append(f"Correlation {i} missing field: {field}")

                # Validate correlation score range
                if "correlation_score" in corr:
                    score = corr["correlation_score"]
                    if not (0.0 <= score <= 1.0):
                        errors.append(f"Correlation {i} score {score} out of range [0.0, 1.0]")

        # Validate smart recommendations structure
        if result.get("smart_recommendations"):
            for i, rec in enumerate(result["smart_recommendations"]):
                required_rec_fields = ["category", "description", "priority", "impact", "effort"]
                for field in required_rec_fields:
                    if field not in rec:
                        errors.append(f"Recommendation {i} missing field: {field}")

                # Validate priority values
                if "priority" in rec and rec["priority"] not in ["low", "medium", "high", "critical"]:
                    errors.append(f"Recommendation {i} invalid priority: {rec['priority']}")

        # Validate audit trail structure
        if result.get("audit_trail"):
            for i, entry in enumerate(result["audit_trail"]):
                required_audit_fields = ["phase", "started", "completed"]
                for field in required_audit_fields:
                    if field not in entry:
                        errors.append(f"Audit trail entry {i} missing field: {field}")

        return len(errors) == 0, errors

    @staticmethod
    def measure_performance(func, *args, **kwargs) -> Tuple[Any, float, float]:
        """Measure function performance (execution time and memory usage)."""
        process = psutil.Process()

        # Get initial memory usage
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Measure execution time
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()

        # Get final memory usage
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_delta = final_memory - initial_memory

        execution_time = end_time - start_time

        return result, execution_time, memory_delta

    @staticmethod
    def create_test_file(content: str, file_path: Path) -> Path:
        """Create temporary test file with specified content."""
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        return file_path

    @staticmethod
    def assert_correlation_quality(correlations: List[Dict[str, Any]], min_score: float = 0.7) -> None:
        """Assert that correlations meet quality thresholds."""
        assert len(correlations) > 0, "No correlations found"

        for corr in correlations:
            assert (
                corr["correlation_score"] >= min_score
            ), f"Correlation {corr.get('description', 'unknown')} score {corr['correlation_score']} below threshold {min_score}"

    @staticmethod
    def assert_recommendations_actionable(recommendations: List[Dict[str, Any]]) -> None:
        """Assert that recommendations are actionable and well-formed."""
        assert len(recommendations) > 0, "No recommendations found"

        for rec in recommendations:
            assert rec.get("description", "").strip(), "Recommendation missing description"
            assert rec.get("category", "").strip(), "Recommendation missing category"
            assert rec.get("priority") in [
                "low",
                "medium",
                "high",
                "critical",
            ], f"Invalid priority: {rec.get('priority')}"

    @staticmethod
    def assert_audit_trail_complete(audit_trail: List[Dict[str, Any]], expected_phases: List[str]) -> None:
        """Assert that audit trail contains expected phases."""
        actual_phases = [entry["phase"] for entry in audit_trail]

        for phase in expected_phases:
            assert phase in actual_phases, f"Missing expected phase: {phase}"

        # Verify timing makes sense
        for entry in audit_trail:
            start_time = entry.get("started")
            end_time = entry.get("completed")
            assert start_time and end_time, f"Phase {entry['phase']} missing timing information"


@pytest.fixture
def enhanced_test_datasets():
    """Fixture providing enhanced test datasets."""
    return EnhancedTestDatasets()


@pytest.fixture
def mock_enhanced_analyzer():
    """Fixture providing mock enhanced analyzer."""
    return MockEnhancedAnalyzer()


@pytest.fixture
def enhanced_test_utilities():
    """Fixture providing enhanced test utilities."""
    return EnhancedTestUtilities()


@pytest.fixture
def sample_code_file(tmp_path):
    """Fixture providing sample code file for testing."""
    sample_file = tmp_path / "test_sample.py"
    sample_file.write_text(EnhancedTestDatasets.get_connascence_sample_code())
    return sample_file


# Performance testing decorators
def performance_test(max_time_seconds: float = 30.0, max_memory_mb: float = 100.0):
    """Decorator for performance testing with time and memory limits.

    This decorator is compatible with pytest fixtures by using functools.wraps
    to preserve the original function signature for fixture injection.
    """
    import functools

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            result, exec_time, memory_delta = EnhancedTestUtilities.measure_performance(func, *args, **kwargs)

            assert (
                exec_time <= max_time_seconds
            ), f"Function {func.__name__} took {exec_time:.2f}s, exceeds limit {max_time_seconds}s"
            assert (
                memory_delta <= max_memory_mb
            ), f"Function {func.__name__} used {memory_delta:.2f}MB memory, exceeds limit {max_memory_mb}MB"

            return result

        return wrapper

    return decorator


def integration_test(interfaces: List[str]):
    """Decorator for integration tests targeting specific interfaces.

    This decorator marks tests for integration testing and preserves
    the original function signature for pytest fixture injection.
    """
    import functools

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        wrapper._integration_test = True
        wrapper._target_interfaces = interfaces
        return wrapper

    return decorator
