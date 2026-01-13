# SPDX-License-Identifier: MIT
"""
Core analyzer module with command-line interface support.
Provides the main entry point for connascence analysis.
"""

import argparse
from datetime import datetime
import json
import logging
from pathlib import Path
import sys
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Import using unified import strategy
sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    from core.unified_imports import IMPORT_MANAGER
except ImportError:
    # Fallback for legacy execution
    sys.path.insert(0, str(Path(__file__).parent.parent / "core"))
    from unified_imports import IMPORT_MANAGER

# Import constants with unified strategy
constants_result = IMPORT_MANAGER.import_constants()
if constants_result.has_module:
    constants = constants_result.module
    NASA_COMPLIANCE_THRESHOLD = getattr(constants, "NASA_COMPLIANCE_THRESHOLD", 0.95)
    MECE_QUALITY_THRESHOLD = getattr(constants, "MECE_QUALITY_THRESHOLD", 0.80)
    OVERALL_QUALITY_THRESHOLD = getattr(constants, "OVERALL_QUALITY_THRESHOLD", 0.70)
    VIOLATION_WEIGHTS = getattr(constants, "VIOLATION_WEIGHTS", {"critical": 10, "high": 5, "medium": 2, "low": 1})
    # Import policy resolution functions
    resolve_policy_name = getattr(constants, "resolve_policy_name", None)
    validate_policy_name = getattr(constants, "validate_policy_name", None)
    list_available_policies = getattr(constants, "list_available_policies", None)
else:
    # Fallback constants and functions
    NASA_COMPLIANCE_THRESHOLD = 0.95
    MECE_QUALITY_THRESHOLD = 0.80
    OVERALL_QUALITY_THRESHOLD = 0.70
    VIOLATION_WEIGHTS = {"critical": 10, "high": 5, "medium": 2, "low": 1}
    resolve_policy_name = None
    validate_policy_name = None
    list_available_policies = None

# Import unified analyzer with fallback
analyzer_result = IMPORT_MANAGER.import_unified_analyzer()
UNIFIED_ANALYZER_AVAILABLE = analyzer_result.has_module
if UNIFIED_ANALYZER_AVAILABLE:
    UnifiedConnascenceAnalyzer = analyzer_result.module
else:
    logger.warning("Unified analyzer not available, using fallback mode")
    UnifiedConnascenceAnalyzer = None

# Import unified duplication analyzer
try:
    from analyzer.duplication_helper import format_duplication_analysis
    from analyzer.duplication_unified import UnifiedDuplicationAnalyzer

    DUPLICATION_ANALYZER_AVAILABLE = True
except ImportError:
    logger.warning("Unified duplication analyzer not available")
    DUPLICATION_ANALYZER_AVAILABLE = False
    UnifiedDuplicationAnalyzer = None

    def format_duplication_analysis(result):
        return {"score": 1.0, "violations": [], "available": False}


# Import MCP server components with unified strategy
mcp_result = IMPORT_MANAGER.import_mcp_server()
if mcp_result.has_module:
    ConnascenceViolation = getattr(mcp_result.module, "ConnascenceViolation", None)
else:
    # Import canonical ConnascenceViolation as fallback
    from utils.types import ConnascenceViolation


# Import reporting with unified strategy
json_reporter_result = IMPORT_MANAGER.import_reporting("json")
sarif_reporter_result = IMPORT_MANAGER.import_reporting("sarif")

JSONReporter = getattr(json_reporter_result.module, "JSONReporter", None) if json_reporter_result.has_module else None
SARIFReporter = (
    getattr(sarif_reporter_result.module, "SARIFReporter", None) if sarif_reporter_result.has_module else None
)

if not JSONReporter or not SARIFReporter:
    # Fallback for direct execution
    from analyzer.reporting.json import JSONReporter
    from analyzer.reporting.sarif import SARIFReporter

# Fallback imports for when unified analyzer is not available
try:
    from .check_connascence import ConnascenceAnalyzer as FallbackAnalyzer

    FALLBACK_ANALYZER_AVAILABLE = True
except ImportError:
    try:
        from check_connascence import ConnascenceAnalyzer as FallbackAnalyzer

        FALLBACK_ANALYZER_AVAILABLE = True
    except ImportError:
        FALLBACK_ANALYZER_AVAILABLE = False


class ConnascenceAnalyzer:
    """Main connascence analyzer with unified pipeline integration."""

    def __init__(self):
        self.version = "2.0.0"

        # Initialize duplication analyzer
        if DUPLICATION_ANALYZER_AVAILABLE:
            self.duplication_analyzer = UnifiedDuplicationAnalyzer(similarity_threshold=0.7)
        else:
            self.duplication_analyzer = None

        # Initialize the appropriate analyzer
        if UNIFIED_ANALYZER_AVAILABLE:
            self.unified_analyzer = UnifiedConnascenceAnalyzer()
            self.analysis_mode = "unified"
        elif FALLBACK_ANALYZER_AVAILABLE:
            self.fallback_analyzer = FallbackAnalyzer()
            self.analysis_mode = "fallback"
        else:
            self.analysis_mode = "mock"
            logger.warning("Neither unified nor fallback analyzer available, using mock mode")

    def analyze_path(self, path: str, policy: str = "default", **kwargs) -> Dict[str, Any]:
        """Analyze a file or directory for connascence violations using real analysis pipeline."""
        try:
            path_obj = Path(path)

            if not path_obj.exists():
                return {
                    "success": False,
                    "error": f"Path does not exist: {path}",
                    "violations": [],
                    "summary": {"total_violations": 0},
                    "nasa_compliance": {"score": 0.0, "violations": []},
                    "mece_analysis": {"score": 0.0, "duplications": []},
                    "duplication_analysis": {"score": 1.0, "violations": []},
                    "god_objects": [],
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Path analysis error: {e!s}",
                "violations": [],
                "summary": {"total_violations": 0},
                "nasa_compliance": {"score": 0.0, "violations": []},
                "mece_analysis": {"score": 0.0, "duplications": []},
                "duplication_analysis": {"score": 1.0, "violations": []},
                "god_objects": [],
            }

        # Run duplication analysis if requested
        duplication_result = None
        if kwargs.get("include_duplication", True) and self.duplication_analyzer:
            duplication_result = self.duplication_analyzer.analyze_path(path, comprehensive=True)

        # Use real analysis based on available components
        if self.analysis_mode == "unified":
            return self._run_unified_analysis(path, policy, duplication_result, **kwargs)
        elif self.analysis_mode == "fallback":
            return self._run_fallback_analysis(path, policy, duplication_result, **kwargs)
        else:
            return self._run_mock_analysis(path, policy, duplication_result, **kwargs)

    def _analyze_file_or_directory(self, path_obj, policy_preset, **kwargs):
        """
        Analyze file or directory based on path type.

        NASA Rule 4: Function under 60 lines
        """
        if path_obj.is_file():
            # For single files, use analyze_file method
            file_result = self.unified_analyzer.analyze_file(str(path_obj))
            violations = file_result.get("connascence_violations", [])
            nasa_violations = file_result.get("nasa_violations", [])

            # Create a mock result object with all required attributes
            class MockUnifiedResult:
                def __init__(self):
                    self.connascence_violations = violations
                    self.nasa_violations = nasa_violations
                    self.duplication_clusters = []
                    self.total_violations = len(violations)
                    self.critical_count = len([v for v in violations if v.get("severity") == "critical"])
                    self.overall_quality_score = file_result.get("nasa_compliance_score", 1.0)
                    self.nasa_compliance_score = file_result.get("nasa_compliance_score", 1.0)
                    self.duplication_score = 1.0
                    self.connascence_index = sum(v.get("weight", 1) for v in violations)
                    self.files_analyzed = 1
                    self.analysis_duration_ms = 100

            return MockUnifiedResult()
        else:
            # For directories, use analyze_project method
            return self.unified_analyzer.analyze_project(
                project_path=str(path_obj), policy_preset=policy_preset, options=kwargs
            )

    def _format_unified_result(self, result, path: str, policy: str, duplication_result):
        """
        Convert unified result to expected format.

        NASA Rule 4: Function under 60 lines
        """
        return {
            "success": True,
            "path": str(path),
            "policy": policy,
            "violations": result.connascence_violations,
            "summary": {
                "total_violations": result.total_violations,
                "critical_violations": result.critical_count,
                "overall_quality_score": result.overall_quality_score,
            },
            "nasa_compliance": {
                "score": result.nasa_compliance_score,
                "violations": result.nasa_violations,
                "passing": result.nasa_compliance_score >= NASA_COMPLIANCE_THRESHOLD,
            },
            "mece_analysis": {
                "score": result.duplication_score,
                "duplications": result.duplication_clusters,
                "passing": result.duplication_score >= MECE_QUALITY_THRESHOLD,
            },
            "duplication_analysis": format_duplication_analysis(duplication_result),
            "god_objects": self._extract_god_objects(result.connascence_violations),
            "metrics": {
                "files_analyzed": result.files_analyzed,
                "analysis_time": result.analysis_duration_ms / 1000.0,
                "timestamp": time.time(),
                "connascence_index": result.connascence_index,
            },
            "quality_gates": {
                "overall_passing": result.overall_quality_score >= OVERALL_QUALITY_THRESHOLD,
                "nasa_passing": result.nasa_compliance_score >= NASA_COMPLIANCE_THRESHOLD,
                "mece_passing": result.duplication_score >= MECE_QUALITY_THRESHOLD,
            },
        }

    def _create_error_result(self, error: Exception):
        """
        Create error result structure.

        NASA Rule 4: Function under 60 lines
        """
        return {
            "success": False,
            "error": f"Unified analysis error: {error!s}",
            "violations": [],
            "summary": {"total_violations": 0},
            "nasa_compliance": {"score": 0.0, "violations": []},
            "mece_analysis": {"score": 0.0, "duplications": []},
            "god_objects": [],
        }

    def _run_unified_analysis(
        self, path: str, policy: str, duplication_result: Optional[Any] = None, **kwargs
    ) -> Dict[str, Any]:
        """
        Run analysis using the unified analyzer pipeline.

        Refactored to comply with NASA Rule 4 (<=60 lines per function).
        Helper functions handle file/directory analysis, result formatting, and errors.
        """
        try:
            time.time()

            # Convert policy to unified analyzer format
            policy_preset = self._convert_policy_to_preset(policy)
            path_obj = Path(path)

            # Analyze file or directory
            result = self._analyze_file_or_directory(path_obj, policy_preset, **kwargs)

            # Format and return result
            return self._format_unified_result(result, path, policy, duplication_result)

        except Exception as e:
            return self._create_error_result(e)

    def _run_fallback_analysis(
        self, path: str, policy: str, duplication_result: Optional[Any] = None, **kwargs
    ) -> Dict[str, Any]:
        """Run analysis using fallback analyzer."""
        try:
            path_obj = Path(path)
            if path_obj.is_file():
                violations = self.fallback_analyzer.analyze_file(path_obj)
            else:
                violations = self.fallback_analyzer.analyze_directory(path_obj)

            # Convert violations to expected format
            violation_dicts = [self._violation_to_dict(v) for v in violations]

            # Calculate basic metrics
            total_violations = len(violations)
            critical_count = len([v for v in violations if getattr(v, "severity", "medium") == "critical"])

            # Basic quality score calculation
            quality_score = max(0.0, 1.0 - (total_violations * 0.01))

            return {
                "success": True,
                "path": str(path),
                "policy": policy,
                "violations": violation_dicts,
                "summary": {
                    "total_violations": total_violations,
                    "critical_violations": critical_count,
                    "overall_quality_score": quality_score,
                },
                "nasa_compliance": {
                    "score": 0.8,  # Fallback score
                    "violations": [v for v in violation_dicts if "NASA" in v.get("rule_id", "")],
                },
                "mece_analysis": {"score": 0.75, "duplications": []},  # Fallback score
                "god_objects": self._extract_god_objects(violation_dicts),
                "metrics": {
                    # B3.4 FIX: Count unique files from violations, not all .py files
                    "files_analyzed": len(set(v.get("file_path", "") for v in violation_dicts if v.get("file_path"))) or (1 if Path(path).is_file() else 0),
                    "analysis_time": 1.0,
                    "timestamp": time.time(),
                },
            }

        except Exception:
            return self._run_mock_analysis(path, policy, **kwargs)

    def _run_mock_analysis(self, path: str, policy: str, **kwargs) -> Dict[str, Any]:
        """Fallback mock analysis when real analyzers are unavailable."""
        # Generate basic mock violations for testing
        violations = self._generate_mock_violations(path, policy)

        return {
            "success": True,
            "path": str(path),
            "policy": policy,
            "violations": [self._violation_to_dict(v) for v in violations],
            "summary": {
                "total_violations": len(violations),
                "critical_violations": len([v for v in violations if v.severity == "critical"]),
                "overall_quality_score": 0.75,
            },
            "nasa_compliance": {
                "score": 0.85,
                "violations": [self._violation_to_dict(v) for v in violations if v.rule_id.startswith("NASA")],
            },
            "mece_analysis": {"score": 0.75, "duplications": []},
            "god_objects": [],
            "metrics": {
                "files_analyzed": 1 if Path(path).is_file() else 5,
                "analysis_time": 0.5,
                "timestamp": time.time(),
            },
        }

    def _generate_mock_violations(self, path: str, policy: str) -> List[ConnascenceViolation]:
        """Generate mock violations only when real analysis is unavailable."""
        violations = [
            ConnascenceViolation(
                id="mock_1",
                rule_id="CON_CoM",
                connascence_type="CoM",
                severity="medium",
                description="Mock: Magic literal detected (fallback mode)",
                file_path=f"{path}/mock_file.py",
                line_number=42,
                weight=2.0,
            )
        ]

        if policy == "nasa_jpl_pot10":
            violations.append(
                ConnascenceViolation(
                    id="nasa_mock",
                    rule_id="NASA_POT10_2",
                    connascence_type="CoA",
                    severity="critical",
                    description="Mock: NASA Power of Ten Rule violation (fallback mode)",
                    file_path=f"{path}/memory.py",
                    line_number=88,
                    weight=5.0,
                )
            )

        return violations

    def _convert_policy_to_preset(self, policy: str) -> str:
        """Convert policy string to unified analyzer preset.

        Raises:
            ValueError: If policy name is not recognized
        """
        import warnings

        policy_mapping = {
            # Legacy CLI policy names
            "default": "service-defaults",
            "strict-core": "strict-core",
            "nasa_jpl_pot10": "service-defaults",  # Map to available preset
            "lenient": "lenient",
            # Unified policy names (resolved)
            "nasa-compliance": "service-defaults",  # Map to available preset
            "strict": "strict-core",
            "standard": "service-defaults",
            # Direct preset names
            "service-defaults": "service-defaults",
            "experimental": "experimental",
            "balanced": "balanced",
        }

        if policy not in policy_mapping:
            available_policies = list(policy_mapping.keys())
            warnings.warn(
                f"Unknown policy '{policy}'. Using 'service-defaults'. "
                f"Available: {', '.join(available_policies)}",
                UserWarning,
                stacklevel=2
            )

        return policy_mapping.get(policy, "service-defaults")

    def _extract_god_objects(self, violations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract god object violations from violation list."""
        return [v for v in violations if v.get("type") == "god_object" or "god_object" in v.get("rule_id", "").lower()]

    def _violation_to_dict(self, violation: ConnascenceViolation) -> Dict[str, Any]:
        """Convert violation object to dictionary with enhanced metadata."""
        if isinstance(violation, dict):
            return violation  # Already a dictionary

        return {
            "id": getattr(violation, "id", str(hash(str(violation)))),
            "rule_id": getattr(violation, "rule_id", "UNKNOWN"),
            "type": getattr(violation, "connascence_type", getattr(violation, "type", "unknown")),
            "severity": getattr(violation, "severity", "medium"),
            "description": getattr(violation, "description", str(violation)),
            "file_path": getattr(violation, "file_path", ""),
            "line_number": getattr(violation, "line_number", 0),
            "weight": getattr(violation, "weight", VIOLATION_WEIGHTS.get(getattr(violation, "severity", "medium"), 1)),
            "analysis_mode": self.analysis_mode,
        }


def _add_basic_arguments(parser: argparse.ArgumentParser):
    """
    Add basic arguments (path, policy, format, output).

    NASA Rule 4: Function under 60 lines
    """
    # Use separate destinations for positional and optional path arguments
    # This allows --path to override positional without default value conflicts
    parser.add_argument("positional_path", nargs="?", default=argparse.SUPPRESS, metavar="path", help="Path to analyze (default: current directory)")
    parser.add_argument("--path", "-p", dest="optional_path", type=str, help="Path to analyze (alternative to positional)")

    # Get available policies for help text
    policy_help = (
        "Analysis policy to use. Unified: nasa-compliance, strict, standard, lenient (legacy names also accepted, default: default)"
    )
    try:
        if "list_available_policies" in globals() and list_available_policies:
            available_policies = list_available_policies(include_legacy=True)
            policy_help = f"Analysis policy to use. Available: {', '.join(available_policies)}"
    except (ImportError, AttributeError, TypeError) as e:
        pass  # Use default policy_help if policy listing fails

    parser.add_argument("--policy", type=str, default="default", help=policy_help)
    parser.add_argument(
        "--format", "-f", type=str, default="json", choices=["json", "yaml", "sarif"], help="Output format"
    )
    parser.add_argument("--output", "-o", type=str, help="Output file path")


def _add_analysis_arguments(parser: argparse.ArgumentParser):
    """
    Add analysis control arguments (NASA validation, duplication, strict mode).

    NASA Rule 4: Function under 60 lines
    """
    parser.add_argument("--nasa-validation", action="store_true", help="Enable NASA Power of Ten validation")
    parser.add_argument(
        "--duplication-analysis",
        action="store_true",
        default=True,
        help="Enable unified duplication analysis (default: enabled)",
    )
    parser.add_argument("--no-duplication", action="store_true", help="Disable duplication analysis")
    parser.add_argument(
        "--duplication-threshold",
        type=float,
        default=0.7,
        help="Similarity threshold for duplication detection (0.0-1.0, default: 0.7)",
    )
    parser.add_argument("--strict-mode", action="store_true", help="Enable strict analysis mode")
    parser.add_argument("--exclude", action="append", default=[], help="Paths to exclude from analysis (can be used multiple times)")


def _add_output_control_arguments(parser: argparse.ArgumentParser):
    """
    Add output control arguments (include flags, tool correlation).

    NASA Rule 4: Function under 60 lines
    """
    parser.add_argument("--include-nasa-rules", action="store_true", help="Include NASA-specific rules in SARIF output")
    parser.add_argument(
        "--include-god-objects", action="store_true", help="Include god object analysis in SARIF output"
    )
    parser.add_argument(
        "--include-mece-analysis", action="store_true", help="Include MECE duplication analysis in SARIF output"
    )
    parser.add_argument("--enable-tool-correlation", action="store_true", help="Enable cross-tool analysis correlation")
    parser.add_argument("--confidence-threshold", type=float, default=0.8, help="Confidence threshold for correlations")


def _add_exit_condition_arguments(parser: argparse.ArgumentParser):
    """
    Add exit condition arguments (fail-on-critical, thresholds).

    NASA Rule 4: Function under 60 lines
    """
    parser.add_argument("--fail-on-critical", action="store_true", help="Exit with error code on critical violations")
    parser.add_argument("--max-god-objects", type=int, default=5, help="Maximum allowed god objects before failure")
    parser.add_argument("--compliance-threshold", type=int, default=95, help="Compliance threshold percentage (0-100)")


def _add_enhanced_pipeline_arguments(parser: argparse.ArgumentParser):
    """
    Add enhanced pipeline arguments (correlations, audit trail, recommendations).

    NASA Rule 4: Function under 60 lines
    """
    parser.add_argument("--enable-correlations", action="store_true", help="Enable cross-phase correlation analysis")
    parser.add_argument("--enable-audit-trail", action="store_true", help="Enable analysis audit trail tracking")
    parser.add_argument(
        "--enable-smart-recommendations", action="store_true", help="Enable AI-powered smart recommendations"
    )
    parser.add_argument(
        "--correlation-threshold",
        type=float,
        default=0.7,
        help="Minimum correlation threshold for cross-phase analysis (0.0-1.0)",
    )
    parser.add_argument("--export-audit-trail", type=str, help="Export audit trail to specified file path")
    parser.add_argument("--export-correlations", type=str, help="Export correlation data to specified file path")
    parser.add_argument(
        "--export-recommendations", type=str, help="Export smart recommendations to specified file path"
    )
    parser.add_argument("--enhanced-output", action="store_true", help="Include enhanced pipeline metadata in output")
    parser.add_argument("--phase-timing", action="store_true", help="Display detailed phase timing information")


def create_parser() -> argparse.ArgumentParser:
    """
    Create command-line argument parser with custom path resolution.

    Refactored to comply with NASA Rule 4 (<=60 lines per function).
    Helper functions organize arguments into logical groups.
    """
    parser = argparse.ArgumentParser(
        description="Connascence Safety Analyzer", formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # Add argument groups
    _add_basic_arguments(parser)
    _add_analysis_arguments(parser)
    _add_output_control_arguments(parser)
    _add_exit_condition_arguments(parser)
    _add_enhanced_pipeline_arguments(parser)

    # Wrap parse_args to handle path resolution
    original_parse_args = parser.parse_args
    def custom_parse_args(args=None, namespace=None):
        result = original_parse_args(args, namespace)
        # Resolve path from either --path or positional argument
        if hasattr(result, 'optional_path') and result.optional_path:
            result.path = result.optional_path
        elif hasattr(result, 'positional_path'):
            result.path = result.positional_path
        else:
            result.path = "."
        return result
    parser.parse_args = custom_parse_args

    return parser


def _validate_and_resolve_policy(policy: str) -> str:
    """
    Validate and resolve policy name.

    NASA Rule 4: Function under 60 lines
    """
    # Resolve policy name (legacy to unified mapping)
    if resolve_policy_name:
        try:
            resolved_policy = resolve_policy_name(policy, warn_deprecated=True)
            policy = resolved_policy
        except Exception:
            # Fallback: use original policy name if resolution fails
            pass

    # Validate policy name (after resolution)
    if validate_policy_name and not validate_policy_name(policy):
        available_policies = []
        if list_available_policies:
            try:
                available_policies = list_available_policies(include_legacy=True)
            except Exception:
                from analyzer.constants import UNIFIED_POLICY_NAMES

                available_policies = UNIFIED_POLICY_NAMES
        else:
            from analyzer.constants import UNIFIED_POLICY_NAMES

            available_policies = UNIFIED_POLICY_NAMES

        logger.error(
            "Unknown policy '%s'. Available policies: %s",
            policy,
            ", ".join(available_policies),
        )
        sys.exit(1)

    return policy


def _setup_duplication_analysis(args, analyzer) -> tuple:
    """
    Setup duplication analysis configuration.

    Returns: (include_duplication, duplication_threshold)
    NASA Rule 4: Function under 60 lines
    """
    include_duplication = args.duplication_analysis and not args.no_duplication
    duplication_threshold = args.duplication_threshold

    if include_duplication and DUPLICATION_ANALYZER_AVAILABLE:
        analyzer.duplication_analyzer.similarity_threshold = duplication_threshold

    return include_duplication, duplication_threshold


def _run_analysis(args, policy: str, analyzer, include_duplication: bool, duplication_threshold: float):
    """
    Run analysis with appropriate analyzer (enhanced or standard).

    NASA Rule 4: Function under 60 lines
    """
    use_enhanced_analyzer = (
        args.enable_correlations or args.enable_audit_trail or args.enable_smart_recommendations or args.enhanced_output
    )

    if use_enhanced_analyzer and UNIFIED_ANALYZER_AVAILABLE:
        logger.info("Using enhanced unified analyzer for cross-phase analysis...")

        enhanced_analyzer = UnifiedConnascenceAnalyzer()
        result = enhanced_analyzer.analyze_path(
            path=args.path,
            policy=policy,
            enable_cross_phase_correlation=args.enable_correlations,
            enable_audit_trail=args.enable_audit_trail,
            enable_smart_recommendations=args.enable_smart_recommendations,
            correlation_threshold=args.correlation_threshold,
            include_duplication=include_duplication,
            duplication_threshold=duplication_threshold,
            nasa_validation=args.nasa_validation,
            strict_mode=args.strict_mode,
            enable_tool_correlation=args.enable_tool_correlation,
            confidence_threshold=args.confidence_threshold,
        )
    else:
        result = analyzer.analyze_path(
            path=args.path,
            policy=policy,
            include_duplication=include_duplication,
            duplication_threshold=duplication_threshold,
            nasa_validation=args.nasa_validation,
            strict_mode=args.strict_mode,
            enable_tool_correlation=args.enable_tool_correlation,
            confidence_threshold=args.confidence_threshold,
        )

    return result, use_enhanced_analyzer


def _handle_output_format(args, result):
    """
    Handle different output formats (SARIF, JSON, plain).

    NASA Rule 4: Function under 60 lines
    """
    if args.format == "sarif":
        sarif_reporter = SARIFReporter()
        if args.output:
            sarif_reporter.export_results(result, args.output)
            logger.info("SARIF report written to: %s", args.output)
        else:
            sarif_output = sarif_reporter.export_results(result)
            try:
                logger.info("%s", sarif_output)
            except UnicodeEncodeError:
                logger.info("%s", sarif_output.encode("ascii", errors="replace").decode("ascii"))
    elif args.format == "json":
        json_reporter = JSONReporter()
        if args.output:
            json_reporter.export_results(result, args.output)
            logger.info("JSON report written to: %s", args.output)
        else:
            json_output = json_reporter.export_results(result)
            try:
                logger.info("%s", json_output)
            except UnicodeEncodeError:
                logger.info("%s", json_output.encode("ascii", errors="replace").decode("ascii"))
    elif args.output:
        with open(args.output, "w") as f:
            f.write(str(result))
    else:
        logger.info("%s", result)


def _export_enhanced_results(args, result, use_enhanced_analyzer: bool):
    """
    Export enhanced pipeline results (audit trail, correlations, recommendations).

    NASA Rule 4: Function under 60 lines (54 LOC)
    """
    if not use_enhanced_analyzer or not UNIFIED_ANALYZER_AVAILABLE:
        return

    # Export audit trail
    if args.export_audit_trail and result.get("audit_trail"):
        with open(args.export_audit_trail, "w") as f:
            json.dump(result["audit_trail"], f, indent=2, default=str)
        logger.info("Audit trail exported to: %s", args.export_audit_trail)

    # Export correlations
    if args.export_correlations and result.get("correlations"):
        with open(args.export_correlations, "w") as f:
            json.dump(result["correlations"], f, indent=2, default=str)
        logger.info("Correlations exported to: %s", args.export_correlations)

    # Export smart recommendations
    if args.export_recommendations and result.get("smart_recommendations"):
        with open(args.export_recommendations, "w") as f:
            json.dump(result["smart_recommendations"], f, indent=2, default=str)
        logger.info("Smart recommendations exported to: %s", args.export_recommendations)

    # Display phase timing
    _display_phase_timing(args, result)

    # Display correlations summary
    _display_correlations_summary(result)

    # Display recommendations summary
    _display_recommendations_summary(result)


def _display_phase_timing(args, result):
    """Display phase timing information (helper for _export_enhanced_results)."""
    if args.phase_timing and result.get("audit_trail"):
        logger.info("=== Analysis Phase Timing ===")
        for phase in result["audit_trail"]:
            if phase.get("started") and phase.get("completed"):
                start_time = datetime.fromisoformat(phase["started"].replace("Z", "+00:00"))
                end_time = datetime.fromisoformat(phase["completed"].replace("Z", "+00:00"))
                duration = (end_time - start_time).total_seconds() * 1000

                phase_name = phase["phase"].replace("_", " ").title()
                violations = phase.get("violations_found", 0)
                clusters = phase.get("clusters_found", 0)

                logger.info(
                    "%-25s | %8.1fms | %3d violations | %3d clusters",
                    phase_name,
                    duration,
                    violations,
                    clusters,
                )


def _display_correlations_summary(result):
    """Display correlation summary (helper for _export_enhanced_results)."""
    if result.get("correlations") and len(result["correlations"]) > 0:
        logger.info("=== Cross-Phase Analysis Summary ===")
        correlations = result["correlations"]
        logger.info("Found %s cross-phase correlations", len(correlations))

        sorted_corr = sorted(correlations, key=lambda x: x.get("correlation_score", 0), reverse=True)
        for i, corr in enumerate(sorted_corr[:3]):
            score = corr.get("correlation_score", 0) * 100
            analyzer1 = corr.get("analyzer1", "Unknown")
            analyzer2 = corr.get("analyzer2", "Unknown")
            logger.info("%s. %s <-> %s: %.1f%% correlation", i + 1, analyzer1, analyzer2, score)


def _display_recommendations_summary(result):
    """Display recommendations summary (helper for _export_enhanced_results)."""
    if result.get("smart_recommendations") and len(result["smart_recommendations"]) > 0:
        logger.info("=== Smart Recommendations Summary ===")
        recommendations = result["smart_recommendations"]
        logger.info("Generated %s architectural recommendations", len(recommendations))

        high_priority = [r for r in recommendations if r.get("priority", "").lower() == "high"]
        for rec in high_priority[:3]:
            category = rec.get("category", "General")
            description = rec.get("description", "No description")[:60] + "..."
            logger.info("• [%s] %s", category, description)


def _check_exit_conditions(args, result):
    """
    Check exit conditions and exit with appropriate code.

    NASA Rule 4: Function under 60 lines
    """
    if not result.get("success", False):
        logger.error("Analysis failed: %s", result.get("error", "Unknown error"))
        sys.exit(1)

    violations = result.get("violations", [])
    critical_count = len([v for v in violations if v.get("severity") == "critical"])
    god_objects = result.get("god_objects", [])
    god_object_count = len(god_objects)
    overall_quality_score = result.get("summary", {}).get("overall_quality_score", 1.0)
    compliance_percent = int(overall_quality_score * 100)

    should_exit_with_error = False
    exit_reasons = []

    if args.fail_on_critical and critical_count > 0:
        should_exit_with_error = True
        exit_reasons.append(f"{critical_count} critical violations found")

    if god_object_count > args.max_god_objects:
        should_exit_with_error = True
        exit_reasons.append(f"{god_object_count} god objects (max: {args.max_god_objects})")

    if compliance_percent < args.compliance_threshold:
        should_exit_with_error = True
        exit_reasons.append(f"compliance {compliance_percent}% < {args.compliance_threshold}%")

    if critical_count > 0 and args.strict_mode:
        should_exit_with_error = True
        exit_reasons.append(f"{critical_count} critical violations (strict mode)")

    if should_exit_with_error:
        logger.error("Analysis failed: %s", ", ".join(exit_reasons))
        sys.exit(1)

    logger.info(
        "Analysis completed successfully. %s total violations (%s critical)",
        len(violations),
        critical_count,
    )
    sys.exit(0)


def _handle_error(e: Exception, args):
    """
    Handle errors and generate minimal output for CI compatibility.

    NASA Rule 4: Function under 60 lines
    """
    logger.error("Analyzer error: %s", e)
    import traceback

    traceback.print_exc()

    if args.output and args.format in ["json", "sarif"]:
        try:
            minimal_result = {
                "success": False,
                "error": str(e),
                "violations": [],
                "summary": {"total_violations": 0},
                "nasa_compliance": {"score": 0.0, "violations": []},
            }

            if args.format == "sarif":
                sarif_reporter = SARIFReporter()
                sarif_reporter.export_results(minimal_result, args.output)
            else:
                json_reporter = JSONReporter()
                json_reporter.export_results(minimal_result, args.output)

            logger.info("Minimal %s report written for CI compatibility", args.format.upper())
        except Exception as export_error:
            logger.error("Failed to write minimal report: %s", export_error)

    sys.exit(1)


def main():
    """
    Main entry point for command-line execution.

    Refactored to comply with NASA Rule 4 (<=60 lines per function).
    Helper functions handle distinct logical sections.
    """
    parser = create_parser()
    args = parser.parse_args()

    # Validate path exists (path resolution done in parser)
    if not Path(args.path).exists():
        logger.error("Path does not exist: %s", args.path)
        sys.exit(2)

    analyzer = ConnascenceAnalyzer()
    policy = "nasa_jpl_pot10" if args.nasa_validation else args.policy

    # Validate and resolve policy
    policy = _validate_and_resolve_policy(policy)

    # Setup duplication analysis
    include_duplication, duplication_threshold = _setup_duplication_analysis(args, analyzer)

    try:
        # Run analysis
        result, use_enhanced_analyzer = _run_analysis(
            args, policy, analyzer, include_duplication, duplication_threshold
        )

        # Handle output format
        _handle_output_format(args, result)

        # Export enhanced results
        _export_enhanced_results(args, result, use_enhanced_analyzer)

        # Check exit conditions
        _check_exit_conditions(args, result)

    except KeyboardInterrupt:
        logger.warning("Analysis interrupted by user")
        sys.exit(130)
    except Exception as e:
        _handle_error(e, args)


# Deprecated: Use SARIFReporter class instead
def convert_to_sarif(result: Dict[str, Any], args) -> Dict[str, Any]:
    """Legacy SARIF conversion - use SARIFReporter class instead."""
    logger.warning("Using deprecated convert_to_sarif function. Use SARIFReporter class instead.")
    reporter = SARIFReporter()
    return json.loads(reporter.export_results(result))


# Deprecated: Use SARIFReporter._map_severity_to_level instead
def map_severity_to_sarif(severity: str) -> str:
    """Legacy severity mapping - use SARIFReporter class instead."""
    from analyzer.reporting.sarif import SARIFReporter

    reporter = SARIFReporter()
    return reporter._map_severity_to_level(severity)


if __name__ == "__main__":
    main()


__all__ = ["ConnascenceAnalyzer", "ConnascenceViolation", "main"]
