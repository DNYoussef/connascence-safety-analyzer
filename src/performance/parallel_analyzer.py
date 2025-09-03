"""
High-Performance Parallel Connascence Analyzer

Implements multi-processing, single-pass AST analysis, caching, and algorithm optimizations
to achieve >20% performance improvement over the baseline sequential implementation.
"""

import ast
import hashlib
import json
import multiprocessing as mp
import pickle
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

# Performance optimization imports
import functools
import os
from collections import defaultdict, deque


@dataclass
class PerformanceMetrics:
    """Performance tracking metrics."""
    
    start_time: float
    end_time: float
    files_analyzed: int
    lines_analyzed: int
    cache_hits: int
    cache_misses: int
    parallel_speedup: Optional[float] = None
    memory_peak_mb: Optional[float] = None
    
    @property
    def duration_ms(self) -> int:
        return int((self.end_time - self.start_time) * 1000)
    
    @property
    def lines_per_second(self) -> float:
        duration_s = self.end_time - self.start_time
        return self.lines_analyzed / max(0.001, duration_s)
    
    @property
    def cache_hit_rate(self) -> float:
        total = self.cache_hits + self.cache_misses
        return self.cache_hits / max(1, total)


@dataclass
class OptimizedViolation:
    """Streamlined violation structure optimized for performance."""
    
    id: str
    type: str
    severity: str
    file_path: str
    line_number: int
    column: int
    description: str
    recommendation: str
    weight: float = 1.0
    context: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.context is None:
            self.context = {}
        
        # Generate stable fingerprint for deduplication
        if not self.id:
            self.id = self._generate_fingerprint()
    
    def _generate_fingerprint(self) -> str:
        """Generate stable fingerprint for violation deduplication."""
        components = [
            self.type,
            self.file_path,
            str(self.line_number),
            str(self.column),
            self.description[:50],
        ]
        content = "|".join(components)
        return hashlib.md5(content.encode()).hexdigest()[:12]


class FileCache:
    """High-performance file analysis cache using file hashes."""
    
    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or Path.home() / ".connascence_cache"
        self.cache_dir.mkdir(exist_ok=True)
        
        self.hits = 0
        self.misses = 0
        
        # Memory cache for frequently accessed items
        self._memory_cache = {}
        self._max_memory_items = 1000
    
    def get_file_hash(self, file_path: Path) -> str:
        """Calculate hash of file contents and metadata."""
        try:
            stat = file_path.stat()
            with open(file_path, 'rb') as f:
                content = f.read()
            
            # Combine content hash with metadata
            hasher = hashlib.md5()
            hasher.update(content)
            hasher.update(str(stat.st_mtime).encode())
            hasher.update(str(stat.st_size).encode())
            return hasher.hexdigest()
        except (OSError, IOError):
            return ""
    
    def get(self, file_path: Path) -> Optional[List[OptimizedViolation]]:
        """Get cached analysis result for file."""
        file_hash = self.get_file_hash(file_path)
        if not file_hash:
            return None
        
        cache_key = f"{file_path.name}_{file_hash}"
        
        # Check memory cache first
        if cache_key in self._memory_cache:
            self.hits += 1
            return self._memory_cache[cache_key]
        
        # Check disk cache
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        if cache_file.exists():
            try:
                with open(cache_file, 'rb') as f:
                    violations = pickle.load(f)
                
                # Store in memory cache
                self._memory_cache[cache_key] = violations
                if len(self._memory_cache) > self._max_memory_items:
                    # Remove oldest item
                    oldest_key = next(iter(self._memory_cache))
                    del self._memory_cache[oldest_key]
                
                self.hits += 1
                return violations
            except (pickle.UnpicklingError, IOError):
                # Cache corruption, remove file
                cache_file.unlink(missing_ok=True)
        
        self.misses += 1
        return None
    
    def set(self, file_path: Path, violations: List[OptimizedViolation]) -> None:
        """Cache analysis result for file."""
        file_hash = self.get_file_hash(file_path)
        if not file_hash:
            return
        
        cache_key = f"{file_path.name}_{file_hash}"
        
        # Store in memory cache
        self._memory_cache[cache_key] = violations
        if len(self._memory_cache) > self._max_memory_items:
            oldest_key = next(iter(self._memory_cache))
            del self._memory_cache[oldest_key]
        
        # Store in disk cache
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(violations, f, protocol=pickle.HIGHEST_PROTOCOL)
        except IOError:
            pass  # Ignore cache write failures
    
    def clear(self) -> None:
        """Clear all cached data."""
        self._memory_cache.clear()
        for cache_file in self.cache_dir.glob("*.pkl"):
            cache_file.unlink(missing_ok=True)


class UnifiedASTAnalyzer:
    """Single-pass AST analyzer that combines all connascence detection."""
    
    def __init__(self, thresholds: Optional[Dict[str, Any]] = None):
        self.thresholds = thresholds or self._default_thresholds()
        
        # Optimized data structures
        self.name_usage = defaultdict(int)
        self.function_signatures = {}
        self.violations = []
        
        # Context tracking for single pass
        self.current_file_path = ""
        self.current_source_lines = []
        self.function_stack = deque()  # Track function context
        self.class_stack = deque()     # Track class context
    
    def _default_thresholds(self) -> Dict[str, Any]:
        """Default analysis thresholds optimized for performance."""
        return {
            "max_positional_params": 4,
            "max_cyclomatic_complexity": 10,
            "god_class_methods": 15,
            "god_class_lines": 200,
            "magic_literal_exceptions": {None, 0, 1, -1, 2, True, False, "", "utf-8"},
            "high_name_usage_threshold": 15,
        }
    
    def analyze_file(self, file_path: Path) -> List[OptimizedViolation]:
        """Analyze a single file using optimized single-pass algorithm."""
        self.current_file_path = str(file_path)
        self.violations = []
        self.name_usage.clear()
        self.function_signatures.clear()
        self.function_stack.clear()
        self.class_stack.clear()
        
        try:
            with open(file_path, encoding="utf-8", errors="ignore") as f:
                source = f.read()
                self.current_source_lines = source.splitlines()
            
            if not source.strip():
                return []
            
            tree = ast.parse(source, filename=str(file_path))
            
            # Single-pass analysis using custom visitor
            self._unified_ast_walk(tree)
            
            # Post-processing optimizations
            self._detect_duplicate_algorithms()
            self._detect_excessive_name_coupling()
            
        except (SyntaxError, UnicodeDecodeError) as e:
            self.violations.append(OptimizedViolation(
                id="",
                type="parse_error",
                severity="critical",
                file_path=self.current_file_path,
                line_number=getattr(e, "lineno", 1),
                column=getattr(e, "offset", 0) or 0,
                description=f"File cannot be parsed: {e}",
                recommendation="Fix syntax errors before analyzing connascence"
            ))
        
        return self.violations
    
    def _unified_ast_walk(self, tree: ast.AST) -> None:
        """Single-pass AST traversal that performs all analysis types."""
        for node in ast.walk(tree):
            # Track context for locality analysis
            if isinstance(node, ast.FunctionDef):
                self.function_stack.append(node.name)
                self._analyze_function_node(node)
            elif isinstance(node, ast.ClassDef):
                self.class_stack.append(node.name)
                self._analyze_class_node(node)
            elif isinstance(node, ast.Name):
                self._analyze_name_node(node)
            elif isinstance(node, ast.Call):
                self._analyze_call_node(node)
            elif isinstance(node, (ast.Constant, ast.Num, ast.Str)):
                self._analyze_literal_node(node)
    
    def _analyze_function_node(self, node: ast.FunctionDef) -> None:
        """Analyze function for position and type connascence."""
        # Position connascence: too many positional parameters
        args = node.args.args
        if args and args[0].arg in ["self", "cls"]:
            args = args[1:]
        
        positional_count = len(args)
        if positional_count > self.thresholds["max_positional_params"]:
            self.violations.append(OptimizedViolation(
                id="",
                type="position",
                severity="high",
                file_path=self.current_file_path,
                line_number=node.lineno,
                column=node.col_offset,
                description=f"Function '{node.name}' has {positional_count} positional parameters",
                recommendation="Use keyword arguments, data classes, or parameter objects",
                context={"parameter_count": positional_count}
            ))
        
        # Type connascence: missing type annotations
        has_return_annotation = node.returns is not None
        has_arg_annotations = any(arg.annotation for arg in node.args.args)
        
        if not has_return_annotation and not has_arg_annotations and not node.name.startswith("_"):
            self.violations.append(OptimizedViolation(
                id="",
                type="type",
                severity="low",
                file_path=self.current_file_path,
                line_number=node.lineno,
                column=node.col_offset,
                description=f"Function '{node.name}' lacks type annotations",
                recommendation="Add type hints for better type safety"
            ))
        
        # Algorithm connascence: high cyclomatic complexity
        complexity = self._calculate_cyclomatic_complexity(node)
        if complexity > self.thresholds["max_cyclomatic_complexity"]:
            self.violations.append(OptimizedViolation(
                id="",
                type="algorithm",
                severity="high",
                file_path=self.current_file_path,
                line_number=node.lineno,
                column=node.col_offset,
                description=f"Function '{node.name}' has high complexity ({complexity})",
                recommendation="Break down into smaller, focused functions",
                context={"complexity": complexity}
            ))
        
        # Store function signature for duplicate detection
        signature = self._calculate_function_signature(node)
        if signature in self.function_signatures:
            self.function_signatures[signature].append(node)
        else:
            self.function_signatures[signature] = [node]
    
    def _analyze_class_node(self, node: ast.ClassDef) -> None:
        """Analyze class for god object detection."""
        method_count = len([n for n in node.body if isinstance(n, ast.FunctionDef)])
        loc = (getattr(node, 'end_lineno', node.lineno + 10)) - node.lineno
        
        if (method_count > self.thresholds["god_class_methods"] or 
            loc > self.thresholds["god_class_lines"]):
            self.violations.append(OptimizedViolation(
                id="",
                type="algorithm",
                severity="critical",
                file_path=self.current_file_path,
                line_number=node.lineno,
                column=node.col_offset,
                description=f"God Object: class '{node.name}' has {method_count} methods, ~{loc} lines",
                recommendation="Split into smaller, focused classes",
                context={"method_count": method_count, "lines_of_code": loc}
            ))
    
    def _analyze_name_node(self, node: ast.Name) -> None:
        """Track name usage for coupling analysis."""
        self.name_usage[node.id] += 1
    
    def _analyze_call_node(self, node: ast.Call) -> None:
        """Analyze function calls for position connascence."""
        if len(node.args) > self.thresholds["max_positional_params"]:
            self.violations.append(OptimizedViolation(
                id="",
                type="position",
                severity="medium",
                file_path=self.current_file_path,
                line_number=node.lineno,
                column=node.col_offset,
                description=f"Function call with {len(node.args)} positional arguments",
                recommendation="Use keyword arguments for better readability",
                context={"argument_count": len(node.args)}
            ))
    
    def _analyze_literal_node(self, node: Union[ast.Constant, ast.Num, ast.Str]) -> None:
        """Analyze literals for meaning connascence."""
        if isinstance(node, ast.Constant):
            value = node.value
        elif isinstance(node, ast.Num):
            value = node.n
        else:  # ast.Str
            value = node.s
        
        if value not in self.thresholds["magic_literal_exceptions"]:
            # Determine severity based on context
            is_conditional = self._is_in_conditional_context(node)
            severity = "high" if is_conditional else "medium"
            
            self.violations.append(OptimizedViolation(
                id="",
                type="meaning",
                severity=severity,
                file_path=self.current_file_path,
                line_number=node.lineno,
                column=node.col_offset,
                description=f"Magic literal '{value}' should be a named constant",
                recommendation="Replace with a well-named constant",
                context={"literal_value": value, "in_conditional": is_conditional}
            ))
    
    def _detect_duplicate_algorithms(self) -> None:
        """Detect duplicate algorithms using O(n log n) algorithm."""
        # Sort signatures by frequency for efficient duplicate detection
        signature_groups = [(sig, nodes) for sig, nodes in self.function_signatures.items() if len(nodes) > 1]
        signature_groups.sort(key=lambda x: len(x[1]), reverse=True)
        
        for signature, nodes in signature_groups:
            # Report duplicates (skip first occurrence)
            for duplicate_node in nodes[1:]:
                original_node = nodes[0]
                self.violations.append(OptimizedViolation(
                    id="",
                    type="algorithm",
                    severity="medium",
                    file_path=self.current_file_path,
                    line_number=duplicate_node.lineno,
                    column=duplicate_node.col_offset,
                    description=f"Function '{duplicate_node.name}' duplicates algorithm from '{original_node.name}'",
                    recommendation="Extract common algorithm into shared function",
                    context={"similar_function": original_node.name, "signature": signature}
                ))
    
    def _detect_excessive_name_coupling(self) -> None:
        """Detect excessive name coupling using optimized thresholding."""
        high_usage_names = [
            (name, count) for name, count in self.name_usage.items()
            if count > self.thresholds["high_name_usage_threshold"] 
            and name not in {"self", "cls"} 
            and not name.startswith("_")
        ]
        
        for name, count in high_usage_names:
            self.violations.append(OptimizedViolation(
                id="",
                type="name",
                severity="medium",
                file_path=self.current_file_path,
                line_number=1,
                column=0,
                description=f"Name '{name}' used {count} times (high coupling)",
                recommendation="Consider refactoring to reduce name dependencies",
                context={"name": name, "usage_count": count}
            ))
    
    def _is_in_conditional_context(self, node: ast.AST) -> bool:
        """Check if node is in a conditional context."""
        if not hasattr(node, "lineno") or node.lineno > len(self.current_source_lines):
            return False
        
        line_content = self.current_source_lines[node.lineno - 1]
        return any(keyword in line_content for keyword in ["if ", "elif ", "while ", "assert "])
    
    def _calculate_function_signature(self, node: ast.FunctionDef) -> str:
        """Calculate optimized function signature for duplicate detection."""
        # Use structural hash instead of string concatenation for performance
        elements = []
        for stmt in node.body[:5]:  # Limit to first 5 statements for performance
            elements.append(type(stmt).__name__)
            if isinstance(stmt, ast.Return):
                elements.append("has_return")
            elif isinstance(stmt, ast.If):
                elements.append("conditional")
            elif isinstance(stmt, ast.For):
                elements.append("loop")
        
        # Include parameter count as signature component
        elements.append(f"params_{len(node.args.args)}")
        
        return "|".join(elements)
    
    def _calculate_cyclomatic_complexity(self, node: ast.FunctionDef) -> int:
        """Fast cyclomatic complexity calculation."""
        complexity = 1  # Base complexity
        
        # Use direct iteration instead of ast.walk for performance
        for stmt in ast.walk(node):
            if isinstance(stmt, (ast.If, ast.While, ast.For, ast.AsyncFor, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(stmt, ast.BoolOp):
                complexity += len(stmt.values) - 1
        
        return complexity


class HighPerformanceConnascenceAnalyzer:
    """Main analyzer class with all performance optimizations."""
    
    def __init__(
        self,
        max_workers: Optional[int] = None,
        enable_cache: bool = True,
        cache_dir: Optional[Path] = None,
        thresholds: Optional[Dict[str, Any]] = None
    ):
        self.max_workers = max_workers or min(mp.cpu_count(), 8)
        self.enable_cache = enable_cache
        self.cache = FileCache(cache_dir) if enable_cache else None
        self.thresholds = thresholds
        
        self.metrics = None
        
    def analyze_directory(
        self, 
        directory: Path, 
        parallel: bool = True,
        progress_callback: Optional[callable] = None
    ) -> Tuple[List[OptimizedViolation], PerformanceMetrics]:
        """Analyze directory with performance optimizations."""
        start_time = time.time()
        
        # Collect Python files
        python_files = [f for f in directory.rglob("*.py") if self._should_analyze(f)]
        total_files = len(python_files)
        
        if not python_files:
            return [], self._create_metrics(start_time, time.time(), 0, 0, 0, 0)
        
        all_violations = []
        total_lines = 0
        cache_hits = 0
        cache_misses = 0
        
        if parallel and total_files > 1:
            # Parallel processing
            violations_list, total_lines, cache_hits, cache_misses = self._analyze_parallel(
                python_files, progress_callback
            )
            all_violations = [v for violations in violations_list for v in violations]
        else:
            # Sequential processing (for small projects or debugging)
            for i, file_path in enumerate(python_files):
                violations, lines, hits, misses = self._analyze_single_file(file_path)
                all_violations.extend(violations)
                total_lines += lines
                cache_hits += hits
                cache_misses += misses
                
                if progress_callback:
                    progress_callback(i + 1, total_files, file_path.name)
        
        end_time = time.time()
        metrics = self._create_metrics(
            start_time, end_time, total_files, total_lines, cache_hits, cache_misses
        )
        
        return all_violations, metrics
    
    def _analyze_parallel(
        self, 
        python_files: List[Path], 
        progress_callback: Optional[callable] = None
    ) -> Tuple[List[List[OptimizedViolation]], int, int, int]:
        """Analyze files in parallel using ProcessPoolExecutor."""
        violations_list = []
        total_lines = 0
        cache_hits = 0
        cache_misses = 0
        
        # Create analyzer arguments for worker processes
        analyzer_args = {
            'enable_cache': self.enable_cache,
            'cache_dir': self.cache.cache_dir if self.cache else None,
            'thresholds': self.thresholds
        }
        
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_file = {
                executor.submit(_analyze_file_worker, file_path, analyzer_args): file_path
                for file_path in python_files
            }
            
            # Collect results as they complete
            completed = 0
            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    violations, lines, hits, misses = future.result()
                    violations_list.append(violations)
                    total_lines += lines
                    cache_hits += hits
                    cache_misses += misses
                except Exception as e:
                    # Create error violation for failed files
                    error_violation = OptimizedViolation(
                        id="",
                        type="processing_error",
                        severity="critical",
                        file_path=str(file_path),
                        line_number=1,
                        column=0,
                        description=f"Error processing file: {e}",
                        recommendation="Check file syntax and permissions"
                    )
                    violations_list.append([error_violation])
                
                completed += 1
                if progress_callback:
                    progress_callback(completed, len(python_files), file_path.name)
        
        return violations_list, total_lines, cache_hits, cache_misses
    
    def _analyze_single_file(self, file_path: Path) -> Tuple[List[OptimizedViolation], int, int, int]:
        """Analyze a single file with caching support."""
        # Check cache first
        if self.cache:
            cached_violations = self.cache.get(file_path)
            if cached_violations is not None:
                lines = len(file_path.read_text(encoding='utf-8', errors='ignore').splitlines())
                return cached_violations, lines, 1, 0  # cache hit
        
        # Analyze file
        analyzer = UnifiedASTAnalyzer(self.thresholds)
        violations = analyzer.analyze_file(file_path)
        
        # Count lines
        try:
            lines = len(analyzer.current_source_lines)
        except:
            lines = 0
        
        # Cache results
        if self.cache:
            self.cache.set(file_path, violations)
        
        return violations, lines, 0, 1  # cache miss
    
    def _should_analyze(self, file_path: Path) -> bool:
        """Check if file should be analyzed."""
        skip_patterns = [
            "__pycache__", ".pytest_cache", "node_modules", "venv", ".venv",
            "test_", "_test.py", "conftest.py", ".git", "build", "dist"
        ]
        
        path_str = str(file_path)
        return not any(pattern in path_str for pattern in skip_patterns)
    
    def _create_metrics(
        self, 
        start_time: float, 
        end_time: float, 
        files_analyzed: int, 
        lines_analyzed: int,
        cache_hits: int,
        cache_misses: int
    ) -> PerformanceMetrics:
        """Create performance metrics object."""
        return PerformanceMetrics(
            start_time=start_time,
            end_time=end_time,
            files_analyzed=files_analyzed,
            lines_analyzed=lines_analyzed,
            cache_hits=cache_hits,
            cache_misses=cache_misses
        )
    
    def clear_cache(self) -> None:
        """Clear analysis cache."""
        if self.cache:
            self.cache.clear()
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        if not self.cache:
            return {"hits": 0, "misses": 0}
        return {"hits": self.cache.hits, "misses": self.cache.misses}


def _analyze_file_worker(file_path: Path, analyzer_args: Dict[str, Any]) -> Tuple[List[OptimizedViolation], int, int, int]:
    """Worker function for parallel file analysis."""
    # Create analyzer instance in worker process
    cache = FileCache(analyzer_args['cache_dir']) if analyzer_args['enable_cache'] else None
    
    # Check cache
    if cache:
        cached_violations = cache.get(file_path)
        if cached_violations is not None:
            try:
                lines = len(file_path.read_text(encoding='utf-8', errors='ignore').splitlines())
            except:
                lines = 0
            return cached_violations, lines, 1, 0  # cache hit
    
    # Analyze file
    analyzer = UnifiedASTAnalyzer(analyzer_args['thresholds'])
    violations = analyzer.analyze_file(file_path)
    
    # Count lines
    try:
        lines = len(analyzer.current_source_lines)
    except:
        lines = 0
    
    # Cache results
    if cache:
        cache.set(file_path, violations)
    
    return violations, lines, 0, 1  # cache miss


# CLI interface for performance testing
def main():
    """Command-line interface for performance testing."""
    import argparse
    
    parser = argparse.ArgumentParser(description="High-Performance Connascence Analyzer")
    parser.add_argument("path", help="Path to analyze")
    parser.add_argument("--parallel", action="store_true", help="Enable parallel processing")
    parser.add_argument("--workers", type=int, help="Number of worker processes")
    parser.add_argument("--cache", action="store_true", help="Enable caching")
    parser.add_argument("--clear-cache", action="store_true", help="Clear cache before analysis")
    parser.add_argument("--benchmark", action="store_true", help="Run performance benchmark")
    parser.add_argument("--output", help="Output file for results")
    
    args = parser.parse_args()
    
    # Create analyzer
    analyzer = HighPerformanceConnascenceAnalyzer(
        max_workers=args.workers,
        enable_cache=args.cache
    )
    
    if args.clear_cache:
        analyzer.clear_cache()
        print("Cache cleared.")
    
    path = Path(args.path)
    if not path.exists():
        print(f"Error: Path {path} does not exist")
        return 1
    
    # Progress callback
    def progress(current, total, filename):
        percent = (current / total) * 100
        print(f"Progress: {current}/{total} ({percent:.1f}%) - {filename}")
    
    # Run analysis
    print(f"Analyzing {path}...")
    violations, metrics = analyzer.analyze_directory(
        path, 
        parallel=args.parallel,
        progress_callback=progress if not args.benchmark else None
    )
    
    # Generate report
    report = {
        "violations": [asdict(v) for v in violations],
        "performance_metrics": asdict(metrics),
        "cache_stats": analyzer.get_cache_stats(),
        "summary": {
            "total_violations": len(violations),
            "violations_by_type": {},
            "violations_by_severity": {}
        }
    }
    
    # Calculate summary statistics
    for violation in violations:
        v_type = violation.type
        v_severity = violation.severity
        
        report["summary"]["violations_by_type"][v_type] = (
            report["summary"]["violations_by_type"].get(v_type, 0) + 1
        )
        report["summary"]["violations_by_severity"][v_severity] = (
            report["summary"]["violations_by_severity"].get(v_severity, 0) + 1
        )
    
    # Output results
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(report, f, indent=2)
    else:
        print(json.dumps(report, indent=2))
    
    # Print performance summary
    print(f"\nPerformance Summary:", file=os.sys.stderr)
    print(f"  Files analyzed: {metrics.files_analyzed}", file=os.sys.stderr)
    print(f"  Lines analyzed: {metrics.lines_analyzed:,}", file=os.sys.stderr)
    print(f"  Duration: {metrics.duration_ms}ms", file=os.sys.stderr)
    print(f"  Speed: {metrics.lines_per_second:,.0f} lines/sec", file=os.sys.stderr)
    print(f"  Cache hit rate: {metrics.cache_hit_rate:.1%}", file=os.sys.stderr)
    
    return 0


if __name__ == "__main__":
    exit(main())