#!/usr/bin/env python3
"""
Drift Tracking Tools for MCP Server
===================================

Provides comprehensive drift tracking tools for the MCP server including:
- Time-series violation tracking and analysis
- Trend detection and forecasting
- Anomaly detection and alerting
- Performance benchmarking and comparative analysis
- Integration with baseline and waiver systems

Author: Connascence Safety Analyzer Team
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from policy.drift import EnhancedDriftTracker, DriftSeverity


class DriftToolsManager:
    """MCP tools for comprehensive drift tracking and analysis."""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.project_root = Path(config.get('project_root', '.'))
        self.drift_tracker = EnhancedDriftTracker(self.project_root)
    
    async def drift_record(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Record a new drift measurement from analysis results."""
        
        # Get current analysis results
        project_path = args.get('project_path', '.')
        commit_hash = args.get('commit_hash')
        branch = args.get('branch', 'main')
        author = args.get('author')
        metadata = args.get('metadata', {})
        
        try:
            # Run analysis to get current violations
            from analyzer.ast_engine.core_analyzer import ConnascenceASTAnalyzer
            analyzer = ConnascenceASTAnalyzer()
            analysis_result = analyzer.analyze_directory(Path(project_path))
            
            # Record measurement
            metric = self.drift_tracker.record_measurement(
                violations=analysis_result.violations,
                files_analyzed=analysis_result.total_files_analyzed,
                analysis_duration_ms=analysis_result.analysis_duration_ms,
                commit_hash=commit_hash,
                branch=branch,
                author=author,
                metadata=metadata
            )
            
            return {
                'success': True,
                'measurement_recorded': True,
                'timestamp': metric.timestamp,
                'total_violations': metric.total_violations,
                'violations_by_type': metric.violations_by_type,
                'violations_by_severity': metric.violations_by_severity,
                'files_analyzed': metric.files_analyzed,
                'analysis_duration_ms': metric.analysis_duration_ms,
                'commit_hash': metric.commit_hash,
                'branch': metric.branch,
                'total_measurements': len(self.drift_tracker.drift_history),
                'message': 'Drift measurement recorded successfully'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to record drift measurement'
            }
    
    async def drift_analyze(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze drift trends over specified time period."""
        
        analysis_days = args.get('days', 30)
        
        try:
            # Get trend analysis
            trend = self.drift_tracker.analyze_trend(days=analysis_days)
            
            # Get drift severity
            severity = self.drift_tracker.get_drift_severity(trend)
            
            # Get recent measurements for context
            recent_count = len([
                m for m in self.drift_tracker.drift_history
                if (datetime.now() - datetime.fromisoformat(m.timestamp)).days <= analysis_days
            ])
            
            return {
                'success': True,
                'analysis_period_days': analysis_days,
                'trend_analysis': {
                    'trend_direction': trend.trend_direction,
                    'trend_strength': trend.trend_strength,
                    'rate_of_change': trend.rate_of_change,
                    'confidence_score': trend.confidence_score,
                    'forecast_7d': trend.forecast_7d,
                    'forecast_30d': trend.forecast_30d
                },
                'drift_severity': severity.value,
                'recent_measurements': recent_count,
                'total_measurements': len(self.drift_tracker.drift_history),
                'recommendations': self._get_drift_recommendations(trend, severity)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to analyze drift trends'
            }
    
    async def drift_detect_anomalies(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Detect anomalies in current violation patterns."""
        
        project_path = args.get('project_path', '.')
        lookback_days = args.get('lookback_days', 30)
        
        try:
            # Get current violations
            from analyzer.ast_engine.core_analyzer import ConnascenceASTAnalyzer
            analyzer = ConnascenceASTAnalyzer()
            analysis_result = analyzer.analyze_directory(Path(project_path))
            current_violations = len(analysis_result.violations)
            
            # Detect anomalies
            anomaly = self.drift_tracker.detect_anomalies(
                current_violations=current_violations,
                lookback_days=lookback_days
            )
            
            return {
                'success': True,
                'current_violations': current_violations,
                'lookback_period_days': lookback_days,
                'anomaly_detection': {
                    'is_anomaly': anomaly.is_anomaly,
                    'anomaly_score': anomaly.anomaly_score,
                    'baseline_mean': anomaly.baseline_mean,
                    'baseline_stddev': anomaly.baseline_stddev,
                    'current_z_score': anomaly.current_z_score,
                    'threshold_exceeded': anomaly.threshold_exceeded
                },
                'severity': 'high' if anomaly.is_anomaly and anomaly.anomaly_score > 0.8 else 
                          'medium' if anomaly.is_anomaly else 'low',
                'message': 'Anomaly detected in violation pattern' if anomaly.is_anomaly 
                          else 'No anomalies detected'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to detect anomalies'
            }
    
    async def drift_compare_branches(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Compare drift between two branches."""
        
        branch_a = args.get('branch_a', 'main')
        branch_b = args.get('branch_b', 'develop')
        
        try:
            comparison = self.drift_tracker.get_comparative_analysis(branch_a, branch_b)
            
            if not comparison.get('comparison_available'):
                return {
                    'success': False,
                    'comparison_available': False,
                    'error': comparison.get('error', 'Comparison not available'),
                    'message': f'Cannot compare branches {branch_a} and {branch_b}'
                }
            
            return {
                'success': True,
                'comparison_available': True,
                'branch_comparison': comparison,
                'recommendations': self._get_branch_recommendations(comparison)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'Failed to compare branches {branch_a} and {branch_b}'
            }
    
    async def drift_benchmarks(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get performance benchmarks from historical data."""
        
        try:
            benchmarks = self.drift_tracker.get_performance_benchmarks()
            
            if not benchmarks.get('benchmarks_available'):
                return {
                    'success': False,
                    'benchmarks_available': False,
                    'message': 'No historical data available for benchmarking'
                }
            
            return {
                'success': True,
                'benchmarks_available': True,
                'performance_benchmarks': benchmarks,
                'insights': self._get_benchmark_insights(benchmarks)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to get performance benchmarks'
            }
    
    async def drift_cleanup(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Clean up old drift measurements."""
        
        keep_days = args.get('keep_days', 90)
        dry_run = args.get('dry_run', False)
        
        try:
            if dry_run:
                # Calculate what would be cleaned without actually doing it
                cutoff_date = datetime.now() - datetime.timedelta(days=keep_days)
                old_count = len([
                    m for m in self.drift_tracker.drift_history
                    if datetime.fromisoformat(m.timestamp) < cutoff_date
                ])
                
                return {
                    'success': True,
                    'dry_run': True,
                    'would_cleanup_count': old_count,
                    'current_total': len(self.drift_tracker.drift_history),
                    'would_remain': len(self.drift_tracker.drift_history) - old_count,
                    'cutoff_date': cutoff_date.isoformat(),
                    'message': f'Would clean up {old_count} measurements (dry run mode)'
                }
            else:
                cleaned_count = self.drift_tracker.cleanup_old_measurements(keep_days)
                return {
                    'success': True,
                    'dry_run': False,
                    'cleaned_up_count': cleaned_count,
                    'remaining_measurements': len(self.drift_tracker.drift_history),
                    'message': f'Cleaned up {cleaned_count} old measurements'
                }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to cleanup drift measurements'
            }
    
    async def drift_export(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Export comprehensive drift analysis report."""
        
        analysis_days = args.get('days', 30)
        format_type = args.get('format', 'json')  # json, summary
        
        try:
            report = self.drift_tracker.export_drift_report(days=analysis_days)
            
            if format_type == 'summary':
                # Generate human-readable summary
                trend = report['trend_analysis']
                severity = report['drift_severity']
                anomaly = report['anomaly_detection']
                
                summary = f"""
Drift Analysis Report - {analysis_days} days
============================================

Trend Analysis:
- Direction: {trend['trend_direction'].title()}
- Strength: {trend['trend_strength']:.2f} (0.0 = weak, 1.0 = strong)
- Rate of Change: {trend['rate_of_change']:.2f} violations/day
- Confidence: {trend['confidence_score']:.2f} (0.0 = low, 1.0 = high)
- 7-day Forecast: {trend['forecast_7d']} violations
- 30-day Forecast: {trend['forecast_30d']} violations

Drift Severity: {severity.upper()}

Anomaly Detection:
- Current Status: {'ANOMALY DETECTED' if anomaly['is_anomaly'] else 'NORMAL'}
- Anomaly Score: {anomaly['anomaly_score']:.2f}
- Z-Score: {anomaly['current_z_score']:.2f}

Data Quality:
- Total Measurements: {report['total_measurements']}
- Recent Measurements: {report['recent_measurements']}
                """.strip()
                
                report['summary'] = summary
            
            return {
                'success': True,
                'format': format_type,
                'analysis_period_days': analysis_days,
                'report': report,
                'generated_at': report['report_generated_at']
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to export drift report'
            }
    
    async def drift_history(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get drift measurement history with optional filtering."""
        
        days = args.get('days')
        branch = args.get('branch')
        limit = args.get('limit', 50)
        
        try:
            history = list(self.drift_tracker.drift_history)
            
            # Apply filters
            if days:
                cutoff_date = datetime.now() - datetime.timedelta(days=days)
                history = [
                    m for m in history
                    if datetime.fromisoformat(m.timestamp) >= cutoff_date
                ]
            
            if branch:
                history = [m for m in history if m.branch == branch]
            
            # Sort by timestamp (newest first) and limit
            history.sort(key=lambda m: m.timestamp, reverse=True)
            history = history[:limit]
            
            # Convert to serializable format
            history_data = []
            for metric in history:
                history_data.append({
                    'timestamp': metric.timestamp,
                    'total_violations': metric.total_violations,
                    'violations_by_type': metric.violations_by_type,
                    'violations_by_severity': metric.violations_by_severity,
                    'files_analyzed': metric.files_analyzed,
                    'analysis_duration_ms': metric.analysis_duration_ms,
                    'commit_hash': metric.commit_hash,
                    'branch': metric.branch,
                    'author': metric.author,
                    'metadata': metric.metadata
                })
            
            return {
                'success': True,
                'history': history_data,
                'total_count': len(history_data),
                'filters_applied': {
                    'days': days,
                    'branch': branch,
                    'limit': limit
                },
                'total_measurements': len(self.drift_tracker.drift_history)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to get drift history'
            }
    
    def _get_drift_recommendations(self, trend, severity) -> List[str]:
        """Get recommendations based on drift analysis."""
        recommendations = []
        
        if severity == DriftSeverity.CRITICAL:
            recommendations.append("🚨 CRITICAL: Immediate action required - violation count increasing rapidly")
            recommendations.append("Consider implementing emergency refactoring plan")
            recommendations.append("Review recent code changes that may have introduced violations")
        elif severity == DriftSeverity.HIGH:
            recommendations.append("⚠️ HIGH: Schedule refactoring to address increasing violations")
            recommendations.append("Review and update coding standards with team")
        elif severity == DriftSeverity.MEDIUM:
            recommendations.append("📊 MEDIUM: Monitor trend closely and plan preventive measures")
            recommendations.append("Consider code review process improvements")
        elif trend.trend_direction == "improving":
            recommendations.append("✅ IMPROVING: Great work! Continue current practices")
            recommendations.append("Document successful practices for team knowledge sharing")
        else:
            recommendations.append("📈 STABLE: Maintain current code quality practices")
        
        if trend.confidence_score < 0.5:
            recommendations.append("⚠️ Low confidence in trend analysis - collect more data points")
        
        return recommendations
    
    def _get_branch_recommendations(self, comparison) -> List[str]:
        """Get recommendations based on branch comparison."""
        recommendations = []
        
        better_branch = comparison['better_performing_branch']
        worse_branch = comparison['branch_a']['name'] if better_branch == comparison['branch_b']['name'] else comparison['branch_b']['name']
        percentage_diff = abs(comparison['percentage_difference'])
        
        if percentage_diff > 50:
            recommendations.append(f"🚨 SIGNIFICANT DIFFERENCE: {worse_branch} has {percentage_diff:.1f}% more violations than {better_branch}")
            recommendations.append(f"Consider merging improvements from {better_branch} to {worse_branch}")
        elif percentage_diff > 20:
            recommendations.append(f"⚠️ MODERATE DIFFERENCE: {worse_branch} has {percentage_diff:.1f}% more violations than {better_branch}")
            recommendations.append("Review code differences between branches")
        else:
            recommendations.append("✅ Branches have similar violation levels")
        
        return recommendations
    
    def _get_benchmark_insights(self, benchmarks) -> List[str]:
        """Get insights based on performance benchmarks.""" 
        insights = []
        
        violation_stats = benchmarks['violation_statistics']
        performance_stats = benchmarks['performance_statistics']
        
        # Violation insights
        if violation_stats['max'] > violation_stats['mean'] * 3:
            insights.append("📊 High variability in violation counts detected")
        
        cv = violation_stats['stdev'] / violation_stats['mean'] if violation_stats['mean'] > 0 else 0
        if cv > 0.5:
            insights.append("⚠️ Inconsistent code quality across measurements")
        elif cv < 0.2:
            insights.append("✅ Consistent code quality maintained")
        
        # Performance insights
        avg_duration = performance_stats['avg_duration_ms']
        if avg_duration > 10000:  # > 10 seconds
            insights.append("🐌 Analysis performance may need optimization")
        elif avg_duration < 1000:  # < 1 second
            insights.append("⚡ Excellent analysis performance")
        
        return insights


# Tool registry for MCP server integration
DRIFT_TOOLS = {
    'drift_record': {
        'name': 'drift_record',
        'description': 'Record a new drift measurement from current analysis',
        'inputSchema': {
            'type': 'object',
            'properties': {
                'project_path': {
                    'type': 'string',
                    'description': 'Path to project root'
                },
                'commit_hash': {
                    'type': 'string',
                    'description': 'Git commit hash for this measurement'
                },
                'branch': {
                    'type': 'string',
                    'description': 'Git branch name'
                },
                'author': {
                    'type': 'string',
                    'description': 'Commit author'
                },
                'metadata': {
                    'type': 'object',
                    'description': 'Additional metadata for measurement'
                }
            }
        }
    },
    
    'drift_analyze': {
        'name': 'drift_analyze',
        'description': 'Analyze drift trends over specified time period',
        'inputSchema': {
            'type': 'object',
            'properties': {
                'days': {
                    'type': 'integer',
                    'description': 'Number of days to analyze (default: 30)'
                }
            }
        }
    },
    
    'drift_detect_anomalies': {
        'name': 'drift_detect_anomalies',
        'description': 'Detect anomalies in current violation patterns',
        'inputSchema': {
            'type': 'object',
            'properties': {
                'project_path': {
                    'type': 'string',
                    'description': 'Path to project root'
                },
                'lookback_days': {
                    'type': 'integer',
                    'description': 'Days of history to use for baseline (default: 30)'
                }
            }
        }
    },
    
    'drift_compare_branches': {
        'name': 'drift_compare_branches',
        'description': 'Compare drift between two branches',
        'inputSchema': {
            'type': 'object',
            'properties': {
                'branch_a': {
                    'type': 'string',
                    'description': 'First branch to compare (default: main)'
                },
                'branch_b': {
                    'type': 'string',
                    'description': 'Second branch to compare (default: develop)'
                }
            }
        }
    },
    
    'drift_benchmarks': {
        'name': 'drift_benchmarks',
        'description': 'Get performance benchmarks from historical data',
        'inputSchema': {
            'type': 'object',
            'properties': {}
        }
    },
    
    'drift_cleanup': {
        'name': 'drift_cleanup',
        'description': 'Clean up old drift measurements',
        'inputSchema': {
            'type': 'object',
            'properties': {
                'keep_days': {
                    'type': 'integer',
                    'description': 'Number of days of data to keep (default: 90)'
                },
                'dry_run': {
                    'type': 'boolean',
                    'description': 'Preview cleanup without actually removing data'
                }
            }
        }
    },
    
    'drift_export': {
        'name': 'drift_export',
        'description': 'Export comprehensive drift analysis report',
        'inputSchema': {
            'type': 'object',
            'properties': {
                'days': {
                    'type': 'integer',
                    'description': 'Analysis period in days (default: 30)'
                },
                'format': {
                    'type': 'string',
                    'enum': ['json', 'summary'],
                    'description': 'Export format (json for raw data, summary for human-readable)'
                }
            }
        }
    },
    
    'drift_history': {
        'name': 'drift_history',
        'description': 'Get drift measurement history with optional filtering',
        'inputSchema': {
            'type': 'object',
            'properties': {
                'days': {
                    'type': 'integer',
                    'description': 'Number of days of history to retrieve'
                },
                'branch': {
                    'type': 'string',
                    'description': 'Filter by branch name'
                },
                'limit': {
                    'type': 'integer',
                    'description': 'Maximum number of measurements to return (default: 50)'
                }
            }
        }
    }
}