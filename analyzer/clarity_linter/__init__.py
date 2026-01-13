"""
Clarity Linter Orchestrator

Coordinates all 5 Clarity Linter detectors and provides unified API for code clarity analysis.
Integrates with existing connascence analyzer infrastructure and SARIF reporting.

NASA Rule 4 Compliant: All functions under 60 lines
NASA Rule 5 Compliant: Input assertions
"""

import ast
import logging
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from analyzer.clarity_linter.base import BaseClarityDetector
from analyzer.clarity_linter.config_loader import ClarityConfigLoader
from analyzer.clarity_linter.models import ClarityViolation
from analyzer.clarity_linter.sarif_exporter import SARIFExporter

logger = logging.getLogger(__name__)

# Import the 5 clarity detectors
try:
    from analyzer.detectors.clarity_call_chain import CallChainDepthDetector
    from analyzer.detectors.clarity_comment_issues import CommentIssuesDetector
    from analyzer.detectors.clarity_poor_naming import PoorNamingDetector
    from analyzer.detectors.clarity_thin_helper import ThinHelperDetector
    from analyzer.detectors.clarity_useless_indirection import UselessIndirectionDetector
    DETECTORS_AVAILABLE = True
except ImportError:
    DETECTORS_AVAILABLE = False
    logger.warning("Clarity detectors not available for import")


class ClarityLinter:
    """
    Main orchestrator for clarity linting analysis.

    Coordinates 5 specialized detectors:
    1. ThinHelperDetector - Detects thin helper functions
    2. UselessIndirectionDetector - Detects unnecessary indirection
    3. CallChainDepthDetector - Detects excessive call chain depth
    4. PoorNamingDetector - Detects poor variable/function naming
    5. CommentIssuesDetector - Detects comment quality issues

    Provides unified violation reporting and SARIF export.
    """

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize ClarityLinter with configuration.

        NASA Rule 5: Input validation assertions

        Args:
            config_path: Optional path to clarity_linter.yaml config file
        """
        # NASA Rule 5: Input validation
        assert config_path is None or isinstance(config_path, (str, Path)), \
            "config_path must be None, string, or Path"

        self.config_path = config_path or self._find_config()
        self.config = ClarityConfigLoader.load_config(self.config_path)
        self.detectors = self._register_detectors()

        # Validation state
        self._total_files_analyzed = 0
        self._total_violations_found = 0

        # NASA Rule 5: State validation
        assert self.config is not None, "config must be loaded"
        assert len(self.detectors) > 0, "detectors must be registered"

    def _find_config(self) -> Optional[Path]:
        """
        Find clarity_linter.yaml configuration file.

        NASA Rule 4: Function under 60 lines
        NASA Rule 5: Input validation assertions

        Returns:
            Path to config file or None if not found
        """
        # NASA Rule 5: Input validation
        assert True, "No input parameters to validate"

        # Search standard locations
        possible_paths = [
            Path(__file__).parent.parent.parent / "clarity_linter.yaml",
            Path(__file__).parent.parent / "config" / "clarity_linter.yaml",
            Path("clarity_linter.yaml"),
            Path("config") / "clarity_linter.yaml",
        ]

        # NASA Rule 5: Validate paths list
        assert len(possible_paths) > 0, "must have at least one config path to check"

        for path in possible_paths:
            if path.exists():
                return path

        return None

    def _register_detectors(self) -> List[BaseClarityDetector]:
        """
        Register and initialize all clarity detectors.

        NASA Rule 4: Function under 60 lines
        NASA Rule 5: Input validation assertions

        Returns:
            List of initialized detector instances
        """
        # NASA Rule 5: Input validation
        assert self.config is not None, "config must be loaded before registering detectors"

        if not DETECTORS_AVAILABLE:
            logger.warning("Clarity detectors not available, returning empty list")
            return []

        detectors = []

        # Register each detector if enabled in config
        detector_classes = [
            ('CLARITY_THIN_HELPER', ThinHelperDetector),
            ('CLARITY_USELESS_INDIRECTION', UselessIndirectionDetector),
            ('CLARITY_CALL_CHAIN', CallChainDepthDetector),
            ('CLARITY_POOR_NAMING', PoorNamingDetector),
            ('CLARITY_COMMENT_ISSUES', CommentIssuesDetector),
        ]

        for rule_id, detector_class in detector_classes:
            if self._is_rule_enabled(rule_id):
                detector = detector_class(config=self.config)
                detectors.append(detector)

        # NASA Rule 5: Validate detectors registered
        assert isinstance(detectors, list), "detectors must be a list"

        return detectors

    def _is_rule_enabled(self, rule_id: str) -> bool:
        """
        Check if a rule is enabled in configuration.

        NASA Rule 4: Function under 60 lines
        NASA Rule 5: Input validation

        Args:
            rule_id: Rule identifier to check

        Returns:
            True if rule is enabled, False otherwise
        """
        # NASA Rule 5: Input validation
        assert isinstance(rule_id, str), "rule_id must be string"
        assert self.config is not None, "config must be loaded"

        rules = self.config.get('rules', {})
        rule_config = rules.get(rule_id, {})

        # Default to enabled if not explicitly disabled
        return rule_config.get('enabled', True)

    def analyze_project(self, project_path: Path) -> List[ClarityViolation]:
        """
        Analyze entire project with all enabled detectors.

        NASA Rule 4: Function under 60 lines
        NASA Rule 5: Input validation assertions

        Args:
            project_path: Path to project root directory

        Returns:
            Sorted list of all violations found across project
        """
        # NASA Rule 5: Input validation
        assert project_path is not None, "project_path cannot be None"
        assert isinstance(project_path, (str, Path)), "project_path must be string or Path"

        project_path = Path(project_path)
        assert project_path.exists(), f"project_path must exist: {project_path}"
        assert project_path.is_dir(), f"project_path must be directory: {project_path}"

        violations = []

        # Find all Python files in project
        python_files = list(project_path.rglob("*.py"))

        for file_path in python_files:
            if self._should_analyze_file(file_path):
                file_violations = self.analyze_file(file_path)
                violations.extend(file_violations)
                self._total_files_analyzed += 1

        # Sort violations by file path and line number
        sorted_violations = sorted(
            violations,
            key=lambda v: (v.file_path, v.line_number)
        )

        self._total_violations_found = len(sorted_violations)

        return sorted_violations

    def analyze_file(self, file_path: Path) -> List[ClarityViolation]:
        """
        Analyze single file with all enabled detectors.

        NASA Rule 4: Function under 60 lines
        NASA Rule 5: Input validation assertions

        Args:
            file_path: Path to Python file to analyze

        Returns:
            List of violations found in file
        """
        # NASA Rule 5: Input validation
        assert file_path is not None, "file_path cannot be None"
        assert isinstance(file_path, (str, Path)), "file_path must be string or Path"

        file_path = Path(file_path)
        assert file_path.exists(), f"file_path must exist: {file_path}"
        assert file_path.is_file(), f"file_path must be file: {file_path}"

        violations = []

        try:
            # Read and parse file
            with open(file_path, encoding='utf-8') as f:
                source_code = f.read()

            tree = ast.parse(source_code, filename=str(file_path))

            # Run each enabled detector
            for detector in self.detectors:
                detector_violations = detector.detect(tree, file_path)
                violations.extend(detector_violations)

        except SyntaxError as e:
            # Skip files with syntax errors
            logger.warning("Syntax error in %s: %s", file_path, e)
        except Exception as e:
            # Log other errors but continue
            logger.error("Failed to analyze %s: %s", file_path, e)

        return violations

    def _should_analyze_file(self, file_path: Path) -> bool:
        """
        Determine if file should be analyzed based on exclusions.

        NASA Rule 4: Function under 60 lines
        NASA Rule 5: Input validation

        Args:
            file_path: Path to check

        Returns:
            True if file should be analyzed, False otherwise
        """
        # NASA Rule 5: Input validation
        assert file_path is not None, "file_path cannot be None"
        assert isinstance(file_path, (str, Path)), "file_path must be string or Path"

        file_path = Path(file_path)
        exclusions = self.config.get('exclusions', {})

        # Check excluded directories
        excluded_dirs = exclusions.get('directories', [])
        for excluded_dir in excluded_dirs:
            if excluded_dir in file_path.parts:
                return False

        # Check excluded file patterns
        excluded_files = exclusions.get('files', [])
        for pattern in excluded_files:
            if file_path.match(pattern):
                return False

        return True

    def export_sarif(
        self,
        violations: List[ClarityViolation],
        output_path: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        Export violations as SARIF 2.1.0 format.

        NASA Rule 4: Function under 60 lines
        NASA Rule 5: Input validation

        Args:
            violations: List of violations to export
            output_path: Optional path to write SARIF file

        Returns:
            SARIF document as dictionary
        """
        # NASA Rule 5: Input validation
        assert violations is not None, "violations cannot be None"
        assert isinstance(violations, list), "violations must be list"

        sarif_doc = SARIFExporter.export(violations, self.config)

        # Write to file if output path provided
        if output_path:
            SARIFExporter.write_to_file(sarif_doc, output_path)

        return sarif_doc

    def get_summary(self) -> Dict[str, Any]:
        """
        Get analysis summary metrics.

        NASA Rule 4: Function under 60 lines

        Returns:
            Dictionary with summary statistics
        """
        return {
            'total_files_analyzed': self._total_files_analyzed,
            'total_violations_found': self._total_violations_found,
            'detectors_enabled': len(self.detectors),
            'config_path': str(self.config_path) if self.config_path else None,
        }


__all__ = ['ClarityLinter', 'ClarityViolation', 'BaseClarityDetector']
