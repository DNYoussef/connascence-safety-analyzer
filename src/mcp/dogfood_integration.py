"""
Dogfood Integration for MCP Server

Integrates the dogfood self-improvement system with the MCP server,
providing tool handlers and orchestration capabilities.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

# Import dogfood system components
import sys
sys.path.append(str(Path(__file__).parent.parent))

from dogfood import DogfoodController, SafetyValidator, BranchManager, MetricsTracker

class MCPDogfoodIntegration:
    """Integrates dogfood system with MCP server"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Initialize dogfood components
        self.controller = DogfoodController(config)
        self.safety_validator = SafetyValidator(config)
        self.branch_manager = BranchManager(config)
        self.metrics_tracker = MetricsTracker(config)
        
        # Track active cycles
        self.active_cycles = {}
        self.cycle_history = []
    
    async def handle_dogfood_orchestrate(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main dogfood orchestration tool - runs complete improvement cycle
        """
        improvement_goal = args.get('improvement_goal', 'coupling_reduction')
        safety_mode = args.get('safety_mode', 'strict')
        
        self.logger.info(f"🚀 Starting dogfood orchestration: {improvement_goal}")
        
        try:
            # Safety check: ensure we're not on main branch
            current_branch = await self.branch_manager.get_current_branch()
            if current_branch in ['main', 'master']:
                return {
                    'success': False,
                    'error': '🚨 SAFETY VIOLATION: Cannot run dogfood on main branch',
                    'required_action': 'Switch to a dogfood branch first',
                    'suggested_command': f'git checkout -b dogfood-{improvement_goal}'
                }
            
            # Run complete improvement cycle
            result = await self.controller.run_improvement_cycle(
                improvement_goal=improvement_goal,
                safety_mode=safety_mode
            )
            
            # Store result in history
            self.cycle_history.append(result)
            
            # Return structured result
            return {
                'success': result.success,
                'cycle_id': f"cycle_{len(self.cycle_history)}",
                'branch_name': result.branch_name,
                'improvements_applied': len(result.improvements_applied),
                'test_results': {
                    'all_passed': result.test_results.get('all_passed', False),
                    'total_tests': result.test_results.get('total_tests', 0),
                    'failures': result.test_results.get('total_failures', 0)
                },
                'metrics_comparison': result.metrics_comparison,
                'decision': result.decision_reason,
                'rollback_performed': result.rollback_performed,
                'timestamp': result.timestamp.isoformat(),
                'next_recommendations': self._generate_next_recommendations(result)
            }
            
        except Exception as e:
            self.logger.error(f"💥 Dogfood orchestration failed: {e}")
            return {
                'success': False,
                'error': f'Dogfood orchestration failed: {str(e)}',
                'recovery_suggestions': [
                    'Check branch status with git status',
                    'Ensure all dependencies are available',
                    'Run emergency cleanup if needed'
                ]
            }
    
    async def handle_dogfood_status(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get current status of dogfood system
        """
        try:
            current_branch = await self.branch_manager.get_current_branch()
            is_clean = await self.branch_manager.is_clean_working_directory()
            
            # Get recent metrics if available
            recent_metrics = None
            try:
                recent_metrics = await self.metrics_tracker.capture_current_state()
            except:
                pass
            
            return {
                'success': True,
                'current_branch': current_branch,
                'is_dogfood_branch': current_branch.startswith('dogfood'),
                'working_directory_clean': is_clean,
                'active_cycles': len(self.active_cycles),
                'total_cycles_run': len(self.cycle_history),
                'last_cycle_success': (
                    self.cycle_history[-1].success if self.cycle_history else None
                ),
                'current_metrics': {
                    'connascence_score': recent_metrics.connascence_score if recent_metrics else None,
                    'violation_count': recent_metrics.violation_count if recent_metrics else None,
                    'nasa_compliance': recent_metrics.nasa_compliance if recent_metrics else None
                } if recent_metrics else None,
                'system_health': 'operational'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to get dogfood status: {str(e)}',
                'system_health': 'error'
            }
    
    async def handle_dogfood_history(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get history of dogfood cycles
        """
        limit = args.get('limit', 10)
        include_details = args.get('include_details', False)
        
        try:
            # Get recent cycles
            recent_cycles = self.cycle_history[-limit:]
            
            history_data = []
            for i, cycle in enumerate(recent_cycles):
                cycle_data = {
                    'cycle_id': f"cycle_{len(self.cycle_history) - len(recent_cycles) + i + 1}",
                    'success': cycle.success,
                    'branch_name': cycle.branch_name,
                    'timestamp': cycle.timestamp.isoformat(),
                    'improvements_count': len(cycle.improvements_applied),
                    'rollback_performed': cycle.rollback_performed,
                    'decision_summary': cycle.decision_reason
                }
                
                if include_details:
                    cycle_data.update({
                        'improvements_applied': cycle.improvements_applied,
                        'test_results': cycle.test_results,
                        'metrics_comparison': cycle.metrics_comparison
                    })
                
                history_data.append(cycle_data)
            
            # Calculate success rate
            successful_cycles = sum(1 for cycle in self.cycle_history if cycle.success)
            success_rate = successful_cycles / len(self.cycle_history) if self.cycle_history else 0
            
            return {
                'success': True,
                'total_cycles': len(self.cycle_history),
                'success_rate': success_rate,
                'recent_cycles': history_data,
                'trends': self._analyze_trends(),
                'recommendations': self._get_history_based_recommendations()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to get dogfood history: {str(e)}'
            }
    
    def _generate_next_recommendations(self, cycle_result) -> List[str]:
        """Generate recommendations for next dogfood cycle"""
        recommendations = []
        
        if cycle_result.success:
            recommendations.append("✅ Cycle successful - ready for next improvement")
            
            # Analyze what worked well
            if cycle_result.metrics_comparison.get('connascence_score_change', 0) > 0.05:
                recommendations.append("🎯 Consider focusing on similar violation types")
            
            recommendations.append("🔄 Run cascade analysis to find next targets")
        else:
            recommendations.append("❌ Cycle failed - address issues before next attempt")
            
            if 'test' in cycle_result.decision_reason.lower():
                recommendations.append("🧪 Fix failing tests before next cycle")
            elif 'score' in cycle_result.decision_reason.lower():
                recommendations.append("📊 Focus on simpler, safer improvements")
            
            recommendations.append("🔍 Consider switching to 'experimental' safety mode")
        
        return recommendations
    
    def _analyze_trends(self) -> Dict[str, Any]:
        """Analyze trends in dogfood cycles"""
        if len(self.cycle_history) < 2:
            return {"message": "Not enough data for trend analysis"}
        
        # Success rate over time
        recent_success_rate = sum(
            1 for cycle in self.cycle_history[-5:] if cycle.success
        ) / min(5, len(self.cycle_history))
        
        # Average improvements per cycle
        avg_improvements = sum(
            len(cycle.improvements_applied) for cycle in self.cycle_history
        ) / len(self.cycle_history)
        
        return {
            'recent_success_rate': recent_success_rate,
            'average_improvements_per_cycle': avg_improvements,
            'most_common_failure_reason': self._get_most_common_failure(),
            'improvement_velocity': 'increasing' if recent_success_rate > 0.6 else 'needs_attention'
        }
    
    def _get_most_common_failure(self) -> str:
        """Get the most common failure reason"""
        failed_cycles = [cycle for cycle in self.cycle_history if not cycle.success]
        if not failed_cycles:
            return "No failures"
        
        # Simple analysis of failure reasons
        test_failures = sum(1 for cycle in failed_cycles if 'test' in cycle.decision_reason.lower())
        score_failures = sum(1 for cycle in failed_cycles if 'score' in cycle.decision_reason.lower())
        
        if test_failures > score_failures:
            return "Test failures"
        elif score_failures > 0:
            return "Metrics not improving"
        else:
            return "Various issues"
    
    def _get_history_based_recommendations(self) -> List[str]:
        """Get recommendations based on cycle history"""
        if not self.cycle_history:
            return ["🚀 Ready to run first dogfood cycle"]
        
        recommendations = []
        recent_cycles = self.cycle_history[-3:]
        
        # Check for consistent failures
        if all(not cycle.success for cycle in recent_cycles):
            recommendations.append("⚠️ Multiple failures detected - consider switching strategy")
            recommendations.append("🔧 Try 'experimental' safety mode for more aggressive fixes")
        
        # Check for improvement plateau
        elif all(cycle.success for cycle in recent_cycles):
            recommendations.append("🎉 Great progress! Consider more challenging improvement goals")
            recommendations.append("🎯 Try 'nasa_compliance' or 'architectural_health' goals")
        
        return recommendations
    
    async def emergency_reset(self) -> Dict[str, Any]:
        """Emergency reset for dogfood system"""
        try:
            # Clear active cycles
            self.active_cycles.clear()
            
            # Run emergency cleanup
            cleanup_success = await self.branch_manager.emergency_cleanup()
            
            return {
                'success': cleanup_success,
                'message': 'Emergency reset completed' if cleanup_success else 'Emergency reset failed',
                'actions_taken': [
                    'Cleared active cycles',
                    'Attempted branch cleanup',
                    'Returned to main branch'
                ]
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Emergency reset failed: {str(e)}'
            }

# Integration helper function for MCP server
def create_dogfood_integration(config: Optional[Dict[str, Any]] = None) -> MCPDogfoodIntegration:
    """Create dogfood integration instance for MCP server"""
    return MCPDogfoodIntegration(config)