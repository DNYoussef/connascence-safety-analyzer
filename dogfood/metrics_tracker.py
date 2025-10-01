# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2024 Connascence Safety Analyzer Contributors
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

"""
Metrics Tracker - Quality Score Comparison & Baseline Management

Captures and compares connascence metrics to determine if dogfood
changes actually improve code quality.
"""

import asyncio
from dataclasses import asdict, dataclass
from datetime import datetime
import hashlib
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass
class QualityMetrics:
    """Complete quality metrics for codebase state"""

    connascence_score: float
    violation_count: int
    nasa_compliance: float
    code_quality: float
    maintainability_index: float

    # Detailed breakdown
    cop_violations: int  # Connascence of Position
    com_violations: int  # Connascence of Meaning
    con_violations: int  # Connascence of Name
    cot_violations: int  # Connascence of Type
    coa_violations: int  # Connascence of Algorithm

    # Additional metrics
    cyclomatic_complexity: float
    function_length_avg: float
    magic_literals_count: int
    god_object_count: int

    # Meta information
    timestamp: datetime
    codebase_hash: str
    scan_duration: float


@dataclass
class MetricsComparison:
    """Comparison between baseline and current metrics"""

    baseline: QualityMetrics
    current: QualityMetrics
    improvements: Dict[str, float]
    regressions: Dict[str, float]
    overall_improvement: bool
    improvement_score: float
    summary: str


class MetricsTracker:
    """Tracks and compares code quality metrics"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        self.project_root = Path.cwd()

        # Configuration
        self.analyzer_path = self.config.get("analyzer_path", "analyzer")
        self.baseline_file = self.project_root / ".dogfood_baseline.json"
        self.metrics_history_file = self.project_root / ".dogfood_history.json"

        # Quality thresholds
        self.min_improvement_threshold = self.config.get("min_improvement_threshold", 0.01)
        self.significant_improvement_threshold = self.config.get("significant_improvement_threshold", 0.05)

    async def capture_baseline(self) -> QualityMetrics:
        """
        Capture current codebase state as baseline for comparison

        Returns:
            QualityMetrics: Current quality metrics
        """
        self.logger.info("📊 Capturing baseline metrics...")

        try:
            metrics = await self._analyze_codebase()

            # Save baseline to file
            await self._save_baseline(metrics)

            self.logger.info(f"✅ Baseline captured: {metrics.connascence_score:.3f} score")
            return metrics

        except Exception as e:
            self.logger.error(f"❌ Failed to capture baseline: {e}")
            raise

    async def capture_current_state(self) -> QualityMetrics:
        """
        Capture current codebase state after changes

        Returns:
            QualityMetrics: Current quality metrics
        """
        self.logger.info("📈 Capturing current state metrics...")

        try:
            metrics = await self._analyze_codebase()

            # Save to history
            await self._save_to_history(metrics)

            self.logger.info(f"✅ Current state captured: {metrics.connascence_score:.3f} score")
            return metrics

        except Exception as e:
            self.logger.error(f"❌ Failed to capture current state: {e}")
            raise

    async def compare_with_baseline(self, current_metrics: QualityMetrics) -> MetricsComparison:
        """
        Compare current metrics with baseline

        Args:
            current_metrics: Current quality metrics

        Returns:
            MetricsComparison: Detailed comparison results
        """
        self.logger.info("🔍 Comparing metrics with baseline...")

        try:
            baseline_metrics = await self._load_baseline()

            if not baseline_metrics:
                raise RuntimeError("No baseline metrics found")

            # Calculate improvements and regressions
            improvements = {}
            regressions = {}

            metric_fields = ["connascence_score", "nasa_compliance", "code_quality", "maintainability_index"]

            for field in metric_fields:
                baseline_val = getattr(baseline_metrics, field)
                current_val = getattr(current_metrics, field)
                change = current_val - baseline_val

                if change > self.min_improvement_threshold:
                    improvements[field] = change
                elif change < -self.min_improvement_threshold:
                    regressions[field] = abs(change)

            # Count-based metrics (lower is better)
            count_fields = [
                "violation_count",
                "cop_violations",
                "com_violations",
                "con_violations",
                "cot_violations",
                "coa_violations",
                "magic_literals_count",
                "god_object_count",
            ]

            for field in count_fields:
                baseline_val = getattr(baseline_metrics, field)
                current_val = getattr(current_metrics, field)
                change = baseline_val - current_val  # Inverted for count metrics

                if change > 0:  # Reduction in violations is improvement
                    improvements[f"{field}_reduction"] = change
                elif change < 0:  # Increase in violations is regression
                    regressions[f"{field}_increase"] = abs(change)

            # Overall assessment
            overall_improvement = (
                len(improvements) > len(regressions)
                and current_metrics.connascence_score > baseline_metrics.connascence_score
            )

            # Calculate improvement score
            improvement_score = self._calculate_improvement_score(baseline_metrics, current_metrics)

            # Generate summary
            summary = self._generate_comparison_summary(
                improvements, regressions, overall_improvement, improvement_score
            )

            comparison = MetricsComparison(
                baseline=baseline_metrics,
                current=current_metrics,
                improvements=improvements,
                regressions=regressions,
                overall_improvement=overall_improvement,
                improvement_score=improvement_score,
                summary=summary,
            )

            self.logger.info(f"📊 Comparison complete: {summary}")
            return comparison

        except Exception as e:
            self.logger.error(f"❌ Failed to compare metrics: {e}")
            raise

    async def _analyze_codebase(self) -> QualityMetrics:
        """Run comprehensive codebase analysis"""
        scan_start = datetime.now()

        try:
            # Run connascence analyzer
            analysis_result = await self._run_connascence_analysis()

            # Calculate codebase hash for fingerprinting
            codebase_hash = await self._calculate_codebase_hash()

            scan_duration = (datetime.now() - scan_start).total_seconds()

            # Extract metrics from analysis result
            metrics = self._extract_metrics_from_analysis(analysis_result, scan_start, codebase_hash, scan_duration)

            return metrics

        except Exception as e:
            self.logger.error(f"Failed to analyze codebase: {e}")
            # Return default metrics on failure
            return QualityMetrics(
                connascence_score=0.0,
                violation_count=999,
                nasa_compliance=0.0,
                code_quality=0.0,
                maintainability_index=0.0,
                cop_violations=0,
                com_violations=0,
                con_violations=0,
                cot_violations=0,
                coa_violations=0,
                cyclomatic_complexity=999.0,
                function_length_avg=999.0,
                magic_literals_count=999,
                god_object_count=999,
                timestamp=scan_start,
                codebase_hash="error",
                scan_duration=0.0,
            )

    async def _run_connascence_analysis(self) -> Dict[str, Any]:
        """Run the connascence analyzer on the codebase"""
        try:
            # Run analyzer using Python module
            cmd = [
                "python",
                "-c",
                """
import sys
sys.path.append(".")
from analyzer.core import ConnascenceAnalyzer
analyzer = ConnascenceAnalyzer()
results = analyzer.analyze_directory(".")
print(f"VIOLATIONS: {len(results)}")
for violation in results[:10]:  # Limit output
    print(f"VIOLATION: {violation.violation_type} in {violation.file_path}")
""",
            ]

            process = await asyncio.create_subprocess_exec(
                *cmd, cwd=self.project_root, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                # Parse output to extract metrics
                return self._parse_analyzer_output(stdout.decode())
            else:
                self.logger.warning(f"Analyzer returned non-zero exit: {stderr.decode()}")
                return {"violations": [], "metrics": {}}

        except Exception as e:
            self.logger.error(f"Failed to run analyzer: {e}")
            return {"violations": [], "metrics": {}}

    def _parse_analyzer_output(self, output: str) -> Dict[str, Any]:
        """Parse analyzer output into structured data"""
        lines = output.strip().split("\n")
        violations = []
        total_violations = 0

        violation_counts = {
            "cop_violations": 0,
            "com_violations": 0,
            "con_violations": 0,
            "cot_violations": 0,
            "coa_violations": 0,
        }

        for line in lines:
            if line.startswith("VIOLATIONS: "):
                total_violations = int(line.split(": ")[1])
            elif line.startswith("VIOLATION: "):
                violation_info = line.split(": ")[1]
                violations.append(violation_info)

                # Count violation types
                if "Position" in violation_info:
                    violation_counts["cop_violations"] += 1
                elif "Meaning" in violation_info or "Magic" in violation_info:
                    violation_counts["com_violations"] += 1
                elif "Name" in violation_info:
                    violation_counts["con_violations"] += 1
                elif "Type" in violation_info:
                    violation_counts["cot_violations"] += 1
                elif "Algorithm" in violation_info:
                    violation_counts["coa_violations"] += 1

        return {"total_violations": total_violations, "violations": violations, "violation_counts": violation_counts}

    def _extract_metrics_from_analysis(
        self, analysis_result: Dict[str, Any], timestamp: datetime, codebase_hash: str, scan_duration: float
    ) -> QualityMetrics:
        """Extract QualityMetrics from analysis results"""

        total_violations = analysis_result.get("total_violations", 0)
        violation_counts = analysis_result.get("violation_counts", {})

        # Calculate connascence score (0-1, higher is better)
        # Base score on violation density
        estimated_loc = 10000  # Rough estimate, could be calculated
        violation_density = total_violations / estimated_loc if estimated_loc > 0 else 1.0
        connascence_score = max(0.0, 1.0 - violation_density)

        # Calculate NASA compliance (mock implementation)
        nasa_compliance = max(0.0, 1.0 - (violation_counts.get("cop_violations", 0) / 100))

        # Calculate overall code quality score
        code_quality = (connascence_score + nasa_compliance) / 2.0

        # Mock other metrics (would be calculated from actual analysis)
        maintainability_index = min(100.0, code_quality * 100)

        return QualityMetrics(
            connascence_score=connascence_score,
            violation_count=total_violations,
            nasa_compliance=nasa_compliance,
            code_quality=code_quality,
            maintainability_index=maintainability_index,
            cop_violations=violation_counts.get("cop_violations", 0),
            com_violations=violation_counts.get("com_violations", 0),
            con_violations=violation_counts.get("con_violations", 0),
            cot_violations=violation_counts.get("cot_violations", 0),
            coa_violations=violation_counts.get("coa_violations", 0),
            cyclomatic_complexity=10.0,  # Mock value
            function_length_avg=25.0,  # Mock value
            magic_literals_count=violation_counts.get("com_violations", 0),
            god_object_count=max(0, total_violations // 20),  # Rough estimate
            timestamp=timestamp,
            codebase_hash=codebase_hash,
            scan_duration=scan_duration,
        )

    async def _calculate_codebase_hash(self) -> str:
        """Calculate hash of codebase for fingerprinting"""
        try:
            # Get list of Python files
            cmd = ["find", ".", "-name", "*.py", "-type", "f"]
            process = await asyncio.create_subprocess_exec(
                *cmd, cwd=self.project_root, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )

            stdout, _ = await process.communicate()

            if process.returncode == 0:
                files = stdout.decode().strip().split("\n")
                # Create hash from file list and sizes
                hash_input = "|".join(sorted(files))
                return hashlib.md5(hash_input.encode()).hexdigest()
            else:
                return "unknown"

        except Exception:
            return "unknown"

    def _calculate_improvement_score(self, baseline: QualityMetrics, current: QualityMetrics) -> float:
        """Calculate overall improvement score (0-1, higher is better)"""

        # Weighted scoring
        weights = {"connascence_score": 0.4, "nasa_compliance": 0.3, "code_quality": 0.2, "violation_reduction": 0.1}

        # Calculate component scores
        scores = {}

        # Score improvements (0-1 scale)
        for metric in ["connascence_score", "nasa_compliance", "code_quality"]:
            baseline_val = getattr(baseline, metric)
            current_val = getattr(current, metric)

            if baseline_val > 0:
                improvement = (current_val - baseline_val) / baseline_val
                scores[metric] = min(1.0, max(0.0, improvement + 0.5))  # Normalize to 0-1
            else:
                scores[metric] = 0.5

        # Violation reduction score
        violation_reduction = baseline.violation_count - current.violation_count
        if baseline.violation_count > 0:
            reduction_ratio = violation_reduction / baseline.violation_count
            scores["violation_reduction"] = min(1.0, max(0.0, reduction_ratio + 0.5))
        else:
            scores["violation_reduction"] = 0.5

        # Calculate weighted average
        overall_score = sum(scores[metric] * weights[metric] for metric in weights)

        return overall_score

    def _generate_comparison_summary(
        self,
        improvements: Dict[str, float],
        regressions: Dict[str, float],
        overall_improvement: bool,
        improvement_score: float,
    ) -> str:
        """Generate human-readable comparison summary"""

        if overall_improvement:
            status = "✅ IMPROVED"
            if improvement_score > 0.8:
                level = "Excellent"
            elif improvement_score > 0.6:
                level = "Good"
            else:
                level = "Moderate"
        else:
            status = "❌ REGRESSED"
            level = "Poor"

        summary_parts = [f"{status} - {level} improvement (score: {improvement_score:.3f})"]

        if improvements:
            imp_list = [f"{k}: +{v:.3f}" for k, v in list(improvements.items())[:3]]
            summary_parts.append(f"Improvements: {', '.join(imp_list)}")

        if regressions:
            reg_list = [f"{k}: -{v:.3f}" for k, v in list(regressions.items())[:3]]
            summary_parts.append(f"Regressions: {', '.join(reg_list)}")

        return " | ".join(summary_parts)

    async def _save_baseline(self, metrics: QualityMetrics):
        """Save baseline metrics to file"""
        try:
            data = asdict(metrics)
            # Convert datetime to ISO format
            data["timestamp"] = metrics.timestamp.isoformat()

            with open(self.baseline_file, "w") as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            self.logger.error(f"Failed to save baseline: {e}")

    async def _load_baseline(self) -> Optional[QualityMetrics]:
        """Load baseline metrics from file"""
        try:
            if not self.baseline_file.exists():
                return None

            with open(self.baseline_file) as f:
                data = json.load(f)

            # Convert timestamp back
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])

            return QualityMetrics(**data)

        except Exception as e:
            self.logger.error(f"Failed to load baseline: {e}")
            return None

    async def _save_to_history(self, metrics: QualityMetrics):
        """Save metrics to history file"""
        try:
            history = []

            # Load existing history
            if self.metrics_history_file.exists():
                with open(self.metrics_history_file) as f:
                    history = json.load(f)

            # Add new entry
            data = asdict(metrics)
            data["timestamp"] = metrics.timestamp.isoformat()
            history.append(data)

            # Keep only last 100 entries
            history = history[-100:]

            # Save updated history
            with open(self.metrics_history_file, "w") as f:
                json.dump(history, f, indent=2)

        except Exception as e:
            self.logger.error(f"Failed to save to history: {e}")
