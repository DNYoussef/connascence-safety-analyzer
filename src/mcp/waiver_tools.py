#!/usr/bin/env python3
"""
Waiver Management Tools for MCP Server
======================================

Provides comprehensive waiver management tools for the MCP server including:
- YAML-based waiver creation and management
- Approval workflows and audit logging
- Expiration tracking and cleanup
- Enterprise-grade waiver reporting
- Integration with violation fingerprinting

Author: Connascence Safety Analyzer Team
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from policy.waivers import EnhancedWaiverSystem, WaiverScope, WaiverStatus


class WaiverToolsManager:
    """MCP tools for comprehensive waiver management."""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.project_root = Path(config.get('project_root', '.'))
        self.waiver_system = EnhancedWaiverSystem(self.project_root)
    
    async def waiver_create(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new waiver rule."""
        
        # Required parameters
        scope = args.get('scope', 'finding')  # finding, rule, file, project
        pattern = args.get('pattern', '')
        reason = args.get('reason', '')
        justification = args.get('justification', '')
        
        # Optional parameters
        expires_days = args.get('expires_days')
        created_by = args.get('created_by', 'unknown')
        jira_ticket = args.get('jira_ticket')
        
        if not all([pattern, reason, justification]):
            return {
                'success': False,
                'error': 'Missing required parameters: pattern, reason, justification',
                'message': 'Please provide all required waiver details'
            }
        
        try:
            # Convert scope string to enum
            waiver_scope = WaiverScope(scope)
            
            # Create waiver
            waiver = self.waiver_system.create_waiver(
                scope=waiver_scope,
                pattern=pattern,
                reason=reason,
                justification=justification,
                expires_days=expires_days,
                created_by=created_by,
                jira_ticket=jira_ticket
            )
            
            return {
                'success': True,
                'waiver_id': waiver.id,
                'status': waiver.status.value,
                'expires_at': waiver.expires_at,
                'created_at': waiver.metadata.created_at if waiver.metadata else None,
                'message': f'Waiver created successfully. ID: {waiver.id}'
            }
            
        except ValueError as e:
            return {
                'success': False,
                'error': f'Invalid scope: {scope}',
                'valid_scopes': ['finding', 'rule', 'file', 'project'],
                'message': str(e)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to create waiver'
            }
    
    async def waiver_list(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """List waivers with optional filtering."""
        
        status_filter = args.get('status')  # pending, approved, rejected, expired, all
        scope_filter = args.get('scope')    # finding, rule, file, project
        active_only = args.get('active_only', False)
        
        try:
            waivers = self.waiver_system.waivers
            
            # Apply filters
            if status_filter and status_filter != 'all':
                waivers = [w for w in waivers if w.status.value == status_filter]
            
            if scope_filter:
                waivers = [w for w in waivers if w.scope.value == scope_filter]
            
            if active_only:
                waivers = [w for w in waivers if not w.is_expired() and w.status in [WaiverStatus.APPROVED, WaiverStatus.AUTO_APPROVED]]
            
            # Convert to serializable format
            waiver_list = []
            for w in waivers:
                waiver_data = {
                    'id': w.id,
                    'scope': w.scope.value,
                    'pattern': w.pattern,
                    'reason': w.reason,
                    'justification': w.justification,
                    'status': w.status.value,
                    'expires_at': w.expires_at,
                    'is_expired': w.is_expired(),
                    'created_by': w.metadata.created_by if w.metadata else None,
                    'created_at': w.metadata.created_at if w.metadata else None,
                    'approved_by': w.metadata.approved_by if w.metadata else None,
                    'approved_at': w.metadata.approved_at if w.metadata else None,
                    'jira_ticket': w.metadata.jira_ticket if w.metadata else None
                }
                waiver_list.append(waiver_data)
            
            # Get statistics
            stats = self.waiver_system.get_waiver_statistics()
            
            return {
                'success': True,
                'waivers': waiver_list,
                'total_count': len(waiver_list),
                'statistics': stats,
                'filters_applied': {
                    'status': status_filter,
                    'scope': scope_filter,
                    'active_only': active_only
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to list waivers'
            }
    
    async def waiver_approve(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Approve a pending waiver."""
        
        waiver_id = args.get('waiver_id', '')
        approved_by = args.get('approved_by', 'unknown')
        notes = args.get('notes')
        
        if not waiver_id:
            return {
                'success': False,
                'error': 'Missing required parameter: waiver_id',
                'message': 'Please provide waiver ID to approve'
            }
        
        try:
            success = self.waiver_system.approve_waiver(waiver_id, approved_by, notes)
            
            if success:
                waiver = self.waiver_system.get_waiver_by_id(waiver_id)
                return {
                    'success': True,
                    'waiver_id': waiver_id,
                    'status': waiver.status.value if waiver else 'approved',
                    'approved_by': approved_by,
                    'approved_at': datetime.now().isoformat(),
                    'message': f'Waiver {waiver_id} approved successfully'
                }
            else:
                return {
                    'success': False,
                    'error': f'Waiver {waiver_id} not found',
                    'message': 'Cannot approve non-existent waiver'
                }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'Failed to approve waiver {waiver_id}'
            }
    
    async def waiver_reject(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Reject a pending waiver."""
        
        waiver_id = args.get('waiver_id', '')
        rejected_by = args.get('rejected_by', 'unknown')
        notes = args.get('notes')
        
        if not waiver_id:
            return {
                'success': False,
                'error': 'Missing required parameter: waiver_id',
                'message': 'Please provide waiver ID to reject'
            }
        
        try:
            success = self.waiver_system.reject_waiver(waiver_id, rejected_by, notes)
            
            if success:
                waiver = self.waiver_system.get_waiver_by_id(waiver_id)
                return {
                    'success': True,
                    'waiver_id': waiver_id,
                    'status': waiver.status.value if waiver else 'rejected',
                    'rejected_by': rejected_by,
                    'rejected_at': datetime.now().isoformat(),
                    'message': f'Waiver {waiver_id} rejected successfully'
                }
            else:
                return {
                    'success': False,
                    'error': f'Waiver {waiver_id} not found',
                    'message': 'Cannot reject non-existent waiver'
                }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'Failed to reject waiver {waiver_id}'
            }
    
    async def waiver_check(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Check if a violation is covered by an active waiver."""
        
        violation_fingerprint = args.get('violation_fingerprint', '')
        file_path = args.get('file_path', '')
        rule_type = args.get('rule_type', '')
        
        if not all([violation_fingerprint, file_path, rule_type]):
            return {
                'success': False,
                'error': 'Missing required parameters: violation_fingerprint, file_path, rule_type',
                'message': 'Please provide all violation details'
            }
        
        try:
            waiver = self.waiver_system.is_violation_waived(violation_fingerprint, file_path, rule_type)
            
            if waiver:
                return {
                    'success': True,
                    'is_waived': True,
                    'waiver_id': waiver.id,
                    'waiver_reason': waiver.reason,
                    'waiver_scope': waiver.scope.value,
                    'waiver_pattern': waiver.pattern,
                    'expires_at': waiver.expires_at,
                    'approved_by': waiver.metadata.approved_by if waiver.metadata else None,
                    'message': f'Violation is waived by {waiver.id}'
                }
            else:
                return {
                    'success': True,
                    'is_waived': False,
                    'message': 'Violation is not covered by any active waiver'
                }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to check waiver status'
            }
    
    async def waiver_cleanup(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Clean up expired waivers."""
        
        dry_run = args.get('dry_run', False)
        
        try:
            if dry_run:
                # Just get expired waivers without removing them
                expired = self.waiver_system.get_expired_waivers()
                return {
                    'success': True,
                    'dry_run': True,
                    'expired_count': len(expired),
                    'expired_waivers': [
                        {
                            'id': w.id,
                            'pattern': w.pattern,
                            'expires_at': w.expires_at,
                            'reason': w.reason
                        } for w in expired
                    ],
                    'message': f'Found {len(expired)} expired waivers (dry run mode)'
                }
            else:
                # Actually clean up expired waivers
                cleanup_count = self.waiver_system.cleanup_expired_waivers()
                return {
                    'success': True,
                    'dry_run': False,
                    'cleaned_up_count': cleanup_count,
                    'message': f'Cleaned up {cleanup_count} expired waivers'
                }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to cleanup expired waivers'
            }
    
    async def waiver_statistics(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get comprehensive waiver statistics."""
        
        try:
            stats = self.waiver_system.get_waiver_statistics()
            expired = self.waiver_system.get_expired_waivers()
            
            # Add additional insights
            stats['expired_waivers'] = len(expired)
            stats['waivers_file'] = str(self.waiver_system.waivers_file)
            stats['audit_log'] = str(self.waiver_system.audit_log)
            
            return {
                'success': True,
                'statistics': stats,
                'file_info': {
                    'waivers_file_exists': self.waiver_system.waivers_file.exists(),
                    'audit_log_exists': self.waiver_system.audit_log.exists()
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to get waiver statistics'
            }
    
    async def waiver_export(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Export comprehensive waivers report."""
        
        format_type = args.get('format', 'json')  # json, yaml
        
        try:
            report = self.waiver_system.export_waivers_report()
            
            if format_type == 'yaml':
                import yaml
                report_content = yaml.safe_dump(report, default_flow_style=False, sort_keys=False)
            else:
                report_content = json.dumps(report, indent=2)
            
            return {
                'success': True,
                'format': format_type,
                'report': report,
                'report_content': report_content,
                'generated_at': report['report_generated_at']
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to export waivers report'
            }


# Tool registry for MCP server integration
WAIVER_TOOLS = {
    'waiver_create': {
        'name': 'waiver_create',
        'description': 'Create a new waiver rule for violations',
        'inputSchema': {
            'type': 'object',
            'properties': {
                'scope': {
                    'type': 'string',
                    'enum': ['finding', 'rule', 'file', 'project'],
                    'description': 'Waiver scope (finding-specific, rule-wide, file-wide, or project-wide)'
                },
                'pattern': {
                    'type': 'string',
                    'description': 'Pattern to match (fingerprint, rule name, file pattern, or *)'
                },
                'reason': {
                    'type': 'string',
                    'description': 'Brief reason for waiver'
                },
                'justification': {
                    'type': 'string',
                    'description': 'Detailed justification for waiver'
                },
                'expires_days': {
                    'type': 'integer',
                    'description': 'Number of days until waiver expires (optional)'
                },
                'created_by': {
                    'type': 'string',
                    'description': 'User creating the waiver'
                },
                'jira_ticket': {
                    'type': 'string',
                    'description': 'Associated JIRA ticket (optional)'
                }
            },
            'required': ['scope', 'pattern', 'reason', 'justification']
        }
    },
    
    'waiver_list': {
        'name': 'waiver_list',
        'description': 'List waivers with optional filtering',
        'inputSchema': {
            'type': 'object',
            'properties': {
                'status': {
                    'type': 'string',
                    'enum': ['pending', 'approved', 'rejected', 'expired', 'all'],
                    'description': 'Filter by waiver status'
                },
                'scope': {
                    'type': 'string',
                    'enum': ['finding', 'rule', 'file', 'project'],
                    'description': 'Filter by waiver scope'
                },
                'active_only': {
                    'type': 'boolean',
                    'description': 'Show only active (approved, non-expired) waivers'
                }
            }
        }
    },
    
    'waiver_approve': {
        'name': 'waiver_approve',
        'description': 'Approve a pending waiver',
        'inputSchema': {
            'type': 'object',
            'properties': {
                'waiver_id': {
                    'type': 'string',
                    'description': 'ID of waiver to approve'
                },
                'approved_by': {
                    'type': 'string',
                    'description': 'User approving the waiver'
                },
                'notes': {
                    'type': 'string',
                    'description': 'Approval notes (optional)'
                }
            },
            'required': ['waiver_id', 'approved_by']
        }
    },
    
    'waiver_reject': {
        'name': 'waiver_reject',
        'description': 'Reject a pending waiver',
        'inputSchema': {
            'type': 'object',
            'properties': {
                'waiver_id': {
                    'type': 'string',
                    'description': 'ID of waiver to reject'
                },
                'rejected_by': {
                    'type': 'string',
                    'description': 'User rejecting the waiver'
                },
                'notes': {
                    'type': 'string',
                    'description': 'Rejection notes (optional)'
                }
            },
            'required': ['waiver_id', 'rejected_by']
        }
    },
    
    'waiver_check': {
        'name': 'waiver_check',
        'description': 'Check if a violation is covered by an active waiver',
        'inputSchema': {
            'type': 'object',
            'properties': {
                'violation_fingerprint': {
                    'type': 'string',
                    'description': 'Fingerprint of the violation'
                },
                'file_path': {
                    'type': 'string',
                    'description': 'File path containing the violation'
                },
                'rule_type': {
                    'type': 'string',
                    'description': 'Rule type of the violation'
                }
            },
            'required': ['violation_fingerprint', 'file_path', 'rule_type']
        }
    },
    
    'waiver_cleanup': {
        'name': 'waiver_cleanup',
        'description': 'Clean up expired waivers',
        'inputSchema': {
            'type': 'object',
            'properties': {
                'dry_run': {
                    'type': 'boolean',
                    'description': 'Preview expired waivers without removing them'
                }
            }
        }
    },
    
    'waiver_statistics': {
        'name': 'waiver_statistics',
        'description': 'Get comprehensive waiver statistics',
        'inputSchema': {
            'type': 'object',
            'properties': {}
        }
    },
    
    'waiver_export': {
        'name': 'waiver_export',
        'description': 'Export comprehensive waivers report',
        'inputSchema': {
            'type': 'object',
            'properties': {
                'format': {
                    'type': 'string',
                    'enum': ['json', 'yaml'],
                    'description': 'Export format (json or yaml)'
                }
            }
        }
    }
}