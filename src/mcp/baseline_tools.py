#!/usr/bin/env python3
"""
Baseline Management Tools for MCP Server
========================================

Provides comprehensive baseline management tools for the MCP server including:
- Snapshot creation and management
- Baseline comparison and analysis
- Git integration for commit-based snapshots
- Enterprise-grade fingerprinting system

Author: Connascence Safety Analyzer Team
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from policy.baselines import EnhancedBaselineManager, BaselineSnapshot, FindingFingerprint
from analyzer.core import ConnascenceViolation


class BaselineToolsManager:
    """MCP tools for baseline and snapshot management."""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.baseline_manager = EnhancedBaselineManager()
    
    async def snapshot_create(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new baseline snapshot from current codebase analysis."""
        
        # Get parameters
        description = args.get('description', '')
        project_path = args.get('project_path', '.')
        policy_preset = args.get('policy_preset', 'default')
        
        try:
            # Run analysis to get current violations
            from analyzer.ast_engine.core_analyzer import ConnascenceASTAnalyzer
            analyzer = ConnascenceASTAnalyzer()
            analysis_result = analyzer.analyze_directory(Path(project_path))
            
            # Create source lines map for fingerprinting
            source_lines_map = {}
            if hasattr(analysis_result, 'file_stats'):
                for file_path in analysis_result.file_stats.keys():
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            source_lines_map[file_path] = f.read().splitlines()
                    except Exception:
                        pass  # Skip files that can't be read
            
            # Create snapshot
            snapshot = self.baseline_manager.create_snapshot(
                violations=analysis_result.violations,
                description=description,
                source_lines_map=source_lines_map
            )
            
            # Save snapshot
            self.baseline_manager.save_baseline(snapshot)
            
            return {
                'success': True,
                'snapshot_created_at': snapshot.created_at,
                'commit_hash': snapshot.commit_hash,
                'branch': snapshot.branch,
                'description': snapshot.description,
                'total_violations': len(snapshot.fingerprints),
                'baseline_file': str(self.baseline_manager.baseline_file),
                'metadata': snapshot.metadata
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to create baseline snapshot'
            }
    
    async def snapshot_list(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """List available baseline snapshots."""
        
        try:
            baseline_info = self.baseline_manager.get_baseline_info()
            history = self.baseline_manager.list_baseline_history()
            
            if baseline_info['status'] == 'no_baseline':
                return {
                    'success': True,
                    'snapshots': [],
                    'message': 'No baseline snapshots found. Create one with snapshot_create.'
                }
            
            return {
                'success': True,
                'current_baseline': baseline_info,
                'snapshots': history,
                'total_snapshots': len(history)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to list baseline snapshots'
            }
    
    async def snapshot_apply(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Apply a specific baseline snapshot (for future multi-snapshot support)."""
        
        # For now, we only support one snapshot at a time
        # In future versions, this could restore from git history
        
        try:
            baseline_info = self.baseline_manager.get_baseline_info()
            
            if baseline_info['status'] == 'no_baseline':
                return {
                    'success': False,
                    'error': 'No baseline snapshot available to apply',
                    'message': 'Create a baseline first with snapshot_create'
                }
            
            return {
                'success': True,
                'applied_snapshot': baseline_info,
                'message': f'Baseline snapshot from {baseline_info["created_at"]} is currently active'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to apply baseline snapshot'
            }
    
    async def compare_scans(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Compare current scan results with baseline."""
        
        project_path = args.get('project_path', '.')
        include_details = args.get('include_details', False)
        
        try:
            # Run current analysis
            from analyzer.ast_engine.core_analyzer import ConnascenceASTAnalyzer
            analyzer = ConnascenceASTAnalyzer()
            analysis_result = analyzer.analyze_directory(Path(project_path))
            
            # Create source lines map for fingerprinting
            source_lines_map = {}
            for file_path in analysis_result.file_stats.keys():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        source_lines_map[file_path] = f.read().splitlines()
                except Exception:
                    pass
            
            # Compare with baseline
            comparison = self.baseline_manager.compare_with_baseline(
                current_violations=analysis_result.violations,
                source_lines_map=source_lines_map
            )
            
            result = {
                'success': True,
                'comparison': comparison,
                'analysis_metadata': {
                    'files_analyzed': analysis_result.total_files_analyzed,
                    'analysis_duration_ms': analysis_result.analysis_duration_ms,
                    'timestamp': analysis_result.timestamp
                }
            }
            
            # Add detailed violation information if requested
            if include_details and comparison['status'] == 'compared':
                # Filter to new violations only for detailed reporting
                new_violations_only = self.baseline_manager.filter_new_violations_only(
                    violations=analysis_result.violations,
                    source_lines_map=source_lines_map
                )
                
                result['new_violations_only'] = [
                    self._violation_to_dict(v) for v in new_violations_only
                ]
                result['should_fail_ci'] = len(new_violations_only) > 0
                
                # Calculate budget impact
                high_severity_new = [v for v in new_violations_only 
                                   if str(getattr(v, 'severity', 'medium')).lower() in ['high', 'critical']]
                result['budget_impact'] = {
                    'new_high_severity': len(high_severity_new),
                    'total_new': len(new_violations_only),
                    'budget_exceeded': len(high_severity_new) > 0  # Configurable threshold
                }
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to compare scans with baseline'
            }
    
    async def budgets_status(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Check budget status against baseline."""
        
        project_path = args.get('project_path', '.')
        budget_config = args.get('budget_config', {})
        
        # Default budget configuration
        default_budgets = {
            'total_violations': budget_config.get('total_violations', 50),
            'critical_violations': budget_config.get('critical_violations', 0),
            'high_violations': budget_config.get('high_violations', 5),
            'new_violations_per_pr': budget_config.get('new_violations_per_pr', 3)
        }
        
        try:
            # Run analysis and compare
            from analyzer.ast_engine.core_analyzer import ConnascenceASTAnalyzer
            analyzer = ConnascenceASTAnalyzer()
            analysis_result = analyzer.analyze_directory(Path(project_path))
            
            # Get baseline comparison
            source_lines_map = {}
            comparison = self.baseline_manager.compare_with_baseline(
                current_violations=analysis_result.violations,
                source_lines_map=source_lines_map
            )
            
            # Calculate budget status
            if comparison['status'] == 'no_baseline':
                # No baseline = all violations count as new
                total_violations = len(analysis_result.violations)
                new_violations = len(analysis_result.violations)
                severity_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
                
                for v in analysis_result.violations:
                    severity = str(getattr(v, 'severity', 'medium')).lower()
                    if severity in severity_counts:
                        severity_counts[severity] += 1
                
            else:
                # Use baseline comparison
                total_violations = comparison['total_current']
                new_violations = comparison['new_violations']
                
                # Count new violations by severity
                new_violation_details = comparison.get('new_violation_details', [])
                severity_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
                
                for v_detail in new_violation_details:
                    severity = v_detail.get('severity', 'medium').lower()
                    if severity in severity_counts:
                        severity_counts[severity] += 1
            
            # Check against budgets
            budget_status = {
                'total_violations': {
                    'current': total_violations,
                    'budget': default_budgets['total_violations'],
                    'over_budget': total_violations > default_budgets['total_violations']
                },
                'critical_violations': {
                    'current': severity_counts['critical'],
                    'budget': default_budgets['critical_violations'],
                    'over_budget': severity_counts['critical'] > default_budgets['critical_violations']
                },
                'high_violations': {
                    'current': severity_counts['high'],
                    'budget': default_budgets['high_violations'],
                    'over_budget': severity_counts['high'] > default_budgets['high_violations']
                },
                'new_violations': {
                    'current': new_violations,
                    'budget': default_budgets['new_violations_per_pr'],
                    'over_budget': new_violations > default_budgets['new_violations_per_pr']
                }
            }
            
            # Overall budget status
            any_over_budget = any(item['over_budget'] for item in budget_status.values())
            
            return {
                'success': True,
                'budget_status': budget_status,
                'overall_status': 'over_budget' if any_over_budget else 'within_budget',
                'should_fail_ci': any_over_budget,
                'comparison_info': comparison,
                'budgets_config': default_budgets
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to check budget status'
            }
    
    async def baseline_info(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get comprehensive information about the current baseline."""
        
        try:
            baseline_info = self.baseline_manager.get_baseline_info()
            
            # Add file system information
            baseline_file = self.baseline_manager.baseline_file
            
            result = {
                'success': True,
                'baseline_info': baseline_info,
                'file_info': {
                    'path': str(baseline_file),
                    'exists': baseline_file.exists(),
                    'size_bytes': baseline_file.stat().st_size if baseline_file.exists() else 0,
                    'directory': str(baseline_file.parent)
                }
            }
            
            # Add git repository info
            if baseline_info.get('commit_hash'):
                result['git_info'] = {
                    'commit_hash': baseline_info['commit_hash'],
                    'branch': baseline_info.get('branch'),
                    'repository_root': str(self.baseline_manager.baseline_dir)
                }
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to get baseline information'
            }
    
    def _violation_to_dict(self, violation: ConnascenceViolation) -> Dict[str, Any]:
        """Convert violation object to dictionary for JSON serialization."""
        return {
            'id': getattr(violation, 'id', ''),
            'type': getattr(violation, 'connascence_type', getattr(violation, 'type', 'unknown')),
            'severity': str(getattr(violation, 'severity', 'medium')),
            'file_path': getattr(violation, 'file_path', ''),
            'line_number': getattr(violation, 'line_number', 0),
            'column': getattr(violation, 'column', 0),
            'description': getattr(violation, 'description', ''),
            'recommendation': getattr(violation, 'recommendation', ''),
            'weight': getattr(violation, 'weight', 1.0)
        }


# Tool registry for MCP server integration
BASELINE_TOOLS = {
    'snapshot_create': {
        'name': 'snapshot_create',
        'description': 'Create a new baseline snapshot from current codebase',
        'inputSchema': {
            'type': 'object',
            'properties': {
                'description': {
                    'type': 'string',
                    'description': 'Description for this snapshot'
                },
                'project_path': {
                    'type': 'string', 
                    'description': 'Path to project root (default: current directory)'
                },
                'policy_preset': {
                    'type': 'string',
                    'description': 'Policy preset to use for analysis'
                }
            }
        }
    },
    
    'snapshot_list': {
        'name': 'snapshot_list',
        'description': 'List available baseline snapshots',
        'inputSchema': {
            'type': 'object',
            'properties': {}
        }
    },
    
    'snapshot_apply': {
        'name': 'snapshot_apply', 
        'description': 'Apply a specific baseline snapshot',
        'inputSchema': {
            'type': 'object',
            'properties': {
                'snapshot_id': {
                    'type': 'string',
                    'description': 'ID of snapshot to apply (future use)'
                }
            }
        }
    },
    
    'compare_scans': {
        'name': 'compare_scans',
        'description': 'Compare current scan results with baseline',
        'inputSchema': {
            'type': 'object',
            'properties': {
                'project_path': {
                    'type': 'string',
                    'description': 'Path to project root'
                },
                'include_details': {
                    'type': 'boolean',
                    'description': 'Include detailed violation information'
                }
            }
        }
    },
    
    'budgets_status': {
        'name': 'budgets_status',
        'description': 'Check budget status against baseline',
        'inputSchema': {
            'type': 'object',
            'properties': {
                'project_path': {
                    'type': 'string',
                    'description': 'Path to project root'
                },
                'budget_config': {
                    'type': 'object',
                    'description': 'Budget configuration overrides'
                }
            }
        }
    },
    
    'baseline_info': {
        'name': 'baseline_info',
        'description': 'Get comprehensive baseline information',
        'inputSchema': {
            'type': 'object',
            'properties': {}
        }
    }
}