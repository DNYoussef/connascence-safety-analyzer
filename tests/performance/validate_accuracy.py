#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""
Performance Optimization Accuracy Validator
============================================

Validates that performance optimizations maintain analysis accuracy
by comparing results between optimized and baseline implementations.
"""

import sys
import os
import time
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Tuple, Set
from dataclasses import dataclass
import difflib

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from analyzer.core import ConnascenceAnalyzer
from analyzer.performance.parallel_analyzer import ParallelConnascenceAnalyzer
from analyzer.caching.ast_cache import ast_cache, clear_cache
from analyzer.optimization.incremental_analyzer import get_incremental_analyzer
from analyzer.optimization.ast_optimizer import optimize_ast_analysis

logger = logging.getLogger(__name__)


@dataclass
class AccuracyValidationResult:
    """Result of accuracy validation test."""
    
    test_name: str
    baseline_violations: int
    optimized_violations: int
    matching_violations: int
    accuracy_percentage: float
    false_positives: int
    false_negatives: int
    performance_improvement: float
    validation_passed: bool
    issues_found: List[str]


class AccuracyValidator:
    """Validates that performance optimizations maintain accuracy."""
    
    def __init__(self, accuracy_threshold: float = 95.0):
        """Initialize accuracy validator."""
        
        self.accuracy_threshold = accuracy_threshold
        self.baseline_analyzer = ConnascenceAnalyzer()
        
        # Results storage
        self.validation_results = {}
        self.detailed_comparisons = {}
    
    def validate_all_optimizations(self, test_paths: List[str]) -> Dict[str, AccuracyValidationResult]:
        """Validate accuracy of all performance optimizations."""
        
        results = {}
        
        logger.info(f"Starting accuracy validation on {len(test_paths)} test paths")
        
        # Test each optimization
        optimizations_to_test = [
            ('caching', self._validate_caching_accuracy),
            ('parallel_processing', self._validate_parallel_accuracy),
            ('incremental_analysis', self._validate_incremental_accuracy),
            ('ast_optimization', self._validate_ast_optimization_accuracy)
        ]
        
        for test_path in test_paths:
            if not Path(test_path).exists():
                logger.warning(f"Test path does not exist: {test_path}")
                continue
            
            logger.info(f"Validating optimizations for: {test_path}")
            
            # Get baseline results
            baseline_result = self._get_baseline_results(test_path)
            
            # Test each optimization
            for optimization_name, validation_func in optimizations_to_test:
                try:
                    validation_result = validation_func(test_path, baseline_result)
                    results[f"{Path(test_path).name}_{optimization_name}"] = validation_result
                    
                    if validation_result.validation_passed:
                        logger.info(f"✅ {optimization_name} validation PASSED for {test_path}")
                    else:
                        logger.warning(f"❌ {optimization_name} validation FAILED for {test_path}")
                        for issue in validation_result.issues_found:
                            logger.warning(f"   Issue: {issue}")
                
                except Exception as e:
                    logger.error(f"Validation failed for {optimization_name} on {test_path}: {e}")
                    results[f"{Path(test_path).name}_{optimization_name}"] = AccuracyValidationResult(
                        test_name=f"{Path(test_path).name}_{optimization_name}",
                        baseline_violations=0,
                        optimized_violations=0,
                        matching_violations=0,
                        accuracy_percentage=0.0,
                        false_positives=0,
                        false_negatives=0,
                        performance_improvement=0.0,
                        validation_passed=False,
                        issues_found=[f"Validation error: {str(e)}"]
                    )
        
        # Generate summary report
        self._generate_validation_report(results)
        
        return results
    
    def _validate_caching_accuracy(self, test_path: str, baseline_result: Dict[str, Any]) -> AccuracyValidationResult:
        """Validate caching maintains accuracy."""
        
        logger.info(f"Validating caching accuracy for {test_path}")
        
        # Clear cache to ensure clean test
        clear_cache()
        
        # First run (cache cold)
        start_time = time.time()
        cold_result = self.baseline_analyzer.analyze_path(test_path)
        cold_time = time.time() - start_time
        
        # Second run (cache warm)
        start_time = time.time()
        warm_result = self.baseline_analyzer.analyze_path(test_path)
        warm_time = time.time() - start_time
        
        # Compare results
        comparison = self._compare_results(baseline_result, warm_result, "caching")
        
        # Performance improvement
        performance_improvement = ((cold_time - warm_time) / cold_time) * 100 if cold_time > 0 else 0
        
        return AccuracyValidationResult(
            test_name=f"{Path(test_path).name}_caching",
            baseline_violations=len(baseline_result.get('violations', [])),
            optimized_violations=len(warm_result.get('violations', [])),
            matching_violations=comparison['matching_violations'],
            accuracy_percentage=comparison['accuracy_percentage'],
            false_positives=comparison['false_positives'],
            false_negatives=comparison['false_negatives'],
            performance_improvement=performance_improvement,
            validation_passed=comparison['accuracy_percentage'] >= self.accuracy_threshold,
            issues_found=comparison['issues']
        )
    
    def _validate_parallel_accuracy(self, test_path: str, baseline_result: Dict[str, Any]) -> AccuracyValidationResult:
        """Validate parallel processing maintains accuracy."""
        
        logger.info(f"Validating parallel processing accuracy for {test_path}")
        
        # Skip if not enough files for parallel processing
        if Path(test_path).is_file():
            logger.info("Skipping parallel validation for single file")
            return AccuracyValidationResult(
                test_name=f"{Path(test_path).name}_parallel",
                baseline_violations=len(baseline_result.get('violations', [])),
                optimized_violations=len(baseline_result.get('violations', [])),
                matching_violations=len(baseline_result.get('violations', [])),
                accuracy_percentage=100.0,
                false_positives=0,
                false_negatives=0,
                performance_improvement=0.0,
                validation_passed=True,
                issues_found=[]
            )
        
        # Run parallel analysis
        parallel_analyzer = ParallelConnascenceAnalyzer()
        
        start_time = time.time()
        parallel_result = parallel_analyzer.analyze_project_parallel(test_path)
        parallel_time = time.time() - start_time
        
        # Convert parallel result to comparison format
        parallel_violations = {
            'violations': parallel_result.unified_result.connascence_violations,
            'summary': {
                'total_violations': parallel_result.unified_result.total_violations
            }
        }
        
        # Compare results
        comparison = self._compare_results(baseline_result, parallel_violations, "parallel")
        
        # Performance improvement from parallel result
        performance_improvement = ((parallel_result.sequential_equivalent_time - parallel_result.parallel_execution_time) / 
                                 parallel_result.sequential_equivalent_time) * 100 if parallel_result.sequential_equivalent_time > 0 else 0
        
        return AccuracyValidationResult(
            test_name=f"{Path(test_path).name}_parallel",
            baseline_violations=len(baseline_result.get('violations', [])),
            optimized_violations=len(parallel_violations.get('violations', [])),
            matching_violations=comparison['matching_violations'],
            accuracy_percentage=comparison['accuracy_percentage'],
            false_positives=comparison['false_positives'],
            false_negatives=comparison['false_negatives'],
            performance_improvement=performance_improvement,
            validation_passed=comparison['accuracy_percentage'] >= self.accuracy_threshold,
            issues_found=comparison['issues']
        )
    
    def _validate_incremental_accuracy(self, test_path: str, baseline_result: Dict[str, Any]) -> AccuracyValidationResult:
        """Validate incremental analysis maintains accuracy."""
        
        logger.info(f"Validating incremental analysis accuracy for {test_path}")
        
        # Skip if not a directory
        if not Path(test_path).is_dir():
            logger.info("Skipping incremental validation for non-directory")
            return AccuracyValidationResult(
                test_name=f"{Path(test_path).name}_incremental",
                baseline_violations=len(baseline_result.get('violations', [])),
                optimized_violations=len(baseline_result.get('violations', [])),
                matching_violations=len(baseline_result.get('violations', [])),
                accuracy_percentage=100.0,
                false_positives=0,
                false_negatives=0,
                performance_improvement=0.0,
                validation_passed=True,
                issues_found=[]
            )
        
        try:
            # Get incremental analyzer
            incremental_analyzer = get_incremental_analyzer(test_path)
            
            # Create baseline for incremental analyzer
            incremental_analyzer.create_baseline()
            
            # Simulate incremental analysis (analyze a subset of files)
            python_files = list(Path(test_path).glob('**/*.py'))[:5]  # First 5 files
            
            start_time = time.time()
            incremental_result = incremental_analyzer.analyze_changes(
                changed_files=[str(f) for f in python_files]
            )
            incremental_time = time.time() - start_time
            
            # Compare with subset of baseline (same files)
            subset_baseline = self._get_subset_baseline(baseline_result, [str(f) for f in python_files])
            
            incremental_violations = {
                'violations': incremental_result.violations,
                'summary': {
                    'total_violations': len(incremental_result.violations)
                }
            }
            
            comparison = self._compare_results(subset_baseline, incremental_violations, "incremental")
            
            # Performance improvement
            performance_improvement = incremental_result.time_saved_seconds / (incremental_result.analysis_time_seconds + incremental_result.time_saved_seconds) * 100
            
            return AccuracyValidationResult(
                test_name=f"{Path(test_path).name}_incremental",
                baseline_violations=len(subset_baseline.get('violations', [])),
                optimized_violations=len(incremental_violations.get('violations', [])),
                matching_violations=comparison['matching_violations'],
                accuracy_percentage=comparison['accuracy_percentage'],
                false_positives=comparison['false_positives'],
                false_negatives=comparison['false_negatives'],
                performance_improvement=performance_improvement,
                validation_passed=comparison['accuracy_percentage'] >= self.accuracy_threshold,
                issues_found=comparison['issues']
            )
            
        except Exception as e:
            logger.error(f"Incremental validation failed: {e}")
            return AccuracyValidationResult(
                test_name=f"{Path(test_path).name}_incremental",
                baseline_violations=0,
                optimized_violations=0,
                matching_violations=0,
                accuracy_percentage=0.0,
                false_positives=0,
                false_negatives=0,
                performance_improvement=0.0,
                validation_passed=False,
                issues_found=[f"Incremental analysis failed: {str(e)}"]
            )
    
    def _validate_ast_optimization_accuracy(self, test_path: str, baseline_result: Dict[str, Any]) -> AccuracyValidationResult:
        """Validate AST optimization maintains accuracy."""
        
        logger.info(f"Validating AST optimization accuracy for {test_path}")
        
        try:
            # Test on single file for AST optimization
            if Path(test_path).is_dir():
                # Find first Python file
                python_files = list(Path(test_path).glob('**/*.py'))
                if not python_files:
                    return AccuracyValidationResult(
                        test_name=f"{Path(test_path).name}_ast_optimization",
                        baseline_violations=0,
                        optimized_violations=0,
                        matching_violations=0,
                        accuracy_percentage=100.0,
                        false_positives=0,
                        false_negatives=0,
                        performance_improvement=0.0,
                        validation_passed=True,
                        issues_found=["No Python files found for AST optimization test"]
                    )
                test_file = python_files[0]
            else:
                test_file = Path(test_path)
            
            # Parse AST
            with open(test_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            import ast
            ast_tree = ast.parse(content, filename=str(test_file))
            
            # Run optimized AST analysis
            start_time = time.time()
            optimized_result = optimize_ast_analysis(ast_tree)
            optimization_time = time.time() - start_time
            
            # Run baseline analysis on same file
            start_time = time.time()
            file_baseline = self.baseline_analyzer.analyze_path(str(test_file))
            baseline_time = time.time() - start_time
            
            # Compare results
            comparison = self._compare_ast_results(file_baseline, optimized_result, "ast_optimization")
            
            # Performance improvement
            performance_improvement = ((baseline_time - optimization_time) / baseline_time) * 100 if baseline_time > 0 else 0
            
            return AccuracyValidationResult(
                test_name=f"{test_file.name}_ast_optimization",
                baseline_violations=len(file_baseline.get('violations', [])),
                optimized_violations=optimized_result.get('total_violations', 0),
                matching_violations=comparison['matching_violations'],
                accuracy_percentage=comparison['accuracy_percentage'],
                false_positives=comparison['false_positives'],
                false_negatives=comparison['false_negatives'],
                performance_improvement=performance_improvement,
                validation_passed=comparison['accuracy_percentage'] >= self.accuracy_threshold,
                issues_found=comparison['issues']
            )
            
        except Exception as e:
            logger.error(f"AST optimization validation failed: {e}")
            return AccuracyValidationResult(
                test_name=f"{Path(test_path).name}_ast_optimization",
                baseline_violations=0,
                optimized_violations=0,
                matching_violations=0,
                accuracy_percentage=0.0,
                false_positives=0,
                false_negatives=0,
                performance_improvement=0.0,
                validation_passed=False,
                issues_found=[f"AST optimization failed: {str(e)}"]
            )
    
    def _get_baseline_results(self, test_path: str) -> Dict[str, Any]:
        """Get baseline analysis results."""
        
        logger.debug(f"Getting baseline results for {test_path}")
        
        # Use the standard analyzer for baseline
        result = self.baseline_analyzer.analyze_path(test_path)
        
        # Ensure consistent format
        if 'violations' not in result:
            result['violations'] = []
        if 'summary' not in result:
            result['summary'] = {'total_violations': len(result['violations'])}
        
        return result
    
    def _compare_results(self, baseline: Dict[str, Any], optimized: Dict[str, Any], optimization_type: str) -> Dict[str, Any]:
        """Compare baseline and optimized results."""
        
        baseline_violations = baseline.get('violations', [])
        optimized_violations = optimized.get('violations', [])
        
        # Create signatures for violations (for matching)
        def violation_signature(v):
            return (
                v.get('file_path', ''),
                v.get('line_number', 0),
                v.get('rule_id', ''),
                v.get('type', ''),
                v.get('description', '')[:50]  # First 50 chars
            )
        
        baseline_sigs = {violation_signature(v): v for v in baseline_violations}
        optimized_sigs = {violation_signature(v): v for v in optimized_violations}
        
        # Find matches
        matching_sigs = set(baseline_sigs.keys()) & set(optimized_sigs.keys())
        matching_violations = len(matching_sigs)
        
        # Calculate false positives and negatives
        false_positives = len(optimized_sigs) - matching_violations  # In optimized but not baseline
        false_negatives = len(baseline_sigs) - matching_violations   # In baseline but not optimized
        
        # Calculate accuracy
        total_baseline = len(baseline_violations)
        if total_baseline == 0:
            accuracy_percentage = 100.0 if len(optimized_violations) == 0 else 0.0
        else:
            accuracy_percentage = (matching_violations / total_baseline) * 100
        
        # Identify specific issues
        issues = []
        
        if false_positives > 0:
            issues.append(f"{false_positives} false positive(s) in {optimization_type}")
        
        if false_negatives > 0:
            issues.append(f"{false_negatives} false negative(s) in {optimization_type}")
        
        # Check for significant differences in violation types
        baseline_types = set(v.get('type', 'unknown') for v in baseline_violations)
        optimized_types = set(v.get('type', 'unknown') for v in optimized_violations)
        
        missing_types = baseline_types - optimized_types
        extra_types = optimized_types - baseline_types
        
        if missing_types:
            issues.append(f"Missing violation types in {optimization_type}: {', '.join(missing_types)}")
        
        if extra_types:
            issues.append(f"Extra violation types in {optimization_type}: {', '.join(extra_types)}")
        
        return {
            'matching_violations': matching_violations,
            'accuracy_percentage': accuracy_percentage,
            'false_positives': false_positives,
            'false_negatives': false_negatives,
            'issues': issues,
            'baseline_total': len(baseline_violations),
            'optimized_total': len(optimized_violations)
        }
    
    def _compare_ast_results(self, baseline: Dict[str, Any], optimized: Dict[str, Any], optimization_type: str) -> Dict[str, Any]:
        """Compare baseline and AST-optimized results."""
        
        # AST optimization returns a different format
        baseline_violations = baseline.get('violations', [])
        
        # Extract violations from optimized result
        optimized_violations = []
        violations_by_type = optimized.get('violations', {})
        
        for violation_type, violations in violations_by_type.items():
            for violation in violations:
                # Convert to baseline format
                optimized_violations.append({
                    'type': violation.get('type', violation_type),
                    'line_number': violation.get('line_number', 0),
                    'description': violation.get('description', ''),
                    'severity': violation.get('severity', 'medium')
                })
        
        # Use standard comparison logic
        optimized_result_format = {
            'violations': optimized_violations,
            'summary': {'total_violations': len(optimized_violations)}
        }
        
        return self._compare_results(baseline, optimized_result_format, optimization_type)
    
    def _get_subset_baseline(self, baseline: Dict[str, Any], file_subset: List[str]) -> Dict[str, Any]:
        """Get baseline results for a subset of files."""
        
        # Filter baseline violations to only include those from the file subset
        all_violations = baseline.get('violations', [])
        
        subset_violations = []
        for violation in all_violations:
            violation_file = violation.get('file_path', '')
            
            # Check if violation is from one of the subset files
            for file_path in file_subset:
                if file_path in violation_file or violation_file in file_path:
                    subset_violations.append(violation)
                    break
        
        return {
            'violations': subset_violations,
            'summary': {'total_violations': len(subset_violations)}
        }
    
    def _generate_validation_report(self, results: Dict[str, AccuracyValidationResult]):
        """Generate detailed validation report."""
        
        report_file = Path("tests/performance/results/accuracy_validation_report.md")
        report_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_file, 'w') as f:
            f.write("# Performance Optimization Accuracy Validation Report\n\n")
            f.write(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Summary statistics
            total_tests = len(results)
            passed_tests = sum(1 for r in results.values() if r.validation_passed)
            failed_tests = total_tests - passed_tests
            
            f.write("## Summary\n\n")
            f.write(f"- **Total Tests**: {total_tests}\n")
            f.write(f"- **Passed**: {passed_tests} ({(passed_tests/total_tests)*100:.1f}%)\n")
            f.write(f"- **Failed**: {failed_tests} ({(failed_tests/total_tests)*100:.1f}%)\n")
            f.write(f"- **Accuracy Threshold**: {self.accuracy_threshold}%\n\n")
            
            # Detailed results
            f.write("## Detailed Results\n\n")
            f.write("| Test | Baseline | Optimized | Accuracy | Performance | Status |\n")
            f.write("|------|----------|-----------|----------|-------------|--------|\n")
            
            for test_name, result in sorted(results.items()):
                status = "✅ PASS" if result.validation_passed else "❌ FAIL"
                f.write(f"| {result.test_name} | {result.baseline_violations} | "
                       f"{result.optimized_violations} | {result.accuracy_percentage:.1f}% | "
                       f"+{result.performance_improvement:.1f}% | {status} |\n")
            
            f.write("\n")
            
            # Issues found
            f.write("## Issues Found\n\n")
            
            for test_name, result in results.items():
                if result.issues_found:
                    f.write(f"### {result.test_name}\n\n")
                    for issue in result.issues_found:
                        f.write(f"- {issue}\n")
                    f.write("\n")
            
            # Performance improvements
            f.write("## Performance Improvements\n\n")
            
            performance_data = [(r.test_name, r.performance_improvement) for r in results.values() if r.performance_improvement > 0]
            performance_data.sort(key=lambda x: x[1], reverse=True)
            
            f.write("| Optimization | Performance Gain |\n")
            f.write("|--------------|-------------------|\n")
            
            for test_name, improvement in performance_data:
                f.write(f"| {test_name} | +{improvement:.1f}% |\n")
            
            f.write("\n")
            
            # Recommendations
            f.write("## Recommendations\n\n")
            
            recommendations = []
            
            # Analyze results for recommendations
            failed_optimizations = [r for r in results.values() if not r.validation_passed]
            
            if failed_optimizations:
                recommendations.append(f"Investigate {len(failed_optimizations)} failed optimization(s)")
            
            high_performance = [r for r in results.values() if r.performance_improvement > 50]
            if high_performance:
                recommendations.append(f"Prioritize {len(high_performance)} high-performance optimization(s)")
            
            accuracy_issues = [r for r in results.values() if r.accuracy_percentage < self.accuracy_threshold]
            if accuracy_issues:
                recommendations.append(f"Fix accuracy issues in {len(accuracy_issues)} optimization(s)")
            
            if not recommendations:
                recommendations = ["All optimizations validated successfully", "Monitor performance in production"]
            
            for i, rec in enumerate(recommendations, 1):
                f.write(f"{i}. {rec}\n")
            
            f.write(f"\n---\n\n*Report generated by accuracy validator*\n")
        
        logger.info(f"Validation report saved to: {report_file}")


def main():
    """Main entry point for accuracy validation."""
    
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate optimization accuracy")
    parser.add_argument('--test-paths', nargs='+', 
                       default=['analyzer', 'test_packages/express'], 
                       help='Paths to test for accuracy')
    parser.add_argument('--threshold', type=float, default=95.0,
                       help='Accuracy threshold percentage')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Setup logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Run validation
    validator = AccuracyValidator(accuracy_threshold=args.threshold)
    results = validator.validate_all_optimizations(args.test_paths)
    
    # Print summary
    total_tests = len(results)
    passed_tests = sum(1 for r in results.values() if r.validation_passed)
    
    print(f"\nAccuracy Validation Summary:")
    print(f"  Tests run: {total_tests}")
    print(f"  Passed: {passed_tests}")
    print(f"  Failed: {total_tests - passed_tests}")
    print(f"  Success rate: {(passed_tests/total_tests)*100:.1f}%")
    
    # Exit with appropriate code
    if passed_tests == total_tests:
        print("✅ All accuracy validations PASSED")
        sys.exit(0)
    else:
        print("❌ Some accuracy validations FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()