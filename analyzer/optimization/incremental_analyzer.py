# SPDX-License-Identifier: MIT
"""
Incremental Analysis System
===========================

Optimized incremental analysis for CI/CD pipelines that only
analyzes changed files and their dependencies.
"""

from dataclasses import dataclass, field
import hashlib
import json
import logging
from pathlib import Path
import subprocess
import sys
import time
from typing import Any, Dict, List, Optional, Union

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from analyzer.caching.ast_cache import ast_cache
from analyzer.core import ConnascenceAnalyzer

logger = logging.getLogger(__name__)


@dataclass
class FileChangeInfo:
    """Information about a changed file."""

    file_path: str
    change_type: str  # 'added', 'modified', 'deleted', 'renamed'
    old_path: Optional[str] = None
    content_hash: Optional[str] = None
    size_bytes: int = 0
    modification_time: float = 0.0


@dataclass
class IncrementalAnalysisResult:
    """Result from incremental analysis."""

    # Analysis scope
    total_files_in_project: int
    changed_files_count: int
    analyzed_files_count: int
    skipped_files_count: int

    # Results
    violations: List[Dict[str, Any]]
    new_violations: List[Dict[str, Any]]
    resolved_violations: List[Dict[str, Any]]

    # Performance metrics
    analysis_time_seconds: float
    time_saved_seconds: float
    cache_hit_rate: float

    # Change tracking
    baseline_commit: Optional[str]
    current_commit: Optional[str]
    changed_files: List[FileChangeInfo]

    # Quality metrics
    quality_score_change: float
    regression_detected: bool
    improvement_detected: bool

    timestamp: str = field(default_factory=lambda: time.strftime("%Y-%m-%d %H:%M:%S"))


class IncrementalAnalyzer:
    """
    Incremental analyzer that optimizes CI/CD performance by analyzing
    only changed files and their dependencies.
    """

    def __init__(
        self,
        project_root: Union[str, Path],
        baseline_results_file: str = ".connascence_baseline.json",
        dependency_cache_file: str = ".connascence_deps.json",
    ):
        """Initialize incremental analyzer."""

        self.project_root = Path(project_root)
        self.baseline_file = self.project_root / baseline_results_file
        self.dependency_cache_file = self.project_root / dependency_cache_file

        self.analyzer = ConnascenceAnalyzer()
        self.baseline_results = {}
        self.dependency_graph = {}

        # Load existing baseline and dependencies
        self._load_baseline_results()
        self._load_dependency_cache()

        logger.info(f"Incremental analyzer initialized for {self.project_root}")

    def analyze_changes(
        self,
        commit_range: Optional[str] = None,
        changed_files: Optional[List[str]] = None,
        force_baseline: bool = False,
    ) -> IncrementalAnalysisResult:
        """
        Analyze only changed files and their dependencies.

        Args:
            commit_range: Git commit range (e.g., "HEAD~1..HEAD")
            changed_files: Explicit list of changed files
            force_baseline: Force creation of new baseline

        Returns:
            Incremental analysis result
        """

        start_time = time.time()
        logger.info("Starting incremental analysis")

        # Determine changed files
        if changed_files:
            changes = [FileChangeInfo(file_path=f, change_type="modified") for f in changed_files]
        else:
            changes = self._detect_changed_files(commit_range)

        logger.info(f"Detected {len(changes)} changed files")

        # Create or update baseline if needed
        if force_baseline or not self._has_valid_baseline():
            logger.info("Creating new baseline analysis")
            baseline_result = self._create_baseline()
        else:
            logger.info("Using existing baseline")
            baseline_result = self.baseline_results

        # Find files that need analysis (changed files + dependencies)
        files_to_analyze = self._determine_analysis_scope(changes)

        logger.info(f"Analysis scope: {len(files_to_analyze)} files")

        # Perform incremental analysis
        analysis_results = self._analyze_files(files_to_analyze)

        # Compare with baseline
        comparison_results = self._compare_with_baseline(analysis_results, baseline_result)

        # Calculate performance metrics
        analysis_time = time.time() - start_time
        cache_stats = ast_cache.get_cache_statistics()

        # Estimate time saved
        total_files = len(list(self.project_root.glob("**/*.py")))
        files_skipped = total_files - len(files_to_analyze)
        estimated_full_analysis_time = analysis_time * (total_files / max(len(files_to_analyze), 1))
        time_saved = estimated_full_analysis_time - analysis_time

        # Get current commit info
        current_commit = self._get_current_commit()
        baseline_commit = baseline_result.get("commit_hash")

        # Create result
        result = IncrementalAnalysisResult(
            total_files_in_project=total_files,
            changed_files_count=len(changes),
            analyzed_files_count=len(files_to_analyze),
            skipped_files_count=files_skipped,
            violations=analysis_results.get("violations", []),
            new_violations=comparison_results["new_violations"],
            resolved_violations=comparison_results["resolved_violations"],
            analysis_time_seconds=analysis_time,
            time_saved_seconds=time_saved,
            cache_hit_rate=cache_stats.get("hit_rate_percent", 0),
            baseline_commit=baseline_commit,
            current_commit=current_commit,
            changed_files=changes,
            quality_score_change=comparison_results["quality_score_change"],
            regression_detected=comparison_results["regression_detected"],
            improvement_detected=comparison_results["improvement_detected"],
        )

        # Update baseline with current results
        self._update_baseline(analysis_results, current_commit)

        logger.info(
            f"Incremental analysis complete: {analysis_time:.2f}s saved {time_saved:.2f}s "
            f"({len(comparison_results['new_violations'])} new violations)"
        )

        return result

    def create_baseline(self) -> Dict[str, Any]:
        """Create a new baseline by analyzing the entire project."""

        logger.info("Creating comprehensive baseline analysis")
        start_time = time.time()

        # Analyze entire project
        result = self.analyzer.analyze_path(str(self.project_root))

        # Add metadata
        baseline = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "commit_hash": self._get_current_commit(),
            "analysis_time": time.time() - start_time,
            "violations": result.get("violations", []),
            "summary": result.get("summary", {}),
            "quality_metrics": {
                "overall_quality_score": result.get("summary", {}).get("overall_quality_score", 0),
                "total_violations": len(result.get("violations", [])),
                "critical_violations": len(
                    [v for v in result.get("violations", []) if v.get("severity") == "critical"]
                ),
            },
        }

        # Save baseline
        self.baseline_results = baseline
        self._save_baseline_results()

        # Update dependency cache
        self._update_dependency_cache()

        analysis_time = time.time() - start_time
        logger.info(f"Baseline created: {len(baseline['violations'])} violations, {analysis_time:.2f}s")

        return baseline

    def get_analysis_report(self, result: IncrementalAnalysisResult) -> Dict[str, Any]:
        """Generate detailed analysis report."""

        return {
            "incremental_analysis_summary": {
                "analysis_date": result.timestamp,
                "baseline_commit": result.baseline_commit,
                "current_commit": result.current_commit,
                "analysis_scope": {
                    "total_project_files": result.total_files_in_project,
                    "changed_files": result.changed_files_count,
                    "analyzed_files": result.analyzed_files_count,
                    "skipped_files": result.skipped_files_count,
                    "skip_percentage": (result.skipped_files_count / result.total_files_in_project) * 100,
                },
            },
            "performance_metrics": {
                "analysis_time_seconds": result.analysis_time_seconds,
                "time_saved_seconds": result.time_saved_seconds,
                "performance_improvement_percent": (
                    result.time_saved_seconds / (result.analysis_time_seconds + result.time_saved_seconds)
                )
                * 100,
                "cache_hit_rate_percent": result.cache_hit_rate,
                "throughput_files_per_second": (
                    result.analyzed_files_count / result.analysis_time_seconds
                    if result.analysis_time_seconds > 0
                    else 0
                ),
            },
            "quality_changes": {
                "quality_score_change": result.quality_score_change,
                "regression_detected": result.regression_detected,
                "improvement_detected": result.improvement_detected,
                "new_violations_count": len(result.new_violations),
                "resolved_violations_count": len(result.resolved_violations),
                "net_violation_change": len(result.new_violations) - len(result.resolved_violations),
            },
            "change_analysis": {
                "changed_files": [
                    {
                        "file_path": change.file_path,
                        "change_type": change.change_type,
                        "old_path": change.old_path,
                        "size_bytes": change.size_bytes,
                    }
                    for change in result.changed_files
                ],
                "change_types": self._summarize_change_types(result.changed_files),
            },
            "violation_details": {
                "all_violations": result.violations,
                "new_violations": result.new_violations,
                "resolved_violations": result.resolved_violations,
                "violation_trends": self._analyze_violation_trends(result),
            },
        }

    def optimize_for_ci_cd(self) -> Dict[str, Any]:
        """Optimize analyzer settings for CI/CD performance."""

        recommendations = {
            "cache_optimization": {},
            "analysis_scope": {},
            "performance_tuning": {},
            "ci_cd_integration": {},
        }

        # Analyze cache performance
        cache_stats = ast_cache.get_cache_statistics()
        if cache_stats["hit_rate_percent"] < 70:
            recommendations["cache_optimization"]["increase_cache_size"] = {
                "current_hit_rate": cache_stats["hit_rate_percent"],
                "recommendation": "Increase cache size or enable cache warming",
            }

        # Analyze dependency patterns
        if hasattr(self, "dependency_graph") and self.dependency_graph:
            high_fan_out_files = [file_path for file_path, deps in self.dependency_graph.items() if len(deps) > 20]

            if high_fan_out_files:
                recommendations["analysis_scope"]["high_impact_files"] = {
                    "files": high_fan_out_files[:5],  # Top 5
                    "recommendation": "Consider architectural improvements to reduce coupling",
                }

        # Performance tuning
        recommendations["performance_tuning"] = {
            "parallel_processing": "Enable parallel processing for large codebases",
            "incremental_mode": "Use incremental analysis in CI/CD pipelines",
            "cache_warming": "Pre-warm cache in build pipelines",
        }

        # CI/CD integration recommendations
        recommendations["ci_cd_integration"] = {
            "pre_commit_hooks": "Run incremental analysis on changed files only",
            "pr_analysis": "Compare violation changes between branches",
            "baseline_updates": "Update baseline on main branch merges",
            "performance_monitoring": "Track analysis time trends",
        }

        return recommendations

    # Private implementation methods

    def _detect_changed_files(self, commit_range: Optional[str] = None) -> List[FileChangeInfo]:
        """Detect changed files using Git."""

        changes = []

        try:
            # Default to comparing with previous commit
            if not commit_range:
                commit_range = "HEAD~1..HEAD"

            # Get list of changed files
            cmd = ["git", "diff", "--name-status", commit_range]
            result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True)

            if result.returncode != 0:
                logger.warning(f"Git command failed: {result.stderr}")
                return []

            # Parse Git output
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue

                parts = line.split("\t")
                if len(parts) < 2:
                    continue

                status = parts[0]
                file_path = parts[1]

                # Only analyze relevant file types
                if not self._is_analyzable_file(file_path):
                    continue

                change_info = FileChangeInfo(file_path=file_path, change_type=self._map_git_status(status))

                # Add file metadata if file exists
                full_path = self.project_root / file_path
                if full_path.exists():
                    stat = full_path.stat()
                    change_info.size_bytes = stat.st_size
                    change_info.modification_time = stat.st_mtime

                    # Calculate content hash
                    try:
                        with open(full_path, "rb") as f:
                            content_hash = hashlib.md5(f.read()).hexdigest()
                        change_info.content_hash = content_hash
                    except Exception:
                        pass

                changes.append(change_info)

        except Exception as e:
            logger.error(f"Failed to detect changed files: {e}")

        return changes

    def _determine_analysis_scope(self, changes: List[FileChangeInfo]) -> List[str]:
        """Determine which files need analysis based on changes and dependencies."""

        files_to_analyze = set()

        # Add all changed files
        for change in changes:
            if change.change_type != "deleted":
                files_to_analyze.add(change.file_path)

        # Add dependent files
        for change in changes:
            if change.file_path in self.dependency_graph:
                dependents = self.dependency_graph[change.file_path].get("dependents", [])
                files_to_analyze.update(dependents)

        # Filter to only existing, analyzable files
        valid_files = []
        for file_path in files_to_analyze:
            full_path = self.project_root / file_path
            if full_path.exists() and self._is_analyzable_file(file_path):
                valid_files.append(file_path)

        return valid_files

    def _analyze_files(self, file_paths: List[str]) -> Dict[str, Any]:
        """Analyze specific files."""

        if not file_paths:
            return {"violations": [], "summary": {"total_violations": 0}}

        all_violations = []

        for file_path in file_paths:
            try:
                full_path = self.project_root / file_path
                result = self.analyzer.analyze_path(str(full_path))

                # Add file violations
                file_violations = result.get("violations", [])
                all_violations.extend(file_violations)

            except Exception as e:
                logger.warning(f"Failed to analyze {file_path}: {e}")

        return {
            "violations": all_violations,
            "summary": {"total_violations": len(all_violations), "files_analyzed": len(file_paths)},
        }

    def _compare_with_baseline(
        self, current_results: Dict[str, Any], baseline_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Compare current results with baseline."""

        current_violations = current_results.get("violations", [])
        baseline_violations = baseline_results.get("violations", [])

        # Create violation signatures for comparison
        def violation_signature(v):
            return (v.get("file_path", ""), v.get("line_number", 0), v.get("rule_id", ""), v.get("description", ""))

        current_sigs = {violation_signature(v): v for v in current_violations}
        baseline_sigs = {violation_signature(v): v for v in baseline_violations}

        # Find new and resolved violations
        new_violations = [v for sig, v in current_sigs.items() if sig not in baseline_sigs]

        resolved_violations = [v for sig, v in baseline_sigs.items() if sig not in current_sigs]

        # Calculate quality score changes
        current_quality = current_results.get("summary", {}).get("overall_quality_score", 0)
        baseline_quality = baseline_results.get("quality_metrics", {}).get("overall_quality_score", 0)
        quality_change = current_quality - baseline_quality

        # Detect regressions and improvements
        regression_detected = len(new_violations) > 0 or quality_change < -0.05
        improvement_detected = len(resolved_violations) > 0 or quality_change > 0.05

        return {
            "new_violations": new_violations,
            "resolved_violations": resolved_violations,
            "quality_score_change": quality_change,
            "regression_detected": regression_detected,
            "improvement_detected": improvement_detected,
        }

    def _is_analyzable_file(self, file_path: str) -> bool:
        """Check if file should be analyzed."""

        analyzable_extensions = {".py", ".js", ".ts", ".jsx", ".tsx"}
        return Path(file_path).suffix.lower() in analyzable_extensions

    def _map_git_status(self, status: str) -> str:
        """Map Git status codes to change types."""

        mapping = {"A": "added", "M": "modified", "D": "deleted", "R": "renamed", "C": "copied"}

        return mapping.get(status[0], "modified")

    def _has_valid_baseline(self) -> bool:
        """Check if current baseline is valid."""

        if not self.baseline_file.exists():
            return False

        if not self.baseline_results:
            return False

        # Check if baseline is recent (within last 7 days)
        try:
            baseline_time = time.mktime(time.strptime(self.baseline_results.get("timestamp", ""), "%Y-%m-%d %H:%M:%S"))

            age_days = (time.time() - baseline_time) / 86400
            return age_days < 7

        except Exception:
            return False

    def _create_baseline(self) -> Dict[str, Any]:
        """Create new baseline analysis."""
        return self.create_baseline()

    def _load_baseline_results(self):
        """Load baseline results from file."""

        if self.baseline_file.exists():
            try:
                with open(self.baseline_file) as f:
                    self.baseline_results = json.load(f)
                logger.debug("Loaded baseline results")
            except Exception as e:
                logger.warning(f"Failed to load baseline results: {e}")
                self.baseline_results = {}

    def _save_baseline_results(self):
        """Save baseline results to file."""

        try:
            with open(self.baseline_file, "w") as f:
                json.dump(self.baseline_results, f, indent=2, default=str)
            logger.debug("Saved baseline results")
        except Exception as e:
            logger.error(f"Failed to save baseline results: {e}")

    def _update_baseline(self, current_results: Dict[str, Any], commit_hash: Optional[str]):
        """Update baseline with current results."""

        self.baseline_results = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "commit_hash": commit_hash,
            "violations": current_results.get("violations", []),
            "summary": current_results.get("summary", {}),
            "quality_metrics": {
                "overall_quality_score": current_results.get("summary", {}).get("overall_quality_score", 0),
                "total_violations": len(current_results.get("violations", [])),
                "critical_violations": len(
                    [v for v in current_results.get("violations", []) if v.get("severity") == "critical"]
                ),
            },
        }

        self._save_baseline_results()

    def _load_dependency_cache(self):
        """Load dependency cache from file."""

        if self.dependency_cache_file.exists():
            try:
                with open(self.dependency_cache_file) as f:
                    self.dependency_graph = json.load(f)
                logger.debug("Loaded dependency cache")
            except Exception as e:
                logger.warning(f"Failed to load dependency cache: {e}")
                self.dependency_graph = {}

    def _update_dependency_cache(self):
        """Update dependency cache (simplified implementation)."""

        # This is a simplified implementation
        # In a full implementation, this would analyze import/dependency relationships

        python_files = list(self.project_root.glob("**/*.py"))

        for file_path in python_files:
            relative_path = str(file_path.relative_to(self.project_root))

            # Simple dependency detection based on imports
            try:
                with open(file_path, encoding="utf-8") as f:
                    content = f.read()

                dependencies = []
                dependents = []

                # Extract import statements (simplified)
                for line in content.split("\n"):
                    line = line.strip()
                    if line.startswith("import ") or line.startswith("from "):
                        # This is a very simplified dependency extraction
                        # A full implementation would use AST parsing
                        pass

                self.dependency_graph[relative_path] = {
                    "dependencies": dependencies,
                    "dependents": dependents,
                    "last_updated": time.time(),
                }

            except Exception as e:
                logger.warning(f"Failed to analyze dependencies for {file_path}: {e}")

        # Save dependency cache
        try:
            with open(self.dependency_cache_file, "w") as f:
                json.dump(self.dependency_graph, f, indent=2, default=str)
            logger.debug("Updated dependency cache")
        except Exception as e:
            logger.error(f"Failed to save dependency cache: {e}")

    def _get_current_commit(self) -> Optional[str]:
        """Get current Git commit hash."""

        try:
            cmd = ["git", "rev-parse", "HEAD"]
            result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True)

            if result.returncode == 0:
                return result.stdout.strip()

        except Exception as e:
            logger.warning(f"Failed to get current commit: {e}")

        return None

    def _summarize_change_types(self, changes: List[FileChangeInfo]) -> Dict[str, int]:
        """Summarize change types."""

        summary = {}
        for change in changes:
            change_type = change.change_type
            summary[change_type] = summary.get(change_type, 0) + 1

        return summary

    def _analyze_violation_trends(self, result: IncrementalAnalysisResult) -> Dict[str, Any]:
        """Analyze violation trends."""

        return {
            "new_violations_by_severity": self._group_by_severity(result.new_violations),
            "resolved_violations_by_severity": self._group_by_severity(result.resolved_violations),
            "net_change_by_severity": {
                "critical": len([v for v in result.new_violations if v.get("severity") == "critical"])
                - len([v for v in result.resolved_violations if v.get("severity") == "critical"]),
                "high": len([v for v in result.new_violations if v.get("severity") == "high"])
                - len([v for v in result.resolved_violations if v.get("severity") == "high"]),
                "medium": len([v for v in result.new_violations if v.get("severity") == "medium"])
                - len([v for v in result.resolved_violations if v.get("severity") == "medium"]),
                "low": len([v for v in result.new_violations if v.get("severity") == "low"])
                - len([v for v in result.resolved_violations if v.get("severity") == "low"]),
            },
        }

    def _group_by_severity(self, violations: List[Dict[str, Any]]) -> Dict[str, int]:
        """Group violations by severity."""

        groups = {"critical": 0, "high": 0, "medium": 0, "low": 0}

        for violation in violations:
            severity = violation.get("severity", "medium")
            if severity in groups:
                groups[severity] += 1

        return groups


# Global incremental analyzer instance
def get_incremental_analyzer(project_root: Union[str, Path]) -> IncrementalAnalyzer:
    """Get incremental analyzer instance for project."""
    return IncrementalAnalyzer(project_root)
