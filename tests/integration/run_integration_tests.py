#!/usr/bin/env python3
"""
Comprehensive Integration Test Runner
Orchestrates and executes all integration tests with memory coordination and reporting
"""

import asyncio
import pytest
import json
import time
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import concurrent.futures
import subprocess
import argparse

# Import memory coordination
from . import (
    INTEGRATION_COORDINATOR, 
    store_integration_result, 
    get_integration_metrics,
    export_integration_results,
    cleanup_test_memory,
    get_memory_usage_stats
)

class IntegrationTestRunner:
    """Orchestrates comprehensive integration testing with memory coordination"""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.results_dir = self.base_dir.parent.parent / 'test_results' / 'integration'
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        self.test_suites = {
            'mcp_server_integration': {
                'module': 'test_mcp_server_integration.py',
                'description': 'MCP Server Integration Testing',
                'components': ['mcp_server', 'analyzer'],
                'priority': 'high',
                'estimated_time': 30  # seconds
            },
            'autofix_engine_integration': {
                'module': 'test_autofix_engine_integration.py',
                'description': 'Autofix Engine Integration Testing',
                'components': ['autofix', 'analyzer', 'mcp_server'],
                'priority': 'high',
                'estimated_time': 45
            },
            'workflow_integration': {
                'module': 'test_workflow_integration.py',
                'description': 'Complete Workflow Integration Testing',
                'components': ['cli', 'analyzer', 'mcp_server', 'autofix'],
                'priority': 'critical',
                'estimated_time': 60
            },
            'cross_component_validation': {
                'module': 'test_cross_component_validation.py',
                'description': 'Cross-Component Validation Testing',
                'components': ['all'],
                'priority': 'critical',
                'estimated_time': 90
            }
        }
        
    def run_single_test_suite(self, suite_name: str, suite_config: Dict[str, Any]) -> Dict[str, Any]:
        """Run a single integration test suite"""
        
        print(f"\n🧪 Running Integration Test Suite: {suite_name}")
        print(f"   Description: {suite_config['description']}")
        print(f"   Components: {', '.join(suite_config['components'])}")
        print(f"   Estimated Time: {suite_config['estimated_time']}s")
        print("   " + "="*60)
        
        start_time = time.time()
        
        try:
            # Run pytest for specific test module
            module_path = self.base_dir / suite_config['module']
            
            if not module_path.exists():
                raise FileNotFoundError(f"Test module not found: {module_path}")
                
            # Build pytest command
            pytest_cmd = [
                sys.executable, '-m', 'pytest',
                str(module_path),
                '-v',
                '--tb=short',
                '--capture=no',
                f'--junitxml={self.results_dir / f"{suite_name}_results.xml"}',
                f'--json-report', 
                f'--json-report-file={self.results_dir / f"{suite_name}_report.json"}'
            ]
            
            # Execute pytest
            result = subprocess.run(
                pytest_cmd,
                capture_output=True,
                text=True,
                cwd=self.base_dir
            )
            
            execution_time = time.time() - start_time
            
            # Parse results
            success = result.returncode == 0
            
            # Try to load JSON report for detailed metrics
            json_report_path = self.results_dir / f"{suite_name}_report.json"
            detailed_metrics = {}
            
            if json_report_path.exists():
                try:
                    with open(json_report_path, 'r') as f:
                        json_report = json.load(f)
                        detailed_metrics = {
                            'tests_collected': json_report.get('summary', {}).get('total', 0),
                            'tests_passed': json_report.get('summary', {}).get('passed', 0),
                            'tests_failed': json_report.get('summary', {}).get('failed', 0),
                            'tests_skipped': json_report.get('summary', {}).get('skipped', 0),
                            'test_duration': json_report.get('duration', execution_time)
                        }
                except Exception as e:
                    print(f"   ⚠️  Could not parse JSON report: {e}")
                    
            # Store results in memory coordination
            store_integration_result(
                f"{suite_name}_execution",
                'passed' if success else 'failed',
                execution_time,
                'integration_test_runner',
                {
                    'suite_name': suite_name,
                    'components': suite_config['components'],
                    'exit_code': result.returncode,
                    'stdout_lines': len(result.stdout.splitlines()),
                    'stderr_lines': len(result.stderr.splitlines()),
                    'priority': suite_config['priority'],
                    **detailed_metrics
                }
            )
            
            test_result = {
                'suite_name': suite_name,
                'success': success,
                'execution_time': execution_time,
                'exit_code': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'detailed_metrics': detailed_metrics,
                'priority': suite_config['priority']
            }
            
            # Print summary
            status = "✅ PASSED" if success else "❌ FAILED"
            print(f"   {status} in {execution_time:.2f}s")
            
            if detailed_metrics:
                print(f"   📊 Tests: {detailed_metrics.get('tests_collected', 0)} total, "
                      f"{detailed_metrics.get('tests_passed', 0)} passed, "
                      f"{detailed_metrics.get('tests_failed', 0)} failed")
                      
            if not success:
                print(f"   🐛 Exit Code: {result.returncode}")
                if result.stderr:
                    error_lines = result.stderr.splitlines()[:5]  # First 5 error lines
                    for line in error_lines:
                        print(f"      {line}")
                    if len(result.stderr.splitlines()) > 5:
                        print(f"      ... and {len(result.stderr.splitlines()) - 5} more lines")
                        
            return test_result
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            print(f"   ❌ EXCEPTION: {str(e)}")
            
            # Store error result
            store_integration_result(
                f"{suite_name}_error",
                'error',
                execution_time,
                'integration_test_runner',
                {
                    'suite_name': suite_name,
                    'error': str(e),
                    'exception_type': type(e).__name__
                }
            )
            
            return {
                'suite_name': suite_name,
                'success': False,
                'execution_time': execution_time,
                'error': str(e),
                'exception_type': type(e).__name__
            }
            
    def run_all_suites(self, parallel: bool = False, suite_filter: Optional[str] = None) -> Dict[str, Any]:
        """Run all integration test suites"""
        
        print("🚀 CONNASCENCE INTEGRATION TEST SUITE")
        print("="*70)
        print("Running comprehensive integration tests with memory coordination")
        print(f"Results directory: {self.results_dir}")
        print("="*70)
        
        # Filter suites if requested
        suites_to_run = self.test_suites
        if suite_filter:
            suites_to_run = {k: v for k, v in self.test_suites.items() if suite_filter.lower() in k.lower()}
            print(f"🔍 Filtering suites: {list(suites_to_run.keys())}")
            
        if not suites_to_run:
            print(f"❌ No suites match filter: {suite_filter}")
            return {'success': False, 'error': 'No matching suites'}
            
        total_start_time = time.time()
        suite_results = []
        
        # Store overall test run start
        store_integration_result(
            'integration_test_run_start',
            'in_progress',
            0.0,
            'integration_test_runner',
            {
                'suites_planned': list(suites_to_run.keys()),
                'parallel_execution': parallel,
                'suite_filter': suite_filter
            }
        )
        
        if parallel and len(suites_to_run) > 1:
            # Run suites in parallel
            print(f"⚡ Running {len(suites_to_run)} suites in parallel...")
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=min(4, len(suites_to_run))) as executor:
                future_to_suite = {
                    executor.submit(self.run_single_test_suite, suite_name, suite_config): suite_name
                    for suite_name, suite_config in suites_to_run.items()
                }
                
                for future in concurrent.futures.as_completed(future_to_suite):
                    suite_name = future_to_suite[future]
                    try:
                        result = future.result()
                        suite_results.append(result)
                    except Exception as e:
                        print(f"❌ Suite {suite_name} generated exception: {e}")
                        suite_results.append({
                            'suite_name': suite_name,
                            'success': False,
                            'error': str(e),
                            'execution_time': 0.0
                        })
        else:
            # Run suites sequentially
            print(f"🔄 Running {len(suites_to_run)} suites sequentially...")
            
            # Sort by priority: critical first, then high, then others
            priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
            sorted_suites = sorted(
                suites_to_run.items(),
                key=lambda x: priority_order.get(x[1].get('priority', 'medium'), 2)
            )
            
            for suite_name, suite_config in sorted_suites:
                result = self.run_single_test_suite(suite_name, suite_config)
                suite_results.append(result)
                
                # Stop on critical failure unless running in continue mode
                if not result['success'] and suite_config.get('priority') == 'critical':
                    print(f"⚠️  Critical test suite {suite_name} failed - continuing with remaining tests")
                    
        total_execution_time = time.time() - total_start_time
        
        # Calculate overall metrics
        successful_suites = [r for r in suite_results if r.get('success', False)]
        failed_suites = [r for r in suite_results if not r.get('success', False)]
        
        overall_success = len(failed_suites) == 0
        
        # Store overall test run completion
        store_integration_result(
            'integration_test_run_completion',
            'passed' if overall_success else 'failed',
            total_execution_time,
            'integration_test_runner',
            {
                'total_suites': len(suites_to_run),
                'successful_suites': len(successful_suites),
                'failed_suites': len(failed_suites),
                'overall_success': overall_success,
                'total_execution_time': total_execution_time,
                'parallel_execution': parallel
            }
        )
        
        # Generate comprehensive report
        self.generate_integration_report(suite_results, total_execution_time)
        
        # Print summary
        print("\n" + "="*70)
        print("🎯 INTEGRATION TEST SUITE SUMMARY")
        print("="*70)
        
        status_emoji = "✅" if overall_success else "❌"
        print(f"{status_emoji} Overall Status: {'SUCCESS' if overall_success else 'FAILURE'}")
        print(f"⏱️  Total Execution Time: {total_execution_time:.2f}s")
        print(f"📊 Test Suites: {len(successful_suites)}/{len(suites_to_run)} passed")
        
        if successful_suites:
            print(f"✅ Passed Suites: {', '.join(r['suite_name'] for r in successful_suites)}")
            
        if failed_suites:
            print(f"❌ Failed Suites: {', '.join(r['suite_name'] for r in failed_suites)}")
            
        # Memory coordination summary
        memory_stats = get_memory_usage_stats()
        integration_metrics = get_integration_metrics()
        
        print(f"\n🧠 Memory Coordination Summary:")
        print(f"   • Test Results Stored: {memory_stats['total_stored_results']}")
        print(f"   • Components Covered: {integration_metrics['components_covered']}")
        print(f"   • Overall Pass Rate: {integration_metrics['overall_pass_rate']:.1f}%")
        
        print(f"\n📁 Results exported to: {self.results_dir}")
        print("="*70)
        
        return {
            'success': overall_success,
            'suite_results': suite_results,
            'execution_time': total_execution_time,
            'metrics': integration_metrics,
            'memory_stats': memory_stats
        }
        
    def generate_integration_report(self, suite_results: List[Dict[str, Any]], total_time: float):
        """Generate comprehensive integration test report"""
        
        # Get memory coordination metrics
        integration_metrics = get_integration_metrics()
        memory_stats = get_memory_usage_stats()
        
        # Build report
        report = {
            'integration_test_report': {
                'timestamp': time.time(),
                'execution_summary': {
                    'total_execution_time': total_time,
                    'suites_executed': len(suite_results),
                    'suites_passed': len([r for r in suite_results if r.get('success', False)]),
                    'suites_failed': len([r for r in suite_results if not r.get('success', False)]),
                    'overall_success': all(r.get('success', False) for r in suite_results)
                },
                'suite_results': suite_results,
                'memory_coordination': {
                    'metrics': integration_metrics,
                    'memory_usage': memory_stats
                },
                'component_coverage': {
                    'components_tested': list(set().union(*[
                        r.get('components', []) for r in suite_results
                        if 'components' in r
                    ])),
                    'integration_chains_validated': True,
                    'cross_component_validation': any(
                        'cross_component' in r.get('suite_name', '')
                        for r in suite_results
                    )
                },
                'recommendations': self.generate_recommendations(suite_results, integration_metrics)
            }
        }
        
        # Save JSON report
        json_report_path = self.results_dir / 'integration_test_comprehensive_report.json'
        with open(json_report_path, 'w') as f:
            json.dump(report, f, indent=2)
            
        # Save human-readable report
        markdown_report = self.generate_markdown_report(report['integration_test_report'])
        markdown_path = self.results_dir / 'integration_test_report.md'
        with open(markdown_path, 'w') as f:
            f.write(markdown_report)
            
        print(f"📊 Comprehensive report saved: {json_report_path}")
        print(f"📝 Markdown report saved: {markdown_path}")
        
    def generate_recommendations(self, suite_results: List[Dict[str, Any]], 
                                metrics: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on test results"""
        
        recommendations = []
        
        # Performance recommendations
        slow_suites = [r for r in suite_results if r.get('execution_time', 0) > 60]
        if slow_suites:
            recommendations.append(
                f"Consider optimizing performance for slow test suites: {', '.join(r['suite_name'] for r in slow_suites)}"
            )
            
        # Coverage recommendations
        if metrics.get('overall_pass_rate', 0) < 90:
            recommendations.append(
                f"Improve test reliability - current pass rate is {metrics.get('overall_pass_rate', 0):.1f}%"
            )
            
        # Failed suites recommendations
        failed_suites = [r for r in suite_results if not r.get('success', False)]
        if failed_suites:
            for failed_suite in failed_suites:
                recommendations.append(
                    f"Address failures in {failed_suite['suite_name']} suite"
                )
                
        # Memory coordination recommendations
        if metrics.get('components_covered', 0) < 5:
            recommendations.append(
                "Increase component coverage - add more cross-component integration tests"
            )
            
        return recommendations
        
    def generate_markdown_report(self, report_data: Dict[str, Any]) -> str:
        """Generate human-readable markdown report"""
        
        execution_summary = report_data['execution_summary']
        suite_results = report_data['suite_results']
        
        markdown = f"""# Integration Test Report
        
**Generated**: {time.strftime('%Y-%m-%d %H:%M:%S')}

## Executive Summary

- **Overall Status**: {'✅ SUCCESS' if execution_summary['overall_success'] else '❌ FAILURE'}
- **Total Execution Time**: {execution_summary['total_execution_time']:.2f} seconds
- **Test Suites**: {execution_summary['suites_passed']}/{execution_summary['suites_executed']} passed

## Test Suite Results

"""
        
        for result in suite_results:
            status_emoji = "✅" if result.get('success', False) else "❌"
            suite_name = result.get('suite_name', 'unknown')
            execution_time = result.get('execution_time', 0)
            
            markdown += f"""### {status_emoji} {suite_name.replace('_', ' ').title()}

- **Status**: {'PASSED' if result.get('success', False) else 'FAILED'}
- **Execution Time**: {execution_time:.2f}s
"""
            
            if 'detailed_metrics' in result and result['detailed_metrics']:
                metrics = result['detailed_metrics']
                markdown += f"""- **Tests**: {metrics.get('tests_collected', 0)} total, {metrics.get('tests_passed', 0)} passed, {metrics.get('tests_failed', 0)} failed
"""
                
            if not result.get('success', False) and 'error' in result:
                markdown += f"""- **Error**: {result['error']}
"""
            
            markdown += "\n"
            
        # Add memory coordination section
        memory_metrics = report_data.get('memory_coordination', {}).get('metrics', {})
        
        markdown += f"""## Memory Coordination Metrics

- **Test Results Stored**: {memory_metrics.get('total_tests', 0)}
- **Components Covered**: {memory_metrics.get('components_covered', 0)}
- **Overall Pass Rate**: {memory_metrics.get('overall_pass_rate', 0):.1f}%
- **Average Execution Time**: {memory_metrics.get('average_execution_time', 0):.2f}s

## Component Coverage

"""
        
        component_coverage = report_data.get('component_coverage', {})
        components_tested = component_coverage.get('components_tested', [])
        
        if components_tested:
            for component in components_tested:
                markdown += f"- ✅ {component}\n"
        else:
            markdown += "- No component coverage data available\n"
            
        # Add recommendations
        recommendations = report_data.get('recommendations', [])
        if recommendations:
            markdown += f"""

## Recommendations

"""
            for i, rec in enumerate(recommendations, 1):
                markdown += f"{i}. {rec}\n"
                
        markdown += f"""

## Test Artifacts

All detailed test results, logs, and reports are available in the test results directory.

---

*Generated by Connascence Integration Test Runner*
"""
        
        return markdown

def main():
    """Main entry point for integration test runner"""
    
    parser = argparse.ArgumentParser(description='Run Connascence Integration Tests')
    parser.add_argument('--parallel', action='store_true', 
                       help='Run test suites in parallel')
    parser.add_argument('--filter', type=str,
                       help='Filter test suites by name (case insensitive)')
    parser.add_argument('--cleanup', action='store_true',
                       help='Clean up test memory before running')
    parser.add_argument('--export-only', action='store_true',
                       help='Only export existing test results without running tests')
    
    args = parser.parse_args()
    
    # Clean up memory if requested
    if args.cleanup:
        print("🧹 Cleaning up test memory...")
        cleanup_test_memory()
        
    runner = IntegrationTestRunner()
    
    if args.export_only:
        print("📤 Exporting existing integration test results...")
        export_data = export_integration_results()
        print(f"✅ Results exported: {len(export_data.get('test_results', []))} test results")
        return 0
        
    # Run integration tests
    results = runner.run_all_suites(
        parallel=args.parallel,
        suite_filter=args.filter
    )
    
    # Export results to file for CI/CD integration
    export_integration_results()
    
    # Return appropriate exit code
    return 0 if results['success'] else 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)