"""
Six Sigma Telemetry System for Connascence Analysis

Tracks and calculates enterprise-grade quality metrics specifically
for connascence violations and code quality.
"""

import statistics
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import json
import logging

logger = logging.getLogger(__name__)


class QualityLevel(Enum):
    """Six Sigma quality levels with DPMO thresholds"""
    ONE_SIGMA = 1.0      # 691,462 DPMO
    TWO_SIGMA = 2.0      # 308,537 DPMO
    THREE_SIGMA = 3.0    # 66,807 DPMO
    FOUR_SIGMA = 4.0     # 6,210 DPMO
    FIVE_SIGMA = 5.0     # 233 DPMO
    SIX_SIGMA = 6.0      # 3.4 DPMO


@dataclass
class SixSigmaMetrics:
    """Container for Six Sigma quality metrics"""
    dpmo: float = 0.0  # Defects Per Million Opportunities
    rty: float = 0.0   # Rolled Throughput Yield
    sigma_level: float = 0.0
    process_capability: float = 0.0
    quality_level: Optional[QualityLevel] = None
    timestamp: datetime = field(default_factory=datetime.now)
    process_name: str = ""
    sample_size: int = 0
    defect_count: int = 0
    opportunity_count: int = 0
    connascence_metrics: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary"""
        return {
            "dpmo": self.dpmo,
            "rty": self.rty,
            "sigma_level": self.sigma_level,
            "process_capability": self.process_capability,
            "quality_level": self.quality_level.name if self.quality_level else None,
            "timestamp": self.timestamp.isoformat(),
            "process_name": self.process_name,
            "sample_size": self.sample_size,
            "defect_count": self.defect_count,
            "opportunity_count": self.opportunity_count,
            "connascence_metrics": self.connascence_metrics
        }


class SixSigmaTelemetry:
    """
    Six Sigma telemetry system for connascence analysis

    Integrates Six Sigma quality metrics with connascence detection
    to provide enterprise-grade quality monitoring.
    """

    # Quality thresholds (DPMO values)
    QUALITY_THRESHOLDS = {
        QualityLevel.ONE_SIGMA: 691462,
        QualityLevel.TWO_SIGMA: 308537,
        QualityLevel.THREE_SIGMA: 66807,
        QualityLevel.FOUR_SIGMA: 6210,
        QualityLevel.FIVE_SIGMA: 233,
        QualityLevel.SIX_SIGMA: 3.4
    }

    # Connascence severity to opportunity multipliers
    CONNASCENCE_OPPORTUNITIES = {
        'identity': 5,
        'meaning': 4,
        'algorithm': 6,
        'position': 3,
        'execution': 7,
        'timing': 8,
        'values': 3,
        'type': 4,
        'convention': 2
    }

    def __init__(self, process_name: str = "connascence_analysis"):
        """Initialize telemetry system"""
        self.process_name = process_name
        self.metrics_history: List[SixSigmaMetrics] = []
        self.current_session_data = {
            'defects': 0,
            'opportunities': 0,
            'units_processed': 0,
            'units_passed': 0,
            'start_time': time.time(),
            'connascence_violations': {},
            'files_analyzed': 0,
            'critical_violations': 0,
            'high_violations': 0,
            'medium_violations': 0,
            'low_violations': 0
        }

    def record_connascence_violation(self, violation_type: str, severity: str):
        """Record a connascence violation as a defect"""
        # Count as defect
        self.current_session_data['defects'] += 1

        # Track by type
        if violation_type not in self.current_session_data['connascence_violations']:
            self.current_session_data['connascence_violations'][violation_type] = 0
        self.current_session_data['connascence_violations'][violation_type] += 1

        # Track by severity
        severity_key = f"{severity.lower()}_violations"
        if severity_key in self.current_session_data:
            self.current_session_data[severity_key] += 1

        # Calculate opportunities based on violation type
        opportunities = self.CONNASCENCE_OPPORTUNITIES.get(violation_type.lower(), 3)

        # Critical violations have more impact
        if severity.lower() == 'critical':
            opportunities *= 2

        self.current_session_data['opportunities'] += opportunities

        logger.debug(f"Recorded {severity} {violation_type} violation: {opportunities} opportunities")

    def record_file_analyzed(self, violations_found: int, total_checks: int):
        """Record analysis of a file"""
        self.current_session_data['files_analyzed'] += 1
        self.current_session_data['units_processed'] += 1
        self.current_session_data['opportunities'] += total_checks

        # File passes if no critical/high violations
        if violations_found == 0 or (
            self.current_session_data['critical_violations'] == 0 and
            self.current_session_data['high_violations'] == 0
        ):
            self.current_session_data['units_passed'] += 1

    def calculate_dpmo(self, defects: int = None, opportunities: int = None) -> float:
        """
        Calculate Defects Per Million Opportunities

        DPMO = (Number of Defects / Number of Opportunities) * 1,000,000
        """
        if defects is None:
            defects = self.current_session_data['defects']
        if opportunities is None:
            opportunities = self.current_session_data['opportunities']

        if opportunities == 0:
            return 0.0

        dpmo = (defects / opportunities) * 1_000_000
        return round(dpmo, 2)

    def calculate_rty(self, units_processed: int = None, units_passed: int = None) -> float:
        """
        Calculate Rolled Throughput Yield

        RTY = (Units Passed First Time / Total Units Processed) * 100
        """
        if units_processed is None:
            units_processed = self.current_session_data['units_processed']
        if units_passed is None:
            units_passed = self.current_session_data['units_passed']

        if units_processed == 0:
            return 100.0

        rty = (units_passed / units_processed) * 100
        return round(rty, 2)

    def calculate_sigma_level(self, dpmo: float = None) -> float:
        """
        Calculate sigma level from DPMO

        Uses approximation based on standard DPMO-to-sigma conversion
        """
        if dpmo is None:
            dpmo = self.calculate_dpmo()

        if dpmo == 0:
            return 6.0  # Perfect quality

        # Standard DPMO to Sigma conversion
        if dpmo <= 3.4:
            return 6.0
        elif dpmo <= 233:
            return 5.0 + (233 - dpmo) / 229.6  # Interpolate
        elif dpmo <= 6210:
            return 4.0 + (6210 - dpmo) / 5977  # Interpolate
        elif dpmo <= 66807:
            return 3.0 + (66807 - dpmo) / 60597  # Interpolate
        elif dpmo <= 308537:
            return 2.0 + (308537 - dpmo) / 241730  # Interpolate
        elif dpmo <= 691462:
            return 1.0 + (691462 - dpmo) / 382925  # Interpolate
        else:
            return 1.0

    def get_quality_level(self, dpmo: float = None) -> QualityLevel:
        """Determine quality level based on DPMO"""
        if dpmo is None:
            dpmo = self.calculate_dpmo()

        for level, threshold in sorted(self.QUALITY_THRESHOLDS.items(),
                                     key=lambda x: x[1]):
            if dpmo <= threshold:
                return level

        return QualityLevel.ONE_SIGMA  # Default to lowest level

    def calculate_process_capability(self, measurements: List[float],
                                   lower_spec: float, upper_spec: float) -> Tuple[float, float]:
        """
        Calculate process capability indices (Cp, Cpk)

        Cp = (USL - LSL) / (6 * sigma)
        Cpk = min((USL - mean) / (3 * sigma), (mean - LSL) / (3 * sigma))
        """
        if not measurements or len(measurements) < 2:
            return 0.0, 0.0

        mean_val = statistics.mean(measurements)
        std_dev = statistics.stdev(measurements)

        if std_dev == 0:
            return float('inf'), float('inf')

        # Cp - Process Capability
        cp = (upper_spec - lower_spec) / (6 * std_dev)

        # Cpk - Process Capability Index
        cpk_upper = (upper_spec - mean_val) / (3 * std_dev)
        cpk_lower = (mean_val - lower_spec) / (3 * std_dev)
        cpk = min(cpk_upper, cpk_lower)

        return round(cp, 3), round(cpk, 3)

    def generate_metrics_snapshot(self) -> SixSigmaMetrics:
        """Generate current metrics snapshot"""
        dpmo = self.calculate_dpmo()
        rty = self.calculate_rty()
        sigma_level = self.calculate_sigma_level(dpmo)
        quality_level = self.get_quality_level(dpmo)

        # Calculate process capability if we have files analyzed
        process_capability = 0.0
        if self.current_session_data['files_analyzed'] > 0:
            # Use violation rate as process measurement
            violation_rate = self.current_session_data['defects'] / self.current_session_data['files_analyzed']
            # Target: 0 violations per file, acceptable: 5 violations per file
            cp, cpk = self.calculate_process_capability([violation_rate], 0, 5)
            process_capability = cpk

        metrics = SixSigmaMetrics(
            dpmo=dpmo,
            rty=rty,
            sigma_level=sigma_level,
            process_capability=process_capability,
            quality_level=quality_level,
            process_name=self.process_name,
            sample_size=self.current_session_data['units_processed'],
            defect_count=self.current_session_data['defects'],
            opportunity_count=self.current_session_data['opportunities'],
            connascence_metrics=dict(self.current_session_data['connascence_violations'])
        )

        self.metrics_history.append(metrics)
        return metrics

    def reset_session(self):
        """Reset current session data"""
        self.current_session_data = {
            'defects': 0,
            'opportunities': 0,
            'units_processed': 0,
            'units_passed': 0,
            'start_time': time.time(),
            'connascence_violations': {},
            'files_analyzed': 0,
            'critical_violations': 0,
            'high_violations': 0,
            'medium_violations': 0,
            'low_violations': 0
        }

    def get_trend_analysis(self, days: int = 30) -> Dict[str, Any]:
        """Analyze quality trends over specified period"""
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_metrics = [m for m in self.metrics_history
                         if m.timestamp >= cutoff_date]

        if not recent_metrics:
            return {"error": "No metrics data available for trend analysis"}

        dpmo_values = [m.dpmo for m in recent_metrics]
        rty_values = [m.rty for m in recent_metrics]
        sigma_values = [m.sigma_level for m in recent_metrics]

        # Analyze connascence type trends
        connascence_trends = {}
        for metric in recent_metrics:
            for conn_type, count in metric.connascence_metrics.items():
                if conn_type not in connascence_trends:
                    connascence_trends[conn_type] = []
                connascence_trends[conn_type].append(count)

        return {
            "period_days": days,
            "sample_count": len(recent_metrics),
            "dpmo": {
                "current": dpmo_values[-1] if dpmo_values else 0,
                "average": round(statistics.mean(dpmo_values), 2) if dpmo_values else 0,
                "trend": "improving" if dpmo_values and dpmo_values[-1] < dpmo_values[0] else "declining",
                "best": min(dpmo_values) if dpmo_values else 0,
                "worst": max(dpmo_values) if dpmo_values else 0
            },
            "rty": {
                "current": rty_values[-1] if rty_values else 100,
                "average": round(statistics.mean(rty_values), 2) if rty_values else 100,
                "trend": "improving" if rty_values and rty_values[-1] > rty_values[0] else "declining",
                "best": max(rty_values) if rty_values else 100,
                "worst": min(rty_values) if rty_values else 100
            },
            "sigma_level": {
                "current": sigma_values[-1] if sigma_values else 6.0,
                "average": round(statistics.mean(sigma_values), 2) if sigma_values else 6.0,
                "trend": "improving" if sigma_values and sigma_values[-1] > sigma_values[0] else "declining",
                "best": max(sigma_values) if sigma_values else 6.0,
                "worst": min(sigma_values) if sigma_values else 6.0
            },
            "connascence_trends": {
                conn_type: {
                    "total": sum(counts),
                    "average": round(statistics.mean(counts), 2),
                    "trend": "increasing" if counts[-1] > counts[0] else "decreasing"
                }
                for conn_type, counts in connascence_trends.items()
            }
        }

    def export_metrics(self) -> Dict[str, Any]:
        """Export all metrics data"""
        return {
            "process_name": self.process_name,
            "current_session": self.current_session_data,
            "metrics_history": [m.to_dict() for m in self.metrics_history],
            "summary": {
                "total_sessions": len(self.metrics_history),
                "average_dpmo": round(statistics.mean([m.dpmo for m in self.metrics_history]), 2) if self.metrics_history else 0,
                "average_sigma": round(statistics.mean([m.sigma_level for m in self.metrics_history]), 2) if self.metrics_history else 6.0,
                "best_sigma": max([m.sigma_level for m in self.metrics_history]) if self.metrics_history else 6.0
            }
        }

    def save_metrics(self, filepath: Path):
        """Save metrics to file"""
        with open(filepath, 'w') as f:
            json.dump(self.export_metrics(), f, indent=2, default=str)

    def load_metrics(self, filepath: Path):
        """Load metrics from file"""
        with open(filepath, 'r') as f:
            data = json.load(f)
            # Restore metrics history
            for metric_data in data.get('metrics_history', []):
                metric = SixSigmaMetrics(
                    dpmo=metric_data['dpmo'],
                    rty=metric_data['rty'],
                    sigma_level=metric_data['sigma_level'],
                    process_capability=metric_data['process_capability'],
                    quality_level=QualityLevel[metric_data['quality_level']] if metric_data['quality_level'] else None,
                    timestamp=datetime.fromisoformat(metric_data['timestamp']),
                    process_name=metric_data['process_name'],
                    sample_size=metric_data['sample_size'],
                    defect_count=metric_data['defect_count'],
                    opportunity_count=metric_data['opportunity_count'],
                    connascence_metrics=metric_data.get('connascence_metrics', {})
                )
                self.metrics_history.append(metric)