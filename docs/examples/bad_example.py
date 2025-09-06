#!/usr/bin/env python3
"""
Example file with multiple connascence violations for demonstration.
This file intentionally contains common coupling issues.
"""


# Connascence of Name - inconsistent naming
class UserMgr:
    def __init__(self):
        self.data = {}
        self.cnt = 0  # Magic abbreviation

    # Connascence of Position - parameter order matters
    def create_user(self, name, age, email, status):
        # Magic numbers - Connascence of Value
        if age > 150 or age < 0:
            return False
        if status not in [1, 2, 3, 4]:  # Magic numbers
            return False

        # God object violation - too many responsibilities
        user_id = self.cnt + 1
        self.data[user_id] = {
            'name': name,
            'age': age,
            'email': email,
            'status': status,
            'created': self._get_timestamp(),
            'validated': self._validate_email(email),
            'permissions': self._get_default_permissions(status)
        }
        self.cnt += 1
        return user_id

    def _get_timestamp(self):
        import time
        return int(time.time())

    def _validate_email(self, email):
        # Connascence of Algorithm - duplicate validation logic
        return '@' in email and '.' in email

    def _get_default_permissions(self, status):
        # Connascence of Value - magic status codes
        if status == 1:
            return ['read']
        elif status == 2:
            return ['read', 'write']
        elif status == 3:
            return ['read', 'write', 'admin']
        else:
            return []

# Separate class with duplicate validation
class EmailValidator:
    @staticmethod
    def is_valid(email):
        # Connascence of Algorithm - same logic as above
        return '@' in email and '.' in email

# Function with parameter coupling
def calculate_stats(users, include_inactive, sort_by_age, reverse_sort):
    # Connascence of Position and complex parameter interdependence
    results = []
    for user in users.values():
        if not include_inactive and user['status'] == 4:  # Magic number again
            continue
        results.append(user)

    if sort_by_age:
        results.sort(key=lambda x: x['age'], reverse=reverse_sort)

    return len(results), sum(u['age'] for u in results) / len(results) if results else 0
