#!/usr/bin/env python3

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

"""
Comprehensive Waiver Management System
=====================================

Provides enterprise-grade waiver management for connascence violations including:
- YAML-based waiver configuration with schema validation
- Hierarchical waiver patterns (file, rule, finding-specific)
- Expiration tracking and automatic cleanup
- Audit logging and approval workflows
- Integration with baseline fingerprinting system

Author: Connascence Safety Analyzer Team
"""

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import yaml

    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False
    yaml = None


class WaiverStatus(Enum):
    """Waiver approval status."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    AUTO_APPROVED = "auto_approved"


class WaiverScope(Enum):
    """Scope of waiver application."""

    FINDING_SPECIFIC = "finding"  # Specific violation fingerprint
    RULE_WIDE = "rule"  # All violations of a rule type
    FILE_WIDE = "file"  # All violations in a file
    PROJECT_WIDE = "project"  # All violations project-wide


@dataclass
class WaiverMetadata:
    """Metadata for waiver tracking."""

    created_by: str
    created_at: str
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
    review_notes: Optional[str] = None
    jira_ticket: Optional[str] = None
    security_review: bool = False


@dataclass
class WaiverRule:
    """Individual waiver rule configuration."""

    id: str
    scope: WaiverScope
    pattern: str  # Fingerprint, rule name, file pattern, or '*'
    reason: str
    justification: str
    expires_at: Optional[str] = None  # ISO format or 'never'
    status: WaiverStatus = WaiverStatus.PENDING
    metadata: Optional[WaiverMetadata] = None
    conditions: Optional[Dict[str, Any]] = None  # Additional matching conditions

    def is_expired(self) -> bool:
        """Check if waiver has expired."""
        if not self.expires_at or self.expires_at == "never":
            return False
        try:
            expiry_date = datetime.fromisoformat(self.expires_at)
            return datetime.now() > expiry_date
        except ValueError:
            return True  # Invalid date format = expired

    def matches_violation(self, violation_fingerprint: str, file_path: str, rule_type: str) -> bool:
        """Check if this waiver applies to a specific violation."""
        if self.status not in [WaiverStatus.APPROVED, WaiverStatus.AUTO_APPROVED]:
            return False

        if self.is_expired():
            return False

        # Match based on scope
        if self.scope == WaiverScope.FINDING_SPECIFIC:
            return self.pattern == violation_fingerprint
        elif self.scope == WaiverScope.RULE_WIDE:
            return self.pattern == rule_type or self.pattern == "*"
        elif self.scope == WaiverScope.FILE_WIDE:
            # Support glob patterns
            import fnmatch

            return fnmatch.fnmatch(file_path, self.pattern)
        elif self.scope == WaiverScope.PROJECT_WIDE:
            return self.pattern == "*"

        return False


class EnhancedWaiverSystem:
    """Enterprise-grade waiver management system."""

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
        self.waivers_file = self.project_root / ".connascence" / "waivers.yml"
        self.audit_log = self.project_root / ".connascence" / "waiver_audit.json"
        self.logger = logging.getLogger(__name__)

        # Ensure directories exist
        self.waivers_file.parent.mkdir(parents=True, exist_ok=True)

        # Load existing waivers
        self.waivers: List[WaiverRule] = self._load_waivers()

    def _load_waivers(self) -> List[WaiverRule]:
        """Load waivers from YAML configuration."""
        if not self.waivers_file.exists():
            self._create_default_waivers_config()
            return []

        try:
            with open(self.waivers_file, encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if not data or "waivers" not in data:
                return []

            waivers = []
            for waiver_data in data["waivers"]:
                # Convert metadata if present
                metadata = None
                if "metadata" in waiver_data:
                    metadata = WaiverMetadata(**waiver_data["metadata"])
                    waiver_data["metadata"] = metadata

                # Convert enums
                waiver_data["scope"] = WaiverScope(waiver_data.get("scope", "finding"))
                waiver_data["status"] = WaiverStatus(waiver_data.get("status", "pending"))

                waivers.append(WaiverRule(**waiver_data))

            return waivers

        except Exception as e:
            self.logger.error(f"Failed to load waivers: {e}")
            return []

    def _save_waivers(self) -> bool:
        """Save waivers to YAML configuration."""
        try:
            # Convert to serializable format
            waivers_data = []
            for waiver in self.waivers:
                data = asdict(waiver)
                data["scope"] = waiver.scope.value
                data["status"] = waiver.status.value
                if data["metadata"]:
                    # Keep metadata as dict
                    pass
                waivers_data.append(data)

            config = {"version": "1.0", "updated_at": datetime.now().isoformat(), "waivers": waivers_data}

            with open(self.waivers_file, "w", encoding="utf-8") as f:
                yaml.safe_dump(config, f, default_flow_style=False, sort_keys=False)

            return True

        except Exception as e:
            self.logger.error(f"Failed to save waivers: {e}")
            return False

    def _create_default_waivers_config(self):
        """Create default waivers.yml configuration."""
        default_config = {
            "version": "1.0",
            "description": "Connascence Safety Analyzer - Waiver Configuration",
            "created_at": datetime.now().isoformat(),
            "waivers": [
                {
                    "id": "example-rule-waiver",
                    "scope": "rule",
                    "pattern": "connascence_of_naming",
                    "reason": "Legacy code cleanup in progress",
                    "justification": "Temporary waiver during refactoring sprint",
                    "expires_at": (datetime.now() + timedelta(days=90)).isoformat(),
                    "status": "pending",
                    "metadata": {
                        "created_by": "system",
                        "created_at": datetime.now().isoformat(),
                        "jira_ticket": "ENG-1234",
                    },
                }
            ],
        }

        try:
            with open(self.waivers_file, "w", encoding="utf-8") as f:
                yaml.safe_dump(default_config, f, default_flow_style=False, sort_keys=False)
        except Exception as e:
            self.logger.error(f"Failed to create default waivers config: {e}")

    def create_waiver(
        self,
        scope: WaiverScope,
        pattern: str,
        reason: str,
        justification: str,
        expires_days: Optional[int] = None,
        created_by: str = "unknown",
        jira_ticket: Optional[str] = None,
    ) -> WaiverRule:
        """Create a new waiver rule."""

        waiver_id = f"waiver-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{len(self.waivers) + 1}"

        expires_at = None
        if expires_days:
            expires_at = (datetime.now() + timedelta(days=expires_days)).isoformat()

        metadata = WaiverMetadata(created_by=created_by, created_at=datetime.now().isoformat(), jira_ticket=jira_ticket)

        waiver = WaiverRule(
            id=waiver_id,
            scope=scope,
            pattern=pattern,
            reason=reason,
            justification=justification,
            expires_at=expires_at,
            status=WaiverStatus.PENDING,
            metadata=metadata,
        )

        self.waivers.append(waiver)
        self._save_waivers()
        self._log_audit_event("waiver_created", waiver_id, created_by, {"reason": reason})

        return waiver

    def approve_waiver(self, waiver_id: str, approved_by: str, notes: Optional[str] = None) -> bool:
        """Approve a pending waiver."""
        waiver = self.get_waiver_by_id(waiver_id)
        if not waiver:
            return False

        waiver.status = WaiverStatus.APPROVED
        if waiver.metadata:
            waiver.metadata.approved_by = approved_by
            waiver.metadata.approved_at = datetime.now().isoformat()
            waiver.metadata.review_notes = notes

        self._save_waivers()
        self._log_audit_event("waiver_approved", waiver_id, approved_by, {"notes": notes})

        return True

    def reject_waiver(self, waiver_id: str, rejected_by: str, notes: Optional[str] = None) -> bool:
        """Reject a pending waiver."""
        waiver = self.get_waiver_by_id(waiver_id)
        if not waiver:
            return False

        waiver.status = WaiverStatus.REJECTED
        if waiver.metadata:
            waiver.metadata.approved_by = rejected_by  # Track who rejected
            waiver.metadata.approved_at = datetime.now().isoformat()
            waiver.metadata.review_notes = notes

        self._save_waivers()
        self._log_audit_event("waiver_rejected", waiver_id, rejected_by, {"notes": notes})

        return True

    def get_waiver_by_id(self, waiver_id: str) -> Optional[WaiverRule]:
        """Get waiver by ID."""
        for waiver in self.waivers:
            if waiver.id == waiver_id:
                return waiver
        return None

    def is_violation_waived(self, violation_fingerprint: str, file_path: str, rule_type: str) -> Optional[WaiverRule]:
        """Check if a violation is covered by an active waiver."""
        for waiver in self.waivers:
            if waiver.matches_violation(violation_fingerprint, file_path, rule_type):
                return waiver
        return None

    def get_active_waivers(self) -> List[WaiverRule]:
        """Get all active (approved, non-expired) waivers."""
        return [
            w
            for w in self.waivers
            if w.status in [WaiverStatus.APPROVED, WaiverStatus.AUTO_APPROVED] and not w.is_expired()
        ]

    def get_expired_waivers(self) -> List[WaiverRule]:
        """Get all expired waivers."""
        expired = []
        for waiver in self.waivers:
            if waiver.is_expired():
                waiver.status = WaiverStatus.EXPIRED  # Update status
                expired.append(waiver)

        if expired:
            self._save_waivers()  # Save updated statuses

        return expired

    def cleanup_expired_waivers(self) -> int:
        """Remove expired waivers and return count cleaned up."""
        expired_count = 0
        active_waivers = []

        for waiver in self.waivers:
            if waiver.is_expired():
                expired_count += 1
                self._log_audit_event("waiver_expired", waiver.id, "system", {"reason": "automatic_cleanup"})
            else:
                active_waivers.append(waiver)

        self.waivers = active_waivers
        if expired_count > 0:
            self._save_waivers()

        return expired_count

    def get_waiver_statistics(self) -> Dict[str, Any]:
        """Get comprehensive waiver statistics."""
        total = len(self.waivers)
        by_status = {}
        by_scope = {}
        expiring_soon = 0

        for waiver in self.waivers:
            # Count by status
            status = waiver.status.value
            by_status[status] = by_status.get(status, 0) + 1

            # Count by scope
            scope = waiver.scope.value
            by_scope[scope] = by_scope.get(scope, 0) + 1

            # Check if expiring soon (within 7 days)
            if waiver.expires_at and waiver.expires_at != "never":
                try:
                    expiry_date = datetime.fromisoformat(waiver.expires_at)
                    if datetime.now() <= expiry_date <= datetime.now() + timedelta(days=7):
                        expiring_soon += 1
                except ValueError:
                    pass

        return {
            "total_waivers": total,
            "by_status": by_status,
            "by_scope": by_scope,
            "expiring_soon": expiring_soon,
            "active_waivers": len(self.get_active_waivers()),
        }

    def _log_audit_event(self, event_type: str, waiver_id: str, user: str, details: Dict[str, Any]):
        """Log audit event for waiver operations."""
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "waiver_id": waiver_id,
            "user": user,
            "details": details,
        }

        try:
            # Load existing audit log
            audit_events = []
            if self.audit_log.exists():
                with open(self.audit_log, encoding="utf-8") as f:
                    audit_events = json.load(f)

            # Add new event
            audit_events.append(event)

            # Keep only last 1000 events
            if len(audit_events) > 1000:
                audit_events = audit_events[-1000:]

            # Save updated log
            with open(self.audit_log, "w", encoding="utf-8") as f:
                json.dump(audit_events, f, indent=2)

        except Exception as e:
            self.logger.error(f"Failed to log audit event: {e}")

    def export_waivers_report(self) -> Dict[str, Any]:
        """Export comprehensive waivers report for compliance."""
        stats = self.get_waiver_statistics()
        expired = self.get_expired_waivers()
        active = self.get_active_waivers()

        return {
            "report_generated_at": datetime.now().isoformat(),
            "statistics": stats,
            "active_waivers": [asdict(w) for w in active],
            "expired_waivers": [asdict(w) for w in expired],
            "pending_approval": [asdict(w) for w in self.waivers if w.status == WaiverStatus.PENDING],
        }


# Legacy compatibility
class Waiver:
    """Legacy waiver class for backward compatibility."""

    def __init__(self, violation_id, reason, status=WaiverStatus.PENDING):
        self.violation_id = violation_id
        self.reason = reason
        self.status = status


class WaiverSystem:
    """Legacy waiver system for backward compatibility."""

    def __init__(self):
        self.waivers = []
        self.enhanced_system = EnhancedWaiverSystem()

    def request_waiver(self, violation_id, reason):
        waiver = Waiver(violation_id, reason)
        self.waivers.append(waiver)
        return waiver
