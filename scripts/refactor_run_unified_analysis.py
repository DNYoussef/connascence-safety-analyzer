#!/usr/bin/env python3
"""
Script to refactor analyzer/core.py _run_unified_analysis() from 87 LOC to ≤60 LOC.
Extracts result handling into helper functions.
"""

from pathlib import Path
import sys

# Path to the file
core_file = Path(__file__).parent.parent / "analyzer" / "core.py"

# Read the file
with open(core_file, encoding="utf-8") as f:
    content = f.read()

# Helper functions to insert before _run_unified_analysis()
helper_functions = '''
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

'''

# New refactored _run_unified_analysis() function
new_function = '''    def _run_unified_analysis(
        self, path: str, policy: str, duplication_result: Optional[Any] = None, **kwargs
    ) -> Dict[str, Any]:
        """
        Run analysis using the unified analyzer pipeline.

        Refactored to comply with NASA Rule 4 (≤60 lines per function).
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

'''

# Find _run_unified_analysis() in the file
start_marker = "    def _run_unified_analysis(\n        self, path: str, policy: str, duplication_result: Optional[Any] = None, **kwargs\n    ) -> Dict[str, Any]:"
end_marker = "\n    def _run_fallback_analysis(\n        self, path: str, policy: str, duplication_result: Optional[Any] = None, **kwargs"

start_idx = content.find(start_marker)
end_idx = content.find(end_marker)

if start_idx == -1 or end_idx == -1:
    print("[ERROR] Could not find _run_unified_analysis() function boundaries")
    print(f"start_idx: {start_idx}, end_idx: {end_idx}")
    sys.exit(1)

# Create new content
new_content = content[:start_idx] + helper_functions + new_function + content[end_idx:]

# Write the refactored file
with open(core_file, "w", encoding="utf-8") as f:
    f.write(new_content)

print("[SUCCESS] Refactored _run_unified_analysis() function!")
print("  Original: ~87 LOC")
print("  Refactored: ~25 LOC")
print("  Helper functions created: 3")
print("    - _analyze_file_or_directory(): ~35 LOC")
print("    - _format_unified_result(): ~40 LOC")
print("    - _create_error_result(): ~12 LOC")
print("  Lines saved: ~62 LOC from main function")
