#!/usr/bin/env python3
"""
Drift Tracking and Time-Series Analysis System
=============================================

Provides enterprise-grade drift tracking for connascence violations including:
- Time-series violation tracking with historical analysis
- Trend detection and forecasting
- Regression analysis and anomaly detection
- Performance benchmarking and comparative analysis
- Integration with baseline and waiver systems

Author: Connascence Safety Analyzer Team
"""

import json
import statistics
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import logging

@dataclass
class DriftMetric:
    """Individual drift measurement."""
    timestamp: str
    total_violations: int
    violations_by_type: Dict[str, int]
    violations_by_severity: Dict[str, int]
    files_analyzed: int
    analysis_duration_ms: float
    commit_hash: Optional[str] = None
    branch: str = "main"
    author: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class TrendAnalysis:
    """Trend analysis results."""
    trend_direction: str  # "improving", "degrading", "stable"
    trend_strength: float  # 0.0 to 1.0
    rate_of_change: float  # violations per day
    confidence_score: float  # 0.0 to 1.0
    forecast_7d: int  # predicted violations in 7 days
    forecast_30d: int  # predicted violations in 30 days
    analysis_period_days: int

@dataclass
class AnomalyDetection:
    """Anomaly detection results."""
    is_anomaly: bool
    anomaly_score: float  # 0.0 to 1.0
    baseline_mean: float
    baseline_stddev: float
    current_z_score: float
    threshold_exceeded: bool

class DriftSeverity(Enum):
    """Drift severity levels."""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class EnhancedDriftTracker:
    """Enterprise-grade drift tracking system."""
    
    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
        self.drift_file = self.project_root / ".connascence" / "drift.json"
        self.logger = logging.getLogger(__name__)
        
        # Ensure directories exist
        self.drift_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing drift data
        self.drift_history: List[DriftMetric] = self._load_drift_history()
    
    def _load_drift_history(self) -> List[DriftMetric]:
        """Load drift history from JSON file."""
        if not self.drift_file.exists():
            self._create_default_drift_file()
            return []
        
        try:
            with open(self.drift_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not data or 'drift_history' not in data:
                return []
            
            history = []
            for metric_data in data['drift_history']:
                history.append(DriftMetric(**metric_data))
            
            return history
            
        except Exception as e:
            self.logger.error(f"Failed to load drift history: {e}")
            return []
    
    def _save_drift_history(self) -> bool:
        """Save drift history to JSON file."""
        try:
            # Convert to serializable format
            drift_data = [asdict(metric) for metric in self.drift_history]
            
            config = {
                'version': '1.0',
                'updated_at': datetime.now().isoformat(),
                'total_measurements': len(self.drift_history),
                'drift_history': drift_data
            }
            
            with open(self.drift_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save drift history: {e}")
            return False
    
    def _create_default_drift_file(self):
        """Create default drift.json configuration."""
        default_config = {
            'version': '1.0',
            'description': 'Connascence Safety Analyzer - Drift Tracking Configuration',
            'created_at': datetime.now().isoformat(),
            'total_measurements': 0,
            'drift_history': []
        }
        
        try:
            with open(self.drift_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to create default drift config: {e}")
    
    def record_measurement(self, 
                          violations: List[Any],
                          files_analyzed: int,
                          analysis_duration_ms: float,
                          commit_hash: Optional[str] = None,
                          branch: str = "main",
                          author: Optional[str] = None,
                          metadata: Optional[Dict[str, Any]] = None) -> DriftMetric:
        """Record a new drift measurement."""
        
        # Count violations by type and severity
        violations_by_type = {}
        violations_by_severity = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        
        for violation in violations:
            # Count by type
            violation_type = getattr(violation, 'connascence_type', 
                                   getattr(violation, 'type', 'unknown'))
            violations_by_type[violation_type] = violations_by_type.get(violation_type, 0) + 1
            
            # Count by severity
            severity = str(getattr(violation, 'severity', 'medium')).lower()
            if severity in violations_by_severity:
                violations_by_severity[severity] += 1
        
        # Create drift metric
        metric = DriftMetric(
            timestamp=datetime.now().isoformat(),
            total_violations=len(violations),
            violations_by_type=violations_by_type,
            violations_by_severity=violations_by_severity,
            files_analyzed=files_analyzed,
            analysis_duration_ms=analysis_duration_ms,
            commit_hash=commit_hash,
            branch=branch,
            author=author,
            metadata=metadata or {}
        )
        
        # Add to history
        self.drift_history.append(metric)
        
        # Keep only last 1000 measurements to prevent unbounded growth
        if len(self.drift_history) > 1000:
            self.drift_history = self.drift_history[-1000:]
        
        # Save to file
        self._save_drift_history()
        
        return metric
    
    def analyze_trend(self, days: int = 30) -> TrendAnalysis:
        """Analyze trend over specified number of days."""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Filter recent measurements
        recent_metrics = [
            m for m in self.drift_history 
            if datetime.fromisoformat(m.timestamp) >= cutoff_date
        ]
        
        if len(recent_metrics) < 2:
            return TrendAnalysis(
                trend_direction="stable",
                trend_strength=0.0,
                rate_of_change=0.0,
                confidence_score=0.0,
                forecast_7d=0,
                forecast_30d=0,
                analysis_period_days=days
            )
        
        # Extract violation counts and timestamps
        violation_counts = [m.total_violations for m in recent_metrics]
        timestamps = [datetime.fromisoformat(m.timestamp) for m in recent_metrics]
        
        # Calculate linear regression slope
        n = len(violation_counts)
        x_values = [(ts - timestamps[0]).days for ts in timestamps]
        y_values = violation_counts
        
        # Simple linear regression
        x_mean = statistics.mean(x_values)
        y_mean = statistics.mean(y_values)
        
        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, y_values))
        denominator = sum((x - x_mean) ** 2 for x in x_values)
        
        if denominator == 0:
            slope = 0
        else:
            slope = numerator / denominator
        
        # Determine trend direction and strength
        rate_of_change = slope  # violations per day
        
        if abs(slope) < 0.1:
            trend_direction = "stable"
            trend_strength = 0.0
        elif slope > 0:
            trend_direction = "degrading"
            trend_strength = min(abs(slope) / 10.0, 1.0)  # Normalize to 0-1
        else:
            trend_direction = "improving" 
            trend_strength = min(abs(slope) / 10.0, 1.0)
        
        # Calculate confidence score based on data points and variance
        confidence_score = min(n / 30.0, 1.0)  # More data points = higher confidence
        
        if len(violation_counts) > 1:
            variance = statistics.variance(violation_counts)
            if variance > 0:
                cv = statistics.stdev(violation_counts) / statistics.mean(violation_counts)
                confidence_score *= max(0.1, 1.0 - min(cv, 1.0))
        
        # Forecast based on trend
        intercept = y_mean - slope * x_mean
        forecast_7d = max(0, int(intercept + slope * (days + 7)))
        forecast_30d = max(0, int(intercept + slope * (days + 30)))
        
        return TrendAnalysis(
            trend_direction=trend_direction,
            trend_strength=trend_strength,
            rate_of_change=rate_of_change,
            confidence_score=confidence_score,
            forecast_7d=forecast_7d,
            forecast_30d=forecast_30d,
            analysis_period_days=days
        )
    
    def detect_anomalies(self, current_violations: int, lookback_days: int = 30) -> AnomalyDetection:
        """Detect anomalies in current violation count."""
        cutoff_date = datetime.now() - timedelta(days=lookback_days)
        
        # Get baseline measurements
        baseline_metrics = [
            m for m in self.drift_history 
            if datetime.fromisoformat(m.timestamp) >= cutoff_date
        ]
        
        if len(baseline_metrics) < 5:
            return AnomalyDetection(
                is_anomaly=False,
                anomaly_score=0.0,
                baseline_mean=0.0,
                baseline_stddev=0.0,
                current_z_score=0.0,
                threshold_exceeded=False
            )
        
        # Calculate baseline statistics
        baseline_counts = [m.total_violations for m in baseline_metrics]
        baseline_mean = statistics.mean(baseline_counts)
        baseline_stddev = statistics.stdev(baseline_counts) if len(baseline_counts) > 1 else 0.0
        
        # Calculate z-score for current measurement
        if baseline_stddev == 0:
            current_z_score = 0.0
        else:
            current_z_score = (current_violations - baseline_mean) / baseline_stddev
        
        # Anomaly detection thresholds
        threshold_z = 2.5  # 2.5 standard deviations
        is_anomaly = abs(current_z_score) > threshold_z
        anomaly_score = min(abs(current_z_score) / threshold_z, 1.0)
        
        return AnomalyDetection(
            is_anomaly=is_anomaly,
            anomaly_score=anomaly_score,
            baseline_mean=baseline_mean,
            baseline_stddev=baseline_stddev,
            current_z_score=current_z_score,
            threshold_exceeded=is_anomaly
        )
    
    def get_drift_severity(self, trend_analysis: TrendAnalysis) -> DriftSeverity:
        """Determine drift severity based on trend analysis."""
        if trend_analysis.trend_direction == "stable":
            return DriftSeverity.NONE
        
        if trend_analysis.trend_direction == "improving":
            return DriftSeverity.LOW  # Improvement is still tracked but low severity
        
        # Degrading trend - assess severity
        rate = abs(trend_analysis.rate_of_change)
        strength = trend_analysis.trend_strength
        
        if rate > 5.0 and strength > 0.8:
            return DriftSeverity.CRITICAL
        elif rate > 2.0 and strength > 0.6:
            return DriftSeverity.HIGH
        elif rate > 1.0 and strength > 0.4:
            return DriftSeverity.MEDIUM
        else:
            return DriftSeverity.LOW
    
    def get_comparative_analysis(self, branch_a: str = "main", branch_b: str = "develop") -> Dict[str, Any]:
        """Compare drift between two branches."""
        branch_a_metrics = [m for m in self.drift_history if m.branch == branch_a]
        branch_b_metrics = [m for m in self.drift_history if m.branch == branch_b]
        
        if not branch_a_metrics or not branch_b_metrics:
            return {
                'comparison_available': False,
                'error': f'Insufficient data for branches: {branch_a}, {branch_b}'
            }
        
        # Get recent metrics (last 7 days)
        recent_cutoff = datetime.now() - timedelta(days=7)
        recent_a = [m for m in branch_a_metrics 
                   if datetime.fromisoformat(m.timestamp) >= recent_cutoff]
        recent_b = [m for m in branch_b_metrics 
                   if datetime.fromisoformat(m.timestamp) >= recent_cutoff]
        
        if not recent_a or not recent_b:
            return {
                'comparison_available': False,
                'error': 'No recent measurements for comparison'
            }
        
        # Calculate averages
        avg_violations_a = statistics.mean([m.total_violations for m in recent_a])
        avg_violations_b = statistics.mean([m.total_violations for m in recent_b])
        
        # Determine which branch is performing better
        difference = avg_violations_b - avg_violations_a
        percentage_diff = (difference / avg_violations_a * 100) if avg_violations_a > 0 else 0
        
        return {
            'comparison_available': True,
            'branch_a': {
                'name': branch_a,
                'avg_violations': avg_violations_a,
                'measurement_count': len(recent_a)
            },
            'branch_b': {
                'name': branch_b,
                'avg_violations': avg_violations_b,
                'measurement_count': len(recent_b)
            },
            'difference': difference,
            'percentage_difference': percentage_diff,
            'better_performing_branch': branch_a if difference > 0 else branch_b,
            'analysis_period': '7 days'
        }
    
    def get_performance_benchmarks(self) -> Dict[str, Any]:
        """Get performance benchmarks from historical data."""
        if not self.drift_history:
            return {'benchmarks_available': False}
        
        # Calculate various benchmarks
        all_violations = [m.total_violations for m in self.drift_history]
        all_durations = [m.analysis_duration_ms for m in self.drift_history]
        all_files = [m.files_analyzed for m in self.drift_history]
        
        benchmarks = {
            'benchmarks_available': True,
            'violation_statistics': {
                'min': min(all_violations),
                'max': max(all_violations),
                'mean': statistics.mean(all_violations),
                'median': statistics.median(all_violations),
                'stdev': statistics.stdev(all_violations) if len(all_violations) > 1 else 0
            },
            'performance_statistics': {
                'min_duration_ms': min(all_durations),
                'max_duration_ms': max(all_durations),
                'avg_duration_ms': statistics.mean(all_durations),
                'median_duration_ms': statistics.median(all_durations)
            },
            'analysis_scope': {
                'min_files': min(all_files),
                'max_files': max(all_files),
                'avg_files': statistics.mean(all_files)
            },
            'measurement_count': len(self.drift_history),
            'date_range': {
                'earliest': self.drift_history[0].timestamp if self.drift_history else None,
                'latest': self.drift_history[-1].timestamp if self.drift_history else None
            }
        }
        
        return benchmarks
    
    def export_drift_report(self, days: int = 30) -> Dict[str, Any]:
        """Export comprehensive drift analysis report."""
        trend = self.analyze_trend(days)
        anomaly = self.detect_anomalies(
            self.drift_history[-1].total_violations if self.drift_history else 0,
            days
        )
        severity = self.get_drift_severity(trend)
        benchmarks = self.get_performance_benchmarks()
        
        return {
            'report_generated_at': datetime.now().isoformat(),
            'analysis_period_days': days,
            'trend_analysis': asdict(trend),
            'anomaly_detection': asdict(anomaly),
            'drift_severity': severity.value,
            'performance_benchmarks': benchmarks,
            'total_measurements': len(self.drift_history),
            'recent_measurements': len([
                m for m in self.drift_history 
                if datetime.fromisoformat(m.timestamp) >= datetime.now() - timedelta(days=days)
            ])
        }
    
    def cleanup_old_measurements(self, keep_days: int = 90) -> int:
        """Remove measurements older than specified days."""
        cutoff_date = datetime.now() - timedelta(days=keep_days)
        
        initial_count = len(self.drift_history)
        self.drift_history = [
            m for m in self.drift_history 
            if datetime.fromisoformat(m.timestamp) >= cutoff_date
        ]
        
        cleaned_count = initial_count - len(self.drift_history)
        if cleaned_count > 0:
            self._save_drift_history()
        
        return cleaned_count