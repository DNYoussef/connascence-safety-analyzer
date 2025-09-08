"""
Incremental Delta-Based Caching System
======================================

Intelligent caching system for incremental analysis that tracks file changes,
dependencies, and partial analysis results. Integrates with existing file_cache
system while providing delta-based optimization for streaming workflows.

Features:
- Delta-based caching for changed files only
- Dependency graph tracking for cascading updates
- Efficient partial result storage and retrieval
- Cache invalidation based on file dependencies
- Integration with existing FileContentCache system
"""

import hashlib
import time
import threading
from collections import defaultdict, deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union
import logging

# Import existing cache system for integration
try:
    from ..optimization.file_cache import FileContentCache, get_global_cache
    CACHE_INTEGRATION_AVAILABLE = True
except ImportError:
    FileContentCache = None
    get_global_cache = None
    CACHE_INTEGRATION_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class FileDelta:
    """Represents changes to a file since last analysis."""
    file_path: Path
    old_hash: Optional[str]
    new_hash: str
    change_type: str  # 'created', 'modified', 'deleted'
    timestamp: float
    old_size: int = 0
    new_size: int = 0
    lines_added: int = 0
    lines_removed: int = 0
    lines_modified: int = 0
    
    def __post_init__(self):
        """Validate delta data."""
        assert self.change_type in ['created', 'modified', 'deleted'], \
            f"Invalid change_type: {self.change_type}"
        assert self.new_size >= 0, "new_size cannot be negative"
        assert self.old_size >= 0, "old_size cannot be negative"


@dataclass 
class DependencyNode:
    """Represents a file and its dependencies."""
    file_path: str
    content_hash: str
    last_analyzed: float
    dependencies: Set[str] = field(default_factory=set)  # Files this file imports/depends on
    dependents: Set[str] = field(default_factory=set)   # Files that depend on this file
    analysis_results: Optional[Dict[str, Any]] = None
    
    def is_stale(self, file_hashes: Dict[str, str]) -> bool:
        """Check if this node needs reanalysis based on dependency changes."""
        # Check if any dependencies have changed
        for dep_path in self.dependencies:
            if dep_path in file_hashes:
                current_hash = file_hashes[dep_path]
                # This would need to track dependency hashes - simplified for now
                pass
        return False


@dataclass
class PartialResult:
    """Stores partial analysis results that can be incrementally updated."""
    file_path: str
    result_type: str  # 'violations', 'metrics', 'ast_data'
    data: Any
    content_hash: str
    created_at: float
    dependencies: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_valid_for_hash(self, current_hash: str) -> bool:
        """Check if this result is valid for the current file hash."""
        return self.content_hash == current_hash


class IncrementalCache:
    """
    Delta-based caching system for incremental analysis.
    
    Integrates with existing FileContentCache while providing specialized
    capabilities for streaming and incremental analysis workflows.
    """
    
    def __init__(self, 
                 max_partial_results: int = 5000,
                 max_dependency_nodes: int = 10000,
                 cache_retention_hours: float = 24.0):
        """
        Initialize incremental cache.
        
        Args:
            max_partial_results: Maximum partial results to cache
            max_dependency_nodes: Maximum dependency nodes to track
            cache_retention_hours: Hours to retain cached results
        """
        assert 100 <= max_partial_results <= 100000, "max_partial_results must be 100-100000"
        assert 100 <= max_dependency_nodes <= 100000, "max_dependency_nodes must be 100-100000"
        assert 0.1 <= cache_retention_hours <= 168.0, "cache_retention_hours must be 0.1-168"
        
        self.max_partial_results = max_partial_results
        self.max_dependency_nodes = max_dependency_nodes
        self.cache_retention_seconds = cache_retention_hours * 3600
        
        # Partial results cache
        self._partial_results: Dict[str, PartialResult] = {}
        self._results_by_file: Dict[str, Set[str]] = defaultdict(set)
        
        # Dependency tracking
        self._dependency_graph: Dict[str, DependencyNode] = {}
        self._file_hashes: Dict[str, str] = {}
        self._hash_to_files: Dict[str, Set[str]] = defaultdict(set)
        
        # Delta tracking
        self._recent_deltas: deque = deque(maxlen=1000)  # NASA Rule 7: bounded
        self._invalidation_queue: deque = deque(maxlen=10000)
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Integration with existing cache system
        self.file_cache: Optional[FileContentCache] = None
        if CACHE_INTEGRATION_AVAILABLE:
            self.file_cache = get_global_cache()
        
        # Performance metrics
        self._metrics = {
            "cache_hits": 0,
            "cache_misses": 0,
            "delta_updates": 0,
            "dependency_invalidations": 0,
            "partial_result_reuse": 0
        }
    
    def track_file_change(self, file_path: Union[str, Path], 
                         old_content: Optional[str] = None,
                         new_content: Optional[str] = None) -> FileDelta:
        """
        Track file change and create delta.
        
        Args:
            file_path: Path to changed file
            old_content: Previous file content (if available)
            new_content: New file content (if available)
            
        Returns:
            FileDelta representing the change
        """
        file_path_str = str(file_path)
        current_time = time.time()
        
        with self._lock:
            # Calculate hashes
            old_hash = self._file_hashes.get(file_path_str)
            new_hash = None
            new_size = 0
            
            if new_content is not None:
                new_hash = hashlib.sha256(new_content.encode('utf-8')).hexdigest()[:16]
                new_size = len(new_content)
            elif Path(file_path).exists():
                # Read file if content not provided
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        new_content = f.read()
                        new_hash = hashlib.sha256(new_content.encode('utf-8')).hexdigest()[:16]
                        new_size = len(new_content)
                except Exception as e:
                    logger.warning(f"Failed to read {file_path}: {e}")
                    new_hash = "error"
            
            # Determine change type
            if old_hash is None and new_hash:
                change_type = 'created'
            elif old_hash and new_hash is None:
                change_type = 'deleted'
            elif old_hash != new_hash:
                change_type = 'modified'
            else:
                change_type = 'unchanged'
                
            if change_type == 'unchanged':
                # No actual change
                return None
            
            # Calculate line differences (simplified)
            lines_added = lines_removed = lines_modified = 0
            if old_content and new_content:
                old_lines = set(old_content.splitlines())
                new_lines = set(new_content.splitlines())
                lines_added = len(new_lines - old_lines)
                lines_removed = len(old_lines - new_lines)
                lines_modified = min(lines_added, lines_removed)
            
            # Create delta
            delta = FileDelta(
                file_path=Path(file_path),
                old_hash=old_hash,
                new_hash=new_hash,
                change_type=change_type,
                timestamp=current_time,
                old_size=len(old_content) if old_content else 0,
                new_size=new_size,
                lines_added=lines_added,
                lines_removed=lines_removed,
                lines_modified=lines_modified
            )
            
            # Update tracking
            if new_hash:
                self._file_hashes[file_path_str] = new_hash
                self._hash_to_files[new_hash].add(file_path_str)
            
            # Remove old hash tracking
            if old_hash:
                old_files = self._hash_to_files.get(old_hash, set())
                old_files.discard(file_path_str)
                if not old_files:
                    self._hash_to_files.pop(old_hash, None)
            
            # Add to recent deltas
            self._recent_deltas.append(delta)
            
            # Invalidate dependent results
            self._invalidate_dependent_results(file_path_str, delta)
            
            self._metrics["delta_updates"] += 1
            
            return delta
    
    def get_partial_result(self, 
                          file_path: Union[str, Path],
                          result_type: str,
                          current_hash: Optional[str] = None) -> Optional[PartialResult]:
        """
        Get cached partial result for file.
        
        Args:
            file_path: Path to file
            result_type: Type of result ('violations', 'metrics', 'ast_data')
            current_hash: Current content hash for validation
            
        Returns:
            Cached partial result if valid, None otherwise
        """
        file_path_str = str(file_path)
        result_key = f"{file_path_str}:{result_type}"
        
        with self._lock:
            result = self._partial_results.get(result_key)
            if not result:
                self._metrics["cache_misses"] += 1
                return None
            
            # Validate result freshness
            current_time = time.time()
            if current_time - result.created_at > self.cache_retention_seconds:
                # Result too old
                self._remove_partial_result(result_key)
                self._metrics["cache_misses"] += 1
                return None
            
            # Validate content hash if provided
            if current_hash and not result.is_valid_for_hash(current_hash):
                self._remove_partial_result(result_key)
                self._metrics["cache_misses"] += 1
                return None
            
            self._metrics["cache_hits"] += 1
            self._metrics["partial_result_reuse"] += 1
            return result
    
    def store_partial_result(self,
                           file_path: Union[str, Path],
                           result_type: str,
                           data: Any,
                           content_hash: str,
                           dependencies: Optional[Set[str]] = None,
                           metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Store partial analysis result.
        
        Args:
            file_path: Path to analyzed file
            result_type: Type of result
            data: Analysis result data
            content_hash: Hash of analyzed content
            dependencies: Files this result depends on
            metadata: Additional metadata
        """
        file_path_str = str(file_path)
        result_key = f"{file_path_str}:{result_type}"
        
        with self._lock:
            # Enforce cache size limits (NASA Rule 7)
            if len(self._partial_results) >= self.max_partial_results:
                self._evict_old_partial_results()
            
            # Create partial result
            partial_result = PartialResult(
                file_path=file_path_str,
                result_type=result_type,
                data=data,
                content_hash=content_hash,
                created_at=time.time(),
                dependencies=dependencies or set(),
                metadata=metadata or {}
            )
            
            # Store result
            self._partial_results[result_key] = partial_result
            self._results_by_file[file_path_str].add(result_key)
            
            # Update dependency tracking
            self._update_dependency_tracking(file_path_str, dependencies or set())
    
    def _update_dependency_tracking(self, file_path: str, dependencies: Set[str]) -> None:
        """Update dependency graph for file."""
        if file_path not in self._dependency_graph:
            self._dependency_graph[file_path] = DependencyNode(
                file_path=file_path,
                content_hash=self._file_hashes.get(file_path, ""),
                last_analyzed=time.time()
            )
        
        node = self._dependency_graph[file_path]
        
        # Update dependencies
        old_dependencies = node.dependencies.copy()
        node.dependencies = dependencies.copy()
        node.last_analyzed = time.time()
        
        # Update reverse dependencies
        for dep_path in dependencies - old_dependencies:
            if dep_path not in self._dependency_graph:
                self._dependency_graph[dep_path] = DependencyNode(
                    file_path=dep_path,
                    content_hash=self._file_hashes.get(dep_path, ""),
                    last_analyzed=0
                )
            self._dependency_graph[dep_path].dependents.add(file_path)
        
        for dep_path in old_dependencies - dependencies:
            if dep_path in self._dependency_graph:
                self._dependency_graph[dep_path].dependents.discard(file_path)
    
    def _invalidate_dependent_results(self, changed_file: str, delta: FileDelta) -> None:
        """Invalidate results that depend on changed file."""
        if changed_file not in self._dependency_graph:
            return
        
        node = self._dependency_graph[changed_file]
        invalidated_files = set()
        
        # Find all files that depend on the changed file
        to_invalidate = deque([changed_file])
        while to_invalidate:
            current_file = to_invalidate.popleft()
            if current_file in invalidated_files:
                continue
                
            invalidated_files.add(current_file)
            
            # Add dependents
            if current_file in self._dependency_graph:
                for dependent in self._dependency_graph[current_file].dependents:
                    if dependent not in invalidated_files:
                        to_invalidate.append(dependent)
        
        # Remove invalidated partial results
        invalidated_count = 0
        for file_path in invalidated_files:
            result_keys = list(self._results_by_file.get(file_path, set()))
            for result_key in result_keys:
                if result_key in self._partial_results:
                    del self._partial_results[result_key]
                    invalidated_count += 1
            self._results_by_file[file_path].clear()
        
        if invalidated_count > 0:
            logger.debug(f"Invalidated {invalidated_count} results due to change in {changed_file}")
            self._metrics["dependency_invalidations"] += invalidated_count
    
    def _remove_partial_result(self, result_key: str) -> None:
        """Remove partial result from cache."""
        result = self._partial_results.pop(result_key, None)
        if result:
            self._results_by_file[result.file_path].discard(result_key)
    
    def _evict_old_partial_results(self) -> None:
        """Evict oldest partial results to maintain cache size."""
        # Sort by creation time and remove oldest
        sorted_results = sorted(
            self._partial_results.items(),
            key=lambda x: x[1].created_at
        )
        
        # Remove oldest 20%
        evict_count = len(sorted_results) // 5
        for result_key, result in sorted_results[:evict_count]:
            self._remove_partial_result(result_key)
    
    def get_files_needing_analysis(self, 
                                  file_paths: List[str],
                                  analysis_type: str = "violations") -> List[str]:
        """
        Get list of files that need analysis based on cache status.
        
        Args:
            file_paths: Files to check
            analysis_type: Type of analysis to check for
            
        Returns:
            List of files needing analysis
        """
        needs_analysis = []
        
        with self._lock:
            for file_path in file_paths:
                current_hash = self._file_hashes.get(file_path)
                cached_result = self.get_partial_result(file_path, analysis_type, current_hash)
                
                if not cached_result:
                    needs_analysis.append(file_path)
        
        return needs_analysis
    
    def get_dependency_chain(self, file_path: str) -> Set[str]:
        """Get all files in the dependency chain for given file."""
        dependencies = set()
        to_process = deque([file_path])
        processed = set()
        
        while to_process:
            current_file = to_process.popleft()
            if current_file in processed:
                continue
                
            processed.add(current_file)
            dependencies.add(current_file)
            
            # Add dependencies of current file
            if current_file in self._dependency_graph:
                node = self._dependency_graph[current_file]
                for dep in node.dependencies:
                    if dep not in processed:
                        to_process.append(dep)
        
        return dependencies - {file_path}  # Exclude the original file
    
    def clear_file_cache(self, file_path: Union[str, Path]) -> int:
        """Clear all cached results for specific file."""
        file_path_str = str(file_path)
        
        with self._lock:
            result_keys = list(self._results_by_file.get(file_path_str, set()))
            cleared_count = 0
            
            for result_key in result_keys:
                if result_key in self._partial_results:
                    del self._partial_results[result_key]
                    cleared_count += 1
            
            self._results_by_file[file_path_str].clear()
            
            # Remove from dependency graph
            if file_path_str in self._dependency_graph:
                node = self._dependency_graph[file_path_str]
                
                # Remove from dependents' dependencies
                for dependent in node.dependents:
                    if dependent in self._dependency_graph:
                        self._dependency_graph[dependent].dependencies.discard(file_path_str)
                
                # Remove from dependencies' dependents
                for dependency in node.dependencies:
                    if dependency in self._dependency_graph:
                        self._dependency_graph[dependency].dependents.discard(file_path_str)
                
                del self._dependency_graph[file_path_str]
            
            # Remove file hash tracking
            old_hash = self._file_hashes.pop(file_path_str, None)
            if old_hash:
                self._hash_to_files[old_hash].discard(file_path_str)
            
            return cleared_count
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        with self._lock:
            total_requests = self._metrics["cache_hits"] + self._metrics["cache_misses"]
            hit_rate = self._metrics["cache_hits"] / total_requests if total_requests > 0 else 0
            
            return {
                "partial_results_cached": len(self._partial_results),
                "files_tracked": len(self._file_hashes),
                "dependency_nodes": len(self._dependency_graph),
                "cache_hit_rate": hit_rate,
                "cache_hits": self._metrics["cache_hits"],
                "cache_misses": self._metrics["cache_misses"],
                "delta_updates": self._metrics["delta_updates"],
                "dependency_invalidations": self._metrics["dependency_invalidations"],
                "partial_result_reuse": self._metrics["partial_result_reuse"],
                "recent_deltas": len(self._recent_deltas),
                "file_cache_integration": CACHE_INTEGRATION_AVAILABLE
            }
    
    def cleanup_expired_results(self) -> int:
        """Clean up expired cache entries."""
        current_time = time.time()
        expired_keys = []
        
        with self._lock:
            for result_key, result in self._partial_results.items():
                if current_time - result.created_at > self.cache_retention_seconds:
                    expired_keys.append(result_key)
            
            for result_key in expired_keys:
                self._remove_partial_result(result_key)
        
        return len(expired_keys)
    
    def integrate_with_file_cache(self, file_cache: FileContentCache) -> None:
        """Integrate with existing FileContentCache system."""
        self.file_cache = file_cache
        logger.info("Integrated incremental cache with existing FileContentCache")


# Global incremental cache instance
_global_incremental_cache: Optional[IncrementalCache] = None
_cache_lock = threading.Lock()


def get_global_incremental_cache() -> IncrementalCache:
    """Get or create global incremental cache instance."""
    global _global_incremental_cache
    
    with _cache_lock:
        if _global_incremental_cache is None:
            _global_incremental_cache = IncrementalCache()
            
            # Integrate with existing file cache if available
            if CACHE_INTEGRATION_AVAILABLE:
                existing_cache = get_global_cache()
                if existing_cache:
                    _global_incremental_cache.integrate_with_file_cache(existing_cache)
    
    return _global_incremental_cache


def clear_incremental_cache() -> None:
    """Clear global incremental cache."""
    global _global_incremental_cache
    
    with _cache_lock:
        if _global_incremental_cache:
            _global_incremental_cache._partial_results.clear()
            _global_incremental_cache._dependency_graph.clear()
            _global_incremental_cache._file_hashes.clear()