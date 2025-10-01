"""
Detector Pool Architecture for Performance Optimization

NASA Rule 7 Compliant: Bounded resource management
Singleton pattern with thread-safe detector reuse
Eliminates object creation overhead (8 objects per file -> 1 pool)
"""

import threading
import time
from typing import Any, Dict, List, Optional

try:
    from ..detectors import (
        AlgorithmDetector,
        ConventionDetector,
        ExecutionDetector,
        GodObjectDetector,
        MagicLiteralDetector,
        PositionDetector,
        TimingDetector,
        ValuesDetector,
    )
    from ..detectors.base import DetectorBase
except ImportError:
    # Fallback for script execution
    from pathlib import Path
    import sys

    sys.path.insert(0, str(Path(__file__).parent.parent))
    from detectors.base import DetectorBase

    from detectors import (
        AlgorithmDetector,
        ConventionDetector,
        ExecutionDetector,
        GodObjectDetector,
        MagicLiteralDetector,
        PositionDetector,
        TimingDetector,
        ValuesDetector,
    )
try:
    from utils.types import ConnascenceViolation
except ImportError:
    from pathlib import Path
    import sys

    sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class PooledDetector:
    """
    Wrapper for pooled detector instances with state management.

    NASA Rule 4: Class under 60 lines per method
    NASA Rule 5: Input validation
    NASA Rule 6: Clear variable scoping
    """

    def __init__(self, detector_instance: DetectorBase, created_at: float):
        assert isinstance(detector_instance, DetectorBase), "detector_instance must be DetectorBase"
        assert isinstance(created_at, (int, float)), "created_at must be numeric"

        self.detector = detector_instance
        self.created_at = created_at
        self.last_used = created_at
        self.use_count = 0
        self.is_in_use = False
        self._lock = threading.Lock()

    def acquire(self, file_path: str, source_lines: List[str]) -> DetectorBase:
        """
        Acquire detector for use with new file context.

        NASA Rule 4: Function under 60 lines
        NASA Rule 5: Input validation
        """
        assert isinstance(file_path, str), "file_path must be string"
        assert isinstance(source_lines, list), "source_lines must be list"

        with self._lock:
            if self.is_in_use:
                return None  # Already in use

            # Reset detector state for new file
            self.detector.file_path = file_path
            self.detector.source_lines = source_lines
            self.detector.violations = []

            self.is_in_use = True
            self.last_used = time.time()
            self.use_count += 1

            return self.detector

    def release(self):
        """Release detector back to pool."""
        with self._lock:
            self.is_in_use = False
            # Clear sensitive data
            self.detector.file_path = ""
            self.detector.source_lines = []
            self.detector.violations = []


class DetectorPool:
    """
    Thread-safe singleton detector pool for performance optimization.

    NASA Rule 7: Bounded resources (max pool size)
    NASA Rule 4: All methods under 60 lines
    NASA Rule 5: Input validation
    NASA Rule 6: Clear variable scoping

    Performance Benefits:
    - Eliminates 8 object creations per file
    - Consistent memory usage patterns
    - Thread-safe parallel processing
    - Detector warmup for consistent performance
    """

    _instance: Optional["DetectorPool"] = None
    _lock = threading.Lock()

    # NASA Rule 7: Bounded resource limits
    MAX_POOL_SIZE = 16  # Maximum detectors per type
    WARMUP_COUNT = 2  # Pre-warmed instances per type
    CLEANUP_INTERVAL = 300  # 5 minutes
    MAX_IDLE_TIME = 600  # 10 minutes

    def __new__(cls):
        """Thread-safe singleton implementation."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        """Initialize pool with bounded resources."""
        if self._initialized:
            return

        self._initialized = True
        self._pools: Dict[str, List[PooledDetector]] = {}
        self._pool_locks: Dict[str, threading.Lock] = {}
        self._metrics = {"total_acquisitions": 0, "cache_hits": 0, "cache_misses": 0, "pool_size": 0}

        # Detector type mapping
        self._detector_types = {
            "position": PositionDetector,
            "magic_literal": MagicLiteralDetector,
            "algorithm": AlgorithmDetector,
            "god_object": GodObjectDetector,
            "timing": TimingDetector,
            "convention": ConventionDetector,
            "values": ValuesDetector,
            "execution": ExecutionDetector,
        }

        # Initialize pools with warmup
        self._initialize_pools()

        # Start cleanup thread
        self._cleanup_thread = threading.Thread(target=self._cleanup_worker, daemon=True)
        self._cleanup_thread.start()

    def _initialize_pools(self):
        """Initialize detector pools with warmup instances."""
        for detector_name in self._detector_types:
            self._pools[detector_name] = []
            self._pool_locks[detector_name] = threading.Lock()

            # Pre-warm instances for consistent performance
            for _ in range(self.WARMUP_COUNT):
                self._create_detector_instance(detector_name)

    def _create_detector_instance(self, detector_name: str) -> Optional[PooledDetector]:
        """
        Create new detector instance with NASA compliance.

        NASA Rule 4: Function under 60 lines
        NASA Rule 5: Input validation
        NASA Rule 7: Bounded resources
        """
        assert detector_name in self._detector_types, f"Unknown detector: {detector_name}"

        # NASA Rule 7: Check pool size limits
        if len(self._pools[detector_name]) >= self.MAX_POOL_SIZE:
            return None

        try:
            detector_class = self._detector_types[detector_name]
            # Create with dummy values - will be reset on acquire
            detector_instance = detector_class("", [])
            pooled_detector = PooledDetector(detector_instance, time.time())

            self._pools[detector_name].append(pooled_detector)
            self._metrics["pool_size"] += 1

            return pooled_detector

        except Exception as e:
            # NASA Rule 5: Error handling
            print(f"Warning: Failed to create {detector_name} detector: {e}")
            return None

    def acquire_detector(self, detector_name: str, file_path: str, source_lines: List[str]) -> Optional[DetectorBase]:
        """
        Acquire detector from pool for analysis.

        NASA Rule 4: Function under 60 lines
        NASA Rule 5: Input validation
        NASA Rule 7: Resource bounds checking
        """
        assert isinstance(detector_name, str), "detector_name must be string"
        assert isinstance(file_path, str), "file_path must be string"
        assert isinstance(source_lines, list), "source_lines must be list"
        assert detector_name in self._detector_types, f"Unknown detector: {detector_name}"

        self._metrics["total_acquisitions"] += 1

        with self._pool_locks[detector_name]:
            # Try to find available detector
            for pooled_detector in self._pools[detector_name]:
                detector = pooled_detector.acquire(file_path, source_lines)
                if detector is not None:
                    self._metrics["cache_hits"] += 1
                    return detector

            # No available detector, try to create new one
            self._metrics["cache_misses"] += 1
            pooled_detector = self._create_detector_instance(detector_name)

            if pooled_detector is not None:
                return pooled_detector.acquire(file_path, source_lines)

            # Pool at capacity, wait briefly and try again
            time.sleep(0.001)  # 1ms backoff
            return None

    def release_detector(self, detector: DetectorBase):
        """
        Release detector back to pool.

        NASA Rule 4: Function under 60 lines
        NASA Rule 5: Input validation
        """
        assert isinstance(detector, DetectorBase), "detector must be DetectorBase"

        # Find the pooled detector by instance
        for detector_name, pool in self._pools.items():
            with self._pool_locks[detector_name]:
                for pooled_detector in pool:
                    if pooled_detector.detector is detector:
                        pooled_detector.release()
                        return

    def acquire_all_detectors(self, file_path: str, source_lines: List[str]) -> Dict[str, DetectorBase]:
        """
        Acquire all detector types for comprehensive analysis.

        NASA Rule 4: Function under 60 lines
        NASA Rule 5: Input validation
        """
        assert isinstance(file_path, str), "file_path must be string"
        assert isinstance(source_lines, list), "source_lines must be list"

        acquired_detectors = {}
        failed_acquisitions = []

        # Acquire all detector types
        for detector_name in self._detector_types:
            detector = self.acquire_detector(detector_name, file_path, source_lines)
            if detector is not None:
                acquired_detectors[detector_name] = detector
            else:
                failed_acquisitions.append(detector_name)

        # If any acquisition failed, release acquired ones and retry
        if failed_acquisitions and len(acquired_detectors) > 0:
            self._handle_partial_acquisition_failure(acquired_detectors, failed_acquisitions)

        return acquired_detectors

    def _handle_partial_acquisition_failure(self, acquired: Dict[str, DetectorBase], failed: List[str]):
        """
        Handle cases where some detectors couldn't be acquired.

        NASA Rule 4: Function under 60 lines
        """
        # Release successfully acquired detectors
        for detector in acquired.values():
            self.release_detector(detector)

        # Log warning about resource pressure
        print(f"Warning: Could not acquire detectors: {failed}. Pool at capacity.")

    def release_all_detectors(self, detectors: Dict[str, DetectorBase]):
        """Release multiple detectors back to pool."""
        for detector in detectors.values():
            self.release_detector(detector)

    def _cleanup_worker(self):
        """Background cleanup of idle detectors."""
        while True:
            time.sleep(self.CLEANUP_INTERVAL)
            self._cleanup_idle_detectors()

    def _cleanup_idle_detectors(self):
        """Remove detectors that have been idle too long."""
        current_time = time.time()

        for detector_name, pool in self._pools.items():
            with self._pool_locks[detector_name]:
                # Keep warmup count but remove excess idle detectors
                to_remove = []
                active_count = sum(1 for pd in pool if pd.is_in_use)
                idle_count = len(pool) - active_count

                if idle_count > self.WARMUP_COUNT:
                    for pooled_detector in pool:
                        if (
                            not pooled_detector.is_in_use
                            and current_time - pooled_detector.last_used > self.MAX_IDLE_TIME
                            and idle_count > self.WARMUP_COUNT
                        ):
                            to_remove.append(pooled_detector)
                            idle_count -= 1

                for pooled_detector in to_remove:
                    pool.remove(pooled_detector)
                    self._metrics["pool_size"] -= 1

    def get_metrics(self) -> Dict[str, Any]:
        """Get pool performance metrics."""
        hit_rate = 0.0
        if self._metrics["total_acquisitions"] > 0:
            hit_rate = self._metrics["cache_hits"] / self._metrics["total_acquisitions"]

        return {
            **self._metrics,
            "hit_rate": hit_rate,
            "pool_sizes": {name: len(pool) for name, pool in self._pools.items()},
        }

    def warmup_pool(self):
        """Pre-warm all detector pools for consistent performance."""
        for detector_name in self._detector_types:
            with self._pool_locks[detector_name]:
                current_size = len(self._pools[detector_name])
                for _ in range(max(0, self.WARMUP_COUNT - current_size)):
                    self._create_detector_instance(detector_name)


# Global pool instance
_global_pool = None


def get_detector_pool() -> DetectorPool:
    """Get the global detector pool instance."""
    global _global_pool
    if _global_pool is None:
        _global_pool = DetectorPool()
    return _global_pool
