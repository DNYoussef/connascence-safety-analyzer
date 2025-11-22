"""
Stream Processing Coordinator for Unified Analyzer
==================================================

High-level streaming analysis coordination component that manages the interaction
between the UnifiedConnascenceAnalyzer and the low-level streaming infrastructure.

This component is part of the architecture layer and provides:
- Streaming analysis lifecycle management
- Hybrid mode coordination (batch + streaming)
- Incremental cache integration
- File change detection and delta analysis
- Batch processing of file changes

NASA Compliance:
- Rule 4: All functions under 60 lines
- Rule 5: Input validation and assertions
- Rule 7: Bounded resource management
"""

import asyncio
import logging
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

logger = logging.getLogger(__name__)

# Import streaming infrastructure components
try:
    from ..streaming.incremental_cache import IncrementalCache, get_global_incremental_cache
    from ..streaming.stream_processor import (
        StreamProcessor as LowLevelStreamProcessor,
    )
    from ..streaming.stream_processor import (
        create_stream_processor,
    )

    STREAMING_AVAILABLE = True
except ImportError:
    STREAMING_AVAILABLE = False
    IncrementalCache = None  # type: ignore
    LowLevelStreamProcessor = None  # type: ignore


class StreamProcessor:
    """
    High-level stream processing coordinator for the Unified Analyzer.

    This component manages streaming analysis workflows, integrating batch
    analysis with real-time incremental updates. It coordinates between
    the main analyzer and the low-level streaming infrastructure.

    Responsibilities:
    - Initialize streaming components
    - Coordinate streaming and batch analysis modes
    - Manage incremental cache lifecycle
    - Handle file change detection and delta analysis
    - Process file changes in batches for efficiency

    NASA Rule 4: Class under 400 LOC total
    NASA Rule 7: Bounded resource management
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the stream processing coordinator.

        Args:
            config: Configuration dictionary with keys:
                - max_queue_size: Maximum size of processing queue
                - max_workers: Maximum number of worker threads
                - cache_size: Size of incremental cache
                - result_callback: Optional callback for results
                - batch_callback: Optional callback for batch completion

        NASA Rule 5: Input validation
        """
        assert config is not None, "config cannot be None"
        assert isinstance(config, dict), "config must be a dictionary"

        self.config = config
        self.stream_processor: Optional[LowLevelStreamProcessor] = None
        self.incremental_cache: Optional[IncrementalCache] = None
        self._is_initialized = False
        self._watched_directories: List[Path] = []

        # Configuration with defaults
        self.max_queue_size = config.get("max_queue_size", 1000)
        self.max_workers = config.get("max_workers", 4)
        self.cache_size = config.get("cache_size", 10000)

        # Ensure a default event loop exists for synchronous helpers that rely
        # on asyncio timing even outside of async test contexts.
        try:
            self._event_loop = asyncio.get_event_loop()
        except RuntimeError:
            self._event_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._event_loop)

        logger.info(
            f"StreamProcessor initialized with queue_size={self.max_queue_size}, "
            f"workers={self.max_workers}, cache_size={self.cache_size}"
        )

    def initialize(self, analyzer_factory: Callable) -> bool:
        """
        Initialize streaming components with analyzer factory.

        Args:
            analyzer_factory: Factory function to create analyzer instances

        Returns:
            True if initialization successful, False otherwise

        NASA Rule 4: Function under 60 lines
        NASA Rule 5: Error handling
        """
        if not STREAMING_AVAILABLE:
            logger.warning("Streaming not available - missing dependencies")
            return False

        if self._is_initialized:
            logger.warning("StreamProcessor already initialized")
            return True

        try:
            # Initialize global incremental cache
            self.incremental_cache = get_global_incremental_cache()
            logger.info("Incremental cache initialized")

            # Configure stream processor
            stream_config = {
                "max_queue_size": self.max_queue_size,
                "max_workers": self.max_workers,
                "cache_size": self.cache_size,
            }

            # Create low-level stream processor
            self.stream_processor = create_stream_processor(analyzer_factory=analyzer_factory, **stream_config)

            # Setup callbacks if provided
            if "result_callback" in self.config:
                self.stream_processor.add_result_callback(self.config["result_callback"])
                logger.debug("Result callback registered")

            if "batch_callback" in self.config:
                self.stream_processor.add_batch_callback(self.config["batch_callback"])
                logger.debug("Batch callback registered")

            self._is_initialized = True
            logger.info("Stream processing components initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize streaming components: {e}")
            self.stream_processor = None
            self.incremental_cache = None
            self._is_initialized = False
            return False

    async def start_streaming(self, directories: List[Union[str, Path]]) -> bool:
        """
        Start streaming analysis for specified directories.

        Args:
            directories: List of directories to watch for changes

        Returns:
            True if streaming started successfully, False otherwise

        NASA Rule 4: Function under 60 lines
        NASA Rule 5: Input validation and error handling
        """
        assert directories is not None, "directories cannot be None"
        assert len(directories) > 0, "directories list cannot be empty"

        if not self._is_initialized or not self.stream_processor:
            logger.error("StreamProcessor not initialized - call initialize() first")
            return False

        try:
            # Convert all paths to Path objects
            path_objects = [Path(d) for d in directories]

            # Validate all paths exist
            for path in path_objects:
                if not path.exists():
                    logger.warning(f"Directory does not exist: {path}")
                    return False

            # Start the low-level stream processor
            await self.stream_processor.start()

            # Register directories for watching
            for directory in path_objects:
                self.stream_processor.start_watching([str(directory)])
                self._watched_directories.append(directory)

            logger.info(f"Streaming started for {len(directories)} directories")
            return True

        except Exception as e:
            logger.error(f"Failed to start streaming: {e}")
            return False

    async def stop_streaming(self) -> bool:
        """
        Stop streaming analysis and cleanup resources.

        Returns:
            True if streaming stopped successfully, False otherwise

        NASA Rule 4: Function under 60 lines
        NASA Rule 7: Resource cleanup
        """
        if not self.stream_processor:
            logger.warning("No active stream processor to stop")
            return True

        try:
            # Stop watching all directories
            self.stream_processor.stop_watching()

            # Stop the stream processor
            await self.stream_processor.stop()

            # Clear watched directories
            self._watched_directories.clear()

            logger.info("Streaming analysis stopped successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to stop streaming: {e}")
            return False

    def detect_changes(self, files: List[Path]) -> List[Path]:
        """
        Detect which files have changed since last analysis.

        Uses incremental cache to identify files that need re-analysis.

        Args:
            files: List of files to check for changes

        Returns:
            List of files that have changed

        NASA Rule 4: Function under 60 lines
        NASA Rule 5: Input validation
        """
        assert files is not None, "files cannot be None"

        if not self.incremental_cache:
            logger.warning("Incremental cache not available - returning all files")
            return files

        changed_files: List[Path] = []

        try:
            for file_path in files:
                # Check if file has been modified
                if self.incremental_cache.is_file_modified(str(file_path)):
                    changed_files.append(file_path)

            logger.debug(f"Detected {len(changed_files)} changed files out of {len(files)}")
            return changed_files

        except Exception as e:
            logger.error(f"Error detecting changes: {e}")
            # Fail safe: return all files if change detection fails
            return files

    def batch_analyze(self, files: List[Path], batch_size: int = 10) -> List[Dict[str, Any]]:
        """
        Analyze files in batches for optimal performance.

        Processes files in smaller batches to provide incremental feedback
        and better resource management.

        Args:
            files: List of files to analyze
            batch_size: Number of files to process in each batch

        Returns:
            List of analysis results for each batch

        NASA Rule 4: Function under 60 lines
        NASA Rule 5: Input validation
        NASA Rule 7: Bounded resource usage
        """
        assert files is not None, "files cannot be None"
        assert batch_size > 0, "batch_size must be positive"

        if not files:
            logger.debug("No files to analyze in batch")
            return []

        results: List[Dict[str, Any]] = []

        try:
            # Process files in batches
            for i in range(0, len(files), batch_size):
                batch = files[i : i + batch_size]
                batch_num = (i // batch_size) + 1
                total_batches = (len(files) + batch_size - 1) // batch_size

                logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} files)")

                # Analyze batch (this would integrate with the main analyzer)
                batch_result = self._analyze_batch(batch)
                results.append(batch_result)

            logger.info(f"Completed batch analysis of {len(files)} files in {len(results)} batches")
            return results

        except Exception as e:
            logger.error(f"Error in batch analysis: {e}")
            return results  # Return partial results

    def _analyze_batch(self, batch: List[Path]) -> Dict[str, Any]:
        """
        Analyze a single batch of files.

        This is a placeholder that would integrate with the main analyzer.

        Args:
            batch: List of files in this batch

        Returns:
            Analysis results for the batch

        NASA Rule 4: Function under 60 lines
        """
        # This would integrate with the actual analyzer
        # For now, return a placeholder result
        return {
            "batch_size": len(batch),
            "files": [str(f) for f in batch],
            "timestamp": self._event_loop.time(),
        }

    def process_stream(self, file_changes: List[Path]) -> Dict[str, Any]:
        """
        Process a stream of file changes incrementally.

        Coordinates incremental analysis of changed files using the
        low-level stream processor and incremental cache.

        Args:
            file_changes: List of files that have changed

        Returns:
            Incremental analysis results

        NASA Rule 4: Function under 60 lines
        NASA Rule 5: Input validation
        """
        assert file_changes is not None, "file_changes cannot be None"

        if not self._is_initialized:
            logger.error("StreamProcessor not initialized")
            return {"error": "StreamProcessor not initialized"}

        try:
            # Detect which files actually changed (using cache)
            changed_files = self.detect_changes(file_changes)

            if not changed_files:
                logger.debug("No actual changes detected")
                return {"status": "no_changes", "files_checked": len(file_changes)}

            # Batch process the changed files
            results = self.batch_analyze(changed_files, batch_size=10)

            return {
                "status": "success",
                "files_changed": len(changed_files),
                "files_checked": len(file_changes),
                "batches_processed": len(results),
                "results": results,
            }

        except Exception as e:
            logger.error(f"Error processing stream: {e}")
            return {"error": str(e)}

    def get_stats(self) -> Dict[str, Any]:
        """
        Get streaming performance statistics.

        Returns:
            Dictionary with streaming statistics

        NASA Rule 4: Function under 60 lines
        """
        stats = {
            "streaming_available": STREAMING_AVAILABLE,
            "initialized": self._is_initialized,
            "watched_directories": len(self._watched_directories),
            "directories": [str(d) for d in self._watched_directories],
        }

        # Add stream processor stats if available
        if self.stream_processor:
            try:
                processor_stats = self.stream_processor.get_stats()
                stats.update(processor_stats)
            except Exception as e:
                logger.debug(f"Could not get stream processor stats: {e}")

        # Add incremental cache stats if available
        if self.incremental_cache:
            try:
                cache_stats = self.incremental_cache.get_cache_stats()
                stats["cache"] = cache_stats
            except Exception as e:
                logger.debug(f"Could not get cache stats: {e}")

        return stats

    @property
    def is_running(self) -> bool:
        """
        Check if streaming is currently active.

        Returns:
            True if streaming is running, False otherwise
        """
        if not self.stream_processor:
            return False

        try:
            status = self.stream_processor.is_running

            # Some test doubles may expose is_running as a property object;
            # evaluate it defensively while handling any errors gracefully.
            if isinstance(status, property):
                status = status.fget(self.stream_processor)

            return bool(status)
        except Exception:
            return False

    def watch_directory(self, directory: Union[str, Path]) -> bool:
        """
        Add a directory to watch for changes.

        Args:
            directory: Directory path to watch

        Returns:
            True if directory added successfully, False otherwise

        NASA Rule 4: Function under 60 lines
        NASA Rule 5: Input validation
        """
        assert directory is not None, "directory cannot be None"

        if not self._is_initialized or not self.stream_processor:
            logger.error("StreamProcessor not initialized")
            return False

        try:
            path = Path(directory)
            if not path.exists():
                logger.error(f"Directory does not exist: {path}")
                return False

            # Add to watched directories
            self.stream_processor.start_watching([str(path)])
            self._watched_directories.append(path)

            logger.info(f"Now watching directory: {path}")
            return True

        except Exception as e:
            logger.error(f"Failed to watch directory {directory}: {e}")
            return False


def create_stream_processor_coordinator(
    config: Optional[Dict[str, Any]] = None, analyzer_factory: Optional[Callable] = None
) -> StreamProcessor:
    """
    Factory function to create a configured StreamProcessor.

    Args:
        config: Configuration dictionary (uses defaults if None)
        analyzer_factory: Optional analyzer factory function

    Returns:
        Configured StreamProcessor instance

    NASA Rule 4: Function under 60 lines
    NASA Rule 5: Input validation
    """
    if config is None:
        config = {
            "max_queue_size": 1000,
            "max_workers": 4,
            "cache_size": 10000,
        }

    processor = StreamProcessor(config)

    # Initialize if analyzer factory provided
    if analyzer_factory is not None:
        success = processor.initialize(analyzer_factory)
        if not success:
            logger.warning("StreamProcessor initialization failed")

    return processor
