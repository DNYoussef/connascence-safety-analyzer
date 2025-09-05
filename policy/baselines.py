import time
import uuid
import json
import hashlib
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
# Need to create a mock ConnascenceViolation since analyzer.core was removed
class ConnascenceViolation:
    def __init__(self, id=None, rule_id=None, connascence_type=None, severity=None, 
                 description=None, file_path=None, line_number=None, weight=None, type=None, **kwargs):
        self.id = id
        self.rule_id = rule_id
        self.connascence_type = connascence_type or type
        self.type = type or connascence_type
        self.severity = severity
        self.description = description
        self.file_path = file_path
        self.line_number = line_number
        self.weight = weight
        self.context = kwargs.get('context', {})

# Baseline Manager Configuration Constants (CoM Improvement - Pass 2)
DEFAULT_BASELINE_VERSION = "1.0.0"
DEFAULT_BASELINE_CLEANUP_KEEP_COUNT = 5
DEFAULT_BASELINE_FILE = ".connascence/baseline.json"
DEFAULT_FINGERPRINT_VERSION = "2.0.0"

@dataclass
class FindingFingerprint:
    """Stable fingerprint for a finding that persists across code changes."""
    rule_id: str
    fingerprint: str  # SHA256 hash of finding context
    file_path: str
    line_number: int
    column: int
    severity: str
    context_hash: str  # Hash of surrounding code context
    created_at: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "fingerprint": self.fingerprint,
            "file": self.file_path,
            "line": self.line_number,
            "column": self.column,
            "severity": self.severity,
            "context_hash": self.context_hash,
            "created_at": self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FindingFingerprint':
        return cls(
            rule_id=data["rule_id"],
            fingerprint=data["fingerprint"],
            file_path=data["file"],
            line_number=data["line"],
            column=data["column"],
            severity=data["severity"],
            context_hash=data["context_hash"],
            created_at=data["created_at"]
        )

@dataclass
class BaselineSnapshot:
    """Complete baseline snapshot with metadata and git integration."""
    created_at: str
    description: str
    fingerprints: List[FindingFingerprint]
    commit_hash: Optional[str] = None
    branch: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    version: str = DEFAULT_FINGERPRINT_VERSION
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "created_at": self.created_at,
            "commit_hash": self.commit_hash,
            "branch": self.branch,
            "description": self.description,
            "version": self.version,
            "fingerprints": [fp.to_dict() for fp in self.fingerprints],
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BaselineSnapshot':
        return cls(
            created_at=data["created_at"],
            commit_hash=data.get("commit_hash"),
            branch=data.get("branch"),
            description=data["description"],
            version=data.get("version", DEFAULT_FINGERPRINT_VERSION),
            fingerprints=[FindingFingerprint.from_dict(fp) for fp in data["fingerprints"]],
            metadata=data.get("metadata", {})
        )

class EnhancedFingerprintGenerator:
    """Advanced fingerprinting system for stable finding identification."""
    
    @staticmethod
    def generate_finding_fingerprint(violation: ConnascenceViolation, source_lines: List[str] = None) -> FindingFingerprint:
        """Generate stable fingerprint for a violation."""
        
        # Basic violation info
        file_path = getattr(violation, 'file_path', '')
        line_number = getattr(violation, 'line_number', 0)
        column = getattr(violation, 'column', 0)
        severity = str(getattr(violation, 'severity', 'medium'))
        rule_id = getattr(violation, 'id', f"{getattr(violation, 'type', 'unknown')}")
        
        # Create stable context for fingerprinting
        context_elements = [
            rule_id,
            file_path,
            str(line_number),
            getattr(violation, 'description', ''),
            getattr(violation, 'connascence_type', ''),
            severity
        ]
        
        # Add surrounding code context if available
        context_hash = ""
        if source_lines and 0 <= line_number - 1 < len(source_lines):
            # Include 2 lines before and after for context
            context_start = max(0, line_number - 3)
            context_end = min(len(source_lines), line_number + 2)
            context_lines = source_lines[context_start:context_end]
            
            # Normalize whitespace for stable hashing
            normalized_context = '\n'.join(line.strip() for line in context_lines)
            context_hash = hashlib.sha256(normalized_context.encode('utf-8')).hexdigest()[:16]
        
        # Generate primary fingerprint
        fingerprint_content = '|'.join(context_elements) + f"|{context_hash}"
        fingerprint = hashlib.sha256(fingerprint_content.encode('utf-8')).hexdigest()
        
        return FindingFingerprint(
            rule_id=rule_id,
            fingerprint=fingerprint,
            file_path=file_path,
            line_number=line_number,
            column=column,
            severity=severity,
            context_hash=context_hash,
            created_at=datetime.now().isoformat()
        )

class EnhancedBaselineManager:
    """Enterprise-grade baseline management with Git integration and fingerprinting."""
    
    def __init__(self, baseline_file: str = DEFAULT_BASELINE_FILE):
        self.baseline_file = Path(baseline_file)
        self.baseline_dir = self.baseline_file.parent
        self.fingerprint_generator = EnhancedFingerprintGenerator()
        
        # Legacy support
        self.baselines = {}
        self.active_baseline = None
        
        # Ensure baseline directory exists
        self.baseline_dir.mkdir(parents=True, exist_ok=True)
    
    def create_snapshot(self, violations: List[ConnascenceViolation], 
                       description: str = "", source_lines_map: Optional[Dict[str, List[str]]] = None) -> BaselineSnapshot:
        """Create a comprehensive baseline snapshot."""
        
        # Get git information
        commit_hash = self._get_git_commit_hash()
        branch = self._get_git_branch()
        
        # Generate fingerprints for all violations
        fingerprints = []
        for violation in violations:
            file_path = getattr(violation, 'file_path', '')
            source_lines = source_lines_map.get(file_path) if source_lines_map else None
            
            fingerprint = self.fingerprint_generator.generate_finding_fingerprint(
                violation, source_lines
            )
            fingerprints.append(fingerprint)
        
        # Create snapshot
        snapshot = BaselineSnapshot(
            created_at=datetime.now().isoformat(),
            description=description or f"Snapshot at {commit_hash[:8] if commit_hash else 'unknown'}",
            fingerprints=fingerprints,
            commit_hash=commit_hash,
            branch=branch,
            metadata={
                "total_violations": len(violations),
                "severity_counts": self._count_by_severity(violations),
                "rule_counts": self._count_by_rule(violations),
                "files_affected": len(set(getattr(v, 'file_path', '') for v in violations))
            }
        )
        
        return snapshot
    
    def save_baseline(self, snapshot: BaselineSnapshot) -> None:
        """Save baseline snapshot to disk."""
        with open(self.baseline_file, 'w', encoding='utf-8') as f:
            json.dump(snapshot.to_dict(), f, indent=2)
    
    def load_baseline(self) -> Optional[BaselineSnapshot]:
        """Load baseline snapshot from disk."""
        if not self.baseline_file.exists():
            return None
        
        try:
            with open(self.baseline_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return BaselineSnapshot.from_dict(data)
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"Warning: Could not load baseline from {self.baseline_file}: {e}")
            return None
    
    def compare_with_baseline(self, current_violations: List[ConnascenceViolation], 
                             source_lines_map: Optional[Dict[str, List[str]]] = None) -> Dict[str, Any]:
        """Compare current violations with stored baseline."""
        baseline = self.load_baseline()
        if not baseline:
            return {
                "status": "no_baseline",
                "message": "No baseline found. Create one with 'snapshot_create'.",
                "all_violations_new": True,
                "new_violations": len(current_violations),
                "resolved_violations": 0,
                "baseline_violations": 0
            }
        
        # Generate fingerprints for current violations
        current_fingerprints = {}
        for violation in current_violations:
            file_path = getattr(violation, 'file_path', '')
            source_lines = source_lines_map.get(file_path) if source_lines_map else None
            
            fingerprint = self.fingerprint_generator.generate_finding_fingerprint(
                violation, source_lines
            )
            current_fingerprints[fingerprint.fingerprint] = {
                "fingerprint_obj": fingerprint,
                "violation": violation
            }
        
        # Create baseline fingerprint lookup
        baseline_fingerprints = {fp.fingerprint: fp for fp in baseline.fingerprints}
        
        # Find new and resolved violations
        current_fps = set(current_fingerprints.keys())
        baseline_fps = set(baseline_fingerprints.keys())
        
        new_fps = current_fps - baseline_fps
        resolved_fps = baseline_fps - current_fps
        
        # Collect detailed violation information
        new_violations = [current_fingerprints[fp]["violation"] for fp in new_fps]
        resolved_violations = [baseline_fingerprints[fp] for fp in resolved_fps]
        
        return {
            "status": "compared",
            "baseline_created_at": baseline.created_at,
            "baseline_commit": baseline.commit_hash,
            "baseline_branch": baseline.branch,
            "total_current": len(current_violations),
            "total_baseline": len(baseline.fingerprints),
            "new_violations": len(new_violations),
            "resolved_violations": len(resolved_violations),
            "unchanged_violations": len(current_fps & baseline_fps),
            "new_violation_details": [self._violation_summary(v) for v in new_violations],
            "resolved_violation_details": [fp.to_dict() for fp in resolved_violations],
            "net_change": len(current_violations) - len(baseline.fingerprints),
            "improvement_percentage": (len(resolved_violations) / len(baseline.fingerprints) * 100) if baseline.fingerprints else 0
        }
    
    def filter_new_violations_only(self, violations: List[ConnascenceViolation], 
                                  source_lines_map: Optional[Dict[str, List[str]]] = None) -> List[ConnascenceViolation]:
        """Filter violations to only return those not in the baseline."""
        comparison = self.compare_with_baseline(violations, source_lines_map)
        
        if comparison["status"] == "no_baseline":
            return violations  # No baseline = all violations are new
        
        # Use comparison results to filter
        baseline = self.load_baseline()
        if not baseline:
            return violations
        
        # Generate fingerprints for current violations
        current_fps = set()
        violation_by_fp = {}
        
        for violation in violations:
            file_path = getattr(violation, 'file_path', '')
            source_lines = source_lines_map.get(file_path) if source_lines_map else None
            
            fingerprint = self.fingerprint_generator.generate_finding_fingerprint(
                violation, source_lines
            )
            current_fps.add(fingerprint.fingerprint)
            violation_by_fp[fingerprint.fingerprint] = violation
        
        # Baseline fingerprints
        baseline_fps = {fp.fingerprint for fp in baseline.fingerprints}
        
        # New violations are those not in baseline
        new_fps = current_fps - baseline_fps
        return [violation_by_fp[fp] for fp in new_fps]
    
    def _get_git_commit_hash(self) -> Optional[str]:
        """Get current git commit hash."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"], 
                capture_output=True, text=True, cwd=self.baseline_dir
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except (subprocess.SubprocessError, FileNotFoundError):
            pass
        return None
    
    def _get_git_branch(self) -> Optional[str]:
        """Get current git branch."""
        try:
            result = subprocess.run(
                ["git", "branch", "--show-current"], 
                capture_output=True, text=True, cwd=self.baseline_dir
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except (subprocess.SubprocessError, FileNotFoundError):
            pass
        return None
    
    def _count_by_severity(self, violations: List[ConnascenceViolation]) -> Dict[str, int]:
        """Count violations by severity."""
        counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for v in violations:
            severity = str(getattr(v, 'severity', 'medium')).lower()
            if severity in counts:
                counts[severity] += 1
        return counts
    
    def _count_by_rule(self, violations: List[ConnascenceViolation]) -> Dict[str, int]:
        """Count violations by rule."""
        counts = {}
        for v in violations:
            rule = getattr(v, 'connascence_type', 'unknown')
            counts[rule] = counts.get(rule, 0) + 1
        return counts
    
    def _violation_summary(self, violation: ConnascenceViolation) -> Dict[str, Any]:
        """Create summary of violation for reporting."""
        return {
            "rule_id": getattr(violation, 'id', ''),
            "type": getattr(violation, 'connascence_type', ''),
            "severity": str(getattr(violation, 'severity', 'medium')),
            "file": getattr(violation, 'file_path', ''),
            "line": getattr(violation, 'line_number', 0),
            "description": getattr(violation, 'description', '')
        }
    
    def get_baseline_info(self) -> Dict[str, Any]:
        """Get information about current baseline."""
        baseline = self.load_baseline()
        if not baseline:
            return {"status": "no_baseline", "message": "No baseline exists"}
        
        return {
            "status": "exists",
            "created_at": baseline.created_at,
            "commit_hash": baseline.commit_hash,
            "branch": baseline.branch,
            "description": baseline.description,
            "version": baseline.version,
            "total_violations": len(baseline.fingerprints),
            "metadata": baseline.metadata,
            "file_path": str(self.baseline_file)
        }
    
    def list_baseline_history(self) -> List[Dict[str, Any]]:
        """List baseline history (for future git-based versioning)."""
        # For now, return current baseline only
        # In future versions, this could scan git history for baseline.json changes
        baseline = self.load_baseline()
        if not baseline:
            return []
        
        return [self.get_baseline_info()]

# Legacy BaselineManager for backward compatibility
class BaselineManager(EnhancedBaselineManager):
    """Legacy BaselineManager - delegates to enhanced version."""
    
    def __init__(self):
        super().__init__()
        # Keep old interface working
    
    def create_baseline(self, violations: List[ConnascenceViolation], 
                       description: str = "", version: str = DEFAULT_BASELINE_VERSION) -> str:
        """Legacy create_baseline method - creates and saves snapshot."""
        snapshot = self.create_snapshot(violations, description)
        self.save_baseline(snapshot)
        return f"snapshot_{snapshot.created_at}"
    
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

# Note: BaselineSnapshot dataclass defined above, removing duplicate class definition
    
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