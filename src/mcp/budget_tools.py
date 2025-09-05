#!/usr/bin/env python3
"""
Budget Enforcement Tools for MCP Server
=======================================

Provides comprehensive budget enforcement tools for the MCP server including:
- Baseline-aware budget tracking and validation
- Multi-mode budget enforcement (strict, baseline, trending, advisory)
- Integration with waiver and drift tracking systems
- CI/CD budget validation and reporting
- Real-time budget monitoring and alerting

Author: Connascence Safety Analyzer Team
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from policy.budgets import EnhancedBudgetTracker, BudgetConfiguration, BudgetMode


class BudgetToolsManager:
    """MCP tools for comprehensive budget enforcement and monitoring."""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.project_root = Path(config.get('project_root', '.'))
        
        # Initialize budget configuration
        budget_config = BudgetConfiguration(
            mode=BudgetMode(config.get('mode', 'baseline')),
            total_violations=config.get('total_violations', 50),
            critical_violations=config.get('critical_violations', 0),
            high_violations=config.get('high_violations', 5),
            medium_violations=config.get('medium_violations', 20),
            new_violations_per_pr=config.get('new_violations_per_pr', 3),
            trend_degradation_rate=config.get('trend_degradation_rate', 1.0),
            waiver_exemptions_enabled=config.get('waiver_exemptions_enabled', True),
            drift_analysis_enabled=config.get('drift_analysis_enabled', True),
            ci_fail_on_budget_exceeded=config.get('ci_fail_on_budget_exceeded', True)
        )
        
        self.budget_tracker = EnhancedBudgetTracker(self.project_root, budget_config)
    
    async def budget_check(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Check current budget compliance with baseline awareness."""
        
        project_path = args.get('project_path', '.')
        mode = args.get('mode')  # Optional mode override
        
        try:
            # Run analysis to get current violations
            from analyzer.ast_engine.core_analyzer import ConnascenceASTAnalyzer
            analyzer = ConnascenceASTAnalyzer()
            analysis_result = analyzer.analyze_directory(Path(project_path))
            
            # Override mode if specified
            original_mode = None
            if mode and mode in ['strict', 'baseline', 'trending', 'advisory']:
                original_mode = self.budget_tracker.config.mode
                self.budget_tracker.config.mode = BudgetMode(mode)
            
            # Check budget compliance
            budget_result = self.budget_tracker.check_baseline_aware_budget(analysis_result.violations)
            
            # Restore original mode
            if original_mode:
                self.budget_tracker.config.mode = original_mode
            
            # Add analysis metadata
            budget_result['analysis_metadata'] = {
                'files_analyzed': analysis_result.total_files_analyzed,
                'analysis_duration_ms': analysis_result.analysis_duration_ms,
                'timestamp': analysis_result.timestamp,
                'project_path': str(project_path)
            }
            
            return {
                'success': True,
                'budget_check': budget_result,
                'message': 'Budget check completed successfully'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to check budget compliance'
            }
    
    async def budget_configure(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Configure budget enforcement settings."""
        
        try:
            # Update configuration
            config_updates = {}
            
            if 'mode' in args:
                mode_value = args['mode']
                if mode_value in ['strict', 'baseline', 'trending', 'advisory']:
                    self.budget_tracker.config.mode = BudgetMode(mode_value)
                    config_updates['mode'] = mode_value
                else:
                    return {
                        'success': False,
                        'error': f'Invalid mode: {mode_value}',
                        'valid_modes': ['strict', 'baseline', 'trending', 'advisory']
                    }
            
            # Update budget limits
            budget_fields = [
                'total_violations', 'critical_violations', 'high_violations', 
                'medium_violations', 'new_violations_per_pr'
            ]
            for field in budget_fields:
                if field in args:
                    setattr(self.budget_tracker.config, field, args[field])
                    config_updates[field] = args[field]
            
            # Update feature flags
            feature_fields = [
                'waiver_exemptions_enabled', 'drift_analysis_enabled', 
                'ci_fail_on_budget_exceeded'
            ]
            for field in feature_fields:
                if field in args:
                    setattr(self.budget_tracker.config, field, args[field])
                    config_updates[field] = args[field]
            
            # Update trend settings
            if 'trend_degradation_rate' in args:
                self.budget_tracker.config.trend_degradation_rate = args['trend_degradation_rate']
                config_updates['trend_degradation_rate'] = args['trend_degradation_rate']
            
            return {
                'success': True,
                'configuration_updated': config_updates,
                'current_configuration': {
                    'mode': self.budget_tracker.config.mode.value,
                    'budgets': {
                        'total_violations': self.budget_tracker.config.total_violations,
                        'critical_violations': self.budget_tracker.config.critical_violations,
                        'high_violations': self.budget_tracker.config.high_violations,
                        'medium_violations': self.budget_tracker.config.medium_violations,
                        'new_violations_per_pr': self.budget_tracker.config.new_violations_per_pr
                    },
                    'features': {
                        'waiver_exemptions_enabled': self.budget_tracker.config.waiver_exemptions_enabled,
                        'drift_analysis_enabled': self.budget_tracker.config.drift_analysis_enabled,
                        'ci_fail_on_budget_exceeded': self.budget_tracker.config.ci_fail_on_budget_exceeded
                    },
                    'trend_degradation_rate': self.budget_tracker.config.trend_degradation_rate
                },
                'message': 'Budget configuration updated successfully'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to configure budget settings'
            }
    
    async def budget_report(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive budget enforcement report."""
        
        project_path = args.get('project_path', '.')
        include_history = args.get('include_history', False)
        format_type = args.get('format', 'json')  # json, summary
        
        try:
            # Run analysis to get current violations
            from analyzer.ast_engine.core_analyzer import ConnascenceASTAnalyzer
            analyzer = ConnascenceASTAnalyzer()
            analysis_result = analyzer.analyze_directory(Path(project_path))
            
            # Generate comprehensive budget report
            budget_report = self.budget_tracker.generate_budget_report(analysis_result.violations)
            
            # Add analysis context
            budget_report['analysis_context'] = {
                'files_analyzed': analysis_result.total_files_analyzed,
                'analysis_duration_ms': analysis_result.analysis_duration_ms,
                'timestamp': analysis_result.timestamp,
                'project_path': str(project_path)
            }
            
            # Add historical context if requested
            if include_history and self.budget_tracker.drift_tracker:
                try:
                    recent_history = self.budget_tracker.drift_tracker.drift_history[-10:]  # Last 10 measurements
                    budget_report['historical_context'] = {
                        'recent_measurements': len(recent_history),
                        'trend_summary': self.budget_tracker.drift_tracker.analyze_trend(days=7)
                    }
                except Exception:
                    budget_report['historical_context'] = {'error': 'Unable to load historical data'}
            
            # Generate human-readable summary if requested
            if format_type == 'summary':
                summary = self._generate_budget_summary(budget_report)
                budget_report['summary'] = summary
            
            return {
                'success': True,
                'format': format_type,
                'budget_report': budget_report,
                'generated_at': datetime.now().isoformat(),
                'message': 'Budget report generated successfully'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to generate budget report'
            }
    
    async def budget_validate_ci(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Validate budget for CI/CD pipeline with exit code recommendation."""
        
        project_path = args.get('project_path', '.')
        pr_mode = args.get('pr_mode', False)  # Special handling for PR validation
        
        try:
            # Run analysis
            from analyzer.ast_engine.core_analyzer import ConnascenceASTAnalyzer
            analyzer = ConnascenceASTAnalyzer()
            analysis_result = analyzer.analyze_directory(Path(project_path))
            
            # Check budget with appropriate mode
            if pr_mode and self.budget_tracker.config.mode != BudgetMode.BASELINE:
                # Force baseline mode for PR validation
                original_mode = self.budget_tracker.config.mode
                self.budget_tracker.config.mode = BudgetMode.BASELINE
                budget_result = self.budget_tracker.check_baseline_aware_budget(analysis_result.violations)
                self.budget_tracker.config.mode = original_mode
            else:
                budget_result = self.budget_tracker.check_baseline_aware_budget(analysis_result.violations)
            
            # Determine CI exit code
            should_fail = budget_result.get('should_fail_ci', False)
            exit_code = 1 if should_fail else 0
            
            # Create CI-friendly summary
            ci_summary = {
                'exit_code': exit_code,
                'budget_compliant': budget_result['compliant'],
                'mode': budget_result['mode'],
                'total_violations': budget_result.get('total_violations', 0),
                'budget_violations_count': len(budget_result.get('budget_violations', [])),
                'waived_violations': budget_result.get('waived_violations', 0)
            }
            
            # Add violation details for CI logs
            if budget_result.get('budget_violations'):
                ci_summary['budget_failures'] = []
                for violation in budget_result['budget_violations']:
                    ci_summary['budget_failures'].append(
                        f"{violation['type']}: {violation['current']} > {violation['limit']} (exceeded by {violation['exceeded_by']})"
                    )
            
            return {
                'success': True,
                'ci_validation': ci_summary,
                'full_budget_report': budget_result,
                'analysis_metadata': {
                    'files_analyzed': analysis_result.total_files_analyzed,
                    'analysis_duration_ms': analysis_result.analysis_duration_ms,
                    'timestamp': analysis_result.timestamp
                },
                'message': f'CI validation completed - Exit code: {exit_code}'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'ci_validation': {'exit_code': 2, 'error': True},  # Error exit code
                'message': 'Failed to validate budget for CI/CD'
            }
    
    async def budget_monitor(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Monitor budget status with alerting thresholds."""
        
        project_path = args.get('project_path', '.')
        alert_thresholds = args.get('alert_thresholds', {
            'budget_utilization': 0.8,  # Alert when 80% of budget used
            'new_violations': 2,        # Alert on 2+ new violations
            'trend_degradation': 0.5    # Alert on degradation rate
        })
        
        try:
            # Run analysis
            from analyzer.ast_engine.core_analyzer import ConnascenceASTAnalyzer
            analyzer = ConnascenceASTAnalyzer()
            analysis_result = analyzer.analyze_directory(Path(project_path))
            
            # Check budget
            budget_result = self.budget_tracker.check_baseline_aware_budget(analysis_result.violations)
            
            # Analyze for alerts
            alerts = []
            
            # Check budget utilization alerts
            for violation in budget_result.get('budget_violations', []):
                utilization = violation['current'] / violation['limit'] if violation['limit'] > 0 else 1.0
                if utilization >= alert_thresholds['budget_utilization']:
                    alerts.append({
                        'type': 'budget_utilization',
                        'severity': 'high' if utilization >= 0.95 else 'medium',
                        'message': f"{violation['type']} at {utilization:.1%} of budget ({violation['current']}/{violation['limit']})",
                        'details': violation
                    })
            
            # Check new violations alert (baseline mode only)
            if budget_result.get('mode') == 'baseline':
                new_count = budget_result.get('new_violations_count', 0)
                if new_count >= alert_thresholds['new_violations']:
                    alerts.append({
                        'type': 'new_violations',
                        'severity': 'high' if new_count >= 5 else 'medium',
                        'message': f"{new_count} new violations detected (threshold: {alert_thresholds['new_violations']})",
                        'details': {'new_violations': new_count}
                    })
            
            # Check trend degradation alert (if drift tracking available)
            if (self.budget_tracker.drift_tracker and 
                budget_result.get('trend_analysis')):
                trend = budget_result['trend_analysis']
                if (trend['direction'] == 'degrading' and 
                    abs(trend['rate_of_change']) >= alert_thresholds['trend_degradation']):
                    alerts.append({
                        'type': 'trend_degradation',
                        'severity': 'high',
                        'message': f"Degrading trend detected: {abs(trend['rate_of_change']):.2f} violations/day",
                        'details': trend
                    })
            
            # Determine overall monitoring status
            alert_levels = [alert['severity'] for alert in alerts]
            if 'high' in alert_levels:
                monitoring_status = 'critical'
            elif 'medium' in alert_levels:
                monitoring_status = 'warning'
            else:
                monitoring_status = 'healthy'
            
            return {
                'success': True,
                'monitoring_status': monitoring_status,
                'alerts': alerts,
                'alert_count': len(alerts),
                'budget_status': budget_result,
                'thresholds': alert_thresholds,
                'timestamp': datetime.now().isoformat(),
                'message': f'Budget monitoring completed - Status: {monitoring_status}'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'monitoring_status': 'error',
                'message': 'Failed to monitor budget status'
            }
    
    def _generate_budget_summary(self, budget_report: Dict[str, Any]) -> str:
        """Generate human-readable budget summary."""
        
        mode = budget_report.get('mode', 'unknown')
        compliant = budget_report.get('compliant', False)
        violations = budget_report.get('budget_violations', [])
        
        summary_lines = [
            f"Budget Enforcement Report - Mode: {mode.upper()}",
            "=" * 50,
            ""
        ]
        
        # Overall status
        status_icon = "✅" if compliant else "❌"
        summary_lines.append(f"{status_icon} Overall Status: {'COMPLIANT' if compliant else 'NON-COMPLIANT'}")
        summary_lines.append("")
        
        # Configuration
        config = budget_report.get('configuration', {})
        if config:
            summary_lines.append("Configuration:")
            budgets = config.get('budgets', {})
            for budget_type, limit in budgets.items():
                summary_lines.append(f"  {budget_type}: {limit}")
            summary_lines.append("")
        
        # Violations
        if violations:
            summary_lines.append("Budget Violations:")
            for violation in violations:
                summary_lines.append(
                    f"  ❌ {violation['type']}: {violation['current']} > {violation['limit']} "
                    f"(exceeded by {violation['exceeded_by']})"
                )
        else:
            summary_lines.append("✅ No budget violations detected")
        
        summary_lines.append("")
        
        # Recommendations
        recommendations = budget_report.get('recommendations', [])
        if recommendations:
            summary_lines.append("Recommendations:")
            for rec in recommendations:
                summary_lines.append(f"  • {rec}")
        
        return "\n".join(summary_lines)


# Tool registry for MCP server integration
BUDGET_TOOLS = {
    'budget_check': {
        'name': 'budget_check',
        'description': 'Check current budget compliance with baseline awareness',
        'inputSchema': {
            'type': 'object',
            'properties': {
                'project_path': {
                    'type': 'string',
                    'description': 'Path to project root'
                },
                'mode': {
                    'type': 'string',
                    'enum': ['strict', 'baseline', 'trending', 'advisory'],
                    'description': 'Budget enforcement mode override'
                }
            }
        }
    },
    
    'budget_configure': {
        'name': 'budget_configure',
        'description': 'Configure budget enforcement settings',
        'inputSchema': {
            'type': 'object',
            'properties': {
                'mode': {
                    'type': 'string',
                    'enum': ['strict', 'baseline', 'trending', 'advisory'],
                    'description': 'Budget enforcement mode'
                },
                'total_violations': {
                    'type': 'integer',
                    'description': 'Maximum total violations allowed'
                },
                'critical_violations': {
                    'type': 'integer',
                    'description': 'Maximum critical violations allowed'
                },
                'high_violations': {
                    'type': 'integer',
                    'description': 'Maximum high severity violations allowed'
                },
                'medium_violations': {
                    'type': 'integer',
                    'description': 'Maximum medium severity violations allowed'
                },
                'new_violations_per_pr': {
                    'type': 'integer',
                    'description': 'Maximum new violations allowed per PR'
                },
                'trend_degradation_rate': {
                    'type': 'number',
                    'description': 'Maximum acceptable degradation rate (violations/day)'
                },
                'waiver_exemptions_enabled': {
                    'type': 'boolean',
                    'description': 'Enable waiver exemptions'
                },
                'drift_analysis_enabled': {
                    'type': 'boolean',
                    'description': 'Enable drift analysis'
                },
                'ci_fail_on_budget_exceeded': {
                    'type': 'boolean',
                    'description': 'Fail CI when budget is exceeded'
                }
            }
        }
    },
    
    'budget_report': {
        'name': 'budget_report',
        'description': 'Generate comprehensive budget enforcement report',
        'inputSchema': {
            'type': 'object',
            'properties': {
                'project_path': {
                    'type': 'string',
                    'description': 'Path to project root'
                },
                'include_history': {
                    'type': 'boolean',
                    'description': 'Include historical trend data'
                },
                'format': {
                    'type': 'string',
                    'enum': ['json', 'summary'],
                    'description': 'Report format'
                }
            }
        }
    },
    
    'budget_validate_ci': {
        'name': 'budget_validate_ci',
        'description': 'Validate budget for CI/CD pipeline with exit code recommendation',
        'inputSchema': {
            'type': 'object',
            'properties': {
                'project_path': {
                    'type': 'string',
                    'description': 'Path to project root'
                },
                'pr_mode': {
                    'type': 'boolean',
                    'description': 'Enable PR validation mode (uses baseline checking)'
                }
            }
        }
    },
    
    'budget_monitor': {
        'name': 'budget_monitor',
        'description': 'Monitor budget status with alerting thresholds',
        'inputSchema': {
            'type': 'object',
            'properties': {
                'project_path': {
                    'type': 'string',
                    'description': 'Path to project root'
                },
                'alert_thresholds': {
                    'type': 'object',
                    'description': 'Alert thresholds configuration',
                    'properties': {
                        'budget_utilization': {
                            'type': 'number',
                            'description': 'Alert threshold for budget utilization (0.0-1.0)'
                        },
                        'new_violations': {
                            'type': 'integer',
                            'description': 'Alert threshold for new violations'
                        },
                        'trend_degradation': {
                            'type': 'number',
                            'description': 'Alert threshold for trend degradation rate'
                        }
                    }
                }
            }
        }
    }
}