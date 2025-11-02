#!/usr/bin/env python3
"""
Script to refactor analyzer/core.py main() function from 264 LOC to <=60 LOC.
Extracts helper functions while maintaining functionality.
"""

from pathlib import Path
import sys

# Path to the file
core_file = Path(__file__).parent.parent / "analyzer" / "core.py"

# Read the file
with open(core_file, encoding="utf-8") as f:
    lines = f.readlines()

# Helper functions to insert before main()
helper_functions = '''
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
    if validate_policy_name:
        if not validate_policy_name(policy):
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

            print(
                f"Error: Unknown policy '{policy}'. Available policies: {', '.join(available_policies)}",
                file=sys.stderr,
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
        args.enable_correlations
        or args.enable_audit_trail
        or args.enable_smart_recommendations
        or args.enhanced_output
    )

    if use_enhanced_analyzer and UNIFIED_ANALYZER_AVAILABLE:
        print("Using enhanced unified analyzer for cross-phase analysis...")

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
            print(f"SARIF report written to: {args.output}")
        else:
            sarif_output = sarif_reporter.export_results(result)
            try:
                print(sarif_output)
            except UnicodeEncodeError:
                print(sarif_output.encode("ascii", errors="replace").decode("ascii"))
    elif args.format == "json":
        json_reporter = JSONReporter()
        if args.output:
            json_reporter.export_results(result, args.output)
            print(f"JSON report written to: {args.output}")
        else:
            json_output = json_reporter.export_results(result)
            try:
                print(json_output)
            except UnicodeEncodeError:
                print(json_output.encode("ascii", errors="replace").decode("ascii"))
    elif args.output:
        with open(args.output, "w") as f:
            f.write(str(result))
    else:
        print(result)


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
        print(f"Audit trail exported to: {args.export_audit_trail}")

    # Export correlations
    if args.export_correlations and result.get("correlations"):
        with open(args.export_correlations, "w") as f:
            json.dump(result["correlations"], f, indent=2, default=str)
        print(f"Correlations exported to: {args.export_correlations}")

    # Export smart recommendations
    if args.export_recommendations and result.get("smart_recommendations"):
        with open(args.export_recommendations, "w") as f:
            json.dump(result["smart_recommendations"], f, indent=2, default=str)
        print(f"Smart recommendations exported to: {args.export_recommendations}")

    # Display phase timing
    _display_phase_timing(args, result)

    # Display correlations summary
    _display_correlations_summary(result)

    # Display recommendations summary
    _display_recommendations_summary(result)


def _display_phase_timing(args, result):
    """Display phase timing information (helper for _export_enhanced_results)."""
    if args.phase_timing and result.get("audit_trail"):
        print("\\n=== Analysis Phase Timing ===")
        for phase in result["audit_trail"]:
            if phase.get("started") and phase.get("completed"):
                start_time = datetime.fromisoformat(phase["started"].replace("Z", "+00:00"))
                end_time = datetime.fromisoformat(phase["completed"].replace("Z", "+00:00"))
                duration = (end_time - start_time).total_seconds() * 1000

                phase_name = phase["phase"].replace("_", " ").title()
                violations = phase.get("violations_found", 0)
                clusters = phase.get("clusters_found", 0)

                print(
                    f"{phase_name:25} | {duration:8.1f}ms | {violations:3d} violations | {clusters:3d} clusters"
                )


def _display_correlations_summary(result):
    """Display correlation summary (helper for _export_enhanced_results)."""
    if result.get("correlations") and len(result["correlations"]) > 0:
        print("\\n=== Cross-Phase Analysis Summary ===")
        correlations = result["correlations"]
        print(f"Found {len(correlations)} cross-phase correlations")

        sorted_corr = sorted(correlations, key=lambda x: x.get("correlation_score", 0), reverse=True)
        for i, corr in enumerate(sorted_corr[:3]):
            score = corr.get("correlation_score", 0) * 100
            analyzer1 = corr.get("analyzer1", "Unknown")
            analyzer2 = corr.get("analyzer2", "Unknown")
            print(f"{i+1}. {analyzer1} <-> {analyzer2}: {score:.1f}% correlation")


def _display_recommendations_summary(result):
    """Display recommendations summary (helper for _export_enhanced_results)."""
    if result.get("smart_recommendations") and len(result["smart_recommendations"]) > 0:
        print("\\n=== Smart Recommendations Summary ===")
        recommendations = result["smart_recommendations"]
        print(f"Generated {len(recommendations)} architectural recommendations")

        high_priority = [r for r in recommendations if r.get("priority", "").lower() == "high"]
        for rec in high_priority[:3]:
            category = rec.get("category", "General")
            description = rec.get("description", "No description")[:60] + "..."
            print(f"• [{category}] {description}")


def _check_exit_conditions(args, result):
    """
    Check exit conditions and exit with appropriate code.

    NASA Rule 4: Function under 60 lines
    """
    if not result.get("success", False):
        print(f"Analysis failed: {result.get('error', 'Unknown error')}", file=sys.stderr)
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
        print(f"Analysis failed: {', '.join(exit_reasons)}", file=sys.stderr)
        sys.exit(1)

    print(f"Analysis completed successfully. {len(violations)} total violations ({critical_count} critical)")
    sys.exit(0)


def _handle_error(e: Exception, args):
    """
    Handle errors and generate minimal output for CI compatibility.

    NASA Rule 4: Function under 60 lines
    """
    print(f"Analyzer error: {e}", file=sys.stderr)
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

            print(f"Minimal {args.format.upper()} report written for CI compatibility")
        except Exception as export_error:
            print(f"Failed to write minimal report: {export_error}", file=sys.stderr)

    sys.exit(1)


'''

# New refactored main() function
new_main = '''def main():
    """
    Main entry point for command-line execution.

    Refactored to comply with NASA Rule 4 (<=60 lines per function).
    Helper functions handle distinct logical sections.
    """
    parser = create_parser()
    args = parser.parse_args()

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

    except Exception as e:
        _handle_error(e, args)


'''

# Find the line number where main() starts (should be around line 510)
main_start = None
for i, line in enumerate(lines):
    if line.strip().startswith("def main():"):
        main_start = i
        break

if main_start is None:
    print("[ERROR] Could not find main() function")
    sys.exit(1)

# Find the end of main() (next function definition or end of file)
main_end = None
for i in range(main_start + 1, len(lines)):
    # Look for next function definition at the same indentation level
    if lines[i].startswith("def ") or lines[i].startswith("# Deprecated"):
        main_end = i
        break

if main_end is None:
    main_end = len(lines)

# Create new file content
new_lines = []

# Add everything before main()
new_lines.extend(lines[:main_start])

# Add helper functions
new_lines.append(helper_functions)

# Add refactored main()
new_lines.append(new_main)

# Add everything after main()
new_lines.extend(lines[main_end:])

# Write the refactored file
with open(core_file, "w", encoding="utf-8") as f:
    f.writelines(new_lines)

print("[SUCCESS] Refactored analyzer/core.py main() function!")
print("  Original: ~264 LOC")
print("  Refactored: ~35 LOC")
print("  Helper functions created: 10")
print("  Lines saved: ~229 LOC")
