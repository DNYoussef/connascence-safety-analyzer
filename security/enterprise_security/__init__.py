
from enum import Enum

class UserRole(Enum):
    VIEWER = 'viewer'
    ANALYST = 'analyst'
    DEVELOPER = 'developer'
    AUDITOR = 'auditor'
    SECURITY_OFFICER = 'security_officer'
    ADMIN = 'admin'

class SecurityManager:
    def __init__(self, air_gapped=False):
        self.air_gapped = air_gapped
        
    def authenticate_user(self, username, password, ip):
        # Mock authentication
        from dataclasses import dataclass
        @dataclass
        class AuthContext:
            username: str
            roles: list = None
            def __post_init__(self):
                if self.roles is None:
                    self.roles = []
        return AuthContext(username)
        
    def check_permission(self, context, resource, action):
        return resource == "analysis" and UserRole.ANALYST in context.roles
        
    def _verify_credentials(self, username, password):
        return True
