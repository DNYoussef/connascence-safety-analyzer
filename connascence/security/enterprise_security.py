"""Minimal enterprise security façade for integration testing."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List


class UserRole(str, Enum):
    ANALYST = "analyst"
    ADMIN = "admin"
    AUDITOR = "auditor"


@dataclass
class SecurityContext:
    username: str
    roles: List[UserRole] = field(default_factory=list)
    ip_address: str = "0.0.0.0"


class SecurityManager:
    """Provide a predictable interface for the integration tests."""

    def __init__(self, *, air_gapped: bool = False) -> None:
        self.air_gapped = air_gapped

    # ------------------------------------------------------------------
    # Authentication helpers
    # ------------------------------------------------------------------
    def authenticate_user(self, username: str, password: str, ip_address: str) -> SecurityContext:
        if not self._verify_credentials(username, password):
            raise PermissionError("Invalid credentials")

        context = SecurityContext(username=username, roles=[UserRole.ANALYST], ip_address=ip_address)
        return context

    def _verify_credentials(self, username: str, password: str) -> bool:
        return bool(username and password)

    # ------------------------------------------------------------------
    # Authorization helpers
    # ------------------------------------------------------------------
    def check_permission(self, context: SecurityContext, domain: str, action: str) -> bool:
        if UserRole.ADMIN in context.roles:
            return True

        if domain == "analysis" and action in {"execute", "view"}:
            return UserRole.ANALYST in context.roles

        return False

    # ------------------------------------------------------------------
    # Health checks
    # ------------------------------------------------------------------
    def get_status(self) -> dict:
        return {"air_gapped": self.air_gapped, "services": ["auth", "policy", "telemetry"]}

    def list_roles(self) -> List[UserRole]:
        return list(UserRole)
