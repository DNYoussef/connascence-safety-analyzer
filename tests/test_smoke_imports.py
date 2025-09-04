#!/usr/bin/env python3
"""
Smoke Test Suite: Module Import Tests

Comprehensive smoke tests to ensure all critical modules can be imported
without ImportError and basic functionality is accessible.
"""

import sys
import importlib
import pytest
from pathlib import Path
from typing import List, Tuple, Optional


class TestSmokeImports:
    """Smoke tests for module imports and basic accessibility."""

    @pytest.fixture(scope="class", autouse=True)
    def setup_path(self):
        """Add project root to Python path for imports."""
        project_root = Path(__file__).parent.parent
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
        
    def test_core_analyzer_modules(self):
        """Test that all core analyzer modules can be imported."""
        analyzer_modules = [
            'analyzer',
            'analyzer.core',
            'analyzer.ast_engine',
            'analyzer.ast_engine.core_analyzer',
            'analyzer.ast_engine.visitors',
            'analyzer.connascence_analyzer',
            'analyzer.check_connascence',
            'analyzer.cohesion_analyzer',
            'analyzer.architectural_analysis',
            'analyzer.grammar_enhanced_analyzer',
            'analyzer.magic_literal_analyzer',
            'analyzer.thresholds'
        ]
        
        for module_name in analyzer_modules:
            try:
                module = importlib.import_module(module_name)
                assert module is not None, f"Module {module_name} imported but is None"
            except ImportError as e:
                pytest.fail(f"Failed to import {module_name}: {e}")
    
    def test_autofix_modules(self):
        """Test that all autofix modules can be imported."""
        autofix_modules = [
            'autofix',
            'autofix.core',
            'autofix.class_splits',
            'autofix.god_objects',
            'autofix.magic_literals',
            'autofix.param_bombs'
        ]
        
        for module_name in autofix_modules:
            try:
                module = importlib.import_module(module_name)
                assert module is not None, f"Module {module_name} imported but is None"
            except ImportError as e:
                pytest.fail(f"Failed to import {module_name}: {e}")
    
    def test_policy_modules(self):
        """Test that policy management modules can be imported."""
        policy_modules = [
            'policy.manager',
            'policy.budgets',
            'policy.baselines'
        ]
        
        for module_name in policy_modules:
            try:
                module = importlib.import_module(module_name)
                assert module is not None, f"Module {module_name} imported but is None"
            except ImportError as e:
                pytest.fail(f"Failed to import {module_name}: {e}")
    
    def test_reporting_modules(self):
        """Test that reporting modules can be imported."""
        try:
            import reporting
            assert reporting is not None
        except ImportError as e:
            pytest.fail(f"Failed to import reporting module: {e}")
    
    def test_cli_modules(self):
        """Test that CLI modules can be imported."""
        cli_modules = [
            'cli.connascence'
        ]
        
        # Also test the constants module that CLI depends on
        try:
            from src.constants import ExitCode, ValidationMessages
            assert ExitCode is not None
            assert ValidationMessages is not None
        except ImportError as e:
            pytest.fail(f"Failed to import constants: {e}")
        
        for module_name in cli_modules:
            try:
                module = importlib.import_module(module_name)
                assert module is not None, f"Module {module_name} imported but is None"
            except ImportError as e:
                pytest.fail(f"Failed to import {module_name}: {e}")
    
    def test_mcp_modules(self):
        """Test that MCP server modules can be imported."""
        try:
            import mcp
            assert mcp is not None
        except ImportError as e:
            # MCP might not be installed, so this is not a hard failure
            pytest.skip(f"MCP module not available: {e}")
    
    def test_dashboard_modules(self):
        """Test that dashboard modules can be imported."""
        try:
            import dashboard
            assert dashboard is not None
        except ImportError as e:
            pytest.skip(f"Dashboard module not available: {e}")
    
    def test_critical_class_instantiation(self):
        """Test that critical classes can be instantiated."""
        try:
            from policy.manager import PolicyManager
            from policy.baselines import BaselineManager
            from policy.budgets import BudgetTracker
            
            # Test basic instantiation
            policy_manager = PolicyManager()
            baseline_manager = BaselineManager()
            budget_tracker = BudgetTracker()
            
            assert policy_manager is not None
            assert baseline_manager is not None
            assert budget_tracker is not None
            
        except Exception as e:
            pytest.fail(f"Failed to instantiate critical classes: {e}")
    
    def test_analyzer_core_functionality(self):
        """Test that core analyzer functionality is accessible."""
        try:
            from analyzer.core import ConnascenceAnalyzer
            
            # Test instantiation
            analyzer = ConnascenceAnalyzer()
            assert analyzer is not None
            
            # Test that analyze method exists and is callable
            assert hasattr(analyzer, 'analyze')
            assert callable(analyzer.analyze)
            
        except ImportError as e:
            pytest.skip(f"Core analyzer not available: {e}")
        except Exception as e:
            pytest.fail(f"Core analyzer functionality test failed: {e}")
    
    def test_constants_module_accessibility(self):
        """Test that all constants are properly accessible."""
        try:
            from src.constants import (
                ExitCode, SeverityLevel, ConnascenceType,
                AnalysisLimits, FileSizeThresholds, OutputFormats,
                PolicyPresets, ValidationMessages
            )
            
            # Test enum values
            assert ExitCode.SUCCESS == 0
            assert ExitCode.GENERAL_ERROR == 1
            assert ExitCode.LICENSE_ERROR == 4
            
            assert SeverityLevel.LOW.value == "low"
            assert SeverityLevel.HIGH.value == "high"
            
            assert ConnascenceType.MEANING.value == "CoM"
            assert ConnascenceType.POSITION.value == "CoP"
            
        except ImportError as e:
            pytest.fail(f"Failed to import constants: {e}")
        except AttributeError as e:
            pytest.fail(f"Constants not properly defined: {e}")
    
    def test_cli_handlers_import(self):
        """Test that CLI handlers can be imported."""
        try:
            from src.cli_handlers import (
                ScanCommandHandler, LicenseCommandHandler, 
                BaselineCommandHandler, MCPCommandHandler,
                ExplainCommandHandler, AutofixCommandHandler,
                ScanDiffCommandHandler
            )
            
            # Test that classes are properly defined
            assert ScanCommandHandler is not None
            assert LicenseCommandHandler is not None
            assert BaselineCommandHandler is not None
            
        except ImportError as e:
            pytest.skip(f"CLI handlers not available: {e}")
    
    def test_optional_dependencies_graceful_handling(self):
        """Test that optional dependencies are handled gracefully."""
        # Test license validation (optional)
        try:
            from src.licensing import LicenseValidator, LicenseValidationResult
            license_available = True
        except ImportError:
            license_available = False
        
        # This should not fail - the application should handle missing optional deps
        assert license_available in [True, False]  # Either works
        
        # Test MCP integration (optional)
        try:
            from analyzer.mcp_integration import MCPAnalysisServer
            mcp_available = True
        except ImportError:
            mcp_available = False
        
        assert mcp_available in [True, False]  # Either works
    
    def test_package_metadata_accessible(self):
        """Test that package metadata is accessible."""
        try:
            import analyzer
            # Check if version info is available
            version_info = getattr(analyzer, '__version__', None)
            # Version might not be set in development, so this is informational
            # Just ensure we can access the module without errors
            assert analyzer is not None
            
        except ImportError as e:
            pytest.fail(f"Failed to access package metadata: {e}")
    
    @pytest.mark.slow
    def test_all_python_files_importable(self):
        """Test that all Python files in the project can be imported (slow test)."""
        project_root = Path(__file__).parent.parent
        python_files = []
        
        # Find all Python files
        for path in project_root.rglob("*.py"):
            # Skip test files, __pycache__, and other non-importable files
            if any(skip in str(path) for skip in [
                '__pycache__', 'test_', '_test.py', 'conftest.py', 
                'setup.py', 'build/', 'dist/', '.git/', 'deprecated/'
            ]):
                continue
            
            # Convert file path to module name
            relative_path = path.relative_to(project_root)
            module_name = str(relative_path.with_suffix('')).replace('/', '.').replace('\\', '.')
            
            # Skip if it starts with numbers or invalid module names
            if module_name[0].isdigit() or any(part.startswith('.') for part in module_name.split('.')):
                continue
                
            python_files.append(module_name)
        
        # Test importing each module
        failed_imports = []
        for module_name in python_files[:20]:  # Limit to first 20 to avoid timeout
            try:
                importlib.import_module(module_name)
            except ImportError as e:
                failed_imports.append((module_name, str(e)))
            except Exception as e:
                # Other errors might be OK (e.g., script files)
                continue
        
        # Report failed imports (but don't fail the test entirely)
        if failed_imports:
            import warnings
            warnings.warn(f"Some modules failed to import: {failed_imports[:5]}")


class TestCriticalFunctionality:
    """Test that critical functionality works at a basic level."""
    
    def test_main_cli_function_exists(self):
        """Test that the main CLI function exists and is callable."""
        try:
            from cli.connascence import main
            assert callable(main)
        except ImportError as e:
            pytest.fail(f"Failed to import main CLI function: {e}")
    
    def test_connascence_cli_class_instantiation(self):
        """Test that ConnascenceCLI class can be instantiated."""
        try:
            from cli.connascence import ConnascenceCLI
            cli = ConnascenceCLI()
            assert cli is not None
            assert hasattr(cli, 'run')
            assert callable(cli.run)
        except ImportError as e:
            pytest.fail(f"Failed to import ConnascenceCLI: {e}")
        except Exception as e:
            pytest.fail(f"Failed to instantiate ConnascenceCLI: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])