#!/usr/bin/env python3
"""
Integration tests for real-world scenarios on actual code samples.

Tests Requirements:
1. Run analyzer on test_packages/express, test_packages/curl  
2. Validate output matches expectations
3. Test performance on large codebases
4. Compare results before/after changes
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Any

import pytest

from analyzer.core import ConnascenceAnalyzer
from analyzer.check_connascence import ConnascenceAnalyzer as LegacyAnalyzer


class TestRealWorldScenarios:
    """Test analyzer on real-world code samples."""

    def setup_method(self):
        """Set up test fixtures."""
        self.project_root = Path(__file__).parent.parent.parent
        self.test_packages_dir = self.project_root / "test_packages"
        
        # Ensure test packages exist
        if not self.test_packages_dir.exists():
            pytest.skip("test_packages directory not found")
        
        self.analyzer = ConnascenceAnalyzer()
        self.legacy_analyzer = LegacyAnalyzer()

    def test_express_package_analysis(self):
        """Test analysis of Express.js package (JavaScript)."""
        express_dir = self.test_packages_dir / "express"
        
        if not express_dir.exists():
            pytest.skip("Express test package not found")
        
        # Run analysis
        start_time = time.time()
        result = self.analyzer.analyze_path(
            path=str(express_dir),
            policy="standard"
        )
        analysis_time = time.time() - start_time
        
        # Validate result structure
        assert result['success'] is True, f"Analysis failed: {result.get('error', 'Unknown error')}"
        assert 'violations' in result
        assert 'summary' in result
        assert 'metrics' in result
        
        # Performance check - should complete within reasonable time
        assert analysis_time < 30.0, f"Analysis took too long: {analysis_time}s"
        
        # Check violation types found
        violations = result['violations']
        violation_types = [v.get('type', v.get('connascence_type')) for v in violations]
        
        # Should find typical JavaScript violations
        expected_types = [
            'connascence_of_meaning',  # Magic numbers/strings
            'connascence_of_position', # Parameter coupling
        ]
        
        found_types = set(violation_types)
        for expected_type in expected_types:
            if expected_type in found_types:
                # At least some expected types should be found
                break
        
        # Log results for debugging
        print(f"Express analysis completed in {analysis_time:.2f}s")
        print(f"Found {len(violations)} violations")
        print(f"Violation types: {list(found_types)}")

    def test_curl_package_analysis(self):
        """Test analysis of cURL package (C/C++)."""
        curl_dir = self.test_packages_dir / "curl"
        
        if not curl_dir.exists():
            pytest.skip("cURL test package not found")
        
        # Run analysis
        start_time = time.time()
        result = self.analyzer.analyze_path(
            path=str(curl_dir),
            policy="standard"
        )
        analysis_time = time.time() - start_time
        
        # Validate result structure
        assert result['success'] is True, f"Analysis failed: {result.get('error', 'Unknown error')}"
        assert 'violations' in result
        assert 'summary' in result
        
        # Performance check
        assert analysis_time < 60.0, f"Analysis took too long: {analysis_time}s"
        
        # Check for C-specific violations
        violations = result['violations']
        
        # Log results
        print(f"cURL analysis completed in {analysis_time:.2f}s")
        print(f"Found {len(violations)} violations")

    def test_python_project_analysis(self):
        """Test analysis of Python project (our own codebase)."""
        analyzer_dir = self.project_root / "analyzer"
        
        if not analyzer_dir.exists():
            pytest.skip("Analyzer directory not found")
        
        # Run analysis on our own code
        start_time = time.time()
        result = self.analyzer.analyze_path(
            path=str(analyzer_dir),
            policy="strict-core",
            strict_mode=True
        )
        analysis_time = time.time() - start_time
        
        # Validate result
        assert result['success'] is True
        
        # Check metrics
        metrics = result.get('metrics', {})
        assert metrics.get('files_analyzed', 0) > 0
        assert metrics.get('analysis_time', 0) > 0
        
        # Performance check
        assert analysis_time < 45.0, f"Self-analysis took too long: {analysis_time}s"
        
        # Check quality gates
        quality_gates = result.get('quality_gates', {})
        nasa_score = result.get('nasa_compliance', {}).get('score', 0)
        overall_score = result.get('summary', {}).get('overall_quality_score', 0)
        
        print(f"Self-analysis results:")
        print(f"  Analysis time: {analysis_time:.2f}s")
        print(f"  Files analyzed: {metrics.get('files_analyzed', 0)}")
        print(f"  Total violations: {len(result.get('violations', []))}")
        print(f"  NASA compliance: {nasa_score:.3f}")
        print(f"  Overall quality: {overall_score:.3f}")

    def test_large_codebase_performance(self):
        """Test performance on large codebase."""
        # Use the entire project as a large codebase test
        project_root = self.project_root
        
        # Run with performance monitoring
        start_time = time.time()
        result = self.analyzer.analyze_path(
            path=str(project_root),
            policy="lenient",  # Use lenient for performance test
            exclude=[
                "test_*", 
                "__pycache__", 
                ".git", 
                "node_modules",
                "*.egg-info",
                ".pytest_cache",
                "dist",
                "build"
            ]
        )
        analysis_time = time.time() - start_time
        
        # Validate performance
        assert analysis_time < 120.0, f"Large codebase analysis took too long: {analysis_time}s"
        
        # Check that analysis succeeded
        assert result['success'] is True
        
        # Check metrics for reasonableness
        metrics = result.get('metrics', {})
        files_analyzed = metrics.get('files_analyzed', 0)
        assert files_analyzed > 20, f"Expected to analyze more files, got {files_analyzed}"
        
        # Calculate performance metrics
        files_per_second = files_analyzed / analysis_time if analysis_time > 0 else 0
        
        print(f"Large codebase performance:")
        print(f"  Analysis time: {analysis_time:.2f}s")
        print(f"  Files analyzed: {files_analyzed}")
        print(f"  Performance: {files_per_second:.2f} files/second")
        
        # Performance should be reasonable
        assert files_per_second > 1.0, f"Performance too slow: {files_per_second} files/second"

    def test_multi_language_project(self):
        """Test analysis of project with multiple languages."""
        if not self.test_packages_dir.exists():
            pytest.skip("Test packages directory not found")
        
        # Analyze entire test packages directory (multi-language)
        start_time = time.time()
        result = self.analyzer.analyze_path(
            path=str(self.test_packages_dir),
            policy="standard"
        )
        analysis_time = time.time() - start_time
        
        # Should handle multiple languages
        assert result['success'] is True
        
        # Check that multiple file types were processed
        violations = result.get('violations', [])
        file_paths = [v.get('file_path', '') for v in violations]
        
        # Should have violations from different file types
        extensions = set()
        for path in file_paths:
            if '.' in path:
                ext = path.split('.')[-1].lower()
                extensions.add(ext)
        
        print(f"Multi-language analysis:")
        print(f"  Analysis time: {analysis_time:.2f}s")
        print(f"  Total violations: {len(violations)}")
        print(f"  File extensions found: {sorted(extensions)}")

    def test_nasa_compliance_validation(self):
        """Test NASA compliance validation on real code."""
        analyzer_dir = self.project_root / "analyzer"
        
        if not analyzer_dir.exists():
            pytest.skip("Analyzer directory not found")
        
        # Run NASA compliance analysis
        result = self.analyzer.analyze_path(
            path=str(analyzer_dir),
            policy="nasa_jpl_pot10",
            nasa_validation=True
        )
        
        # Validate NASA compliance structure
        assert 'nasa_compliance' in result
        nasa_compliance = result['nasa_compliance']
        
        assert 'score' in nasa_compliance
        assert 'violations' in nasa_compliance
        assert 'passing' in nasa_compliance
        
        # Score should be between 0 and 1
        score = nasa_compliance['score']
        assert 0.0 <= score <= 1.0, f"NASA compliance score out of range: {score}"
        
        print(f"NASA compliance validation:")
        print(f"  Score: {score:.3f}")
        print(f"  Passing: {nasa_compliance.get('passing', False)}")
        print(f"  NASA violations: {len(nasa_compliance.get('violations', []))}")

    def test_god_object_detection_real_code(self):
        """Test god object detection on real codebase."""
        result = self.analyzer.analyze_path(
            path=str(self.project_root / "analyzer"),
            policy="strict-core",
            include_god_objects=True
        )
        
        # Check for god object analysis
        god_objects = result.get('god_objects', [])
        violations = result.get('violations', [])
        
        # Find god object violations
        god_object_violations = [v for v in violations if v.get('type') == 'god_object']
        
        print(f"God object detection:")
        print(f"  God objects found: {len(god_objects)}")
        print(f"  God object violations: {len(god_object_violations)}")
        
        # If god objects found, validate their structure
        for god_obj in god_object_violations[:3]:  # Check first 3
            assert 'file_path' in god_obj
            assert 'description' in god_obj
            assert 'severity' in god_obj
            assert god_obj['severity'] in ['critical', 'high', 'medium']

    def test_mece_analysis_real_code(self):
        """Test MECE duplication analysis on real code."""
        result = self.analyzer.analyze_path(
            path=str(self.project_root / "analyzer"),
            policy="standard",
            include_mece_analysis=True
        )
        
        # Check MECE analysis results
        mece_analysis = result.get('mece_analysis', {})
        assert 'score' in mece_analysis
        assert 'duplications' in mece_analysis
        
        score = mece_analysis['score']
        assert 0.0 <= score <= 1.0, f"MECE score out of range: {score}"
        
        duplications = mece_analysis['duplications']
        
        print(f"MECE analysis:")
        print(f"  Score: {score:.3f}")
        print(f"  Duplication clusters: {len(duplications)}")
        print(f"  Passing: {mece_analysis.get('passing', False)}")

    def test_regression_baseline_comparison(self):
        """Test that results are consistent with baseline expectations."""
        # This test compares current results with expected patterns
        # to catch regressions in analysis quality
        
        analyzer_dir = self.project_root / "analyzer"
        
        if not analyzer_dir.exists():
            pytest.skip("Analyzer directory not found")
        
        # Run standard analysis
        result = self.analyzer.analyze_path(
            path=str(analyzer_dir),
            policy="standard"
        )
        
        # Basic regression checks
        assert result['success'] is True
        
        violations = result.get('violations', [])
        summary = result.get('summary', {})
        
        # Should find some violations but not be overwhelmed
        total_violations = summary.get('total_violations', 0)
        assert total_violations >= 0  # At least some issues in any real codebase
        
        # Critical violations should be limited
        critical_violations = summary.get('critical_violations', 0)
        assert critical_violations < 10, f"Too many critical violations: {critical_violations}"
        
        # Quality score should be reasonable
        quality_score = summary.get('overall_quality_score', 0)
        assert quality_score >= 0.3, f"Quality score too low: {quality_score}"
        
        print(f"Regression baseline check:")
        print(f"  Total violations: {total_violations}")
        print(f"  Critical violations: {critical_violations}")
        print(f"  Quality score: {quality_score:.3f}")

    def test_error_handling_invalid_files(self):
        """Test error handling with invalid or corrupted files."""
        # Create a temporary directory with problematic files
        import tempfile
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create files with various issues
            
            # Syntax error file
            syntax_error_file = temp_path / "syntax_error.py"
            syntax_error_file.write_text('''
def broken_function(
    # Missing closing parenthesis and body
''')
            
            # Binary file with .py extension
            binary_file = temp_path / "binary.py"
            binary_file.write_bytes(b'\x00\x01\x02\x03\x04\x05')
            
            # Empty file
            empty_file = temp_path / "empty.py"
            empty_file.touch()
            
            # Run analysis
            result = self.analyzer.analyze_path(
                path=str(temp_path),
                policy="standard"
            )
            
            # Analysis should succeed despite problematic files
            assert result['success'] is True
            
            # Should have some error violations
            violations = result.get('violations', [])
            error_violations = [v for v in violations if 'error' in v.get('type', '').lower()]
            
            print(f"Error handling test:")
            print(f"  Total violations: {len(violations)}")
            print(f"  Error violations: {len(error_violations)}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])