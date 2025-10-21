# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2024 Connascence Safety Analyzer Contributors
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

from dataclasses import dataclass, field
from datetime import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import time
from typing import Any, Dict, List, Optional

from fixes.phase0.production_safe_assertions import ProductionAssert
from utils.types import ConnascenceViolation

# Need to create a mock ConnascenceViolation since analyzer.core was removed
# ConnascenceViolation now available from utils.types
# This duplicate class has been removed

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
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FindingFingerprint":
        return cls(
            rule_id=data["rule_id"],
            fingerprint=data["fingerprint"],
            file_path=data["file"],
            line_number=data["line"],
            column=data["column"],
            severity=data["severity"],
            context_hash=data["context_hash"],
            created_at=data["created_at"],
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
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BaselineSnapshot":
        return cls(
            created_at=data["created_at"],
            commit_hash=data.get("commit_hash"),
            branch=data.get("branch"),
            description=data["description"],
            version=data.get("version", DEFAULT_FINGERPRINT_VERSION),
            fingerprints=[FindingFingerprint.from_dict(fp) for fp in data["fingerprints"]],
            metadata=data.get("metadata", {}),
        )


class EnhancedFingerprintGenerator:
    """Advanced fingerprinting system for stable finding identification."""

    @staticmethod
    def generate_finding_fingerprint(
        violation: ConnascenceViolation, source_lines: Optional[List[str]] = None
    ) -> FindingFingerprint:
        """Generate stable fingerprint for a violation."""

        # Basic violation info
        file_path = getattr(violation, "file_path", "")
        line_number = getattr(violation, "line_number", 0)
        column = getattr(violation, "column", 0)
        severity = str(getattr(violation, "severity", "medium"))
        rule_id = getattr(violation, "id", f"{getattr(violation, 'type', 'unknown')}")

        # Create stable context for fingerprinting
        context_elements = [
            rule_id,
            file_path,
            str(line_number),
            getattr(violation, "description", ""),
            getattr(violation, "connascence_type", ""),
            severity,
        ]

        # Add surrounding code context if available
        context_hash = ""
        if source_lines and 0 <= line_number - 1 < len(source_lines):
            # Include 2 lines before and after for context
            context_start = max(0, line_number - 3)
            context_end = min(len(source_lines), line_number + 2)
            context_lines = source_lines[context_start:context_end]

            # Normalize whitespace for stable hashing
            normalized_context = "\n".join(line.strip() for line in context_lines)
            context_hash = hashlib.sha256(normalized_context.encode("utf-8")).hexdigest()[:16]

        # Generate primary fingerprint
        fingerprint_content = "|".join(context_elements) + f"|{context_hash}"
        fingerprint = hashlib.sha256(fingerprint_content.encode("utf-8")).hexdigest()

        return FindingFingerprint(
            rule_id=rule_id,
            fingerprint=fingerprint,
            file_path=file_path,
            line_number=line_number,
            column=column,
            severity=severity,
            context_hash=context_hash,
            created_at=datetime.now().isoformat(),
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

    def create_snapshot(
        self,
        violations: List[ConnascenceViolation],
        description: str = "",
        source_lines_map: Optional[Dict[str, List[str]]] = None,
    ) -> BaselineSnapshot:
        """Create a comprehensive baseline snapshot."""

        # Get git information
        commit_hash = self._get_git_commit_hash()
        branch = self._get_git_branch()

        # Generate fingerprints for all violations
        fingerprints = []
        for violation in violations:
            file_path = getattr(violation, "file_path", "")
            source_lines = source_lines_map.get(file_path) if source_lines_map else None

            fingerprint = self.fingerprint_generator.generate_finding_fingerprint(violation, source_lines)
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
                "files_affected": len({getattr(v, "file_path", "") for v in violations}),
            },
        )

        return snapshot

    def save_baseline(self, snapshot: BaselineSnapshot) -> None:
        """Save baseline snapshot to disk."""
        with open(self.baseline_file, "w", encoding="utf-8") as f:
            json.dump(snapshot.to_dict(), f, indent=2)

    def load_baseline(self) -> Optional[BaselineSnapshot]:
        """Load baseline snapshot from disk."""
        if not self.baseline_file.exists():
            return None

        try:
            with open(self.baseline_file, encoding="utf-8") as f:
                data = json.load(f)
                return BaselineSnapshot.from_dict(data)
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"Warning: Could not load baseline from {self.baseline_file}: {e}")
            return None

    def compare_with_baseline(
        self, current_violations: List[ConnascenceViolation], source_lines_map: Optional[Dict[str, List[str]]] = None
    ) -> Dict[str, Any]:
        """Compare current violations with stored baseline."""
        baseline = self.load_baseline()
        if not baseline:
            return {
                "status": "no_baseline",
                "message": "No baseline found. Create one with 'snapshot_create'.",
                "all_violations_new": True,
                "new_violations": len(current_violations),
                "resolved_violations": 0,
                "baseline_violations": 0,
            }

        # Generate fingerprints for current violations
        current_fingerprints = {}
        for violation in current_violations:
            file_path = getattr(violation, "file_path", "")
            source_lines = source_lines_map.get(file_path) if source_lines_map else None

            fingerprint = self.fingerprint_generator.generate_finding_fingerprint(violation, source_lines)
            current_fingerprints[fingerprint.fingerprint] = {"fingerprint_obj": fingerprint, "violation": violation}

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
            "improvement_percentage": (
                (len(resolved_violations) / len(baseline.fingerprints) * 100) if baseline.fingerprints else 0
            ),
        }

    def filter_new_violations_only(
        self, violations: List[ConnascenceViolation], source_lines_map: Optional[Dict[str, List[str]]] = None
    ) -> List[ConnascenceViolation]:
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
            file_path = getattr(violation, "file_path", "")
            source_lines = source_lines_map.get(file_path) if source_lines_map else None

            fingerprint = self.fingerprint_generator.generate_finding_fingerprint(violation, source_lines)
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
                ["git", "rev-parse", "HEAD"], check=False, capture_output=True, text=True, cwd=self.baseline_dir
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
                ["git", "branch", "--show-current"], check=False, capture_output=True, text=True, cwd=self.baseline_dir
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
            severity = str(getattr(v, "severity", "medium")).lower()
            if severity in counts:
                counts[severity] += 1
        return counts

    def _count_by_rule(self, violations: List[ConnascenceViolation]) -> Dict[str, int]:
        """Count violations by rule."""
        counts = {}
        for v in violations:
            rule = getattr(v, "connascence_type", "unknown")
            counts[rule] = counts.get(rule, 0) + 1
        return counts

    def _violation_summary(self, violation: ConnascenceViolation) -> Dict[str, Any]:
        """Create summary of violation for reporting."""
        return {
            "rule_id": getattr(violation, "id", ""),
            "type": getattr(violation, "connascence_type", ""),
            "severity": str(getattr(violation, "severity", "medium")),
            "file": getattr(violation, "file_path", ""),
            "line": getattr(violation, "line_number", 0),
            "description": getattr(violation, "description", ""),
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
            "file_path": str(self.baseline_file),
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
class BaselineManager:
    """Simple BaselineManager for test compatibility."""

    def __init__(self):
        self.baselines = {}  # In-memory storage for tests
        self.active_baseline = None

    def create_baseline(
        self, violations: List[ConnascenceViolation], description: str = "", version: str = DEFAULT_BASELINE_VERSION
    ) -> str:
        """Create a new quality baseline."""
        # Use unique ID to avoid collisions
        timestamp = time.time()
        baseline_counter = len(self.baselines)  # Simple counter for uniqueness
        baseline_id = f"baseline_{int(timestamp)}_{baseline_counter}_{len(violations)}"

        baseline_data = {
            "id": baseline_id,
            "description": description,
            "created_at": datetime.fromtimestamp(timestamp).isoformat(),
            "violations": [self._violation_to_dict(v) for v in violations],
            "version": version or "1.0.0",
            "_sort_key": timestamp + baseline_counter * 0.001,  # Add slight offset for uniqueness
        }

        # Store in memory for tests
        self.baselines[baseline_id] = baseline_data

        # Add small delay to ensure different timestamps for next call
        time.sleep(0.01)

        return baseline_id

    def _violation_to_dict(self, violation: ConnascenceViolation) -> Dict[str, Any]:
        """Convert violation object to dictionary."""
        return {
            "id": getattr(violation, "id", ""),
            "rule_id": getattr(violation, "rule_id", ""),
            "connascence_type": getattr(violation, "connascence_type", ""),
            "severity": getattr(violation, "severity", "medium"),
            "description": getattr(violation, "description", ""),
            "file_path": getattr(violation, "file_path", ""),
            "line_number": getattr(violation, "line_number", 0),
            "weight": getattr(violation, "weight", 1.0),
        }

    def get_baseline(self, baseline_id: str) -> Optional[Dict[str, Any]]:
        """Get baseline by ID."""
        return self.baselines.get(baseline_id)

    def compare_against_baseline(
        self, current_violations: List[ConnascenceViolation], baseline_id: str
    ) -> Dict[str, Any]:
        """Compare current violations against baseline."""
        baseline_data = self.get_baseline(baseline_id)
        if not baseline_data:
            raise ValueError(f"Baseline not found: {baseline_id}")

        # Get baseline violations
        baseline_violations = baseline_data.get("violations", [])
        baseline_ids = {v.get("id", "") for v in baseline_violations}

        # Categorize current violations
        current_ids = {getattr(v, "id", "") for v in current_violations}

        new_violation_ids = current_ids - baseline_ids
        resolved_violation_ids = baseline_ids - current_ids
        unchanged_violation_ids = current_ids & baseline_ids

        # Map back to violations
        current_by_id = {getattr(v, "id", ""): v for v in current_violations}
        baseline_by_id = {v.get("id", ""): v for v in baseline_violations}

        new_violations = [current_by_id[vid] for vid in new_violation_ids if vid in current_by_id]
        resolved_violations = [baseline_by_id[vid] for vid in resolved_violation_ids if vid in baseline_by_id]
        unchanged_violations = [current_by_id[vid] for vid in unchanged_violation_ids if vid in current_by_id]

        return {
            "new_violations": [self._violation_to_dict(v) for v in new_violations],
            "resolved_violations": resolved_violations,
            "unchanged_violations": [self._violation_to_dict(v) for v in unchanged_violations],
            "summary": {
                "total_new": len(new_violations),
                "total_resolved": len(resolved_violations),
                "total_unchanged": len(unchanged_violations),
                "net_change": len(new_violations) - len(resolved_violations),
            },
        }

    def filter_new_violations(
        self, current_violations: List[ConnascenceViolation], baseline_id: str
    ) -> List[Dict[str, Any]]:
        """Filter violations to only return new ones not in baseline."""
        comparison = self.compare_against_baseline(current_violations, baseline_id)
        return comparison["new_violations"]

    def list_baselines(self) -> List[Dict[str, Any]]:
        """List all baselines with metadata."""
        baseline_list = []

        for baseline_id, baseline_data in self.baselines.items():
            summary = {
                "id": baseline_id,
                "description": baseline_data.get("description", ""),
                "created_at": baseline_data.get("created_at", ""),
                "version": baseline_data.get("version", DEFAULT_BASELINE_VERSION),
                "violation_count": len(baseline_data.get("violations", [])),
                "violations": baseline_data.get("violations", []),
            }
            baseline_list.append(summary)

        # Sort by creation time (newest first)
        baseline_list.sort(key=lambda x: x["created_at"], reverse=True)
        return baseline_list

    def cleanup_old_baselines(self, keep_count: int = DEFAULT_BASELINE_CLEANUP_KEEP_COUNT):
        """Clean up old baselines, keeping only the most recent ones."""

        ProductionAssert.not_none(keep_count, "keep_count")

        ProductionAssert.not_none(keep_count, "keep_count")

        if len(self.baselines) <= keep_count:
            return

        # Get sorted list of baselines by sort key or creation time (newest first)
        sorted_baselines = sorted(self.baselines.items(), key=lambda x: x[1].get("_sort_key", 0), reverse=True)

        # Keep only the most recent ones
        baselines_to_keep = dict(sorted_baselines[:keep_count])
        self.baselines = baselines_to_keep


class BaselineComparison:
    def __init__(self, baseline_violations: List[ConnascenceViolation], current_violations: List[ConnascenceViolation]):
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
            len(self.resolved_violations) / len(self.baseline_violations) if self.baseline_violations else 0
        )

        self.regression_ratio = (
            len(self.new_violations) / len(self.baseline_violations) if self.baseline_violations else 0
        )

    def _get_violation_signature(self, violation: ConnascenceViolation) -> str:
        """Generate a unique signature for a violation."""
        file_path = getattr(violation, "file_path", "")
        line_number = getattr(violation, "line_number", 0)
        conn_type = getattr(violation, "connascence_type", "")
        description = getattr(violation, "description", "")

        return f"{file_path}:{line_number}:{conn_type}:{description}"

    def get_summary(self) -> Dict[str, Any]:
        """Get comparison summary."""
        return {
            "baseline_count": len(self.baseline_violations),
            "current_count": len(self.current_violations),
            "new_violations": len(self.new_violations),
            "resolved_violations": len(self.resolved_violations),
            "improvement_ratio": self.improvement_ratio,
            "regression_ratio": self.regression_ratio,
            "net_change": len(self.current_violations) - len(self.baseline_violations),
        }
