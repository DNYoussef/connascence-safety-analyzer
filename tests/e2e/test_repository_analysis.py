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
End-to-End Repository Analysis Tests

Tests real repository analysis workflows with various project types.
Uses memory coordination for tracking analysis patterns and performance.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import time
from typing import Any, Dict, List, Optional

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from cli.connascence import ConnascenceCLI
from tests.e2e.test_cli_workflows import SequentialWorkflowValidator


class RepositoryAnalysisCoordinator:
    """Specialized memory coordinator for repository analysis scenarios."""

    def __init__(self):
        self.repository_profiles = {}
        self.analysis_patterns = {}
        self.framework_detections = {}
        self.violation_densities = {}
        self.complexity_metrics = {}
        self.repository_comparisons = {}
        self.test_scenarios = {}
        self.performance_metrics = {}

    def store_repository_profile(self, repo_id: str, profile: Dict[str, Any]):
        """Store repository analysis profile."""
        self.repository_profiles[repo_id] = {"profile": profile, "timestamp": time.time(), "analysis_completed": False}

    def store_analysis_pattern(self, repo_id: str, patterns: Dict[str, Any]):
        """Store detected connascence patterns for repository."""
        self.analysis_patterns[repo_id] = patterns

    def store_framework_detection(
        self, repo_id: str, frameworks: List[str], framework_specific_violations: Dict[str, List]
    ):
        """Store framework detection results."""
        self.framework_detections[repo_id] = {
            "detected_frameworks": frameworks,
            "framework_violations": framework_specific_violations,
            "timestamp": time.time(),
        }

    def store_violation_density(self, repo_id: str, density_metrics: Dict[str, float]):
        """Store violation density metrics."""
        self.violation_densities[repo_id] = density_metrics

    def store_complexity_metrics(self, repo_id: str, metrics: Dict[str, Any]):
        """Store complexity analysis metrics."""
        self.complexity_metrics[repo_id] = metrics

    def store_test_scenario(self, scenario_id: str, config: Dict[str, Any]):
        """Store test scenario configuration (compatibility with SequentialWorkflowValidator)."""
        self.test_scenarios[scenario_id] = {"config": config, "timestamp": time.time(), "status": "initialized"}

    def update_scenario_status(self, scenario_id: str, status: str, results: Optional[Dict] = None):
        """Update scenario status and results (compatibility with SequentialWorkflowValidator)."""
        if scenario_id in self.test_scenarios:
            self.test_scenarios[scenario_id]["status"] = status
            if results:
                self.test_scenarios[scenario_id]["results"] = results

    def store_performance_metrics(self, scenario_id: str, metrics: Dict[str, Any]):
        """Store performance metrics for scenario (compatibility with SequentialWorkflowValidator)."""
        self.performance_metrics[scenario_id] = metrics

    def compare_repositories(self, repo_ids: List[str]) -> Dict[str, Any]:
        """Compare multiple repository analysis results."""
        comparison = {"repositories": repo_ids, "comparison_timestamp": time.time(), "metrics": {}}

        # Mapping of metric types to actual attribute names
        metric_to_attr = {
            "violation_density": "violation_densities",
            "complexity": "complexity_metrics",
            "patterns": "analysis_patterns"
        }

        for metric_type in ["violation_density", "complexity", "patterns"]:
            comparison["metrics"][metric_type] = {}
            attr_name = metric_to_attr[metric_type]
            storage = getattr(self, attr_name, {})

            for repo_id in repo_ids:
                if repo_id in storage:
                    comparison["metrics"][metric_type][repo_id] = storage.get(repo_id, {})

        self.repository_comparisons[f"comparison_{len(self.repository_comparisons)}"] = comparison
        return comparison


# Global repository coordinator
repo_coordinator = RepositoryAnalysisCoordinator()


@pytest.fixture
def django_project_template():
    """Create Django-style project for framework-specific testing."""
    temp_dir = tempfile.mkdtemp()
    project_path = Path(temp_dir)

    # Create Django project structure
    (project_path / "myproject").mkdir()
    (project_path / "myproject" / "myproject").mkdir()
    (project_path / "myproject" / "apps").mkdir()
    (project_path / "myproject" / "apps" / "users").mkdir()
    (project_path / "myproject" / "apps" / "orders").mkdir()
    (project_path / "myproject" / "static").mkdir()
    (project_path / "myproject" / "templates").mkdir()

    # Django settings with violations
    (project_path / "myproject" / "myproject" / "settings.py").write_text(
        """
import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-your-secret-key-here-12345'  # Magic string - security violation

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'apps.users',
    'apps.orders',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'myproject.urls'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,  # Magic literal
        }
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Cache configuration
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'TIMEOUT': 300,  # Magic literal - cache timeout
        'OPTIONS': {
            'MAX_ENTRIES': 1000,  # Magic literal
        }
    }
}

# Email configuration
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = 'noreply@example.com'  # Magic string
EMAIL_TIMEOUT = 30  # Magic literal

# Security settings with magic values
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SESSION_COOKIE_SECURE = False  # Should be True in production
CSRF_COOKIE_SECURE = False    # Should be True in production
SESSION_COOKIE_AGE = 1209600  # Magic literal - 2 weeks in seconds
"""
    )

    # Django models with violations
    (project_path / "myproject" / "apps" / "users" / "models.py").write_text(
        """
from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    '''User model with connascence violations.'''

    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30)  # Magic literal
    last_name = models.CharField(max_length=30)   # Magic literal
    phone = models.CharField(max_length=15, blank=True)  # Magic literal
    birth_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        db_table = 'users_customuser'
        verbose_name = 'User'
        verbose_name_plural = 'Users'


class UserProfile(models.Model):
    '''Profile model with violations.'''

    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    bio = models.TextField(max_length=500, blank=True)  # Magic literal
    location = models.CharField(max_length=100, blank=True)  # Magic literal
    website = models.URLField(max_length=200, blank=True)  # Magic literal
    avatar = models.ImageField(upload_to='avatars/', blank=True)

    # Magic string and literals
    default_theme = models.CharField(
        max_length=20,  # Magic literal
        default='light',  # Magic string
        choices=[
            ('light', 'Light Theme'),  # Magic strings
            ('dark', 'Dark Theme'),    # Magic strings
            ('auto', 'Auto Theme'),    # Magic strings
        ]
    )

    notification_preferences = models.JSONField(default=dict)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    login_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.user.username} Profile"

    class Meta:
        db_table = 'users_userprofile'
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
"""
    )

    # Django views with parameter bombs and violations
    (project_path / "myproject" / "apps" / "users" / "views.py").write_text(
        """
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json

from .models import CustomUser, UserProfile


def register_user(request, username, email, password, first_name, last_name, phone):
    '''Registration function with parameter bomb violation.'''
    if request.method == 'POST':
        # Magic strings and literals throughout
        if len(password) < 8:  # Magic literal
            messages.error(request, 'Password must be at least 8 characters')
            return render(request, 'registration/register.html')

        if len(username) < 3:  # Magic literal
            messages.error(request, 'Username must be at least 3 characters')
            return render(request, 'registration/register.html')

        if '@' not in email:  # Magic string
            messages.error(request, 'Invalid email format')
            return render(request, 'registration/register.html')

        try:
            user = CustomUser.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )

            # Create profile with magic values
            profile = UserProfile.objects.create(
                user=user,
                bio="New user",  # Magic string
                default_theme="light",  # Magic string
                login_count=0  # Magic literal
            )

            messages.success(request, 'Registration successful!')
            return redirect('login')

        except Exception as e:
            messages.error(request, f'Registration failed: {str(e)}')
            return render(request, 'registration/register.html')

    return render(request, 'registration/register.html')


def validate_user_data(request, user_id, email, phone, age, status, preferences):
    '''Validation function with parameter bomb and meaning violations.'''

    # Magic literals and complex conditions
    if age < 13:  # Magic literal - COPPA compliance
        return JsonResponse({
            'valid': False,
            'error': 'User must be at least 13 years old'  # Magic string
        })

    if age > 120:  # Magic literal
        return JsonResponse({
            'valid': False,
            'error': 'Invalid age'  # Magic string
        })

    # Email validation with magic strings
    if '@' not in email or '.' not in email:  # Magic strings
        return JsonResponse({
            'valid': False,
            'error': 'Invalid email format'  # Magic string
        })

    # Phone validation with magic patterns
    if phone and len(phone) < 10:  # Magic literal
        return JsonResponse({
            'valid': False,
            'error': 'Phone number too short'  # Magic string
        })

    # Status validation with magic strings
    valid_statuses = ['active', 'inactive', 'pending', 'suspended']  # Magic strings
    if status not in valid_statuses:
        return JsonResponse({
            'valid': False,
            'error': 'Invalid status'  # Magic string
        })

    return JsonResponse({'valid': True})


@login_required
def update_user_profile(request, user_id, bio, location, website, theme, notifications, privacy_level):
    '''Profile update with parameter bomb and algorithm connascence.'''

    user = get_object_or_404(CustomUser, id=user_id)
    profile, created = UserProfile.objects.get_or_create(user=user)

    # Complex validation logic with magic values
    if bio and len(bio) > 500:  # Magic literal
        messages.error(request, 'Bio too long (max 500 characters)')  # Magic string
        return redirect('profile')

    if location and len(location) > 100:  # Magic literal
        messages.error(request, 'Location too long (max 100 characters)')  # Magic string
        return redirect('profile')

    if website:
        if not website.startswith('http://') and not website.startswith('https://'):  # Magic strings
            website = f'https://{website}'  # Magic string

        if len(website) > 200:  # Magic literal
            messages.error(request, 'Website URL too long')  # Magic string
            return redirect('profile')

    # Theme validation with magic strings
    valid_themes = ['light', 'dark', 'auto']  # Magic strings
    if theme not in valid_themes:
        theme = 'light'  # Magic string default

    # Privacy level validation with magic numbers and algorithm connascence
    if privacy_level == 1:  # Magic literal - public
        can_view_profile = True
        can_view_email = True
        can_view_phone = True
    elif privacy_level == 2:  # Magic literal - friends only
        can_view_profile = True
        can_view_email = False
        can_view_phone = False
    elif privacy_level == 3:  # Magic literal - private
        can_view_profile = False
        can_view_email = False
        can_view_phone = False
    else:
        privacy_level = 2  # Magic literal default
        can_view_profile = True
        can_view_email = False
        can_view_phone = False

    # Update profile with validated data
    profile.bio = bio
    profile.location = location
    profile.website = website
    profile.default_theme = theme
    profile.save()

    messages.success(request, 'Profile updated successfully!')  # Magic string
    return redirect('profile')


class UserManagementView:
    '''God class with too many methods - algorithm connascence.'''

    def __init__(self):
        self.cache_timeout = 300  # Magic literal
        self.max_login_attempts = 5  # Magic literal
        self.password_min_length = 8  # Magic literal

    def authenticate_user(self, username, password):  # Missing type hints
        pass

    def validate_password(self, password):  # Missing type hints
        pass

    def check_login_attempts(self, user_id):  # Missing type hints
        pass

    def reset_password(self, user_id):  # Missing type hints
        pass

    def send_verification_email(self, user_id):  # Missing type hints
        pass

    def verify_email_token(self, token):  # Missing type hints
        pass

    def update_last_login(self, user_id):  # Missing type hints
        pass

    def log_user_activity(self, user_id, activity):  # Missing type hints
        pass

    def check_user_permissions(self, user_id, permission):  # Missing type hints
        pass

    def assign_user_role(self, user_id, role):  # Missing type hints
        pass

    def remove_user_role(self, user_id, role):  # Missing type hints
        pass

    def get_user_statistics(self, user_id):  # Missing type hints
        pass

    def export_user_data(self, user_id):  # Missing type hints
        pass

    def import_users_batch(self, users_data):  # Missing type hints
        pass

    def deactivate_user(self, user_id):  # Missing type hints
        pass

    def reactivate_user(self, user_id):  # Missing type hints
        pass

    def delete_user_account(self, user_id):  # Missing type hints
        pass

    def backup_user_data(self, user_id):  # Missing type hints
        pass

    def restore_user_data(self, user_id, backup_id):  # Missing type hints
        pass

    def generate_user_report(self, user_id):  # Missing type hints
        pass

    def audit_user_changes(self, user_id):  # Missing type hints
        pass

    def sync_user_external(self, user_id, external_id):  # Missing type hints
        pass

    def validate_user_compliance(self, user_id):  # Missing type hints
        pass

    def process_user_gdpr_request(self, user_id, request_type):  # Missing type hints
        pass

    def calculate_user_score(self, user_id):  # Missing type hints
        pass
"""
    )

    # Additional files for comprehensive analysis
    (project_path / "myproject" / "apps" / "orders" / "models.py").write_text(
        """
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Order(models.Model):
    '''Order model with various violations.'''

    STATUS_CHOICES = [
        ('pending', 'Pending'),      # Magic strings
        ('processing', 'Processing'), # Magic strings
        ('shipped', 'Shipped'),      # Magic strings
        ('delivered', 'Delivered'),  # Magic strings
        ('cancelled', 'Cancelled'),  # Magic strings
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    order_number = models.CharField(max_length=20, unique=True)  # Magic literal
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')  # Magic literals/strings
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)  # Magic literals
    shipping_cost = models.DecimalField(max_digits=8, decimal_places=2, default=0)  # Magic literals
    tax_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0)  # Magic literals

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    shipped_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    shipping_address = models.TextField(max_length=500)  # Magic literal
    billing_address = models.TextField(max_length=500)   # Magic literal

    notes = models.TextField(max_length=1000, blank=True)  # Magic literal

    def __str__(self):
        return f"Order {self.order_number}"

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'
"""
    )

    yield project_path

    # Cleanup
    import shutil

    shutil.rmtree(temp_dir)


@pytest.fixture
def flask_api_project():
    """Create Flask API project for framework detection testing."""
    temp_dir = tempfile.mkdtemp()
    project_path = Path(temp_dir)

    # Flask project structure
    (project_path / "app").mkdir()
    (project_path / "app" / "api").mkdir()
    (project_path / "app" / "models").mkdir()
    (project_path / "app" / "utils").mkdir()
    (project_path / "tests").mkdir()
    (project_path / "config").mkdir()

    # Flask app with violations
    (project_path / "app" / "__init__.py").write_text(
        """
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS

db = SQLAlchemy()
migrate = Migrate()

def create_app(config_name='development'):  # Magic string
    app = Flask(__name__)

    # Configuration with magic values
    app.config['SECRET_KEY'] = 'your-secret-key-here-12345'  # Magic string - security violation
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'  # Magic string
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = 'jwt-secret-string'  # Magic string - security violation
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 3600  # Magic literal - 1 hour
    app.config['UPLOAD_FOLDER'] = 'uploads'  # Magic string
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Magic literal - 16MB

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app)

    # Register blueprints
    from app.api import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')

    return app
"""
    )

    # Flask API routes with violations
    (project_path / "app" / "api" / "__init__.py").write_text(
        """
from flask import Blueprint

api_bp = Blueprint('api', __name__)

from . import auth, users, products
"""
    )

    (project_path / "app" / "api" / "users.py").write_text(
        """
from flask import request, jsonify, current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
import hashlib
import re

from app.api import api_bp
from app.models.user import User
from app import db


@api_bp.route('/users', methods=['POST'])
def create_user(username, email, password, full_name, phone, role):
    '''User creation with parameter bomb violation.'''

    # Magic string validations
    if len(username) < 3:  # Magic literal
        return jsonify({'error': 'Username too short (min 3 chars)'}), 400  # Magic literal/string

    if len(password) < 8:  # Magic literal
        return jsonify({'error': 'Password too short (min 8 chars)'}), 400  # Magic literal/string

    # Magic regex patterns
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'  # Magic string
    if not re.match(email_pattern, email):
        return jsonify({'error': 'Invalid email format'}), 400  # Magic string/literal

    phone_pattern = r'^\\+?1?d{9,15}$'  # Magic string
    if phone and not re.match(phone_pattern, phone):
        return jsonify({'error': 'Invalid phone format'}), 400  # Magic string/literal

    # Role validation with magic strings
    valid_roles = ['user', 'admin', 'moderator', 'guest']  # Magic strings
    if role not in valid_roles:
        role = 'user'  # Magic string default

    # Password hashing with magic values
    salt = 'fixed-salt-value'  # Magic string - security violation
    password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)  # Magic literal

    try:
        user = User(
            username=username,
            email=email,
            password_hash=password_hash,
            full_name=full_name,
            phone=phone,
            role=role,
            is_active=True,
            login_attempts=0  # Magic literal
        )

        db.session.add(user)
        db.session.commit()

        # Generate JWT token with magic expiration
        access_token = create_access_token(
            identity=user.id,
            expires_delta=timedelta(hours=24)  # Magic literal
        )

        return jsonify({
            'message': 'User created successfully',  # Magic string
            'user_id': user.id,
            'access_token': access_token
        }), 201  # Magic literal

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'User creation failed: {str(e)}')
        return jsonify({'error': 'User creation failed'}), 500  # Magic string/literal


@api_bp.route('/users/<int:user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id, username, email, full_name, phone, bio, preferences):
    '''User update with parameter bomb and algorithm violations.'''

    current_user_id = get_jwt_identity()

    # Permission check with magic role strings
    current_user = User.query.get(current_user_id)
    if current_user.role != 'admin' and current_user.id != user_id:  # Magic string
        return jsonify({'error': 'Insufficient permissions'}), 403  # Magic string/literal

    user = User.query.get_or_404(user_id)

    # Validation with magic values
    if username and len(username) < 3:  # Magic literal
        return jsonify({'error': 'Username too short'}), 400  # Magic string/literal

    if email:
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'  # Magic string
        if not re.match(email_pattern, email):
            return jsonify({'error': 'Invalid email'}), 400  # Magic string/literal

    if bio and len(bio) > 500:  # Magic literal
        return jsonify({'error': 'Bio too long (max 500 chars)'}), 400  # Magic string/literal

    # Complex update logic with algorithm connascence
    updates = {}
    if username and username != user.username:
        # Check uniqueness
        existing_user = User.query.filter_by(username=username).first()
        if existing_user and existing_user.id != user.id:
            return jsonify({'error': 'Username already taken'}), 409  # Magic string/literal
        updates['username'] = username

    if email and email != user.email:
        # Check uniqueness
        existing_user = User.query.filter_by(email=email).first()
        if existing_user and existing_user.id != user.id:
            return jsonify({'error': 'Email already taken'}), 409  # Magic string/literal
        updates['email'] = email

    if full_name:
        updates['full_name'] = full_name

    if phone:
        phone_pattern = r'^\\+?1?d{9,15}$'  # Magic string
        if not re.match(phone_pattern, phone):
            return jsonify({'error': 'Invalid phone format'}), 400  # Magic string/literal
        updates['phone'] = phone

    if bio is not None:
        updates['bio'] = bio

    # Apply updates
    for key, value in updates.items():
        setattr(user, key, value)

    user.updated_at = datetime.now(datetime.UTC)

    try:
        db.session.commit()
        return jsonify({
            'message': 'User updated successfully',  # Magic string
            'user_id': user.id
        }), 200  # Magic literal

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'User update failed: {str(e)}')
        return jsonify({'error': 'Update failed'}), 500  # Magic string/literal


class UserManager:
    '''God class for user management with algorithm connascence.'''

    def __init__(self):
        self.max_login_attempts = 5  # Magic literal
        self.lockout_duration = 1800  # Magic literal - 30 minutes
        self.password_min_length = 8  # Magic literal
        self.session_timeout = 3600  # Magic literal - 1 hour

    def authenticate_user(self, username, password):  # Missing type hints
        pass

    def validate_password_strength(self, password):  # Missing type hints
        pass

    def hash_password(self, password):  # Missing type hints
        pass

    def verify_password(self, password, hash):  # Missing type hints
        pass

    def generate_reset_token(self, user_id):  # Missing type hints
        pass

    def verify_reset_token(self, token):  # Missing type hints
        pass

    def send_verification_email(self, user_id):  # Missing type hints
        pass

    def verify_email_token(self, token):  # Missing type hints
        pass

    def update_login_attempts(self, user_id):  # Missing type hints
        pass

    def check_account_lockout(self, user_id):  # Missing type hints
        pass

    def unlock_account(self, user_id):  # Missing type hints
        pass

    def log_user_activity(self, user_id, activity):  # Missing type hints
        pass

    def get_user_sessions(self, user_id):  # Missing type hints
        pass

    def invalidate_user_sessions(self, user_id):  # Missing type hints
        pass

    def export_user_data(self, user_id):  # Missing type hints
        pass

    def delete_user_data(self, user_id):  # Missing type hints
        pass

    def backup_user_data(self, user_id):  # Missing type hints
        pass

    def restore_user_data(self, backup_data):  # Missing type hints
        pass

    def validate_permissions(self, user_id, resource):  # Missing type hints
        pass

    def assign_role(self, user_id, role):  # Missing type hints
        pass

    def remove_role(self, user_id, role):  # Missing type hints
        pass

    def calculate_user_metrics(self, user_id):  # Missing type hints
        pass

    def generate_user_report(self, user_id):  # Missing type hints
        pass

    def sync_external_systems(self, user_id):  # Missing type hints
        pass

    def process_gdpr_request(self, user_id, request_type):  # Missing type hints
        pass
"""
    )

    yield project_path

    # Cleanup
    import shutil

    shutil.rmtree(temp_dir)


@pytest.fixture
def repo_workflow_validator():
    """Create workflow validator for repository analysis."""
    return SequentialWorkflowValidator(repo_coordinator)


class TestRepositoryAnalysisWorkflows:
    """Test end-to-end repository analysis workflows."""

    def test_django_project_analysis_workflow(self, django_project_template, repo_workflow_validator):
        """Test comprehensive Django project analysis."""
        scenario_id = "django_project_analysis"
        repo_workflow_validator.start_scenario(scenario_id, "Django project analysis workflow")

        # Step 1: Repository profiling
        repo_profile = {
            "project_type": "django_web_app",
            "estimated_size": "medium",
            "framework_indicators": ["django", "python"],
            "file_count": len(list(django_project_template.rglob("*.py"))),
            "structure_complexity": "moderate",
        }

        repo_coordinator.store_repository_profile(scenario_id, repo_profile)
        repo_workflow_validator.add_step("repository_profiling", repo_profile)

        # Step 2: Framework detection
        detected_frameworks = ["django", "python"]
        framework_violations = {
            "django": ["SECRET_KEY", "magic_literals", "settings_violations"],
            "python": ["parameter_bombs", "god_classes", "type_hints"],
        }

        repo_coordinator.store_framework_detection(scenario_id, detected_frameworks, framework_violations)
        repo_workflow_validator.add_step(
            "framework_detection",
            {"frameworks": detected_frameworks, "framework_specific_patterns": framework_violations},
        )

        # Step 3: Execute comprehensive analysis
        cli = ConnascenceCLI()
        output_file = django_project_template / "django_analysis.json"

        start_time = time.time()
        exit_code = cli.run(
            [
                "scan",
                str(django_project_template),
                "--policy",
                "service-defaults",
                "--format",
                "json",
                "--output",
                str(output_file),
            ]
        )
        execution_time = time.time() - start_time

        repo_workflow_validator.add_step(
            "execute_analysis",
            {"exit_code": exit_code, "execution_time_ms": execution_time * 1000, "output_file": str(output_file)},
        )

        # Step 4: Analyze results for patterns
        assert output_file.exists(), "Analysis output file not created"

        with open(output_file) as f:
            analysis_results = json.load(f)

        violations = analysis_results.get("violations", [])

        # Pattern analysis
        patterns = {
            "magic_string_count": len(
                [
                    v
                    for v in violations
                    if "magic" in v.get("description", "").lower() and "string" in v.get("description", "").lower()
                ]
            ),
            "magic_literal_count": len(
                [
                    v
                    for v in violations
                    if "magic" in v.get("description", "").lower() and "literal" in v.get("description", "").lower()
                ]
            ),
            "parameter_bomb_count": len([v for v in violations if "parameter" in v.get("description", "").lower()]),
            "god_class_count": len(
                [
                    v
                    for v in violations
                    if "class" in v.get("description", "").lower()
                    and ("methods" in v.get("description", "").lower() or "god" in v.get("description", "").lower())
                ]
            ),
            "type_hint_count": len(
                [
                    v
                    for v in violations
                    if "type" in v.get("description", "").lower() and "hint" in v.get("description", "").lower()
                ]
            ),
            "security_violation_count": len(
                [
                    v
                    for v in violations
                    if "secret" in v.get("description", "").lower() or "key" in v.get("description", "").lower()
                ]
            ),
        }

        repo_coordinator.store_analysis_pattern(scenario_id, patterns)
        repo_workflow_validator.add_step("pattern_analysis", patterns)

        # Step 5: Calculate violation density
        total_lines = sum(
            1 for py_file in django_project_template.rglob("*.py") for line in py_file.read_text().splitlines()
        )
        density_metrics = {
            "violations_per_file": len(violations) / max(repo_profile["file_count"], 1),
            "violations_per_100_lines": (len(violations) / max(total_lines, 1)) * 100,
            "high_severity_density": len(
                [v for v in violations if v.get("severity", {}).get("value") in ["high", "critical"]]
            )
            / max(total_lines, 1)
            * 100,
        }

        repo_coordinator.store_violation_density(scenario_id, density_metrics)
        repo_workflow_validator.add_step("density_calculation", density_metrics)

        # Step 6: Django-specific validation
        # Should find Django-specific violations like SECRET_KEY issues
        security_violations = [v for v in violations if "secret" in v.get("description", "").lower()]
        settings_violations = [v for v in violations if "settings.py" in v.get("file_path", "")]

        django_specific_metrics = {
            "security_violations_found": len(security_violations) > 0,
            "settings_violations_found": len(settings_violations) > 0,
            "django_patterns_detected": len(security_violations) + len(settings_violations) > 0,
        }

        repo_workflow_validator.add_step("django_specific_validation", django_specific_metrics)

        # Assertions
        assert exit_code == 1, "Should find violations in Django project"
        assert len(violations) > 0, "Should detect violations in Django project"
        assert patterns["magic_string_count"] > 0, "Should detect magic strings in Django settings"
        assert patterns["parameter_bomb_count"] > 0, "Should detect parameter bombs in views"
        assert patterns["god_class_count"] > 0, "Should detect god classes"

        repo_workflow_validator.complete_scenario(
            True,
            {
                "total_violations": len(violations),
                "patterns": patterns,
                "density_metrics": density_metrics,
                "django_specific_findings": django_specific_metrics,
            },
        )

    def test_flask_api_analysis_workflow(self, flask_api_project, repo_workflow_validator):
        """Test Flask API project analysis with framework-specific patterns."""
        scenario_id = "flask_api_analysis"
        repo_workflow_validator.start_scenario(scenario_id, "Flask API project analysis workflow")

        # Repository profiling
        repo_profile = {
            "project_type": "flask_api",
            "estimated_size": "small",
            "framework_indicators": ["flask", "api", "python"],
            "file_count": len(list(flask_api_project.rglob("*.py"))),
            "api_specific": True,
        }

        repo_coordinator.store_repository_profile(scenario_id, repo_profile)
        repo_workflow_validator.add_step("repository_profiling", repo_profile)

        # Execute analysis
        cli = ConnascenceCLI()
        output_file = flask_api_project / "flask_analysis.json"

        exit_code = cli.run(
            [
                "scan",
                str(flask_api_project),
                "--policy",
                "strict-core",
                "--format",
                "json",
                "--output",
                str(output_file),
            ]
        )

        repo_workflow_validator.add_step("execute_analysis", {"exit_code": exit_code})

        # Analyze Flask-specific patterns
        with open(output_file) as f:
            analysis_results = json.load(f)

        violations = analysis_results.get("violations", [])

        flask_patterns = {
            "api_parameter_bombs": len(
                [
                    v
                    for v in violations
                    if "parameter" in v.get("description", "").lower()
                    and any(keyword in v.get("file_path", "") for keyword in ["api", "users", "routes"])
                ]
            ),
            "security_violations": len(
                [
                    v
                    for v in violations
                    if any(keyword in v.get("description", "").lower() for keyword in ["secret", "key", "token"])
                ]
            ),
            "api_specific_violations": len(
                [v for v in violations if any(keyword in v.get("file_path", "") for keyword in ["api", "routes"])]
            ),
            "flask_config_violations": len([v for v in violations if "__init__.py" in v.get("file_path", "")]),
        }

        repo_coordinator.store_analysis_pattern(scenario_id, flask_patterns)
        repo_workflow_validator.add_step("flask_pattern_analysis", flask_patterns)

        # Flask-specific assertions
        assert exit_code == 1, "Should find violations in Flask project"
        assert flask_patterns["security_violations"] > 0, "Should detect security violations in Flask config"
        assert flask_patterns["api_parameter_bombs"] > 0, "Should detect API parameter bombs"

        repo_workflow_validator.complete_scenario(True, {"flask_analysis_completed": True, "patterns": flask_patterns})

    def test_repository_comparison_workflow(self, django_project_template, flask_api_project, repo_workflow_validator):
        """Test repository comparison and benchmarking."""
        scenario_id = "repository_comparison"
        repo_workflow_validator.start_scenario(scenario_id, "Repository comparison workflow")

        # Analyze both projects
        projects = [
            ("django_comparison", django_project_template, "Django"),
            ("flask_comparison", flask_api_project, "Flask"),
        ]

        comparison_results = {}

        for proj_id, project_path, framework in projects:
            repo_workflow_validator.add_step(f"analyze_{proj_id}", {"framework": framework})

            cli = ConnascenceCLI()
            output_file = project_path / f"{proj_id}_comparison.json"

            start_time = time.time()
            exit_code = cli.run(["scan", str(project_path), "--format", "json", "--output", str(output_file)])
            execution_time = time.time() - start_time

            with open(output_file) as f:
                analysis_results = json.load(f)

            violations = analysis_results.get("violations", [])
            file_count = len(list(project_path.rglob("*.py")))

            comparison_results[proj_id] = {
                "framework": framework,
                "total_violations": len(violations),
                "violations_per_file": len(violations) / max(file_count, 1),
                "execution_time_ms": execution_time * 1000,
                "exit_code": exit_code,
                "file_count": file_count,
                "violation_types": {
                    "magic_literals": len(
                        [
                            v
                            for v in violations
                            if "magic" in v.get("description", "").lower()
                            and "literal" in v.get("description", "").lower()
                        ]
                    ),
                    "magic_strings": len(
                        [
                            v
                            for v in violations
                            if "magic" in v.get("description", "").lower()
                            and "string" in v.get("description", "").lower()
                        ]
                    ),
                    "parameter_bombs": len([v for v in violations if "parameter" in v.get("description", "").lower()]),
                    "god_classes": len(
                        [
                            v
                            for v in violations
                            if "class" in v.get("description", "").lower()
                            and "methods" in v.get("description", "").lower()
                        ]
                    ),
                    "type_violations": len([v for v in violations if "type" in v.get("description", "").lower()]),
                },
            }

        # Store comparison
        comparison_summary = repo_coordinator.compare_repositories(["django_comparison", "flask_comparison"])
        repo_workflow_validator.add_step("repository_comparison", comparison_summary)

        # Analysis insights
        insights = {
            "django_has_more_violations": comparison_results["django_comparison"]["total_violations"]
            > comparison_results["flask_comparison"]["total_violations"],
            "performance_comparison": {
                "django_time": comparison_results["django_comparison"]["execution_time_ms"],
                "flask_time": comparison_results["flask_comparison"]["execution_time_ms"],
            },
            "violation_density_comparison": {
                "django_density": comparison_results["django_comparison"]["violations_per_file"],
                "flask_density": comparison_results["flask_comparison"]["violations_per_file"],
            },
        }

        repo_workflow_validator.add_step("comparison_insights", insights)

        # Assertions
        assert len(comparison_results) == 2, "Should analyze both projects"
        assert all(r["exit_code"] == 1 for r in comparison_results.values()), "Both projects should have violations"

        repo_workflow_validator.complete_scenario(
            True,
            {
                "comparison_completed": True,
                "projects_analyzed": len(projects),
                "comparison_results": comparison_results,
                "insights": insights,
            },
        )

    def test_large_repository_performance(self, repo_workflow_validator):
        """Test performance with large repository simulation."""
        scenario_id = "large_repository_performance"
        repo_workflow_validator.start_scenario(scenario_id, "Large repository performance test")

        # Create large project structure
        temp_dir = tempfile.mkdtemp()
        large_project = Path(temp_dir)

        repo_workflow_validator.add_step("create_large_project", {"action": "generating_structure"})

        # Generate 50 modules with violations
        for i in range(50):
            module_dir = large_project / f"module_{i:02d}"
            module_dir.mkdir()

            # Create multiple files per module
            for j in range(3):
                (module_dir / f"component_{j}.py").write_text(
                    f"""
# Module {i} Component {j} with violations

def process_function_{i}_{j}(param1, param2, param3, param4, param5, param6):  # Parameter bomb
    threshold_{i} = {100 + i * 10}  # Magic literal
    secret_key_{i} = "secret_key_{i}_{j}"  # Magic string

    if param1 > threshold_{i}:
        multiplier = {2.5 + j * 0.1}  # Magic literal
        return param1 * multiplier

    return param1 + {42 + i + j}  # Magic literal

class ProcessorClass_{i}_{j}:
    '''Class with many methods - potential god class.'''

    def __init__(self):
        self.cache_timeout = {300 + i * 10}  # Magic literal
        self.max_retries = {5 + j}  # Magic literal
        self.api_key = "api_key_{i}_{j}"  # Magic string

    def method_01(self): pass
    def method_02(self): pass
    def method_03(self): pass
    def method_04(self): pass
    def method_05(self): pass
    def method_06(self): pass
    def method_07(self): pass
    def method_08(self): pass
    def method_09(self): pass
    def method_10(self): pass
    def method_11(self): pass
    def method_12(self): pass
    def method_13(self): pass
    def method_14(self): pass
    def method_15(self): pass
    def method_16(self): pass
    def method_17(self): pass
    def method_18(self): pass
    def method_19(self): pass
    def method_20(self): pass
    def method_21(self): pass  # God class threshold
"""
                )

        total_files = 50 * 3  # 150 files
        repo_workflow_validator.add_step(
            "large_project_generated",
            {"modules": 50, "total_files": total_files, "estimated_violations": total_files * 10},  # Rough estimate
        )

        # Execute performance analysis
        cli = ConnascenceCLI()
        output_file = large_project / "large_repo_analysis.json"

        start_time = time.time()
        exit_code = cli.run(["scan", str(large_project), "--format", "json", "--output", str(output_file)])
        execution_time = time.time() - start_time

        repo_workflow_validator.add_step(
            "execute_large_analysis", {"execution_time_ms": execution_time * 1000, "exit_code": exit_code}
        )

        # Analyze performance metrics
        with open(output_file) as f:
            results = json.load(f)

        violations = results.get("violations", [])

        performance_metrics = {
            "execution_time_ms": execution_time * 1000,
            "files_analyzed": results.get("total_files_analyzed", 0),
            "violations_found": len(violations),
            "violations_per_second": len(violations) / max(execution_time, 0.001),
            "files_per_second": results.get("total_files_analyzed", 0) / max(execution_time, 0.001),
            "performance_acceptable": execution_time < 60.0,  # Should complete in under 1 minute
            "memory_efficient": True,  # Assuming no memory issues
        }

        repo_coordinator.store_complexity_metrics(scenario_id, performance_metrics)
        repo_workflow_validator.add_step("performance_analysis", performance_metrics)

        # Store results
        repo_coordinator.store_performance_metrics(scenario_id, performance_metrics)

        # Cleanup
        import shutil

        shutil.rmtree(temp_dir)

        # Performance assertions
        assert execution_time < 60.0, f"Large project analysis took too long: {execution_time}s"
        assert exit_code == 1, "Should find violations in large project"
        assert len(violations) > 100, "Should find many violations in large project"
        assert performance_metrics["files_per_second"] > 1.0, "Should process at least 1 file per second"

        repo_workflow_validator.complete_scenario(
            True, {"performance_test_passed": True, "metrics": performance_metrics}
        )

    def test_memory_coordination_repository_tracking(self):
        """Test memory coordination for repository analysis tracking."""
        # Test repository coordinator functionality
        test_repo_id = "memory_test_repo"

        # Store test data
        repo_coordinator.store_repository_profile(
            test_repo_id, {"type": "test_project", "size": "small", "complexity": "low"}
        )

        repo_coordinator.store_analysis_pattern(test_repo_id, {"pattern_1": 10, "pattern_2": 5, "pattern_3": 2})

        repo_coordinator.store_violation_density(
            test_repo_id, {"violations_per_file": 2.5, "high_severity_density": 0.1}
        )

        # Validate data storage
        assert test_repo_id in repo_coordinator.repository_profiles
        assert test_repo_id in repo_coordinator.analysis_patterns
        assert test_repo_id in repo_coordinator.violation_densities

        # Test comparison functionality
        test_repo_2 = "memory_test_repo_2"
        repo_coordinator.store_violation_density(
            test_repo_2, {"violations_per_file": 1.8, "high_severity_density": 0.05}
        )

        comparison = repo_coordinator.compare_repositories([test_repo_id, test_repo_2])
        assert "repositories" in comparison
        assert len(comparison["repositories"]) == 2
        assert "metrics" in comparison


@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.integration
def test_repository_analysis_integration():
    """Integration test for repository analysis workflows."""
    coordinator = RepositoryAnalysisCoordinator()

    # This test validates the complete repository analysis pipeline
    scenario_id = "repo_integration_test"

    # Mock repository analysis
    coordinator.store_repository_profile(scenario_id, {"integration_test": True, "timestamp": time.time()})

    coordinator.store_analysis_pattern(scenario_id, {"test_pattern": True})

    # Validate integration
    assert scenario_id in coordinator.repository_profiles
    assert scenario_id in coordinator.analysis_patterns

    print("Repository analysis integration test completed successfully")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-m", "e2e"])
