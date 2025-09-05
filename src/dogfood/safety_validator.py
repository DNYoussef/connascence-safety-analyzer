"""
Safety Validator - Test Execution & Regression Detection

Handles comprehensive test execution and functional regression detection
to ensure dogfood changes don't break existing functionality.
"""

import asyncio
import subprocess
import json
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime

@dataclass
class TestResult:
    """Result from running a single test suite"""
    name: str
    passed: bool
    test_count: int
    failures: List[str]
    execution_time: float
    coverage_percent: Optional[float] = None

@dataclass
class ComprehensiveTestResults:
    """Complete test execution results"""
    all_passed: bool
    total_tests: int
    total_failures: int
    test_suites: List[TestResult]
    functional_regressions: List[str]
    performance_regressions: List[Dict[str, Any]]
    execution_summary: Dict[str, Any]
    timestamp: datetime

class SafetyValidator:
    """Validates safety of dogfood changes through comprehensive testing"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        self.project_root = Path.cwd()
        
        # Test configuration
        self.test_timeout = self.config.get('test_timeout', 300)  # 5 minutes default
        self.parallel_execution = self.config.get('parallel_execution', True)
        self.performance_baseline = {}
        
    async def run_all_tests(self) -> ComprehensiveTestResults:
        """
        Run complete test suite and detect any regressions
        
        Returns:
            ComprehensiveTestResults with detailed results
        """
        self.logger.info("🧪 Starting comprehensive test execution...")
        execution_start = datetime.now()
        
        try:
            # Define test suites to run
            test_suites = [
                ("unit_tests", "tests/", "test_*.py"),
                ("integration_tests", "tests/integration/", "test_*.py"),
                ("mcp_server_tests", "tests/", "test_mcp_server.py"),
                ("analyzer_tests", "tests/", "test_ast_analyzer.py"),
                ("autofix_tests", "tests/", "test_autofix.py")
            ]
            
            # Run all test suites
            suite_results = []
            if self.parallel_execution:
                suite_results = await self._run_tests_parallel(test_suites)
            else:
                suite_results = await self._run_tests_sequential(test_suites)
            
            # Analyze results
            all_passed = all(result.passed for result in suite_results)
            total_tests = sum(result.test_count for result in suite_results)
            total_failures = sum(len(result.failures) for result in suite_results)
            
            # Detect functional regressions
            functional_regressions = self._detect_functional_regressions(suite_results)
            
            # Detect performance regressions  
            performance_regressions = self._detect_performance_regressions(suite_results)
            
            execution_time = (datetime.now() - execution_start).total_seconds()
            
            return ComprehensiveTestResults(
                all_passed=all_passed,
                total_tests=total_tests,
                total_failures=total_failures,
                test_suites=suite_results,
                functional_regressions=functional_regressions,
                performance_regressions=performance_regressions,
                execution_summary={
                    "execution_time": execution_time,
                    "suites_run": len(suite_results),
                    "parallel_execution": self.parallel_execution
                },
                timestamp=execution_start
            )
            
        except Exception as e:
            self.logger.error(f"💥 Test execution failed: {e}")
            # Return failed result
            return ComprehensiveTestResults(
                all_passed=False,
                total_tests=0,
                total_failures=1,
                test_suites=[],
                functional_regressions=[f"Test execution failed: {str(e)}"],
                performance_regressions=[],
                execution_summary={"error": str(e)},
                timestamp=execution_start
            )
    
    async def _run_tests_parallel(self, test_suites: List[tuple]) -> List[TestResult]:
        """Run test suites in parallel for faster execution"""
        self.logger.info("⚡ Running tests in parallel...")
        
        tasks = []
        for suite_name, path, pattern in test_suites:
            task = asyncio.create_task(
                self._run_single_test_suite(suite_name, path, pattern)
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and convert to TestResult objects
        valid_results = []
        for result in results:
            if isinstance(result, TestResult):
                valid_results.append(result)
            elif isinstance(result, Exception):
                self.logger.error(f"Test suite failed: {result}")
                # Add failed test result
                valid_results.append(TestResult(
                    name="failed_suite",
                    passed=False,
                    test_count=0,
                    failures=[str(result)],
                    execution_time=0.0
                ))
        
        return valid_results
    
    async def _run_tests_sequential(self, test_suites: List[tuple]) -> List[TestResult]:
        """Run test suites sequentially"""
        self.logger.info("🔄 Running tests sequentially...")
        
        results = []
        for suite_name, path, pattern in test_suites:
            result = await self._run_single_test_suite(suite_name, path, pattern)
            results.append(result)
        
        return results
    
    async def _run_single_test_suite(
        self, 
        suite_name: str, 
        path: str, 
        pattern: str
    ) -> TestResult:
        """Run a single test suite using pytest"""
        start_time = datetime.now()
        self.logger.info(f"🧪 Running {suite_name}...")
        
        try:
            # Build pytest command
            test_path = self.project_root / path
            cmd = [
                "python", "-m", "pytest",
                str(test_path),
                "-k", pattern.replace("*.py", "").replace("test_", ""),
                "--tb=short",
                "--json-report",
                "--json-report-file=/tmp/pytest_report.json",
                f"--timeout={self.test_timeout}"
            ]
            
            # Run tests
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.project_root
            )
            
            stdout, stderr = await process.communicate()
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Parse results
            if process.returncode == 0:
                # Tests passed
                return TestResult(
                    name=suite_name,
                    passed=True,
                    test_count=self._count_tests_from_output(stdout.decode()),
                    failures=[],
                    execution_time=execution_time
                )
            else:
                # Tests failed  
                failures = self._extract_failures_from_output(stderr.decode())
                return TestResult(
                    name=suite_name,
                    passed=False,
                    test_count=self._count_tests_from_output(stdout.decode()),
                    failures=failures,
                    execution_time=execution_time
                )
                
        except asyncio.TimeoutError:
            return TestResult(
                name=suite_name,
                passed=False,
                test_count=0,
                failures=[f"Test suite timed out after {self.test_timeout}s"],
                execution_time=self.test_timeout
            )
        except Exception as e:
            return TestResult(
                name=suite_name,
                passed=False,
                test_count=0,
                failures=[f"Test execution error: {str(e)}"],
                execution_time=(datetime.now() - start_time).total_seconds()
            )
    
    def _count_tests_from_output(self, output: str) -> int:
        """Extract test count from pytest output"""
        # Look for patterns like "3 passed", "5 failed", etc.
        import re
        patterns = [
            r'(\d+) passed',
            r'(\d+) failed', 
            r'(\d+) error',
            r'(\d+) skipped'
        ]
        
        total_count = 0
        for pattern in patterns:
            matches = re.findall(pattern, output)
            for match in matches:
                total_count += int(match)
        
        return total_count if total_count > 0 else 1  # Assume at least 1 if we can't parse
    
    def _extract_failures_from_output(self, output: str) -> List[str]:
        """Extract failure messages from pytest output"""
        # Simple extraction - look for FAILED lines
        import re
        failures = re.findall(r'FAILED (.+)', output)
        return failures[:10]  # Limit to first 10 failures
    
    def _detect_functional_regressions(self, suite_results: List[TestResult]) -> List[str]:
        """Detect functional regressions in test results"""
        regressions = []
        
        # Check for specific test failures that indicate functional issues
        critical_test_patterns = [
            "test_analyzer_core",
            "test_mcp_server_integration", 
            "test_violation_detection",
            "test_autofix_application"
        ]
        
        for suite in suite_results:
            if not suite.passed:
                for failure in suite.failures:
                    for pattern in critical_test_patterns:
                        if pattern in failure.lower():
                            regressions.append(f"Critical functionality regression: {failure}")
        
        return regressions
    
    def _detect_performance_regressions(self, suite_results: List[TestResult]) -> List[Dict[str, Any]]:
        """Detect performance regressions in test execution"""
        regressions = []
        
        for suite in suite_results:
            # Check if this suite took significantly longer than baseline
            baseline_time = self.performance_baseline.get(suite.name, suite.execution_time)
            
            if suite.execution_time > baseline_time * 1.5:  # 50% slower
                regressions.append({
                    "suite": suite.name,
                    "baseline_time": baseline_time,
                    "current_time": suite.execution_time,
                    "slowdown_factor": suite.execution_time / baseline_time,
                    "issue": "Test suite execution significantly slower"
                })
        
        return regressions
    
    def update_performance_baseline(self, suite_results: List[TestResult]):
        """Update performance baseline with current results"""
        for suite in suite_results:
            if suite.passed:  # Only update baseline with successful runs
                self.performance_baseline[suite.name] = suite.execution_time
    
    async def validate_core_functionality(self) -> Dict[str, Any]:
        """Run focused tests on core functionality only"""
        self.logger.info("🎯 Running focused core functionality tests...")
        
        # Test just the critical components
        core_tests = [
            ("analyzer_core", "tests/", "test_ast_analyzer.py"),
            ("mcp_server", "tests/", "test_mcp_server.py")
        ]
        
        results = await self._run_tests_sequential(core_tests)
        
        return {
            "core_functionality_intact": all(r.passed for r in results),
            "test_results": results,
            "critical_failures": [
                f for result in results 
                for f in result.failures
                if not result.passed
            ]
        }