"""
Unit tests for Clarity Linter Orchestrator

Tests ClarityLinter, BaseClarityDetector, and related components.

NASA Rule 4 Compliant: All test functions under 60 lines
"""

import ast
from pathlib import Path
from typing import List

import pytest

from analyzer.clarity_linter import BaseClarityDetector, ClarityLinter, ClarityViolation
from analyzer.clarity_linter.config_loader import ClarityConfigLoader
from analyzer.clarity_linter.models import ClaritySummary
from analyzer.clarity_linter.sarif_exporter import SARIFExporter


class MockDetector(BaseClarityDetector):
    """Mock detector for testing."""

    rule_id = "MOCK_RULE"
    rule_name = "Mock Rule"
    default_severity = "medium"

    def detect(self, tree: ast.Module, file_path: Path) -> List[ClarityViolation]:
        """Return mock violation."""
        return [
            self.create_violation(
                file_path=file_path,
                line_number=1,
                description="Mock violation for testing",
                recommendation="Fix the mock issue"
            )
        ]


class TestClarityLinter:
    """Test suite for ClarityLinter orchestrator."""

    def test_init_default_config(self):
        """Test initialization with default configuration."""
        linter = ClarityLinter()

        assert linter.config is not None
        assert isinstance(linter.config, dict)
        assert isinstance(linter.detectors, list)
        assert linter._total_files_analyzed == 0
        assert linter._total_violations_found == 0

    def test_init_custom_config(self, tmp_path):
        """Test initialization with custom config file."""
        config_file = tmp_path / "test_clarity.yaml"
        config_file.write_text("""
metadata:
  name: Test Config
  version: 1.0.0
rules:
  CLARITY_THIN_HELPER:
    enabled: false
exclusions:
  directories:
    - test_exclude
        """)

        linter = ClarityLinter(config_path=config_file)

        assert linter.config is not None
        assert linter.config['metadata']['name'] == 'Test Config'

    def test_find_config(self):
        """Test config file discovery."""
        linter = ClarityLinter()
        config_path = linter._find_config()

        # Should find config or return None
        assert config_path is None or Path(config_path).exists()

    def test_register_detectors(self):
        """Test detector registration."""
        linter = ClarityLinter()

        # Should have registered detectors
        assert isinstance(linter.detectors, list)

        # Each detector should be BaseClarityDetector
        for detector in linter.detectors:
            assert isinstance(detector, BaseClarityDetector)
            assert hasattr(detector, 'rule_id')
            assert hasattr(detector, 'rule_name')
            assert hasattr(detector, 'severity')

    def test_analyze_file_syntax_error(self, tmp_path):
        """Test analyzing file with syntax error."""
        # Create file with syntax error
        bad_file = tmp_path / "bad_syntax.py"
        bad_file.write_text("def broken(\n  # Missing closing paren")

        linter = ClarityLinter()
        violations = linter.analyze_file(bad_file)

        # Should return empty list for syntax errors
        assert violations == []

    def test_analyze_file_valid(self, tmp_path):
        """Test analyzing valid Python file."""
        # Create valid Python file
        valid_file = tmp_path / "valid.py"
        valid_file.write_text("""
def example_function():
    '''Example function.'''
    return 42
        """)

        linter = ClarityLinter()
        violations = linter.analyze_file(valid_file)

        # Should return list (may be empty or have violations)
        assert isinstance(violations, list)

    def test_should_analyze_file_excluded_dir(self):
        """Test file exclusion based on directory."""
        linter = ClarityLinter()

        # Should exclude files in excluded directories
        excluded_file = Path("node_modules") / "test.py"
        assert not linter._should_analyze_file(excluded_file)

        venv_file = Path("venv") / "lib" / "test.py"
        assert not linter._should_analyze_file(venv_file)

    def test_should_analyze_file_excluded_pattern(self):
        """Test file exclusion based on pattern."""
        linter = ClarityLinter()

        # Should exclude files matching patterns
        minified_file = Path("dist") / "app.min.js"
        # Note: .min.js is in exclusions
        # Python files should be analyzed
        python_file = Path("src") / "module.py"
        assert linter._should_analyze_file(python_file)

    def test_get_summary(self):
        """Test summary generation."""
        linter = ClarityLinter()
        linter._total_files_analyzed = 5
        linter._total_violations_found = 10

        summary = linter.get_summary()

        assert summary['total_files_analyzed'] == 5
        assert summary['total_violations_found'] == 10
        assert summary['detectors_enabled'] == len(linter.detectors)
        assert 'config_path' in summary


class TestBaseClarityDetector:
    """Test suite for BaseClarityDetector base class."""

    def test_init_default_config(self):
        """Test detector initialization with default config."""
        detector = MockDetector()

        assert detector.config == {}
        assert isinstance(detector.violations, list)
        assert len(detector.violations) == 0
        assert detector.severity == "medium"
        assert detector.enabled is True

    def test_init_with_config(self):
        """Test detector initialization with custom config."""
        config = {
            'rules': {
                'MOCK_RULE': {
                    'enabled': False,
                    'severity': 'high'
                }
            }
        }

        detector = MockDetector(config=config)

        assert detector.severity == 'high'
        assert detector.enabled is False

    def test_is_enabled(self):
        """Test enabled status checking."""
        # Enabled by default
        detector1 = MockDetector()
        assert detector1.is_enabled() is True

        # Disabled in config
        config = {
            'rules': {
                'MOCK_RULE': {
                    'enabled': False
                }
            }
        }
        detector2 = MockDetector(config=config)
        assert detector2.is_enabled() is False

    def test_detect_abstract_method(self, tmp_path):
        """Test detect method returns violations."""
        detector = MockDetector()

        test_file = tmp_path / "test.py"
        test_file.write_text("print('test')")

        tree = ast.parse("print('test')")
        violations = detector.detect(tree, test_file)

        assert isinstance(violations, list)
        assert len(violations) == 1
        assert isinstance(violations[0], ClarityViolation)

    def test_create_violation(self, tmp_path):
        """Test violation creation."""
        detector = MockDetector()
        test_file = tmp_path / "test.py"

        violation = detector.create_violation(
            file_path=test_file,
            line_number=10,
            description="Test violation",
            recommendation="Fix it"
        )

        assert violation.rule_id == "MOCK_RULE"
        assert violation.rule_name == "Mock Rule"
        assert violation.severity == "medium"
        assert violation.line_number == 10
        assert violation.description == "Test violation"
        assert violation.recommendation == "Fix it"

    def test_reset(self):
        """Test detector state reset."""
        detector = MockDetector()
        detector.violations = [ClarityViolation(
            rule_id="TEST",
            rule_name="Test",
            severity="low",
            file_path="test.py",
            line_number=1,
            description="Test",
            recommendation="Fix"
        )]

        detector.reset()

        assert len(detector.violations) == 0

    def test_get_metrics(self):
        """Test detector metrics retrieval."""
        detector = MockDetector()
        metrics = detector.get_metrics()

        assert metrics['rule_id'] == 'MOCK_RULE'
        assert metrics['rule_name'] == 'Mock Rule'
        assert metrics['severity'] == 'medium'
        assert metrics['enabled'] is True
        assert metrics['violations_found'] == 0


class TestClarityViolation:
    """Test suite for ClarityViolation dataclass."""

    def test_violation_creation(self):
        """Test creating violation."""
        violation = ClarityViolation(
            rule_id="TEST001",
            rule_name="Test Rule",
            severity="high",
            file_path="test.py",
            line_number=42,
            description="Test description",
            recommendation="Test recommendation"
        )

        assert violation.rule_id == "TEST001"
        assert violation.severity == "high"
        assert violation.line_number == 42

    def test_to_dict(self):
        """Test violation conversion to dict."""
        violation = ClarityViolation(
            rule_id="TEST001",
            rule_name="Test Rule",
            severity="medium",
            file_path="test.py",
            line_number=10,
            description="Test",
            recommendation="Fix",
            code_snippet="test code"
        )

        result = violation.to_dict()

        assert result['rule_id'] == "TEST001"
        assert result['severity'] == "medium"
        assert result['line_number'] == 10
        assert result['code_snippet'] == "test code"

    def test_to_connascence_violation(self):
        """Test conversion to connascence format."""
        violation = ClarityViolation(
            rule_id="TEST001",
            rule_name="Test Rule",
            severity="high",
            file_path="test.py",
            line_number=5,
            description="Test violation",
            recommendation="Fix it"
        )

        connascence = violation.to_connascence_violation()

        assert connascence['type'] == "TEST001"
        assert connascence['severity'] == "high"
        assert connascence['file_path'] == "test.py"
        assert connascence['line_number'] == 5
        assert connascence['context']['clarity_violation'] is True


class TestClaritySummary:
    """Test suite for ClaritySummary dataclass."""

    def test_summary_creation(self):
        """Test creating empty summary."""
        summary = ClaritySummary()

        assert summary.total_files == 0
        assert summary.total_violations == 0
        assert isinstance(summary.violations_by_severity, dict)

    def test_from_violations(self):
        """Test creating summary from violations list."""
        violations = [
            ClarityViolation(
                rule_id="TEST001",
                rule_name="Test 1",
                severity="high",
                file_path="file1.py",
                line_number=1,
                description="Test",
                recommendation="Fix"
            ),
            ClarityViolation(
                rule_id="TEST002",
                rule_name="Test 2",
                severity="medium",
                file_path="file2.py",
                line_number=1,
                description="Test",
                recommendation="Fix"
            ),
            ClarityViolation(
                rule_id="TEST001",
                rule_name="Test 1",
                severity="high",
                file_path="file1.py",
                line_number=2,
                description="Test",
                recommendation="Fix"
            )
        ]

        summary = ClaritySummary.from_violations(violations, total_files=2)

        assert summary.total_files == 2
        assert summary.total_violations == 3
        assert summary.violations_by_severity['high'] == 2
        assert summary.violations_by_severity['medium'] == 1
        assert summary.violations_by_rule['TEST001'] == 2
        assert summary.violations_by_rule['TEST002'] == 1


class TestClarityConfigLoader:
    """Test suite for ClarityConfigLoader."""

    def test_load_default_config(self):
        """Test loading default configuration."""
        config = ClarityConfigLoader.load_config()

        assert config is not None
        assert 'metadata' in config
        assert 'rules' in config
        assert 'exclusions' in config

    def test_load_from_file(self, tmp_path):
        """Test loading configuration from file."""
        config_file = tmp_path / "test_config.yaml"
        config_file.write_text("""
metadata:
  name: Test
  version: 1.0.0
rules:
  TEST_RULE:
    enabled: true
    severity: high
exclusions:
  directories:
    - test
        """)

        config = ClarityConfigLoader.load_config(config_file)

        assert config['metadata']['name'] == 'Test'
        assert 'TEST_RULE' in config['rules']

    def test_get_rule_config(self):
        """Test getting rule-specific configuration."""
        config = {
            'rules': {
                'TEST_RULE': {
                    'enabled': True,
                    'severity': 'high',
                    'threshold': 5
                }
            }
        }

        rule_config = ClarityConfigLoader.get_rule_config(config, 'TEST_RULE')

        assert rule_config['enabled'] is True
        assert rule_config['severity'] == 'high'
        assert rule_config['threshold'] == 5


class TestSARIFExporter:
    """Test suite for SARIFExporter."""

    def test_export_empty_violations(self):
        """Test exporting empty violations list."""
        violations = []
        sarif_doc = SARIFExporter.export(violations)

        assert sarif_doc['$schema'] == SARIFExporter.SARIF_SCHEMA
        assert sarif_doc['version'] == SARIFExporter.SARIF_VERSION
        assert len(sarif_doc['runs']) == 1
        assert len(sarif_doc['runs'][0]['results']) == 0

    def test_export_with_violations(self):
        """Test exporting violations to SARIF."""
        violations = [
            ClarityViolation(
                rule_id="TEST001",
                rule_name="Test Rule",
                severity="high",
                file_path="test.py",
                line_number=10,
                description="Test violation",
                recommendation="Fix it",
                code_snippet="test code"
            )
        ]

        sarif_doc = SARIFExporter.export(violations)

        assert len(sarif_doc['runs'][0]['results']) == 1
        result = sarif_doc['runs'][0]['results'][0]
        assert result['ruleId'] == "TEST001"
        assert result['level'] == 'error'  # high -> error
        assert result['message']['text'] == "Test violation"

    def test_severity_mapping(self):
        """Test severity to SARIF level mapping."""
        assert SARIFExporter._map_severity('critical') == 'error'
        assert SARIFExporter._map_severity('high') == 'error'
        assert SARIFExporter._map_severity('medium') == 'warning'
        assert SARIFExporter._map_severity('low') == 'note'
        assert SARIFExporter._map_severity('info') == 'note'

    def test_write_to_file(self, tmp_path):
        """Test writing SARIF document to file."""
        sarif_doc = {
            '$schema': SARIFExporter.SARIF_SCHEMA,
            'version': SARIFExporter.SARIF_VERSION,
            'runs': []
        }

        output_file = tmp_path / "test.sarif"
        SARIFExporter.write_to_file(sarif_doc, output_file)

        assert output_file.exists()
        import json
        with open(output_file) as f:
            loaded = json.load(f)

        assert loaded['version'] == SARIFExporter.SARIF_VERSION


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
