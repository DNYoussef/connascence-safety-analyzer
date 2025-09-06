#!/usr/bin/env python3
"""
Refactored example showing improved coupling and design.
This demonstrates how to address connascence violations.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional
import time


class UserStatus(Enum):
    """Eliminates magic numbers through named constants."""
    PENDING = "pending"
    ACTIVE = "active" 
    PREMIUM = "premium"
    INACTIVE = "inactive"


class Permission(Enum):
    """Clear permission definitions."""
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"


@dataclass
class User:
    """Immutable user data with clear structure."""
    user_id: int
    name: str
    age: int
    email: str
    status: UserStatus
    created_at: int
    permissions: List[Permission]


class EmailValidator:
    """Single responsibility for email validation."""
    
    MIN_EMAIL_LENGTH = 5
    MAX_EMAIL_LENGTH = 254
    
    @classmethod
    def is_valid(cls, email: str) -> bool:
        """Comprehensive email validation with clear rules."""
        if not email or len(email) < cls.MIN_EMAIL_LENGTH:
            return False
        if len(email) > cls.MAX_EMAIL_LENGTH:
            return False
        if email.count('@') != 1:
            return False
        
        local, domain = email.split('@')
        return len(local) > 0 and '.' in domain and len(domain.split('.')) >= 2


class PermissionManager:
    """Handles permission logic separately from user management."""
    
    DEFAULT_PERMISSIONS = {
        UserStatus.PENDING: [Permission.READ],
        UserStatus.ACTIVE: [Permission.READ, Permission.WRITE],
        UserStatus.PREMIUM: [Permission.READ, Permission.WRITE, Permission.ADMIN],
        UserStatus.INACTIVE: []
    }
    
    @classmethod
    def get_default_permissions(cls, status: UserStatus) -> List[Permission]:
        """Get default permissions for user status."""
        return cls.DEFAULT_PERMISSIONS.get(status, [])


class UserRepository:
    """Focused on user data management only."""
    
    def __init__(self):
        self._users: Dict[int, User] = {}
        self._next_id = 1
    
    def save_user(self, user: User) -> None:
        """Save user to storage."""
        self._users[user.user_id] = user
    
    def get_user(self, user_id: int) -> Optional[User]:
        """Retrieve user by ID."""
        return self._users.get(user_id)
    
    def get_all_users(self) -> Dict[int, User]:
        """Get all users."""
        return self._users.copy()
    
    def get_next_id(self) -> int:
        """Get next available user ID."""
        current_id = self._next_id
        self._next_id += 1
        return current_id


class UserService:
    """Clean user service with single responsibility."""
    
    MIN_AGE = 0
    MAX_AGE = 150
    
    def __init__(self, repository: UserRepository):
        self._repository = repository
    
    def create_user(self, name: str, age: int, email: str, status: UserStatus) -> Optional[int]:
        """Create a new user with validation."""
        if not self._validate_age(age):
            return None
        
        if not EmailValidator.is_valid(email):
            return None
            
        user_id = self._repository.get_next_id()
        permissions = PermissionManager.get_default_permissions(status)
        
        user = User(
            user_id=user_id,
            name=name,
            age=age,
            email=email,
            status=status,
            created_at=int(time.time()),
            permissions=permissions
        )
        
        self._repository.save_user(user)
        return user_id
    
    def _validate_age(self, age: int) -> bool:
        """Validate age within acceptable range."""
        return self.MIN_AGE <= age <= self.MAX_AGE


@dataclass
class UserStats:
    """Clear return type for statistics."""
    total_count: int
    average_age: float
    active_count: int


class UserAnalytics:
    """Separate service for user analytics."""
    
    def __init__(self, repository: UserRepository):
        self._repository = repository
    
    def calculate_stats(self, include_inactive: bool = True) -> UserStats:
        """Calculate user statistics with clear parameters."""
        all_users = self._repository.get_all_users()
        
        if include_inactive:
            filtered_users = list(all_users.values())
        else:
            filtered_users = [
                user for user in all_users.values() 
                if user.status != UserStatus.INACTIVE
            ]
        
        if not filtered_users:
            return UserStats(0, 0.0, 0)
        
        total_count = len(filtered_users)
        average_age = sum(user.age for user in filtered_users) / total_count
        active_count = sum(
            1 for user in filtered_users 
            if user.status in [UserStatus.ACTIVE, UserStatus.PREMIUM]
        )
        
        return UserStats(total_count, average_age, active_count)