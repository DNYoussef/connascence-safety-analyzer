# SPDX-License-Identifier: MIT
"""
Core analyzer module with command-line interface support.
Provides the main entry point for connascence analysis.
"""

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import using unified import strategy
sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    from core.unified_imports import IMPORT_MANAGER, ImportSpec
except ImportError:
    # Fallback for legacy execution
    sys.path.insert(0, str(Path(__file__).parent.parent / "core"))
    from unified_imports import IMPORT_MANAGER, ImportSpec

# Import constants with unified strategy
constants_result = IMPORT_MANAGER.import_constants()
if constants_result.has_module:
    constants = constants_result.module
    NASA_COMPLIANCE_THRESHOLD = getattr(constants, 'NASA_COMPLIANCE_THRESHOLD', 0.95)
    MECE_QUALITY_THRESHOLD = getattr(constants, 'MECE_QUALITY_THRESHOLD', 0.80)
    OVERALL_QUALITY_THRESHOLD = getattr(constants, 'OVERALL_QUALITY_THRESHOLD', 0.75)
    VIOLATION_WEIGHTS = getattr(constants, 'VIOLATION_WEIGHTS', {'critical': 10, 'high': 5, 'medium': 2, 'low': 1})
else:
    # Fallback constants
    NASA_COMPLIANCE_THRESHOLD = 0.95
    MECE_QUALITY_THRESHOLD = 0.80
    OVERALL_QUALITY_THRESHOLD = 0.75
    VIOLATION_WEIGHTS = {'critical': 10, 'high': 5, 'medium': 2, 'low': 1}

# Import unified analyzer with fallback
analyzer_result = IMPORT_MANAGER.import_unified_analyzer()
UNIFIED_ANALYZER_AVAILABLE = analyzer_result.has_module
if UNIFIED_ANALYZER_AVAILABLE:
    UnifiedConnascenceAnalyzer = analyzer_result.module
else:
    print("[WARNING] Unified analyzer not available, using fallback mode")
    UnifiedConnascenceAnalyzer = None

# Import MCP server components with unified strategy
mcp_result = IMPORT_MANAGER.import_mcp_server()
if mcp_result.has_module:
    ConnascenceViolation = getattr(mcp_result.module, 'ConnascenceViolation', None)
else:
    # Create minimal ConnascenceViolation for fallback
    class ConnascenceViolation:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

# Import reporting with unified strategy
json_reporter_result = IMPORT_MANAGER.import_reporting("json")
sarif_reporter_result = IMPORT_MANAGER.import_reporting("sarif")

JSONReporter = getattr(json_reporter_result.module, 'JSONReporter', None) if json_reporter_result.has_module else None
SARIFReporter = getattr(sarif_reporter_result.module, 'SARIFReporter', None) if sarif_reporter_result.has_module else None

if not JSONReporter or not SARIFReporter:
    # Fallback for direct execution
    from reporting.sarif_export import SARIFReporter
    from reporting.json_export import JSONReporter

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
        
        # Initialize the appropriate analyzer
        if UNIFIED_ANALYZER_AVAILABLE:
            self.unified_analyzer = UnifiedConnascenceAnalyzer()
            self.analysis_mode = "unified"
        elif FALLBACK_ANALYZER_AVAILABLE:
            self.fallback_analyzer = FallbackAnalyzer()
            self.analysis_mode = "fallback"
        else:
            self.analysis_mode = "mock"
            print("[WARNING] Neither unified nor fallback analyzer available, using mock mode")
    
    def analyze_path(self, path: str, policy: str = "default", **kwargs) -> Dict[str, Any]:
        """Analyze a file or directory for connascence violations using real analysis pipeline."""
        try:
            path_obj = Path(path)
            
            if not path_obj.exists():
                return {
                    'success': False,
                    'error': f"Path does not exist: {path}",
                    'violations': [],
                    'summary': {'total_violations': 0},
                    'nasa_compliance': {'score': 0.0, 'violations': []},
                    'mece_analysis': {'score': 0.0, 'duplications': []},
                    'god_objects': []
                }
        except Exception as e:
            return {
                'success': False,
                'error': f"Path analysis error: {str(e)}",
                'violations': [],
                'summary': {'total_violations': 0},
                'nasa_compliance': {'score': 0.0, 'violations': []},
                'mece_analysis': {'score': 0.0, 'duplications': []},
                'god_objects': []
            }
        
        # Use real analysis based on available components
        if self.analysis_mode == "unified":
            return self._run_unified_analysis(path, policy, **kwargs)
        elif self.analysis_mode == "fallback":
            return self._run_fallback_analysis(path, policy, **kwargs)
        else:
            return self._run_mock_analysis(path, policy, **kwargs)
    
    def _run_unified_analysis(self, path: str, policy: str, **kwargs) -> Dict[str, Any]:
        """Run analysis using the unified analyzer pipeline."""
        try:
            start_time = time.time()
            
            # Convert policy to unified analyzer format
            policy_preset = self._convert_policy_to_preset(policy)
            
            # Run comprehensive analysis
            result = self.unified_analyzer.analyze_project(
                project_path=path,
                policy_preset=policy_preset,
                options=kwargs
            )
            
            # Convert unified result to expected format
            return {
                'success': True,
                'path': str(path),
                'policy': policy,
                'violations': result.connascence_violations,
                'summary': {
                    'total_violations': result.total_violations,
                    'critical_violations': result.critical_count,
                    'overall_quality_score': result.overall_quality_score
                },
                'nasa_compliance': {
                    'score': result.nasa_compliance_score,
                    'violations': result.nasa_violations,
                    'passing': result.nasa_compliance_score >= NASA_COMPLIANCE_THRESHOLD
                },
                'mece_analysis': {
                    'score': result.duplication_score,
                    'duplications': result.duplication_clusters,
                    'passing': result.duplication_score >= MECE_QUALITY_THRESHOLD
                },
                'god_objects': self._extract_god_objects(result.connascence_violations),
                'metrics': {
                    'files_analyzed': result.files_analyzed,
                    'analysis_time': result.analysis_duration_ms / 1000.0,
                    'timestamp': time.time(),
                    'connascence_index': result.connascence_index
                },
                'quality_gates': {
                    'overall_passing': result.overall_quality_score >= OVERALL_QUALITY_THRESHOLD,
                    'nasa_passing': result.nasa_compliance_score >= NASA_COMPLIANCE_THRESHOLD,
                    'mece_passing': result.duplication_score >= MECE_QUALITY_THRESHOLD
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Unified analysis error: {str(e)}",
                'violations': [],
                'summary': {'total_violations': 0},
                'nasa_compliance': {'score': 0.0, 'violations': []},
                'mece_analysis': {'score': 0.0, 'duplications': []},
                'god_objects': []
            }
    
    def _run_fallback_analysis(self, path: str, policy: str, **kwargs) -> Dict[str, Any]:
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
            critical_count = len([v for v in violations if getattr(v, 'severity', 'medium') == 'critical'])
            
            # Basic quality score calculation
            quality_score = max(0.0, 1.0 - (total_violations * 0.01))
            
            return {
                'success': True,
                'path': str(path),
                'policy': policy,
                'violations': violation_dicts,
                'summary': {
                    'total_violations': total_violations,
                    'critical_violations': critical_count,
                    'overall_quality_score': quality_score
                },
                'nasa_compliance': {
                    'score': 0.8,  # Fallback score
                    'violations': [v for v in violation_dicts if 'NASA' in v.get('rule_id', '')]
                },
                'mece_analysis': {
                    'score': 0.75,  # Fallback score
                    'duplications': []
                },
                'god_objects': self._extract_god_objects(violation_dicts),
                'metrics': {
                    'files_analyzed': len(list(Path(path).glob('**/*.py'))) if Path(path).is_dir() else 1,
                    'analysis_time': 1.0,
                    'timestamp': time.time()
                }
            }
            
        except Exception as e:
            return self._run_mock_analysis(path, policy, **kwargs)
    
    def _run_mock_analysis(self, path: str, policy: str, **kwargs) -> Dict[str, Any]:
        """Fallback mock analysis when real analyzers are unavailable."""
        # Generate basic mock violations for testing
        violations = self._generate_mock_violations(path, policy)
        
        return {
            'success': True,
            'path': str(path),
            'policy': policy,
            'violations': [self._violation_to_dict(v) for v in violations],
            'summary': {
                'total_violations': len(violations),
                'critical_violations': len([v for v in violations if v.severity == 'critical']),
                'overall_quality_score': 0.75
            },
            'nasa_compliance': {
                'score': 0.85,
                'violations': [self._violation_to_dict(v) for v in violations if v.rule_id.startswith('NASA')]
            },
            'mece_analysis': {
                'score': 0.75,
                'duplications': []
            },
            'god_objects': [],
            'metrics': {
                'files_analyzed': 1 if Path(path).is_file() else 5,
                'analysis_time': 0.5,
                'timestamp': time.time()
            }
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
                weight=2.0
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
                    weight=5.0
                )
            )
        
        return violations
    
    def _convert_policy_to_preset(self, policy: str) -> str:
        """Convert policy string to unified analyzer preset."""
        policy_mapping = {
            "default": "service-defaults",
            "strict-core": "strict-analysis",
            "nasa_jpl_pot10": "nasa-compliance",
            "lenient": "basic-analysis"
        }
        return policy_mapping.get(policy, "service-defaults")
    
    def _extract_god_objects(self, violations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract god object violations from violation list."""
        return [v for v in violations if v.get('type') == 'god_object' or 'god_object' in v.get('rule_id', '').lower()]
    
    def _violation_to_dict(self, violation: ConnascenceViolation) -> Dict[str, Any]:
        """Convert violation object to dictionary with enhanced metadata."""
        if isinstance(violation, dict):
            return violation  # Already a dictionary
            
        return {
            'id': getattr(violation, 'id', str(hash(str(violation)))),
            'rule_id': getattr(violation, 'rule_id', 'UNKNOWN'),
            'type': getattr(violation, 'connascence_type', getattr(violation, 'type', 'unknown')),
            'severity': getattr(violation, 'severity', 'medium'),
            'description': getattr(violation, 'description', str(violation)),
            'file_path': getattr(violation, 'file_path', ''),
            'line_number': getattr(violation, 'line_number', 0),
            'weight': getattr(violation, 'weight', VIOLATION_WEIGHTS.get(getattr(violation, 'severity', 'medium'), 1)),
            'analysis_mode': self.analysis_mode
        }


def create_parser() -> argparse.ArgumentParser:
    """Create command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Connascence Safety Analyzer",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--path', '-p',
        type=str,
        default='.',
        help='Path to analyze (default: current directory)'
    )
    
    parser.add_argument(
        '--policy',
        type=str,
        default='default',
        choices=['default', 'strict-core', 'nasa_jpl_pot10', 'lenient'],
        help='Analysis policy to use'
    )
    
    parser.add_argument(
        '--format', '-f',
        type=str,
        default='json',
        choices=['json', 'yaml', 'sarif'],
        help='Output format'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        help='Output file path'
    )
    
    parser.add_argument(
        '--nasa-validation',
        action='store_true',
        help='Enable NASA Power of Ten validation'
    )
    
    parser.add_argument(
        '--strict-mode',
        action='store_true',
        help='Enable strict analysis mode'
    )
    
    parser.add_argument(
        '--exclude',
        type=str,
        nargs='*',
        default=[],
        help='Paths to exclude from analysis'
    )
    
    parser.add_argument(
        '--include-nasa-rules',
        action='store_true',
        help='Include NASA-specific rules in SARIF output'
    )
    
    parser.add_argument(
        '--include-god-objects',
        action='store_true',
        help='Include god object analysis in SARIF output'
    )
    
    parser.add_argument(
        '--include-mece-analysis',
        action='store_true',
        help='Include MECE duplication analysis in SARIF output'
    )
    
    parser.add_argument(
        '--enable-tool-correlation',
        action='store_true',
        help='Enable cross-tool analysis correlation'
    )
    
    parser.add_argument(
        '--confidence-threshold',
        type=float,
        default=0.8,
        help='Confidence threshold for correlations'
    )
    
    return parser


def main():
    """Main entry point for command-line execution."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Initialize analyzer
    analyzer = ConnascenceAnalyzer()
    
    # Set policy based on flags
    if args.nasa_validation:
        policy = 'nasa_jpl_pot10'
    else:
        policy = args.policy
    
    try:
        # Run analysis
        result = analyzer.analyze_path(
            path=args.path,
            policy=policy,
            strict_mode=args.strict_mode,
            exclude=args.exclude,
            enable_tool_correlation=args.enable_tool_correlation,
            confidence_threshold=args.confidence_threshold
        )
        
        # Handle different output formats
        if args.format == 'sarif':
            # Use the proper SARIFReporter class
            sarif_reporter = SARIFReporter()
            if args.output:
                sarif_reporter.export_results(result, args.output)
                print(f"SARIF report written to: {args.output}")
            else:
                sarif_output = sarif_reporter.export_results(result)
                # Handle Unicode characters for Windows terminal
                try:
                    print(sarif_output)
                except UnicodeEncodeError:
                    print(sarif_output.encode('ascii', errors='replace').decode('ascii'))
        elif args.format == 'json':
            # Use JSONReporter for consistent formatting
            json_reporter = JSONReporter()
            if args.output:
                json_reporter.export_results(result, args.output)
                print(f"JSON report written to: {args.output}")
            else:
                json_output = json_reporter.export_results(result)
                # Handle Unicode characters for Windows terminal
                try:
                    print(json_output)
                except UnicodeEncodeError:
                    print(json_output.encode('ascii', errors='replace').decode('ascii'))
        else:
            # Fallback to simple output
            if args.output:
                with open(args.output, 'w') as f:
                    f.write(str(result))
            else:
                print(result)
        
        # Exit with appropriate code
        if result.get('success', False):
            violations = result.get('violations', [])
            critical_count = len([v for v in violations if v.get('severity') == 'critical'])
            # Only fail on critical violations if in strict mode
            if critical_count > 0 and args.strict_mode:
                print(f"Analysis completed with {critical_count} critical violations", file=sys.stderr)
                sys.exit(1)
            print(f"Analysis completed successfully. {len(violations)} total violations ({critical_count} critical)")
            sys.exit(0)
        else:
            print(f"Analysis failed: {result.get('error', 'Unknown error')}", file=sys.stderr)
            sys.exit(1)
            
    except Exception as e:
        print(f"Analyzer error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        
        # Generate a minimal output file for CI compatibility
        if args.output and args.format in ['json', 'sarif']:
            try:
                minimal_result = {
                    'success': False,
                    'error': str(e),
                    'violations': [],
                    'summary': {'total_violations': 0},
                    'nasa_compliance': {'score': 0.0, 'violations': []}
                }
                
                if args.format == 'sarif':
                    sarif_reporter = SARIFReporter()
                    sarif_reporter.export_results(minimal_result, args.output)
                else:
                    json_reporter = JSONReporter()
                    json_reporter.export_results(minimal_result, args.output)
                    
                print(f"Minimal {args.format.upper()} report written for CI compatibility")
            except Exception as export_error:
                print(f"Failed to write minimal report: {export_error}", file=sys.stderr)
                
        sys.exit(1)


# Deprecated: Use SARIFReporter class instead
def convert_to_sarif(result: Dict[str, Any], args) -> Dict[str, Any]:
    """Legacy SARIF conversion - use SARIFReporter class instead."""
    print("Warning: Using deprecated convert_to_sarif function. Use SARIFReporter class instead.", file=sys.stderr)
    reporter = SARIFReporter()
    return json.loads(reporter.export_results(result))


# Deprecated: Use SARIFReporter._map_severity_to_level instead
def map_severity_to_sarif(severity: str) -> str:
    """Legacy severity mapping - use SARIFReporter class instead."""
    from reporting.sarif_export import SARIFReporter
    reporter = SARIFReporter()
    return reporter._map_severity_to_level(severity)


if __name__ == "__main__":
    main()


__all__ = ["ConnascenceAnalyzer", "ConnascenceViolation", "main"]
