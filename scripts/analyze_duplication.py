#!/usr/bin/env python3
"""
Analyze duplication patterns from AIVillage MCP analysis results
"""
import json
import os


def analyze_duplication_patterns():
    """Extract and analyze duplication patterns from MCP results."""

    # Load the comprehensive MCP analysis results
    with open("reports/fixed_aivillage_mcp_analysis.json") as f:
        mcp_data = json.load(f)

    # Extract duplication-related violations
    duplication_violations = []
    god_objects = []
    parameter_bombs = []
    magic_literals = []

    total_files = mcp_data.get("summary", {}).get("total_files_analyzed", 0)
    total_violations = mcp_data.get("summary", {}).get("total_violations", 0)

    print("DUPLICATION ANALYSIS RESULTS FROM AIVILLAGE:")
    print("=" * 60)
    print(f"Total Files Analyzed: {total_files}")
    print(f"Total Violations Found: {total_violations}")
    print()

    # Process file results to extract duplication patterns
    file_results = mcp_data.get("file_results", [])
    for file_result in file_results:
        violations = file_result.get("violations", [])
        file_path = file_result.get("file_path", "")

        for violation in violations:
            v_type = violation.get("type", "")
            severity = violation.get("severity", "")
            description = violation.get("description", "")
            line_num = violation.get("line_number", 0)

            violation_data = {
                "file": os.path.basename(file_path),
                "full_path": file_path,
                "description": description,
                "line": line_num,
                "severity": severity,
            }

            if v_type == "god_object":
                god_objects.append(violation_data)
            elif v_type == "CoP":  # Connascence of Position - Parameter bombs
                parameter_bombs.append(violation_data)
            elif v_type == "CoM":  # Connascence of Meaning - Magic literals
                magic_literals.append(violation_data)
            elif "duplicate" in description.lower() or "similar" in description.lower():
                duplication_violations.append(violation_data)

    # Display results
    print(f"GOD OBJECTS DETECTED: {len(god_objects)}")
    for i, go in enumerate(god_objects[:5]):  # Show first 5
        print(f'   {i+1}. {go["description"]} (Line {go["line"]})')
        print(f'      File: {go["file"]}')
        print()

    print(f"PARAMETER BOMBS (CoP): {len(parameter_bombs)}")
    for i, pb in enumerate(parameter_bombs[:3]):
        print(f'   {i+1}. {pb["description"]} (Line {pb["line"]})')
        print(f'      File: {pb["file"]}')
        print()

    print(f"MAGIC LITERALS (CoM): {len(magic_literals)}")
    print(
        f'   Found {len(magic_literals)} magic literal violations across {len({ml["file"] for ml in magic_literals})} files'
    )
    print()

    print(f"EXPLICIT DUPLICATION PATTERNS: {len(duplication_violations)}")
    for i, dv in enumerate(duplication_violations[:3]):
        print(f'   {i+1}. {dv["description"]}')
        print(f'      File: {dv["file"]}')
        print()

    # Calculate duplication statistics
    total_dup_violations = len(magic_literals) + len(god_objects) + len(parameter_bombs)
    print("DUPLICATION STATISTICS:")
    print(f"   • Total Duplication-Related Violations: {total_dup_violations}")
    print(f"   • Duplication Density: {total_dup_violations / max(total_files, 1):.2f} violations per file")
    print(f"   • God Object Rate: {len(god_objects) / max(total_files, 1) * 100:.1f}% of files")
    print(f"   • Magic Literal Rate: {len(magic_literals) / max(total_files, 1):.2f} per file")

    # Create summary report
    summary = {
        "total_files_analyzed": total_files,
        "total_violations": total_violations,
        "duplication_analysis": {
            "god_objects": len(god_objects),
            "parameter_bombs": len(parameter_bombs),
            "magic_literals": len(magic_literals),
            "explicit_duplications": len(duplication_violations),
            "total_duplication_violations": total_dup_violations,
            "duplication_density": total_dup_violations / max(total_files, 1),
            "god_object_rate": len(god_objects) / max(total_files, 1) * 100,
        },
        "top_god_objects": god_objects[:10],
        "top_parameter_bombs": parameter_bombs[:10],
        "sample_magic_literals": magic_literals[:20],
    }

    # Save detailed duplication analysis
    with open("reports/aivillage_duplication_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    print("\nDetailed analysis saved to reports/aivillage_duplication_summary.json")
    return summary


if __name__ == "__main__":
    analyze_duplication_patterns()
