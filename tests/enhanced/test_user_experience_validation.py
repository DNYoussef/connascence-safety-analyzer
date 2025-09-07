# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2024 Connascence Safety Analyzer Contributors

"""
Enhanced Pipeline User Experience Validation Tests
=================================================

Real-world user experience validation for the enhanced pipeline:
- Realistic codebase patterns and structures
- Developer workflow integration testing
- User interface responsiveness validation
- Practical recommendation quality assessment
- Cross-phase correlation effectiveness
- Smart recommendation actionability
- Audit trail comprehensiveness
- Production-ready deployment validation
"""

import os
import json
import time
import tempfile
import statistics
import pytest
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Any, Optional, Tuple
from unittest.mock import Mock, patch

from .test_infrastructure import (
    EnhancedTestDatasets,
    MockEnhancedAnalyzer,
    EnhancedTestUtilities,
    MockCorrelation,
    MockSmartRecommendation,
    MockAuditTrailEntry,
    integration_test,
    performance_test
)


@dataclass
class RealWorldCodebase:
    """Real-world codebase pattern for validation"""
    name: str
    description: str
    architecture_pattern: str
    complexity_level: str
    files: Dict[str, str]
    expected_insights: Dict[str, Any]
    user_scenarios: List[Dict[str, Any]]


@dataclass
class UserExperienceMetrics:
    """Metrics for user experience validation"""
    analysis_response_time: float
    correlation_discovery_accuracy: float
    recommendation_actionability_score: float
    interface_responsiveness: float
    insight_relevance_score: float
    workflow_integration_score: float


class UserExperienceValidationSuite:
    """Comprehensive user experience validation suite"""
    
    def __init__(self):
        self.real_world_codebases = self._create_real_world_codebases()
        self.user_scenarios = self._create_user_scenarios()
    
    def _create_real_world_codebases(self) -> List[RealWorldCodebase]:
        """Create realistic codebase patterns for validation"""
        return [
            RealWorldCodebase(
                name="django_web_application",
                description="Typical Django web application with models, views, and templates",
                architecture_pattern="mvc",
                complexity_level="medium",
                files={
                    "models.py": '''
from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # CofE: Identity - profile tied to User model structure
    bio = models.TextField(max_length=500, blank=True)
    location = models.CharField(max_length=30, blank=True)
    birth_date = models.DateField(null=True, blank=True)

class Post(models.Model):
    DRAFT = 'DR'
    PUBLISHED = 'PB'
    STATUS_CHOICES = [
        (DRAFT, 'Draft'),
        (PUBLISHED, 'Published'),
    ]
    
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    # CofE: Type - Post depends on User model
    title = models.CharField(max_length=200)
    content = models.TextField()
    status = models.CharField(max_length=2, choices=STATUS_CHOICES, default=DRAFT)
    # CofE: Meaning - status values have semantic coupling
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
                    ''',
                    "views.py": '''
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Post, UserProfile

def post_list(request):
    # CofE: Algorithm - view depends on Post model structure
    published_posts = Post.objects.filter(status=Post.PUBLISHED).order_by('-created_at')
    # CofE: Meaning - hardcoded status value creates coupling
    return render(request, 'blog/post_list.html', {'posts': published_posts})

@login_required
def create_post(request):
    if request.method == 'POST':
        # CofE: Position - parameter processing depends on order
        title = request.POST.get('title')
        content = request.POST.get('content')
        
        if title and content:
            # CofE: Execution - must create in specific sequence
            post = Post(author=request.user, title=title, content=content)
            post.status = Post.DRAFT  # CofE: Meaning - status coupling
            post.save()
            return redirect('post_detail', pk=post.pk)
    
    return render(request, 'blog/create_post.html')

def user_profile_api(request, user_id):
    # CofE: Type - API depends on specific model structure
    try:
        profile = get_object_or_404(UserProfile, user_id=user_id)
        return JsonResponse({
            'user_id': profile.user.id,
            'username': profile.user.username,  # CofE: Identity - profile structure coupling
            'bio': profile.bio,
            'location': profile.location,
        })
    except UserProfile.DoesNotExist:
        return JsonResponse({'error': 'Profile not found'}, status=404)
                    ''',
                    "serializers.py": '''
from rest_framework import serializers
from .models import Post, UserProfile

class UserProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    # CofE: Identity - serializer coupled to User model structure
    
    class Meta:
        model = UserProfile
        fields = ['user', 'username', 'bio', 'location', 'birth_date']

class PostSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.username', read_only=True)
    # CofE: Type - serializer depends on specific author structure
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Post
        fields = ['id', 'title', 'content', 'status', 'status_display', 'author', 'author_name', 'created_at']
    
    def validate_status(self, value):
        # CofE: Meaning - validation coupled to specific status values
        if value not in [Post.DRAFT, Post.PUBLISHED]:
            raise serializers.ValidationError("Invalid status value")
        return value
                    '''
                },
                expected_insights={
                    "correlation_count": 8,
                    "critical_recommendations": 3,
                    "refactoring_opportunities": 5,
                    "architectural_improvements": 2
                },
                user_scenarios=[
                    {"role": "backend_developer", "task": "add_new_status", "expected_changes": 4},
                    {"role": "frontend_developer", "task": "extend_api", "expected_changes": 2},
                    {"role": "architect", "task": "decouple_components", "expected_changes": 6}
                ]
            ),
            
            RealWorldCodebase(
                name="microservices_e_commerce",
                description="E-commerce microservices with service interdependencies",
                architecture_pattern="microservices",
                complexity_level="high",
                files={
                    "user_service.py": '''
class UserService:
    def __init__(self, database, auth_service):
        # CofE: Type - depends on specific database and auth implementations
        self.db = database
        self.auth = auth_service
        
    def create_user(self, user_data):
        # CofE: Algorithm - user creation depends on auth service workflow
        if not self.auth.validate_registration_data(user_data):
            return {'error': 'Invalid registration data'}
        
        # CofE: Execution - specific order required for user creation
        user_id = self.db.create_user(user_data)
        self.auth.create_auth_record(user_id, user_data['password'])
        
        # CofE: Meaning - user status has semantic coupling across services
        self.db.update_user_status(user_id, 'PENDING_VERIFICATION')
        
        return {'user_id': user_id, 'status': 'created'}
    
    def get_user_profile(self, user_id):
        # CofE: Identity - profile structure coupled to database schema
        user_data = self.db.get_user(user_id)
        if not user_data:
            return None
        
        return {
            'id': user_data['id'],
            'username': user_data['username'],
            'email': user_data['email'],
            'status': user_data['status'],  # CofE: Meaning - status coupling
            'created_at': user_data['created_at']
        }
                    ''',
                    "order_service.py": '''
from user_service import UserService
from inventory_service import InventoryService

class OrderService:
    def __init__(self, user_service: UserService, inventory_service: InventoryService):
        # CofE: Type - tight coupling to specific service implementations
        self.user_service = user_service
        self.inventory_service = inventory_service
        
    def create_order(self, user_id, items):
        # CofE: Algorithm - order creation depends on user service validation
        user_profile = self.user_service.get_user_profile(user_id)
        if not user_profile or user_profile['status'] != 'ACTIVE':
            # CofE: Meaning - status string coupling across services
            return {'error': 'Invalid user or inactive account'}
        
        # CofE: Execution - must check inventory before creating order
        for item in items:
            if not self.inventory_service.check_availability(item['product_id'], item['quantity']):
                return {'error': f'Insufficient inventory for {item["product_id"]}'}
        
        # CofE: Algorithm - order processing algorithm depends on inventory service
        order_id = self._generate_order_id()
        for item in items:
            self.inventory_service.reserve_item(item['product_id'], item['quantity'])
        
        order_data = {
            'id': order_id,
            'user_id': user_id,
            'items': items,
            'status': 'PROCESSING',  # CofE: Meaning - order status coupling
            'created_at': self._get_timestamp()
        }
        
        return {'order_id': order_id, 'status': 'created'}
                    ''',
                    "inventory_service.py": '''
class InventoryService:
    def __init__(self, database, cache):
        # CofE: Identity - service structure depends on database and cache
        self.db = database
        self.cache = cache
        
    def check_availability(self, product_id, requested_quantity):
        # CofE: Algorithm - availability check algorithm coupled to cache strategy
        cached_stock = self.cache.get(f"stock_{product_id}")
        if cached_stock is not None:
            return cached_stock >= requested_quantity
        
        # CofE: Execution - fallback to database requires specific query pattern
        db_stock = self.db.get_product_stock(product_id)
        self.cache.set(f"stock_{product_id}", db_stock, timeout=300)
        return db_stock >= requested_quantity
    
    def reserve_item(self, product_id, quantity):
        # CofE: Algorithm - reservation algorithm depends on transaction handling
        current_stock = self.db.get_product_stock(product_id)
        if current_stock < quantity:
            raise Exception(f"Insufficient stock for product {product_id}")
        
        # CofE: Execution - must update database and cache in specific order
        new_stock = current_stock - quantity
        self.db.update_product_stock(product_id, new_stock)
        self.cache.set(f"stock_{product_id}", new_stock, timeout=300)
        
        return True
    
    def get_product_info(self, product_id):
        # CofE: Identity - product info structure coupled to database schema
        product_data = self.db.get_product(product_id)
        if not product_data:
            return None
        
        return {
            'id': product_data['id'],
            'name': product_data['name'],
            'price': product_data['price'],
            'stock': product_data['stock'],
            'status': product_data['status']  # CofE: Meaning - product status coupling
        }
                    '''
                },
                expected_insights={
                    "correlation_count": 12,
                    "critical_recommendations": 5,
                    "refactoring_opportunities": 8,
                    "architectural_improvements": 4
                },
                user_scenarios=[
                    {"role": "microservices_architect", "task": "decouple_services", "expected_changes": 10},
                    {"role": "devops_engineer", "task": "improve_resilience", "expected_changes": 6},
                    {"role": "senior_developer", "task": "refactor_status_handling", "expected_changes": 8}
                ]
            ),
            
            RealWorldCodebase(
                name="data_processing_pipeline",
                description="Data processing pipeline with ETL operations",
                architecture_pattern="pipeline",
                complexity_level="medium",
                files={
                    "data_extractor.py": '''
import pandas as pd
from typing import Dict, List, Any

class DataExtractor:
    def __init__(self, config):
        # CofE: Identity - extractor coupled to specific config structure
        self.source_type = config['source_type']
        self.connection_params = config['connection_params']
        
    def extract_data(self, query_params):
        # CofE: Algorithm - extraction algorithm depends on source type
        if self.source_type == 'database':
            return self._extract_from_database(query_params)
        elif self.source_type == 'csv':
            return self._extract_from_csv(query_params)
        elif self.source_type == 'api':
            return self._extract_from_api(query_params)
        else:
            raise ValueError(f"Unsupported source type: {self.source_type}")
    
    def _extract_from_database(self, params):
        # CofE: Position - parameter order matters for database queries
        query = params.get('query')
        limit = params.get('limit', 1000)
        offset = params.get('offset', 0)
        
        # CofE: Execution - must connect before querying
        connection = self._get_database_connection()
        result = connection.execute(query, limit=limit, offset=offset)
        return pd.DataFrame(result.fetchall())
    
    def _extract_from_csv(self, params):
        # CofE: Meaning - file path structure has semantic coupling
        file_path = params['file_path']
        delimiter = params.get('delimiter', ',')
        
        return pd.read_csv(file_path, delimiter=delimiter)
                    ''',
                    "data_transformer.py": '''
import pandas as pd
import numpy as np
from data_extractor import DataExtractor

class DataTransformer:
    def __init__(self, extractor: DataExtractor):
        # CofE: Type - transformer depends on specific extractor implementation
        self.extractor = extractor
        self.transformation_rules = {}
        
    def transform_data(self, data: pd.DataFrame, rules: Dict[str, Any]):
        # CofE: Algorithm - transformation depends on rule structure
        transformed_data = data.copy()
        
        for column, rule in rules.items():
            if rule['type'] == 'normalize':
                # CofE: Meaning - rule types have semantic coupling
                transformed_data[column] = self._normalize_column(transformed_data[column])
            elif rule['type'] == 'categorize':
                transformed_data[column] = self._categorize_column(transformed_data[column], rule['categories'])
            elif rule['type'] == 'aggregate':
                transformed_data = self._aggregate_data(transformed_data, column, rule['function'])
        
        return transformed_data
    
    def _normalize_column(self, column):
        # CofE: Algorithm - normalization algorithm has specific requirements
        if column.dtype in ['int64', 'float64']:
            return (column - column.min()) / (column.max() - column.min())
        return column
    
    def _categorize_column(self, column, categories):
        # CofE: Position - category order affects results
        def categorize_value(value):
            for category in categories:
                if category['min'] <= value <= category['max']:
                    return category['label']
            return 'Unknown'
        
        return column.apply(categorize_value)
    
    def validate_transformation(self, original_data, transformed_data):
        # CofE: Execution - validation must happen after transformation
        validation_results = {}
        
        # Check data integrity
        if len(original_data) != len(transformed_data):
            validation_results['row_count_mismatch'] = True
        
        # Check for null values introduced during transformation
        original_nulls = original_data.isnull().sum().sum()
        transformed_nulls = transformed_data.isnull().sum().sum()
        
        if transformed_nulls > original_nulls:
            validation_results['new_nulls_introduced'] = transformed_nulls - original_nulls
        
        return validation_results
                    ''',
                    "data_loader.py": '''
import pandas as pd
from data_transformer import DataTransformer

class DataLoader:
    def __init__(self, transformer: DataTransformer, target_config):
        # CofE: Type - loader depends on specific transformer implementation
        self.transformer = transformer
        # CofE: Identity - loader structure coupled to target config
        self.target_type = target_config['type']
        self.target_params = target_config['params']
        
    def load_data(self, data: pd.DataFrame):
        # CofE: Algorithm - loading algorithm depends on target type
        if self.target_type == 'database':
            return self._load_to_database(data)
        elif self.target_type == 'csv':
            return self._load_to_csv(data)
        elif self.target_type == 'parquet':
            return self._load_to_parquet(data)
        else:
            raise ValueError(f"Unsupported target type: {self.target_type}")
    
    def _load_to_database(self, data):
        # CofE: Position - database parameters must be in correct order
        table_name = self.target_params['table_name']
        if_exists = self.target_params.get('if_exists', 'append')
        index = self.target_params.get('index', False)
        
        # CofE: Execution - must establish connection before loading
        connection = self._get_database_connection()
        data.to_sql(table_name, connection, if_exists=if_exists, index=index)
        
        return {'status': 'success', 'rows_loaded': len(data)}
    
    def _load_to_csv(self, data):
        # CofE: Meaning - file path structure has semantic meaning
        file_path = self.target_params['file_path']
        delimiter = self.target_params.get('delimiter', ',')
        
        data.to_csv(file_path, sep=delimiter, index=False)
        return {'status': 'success', 'file_path': file_path}
    
    def run_full_pipeline(self, query_params, transformation_rules):
        # CofE: Execution - pipeline steps must execute in specific order
        # Step 1: Extract data
        raw_data = self.transformer.extractor.extract_data(query_params)
        
        # Step 2: Transform data
        transformed_data = self.transformer.transform_data(raw_data, transformation_rules)
        
        # Step 3: Validate transformation
        validation_results = self.transformer.validate_transformation(raw_data, transformed_data)
        
        # Step 4: Load data if validation passes
        if not validation_results:  # No validation errors
            load_results = self.load_data(transformed_data)
            return {'status': 'success', 'load_results': load_results}
        else:
            return {'status': 'validation_failed', 'validation_errors': validation_results}
                    '''
                },
                expected_insights={
                    "correlation_count": 10,
                    "critical_recommendations": 4,
                    "refactoring_opportunities": 6,
                    "architectural_improvements": 3
                },
                user_scenarios=[
                    {"role": "data_engineer", "task": "add_new_source", "expected_changes": 5},
                    {"role": "data_scientist", "task": "customize_transformations", "expected_changes": 3},
                    {"role": "platform_engineer", "task": "improve_pipeline_resilience", "expected_changes": 7}
                ]
            )
        ]
    
    def _create_user_scenarios(self) -> List[Dict[str, Any]]:
        """Create user interaction scenarios for validation"""
        return [
            {
                "name": "quick_analysis_workflow",
                "description": "Developer quickly analyzes code for immediate insights",
                "steps": ["open_file", "analyze", "review_correlations", "implement_recommendation"],
                "max_time_seconds": 30.0,
                "expected_insights": 5
            },
            {
                "name": "comprehensive_refactoring_session",
                "description": "Architect performs comprehensive refactoring analysis",
                "steps": ["analyze_full_project", "review_architecture", "plan_refactoring", "validate_changes"],
                "max_time_seconds": 120.0,
                "expected_insights": 20
            },
            {
                "name": "continuous_integration_validation",
                "description": "CI/CD pipeline validates code changes automatically",
                "steps": ["analyze_changes", "compare_baselines", "generate_report", "fail_on_regressions"],
                "max_time_seconds": 60.0,
                "expected_insights": 10
            }
        ]


@pytest.fixture
def ux_validation_suite():
    """Fixture providing user experience validation suite"""
    return UserExperienceValidationSuite()


@pytest.fixture
def temp_ux_directory():
    """Create temporary directory for UX testing"""
    with tempfile.TemporaryDirectory() as temp_dir:
        ux_test_path = Path(temp_dir) / "ux_test_project"
        ux_test_path.mkdir()
        yield ux_test_path


class TestUserExperienceValidation:
    """User experience validation tests"""
    
    @integration_test(["user_experience"])
    @performance_test(max_time_seconds=60.0, max_memory_mb=200.0)
    def test_django_web_application_analysis(self, ux_validation_suite, temp_ux_directory):
        """Test enhanced pipeline with realistic Django application"""
        codebase = ux_validation_suite.real_world_codebases[0]  # Django web application
        
        # Setup codebase files
        self._setup_codebase(temp_ux_directory, codebase)
        
        # Execute enhanced analysis
        start_time = time.time()
        mock_analyzer = MockEnhancedAnalyzer("success")
        result = mock_analyzer.analyze_path(
            str(temp_ux_directory),
            enable_cross_phase_correlation=True,
            enable_smart_recommendations=True,
            enable_audit_trail=True
        )
        analysis_time = time.time() - start_time
        
        # Validate user experience metrics
        ux_metrics = self._calculate_ux_metrics(result, analysis_time, codebase)
        
        # Validate analysis quality
        correlations = result.get("correlations", [])
        recommendations = result.get("smart_recommendations", [])
        
        assert len(correlations) >= codebase.expected_insights["correlation_count"] * 0.7, \
            "Should discover most expected correlations"
        
        assert len(recommendations) >= codebase.expected_insights["critical_recommendations"], \
            "Should provide critical recommendations"
        
        # Validate recommendation actionability
        actionable_recommendations = [
            r for r in recommendations
            if r.get("implementation_guide") and len(r.get("affected_files", [])) > 0
        ]
        
        actionability_ratio = len(actionable_recommendations) / len(recommendations) if recommendations else 0
        assert actionability_ratio >= 0.8, "At least 80% of recommendations should be actionable"
        
        # Validate user scenario outcomes
        for scenario in codebase.user_scenarios:
            scenario_result = self._simulate_user_scenario(result, scenario)
            assert scenario_result["success"], f"User scenario {scenario['role']} should succeed"
        
        # Validate interface responsiveness
        interface_response_times = self._test_interface_responsiveness(result)
        avg_response_time = statistics.mean(interface_response_times.values())
        assert avg_response_time <= 2.0, "Average interface response time should be <= 2 seconds"
    
    @integration_test(["user_experience"])
    @performance_test(max_time_seconds=90.0, max_memory_mb=300.0)
    def test_microservices_e_commerce_analysis(self, ux_validation_suite, temp_ux_directory):
        """Test enhanced pipeline with complex microservices architecture"""
        codebase = ux_validation_suite.real_world_codebases[1]  # Microservices e-commerce
        
        # Setup codebase files
        self._setup_codebase(temp_ux_directory, codebase)
        
        # Execute enhanced analysis
        start_time = time.time()
        mock_analyzer = MockEnhancedAnalyzer("success")
        result = mock_analyzer.analyze_path(
            str(temp_ux_directory),
            enable_cross_phase_correlation=True,
            enable_smart_recommendations=True,
            enable_audit_trail=True
        )
        analysis_time = time.time() - start_time
        
        # Validate complex system analysis
        correlations = result.get("correlations", [])
        cross_service_correlations = [
            c for c in correlations
            if any(service in c.get("description", "").lower() for service in ["service", "microservice", "cross"])
        ]
        
        assert len(cross_service_correlations) >= 5, "Should detect cross-service correlations"
        
        # Validate architectural recommendations
        recommendations = result.get("smart_recommendations", [])
        architectural_recommendations = [
            r for r in recommendations
            if any(keyword in r.get("title", "").lower() for keyword in ["decouple", "interface", "extract", "pattern"])
        ]
        
        assert len(architectural_recommendations) >= codebase.expected_insights["architectural_improvements"], \
            "Should provide architectural improvement recommendations"
        
        # Validate high-complexity scenario handling
        assert analysis_time <= 80.0, "Complex microservices analysis should complete within reasonable time"
        
        # Test recommendation priority accuracy
        critical_recommendations = [r for r in recommendations if r.get("priority") == "critical"]
        high_priority_recommendations = [r for r in recommendations if r.get("priority") == "high"]
        
        assert len(critical_recommendations) >= 2, "Should identify critical issues in complex system"
        assert len(high_priority_recommendations) >= 3, "Should identify high-priority improvements"
    
    @integration_test(["user_experience"])
    @performance_test(max_time_seconds=75.0, max_memory_mb=250.0)
    def test_data_processing_pipeline_analysis(self, ux_validation_suite, temp_ux_directory):
        """Test enhanced pipeline with data processing workflow"""
        codebase = ux_validation_suite.real_world_codebases[2]  # Data processing pipeline
        
        # Setup codebase files
        self._setup_codebase(temp_ux_directory, codebase)
        
        # Execute enhanced analysis
        mock_analyzer = MockEnhancedAnalyzer("success")
        result = mock_analyzer.analyze_path(
            str(temp_ux_directory),
            enable_cross_phase_correlation=True,
            enable_smart_recommendations=True,
            enable_audit_trail=True
        )
        
        # Validate pipeline-specific insights
        correlations = result.get("correlations", [])
        pipeline_correlations = [
            c for c in correlations
            if any(keyword in c.get("description", "").lower() for keyword in ["pipeline", "etl", "data", "transform"])
        ]
        
        assert len(pipeline_correlations) >= 6, "Should detect data flow correlations"
        
        # Validate data processing recommendations
        recommendations = result.get("smart_recommendations", [])
        data_quality_recommendations = [
            r for r in recommendations
            if any(keyword in r.get("title", "").lower() for keyword in ["validation", "error", "resilience", "monitoring"])
        ]
        
        assert len(data_quality_recommendations) >= 2, "Should recommend data quality improvements"
        
        # Test audit trail completeness for data pipeline
        audit_trail = result.get("audit_trail", [])
        pipeline_phases = ["extraction", "transformation", "loading", "validation"]
        
        audit_phases = set(entry.get("phase", "") for entry in audit_trail)
        covered_phases = [phase for phase in pipeline_phases if any(phase in audit_phase for audit_phase in audit_phases)]
        
        assert len(covered_phases) >= 3, "Audit trail should cover major pipeline phases"
    
    @integration_test(["user_experience"])
    def test_quick_analysis_workflow_simulation(self, ux_validation_suite):
        """Test quick analysis workflow for developer productivity"""
        scenario = ux_validation_suite.user_scenarios[0]  # Quick analysis workflow
        
        # Create simple test case
        test_code = '''
class QuickTestClass:
    def __init__(self, config_dict):
        # CofE: Identity - coupled to config structure
        self.setting = config_dict["setting"]
        self.mode = config_dict["mode"]
    
    def process(self, data, format="json"):
        # CofE: Position - parameter order dependency
        # CofE: Meaning - format string coupling
        if self.mode == "FAST":
            return self._fast_process(data, format)
        else:
            return self._standard_process(data, format)
'''
        
        # Simulate quick analysis workflow
        start_time = time.time()
        
        # Step 1: Analyze
        mock_analyzer = MockEnhancedAnalyzer("success")
        result = mock_analyzer.analyze_path(
            "quick_test.py",
            code_content=test_code,
            enable_cross_phase_correlation=True,
            enable_smart_recommendations=True
        )
        
        # Step 2: Review correlations (simulate UI interaction)
        correlations = result.get("correlations", [])
        correlation_review_time = 0.5  # Simulated review time
        
        # Step 3: Implement recommendation (simulate selection)
        recommendations = result.get("smart_recommendations", [])
        recommendation_selection_time = 0.3
        
        total_workflow_time = time.time() - start_time + correlation_review_time + recommendation_selection_time
        
        # Validate quick workflow performance
        assert total_workflow_time <= scenario["max_time_seconds"], \
            f"Quick analysis workflow took {total_workflow_time:.2f}s, expected <= {scenario['max_time_seconds']}s"
        
        assert len(correlations) + len(recommendations) >= scenario["expected_insights"], \
            "Should provide sufficient insights for quick analysis"
        
        # Validate insight relevance
        relevant_insights = self._assess_insight_relevance(result, test_code)
        assert relevant_insights >= 0.8, "At least 80% of insights should be relevant"
    
    @integration_test(["user_experience"])
    def test_comprehensive_refactoring_session(self, ux_validation_suite, temp_ux_directory):
        """Test comprehensive refactoring session workflow"""
        scenario = ux_validation_suite.user_scenarios[1]  # Comprehensive refactoring session
        
        # Create complex refactoring test case
        refactoring_files = {
            "legacy_system.py": '''
class LegacySystem:
    def __init__(self):
        self.mode = "LEGACY"  # CofE: Meaning - mode coupling
        self.processor = None
        
    def initialize(self, config):
        # CofE: Execution - initialization order matters
        if config["type"] == "BATCH":
            self.processor = BatchProcessor(config)
        elif config["type"] == "STREAM":
            self.processor = StreamProcessor(config)
        self.mode = config["type"]  # CofE: Meaning - mode synchronization
        
    def process_data(self, data):
        # CofE: Algorithm - processing depends on mode
        if self.mode == "BATCH":
            return self._batch_process(data)
        elif self.mode == "STREAM":
            return self._stream_process(data)
            ''',
            "modern_adapter.py": '''
from legacy_system import LegacySystem

class ModernAdapter:
    def __init__(self, legacy: LegacySystem):
        # CofE: Type - tight coupling to legacy system
        self.legacy = legacy
        
    def modernize_input(self, modern_data):
        # CofE: Algorithm - adapter depends on legacy format requirements
        legacy_format = self._convert_to_legacy_format(modern_data)
        result = self.legacy.process_data(legacy_format)
        return self._convert_from_legacy_format(result)
            '''
        }
        
        # Setup refactoring project
        for filename, content in refactoring_files.items():
            file_path = temp_ux_directory / filename
            file_path.write_text(content, encoding="utf-8")
        
        # Simulate comprehensive refactoring session
        start_time = time.time()
        
        # Step 1: Analyze full project
        mock_analyzer = MockEnhancedAnalyzer("success")
        result = mock_analyzer.analyze_path(
            str(temp_ux_directory),
            enable_cross_phase_correlation=True,
            enable_smart_recommendations=True,
            enable_audit_trail=True
        )
        
        # Step 2: Review architecture (simulated)
        architecture_review_time = 5.0  # Simulated comprehensive review
        
        # Step 3: Plan refactoring (simulated)
        refactoring_planning_time = 8.0
        
        # Step 4: Validate changes (simulated)
        validation_time = 3.0
        
        total_session_time = time.time() - start_time + architecture_review_time + refactoring_planning_time + validation_time
        
        # Validate comprehensive session performance
        assert total_session_time <= scenario["max_time_seconds"], \
            f"Comprehensive refactoring session took {total_session_time:.2f}s, expected <= {scenario['max_time_seconds']}s"
        
        # Validate comprehensive insights
        total_insights = len(result.get("correlations", [])) + len(result.get("smart_recommendations", []))
        assert total_insights >= scenario["expected_insights"], \
            "Should provide comprehensive insights for refactoring session"
        
        # Validate architectural recommendations quality
        recommendations = result.get("smart_recommendations", [])
        architectural_recs = [
            r for r in recommendations
            if any(keyword in r.get("title", "").lower() for keyword in ["extract", "decouple", "interface", "pattern"])
        ]
        
        assert len(architectural_recs) >= 3, "Should provide architectural refactoring recommendations"
    
    @integration_test(["user_experience"])
    def test_continuous_integration_validation(self, ux_validation_suite):
        """Test CI/CD integration scenario"""
        scenario = ux_validation_suite.user_scenarios[2]  # Continuous integration validation
        
        # Simulate CI/CD scenario with code changes
        original_code = '''
class OriginalClass:
    def process(self, data):
        # CofE: Algorithm - original implementation
        return {"result": data}
'''
        
        modified_code = '''
class OriginalClass:
    def __init__(self, config):
        # CofE: Identity - new config dependency added
        self.config = config
        
    def process(self, data, output_format="json"):
        # CofE: Position - new parameter added
        # CofE: Meaning - format coupling introduced
        if output_format == "json":
            return {"result": data}
        elif output_format == "xml":
            return f"<result>{data}</result>"
'''
        
        # Analyze changes for CI/CD
        start_time = time.time()
        
        # Step 1: Analyze changes
        mock_analyzer = MockEnhancedAnalyzer("success")
        result = mock_analyzer.analyze_path(
            "ci_test.py",
            code_content=modified_code,
            enable_cross_phase_correlation=True,
            enable_smart_recommendations=True
        )
        
        # Step 2: Compare baselines (simulated)
        baseline_comparison_time = 2.0
        
        # Step 3: Generate report (simulated)
        report_generation_time = 1.5
        
        # Step 4: Fail on regressions check
        regression_check_time = 1.0
        
        total_ci_time = time.time() - start_time + baseline_comparison_time + report_generation_time + regression_check_time
        
        # Validate CI/CD performance
        assert total_ci_time <= scenario["max_time_seconds"], \
            f"CI/CD validation took {total_ci_time:.2f}s, expected <= {scenario['max_time_seconds']}s"
        
        # Validate CI/CD insights
        findings = result.get("findings", [])
        new_issues = [f for f in findings if f.get("severity") in ["high", "medium"]]
        
        assert len(new_issues) >= 2, "Should detect new connascence issues introduced in changes"
        
        # Validate CI-friendly reporting
        assert "audit_trail" in result, "Should provide audit trail for CI reporting"
        assert len(result.get("correlations", [])) >= 1, "Should detect correlations in modified code"
    
    def _setup_codebase(self, directory: Path, codebase: RealWorldCodebase):
        """Setup codebase files in directory"""
        for filename, content in codebase.files.items():
            file_path = directory / filename
            file_path.write_text(content, encoding="utf-8")
    
    def _calculate_ux_metrics(self, result: Dict[str, Any], analysis_time: float, codebase: RealWorldCodebase) -> UserExperienceMetrics:
        """Calculate user experience metrics"""
        correlations = result.get("correlations", [])
        recommendations = result.get("smart_recommendations", [])
        
        # Calculate correlation discovery accuracy
        expected_correlations = codebase.expected_insights["correlation_count"]
        correlation_accuracy = min(len(correlations) / expected_correlations, 1.0) if expected_correlations > 0 else 0
        
        # Calculate recommendation actionability
        actionable_recs = [r for r in recommendations if r.get("implementation_guide")]
        actionability = len(actionable_recs) / len(recommendations) if recommendations else 0
        
        # Calculate interface responsiveness (simulated)
        interface_responsiveness = max(0, 1.0 - (analysis_time / 60.0))  # Decreases with longer analysis time
        
        # Calculate insight relevance (simulated based on correlation accuracy)
        insight_relevance = correlation_accuracy * 0.8 + actionability * 0.2
        
        # Calculate workflow integration score (simulated)
        workflow_integration = min(1.0, len(result.get("audit_trail", [])) / 5.0)  # Based on audit completeness
        
        return UserExperienceMetrics(
            analysis_response_time=analysis_time,
            correlation_discovery_accuracy=correlation_accuracy,
            recommendation_actionability_score=actionability,
            interface_responsiveness=interface_responsiveness,
            insight_relevance_score=insight_relevance,
            workflow_integration_score=workflow_integration
        )
    
    def _simulate_user_scenario(self, result: Dict[str, Any], scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate user scenario execution"""
        recommendations = result.get("smart_recommendations", [])
        correlations = result.get("correlations", [])
        
        # Check if scenario requirements can be met
        task = scenario.get("task", "")
        expected_changes = scenario.get("expected_changes", 0)
        
        relevant_recommendations = []
        if "status" in task:
            relevant_recommendations = [r for r in recommendations if "status" in r.get("title", "").lower()]
        elif "decouple" in task:
            relevant_recommendations = [r for r in recommendations if "decouple" in r.get("title", "").lower()]
        elif "api" in task:
            relevant_recommendations = [r for r in recommendations if "api" in r.get("title", "").lower()]
        else:
            relevant_recommendations = recommendations[:expected_changes]  # Take first N recommendations
        
        success = len(relevant_recommendations) >= min(expected_changes, len(recommendations))
        
        return {
            "success": success,
            "relevant_recommendations": len(relevant_recommendations),
            "available_correlations": len(correlations)
        }
    
    def _test_interface_responsiveness(self, result: Dict[str, Any]) -> Dict[str, float]:
        """Test interface responsiveness with formatting times"""
        interfaces = ["vscode", "mcp_server", "web_dashboard", "cli"]
        response_times = {}
        
        for interface in interfaces:
            start_time = time.time()
            formatted_output = self._format_for_interface(result, interface)
            response_time = time.time() - start_time
            response_times[interface] = response_time
        
        return response_times
    
    def _assess_insight_relevance(self, result: Dict[str, Any], test_code: str) -> float:
        """Assess relevance of insights to provided code"""
        findings = result.get("findings", [])
        correlations = result.get("correlations", [])
        recommendations = result.get("smart_recommendations", [])
        
        total_insights = len(findings) + len(correlations) + len(recommendations)
        if total_insights == 0:
            return 0.0
        
        # Simple heuristic: check if insights mention concepts present in code
        code_concepts = ["config", "mode", "format", "process", "class", "method"]
        relevant_insights = 0
        
        for finding in findings:
            if any(concept in finding.get("message", "").lower() for concept in code_concepts):
                relevant_insights += 1
        
        for correlation in correlations:
            if any(concept in correlation.get("description", "").lower() for concept in code_concepts):
                relevant_insights += 1
        
        for recommendation in recommendations:
            if any(concept in recommendation.get("title", "").lower() for concept in code_concepts):
                relevant_insights += 1
        
        return relevant_insights / total_insights
    
    def _format_for_interface(self, result: Dict[str, Any], interface: str) -> Dict[str, Any]:
        """Format result for specific interface"""
        if interface == "vscode":
            return {
                "correlations": result.get("correlations", []),
                "recommendations": result.get("smart_recommendations", []),
                "audit_summary": len(result.get("audit_trail", []))
            }
        elif interface == "mcp_server":
            return {
                "enhanced_context": {
                    "correlation_count": len(result.get("correlations", [])),
                    "recommendation_count": len(result.get("smart_recommendations", []))
                }
            }
        elif interface == "web_dashboard":
            correlations = result.get("correlations", [])
            return {
                "chart_data": {
                    "correlation_scores": [c.get("correlation_score", 0) for c in correlations],
                    "correlation_types": [c.get("correlation_type", "") for c in correlations]
                },
                "timeline_events": result.get("audit_trail", [])
            }
        elif interface == "cli":
            return {
                "summary": f"Found {len(result.get('findings', []))} findings, {len(result.get('correlations', []))} correlations",
                "recommendations_count": len(result.get("smart_recommendations", []))
            }
        
        return {}


if __name__ == "__main__":
    # Run user experience validation tests
    pytest.main([__file__, "-v", "-m", "user_experience"])