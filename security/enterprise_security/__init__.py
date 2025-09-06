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
