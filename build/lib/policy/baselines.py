import time
import uuid
from typing import Dict, List, Any, Optional
from analyzer.core import ConnascenceViolation

# Baseline Manager Configuration Constants (CoM Improvement - Pass 2)
DEFAULT_BASELINE_VERSION = "1.0.0"
DEFAULT_BASELINE_CLEANUP_KEEP_COUNT = 5

class BaselineManager:
    def __init__(self):
        self.baselines = {}
        self.active_baseline = None
    
    def create_baseline(self, violations: List[ConnascenceViolation], 
                       description: str = "", version: str = DEFAULT_BASELINE_VERSION) -> str:
        """Create a new baseline from violations."""
        baseline_id = str(uuid.uuid4())
        
        baseline = BaselineSnapshot(
            baseline_id=baseline_id,
            violations=violations.copy(),
            description=description,
            version=version,
            created_at=time.time()
        )
        
        self.baselines[baseline_id] = baseline
        
        # Set as active if it's the first baseline
        if self.active_baseline is None:
            self.active_baseline = baseline_id
        
        return baseline_id
    
    def get_baseline(self, baseline_id: str) -> Optional['BaselineSnapshot']:
        """Get baseline by ID."""
        return self.baselines.get(baseline_id)
    
    def set_active_baseline(self, baseline_id: str) -> None:
        """Set the active baseline for comparisons."""
        if baseline_id not in self.baselines:
            raise ValueError(f"Baseline {baseline_id} not found")
        self.active_baseline = baseline_id
    
    def compare_to_baseline(self, current_violations: List[ConnascenceViolation],
                          baseline_id: str = None) -> 'BaselineComparison':
        """Compare current violations to baseline."""
        if baseline_id is None:
            baseline_id = self.active_baseline
        
        if baseline_id is None or baseline_id not in self.baselines:
            raise ValueError("No baseline available for comparison")
        
        baseline = self.baselines[baseline_id]
        return BaselineComparison(baseline.violations, current_violations)
    
    def filter_new_violations(self, current_violations: List[ConnascenceViolation],
                            baseline_id: str = None) -> List[ConnascenceViolation]:
        """Filter violations that are new compared to baseline."""
        comparison = self.compare_to_baseline(current_violations, baseline_id)
        return comparison.new_violations
    
    def list_baselines(self) -> List[Dict[str, Any]]:
        """List all baselines with metadata."""
        baseline_list = []
        for baseline_id, baseline in self.baselines.items():
            baseline_list.append({
                'id': baseline_id,
                'description': baseline.description,
                'version': baseline.version,
                'created_at': baseline.created_at,
                'violation_count': len(baseline.violations),
                'is_active': baseline_id == self.active_baseline
            })
        
        # Sort by creation time
        return sorted(baseline_list, key=lambda x: x['created_at'], reverse=True)
    
    def delete_baseline(self, baseline_id: str) -> None:
        """Delete a baseline."""
        if baseline_id not in self.baselines:
            raise ValueError(f"Baseline {baseline_id} not found")
        
        if baseline_id == self.active_baseline:
            # Find another baseline to set as active
            remaining_baselines = [bid for bid in self.baselines.keys() if bid != baseline_id]
            self.active_baseline = remaining_baselines[0] if remaining_baselines else None
        
        del self.baselines[baseline_id]
    
    def cleanup_old_baselines(self, keep_count: int = DEFAULT_BASELINE_CLEANUP_KEEP_COUNT) -> List[str]:
        """Clean up old baselines, keeping only the most recent ones."""
        if len(self.baselines) <= keep_count:
            return []
        
        baseline_list = self.list_baselines()
        to_delete = baseline_list[keep_count:]
        deleted_ids = []
        
        for baseline_info in to_delete:
            baseline_id = baseline_info['id']
            if baseline_id != self.active_baseline:  # Never delete active baseline
                self.delete_baseline(baseline_id)
                deleted_ids.append(baseline_id)
        
        return deleted_ids
    
    def get_baseline_statistics(self, baseline_id: str = None) -> Dict[str, Any]:
        """Get statistics for a baseline."""
        if baseline_id is None:
            baseline_id = self.active_baseline
        
        if baseline_id is None or baseline_id not in self.baselines:
            raise ValueError("No baseline available")
        
        baseline = self.baselines[baseline_id]
        violations = baseline.violations
        
        # Calculate statistics
        severity_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        type_counts = {}
        
        for violation in violations:
            severity = getattr(violation, 'severity', 'medium')
            if severity in severity_counts:
                severity_counts[severity] += 1
            
            conn_type = getattr(violation, 'connascence_type', 'unknown')
            type_counts[conn_type] = type_counts.get(conn_type, 0) + 1
        
        return {
            'baseline_id': baseline_id,
            'total_violations': len(violations),
            'severity_breakdown': severity_counts,
            'type_breakdown': type_counts,
            'created_at': baseline.created_at,
            'description': baseline.description,
            'version': baseline.version
        }

class BaselineSnapshot:
    def __init__(self, baseline_id: str, violations: List[ConnascenceViolation],
                 description: str = "", version: str = DEFAULT_BASELINE_VERSION, created_at: float = None):
        self.baseline_id = baseline_id
        self.violations = violations
        self.description = description
        self.version = version
        self.created_at = created_at or time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'baseline_id': self.baseline_id,
            'description': self.description,
            'version': self.version,
            'created_at': self.created_at,
            'violation_count': len(self.violations),
            'violations': [v.to_dict() if hasattr(v, 'to_dict') else str(v) for v in self.violations]
        }
    
class BaselineComparison:
    def __init__(self, baseline_violations: List[ConnascenceViolation], 
                 current_violations: List[ConnascenceViolation]):
        self.baseline_violations = baseline_violations
        self.current_violations = current_violations
        
        # Analyze differences
        self._analyze_differences()
    
    def _analyze_differences(self):
        """Analyze differences between baseline and current violations."""
        # Create sets for comparison (using violation signatures)
        baseline_signatures = set()
        current_signatures = set()
        
        for v in self.baseline_violations:
            sig = self._get_violation_signature(v)
            baseline_signatures.add(sig)
        
        for v in self.current_violations:
            sig = self._get_violation_signature(v)
            current_signatures.add(sig)
        
        # Find new and resolved violations
        new_sigs = current_signatures - baseline_signatures
        resolved_sigs = baseline_signatures - current_signatures
        
        # Map back to violation objects
        self.new_violations = []
        self.resolved_violations = []
        
        for v in self.current_violations:
            if self._get_violation_signature(v) in new_sigs:
                self.new_violations.append(v)
        
        for v in self.baseline_violations:
            if self._get_violation_signature(v) in resolved_sigs:
                self.resolved_violations.append(v)
        
        # Calculate improvement metrics
        self.improvement_ratio = (
            len(self.resolved_violations) / len(self.baseline_violations) 
            if self.baseline_violations else 0
        )
        
        self.regression_ratio = (
            len(self.new_violations) / len(self.baseline_violations)
            if self.baseline_violations else 0
        )
    
    def _get_violation_signature(self, violation: ConnascenceViolation) -> str:
        """Generate a unique signature for a violation."""
        file_path = getattr(violation, 'file_path', '')
        line_number = getattr(violation, 'line_number', 0)
        conn_type = getattr(violation, 'connascence_type', '')
        description = getattr(violation, 'description', '')
        
        return f"{file_path}:{line_number}:{conn_type}:{description}"
    
    def get_summary(self) -> Dict[str, Any]:
        """Get comparison summary."""
        return {
            'baseline_count': len(self.baseline_violations),
            'current_count': len(self.current_violations),
            'new_violations': len(self.new_violations),
            'resolved_violations': len(self.resolved_violations),
            'improvement_ratio': self.improvement_ratio,
            'regression_ratio': self.regression_ratio,
            'net_change': len(self.current_violations) - len(self.baseline_violations)
        }