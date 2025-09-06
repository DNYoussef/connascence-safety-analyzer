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
Secure Authentication Utilities

Provides secure password hashing, validation, and authentication utilities
to replace insecure plain text password comparisons throughout the system.
"""

from datetime import datetime, timedelta
import logging
import re
import secrets
from typing import Any, Dict, Optional

import bcrypt

logger = logging.getLogger(__name__)


class SecurePasswordManager:
    """Secure password management with bcrypt hashing."""

    # Password complexity requirements
    MIN_LENGTH = 8
    MAX_LENGTH = 128
    REQUIRE_UPPERCASE = True
    REQUIRE_LOWERCASE = True
    REQUIRE_DIGITS = True
    REQUIRE_SPECIAL = True

    def __init__(self, cost_factor: int = 12):
        """Initialize password manager with bcrypt cost factor."""
        self.cost_factor = cost_factor

    @staticmethod
    def generate_secure_password(length: int = 16) -> str:
        """Generate a cryptographically secure password."""
        if length < SecurePasswordManager.MIN_LENGTH:
            length = SecurePasswordManager.MIN_LENGTH
        if length > SecurePasswordManager.MAX_LENGTH:
            length = SecurePasswordManager.MAX_LENGTH

        # Character sets for password generation
        lowercase = 'abcdefghijklmnopqrstuvwxyz'
        uppercase = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        digits = '0123456789'
        special = '!@#$%^&*()_+-=[]{}|;:,.<>?'

        # Ensure at least one character from each required set
        password_chars = [
            secrets.choice(lowercase),
            secrets.choice(uppercase),
            secrets.choice(digits),
            secrets.choice(special)
        ]

        # Fill remaining length with random characters from all sets
        all_chars = lowercase + uppercase + digits + special
        for _ in range(length - 4):
            password_chars.append(secrets.choice(all_chars))

        # Shuffle the password characters
        secrets.SystemRandom().shuffle(password_chars)

        return ''.join(password_chars)

    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt with secure salt."""
        # Validate password first
        if not self.validate_password_strength(password):
            raise ValueError("Password does not meet security requirements")

        # Generate salt and hash password
        salt = bcrypt.gensalt(rounds=self.cost_factor)
        password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)

        return password_hash.decode('utf-8')

    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against bcrypt hash with timing attack protection."""
        try:
            password_bytes = password.encode('utf-8')
            hash_bytes = password_hash.encode('utf-8')

            # bcrypt.checkpw provides timing attack protection
            return bcrypt.checkpw(password_bytes, hash_bytes)

        except Exception as e:
            logger.warning(f"Password verification failed: {e}")
            return False

    def validate_password_strength(self, password: str) -> bool:
        """Validate password meets security requirements."""
        if not password:
            return False

        # Check length requirements
        if len(password) < self.MIN_LENGTH or len(password) > self.MAX_LENGTH:
            return False

        # Check complexity requirements
        if self.REQUIRE_UPPERCASE and not re.search(r'[A-Z]', password):
            return False
        if self.REQUIRE_LOWERCASE and not re.search(r'[a-z]', password):
            return False
        if self.REQUIRE_DIGITS and not re.search(r'\d', password):
            return False
        if self.REQUIRE_SPECIAL and not re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>?]', password):
            return False

        # Check for common weak patterns
        weak_patterns = [
            r'(.)\1{3,}',  # Repeated characters (aaaa)
            r'(abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz)',  # Sequential letters
            r'(123|234|345|456|567|678|789|890)',  # Sequential numbers
            r'(password|admin|user|test|guest|123456|qwerty)',  # Common passwords
        ]

        password_lower = password.lower()
        return all(not re.search(pattern, password_lower, re.IGNORECASE) for pattern in weak_patterns)

    def get_password_strength_score(self, password: str) -> Dict[str, Any]:
        """Get detailed password strength analysis."""
        score = 0
        feedback = []

        if not password:
            return {'score': 0, 'strength': 'invalid', 'feedback': ['Password is required']}

        # Length scoring
        length = len(password)
        if length >= 12:
            score += 25
        elif length >= 8:
            score += 15
        else:
            feedback.append(f"Password too short ({length} chars). Minimum 8 required.")

        # Character variety scoring
        if re.search(r'[A-Z]', password):
            score += 15
        else:
            feedback.append("Add uppercase letters")

        if re.search(r'[a-z]', password):
            score += 15
        else:
            feedback.append("Add lowercase letters")

        if re.search(r'\d', password):
            score += 15
        else:
            feedback.append("Add numbers")

        if re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>?]', password):
            score += 15
        else:
            feedback.append("Add special characters")

        # Bonus points for extra length and variety
        if length >= 16:
            score += 10
        if len(set(password)) > length * 0.7:  # High character variety
            score += 5

        # Deduct points for weak patterns
        weak_checks = [
            (r'(.)\1{3,}', -10, "Avoid repeated characters"),
            (r'(abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz)', -15, "Avoid sequential letters"),
            (r'(123|234|345|456|567|678|789|890)', -15, "Avoid sequential numbers"),
            (r'(password|admin|user|test|guest|123456|qwerty)', -25, "Avoid common passwords"),
        ]

        for pattern, penalty, message in weak_checks:
            if re.search(pattern, password.lower(), re.IGNORECASE):
                score += penalty
                feedback.append(message)

        # Normalize score to 0-100
        score = max(0, min(100, score))

        # Determine strength level
        if score >= 80:
            strength = 'very_strong'
        elif score >= 60:
            strength = 'strong'
        elif score >= 40:
            strength = 'moderate'
        elif score >= 20:
            strength = 'weak'
        else:
            strength = 'very_weak'

        return {
            'score': score,
            'strength': strength,
            'feedback': feedback if feedback else ['Password meets security requirements']
        }


class AccountLockoutManager:
    """Manages account lockout functionality to prevent brute force attacks."""

    def __init__(self, max_attempts: int = 5, lockout_duration: int = 900):  # 15 minutes
        """Initialize lockout manager."""
        self.max_attempts = max_attempts
        self.lockout_duration = lockout_duration
        self.failed_attempts: Dict[str, Dict] = {}

    def record_failed_attempt(self, username: str, ip_address: str) -> None:
        """Record a failed login attempt."""
        now = datetime.now(datetime.UTC)

        if username not in self.failed_attempts:
            self.failed_attempts[username] = {
                'count': 0,
                'last_attempt': now,
                'locked_until': None,
                'ip_addresses': set()
            }

        self.failed_attempts[username]['count'] += 1
        self.failed_attempts[username]['last_attempt'] = now
        self.failed_attempts[username]['ip_addresses'].add(ip_address)

        # Lock account if max attempts exceeded
        if self.failed_attempts[username]['count'] >= self.max_attempts:
            self.failed_attempts[username]['locked_until'] = now + timedelta(seconds=self.lockout_duration)

            logger.warning(f"Account locked: {username} after {self.max_attempts} failed attempts")

    def record_successful_attempt(self, username: str) -> None:
        """Record successful login and reset failed attempts."""
        if username in self.failed_attempts:
            del self.failed_attempts[username]

    def is_account_locked(self, username: str) -> bool:
        """Check if account is currently locked."""
        if username not in self.failed_attempts:
            return False

        locked_until = self.failed_attempts[username].get('locked_until')
        if not locked_until:
            return False

        # Check if lockout period has expired
        if datetime.now(datetime.UTC) > locked_until:
            # Clear lockout
            del self.failed_attempts[username]
            return False

        return True

    def get_lockout_info(self, username: str) -> Optional[Dict[str, Any]]:
        """Get lockout information for a user."""
        if username not in self.failed_attempts:
            return None

        attempt_info = self.failed_attempts[username]
        locked_until = attempt_info.get('locked_until')

        return {
            'failed_attempts': attempt_info['count'],
            'last_attempt': attempt_info['last_attempt'],
            'is_locked': self.is_account_locked(username),
            'locked_until': locked_until,
            'time_remaining': (locked_until - datetime.now(datetime.UTC)).total_seconds() if locked_until and locked_until > datetime.now(datetime.UTC) else 0
        }


# Secure password validation decorator
def require_secure_password(func):
    """Decorator to ensure password meets security requirements."""
    def wrapper(*args, **kwargs):
        password_manager = SecurePasswordManager()

        # Look for password in args or kwargs
        password = None
        if 'password' in kwargs:
            password = kwargs['password']
        elif len(args) > 1:
            password = args[1]  # Assume second arg is password

        if password and not password_manager.validate_password_strength(password):
            raise ValueError("Password does not meet security requirements")

        return func(*args, **kwargs)

    return wrapper


# Example secure user storage (for demonstration)
class SecureUserStore:
    """Secure user storage with proper password hashing."""

    def __init__(self):
        self.password_manager = SecurePasswordManager()
        self.lockout_manager = AccountLockoutManager()

        # Example secure users with bcrypt hashes
        self.users = {
            "admin": {
                "user_id": "admin-001",
                "password_hash": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeOfMxqfW5gJCx3WK",  # SecureAdmin2024!
                "roles": ["admin"],
                "security_clearance": "top_secret",
                "created_at": datetime.now(datetime.UTC),
                "last_login": None
            },
            "analyst": {
                "user_id": "analyst-001",
                "password_hash": "$2b$12$8K7Qv.VL6i3K8mHxE9y2eO5qR9sT4uP2wX6zB8cF1aG4hJ7kL9mN0",  # AnalystPass2024!
                "roles": ["analyst"],
                "security_clearance": "confidential",
                "created_at": datetime.now(datetime.UTC),
                "last_login": None
            }
        }

    def authenticate_user(self, username: str, password: str, ip_address: str) -> Optional[Dict[str, Any]]:
        """Authenticate user with secure password verification."""
        # Check account lockout first
        if self.lockout_manager.is_account_locked(username):
            logger.warning(f"Authentication blocked: Account {username} is locked")
            return None

        user_data = self.users.get(username)
        if not user_data:
            # Still record failed attempt even for non-existent users
            self.lockout_manager.record_failed_attempt(username, ip_address)
            return None

        # Verify password
        if self.password_manager.verify_password(password, user_data['password_hash']):
            # Successful authentication
            self.lockout_manager.record_successful_attempt(username)
            user_data['last_login'] = datetime.now(datetime.UTC)

            logger.info(f"Successful authentication for user: {username}")
            return user_data
        else:
            # Failed authentication
            self.lockout_manager.record_failed_attempt(username, ip_address)
            logger.warning(f"Failed authentication attempt for user: {username} from IP: {ip_address}")
            return None

    @require_secure_password
    def create_user(self, username: str, password: str, **user_data) -> bool:
        """Create new user with secure password hashing."""
        if username in self.users:
            return False

        password_hash = self.password_manager.hash_password(password)

        self.users[username] = {
            "user_id": f"{username}-{secrets.token_hex(4)}",
            "password_hash": password_hash,
            "created_at": datetime.now(datetime.UTC),
            "last_login": None,
            **user_data
        }

        logger.info(f"Created new user: {username}")
        return True
