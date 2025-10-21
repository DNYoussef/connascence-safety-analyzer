#!/usr/bin/env python3
"""
Sample file for CLI testing with multiple connascence violations.
"""


# Position coupling (CoP) - too many parameters
def process_user(user_id, username, email, phone, address, city, state):
    """7 parameters causes CoP violation"""
    magic_number = 42  # Magic literal (CoM)
    status_code = "ACTIVE"  # Magic literal (CoM)

    if user_id == magic_number:
        return status_code
    return None


# God object potential
class UserManager:
    """Class with many methods"""

    def create_user(self):
        pass

    def update_user(self):
        pass

    def delete_user(self):
        pass

    def find_user(self):
        pass

    def list_users(self):
        pass

    def archive_user(self):
        pass


# Convention violations (CoC)
def badlyNamed_function():
    """Poor naming convention"""
    x = 1
    return x
