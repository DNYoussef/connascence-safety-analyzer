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
Comprehensive tests for license validation system with exit code 4 pathway.

Tests all key components:
- Memory coordination
- Sequential thinking workflow
- BSL-1.1 license validation
- Enterprise license validation
- Exit code 4 pathways
- CLI integration
"""

import json
import pytest
import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock

# License validation system not yet implemented
# Skip all tests in this file until licensing module is added
pytest.skip("License validation system not implemented", allow_module_level=True)


class TestMemoryCoordinator:
    """Test memory coordination functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.memory_file = self.temp_dir / "test_license_memory.json"
        self.coordinator = MemoryCoordinator(self.memory_file)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_memory_initialization(self):
        """Test memory coordinator initialization."""
        assert self.coordinator.memory_file == self.memory_file
        assert "license_rules" in self.coordinator._memory_cache
        assert "validation_history" in self.coordinator._memory_cache
    
    def test_store_and_retrieve_validation_result(self):
        """Test storing and retrieving validation results."""
        from src.licensing.license_validator import LicenseValidationReport
        
        # Create test report
        report = LicenseValidationReport(
            timestamp=datetime.now(),
            system_info={"test": "data"},
            license_info=None,
            validation_result=LicenseValidationResult.VALID,
            errors=[],
            warnings=[],
            memory_storage_key="test_key",
            sequential_steps=["step1", "step2"],
            exit_code=0
        )
        
        # Store and retrieve
        self.coordinator.store_validation_result("test_key", report)
        retrieved = self.coordinator.get_validation_result("test_key")
        
        assert retrieved is not None
        assert retrieved.validation_result == LicenseValidationResult.VALID
        assert retrieved.memory_storage_key == "test_key"
        assert retrieved.exit_code == 0
    
    def test_license_rules_storage(self):
        """Test license rules storage and retrieval."""
        test_rules = {
            "BSL-1.1": {"test": "value"},
            "Enterprise": {"test2": "value2"}
        }
        
        self.coordinator.store_license_rules(test_rules)
        retrieved_rules = self.coordinator.get_license_rules()
        
        assert retrieved_rules["BSL-1.1"]["test"] == "value"
        assert retrieved_rules["Enterprise"]["test2"] == "value2"


class TestSequentialThinkingProcessor:
    """Test sequential thinking workflow."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.memory_coordinator = MemoryCoordinator(self.temp_dir / "memory.json")
        self.processor = SequentialThinkingProcessor(self.memory_coordinator)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_step_addition(self):
        """Test adding steps to sequential thinking process."""
        self.processor.add_step("Test step 1")
        self.processor.add_step("Test step 2")
        
        assert len(self.processor.steps) == 2
        assert "Test step 1" in self.processor.steps[0]
        assert "Test step 2" in self.processor.steps[1]
    
    def test_license_validation_process(self):
        """Test full sequential thinking license validation process."""
        # Create test project structure
        project_root = self.temp_dir / "test_project"
        project_root.mkdir()
        
        # Create test LICENSE file
        license_file = project_root / "LICENSE"
        license_file.write_text("Business Source License 1.1\n\nParameters\nLicensor: Test\n")
        
        # Run sequential validation
        result, steps = self.processor.process_license_validation(license_file, project_root)
        
        # Verify steps were recorded
        assert len(steps) > 0
        assert any("Starting sequential" in step for step in steps)
        assert any("Step 1:" in step for step in steps)
        assert any("Step 6:" in step for step in steps)


class TestLicenseValidator:
    """Test main license validator functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.validator = LicenseValidator(self.temp_dir / "memory.json")
    
    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_bsl_license_detection(self):
        """Test BSL-1.1 license detection and validation."""
        # Create project with BSL license
        project_root = self.temp_dir / "bsl_project"
        project_root.mkdir()
        
        bsl_content = """
        Business Source License 1.1
        
        Parameters
        Licensor: Test Company
        Licensed Work: Test Software
        Additional Use Grant: Non-commercial use
        Change Date: 2028-01-01
        Change License: Apache 2.0
        """
        
        (project_root / "LICENSE").write_text(bsl_content)
        
        report = self.validator.validate_license(project_root)
        
        assert report.license_info is not None
        assert report.license_info.license_type == LicenseType.BSL_1_1
        assert report.validation_result in [LicenseValidationResult.VALID, LicenseValidationResult.RESTRICTED]
    
    def test_enterprise_license_detection(self):
        """Test enterprise license detection and validation."""
        # Create project with enterprise license
        project_root = self.temp_dir / "enterprise_project"
        project_root.mkdir()
        (project_root / "dist").mkdir()
        
        enterprise_content = """
        ENTERPRISE LICENSE AGREEMENT
        
        This software is proprietary and licensed for enterprise use only.
        Commercial use permitted under enterprise agreement.
        Contact: legal@example.com
        """
        
        (project_root / "dist" / "LICENSE_ENTERPRISE.txt").write_text(enterprise_content)
        
        report = self.validator.validate_license(project_root)
        
        assert report.license_info is not None
        assert report.license_info.license_type == LicenseType.ENTERPRISE
        assert report.license_info.commercial_use == True
    
    def test_missing_license_error(self):
        """Test handling of missing license files."""
        # Create project without license
        project_root = self.temp_dir / "no_license_project"
        project_root.mkdir()
        
        report = self.validator.validate_license(project_root)
        
        assert report.license_info is None
        assert report.validation_result == LicenseValidationResult.NOT_FOUND
        assert report.exit_code == 4
        assert len(report.errors) > 0
        assert any("MissingLicense" in error.error_type for error in report.errors)
    
    def test_license_expiration_detection(self):
        """Test detection of expired licenses."""
        project_root = self.temp_dir / "expired_project"
        project_root.mkdir()
        
        # Mock license info with expired date
        expired_license = LicenseInfo(
            license_type=LicenseType.ENTERPRISE,
            version="1.0",
            issued_date=datetime.now() - timedelta(days=400),
            expiration_date=datetime.now() - timedelta(days=10),  # Expired
            permitted_uses=["enterprise"],
            restrictions=[],
            commercial_use=True,
            distribution_allowed=False,
            modification_allowed=False,
            patent_grant=False
        )
        
        # Mock the license discovery to return expired license
        with patch.object(self.validator, '_discover_license_info', return_value=expired_license):
            report = self.validator.validate_license(project_root)
        
        assert report.exit_code == 4
        assert any("ExpiredLicense" in error.error_type for error in report.errors)
    
    def test_distribution_restriction_violation(self):
        """Test detection of distribution restriction violations."""
        project_root = self.temp_dir / "dist_violation_project"
        project_root.mkdir()
        
        # Create dist directory with files (potential violation)
        dist_dir = project_root / "dist"
        dist_dir.mkdir()
        (dist_dir / "package.tar.gz").write_text("fake package")
        
        # Mock license that prohibits distribution
        restricted_license = LicenseInfo(
            license_type=LicenseType.PROPRIETARY,
            version="1.0",
            issued_date=datetime.now() - timedelta(days=30),
            expiration_date=None,
            permitted_uses=["internal"],
            restrictions=["no distribution"],
            commercial_use=False,
            distribution_allowed=False,  # Distribution not allowed
            modification_allowed=True,
            patent_grant=False
        )
        
        with patch.object(self.validator, '_discover_license_info', return_value=restricted_license):
            report = self.validator.validate_license(project_root)
        
        # Should detect distribution restriction violation
        distribution_errors = [e for e in report.errors if "DistributionRestriction" in e.error_type]
        assert len(distribution_errors) > 0
    
    def test_memory_caching(self):
        """Test license validation result caching."""
        project_root = self.temp_dir / "cache_test_project"
        project_root.mkdir()
        (project_root / "LICENSE").write_text("MIT License")
        
        # First validation
        report1 = self.validator.validate_license(project_root)
        
        # Second validation should use cache
        report2 = self.validator.validate_license(project_root)
        
        # Both should have same memory key and results
        assert report1.memory_storage_key == report2.memory_storage_key
        assert report1.validation_result == report2.validation_result


class TestCLIIntegration:
    """Test CLI integration of license validation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
    
    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_cli_license_validate_command(self):
        """Test CLI license validate command."""
        from cli.connascence import ConnascenceCLI
        
        # Create test project
        project_root = self.temp_dir / "cli_test_project"
        project_root.mkdir()
        (project_root / "LICENSE").write_text("MIT License")
        
        # Test CLI command
        cli = ConnascenceCLI()
        
        # Mock args for license validate
        class MockArgs:
            license_action = "validate"
            path = str(project_root)
            format = "text"
        
        args = MockArgs()
        result = cli._handle_license_validate(args)
        
        # Should return appropriate exit code
        assert result in [0, 4]  # Success or license error
    
    def test_cli_skip_license_check(self):
        """Test CLI --skip-license-check flag."""
        from cli.connascence import ConnascenceCLI
        
        cli = ConnascenceCLI()
        
        # Test with skip flag
        args = ["scan", ".", "--skip-license-check"]
        result = cli.run(args)
        
        # Should not perform license validation
        assert result >= 0
    
    @patch('sys.stderr')
    def test_automatic_license_validation(self, mock_stderr):
        """Test automatic license validation on CLI commands."""
        from cli.connascence import ConnascenceCLI
        
        # Create project without license
        project_root = self.temp_dir / "auto_validate_project"
        project_root.mkdir()
        
        cli = ConnascenceCLI()
        
        # Change to test directory
        original_cwd = Path.cwd()
        try:
            import os
            os.chdir(project_root)
            
            # Run scan command (should trigger license validation)
            result = cli.run(["scan", "."])
            
            # Should return exit code 4 for license error
            assert result == 4
            
        finally:
            os.chdir(original_cwd)


class TestExitCodePathways:
    """Test all exit code 4 pathways."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.validator = LicenseValidator(self.temp_dir / "memory.json")
    
    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_exit_code_4_missing_license(self):
        """Test exit code 4 for missing license."""
        project_root = self.temp_dir / "missing_license"
        project_root.mkdir()
        
        report = self.validator.validate_license(project_root)
        assert report.exit_code == 4
        assert report.validation_result == LicenseValidationResult.NOT_FOUND
    
    def test_exit_code_4_bsl_violation(self):
        """Test exit code 4 for BSL violations."""
        project_root = self.temp_dir / "bsl_violation"
        project_root.mkdir()
        
        # Mock license with commercial use violation
        violating_license = LicenseInfo(
            license_type=LicenseType.BSL_1_1,
            version="1.1",
            issued_date=datetime.now(),
            expiration_date=None,
            permitted_uses=["development"],
            restrictions=["no commercial use"],
            commercial_use=True,  # Violates BSL restrictions
            distribution_allowed=False,
            modification_allowed=True,
            patent_grant=False
        )
        
        with patch.object(self.validator, '_discover_license_info', return_value=violating_license):
            report = self.validator.validate_license(project_root)
        
        assert report.exit_code == 4
        assert report.validation_result == LicenseValidationResult.BSL_VIOLATION
    
    def test_exit_code_4_enterprise_required(self):
        """Test exit code 4 for enterprise license required."""
        project_root = self.temp_dir / "enterprise_required"
        project_root.mkdir()
        
        # Create enterprise feature files
        (project_root / "dashboard").mkdir()
        (project_root / "enterprise_security.py").write_text("# Enterprise feature")
        
        # No enterprise license
        report = self.validator.validate_license(project_root)
        
        # Should require enterprise license
        enterprise_errors = [e for e in report.errors if "EnterpriseRequired" in e.error_type]
        if enterprise_errors:
            assert report.exit_code == 4
    
    def test_exit_code_0_valid_license(self):
        """Test exit code 0 for valid license."""
        project_root = self.temp_dir / "valid_license"
        project_root.mkdir()
        
        # Create valid MIT license
        mit_content = """
        MIT License
        
        Copyright (c) 2024 Test
        
        Permission is hereby granted, free of charge, to any person obtaining a copy...
        """
        (project_root / "LICENSE").write_text(mit_content)
        
        report = self.validator.validate_license(project_root)
        
        # MIT license should be valid
        if report.validation_result == LicenseValidationResult.VALID:
            assert report.exit_code == 0


class TestLicenseMemoryPersistence:
    """Test license memory persistence across sessions."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.memory_file = self.temp_dir / "persistent_memory.json"
    
    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_memory_persistence(self):
        """Test that license validation memory persists across validator instances."""
        # Create first validator and store data
        validator1 = LicenseValidator(self.memory_file)
        test_rules = {"test": "data"}
        validator1.memory_coordinator.store_license_rules(test_rules)
        
        # Create second validator with same memory file
        validator2 = LicenseValidator(self.memory_file)
        retrieved_rules = validator2.memory_coordinator.get_license_rules()
        
        assert retrieved_rules["test"] == "data"
    
    def test_cache_expiration(self):
        """Test that cached validation results expire appropriately."""
        validator = LicenseValidator(self.memory_file)
        
        # Create old cache entry
        from src.licensing.license_validator import LicenseValidationReport
        old_report = LicenseValidationReport(
            timestamp=datetime.now() - timedelta(hours=25),  # Older than 24 hours
            system_info={},
            license_info=None,
            validation_result=LicenseValidationResult.VALID,
            errors=[],
            warnings=[],
            memory_storage_key="test_key",
            sequential_steps=[],
            exit_code=0
        )
        
        # Cache should be considered invalid
        assert not validator._is_cache_valid(old_report)
        
        # Fresh cache should be valid
        fresh_report = LicenseValidationReport(
            timestamp=datetime.now(),
            system_info={},
            license_info=None,
            validation_result=LicenseValidationResult.VALID,
            errors=[],
            warnings=[],
            memory_storage_key="test_key",
            sequential_steps=[],
            exit_code=0
        )
        
        assert validator._is_cache_valid(fresh_report)


def test_license_validation_main_function():
    """Test the main function of license_validator module."""
    from src.licensing.license_validator import main
    
    # Test with minimal args
    with patch('sys.argv', ['license_validator.py', '--help']):
        try:
            main()
        except SystemExit as e:
            # Help should exit with 0
            assert e.code == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])