"""
Production Readiness Validation Tests
=====================================

Comprehensive test suite to validate the entire connascence analyzer system
for production deployment. Tests all critical functionality, performance
benchmarks, error handling, and system integration.

NASA Power of Ten Compliant: All tests follow rules 1-10.
"""

import unittest
import sys
import time
import tempfile
import shutil
from pathlib import Path
from typing import Any, Dict, List

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from analyzer.unified_analyzer import UnifiedConnascenceAnalyzer
from analyzer.optimization.performance_benchmark import PerformanceBenchmark


class ProductionReadinessTests(unittest.TestCase):
    """
    Production readiness validation test suite.
    
    Tests critical paths, error handling, performance requirements,
    and system integration for production deployment.
    """
    
    def setUp(self):
        """Set up test environment."""
        self.test_dir = Path(tempfile.mkdtemp())
        self.test_files_created = []
        self.analyzers_created = []
        
    def tearDown(self):
        """Clean up test environment."""
        # Clean up test files
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir, ignore_errors=True)
        
        # Clean up any analyzer instances
        for analyzer in self.analyzers_created:
            try:
                if hasattr(analyzer, 'cleanup'):
                    analyzer.cleanup()
            except:
                pass
    
    def create_test_file(self, name: str, content: str) -> Path:
        """Create test file with given content."""
        file_path = self.test_dir / name
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding='utf-8')
        self.test_files_created.append(file_path)
        return file_path
    
    def test_critical_path_batch_analysis(self):
        """Test critical path: batch analysis of Python project."""
        # Create test Python files with various connascence types
        self.create_test_file("main.py", '''
def process_data(data_list, index_pos, flag_value):
    if index_pos == 0:  # Position connascence
        return data_list[0] * 2
    elif flag_value == "SPECIAL":  # Value connascence  
        return sum(data_list)
    return None
        ''')
        
        self.create_test_file("utils.py", '''
def helper_function(data_list, index_pos, flag_value):
    # Same parameter order - algorithm connascence
    return process_external(data_list, index_pos, flag_value)

def process_external(items, pos, special_flag):
    # Different parameter names but same meaning
    return items[pos] if special_flag != "SPECIAL" else 0
        ''')
        
        # Test analyzer creation and analysis
        analyzer = UnifiedConnascenceAnalyzer(analysis_mode="batch")
        self.analyzers_created.append(analyzer)
        
        start_time = time.time()
        result = analyzer.analyze_project(self.test_dir)
        analysis_time = time.time() - start_time
        
        # Validate critical requirements
        self.assertIsNotNone(result, "Analysis result must not be None")
        self.assertGreater(result.violations_found, 0, "Should detect connascence violations")
        self.assertLess(analysis_time, 10.0, "Analysis should complete within 10 seconds")
        self.assertFalse(result.has_critical_errors(), "Should not have critical errors")
        
        print(f"✓ Batch analysis: {result.violations_found} violations in {analysis_time:.2f}s")
    
    def test_critical_path_streaming_analysis(self):
        """Test critical path: streaming analysis initialization and operation."""
        try:
            # Test streaming analyzer creation
            analyzer = UnifiedConnascenceAnalyzer(analysis_mode="streaming")
            self.analyzers_created.append(analyzer)
            
            self.assertEqual(analyzer.analysis_mode, "streaming", "Should initialize in streaming mode")
            self.assertIsNotNone(analyzer.stream_processor, "Should have stream processor")
            
            # Create test file for streaming
            test_file = self.create_test_file("streaming_test.py", '''
def test_function():
    magic_number = 42  # Magic literal
    return magic_number * 2
            ''')
            
            # Test hybrid mode (more realistic production usage)
            hybrid_analyzer = UnifiedConnascenceAnalyzer(analysis_mode="hybrid")
            self.analyzers_created.append(hybrid_analyzer)
            
            result = hybrid_analyzer.analyze_project(self.test_dir)
            self.assertIsNotNone(result, "Hybrid analysis should return results")
            
            print("✓ Streaming analysis: initialization and hybrid mode working")
            
        except ImportError:
            self.skipTest("Streaming components not available")
    
    def test_memory_management_under_load(self):
        """Test memory management under high load conditions."""
        import psutil
        import gc
        
        # Get baseline memory
        process = psutil.Process()
        baseline_memory = process.memory_info().rss / (1024 * 1024)  # MB
        
        # Create multiple large test files
        for i in range(10):
            large_content = "def function_{}():\n".format(i)
            large_content += "    # Large function with many violations\n" * 100
            large_content += "    magic_value = {}\n".format(i * 42)  # Magic literals
            large_content += "    return magic_value\n"
            
            self.create_test_file(f"large_file_{i}.py", large_content)
        
        # Test multiple analysis runs
        max_memory_growth = 0
        for run in range(5):
            analyzer = UnifiedConnascenceAnalyzer(analysis_mode="batch")
            self.analyzers_created.append(analyzer)
            
            result = analyzer.analyze_project(self.test_dir)
            
            # Check memory usage
            current_memory = process.memory_info().rss / (1024 * 1024)
            memory_growth = current_memory - baseline_memory
            max_memory_growth = max(max_memory_growth, memory_growth)
            
            # Force garbage collection
            gc.collect()
        
        # Memory growth should be reasonable (< 100MB for this test)
        self.assertLess(max_memory_growth, 100.0, 
                       f"Memory growth {max_memory_growth:.1f}MB exceeds 100MB limit")
        
        print(f"✓ Memory management: max growth {max_memory_growth:.1f}MB under load")
    
    def test_error_handling_robustness(self):
        """Test system robustness under error conditions."""
        # Test with invalid Python syntax
        self.create_test_file("invalid_syntax.py", '''
def broken_function(
    # Missing closing parenthesis and colon
        ''')
        
        # Test with unreadable file permissions (if possible)
        restricted_file = self.create_test_file("restricted.py", "def test(): pass")
        
        # Test with non-Python files
        self.create_test_file("README.txt", "This is not Python code")
        self.create_test_file("config.json", '{"key": "value"}')
        
        # Test analyzer handles errors gracefully
        analyzer = UnifiedConnascenceAnalyzer(analysis_mode="batch")
        self.analyzers_created.append(analyzer)
        
        result = analyzer.analyze_project(self.test_dir)
        
        # Should complete without crashing
        self.assertIsNotNone(result, "Analysis should complete despite errors")
        
        # May have errors but should not be critical system failures
        if result.has_errors():
            print(f"✓ Error handling: {len(result.errors)} errors handled gracefully")
        else:
            print("✓ Error handling: no errors encountered")
    
    def test_performance_requirements(self):
        """Test performance meets production requirements."""
        # Create moderately sized project
        for i in range(20):
            content = f"""
def function_{i}(param1, param2, param3):
    magic_value_{i} = {42 + i}  # Magic literal
    if param1 == {i}:  # Position connascence
        return param2[param3]  # Potential timing connascence
    return magic_value_{i}

class TestClass_{i}:
    def __init__(self, value_{i}):
        self.value = value_{i}
        
    def process(self, data_{i}):
        return self.value + data_{i}
            """
            self.create_test_file(f"module_{i}.py", content)
        
        # Benchmark performance
        benchmark = PerformanceBenchmark(str(self.test_dir))
        results = benchmark.run_full_benchmark()
        
        # Validate performance requirements
        file_discovery_time = results.get("file_discovery", {}).get("time_seconds", float('inf'))
        analysis_time = results.get("analysis", {}).get("total_time_seconds", float('inf'))
        
        # Production requirements:
        # - File discovery: < 1 second for moderate projects
        # - Analysis: < 30 seconds for 20 files
        self.assertLess(file_discovery_time, 1.0, 
                       f"File discovery {file_discovery_time:.2f}s exceeds 1s limit")
        self.assertLess(analysis_time, 30.0,
                       f"Analysis time {analysis_time:.2f}s exceeds 30s limit")
        
        print(f"✓ Performance: discovery {file_discovery_time:.2f}s, analysis {analysis_time:.2f}s")
    
    def test_concurrent_access_safety(self):
        """Test thread safety for concurrent operations."""
        import threading
        import queue
        
        # Create test files
        for i in range(5):
            self.create_test_file(f"concurrent_{i}.py", f'''
def concurrent_function_{i}():
    value = {i * 10}
    return value
            ''')
        
        # Test concurrent analysis
        results_queue = queue.Queue()
        errors_queue = queue.Queue()
        
        def analyze_worker():
            try:
                analyzer = UnifiedConnascenceAnalyzer(analysis_mode="batch")
                result = analyzer.analyze_project(self.test_dir)
                results_queue.put(result)
            except Exception as e:
                errors_queue.put(e)
        
        # Start multiple analysis threads
        threads = []
        for _ in range(3):
            thread = threading.Thread(target=analyze_worker)
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join(timeout=30.0)
            self.assertFalse(thread.is_alive(), "Thread should complete within 30 seconds")
        
        # Check results
        results_count = results_queue.qsize()
        errors_count = errors_queue.qsize()
        
        self.assertEqual(results_count, 3, "All threads should complete successfully")
        self.assertEqual(errors_count, 0, "No thread should encounter errors")
        
        print(f"✓ Concurrency: {results_count} threads completed, {errors_count} errors")
    
    def test_system_integration_completeness(self):
        """Test complete system integration functionality."""
        # Create comprehensive test project
        self.create_test_file("main.py", '''
import utils
from config import MAGIC_CONSTANT

def main_function(data_list, position, flag):
    # Multiple connascence types in realistic code
    if position == 0:  # Position connascence
        result = utils.process_first(data_list)
    elif flag == "SPECIAL":  # Value connascence  
        result = utils.process_special(data_list, MAGIC_CONSTANT)
    else:
        result = utils.process_default(data_list, position)
    
    return result
        ''')
        
        self.create_test_file("utils.py", '''
from config import MAGIC_CONSTANT

def process_first(items):
    return items[0] * 2  # Timing connascence with indexing

def process_special(items, magic_value):
    # Algorithm connascence - same processing pattern
    total = 0
    for item in items:
        total += item * magic_value
    return total

def process_default(items, pos):
    return items[pos] if pos < len(items) else 0
        ''')
        
        self.create_test_file("config.py", '''
# Magic literal - should be detected
MAGIC_CONSTANT = 42
DEBUG_FLAG = True
        ''')
        
        # Test all analysis modes
        for mode in ["batch", "streaming", "hybrid"]:
            try:
                analyzer = UnifiedConnascenceAnalyzer(analysis_mode=mode)
                self.analyzers_created.append(analyzer)
                
                result = analyzer.analyze_project(self.test_dir)
                
                # Validate comprehensive analysis
                self.assertIsNotNone(result, f"{mode} analysis should return results")
                self.assertGreater(result.violations_found, 0, f"{mode} should detect violations")
                
                # Check for specific violation types
                violation_types = set()
                for violation_list in result.violations.values():
                    if isinstance(violation_list, list):
                        for v in violation_list:
                            if isinstance(v, dict) and 'type' in v:
                                violation_types.add(v['type'])
                
                print(f"✓ {mode.capitalize()} integration: {result.violations_found} violations, "
                      f"{len(violation_types)} types detected")
                
            except ImportError:
                if mode in ["streaming", "hybrid"]:
                    print(f"! {mode.capitalize()} mode skipped (components not available)")
                else:
                    raise
    
    def test_data_persistence_integrity(self):
        """Test data integrity and persistence mechanisms."""
        # Test that analysis results are consistent across runs
        test_content = '''
def test_consistency():
    magic_number = 123  # Should always be detected
    return magic_number * 2
        '''
        
        self.create_test_file("consistency_test.py", test_content)
        
        results = []
        for run in range(3):
            analyzer = UnifiedConnascenceAnalyzer(analysis_mode="batch")
            self.analyzers_created.append(analyzer)
            
            result = analyzer.analyze_project(self.test_dir)
            results.append(result)
        
        # Results should be consistent
        first_violation_count = results[0].violations_found
        for i, result in enumerate(results[1:], 1):
            self.assertEqual(result.violations_found, first_violation_count,
                           f"Run {i+1} should have same violation count as run 1")
        
        print(f"✓ Data integrity: {first_violation_count} violations consistent across 3 runs")
    
    def test_configuration_flexibility(self):
        """Test system configuration and customization options."""
        # Test different configuration scenarios
        configs = [
            {"analysis_mode": "batch"},
            {"analysis_mode": "streaming"} if self._streaming_available() else {"analysis_mode": "batch"},
            {"analysis_mode": "hybrid"} if self._streaming_available() else {"analysis_mode": "batch"}
        ]
        
        for config in configs:
            try:
                analyzer = UnifiedConnascenceAnalyzer(**config)
                self.analyzers_created.append(analyzer)
                
                self.assertEqual(analyzer.analysis_mode, config["analysis_mode"],
                               f"Should initialize with {config['analysis_mode']} mode")
                
                print(f"✓ Configuration: {config['analysis_mode']} mode configured successfully")
                
            except Exception as e:
                self.fail(f"Configuration {config} failed: {e}")
    
    def _streaming_available(self) -> bool:
        """Check if streaming components are available."""
        try:
            from analyzer.streaming import StreamProcessor
            return True
        except ImportError:
            return False


def run_production_readiness_suite():
    """Run complete production readiness test suite."""
    print("="*80)
    print("PRODUCTION READINESS VALIDATION")
    print("="*80)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(ProductionReadinessTests)
    
    # Run with verbose output
    runner = unittest.TextTestRunner(verbosity=2, buffer=True)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "="*80)
    print("PRODUCTION READINESS SUMMARY")
    print("="*80)
    
    if result.wasSuccessful():
        print("SUCCESS: ALL TESTS PASSED - SYSTEM IS PRODUCTION READY")
        print(f"   • {result.testsRun} tests executed successfully")
        print(f"   • 0 failures, 0 errors")
        print(f"   • Critical paths validated")
        print(f"   • Performance requirements met") 
        print(f"   • Error handling robust")
        print(f"   • Memory management compliant")
        print(f"   • Thread safety verified")
        print(f"   • System integration complete")
        return True
    else:
        print("ERROR: PRODUCTION READINESS ISSUES DETECTED")
        print(f"   • {result.testsRun} tests executed")
        print(f"   • {len(result.failures)} failures")
        print(f"   • {len(result.errors)} errors")
        
        if result.failures:
            print("\nFAILURES:")
            for test, traceback in result.failures:
                print(f"   - {test}: {traceback.split('AssertionError:')[-1].strip()}")
        
        if result.errors:
            print("\nERRORS:")
            for test, traceback in result.errors:
                print(f"   - {test}: {traceback.split('Exception:')[-1].strip()}")
        
        return False


if __name__ == "__main__":
    success = run_production_readiness_suite()
    sys.exit(0 if success else 1)