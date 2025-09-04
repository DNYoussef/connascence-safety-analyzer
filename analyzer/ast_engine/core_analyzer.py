"""
Core AST-based Connascence Analyzer

REFACTORED VERSION: This class now delegates to AnalyzerOrchestrator to resolve God Object violation.
The original 881-line monolithic class has been split into 6 specialized components:
- BaseConnascenceAnalyzer (core functionality)
- PositionAnalyzer (CoP detection) 
- MeaningAnalyzer (CoM/CoN/CoT detection)
- AlgorithmAnalyzer (CoA/CoE/CoV/CoTi detection)
- GodObjectAnalyzer (size detection)
- AnalyzerOrchestrator (coordination)

This provides backward compatibility while using the new modular architecture.

CONSOLIDATED: Merged functionality from legacy analyzer/connascence_analyzer.py:
- License validation integration
- CLI argument support
- Fallback detection methods
"""

import ast
import json
import sys
import argparse
import logging
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass, asdict

from ..thresholds import (
    ThresholdConfig, WeightConfig, PolicyPreset
)
from policy.manager import PolicyManager
from .violations import Violation, AnalysisResult
from .analyzer_orchestrator import AnalyzerOrchestrator

logger = logging.getLogger(__name__)


@dataclass
class ConnascenceViolation:
    """Legacy violation format for backward compatibility"""
    type: str
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    file_path: str
    line_number: int
    description: str
    suggestion: str


class ConnascenceASTAnalyzer:
    """
    Enhanced AST-based connascence analyzer.
    
    REFACTORED: Now delegates to specialized analyzer components instead of 
    containing all analysis logic in a single monolithic class.
    
    This resolves the God Object violation while maintaining full backward compatibility.
    """
    
    def __init__(
        self, 
        thresholds: Optional[ThresholdConfig] = None,
        weights: Optional[WeightConfig] = None,
        policy_preset: Optional[PolicyPreset] = None,
        policy_name: Optional[str] = None,
        exclusions: Optional[List[str]] = None
    ):
        """Initialize the analyzer with delegated orchestrator."""
        # Initialize policy manager for enterprise presets
        self.policy_manager = PolicyManager()
        
        # Apply policy preset if specified by name
        if policy_name and policy_name in self.policy_manager.presets:
            policy_config = self.policy_manager.get_preset(policy_name)
            if not thresholds:
                thresholds = self._policy_to_thresholds(policy_config)
        
        # Delegate to the new modular architecture
        self._orchestrator = AnalyzerOrchestrator(
            thresholds=thresholds,
            weights=weights, 
            policy_preset=policy_preset,
            exclusions=exclusions
        )
        
        # Expose orchestrator properties for backward compatibility
        self.thresholds = self._orchestrator.thresholds
        self.weights = self._orchestrator.weights
        self.policy_preset = self._orchestrator.policy_preset
        self.exclusions = self._orchestrator.exclusions
        self.violations = self._orchestrator.violations
        self.file_stats = self._orchestrator.file_stats
        self.current_file_path = self._orchestrator.current_file_path
        self.current_source_lines = self._orchestrator.current_source_lines
        self.analysis_start_time = self._orchestrator.analysis_start_time
    
    def should_analyze_file(self, file_path: Path) -> bool:
        """Check if file should be analyzed based on exclusions."""
        return self._orchestrator.should_analyze_file(file_path)
    
    def analyze_string(self, source_code: str, filename: str = "string_input.py") -> List[Violation]:
        """Analyze source code string for connascence violations."""
        result = self._orchestrator.analyze_string(source_code, filename)
        self._sync_state_from_orchestrator()
        return result
    
    def analyze_file(self, file_path: Path) -> List[Violation]:
        """Analyze a single file for connascence violations."""
        result = self._orchestrator.analyze_file(file_path)
        self._sync_state_from_orchestrator()
        return result
    
    def analyze_directory(self, directory: Path) -> AnalysisResult:
        """Analyze all Python files in a directory tree."""
        result = self._orchestrator.analyze_directory(directory)
        self._sync_state_from_orchestrator()
        return result
    
    def _sync_state_from_orchestrator(self):
        """Synchronize state from orchestrator for backward compatibility."""
        self.violations = self._orchestrator.violations
        self.file_stats = self._orchestrator.file_stats
        self.current_file_path = self._orchestrator.current_file_path
        self.current_source_lines = self._orchestrator.current_source_lines
        self.analysis_start_time = self._orchestrator.analysis_start_time
    
    # Legacy method compatibility - delegate to orchestrator's utility methods
    def _get_code_snippet(self, node, context_lines: int = 2) -> str:
        """Legacy method for backward compatibility."""
        return self._orchestrator.get_code_snippet(node, context_lines)
    
    def _get_context_lines(self, line_number: int, context: int = 2) -> str:
        """Legacy method for backward compatibility."""
        return self._orchestrator.get_context_lines(line_number, context)
    
    def _calculate_file_stats(self, tree, violations) -> dict:
        """Legacy method for backward compatibility."""
        return self._orchestrator.calculate_file_stats(tree, violations)
    
    def _calculate_summary_metrics(self, violations) -> dict:
        """Legacy method for backward compatibility."""
        return self._orchestrator.calculate_summary_metrics(violations)
    
    def _policy_to_thresholds(self, policy_config: dict) -> ThresholdConfig:
        """Convert policy configuration to ThresholdConfig."""
        thresholds_data = policy_config.get('thresholds', {})
        return ThresholdConfig(
            max_positional_params=thresholds_data.get('max_positional_params', 6),
            god_class_methods=thresholds_data.get('god_class_methods', 25),
            max_cyclomatic_complexity=thresholds_data.get('max_cyclomatic_complexity', 15)
        )


# Legacy ConnascenceAnalyzer class for backward compatibility
class LegacyConnascenceAnalyzer:
    """Legacy analyzer from connascence_analyzer.py - now delegated to ConnascenceASTAnalyzer"""
    
    def __init__(self, strict_mode: bool = False):
        self.strict_mode = strict_mode
        self.violations = []
        # Delegate to the new modular architecture
        self._modern_analyzer = ConnascenceASTAnalyzer()

    def analyze_directory(self, directory: Path) -> List[ConnascenceViolation]:
        """Analyze all Python files in directory for connascence"""
        # Use modern analyzer and convert to legacy format
        result = self._modern_analyzer.analyze_directory(directory)
        
        legacy_violations = []
        for violation in result.violations:
            legacy_violations.append(ConnascenceViolation(
                type=violation.type.value if hasattr(violation.type, 'value') else str(violation.type),
                severity=violation.severity.value if hasattr(violation.severity, 'value') else str(violation.severity),
                file_path=violation.file_path,
                line_number=violation.line_number,
                description=violation.description,
                suggestion=violation.recommendation
            ))
        
        self.violations = legacy_violations
        return legacy_violations

    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if file should be skipped - delegated to modern analyzer"""
        return not self._modern_analyzer.should_analyze_file(file_path)

    def _analyze_file(self, file_path: Path) -> List[ConnascenceViolation]:
        """Analyze single file for connascence violations - delegated"""
        violations = self._modern_analyzer.analyze_file(file_path)
        legacy_violations = []
        for violation in violations:
            legacy_violations.append(ConnascenceViolation(
                type=violation.type.value if hasattr(violation.type, 'value') else str(violation.type),
                severity=violation.severity.value if hasattr(violation.severity, 'value') else str(violation.severity),
                file_path=violation.file_path,
                line_number=violation.line_number,
                description=violation.description,
                suggestion=violation.recommendation
            ))
        return legacy_violations

    # Legacy methods for backward compatibility - basic implementations
    def _check_connascence_of_name(self, tree: ast.AST, file_path: Path) -> List[ConnascenceViolation]:
        """Legacy method - basic name connascence check"""
        violations = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Str):
                if len(node.s) > 3 and node.s.isupper():
                    violations.append(
                        ConnascenceViolation(
                            type="Connascence of Name",
                            severity="MEDIUM",
                            file_path=str(file_path),
                            line_number=getattr(node, 'lineno', 1),
                            description=f"Hardcoded string constant: {node.s}",
                            suggestion="Extract to named constant",
                        )
                    )
        return violations

    def _check_connascence_of_type(self, tree: ast.AST, file_path: Path) -> List[ConnascenceViolation]:
        """Legacy method - basic type connascence check"""
        violations = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Num):
                if isinstance(node.n, (int, float)) and abs(node.n) > 1 and node.n not in [0, 1, -1]:
                    violations.append(
                        ConnascenceViolation(
                            type="Connascence of Type",
                            severity="LOW",
                            file_path=str(file_path),
                            line_number=getattr(node, 'lineno', 1),
                            description=f"Magic number: {node.n}",
                            suggestion="Extract to named constant",
                        )
                    )
        return violations

    def _check_connascence_of_meaning(self, tree: ast.AST, file_path: Path) -> List[ConnascenceViolation]:
        """Legacy method - basic meaning connascence check"""
        violations = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Check for functions with multiple boolean parameters
                bool_args = [
                    arg for arg in node.args if isinstance(arg, ast.NameConstant) and isinstance(arg.value, bool)
                ]
                if len(bool_args) >= 2:
                    violations.append(
                        ConnascenceViolation(
                            type="Connascence of Meaning",
                            severity="HIGH",
                            file_path=str(file_path),
                            line_number=getattr(node, 'lineno', 1),
                            description="Multiple boolean parameters suggest meaning connascence",
                            suggestion="Use named parameters or enum values",
                        )
                    )
        return violations

    def _check_connascence_of_position(self, tree: ast.AST, file_path: Path) -> List[ConnascenceViolation]:
        """Legacy method - basic position connascence check"""
        violations = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if len(node.args) > 4:
                    violations.append(
                        ConnascenceViolation(
                            type="Connascence of Position",
                            severity="HIGH",
                            file_path=str(file_path),
                            line_number=getattr(node, 'lineno', 1),
                            description=f"Function call with {len(node.args)} positional arguments",
                            suggestion="Use keyword arguments or parameter objects",
                        )
                    )
        return violations

    def _check_connascence_of_algorithm(self, tree: ast.AST, file_path: Path) -> List[ConnascenceViolation]:
        """Legacy method - basic algorithm connascence check"""
        violations = []
        for node in ast.walk(tree):
            if isinstance(node, ast.If):
                if self._count_conditions(node.test) > 3:
                    violations.append(
                        ConnascenceViolation(
                            type="Connascence of Algorithm",
                            severity="MEDIUM",
                            file_path=str(file_path),
                            line_number=getattr(node, 'lineno', 1),
                            description="Complex conditional logic suggests algorithm connascence",
                            suggestion="Extract to strategy pattern or lookup table",
                        )
                    )
        return violations

    def _count_conditions(self, node: ast.AST) -> int:
        """Count number of conditions in a test"""
        if isinstance(node, ast.BoolOp):
            return sum(self._count_conditions(child) for child in node.values)
        return 1


def main():
    """Main CLI function - provides legacy command line interface"""
    parser = argparse.ArgumentParser(description="Connascence Analysis Tool")
    parser.add_argument("path", help="Path to analyze")
    parser.add_argument("--strict", action="store_true", help="Enable strict mode")
    parser.add_argument("--fail-on-violations", action="store_true", help="Exit with error if violations found")
    parser.add_argument("--output", help="Output file for JSON results")

    args = parser.parse_args()

    analyzer = LegacyConnascenceAnalyzer(strict_mode=args.strict)
    violations = analyzer.analyze_directory(Path(args.path))

    # Generate report
    report = {
        "total_violations": len(violations),
        "violations_by_severity": {
            "LOW": len([v for v in violations if v.severity == "LOW"]),
            "MEDIUM": len([v for v in violations if v.severity == "MEDIUM"]),
            "HIGH": len([v for v in violations if v.severity == "HIGH"]),
            "CRITICAL": len([v for v in violations if v.severity == "CRITICAL"]),
        },
        "violations": [asdict(v) for v in violations],
    }

    # Output results
    if args.output:
        with open(args.output, "w") as f:
            json.dump(report, f, indent=2)
    else:
        print(json.dumps(report, indent=2))

    # Print summary to stderr
    print(f"Connascence Analysis: {len(violations)} violations found", file=sys.stderr)
    for severity, count in report["violations_by_severity"].items():
        if count > 0:
            print(f"  {severity}: {count}", file=sys.stderr)

    # Check for license validation (exit code 4)
    try:
        from src.licensing import LicenseValidator, LicenseValidationResult
        license_validator = LicenseValidator()
        
        license_report = license_validator.validate_license(Path(args.path))
        if license_report.validation_result != LicenseValidationResult.VALID:
            print(f"License validation failed: {license_report.validation_result.value}", file=sys.stderr)
            print("Use license validation commands for detailed report", file=sys.stderr)
            sys.exit(4)  # License error
            
    except ImportError:
        pass  # License validation not available
    except Exception as e:
        print(f"License validation error: {e}", file=sys.stderr)
        sys.exit(4)

    # Exit with error if requested and violations found
    if args.fail_on_violations and violations:
        high_severity = len([v for v in violations if v.severity in ["HIGH", "CRITICAL"]])
        if high_severity > 0:
            print(f"FAIL: {high_severity} high/critical severity violations found", file=sys.stderr)
            sys.exit(1)

    return 0


# Aliases for backward compatibility
ConnascenceAnalyzer = ConnascenceASTAnalyzer  # Use the modern analyzer by default
LegacyConnascenceAnalyzer_Alias = LegacyConnascenceAnalyzer  # Keep legacy available


if __name__ == "__main__":
    sys.exit(main())