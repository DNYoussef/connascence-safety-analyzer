#!/usr/bin/env python3
"""
Script to refactor analyzer/core.py create_parser() from 102 LOC to ≤60 LOC.
Extracts argument groups into helper functions.
"""

from pathlib import Path
import sys

# Path to the file
core_file = Path(__file__).parent.parent / "analyzer" / "core.py"

# Read the file
with open(core_file, encoding="utf-8") as f:
    content = f.read()

# Helper functions to insert before create_parser()
helper_functions = '''
def _add_basic_arguments(parser: argparse.ArgumentParser):
    """
    Add basic arguments (path, policy, format, output).

    NASA Rule 4: Function under 60 lines
    """
    parser.add_argument("--path", "-p", type=str, default=".", help="Path to analyze (default: current directory)")

    # Get available policies for help text
    policy_help = (
        "Analysis policy to use. Unified: nasa-compliance, strict, standard, lenient (legacy names also accepted)"
    )
    try:
        if "list_available_policies" in globals() and list_available_policies:
            available_policies = list_available_policies(include_legacy=True)
            policy_help = f"Analysis policy to use. Available: {', '.join(available_policies)}"
    except:
        pass

    parser.add_argument(
        "--policy", type=str, default="standard", help=policy_help
    )
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
    parser.add_argument("--exclude", type=str, nargs="*", default=[], help="Paths to exclude from analysis")


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


'''

# New refactored create_parser() function
new_function = '''def create_parser() -> argparse.ArgumentParser:
    """
    Create command-line argument parser.

    Refactored to comply with NASA Rule 4 (≤60 lines per function).
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

    return parser


'''

# Find create_parser() in the file
start_marker = "def create_parser() -> argparse.ArgumentParser:"
end_marker = "\n\ndef _validate_and_resolve_policy(policy: str) -> str:"

start_idx = content.find(start_marker)
end_idx = content.find(end_marker)

if start_idx == -1 or end_idx == -1:
    print("[ERROR] Could not find create_parser() function boundaries")
    sys.exit(1)

# Create new content
new_content = content[:start_idx] + helper_functions + new_function + content[end_idx:]

# Write the refactored file
with open(core_file, "w", encoding="utf-8") as f:
    f.write(new_content)

print("[SUCCESS] Refactored create_parser() function!")
print("  Original: ~102 LOC")
print("  Refactored: ~20 LOC")
print("  Helper functions created: 5")
print("    - _add_basic_arguments(): ~25 LOC")
print("    - _add_analysis_arguments(): ~20 LOC")
print("    - _add_output_control_arguments(): ~15 LOC")
print("    - _add_exit_condition_arguments(): ~10 LOC")
print("    - _add_enhanced_pipeline_arguments(): ~30 LOC")
print("  Lines saved: ~82 LOC from main function")
