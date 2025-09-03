import time
from typing import Dict, List, Any, Optional
from analyzer.core import ConnascenceViolation

class BudgetTracker:
    def __init__(self):
        self.budget_limits = {}
        self.current_usage = {}
        self.violations = []
        self.usage_history = []
        
    def set_budget_limits(self, limits: Dict[str, int]):
        """Set budget limits for different connascence types."""
        self.budget_limits = limits.copy()
    
    def track_violations(self, violations: List[ConnascenceViolation]):
        """Track violations against budget."""
        self.violations.extend(violations)
        
        # Update current usage
        self.current_usage = self._calculate_current_usage(self.violations)
        
        # Record usage snapshot
        self.usage_history.append({
            'timestamp': time.time(),
            'usage': self.current_usage.copy(),
            'violation_count': len(violations)
        })
    
    def check_compliance(self, violations: List[ConnascenceViolation] = None) -> Dict[str, Any]:
        """Check if current violations comply with budget."""
        if violations is None:
            violations = self.violations
            
        usage = self._calculate_current_usage(violations)
        compliance_status = {}
        
        for budget_type, limit in self.budget_limits.items():
            current_usage = usage.get(budget_type, 0)
            is_compliant = current_usage <= limit
            compliance_status[budget_type] = {
                'limit': limit,
                'usage': current_usage,
                'compliant': is_compliant,
                'remaining': max(0, limit - current_usage)
            }
        
        overall_compliant = all(status['compliant'] for status in compliance_status.values())
        
        return {
            'overall_compliant': overall_compliant,
            'compliant': overall_compliant,  # For backwards compatibility
            'budget_status': compliance_status,
            'total_violations': len(violations),
            'violations': []  # For test compatibility
        }
    
    def get_budget_report(self) -> Dict[str, Any]:
        """Get comprehensive budget usage report."""
        compliance = self.check_compliance()
        
        return {
            'budget_limits': self.budget_limits,
            'current_usage': self.current_usage,
            'current_compliance': compliance,
            'usage_history': self.usage_history[-10:],  # Last 10 entries
            'recommendations': self._generate_recommendations(compliance)
        }
    
    def _calculate_current_usage(self, violations: List[ConnascenceViolation]) -> Dict[str, int]:
        """Calculate current usage by connascence type and severity."""
        usage = {'total_violations': len(violations)}
        
        # Count by connascence type
        for violation in violations:
            conn_type = getattr(violation, 'connascence_type', 'unknown')
            usage[conn_type] = usage.get(conn_type, 0) + 1
            
            # Count by severity
            severity = getattr(violation, 'severity', 'medium')
            usage[severity] = usage.get(severity, 0) + 1
        
        return usage
    
    def _generate_recommendations(self, compliance: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on budget status."""
        recommendations = []
        
        if not compliance['overall_compliant']:
            recommendations.append("Budget limits exceeded - consider refactoring")
            
            for budget_type, status in compliance['budget_status'].items():
                if not status['compliant']:
                    recommendations.append(
                        f"Reduce {budget_type} violations by {status['usage'] - status['limit']}"
                    )
        
        return recommendations
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive budget report (alias for get_budget_report)."""
        return self.get_budget_report()
    
    def reset(self):
        """Reset tracked violations and usage."""
        self.violations = []
        self.current_usage = {}
        self.usage_history = []

class BudgetStatus:
    def __init__(self, compliant: bool, details: Dict[str, Any]):
        self.compliant = compliant
        self.details = details
    
class BudgetExceededException(Exception):
    def __init__(self, budget_type: str, current: int, limit: int):
        self.budget_type = budget_type
        self.current = current
        self.limit = limit
        super().__init__(f"Budget exceeded for {budget_type}: {current} > {limit}")