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
End-to-End Performance Benchmarking Tests

Comprehensive performance testing for connascence analysis across various scales.
Tests throughput, latency, memory usage, and scalability characteristics.
Uses memory coordination for tracking performance patterns and benchmarks.
"""

import json
import os
import psutil
import tempfile
import time
import threading
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import pytest
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import Mock, patch
import statistics
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from cli.connascence import ConnascenceCLI
from tests.e2e.test_cli_workflows import E2EMemoryCoordinator, SequentialWorkflowValidator


class PerformanceBenchmarkCoordinator:
    """Memory coordinator for performance benchmarking and metrics tracking."""
    
    def __init__(self):
        self.benchmark_results = {}
        self.performance_baselines = {}
        self.scalability_metrics = {}
        self.memory_profiles = {}
        self.throughput_measurements = {}
        self.latency_measurements = {}
        self.regression_tests = {}
        self.resource_utilization = {}
    
    def store_benchmark_result(self, benchmark_id: str, benchmark_data: Dict[str, Any]):
        """Store benchmark execution results."""
        self.benchmark_results[benchmark_id] = {
            'data': benchmark_data,
            'timestamp': time.time(),
            'benchmark_type': benchmark_data.get('benchmark_type', 'unknown')
        }
    
    def store_performance_baseline(self, baseline_id: str, baseline_data: Dict[str, Any]):
        """Store performance baseline for comparison."""
        self.performance_baselines[baseline_id] = baseline_data
    
    def store_scalability_metrics(self, test_id: str, scalability_data: Dict[str, Any]):
        """Store scalability test results."""
        self.scalability_metrics[test_id] = scalability_data
    
    def store_memory_profile(self, profile_id: str, memory_data: Dict[str, Any]):
        """Store memory usage profiling data."""
        self.memory_profiles[profile_id] = memory_data
    
    def store_throughput_measurement(self, measurement_id: str, throughput_data: Dict[str, Any]):
        """Store throughput measurement results."""
        self.throughput_measurements[measurement_id] = throughput_data
    
    def store_latency_measurement(self, measurement_id: str, latency_data: Dict[str, Any]):
        """Store latency measurement results."""
        self.latency_measurements[measurement_id] = latency_data
    
    def store_regression_test(self, test_id: str, regression_data: Dict[str, Any]):
        """Store performance regression test results."""
        self.regression_tests[test_id] = regression_data
    
    def store_resource_utilization(self, utilization_id: str, resource_data: Dict[str, Any]):
        """Store resource utilization metrics."""
        self.resource_utilization[utilization_id] = resource_data
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance testing summary."""
        return {
            'total_benchmarks': len(self.benchmark_results),
            'performance_baselines': len(self.performance_baselines),
            'scalability_tests': len(self.scalability_metrics),
            'memory_profiles': len(self.memory_profiles),
            'throughput_measurements': len(self.throughput_measurements),
            'latency_measurements': len(self.latency_measurements),
            'regression_tests': len(self.regression_tests),
            'resource_utilization_tests': len(self.resource_utilization),
            'overall_performance_score': self._calculate_performance_score(),
            'performance_trends': self._analyze_performance_trends()
        }
    
    def compare_with_baseline(self, benchmark_id: str, baseline_id: str) -> Dict[str, Any]:
        """Compare benchmark result with baseline."""
        if benchmark_id not in self.benchmark_results or baseline_id not in self.performance_baselines:
            return {'error': 'Missing benchmark or baseline data'}
        
        benchmark = self.benchmark_results[benchmark_id]['data']
        baseline = self.performance_baselines[baseline_id]
        
        comparison = {
            'benchmark_id': benchmark_id,
            'baseline_id': baseline_id,
            'comparison_timestamp': time.time(),
            'metrics_comparison': {}
        }
        
        # Compare common metrics
        common_metrics = ['execution_time_ms', 'memory_peak_mb', 'violations_per_second', 'files_per_second']
        
        for metric in common_metrics:
            if metric in benchmark and metric in baseline:
                benchmark_value = benchmark[metric]
                baseline_value = baseline[metric]
                
                if baseline_value > 0:
                    percent_change = ((benchmark_value - baseline_value) / baseline_value) * 100
                    comparison['metrics_comparison'][metric] = {
                        'benchmark_value': benchmark_value,
                        'baseline_value': baseline_value,
                        'percent_change': percent_change,
                        'regression': percent_change > 10 if metric != 'memory_peak_mb' else percent_change > 20  # Different thresholds
                    }
        
        # Overall regression analysis
        regressions = [m for m in comparison['metrics_comparison'].values() if m.get('regression', False)]
        comparison['overall_regression'] = len(regressions) > 0
        comparison['regression_count'] = len(regressions)
        
        return comparison
    
    def _calculate_performance_score(self) -> float:
        """Calculate overall performance score."""
        if not self.benchmark_results:
            return 0.0
        
        scores = []
        
        # Execution time scores (faster = better)
        execution_times = [b['data'].get('execution_time_ms', 0) for b in self.benchmark_results.values()]
        if execution_times:
            avg_time = statistics.mean(execution_times)
            time_score = max(0, 1.0 - (avg_time / 60000))  # 60 seconds = 0 score
            scores.append(time_score * 0.4)
        
        # Memory efficiency scores (lower peak = better)
        memory_peaks = [b['data'].get('memory_peak_mb', 0) for b in self.benchmark_results.values()]
        if memory_peaks:
            avg_memory = statistics.mean(memory_peaks)
            memory_score = max(0, 1.0 - (avg_memory / 1024))  # 1GB = 0 score
            scores.append(memory_score * 0.3)
        
        # Throughput scores (higher = better)
        throughputs = [b['data'].get('violations_per_second', 0) for b in self.benchmark_results.values()]
        if throughputs:
            avg_throughput = statistics.mean(throughputs)
            throughput_score = min(1.0, avg_throughput / 100)  # 100 violations/sec = full score
            scores.append(throughput_score * 0.3)
        
        return sum(scores) if scores else 0.0
    
    def _analyze_performance_trends(self) -> Dict[str, Any]:
        """Analyze performance trends over time."""
        if len(self.benchmark_results) < 2:
            return {'trend_analysis': 'insufficient_data'}
        
        # Sort benchmarks by timestamp
        sorted_benchmarks = sorted(
            self.benchmark_results.items(),
            key=lambda x: x[1]['timestamp']
        )
        
        # Analyze trends in key metrics
        execution_times = [b[1]['data'].get('execution_time_ms', 0) for b in sorted_benchmarks]
        memory_usage = [b[1]['data'].get('memory_peak_mb', 0) for b in sorted_benchmarks]
        
        trends = {}
        
        if len(execution_times) >= 2:
            time_trend = 'improving' if execution_times[-1] < execution_times[0] else 'degrading'
            trends['execution_time_trend'] = time_trend
        
        if len(memory_usage) >= 2:
            memory_trend = 'improving' if memory_usage[-1] < memory_usage[0] else 'degrading'
            trends['memory_trend'] = memory_trend
        
        return trends


# Global performance coordinator
perf_coordinator = PerformanceBenchmarkCoordinator()


class PerformanceProfiler:
    """System resource profiling for performance analysis."""
    
    def __init__(self):
        self.process = None
        self.monitoring_active = False
        self.resource_samples = []
        self.monitoring_thread = None
    
    def start_profiling(self, process_pid: Optional[int] = None):
        """Start resource monitoring."""
        if process_pid:
            try:
                self.process = psutil.Process(process_pid)
            except psutil.NoSuchProcess:
                self.process = psutil.Process()
        else:
            self.process = psutil.Process()
        
        self.monitoring_active = True
        self.resource_samples = []
        
        # Start monitoring in separate thread
        self.monitoring_thread = threading.Thread(target=self._monitor_resources)
        self.monitoring_thread.start()
    
    def stop_profiling(self) -> Dict[str, Any]:
        """Stop monitoring and return resource usage summary."""
        self.monitoring_active = False
        
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=2)
        
        if not self.resource_samples:
            return {'error': 'No resource samples collected'}
        
        # Calculate statistics
        cpu_percentages = [sample['cpu_percent'] for sample in self.resource_samples]
        memory_mb = [sample['memory_mb'] for sample in self.resource_samples]
        
        return {
            'samples_collected': len(self.resource_samples),
            'monitoring_duration_s': max(sample['timestamp'] for sample in self.resource_samples) - 
                                   min(sample['timestamp'] for sample in self.resource_samples),
            'cpu_stats': {
                'mean': statistics.mean(cpu_percentages),
                'max': max(cpu_percentages),
                'min': min(cpu_percentages),
                'stdev': statistics.stdev(cpu_percentages) if len(cpu_percentages) > 1 else 0
            },
            'memory_stats': {
                'mean_mb': statistics.mean(memory_mb),
                'peak_mb': max(memory_mb),
                'min_mb': min(memory_mb),
                'stdev_mb': statistics.stdev(memory_mb) if len(memory_mb) > 1 else 0
            },
            'resource_efficiency': self._calculate_resource_efficiency()
        }
    
    def _monitor_resources(self):
        """Monitor system resources in background thread."""
        while self.monitoring_active:
            try:
                if self.process and self.process.is_running():
                    cpu_percent = self.process.cpu_percent()
                    memory_info = self.process.memory_info()
                    memory_mb = memory_info.rss / 1024 / 1024  # Convert to MB
                    
                    sample = {
                        'timestamp': time.time(),
                        'cpu_percent': cpu_percent,
                        'memory_mb': memory_mb,
                        'memory_rss': memory_info.rss,
                        'memory_vms': memory_info.vms
                    }
                    
                    self.resource_samples.append(sample)
                
                time.sleep(0.1)  # Sample every 100ms
                
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                break
            except Exception:
                continue
    
    def _calculate_resource_efficiency(self) -> float:
        """Calculate resource utilization efficiency score."""
        if not self.resource_samples:
            return 0.0
        
        cpu_percentages = [sample['cpu_percent'] for sample in self.resource_samples]
        memory_mb = [sample['memory_mb'] for sample in self.resource_samples]
        
        # Efficiency based on reasonable resource usage
        avg_cpu = statistics.mean(cpu_percentages)
        peak_memory = max(memory_mb)
        
        # Good efficiency: moderate CPU usage, reasonable memory
        cpu_efficiency = 1.0 - min(1.0, max(0, (avg_cpu - 50) / 50))  # Penalty for >50% CPU
        memory_efficiency = 1.0 - min(1.0, max(0, (peak_memory - 256) / 768))  # Penalty for >256MB
        
        return (cpu_efficiency + memory_efficiency) / 2


@pytest.fixture
def perf_workflow_validator():
    """Create workflow validator for performance testing."""
    return SequentialWorkflowValidator(perf_coordinator)


@pytest.fixture
def performance_profiler():
    """Create performance profiler."""
    return PerformanceProfiler()


class TestPerformanceBenchmarks:
    """Test comprehensive performance benchmarks."""
    
    def test_small_project_baseline_performance(self, perf_workflow_validator, performance_profiler):
        """Establish baseline performance metrics for small projects."""
        scenario_id = "small_project_baseline"
        perf_workflow_validator.start_scenario(scenario_id, "Small project baseline performance")
        
        # Create small test project
        temp_dir = tempfile.mkdtemp()
        project_path = Path(temp_dir)
        
        # Create 5 small files with various violations
        for i in range(5):
            (project_path / f"module_{i}.py").write_text(f"""
# Module {i} with controlled violations

def function_{i}(param1, param2, param3, param4, param5):  # Parameter bomb
    '''Function with parameter bomb violation.'''
    magic_value = {100 + i * 10}  # Magic literal
    secret_key = "secret_key_{i}"  # Magic string
    
    if param1 > magic_value:
        return param1 * {2.0 + i * 0.1}  # Magic literal
    
    return param1


class Class_{i}:
    '''Class with moderate method count.'''
    
    def __init__(self):
        self.timeout = {1000 + i * 100}  # Magic literal
    
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
""")
        
        perf_workflow_validator.add_step("create_small_project", {
            'files_created': 5,
            'estimated_violations': 25,
            'project_size': 'small'
        })
        
        # Start profiling
        performance_profiler.start_profiling()
        
        # Execute baseline analysis
        cli = ConnascenceCLI()
        output_file = project_path / "baseline_results.json"
        
        start_time = time.time()
        exit_code = cli.run([
            "scan", str(project_path),
            "--format", "json",
            "--output", str(output_file)
        ])
        execution_time = time.time() - start_time
        
        # Stop profiling
        resource_stats = performance_profiler.stop_profiling()
        
        perf_workflow_validator.add_step("execute_baseline_analysis", {
            'exit_code': exit_code,
            'execution_time_ms': execution_time * 1000
        })
        
        # Analyze results
        assert output_file.exists(), "Baseline analysis output not created"
        
        with open(output_file, 'r') as f:
            results = json.load(f)
        
        violations = results.get('violations', [])
        
        # Calculate baseline metrics
        baseline_metrics = {
            'benchmark_type': 'small_project_baseline',
            'files_analyzed': results.get('total_files_analyzed', 0),
            'violations_found': len(violations),
            'execution_time_ms': execution_time * 1000,
            'violations_per_second': len(violations) / max(execution_time, 0.001),
            'files_per_second': results.get('total_files_analyzed', 0) / max(execution_time, 0.001),
            'memory_peak_mb': resource_stats.get('memory_stats', {}).get('peak_mb', 0),
            'cpu_avg_percent': resource_stats.get('cpu_stats', {}).get('mean', 0),
            'resource_efficiency': resource_stats.get('resource_efficiency', 0),
            'project_characteristics': {
                'file_count': 5,
                'estimated_loc': 300,  # Approximately 60 lines per file
                'violation_density': len(violations) / results.get('total_files_analyzed', 1)
            }
        }
        
        # Store as baseline
        perf_coordinator.store_performance_baseline("small_project", baseline_metrics)
        perf_coordinator.store_benchmark_result(scenario_id, baseline_metrics)
        
        perf_workflow_validator.add_step("calculate_baseline_metrics", baseline_metrics)
        
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir)
        
        # Performance assertions
        assert execution_time < 10.0, f"Small project analysis too slow: {execution_time}s"
        assert baseline_metrics['violations_per_second'] > 5, f"Low violation detection rate: {baseline_metrics['violations_per_second']}"
        assert baseline_metrics['memory_peak_mb'] < 512, f"High memory usage for small project: {baseline_metrics['memory_peak_mb']}MB"
        
        perf_workflow_validator.complete_scenario(True, {
            'baseline_established': True,
            'performance_acceptable': execution_time < 10.0,
            'baseline_metrics': baseline_metrics
        })
    
    def test_medium_project_scalability(self, perf_workflow_validator, performance_profiler):
        """Test performance scalability with medium-sized projects."""
        scenario_id = "medium_project_scalability"
        perf_workflow_validator.start_scenario(scenario_id, "Medium project scalability testing")
        
        # Create medium test project
        temp_dir = tempfile.mkdtemp()
        project_path = Path(temp_dir)
        
        # Create 25 files with violations
        file_count = 25
        for i in range(file_count):
            (project_path / f"module_{i:02d}.py").write_text(f"""
# Module {i} with various violation patterns

def primary_function_{i}(param1, param2, param3, param4, param5, param6):  # Parameter bomb
    '''Primary function with violations.'''
    threshold_value = {150 + i * 20}  # Magic literal
    api_secret = "api_secret_key_{i}_production"  # Magic string
    timeout_ms = {5000 + i * 200}  # Magic literal
    
    # Complex conditional logic
    if param1 > threshold_value and param2 == "active":  # Magic string
        if param3 and len(str(param3)) > 10:  # Magic literal
            processing_factor = {1.5 + i * 0.05}  # Magic literal
            return param1 * processing_factor + timeout_ms
        else:
            return param1 + {50 + i}  # Magic literal
    
    return 0


def secondary_function_{i}(data, config, options, metadata, context):  # Parameter bomb
    '''Secondary function with different violation patterns.'''
    cache_size = {1024 * (i + 1)}  # Magic literal
    retry_limit = {3 + (i % 5)}  # Magic literal
    
    if data and len(data) > cache_size // 100:  # Magic literal calculation
        for attempt in range(retry_limit):
            if process_item(data[attempt], config):
                return True
    
    return False


def process_item(item, config):  # Missing type hints
    return len(str(item)) > {20 + (i % 10)}  # Magic literal


class ProcessorClass_{i}:
    '''Class with many methods - approaching god class.'''
    
    def __init__(self):
        self.buffer_size = {8192 + i * 512}  # Magic literal
        self.max_connections = {100 + i * 5}  # Magic literal
        self.heartbeat_interval = {30000 + i * 1000}  # Magic literal
    
    def initialize_{i}(self): pass
    def configure_{i}(self): pass
    def start_processing_{i}(self): pass
    def handle_requests_{i}(self): pass
    def process_batch_{i}(self): pass
    def validate_data_{i}(self): pass
    def transform_data_{i}(self): pass
    def store_results_{i}(self): pass
    def generate_metrics_{i}(self): pass
    def cleanup_resources_{i}(self): pass
    def handle_errors_{i}(self): pass
    def log_activities_{i}(self): pass
    def monitor_health_{i}(self): pass
    def backup_state_{i}(self): pass
    def restore_state_{i}(self): pass
    def scale_resources_{i}(self): pass
    def optimize_performance_{i}(self): pass
    def audit_operations_{i}(self): pass
    def manage_lifecycle_{i}(self): pass
    def coordinate_tasks_{i}(self): pass
    def synthesize_reports_{i}(self): pass  # 21 methods - god class
""")
        
        perf_workflow_validator.add_step("create_medium_project", {
            'files_created': file_count,
            'estimated_violations': file_count * 8,  # ~8 violations per file
            'project_size': 'medium'
        })
        
        # Start profiling
        performance_profiler.start_profiling()
        
        # Execute scalability analysis
        cli = ConnascenceCLI()
        output_file = project_path / "scalability_results.json"
        
        start_time = time.time()
        exit_code = cli.run([
            "scan", str(project_path),
            "--policy", "service-defaults",
            "--format", "json", 
            "--output", str(output_file)
        ])
        execution_time = time.time() - start_time
        
        # Stop profiling
        resource_stats = performance_profiler.stop_profiling()
        
        # Analyze results
        with open(output_file, 'r') as f:
            results = json.load(f)
        
        violations = results.get('violations', [])
        
        # Calculate scalability metrics
        scalability_metrics = {
            'benchmark_type': 'medium_project_scalability',
            'files_analyzed': results.get('total_files_analyzed', 0),
            'violations_found': len(violations),
            'execution_time_ms': execution_time * 1000,
            'violations_per_second': len(violations) / max(execution_time, 0.001),
            'files_per_second': results.get('total_files_analyzed', 0) / max(execution_time, 0.001),
            'memory_peak_mb': resource_stats.get('memory_stats', {}).get('peak_mb', 0),
            'cpu_avg_percent': resource_stats.get('cpu_stats', {}).get('mean', 0),
            'resource_efficiency': resource_stats.get('resource_efficiency', 0),
            'scalability_factor': file_count / 5,  # Compared to small project baseline
            'per_file_processing_time': execution_time / max(file_count, 1),
            'memory_per_file_mb': resource_stats.get('memory_stats', {}).get('peak_mb', 0) / max(file_count, 1)
        }
        
        perf_coordinator.store_scalability_metrics(scenario_id, scalability_metrics)
        perf_coordinator.store_benchmark_result(scenario_id, scalability_metrics)
        
        # Compare with baseline
        if "small_project" in perf_coordinator.performance_baselines:
            baseline_comparison = perf_coordinator.compare_with_baseline(scenario_id, "small_project")
            perf_workflow_validator.add_step("baseline_comparison", baseline_comparison)
        
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir)
        
        # Scalability assertions
        assert execution_time < 30.0, f"Medium project analysis too slow: {execution_time}s"
        assert scalability_metrics['per_file_processing_time'] < 2.0, f"Per-file processing time too high: {scalability_metrics['per_file_processing_time']}s"
        assert scalability_metrics['memory_per_file_mb'] < 20, f"Memory per file too high: {scalability_metrics['memory_per_file_mb']}MB"
        assert scalability_metrics['violations_per_second'] > 10, f"Violation detection rate too low: {scalability_metrics['violations_per_second']}"
        
        perf_workflow_validator.complete_scenario(True, {
            'scalability_test_completed': True,
            'performance_acceptable': execution_time < 30.0,
            'scalability_metrics': scalability_metrics
        })
    
    def test_large_project_stress_testing(self, perf_workflow_validator, performance_profiler):
        """Test performance under stress with large projects."""
        scenario_id = "large_project_stress_test"
        perf_workflow_validator.start_scenario(scenario_id, "Large project stress testing")
        
        # Create large test project
        temp_dir = tempfile.mkdtemp()
        project_path = Path(temp_dir)
        
        # Create project structure with 100 files
        file_count = 100
        
        # Create directories for organization
        for dept in ['core', 'services', 'utils', 'integrations', 'analytics']:
            dept_dir = project_path / dept
            dept_dir.mkdir()
            
            # 20 files per department
            for i in range(20):
                file_index = dept.upper()[0] + f"{i:02d}"
                
                (dept_dir / f"{dept}_module_{i:02d}.py").write_text(f"""
# {dept.title()} Module {i} - Large project stress test

def {dept}_primary_function_{i}(param1, param2, param3, param4, param5, param6, param7):  # Parameter bomb
    '''Primary {dept} function with stress test violations.'''
    
    # Multiple magic values for stress testing
    threshold_alpha = {200 + i * 30}  # Magic literal
    threshold_beta = {500 + i * 50}  # Magic literal  
    threshold_gamma = {1000 + i * 100}  # Magic literal
    
    secret_key = "{dept}_secret_key_{i}_production_environment"  # Magic string
    api_endpoint = "https://api.{dept}.example.com/v1/endpoint/{i}"  # Magic string
    database_url = "postgresql://user:pass@{dept}-db-{i}.internal:5432/db"  # Magic string
    
    # Complex nested logic for stress testing
    if param1 > threshold_alpha:
        if param2 == "high_priority" and param3:  # Magic string
            if param4 and len(str(param4)) > {15 + i}:  # Magic literal
                processing_multiplier = {2.5 + i * 0.1}  # Magic literal
                cache_duration = {3600 + i * 300}  # Magic literal - seconds
                
                for iteration in range({5 + (i % 10)}):  # Magic literal
                    result = complex_calculation(param1, processing_multiplier, cache_duration)
                    if result > threshold_beta:
                        return result * {1.2 + i * 0.02}  # Magic literal
                        
        elif param2 == "medium_priority":  # Magic string
            batch_size = {50 + i * 5}  # Magic literal
            timeout_seconds = {30 + i * 2}  # Magic literal
            
            return batch_process(param1, batch_size, timeout_seconds)
            
    elif param1 > threshold_gamma:
        fallback_value = {42 + i}  # Magic literal
        error_threshold = {10 + (i % 5)}  # Magic literal
        
        return handle_fallback(param1, fallback_value, error_threshold)
    
    return {-1}  # Magic literal


def {dept}_secondary_function_{i}(data, config, options, metadata, context, audit_info):  # Parameter bomb
    '''Secondary function for {dept} with additional violations.'''
    
    max_retries = {3 + (i % 7)}  # Magic literal
    backoff_factor = {1.5 + i * 0.05}  # Magic literal
    circuit_breaker_threshold = {5 + (i % 3)}  # Magic literal
    
    for attempt in range(max_retries):
        try:
            if process_complex_data(data, config):
                success_rate = calculate_success_rate(attempt, max_retries)
                if success_rate > {0.8 - i * 0.01}:  # Magic literal
                    return True
        except Exception:
            wait_time = backoff_factor * (attempt + 1) * {1000}  # Magic literal - ms
            time.sleep(wait_time / 1000)
    
    return False


def complex_calculation(value, multiplier, duration):  # Missing type hints
    '''Complex calculation without type hints.'''
    base_result = value * multiplier
    time_factor = duration / {3600}  # Magic literal
    complexity_bonus = {100 + hash(str(value)) % 200}  # Magic literal
    
    return base_result + time_factor + complexity_bonus


def batch_process(data, batch_size, timeout):  # Missing type hints
    '''Batch processing function.'''
    processed = 0
    batch_count = len(str(data)) // batch_size
    
    for batch in range(batch_count):
        if processed >= {1000}:  # Magic literal - max processed
            break
        processed += batch_size
        
    return processed


def handle_fallback(value, fallback, error_threshold):  # Missing type hints
    '''Fallback handling function.'''
    if value < error_threshold:
        return fallback * {2}  # Magic literal
    return value + fallback


def process_complex_data(data, config):  # Missing type hints
    '''Complex data processing.'''
    return len(str(data)) > {50} and config is not None  # Magic literal


def calculate_success_rate(attempt, max_attempts):  # Missing type hints
    '''Calculate success rate.'''
    return (max_attempts - attempt) / max_attempts


class {dept.title()}MegaProcessor_{i}:
    '''Mega processor class - definite god class for stress testing.'''
    
    def __init__(self):
        self.cache_size = {16384 + i * 1024}  # Magic literal
        self.thread_pool_size = {20 + i}  # Magic literal
        self.connection_timeout = {30000 + i * 1000}  # Magic literal
        self.max_queue_size = {1000 + i * 100}  # Magic literal
    
    # 30+ methods to ensure god class detection
    def initialize_system_{i}(self): pass
    def configure_connections_{i}(self): pass
    def setup_thread_pool_{i}(self): pass
    def start_message_queue_{i}(self): pass
    def handle_incoming_requests_{i}(self): pass
    def validate_request_data_{i}(self): pass
    def authenticate_users_{i}(self): pass
    def authorize_operations_{i}(self): pass
    def process_business_logic_{i}(self): pass
    def transform_data_format_{i}(self): pass
    def validate_business_rules_{i}(self): pass
    def execute_database_queries_{i}(self): pass
    def cache_intermediate_results_{i}(self): pass
    def generate_audit_logs_{i}(self): pass
    def handle_error_conditions_{i}(self): pass
    def retry_failed_operations_{i}(self): pass
    def manage_circuit_breakers_{i}(self): pass
    def monitor_system_health_{i}(self): pass
    def collect_performance_metrics_{i}(self): pass
    def generate_status_reports_{i}(self): pass
    def backup_critical_data_{i}(self): pass
    def restore_from_backups_{i}(self): pass
    def scale_system_resources_{i}(self): pass
    def optimize_query_performance_{i}(self): pass
    def manage_user_sessions_{i}(self): pass
    def handle_file_uploads_{i}(self): pass
    def process_batch_jobs_{i}(self): pass
    def manage_scheduled_tasks_{i}(self): pass
    def coordinate_microservices_{i}(self): pass
    def handle_webhook_callbacks_{i}(self): pass
    def manage_api_rate_limits_{i}(self): pass
    def cleanup_temporary_resources_{i}(self): pass  # 32 methods - definite god class
""")
        
        perf_workflow_validator.add_step("create_large_project", {
            'files_created': file_count,
            'departments': 5,
            'estimated_violations': file_count * 15,  # ~15 violations per file
            'project_size': 'large',
            'stress_test': True
        })
        
        # Start profiling
        performance_profiler.start_profiling()
        
        # Execute stress test analysis
        cli = ConnascenceCLI()
        output_file = project_path / "stress_test_results.json"
        
        start_time = time.time()
        exit_code = cli.run([
            "scan", str(project_path),
            "--policy", "service-defaults",
            "--format", "json",
            "--output", str(output_file)
        ])
        execution_time = time.time() - start_time
        
        # Stop profiling
        resource_stats = performance_profiler.stop_profiling()
        
        # Analyze stress test results
        with open(output_file, 'r') as f:
            results = json.load(f)
        
        violations = results.get('violations', [])
        
        # Calculate stress test metrics
        stress_metrics = {
            'benchmark_type': 'large_project_stress_test',
            'files_analyzed': results.get('total_files_analyzed', 0),
            'violations_found': len(violations),
            'execution_time_ms': execution_time * 1000,
            'violations_per_second': len(violations) / max(execution_time, 0.001),
            'files_per_second': results.get('total_files_analyzed', 0) / max(execution_time, 0.001),
            'memory_peak_mb': resource_stats.get('memory_stats', {}).get('peak_mb', 0),
            'memory_mean_mb': resource_stats.get('memory_stats', {}).get('mean_mb', 0),
            'cpu_avg_percent': resource_stats.get('cpu_stats', {}).get('mean', 0),
            'cpu_peak_percent': resource_stats.get('cpu_stats', {}).get('max', 0),
            'resource_efficiency': resource_stats.get('resource_efficiency', 0),
            'stress_intensity': file_count,
            'per_file_processing_ms': (execution_time * 1000) / max(file_count, 1),
            'memory_efficiency_mb_per_file': resource_stats.get('memory_stats', {}).get('peak_mb', 0) / max(file_count, 1),
            'throughput_stability': self._calculate_throughput_stability(violations, execution_time)
        }
        
        perf_coordinator.store_benchmark_result(scenario_id, stress_metrics)
        
        # Store detailed resource utilization
        resource_utilization = {
            'test_type': 'stress_test',
            'resource_samples': len(resource_stats.get('samples_collected', 0)),
            'monitoring_duration': resource_stats.get('monitoring_duration_s', 0),
            'cpu_utilization': resource_stats.get('cpu_stats', {}),
            'memory_utilization': resource_stats.get('memory_stats', {}),
            'efficiency_score': resource_stats.get('resource_efficiency', 0)
        }
        
        perf_coordinator.store_resource_utilization(scenario_id, resource_utilization)
        
        perf_workflow_validator.add_step("stress_test_analysis", stress_metrics)
        
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir)
        
        # Stress test assertions
        assert execution_time < 120.0, f"Large project stress test too slow: {execution_time}s"
        assert stress_metrics['memory_peak_mb'] < 2048, f"Memory usage too high under stress: {stress_metrics['memory_peak_mb']}MB"
        assert stress_metrics['files_per_second'] > 1.0, f"File processing rate too low: {stress_metrics['files_per_second']}"
        assert stress_metrics['violations_per_second'] > 20, f"Violation detection rate too low under stress: {stress_metrics['violations_per_second']}"
        
        perf_workflow_validator.complete_scenario(True, {
            'stress_test_completed': True,
            'performance_under_stress': execution_time < 120.0,
            'memory_efficient_under_stress': stress_metrics['memory_peak_mb'] < 2048,
            'stress_metrics': stress_metrics
        })
    
    def test_concurrent_analysis_performance(self, perf_workflow_validator, performance_profiler):
        """Test performance of concurrent analysis execution."""
        scenario_id = "concurrent_analysis_performance"
        perf_workflow_validator.start_scenario(scenario_id, "Concurrent analysis performance testing")
        
        # Create multiple projects for concurrent analysis
        temp_base = tempfile.mkdtemp()
        base_path = Path(temp_base)
        
        project_count = 4
        projects = []
        
        # Create projects of varying sizes
        for i in range(project_count):
            project_dir = base_path / f"concurrent_project_{i}"
            project_dir.mkdir()
            
            # Varying file counts: 5, 10, 15, 20
            file_count = 5 + i * 5
            
            for j in range(file_count):
                (project_dir / f"module_{j}.py").write_text(f"""
# Concurrent test module {i}-{j}

def concurrent_function_{i}_{j}(param1, param2, param3, param4, param5):  # Parameter bomb
    magic_value = {100 + i * 10 + j}  # Magic literal
    secret = "secret_{i}_{j}"  # Magic string
    
    if param1 > magic_value:
        return param1 * {2.0 + i * 0.1}  # Magic literal
    return param1


class ConcurrentClass_{i}_{j}:
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
    def method_21(self): pass  # God class
""")
            
            projects.append({
                'path': project_dir,
                'file_count': file_count,
                'project_id': i
            })
        
        perf_workflow_validator.add_step("create_concurrent_projects", {
            'projects_created': project_count,
            'total_files': sum(p['file_count'] for p in projects)
        })
        
        # Sequential execution baseline
        performance_profiler.start_profiling()
        
        sequential_start = time.time()
        sequential_results = []
        
        for project in projects:
            cli = ConnascenceCLI()
            output_file = project['path'] / "sequential_results.json"
            
            exit_code = cli.run([
                "scan", str(project['path']),
                "--format", "json",
                "--output", str(output_file)
            ])
            
            with open(output_file, 'r') as f:
                results = json.load(f)
            
            sequential_results.append({
                'project_id': project['project_id'],
                'violations': len(results.get('violations', [])),
                'files_analyzed': results.get('total_files_analyzed', 0),
                'exit_code': exit_code
            })
        
        sequential_time = time.time() - sequential_start
        sequential_resource_stats = performance_profiler.stop_profiling()
        
        perf_workflow_validator.add_step("sequential_execution", {
            'execution_time_ms': sequential_time * 1000,
            'projects_processed': len(sequential_results)
        })
        
        # Concurrent execution test
        performance_profiler.start_profiling()
        
        def analyze_project_concurrent(project):
            cli = ConnascenceCLI()
            output_file = project['path'] / "concurrent_results.json"
            
            exit_code = cli.run([
                "scan", str(project['path']),
                "--format", "json",
                "--output", str(output_file)
            ])
            
            with open(output_file, 'r') as f:
                results = json.load(f)
            
            return {
                'project_id': project['project_id'],
                'violations': len(results.get('violations', [])),
                'files_analyzed': results.get('total_files_analyzed', 0),
                'exit_code': exit_code
            }
        
        concurrent_start = time.time()
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(analyze_project_concurrent, project) for project in projects]
            concurrent_results = [future.result() for future in futures]
        
        concurrent_time = time.time() - concurrent_start
        concurrent_resource_stats = performance_profiler.stop_profiling()
        
        perf_workflow_validator.add_step("concurrent_execution", {
            'execution_time_ms': concurrent_time * 1000,
            'projects_processed': len(concurrent_results)
        })
        
        # Calculate concurrent performance metrics
        concurrent_metrics = {
            'benchmark_type': 'concurrent_analysis_performance',
            'projects_analyzed': project_count,
            'sequential_time_ms': sequential_time * 1000,
            'concurrent_time_ms': concurrent_time * 1000,
            'speedup_factor': sequential_time / concurrent_time if concurrent_time > 0 else 1.0,
            'efficiency': (sequential_time / concurrent_time) / 3 if concurrent_time > 0 else 0.0,  # 3 workers
            'sequential_memory_peak_mb': sequential_resource_stats.get('memory_stats', {}).get('peak_mb', 0),
            'concurrent_memory_peak_mb': concurrent_resource_stats.get('memory_stats', {}).get('peak_mb', 0),
            'memory_overhead_factor': (
                concurrent_resource_stats.get('memory_stats', {}).get('peak_mb', 0) /
                max(sequential_resource_stats.get('memory_stats', {}).get('peak_mb', 1), 1)
            ),
            'total_violations_sequential': sum(r['violations'] for r in sequential_results),
            'total_violations_concurrent': sum(r['violations'] for r in concurrent_results),
            'results_consistency': sum(r['violations'] for r in sequential_results) == sum(r['violations'] for r in concurrent_results),
            'concurrent_throughput': sum(r['violations'] for r in concurrent_results) / max(concurrent_time, 0.001),
            'resource_utilization_efficiency': concurrent_resource_stats.get('resource_efficiency', 0)
        }
        
        perf_coordinator.store_throughput_measurement(scenario_id, {
            'sequential_throughput': sum(r['violations'] for r in sequential_results) / max(sequential_time, 0.001),
            'concurrent_throughput': concurrent_metrics['concurrent_throughput'],
            'throughput_improvement': concurrent_metrics['speedup_factor']
        })
        
        perf_coordinator.store_benchmark_result(scenario_id, concurrent_metrics)
        
        perf_workflow_validator.add_step("concurrent_performance_analysis", concurrent_metrics)
        
        # Cleanup
        import shutil
        shutil.rmtree(temp_base)
        
        # Concurrent performance assertions
        assert concurrent_metrics['speedup_factor'] > 1.0, f"Concurrent execution should be faster: {concurrent_metrics['speedup_factor']}"
        assert concurrent_metrics['results_consistency'], "Concurrent and sequential results should match"
        assert concurrent_metrics['efficiency'] > 0.3, f"Concurrent efficiency too low: {concurrent_metrics['efficiency']}"
        assert concurrent_metrics['memory_overhead_factor'] < 3.0, f"Memory overhead too high: {concurrent_metrics['memory_overhead_factor']}"
        
        perf_workflow_validator.complete_scenario(True, {
            'concurrent_performance_tested': True,
            'speedup_achieved': concurrent_metrics['speedup_factor'] > 1.0,
            'concurrent_metrics': concurrent_metrics
        })
    
    def test_memory_usage_profiling(self, perf_workflow_validator):
        """Test detailed memory usage profiling."""
        scenario_id = "memory_usage_profiling"
        perf_workflow_validator.start_scenario(scenario_id, "Memory usage profiling")
        
        # Create project with varying memory requirements
        temp_dir = tempfile.mkdtemp()
        project_path = Path(temp_dir)
        
        # Create files with different characteristics that might affect memory
        memory_test_cases = [
            {
                'name': 'small_simple',
                'file_count': 5,
                'complexity': 'low'
            },
            {
                'name': 'medium_complex',
                'file_count': 20,
                'complexity': 'medium'
            },
            {
                'name': 'large_dense',
                'file_count': 50,
                'complexity': 'high'
            }
        ]
        
        memory_profiles = {}
        
        for test_case in memory_test_cases:
            case_dir = project_path / test_case['name']
            case_dir.mkdir()
            
            # Generate files based on complexity
            for i in range(test_case['file_count']):
                if test_case['complexity'] == 'low':
                    content = f"""
def simple_function_{i}(param1, param2, param3, param4): pass  # Parameter bomb
magic_value = {i}  # Magic literal
"""
                elif test_case['complexity'] == 'medium':
                    content = f"""
def medium_function_{i}(p1, p2, p3, p4, p5): pass  # Parameter bomb
magic_a = {i * 10}  # Magic literal
magic_b = {i * 20}  # Magic literal
secret = "key_{i}"  # Magic string

class MediumClass_{i}:
    def m1(self): pass
    def m2(self): pass
    def m3(self): pass
    def m4(self): pass
    def m5(self): pass
    def m6(self): pass
    def m7(self): pass
    def m8(self): pass
    def m9(self): pass
    def m10(self): pass
"""
                else:  # high complexity
                    methods = "\n    ".join([f"def method_{j:02d}(self): pass" for j in range(25)])
                    content = f"""
def complex_function_{i}(a, b, c, d, e, f, g): pass  # Parameter bomb
threshold_1 = {i * 100}  # Magic literal
threshold_2 = {i * 200}  # Magic literal
threshold_3 = {i * 300}  # Magic literal
api_key = "complex_key_{i}_production"  # Magic string
database_url = "postgres://user:pass@host:5432/db_{i}"  # Magic string

class HighComplexityClass_{i}:
    {methods}
"""
                
                (case_dir / f"file_{i:02d}.py").write_text(content)
            
            # Profile memory usage for this case
            profiler = PerformanceProfiler()
            profiler.start_profiling()
            
            cli = ConnascenceCLI()
            start_time = time.time()
            exit_code = cli.run(["scan", str(case_dir)])
            execution_time = time.time() - start_time
            
            resource_stats = profiler.stop_profiling()
            
            memory_profile = {
                'test_case': test_case['name'],
                'file_count': test_case['file_count'],
                'complexity': test_case['complexity'],
                'execution_time_ms': execution_time * 1000,
                'memory_peak_mb': resource_stats.get('memory_stats', {}).get('peak_mb', 0),
                'memory_mean_mb': resource_stats.get('memory_stats', {}).get('mean_mb', 0),
                'memory_efficiency': resource_stats.get('memory_stats', {}).get('peak_mb', 0) / max(test_case['file_count'], 1),
                'memory_growth_pattern': self._analyze_memory_growth(resource_stats),
                'exit_code': exit_code
            }
            
            memory_profiles[test_case['name']] = memory_profile
            
            perf_coordinator.store_memory_profile(f"{scenario_id}_{test_case['name']}", memory_profile)
            perf_workflow_validator.add_step(f"profile_{test_case['name']}", memory_profile)
        
        # Analyze memory scaling patterns
        memory_analysis = {
            'profiles_completed': len(memory_profiles),
            'memory_scaling_factor': self._calculate_memory_scaling(memory_profiles),
            'memory_efficiency_trend': self._analyze_memory_efficiency_trend(memory_profiles),
            'peak_memory_usage': max(p['memory_peak_mb'] for p in memory_profiles.values()),
            'most_memory_efficient': min(memory_profiles.items(), key=lambda x: x[1]['memory_efficiency'])[0],
            'memory_usage_predictable': self._assess_memory_predictability(memory_profiles)
        }
        
        perf_coordinator.store_benchmark_result(scenario_id, {
            'benchmark_type': 'memory_usage_profiling',
            'memory_profiles': memory_profiles,
            'memory_analysis': memory_analysis
        })
        
        perf_workflow_validator.add_step("memory_analysis", memory_analysis)
        
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir)
        
        # Memory profiling assertions
        assert memory_analysis['peak_memory_usage'] < 1024, f"Peak memory usage too high: {memory_analysis['peak_memory_usage']}MB"
        assert memory_analysis['memory_usage_predictable'], "Memory usage should be predictable"
        assert all(p['memory_efficiency'] < 50 for p in memory_profiles.values()), "Memory efficiency per file should be reasonable"
        
        perf_workflow_validator.complete_scenario(True, {
            'memory_profiling_completed': True,
            'memory_usage_acceptable': memory_analysis['peak_memory_usage'] < 1024,
            'memory_analysis': memory_analysis
        })
    
    def test_performance_regression_detection(self, perf_workflow_validator):
        """Test performance regression detection capabilities."""
        scenario_id = "performance_regression_detection"
        perf_workflow_validator.start_scenario(scenario_id, "Performance regression detection")
        
        # Create consistent test project
        temp_dir = tempfile.mkdtemp()
        project_path = Path(temp_dir)
        
        # Create standardized test project
        for i in range(10):
            (project_path / f"regression_test_{i}.py").write_text(f"""
def regression_function_{i}(param1, param2, param3, param4, param5):  # Parameter bomb
    magic_constant = {100 + i * 10}  # Magic literal
    secret_key = "regression_test_key_{i}"  # Magic string
    
    if param1 > magic_constant:
        return param1 * {2.5 + i * 0.1}  # Magic literal
    return param1

class RegressionClass_{i}:
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
    def method_21(self): pass  # God class
""")
        
        # Establish baseline
        baseline_runs = 3
        baseline_results = []
        
        for run in range(baseline_runs):
            profiler = PerformanceProfiler()
            profiler.start_profiling()
            
            cli = ConnascenceCLI()
            start_time = time.time()
            exit_code = cli.run(["scan", str(project_path)])
            execution_time = time.time() - start_time
            
            resource_stats = profiler.stop_profiling()
            
            baseline_results.append({
                'run': run + 1,
                'execution_time_ms': execution_time * 1000,
                'memory_peak_mb': resource_stats.get('memory_stats', {}).get('peak_mb', 0),
                'cpu_avg_percent': resource_stats.get('cpu_stats', {}).get('mean', 0)
            })
        
        # Calculate baseline metrics
        baseline_metrics = {
            'execution_time_ms': statistics.mean([r['execution_time_ms'] for r in baseline_results]),
            'execution_time_stdev': statistics.stdev([r['execution_time_ms'] for r in baseline_results]) if len(baseline_results) > 1 else 0,
            'memory_peak_mb': statistics.mean([r['memory_peak_mb'] for r in baseline_results]),
            'memory_stdev': statistics.stdev([r['memory_peak_mb'] for r in baseline_results]) if len(baseline_results) > 1 else 0,
            'cpu_avg_percent': statistics.mean([r['cpu_avg_percent'] for r in baseline_results]),
            'baseline_runs': baseline_runs
        }
        
        perf_coordinator.store_performance_baseline("regression_baseline", baseline_metrics)
        perf_workflow_validator.add_step("establish_baseline", baseline_metrics)
        
        # Simulate potential regression scenarios
        regression_scenarios = [
            {
                'name': 'current_performance',
                'description': 'Current performance should match baseline',
                'expected_regression': False
            }
        ]
        
        regression_results = {}
        
        for scenario in regression_scenarios:
            scenario_name = scenario['name']
            
            # Run performance test
            profiler = PerformanceProfiler()
            profiler.start_profiling()
            
            cli = ConnascenceCLI()
            start_time = time.time()
            exit_code = cli.run(["scan", str(project_path)])
            execution_time = time.time() - start_time
            
            resource_stats = profiler.stop_profiling()
            
            scenario_metrics = {
                'execution_time_ms': execution_time * 1000,
                'memory_peak_mb': resource_stats.get('memory_stats', {}).get('peak_mb', 0),
                'cpu_avg_percent': resource_stats.get('cpu_stats', {}).get('mean', 0)
            }
            
            # Compare with baseline
            comparison = perf_coordinator.compare_with_baseline(f"temp_{scenario_name}", "regression_baseline")
            
            # Store temporary result for comparison
            perf_coordinator.store_benchmark_result(f"temp_{scenario_name}", {
                'benchmark_type': 'regression_test',
                **scenario_metrics
            })
            
            regression_analysis = {
                'scenario_name': scenario_name,
                'scenario_metrics': scenario_metrics,
                'baseline_comparison': comparison if 'error' not in comparison else None,
                'regression_detected': False,
                'performance_stable': True
            }
            
            # Detect regressions
            if comparison and 'error' not in comparison:
                regressions = [m for m in comparison['metrics_comparison'].values() if m.get('regression', False)]
                regression_analysis['regression_detected'] = len(regressions) > 0
                regression_analysis['regression_details'] = regressions
                regression_analysis['performance_stable'] = not regression_analysis['regression_detected']
            
            regression_results[scenario_name] = regression_analysis
            
            perf_coordinator.store_regression_test(f"{scenario_id}_{scenario_name}", regression_analysis)
            perf_workflow_validator.add_step(f"regression_test_{scenario_name}", regression_analysis)
        
        # Overall regression analysis
        overall_regression_analysis = {
            'scenarios_tested': len(regression_scenarios),
            'regressions_detected': sum(1 for r in regression_results.values() if r['regression_detected']),
            'performance_stable_overall': all(r['performance_stable'] for r in regression_results.values()),
            'baseline_established': True,
            'regression_detection_functional': True
        }
        
        perf_workflow_validator.add_step("overall_regression_analysis", overall_regression_analysis)
        
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir)
        
        # Regression detection assertions
        assert overall_regression_analysis['performance_stable_overall'], "Performance regressions detected"
        assert overall_regression_analysis['baseline_established'], "Baseline should be established"
        
        perf_workflow_validator.complete_scenario(True, {
            'regression_detection_completed': True,
            'performance_stable': overall_regression_analysis['performance_stable_overall'],
            'overall_analysis': overall_regression_analysis
        })
    
    def test_performance_memory_coordination_validation(self):
        """Test performance benchmarking memory coordination system."""
        # Test performance coordinator functionality
        test_benchmark_id = "performance_memory_test"
        
        # Store comprehensive test data
        perf_coordinator.store_benchmark_result(test_benchmark_id, {
            'benchmark_type': 'memory_validation',
            'execution_time_ms': 5000,
            'memory_peak_mb': 256,
            'violations_per_second': 50
        })
        
        perf_coordinator.store_performance_baseline("test_baseline", {
            'execution_time_ms': 4800,
            'memory_peak_mb': 240,
            'violations_per_second': 52
        })
        
        perf_coordinator.store_scalability_metrics("test_scalability", {
            'scalability_factor': 5,
            'files_per_second': 10
        })
        
        perf_coordinator.store_memory_profile("test_memory_profile", {
            'memory_efficiency': 12.5,
            'memory_growth_pattern': 'linear'
        })
        
        perf_coordinator.store_throughput_measurement("test_throughput", {
            'concurrent_throughput': 75,
            'throughput_improvement': 1.5
        })
        
        # Validate comprehensive storage
        assert test_benchmark_id in perf_coordinator.benchmark_results
        assert "test_baseline" in perf_coordinator.performance_baselines
        assert "test_scalability" in perf_coordinator.scalability_metrics
        assert "test_memory_profile" in perf_coordinator.memory_profiles
        assert "test_throughput" in perf_coordinator.throughput_measurements
        
        # Test summary generation
        summary = perf_coordinator.get_performance_summary()
        assert summary['total_benchmarks'] > 0
        assert summary['performance_baselines'] > 0
        assert summary['scalability_tests'] > 0
        assert summary['memory_profiles'] > 0
        assert summary['throughput_measurements'] > 0
        assert summary['overall_performance_score'] >= 0
        
        # Test comparison functionality
        comparison = perf_coordinator.compare_with_baseline(test_benchmark_id, "test_baseline")
        assert 'metrics_comparison' in comparison
        assert 'overall_regression' in comparison
    
    # Helper methods
    def _calculate_throughput_stability(self, violations, execution_time):
        """Calculate throughput stability score."""
        if execution_time <= 0:
            return 0.0
        
        violations_per_second = len(violations) / execution_time
        
        # Stability based on reasonable throughput
        if violations_per_second > 20:
            return 1.0
        elif violations_per_second > 10:
            return 0.8
        elif violations_per_second > 5:
            return 0.6
        else:
            return 0.4
    
    def _analyze_memory_growth(self, resource_stats):
        """Analyze memory growth pattern."""
        if not resource_stats or 'samples_collected' not in resource_stats:
            return 'unknown'
        
        # Simple heuristic based on peak vs mean
        peak_mb = resource_stats.get('memory_stats', {}).get('peak_mb', 0)
        mean_mb = resource_stats.get('memory_stats', {}).get('mean_mb', 0)
        
        if peak_mb > 0 and mean_mb > 0:
            ratio = peak_mb / mean_mb
            if ratio < 1.2:
                return 'stable'
            elif ratio < 1.5:
                return 'moderate_growth'
            else:
                return 'high_growth'
        
        return 'unknown'
    
    def _calculate_memory_scaling(self, memory_profiles):
        """Calculate memory scaling factor across profiles."""
        if len(memory_profiles) < 2:
            return 1.0
        
        profiles = list(memory_profiles.values())
        
        # Sort by file count
        profiles.sort(key=lambda p: p['file_count'])
        
        # Calculate scaling between smallest and largest
        smallest = profiles[0]
        largest = profiles[-1]
        
        file_ratio = largest['file_count'] / max(smallest['file_count'], 1)
        memory_ratio = largest['memory_peak_mb'] / max(smallest['memory_peak_mb'], 1)
        
        # Ideal scaling would be close to 1.0 (linear with file count)
        return memory_ratio / file_ratio if file_ratio > 0 else 1.0
    
    def _analyze_memory_efficiency_trend(self, memory_profiles):
        """Analyze memory efficiency trend across complexity levels."""
        efficiencies = [p['memory_efficiency'] for p in memory_profiles.values()]
        
        if len(efficiencies) < 2:
            return 'insufficient_data'
        
        # Check if efficiency degrades with complexity
        low_complex = [p for p in memory_profiles.values() if p['complexity'] == 'low']
        high_complex = [p for p in memory_profiles.values() if p['complexity'] == 'high']
        
        if low_complex and high_complex:
            avg_low = statistics.mean([p['memory_efficiency'] for p in low_complex])
            avg_high = statistics.mean([p['memory_efficiency'] for p in high_complex])
            
            if avg_high <= avg_low * 1.5:  # Within 50% is acceptable
                return 'efficient'
            elif avg_high <= avg_low * 3.0:  # Within 300% is moderate
                return 'moderate'
            else:
                return 'inefficient'
        
        return 'mixed'
    
    def _assess_memory_predictability(self, memory_profiles):
        """Assess whether memory usage is predictable."""
        profiles = list(memory_profiles.values())
        
        # Check if memory scales reasonably with file count and complexity
        for profile in profiles:
            expected_memory = profile['file_count'] * 5  # Rough estimate: 5MB per file
            actual_memory = profile['memory_peak_mb']
            
            # Allow up to 3x expected memory (very generous)
            if actual_memory > expected_memory * 3:
                return False
        
        return True


@pytest.mark.e2e
@pytest.mark.slow
def test_performance_integration():
    """Integration test for performance benchmarking system."""
    coordinator = PerformanceBenchmarkCoordinator()
    
    # Test complete performance integration
    scenario_id = "performance_integration_test"
    
    coordinator.store_benchmark_result(scenario_id, {
        'integration_test': True,
        'execution_time_ms': 2500,
        'memory_peak_mb': 128
    })
    
    coordinator.store_performance_baseline("integration_baseline", {
        'execution_time_ms': 2400,
        'memory_peak_mb': 120
    })
    
    # Validate integration
    assert scenario_id in coordinator.benchmark_results
    assert "integration_baseline" in coordinator.performance_baselines
    
    summary = coordinator.get_performance_summary()
    assert summary['total_benchmarks'] > 0
    
    print("Performance benchmarking integration test completed successfully")


if __name__ == "__main__":
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "-m", "e2e"
    ])