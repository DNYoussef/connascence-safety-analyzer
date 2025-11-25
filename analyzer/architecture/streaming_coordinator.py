"""
StreamingCoordinator - Centralized streaming analysis management

Extracted from: analyzer/unified_analyzer.py
Purpose: Centralize all streaming analysis logic into a dedicated component

Responsibilities:
- Streaming analysis coordination
- Hybrid batch+streaming analysis
- Streaming component initialization
- Stream lifecycle management (start/stop)
- Streaming performance statistics

NASA Compliance:
- Rule 4: All functions under 60 lines
- Rule 5: Input assertions and error handling
- Rule 7: Bounded resource management
"""

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)

# Import streaming components with availability check
try:
    from ..streaming.incremental_cache import IncrementalCache, get_global_incremental_cache
    from ..streaming.stream_processor import (
        StreamProcessor,
        create_stream_processor,
    )
    STREAMING_AVAILABLE = True
except ImportError:
    STREAMING_AVAILABLE = False
    StreamProcessor = None  # type: ignore
    IncrementalCache = None  # type: ignore
    get_global_incremental_cache = None  # type: ignore
    create_stream_processor = None  # type: ignore


class StreamingCoordinator:
    """
    Intelligent streaming analysis coordinator.

    Features:
    - Real-time file change monitoring
    - Hybrid batch+streaming analysis modes
    - Incremental cache integration
    - Stream lifecycle management
    - Performance statistics tracking

    NASA Rule 4: Class under 500 lines
    NASA Rule 7: Resource-bounded with automatic cleanup
    """

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        stream_processor: Optional[Any] = None,
        incremental_cache: Optional[Any] = None,
        analyzer_factory: Optional[Any] = None,
    ):
        """
        Initialize streaming coordinator with configuration.

        Args:
            config: Streaming configuration dictionary
                - max_queue_size: Maximum event queue size (default: 1000)
                - max_workers: Worker thread count (default: 4)
                - cache_size: Cache entry limit (default: 10000)
                - result_callback: Callback for analysis results
                - batch_callback: Callback for batch processing
            stream_processor: Pre-configured StreamProcessor instance
            incremental_cache: Pre-configured IncrementalCache instance
            analyzer_factory: Factory function to create analyzer instances

        NASA Rule 5: Input validation
        """
        self.config = config or {}
        self.stream_processor = stream_processor
        self.incremental_cache = incremental_cache
        self.analyzer_factory = analyzer_factory

        # Track streaming availability
        self.streaming_available = STREAMING_AVAILABLE

        # Initialize on-demand if not provided
        if not self.stream_processor and STREAMING_AVAILABLE:
            logger.info("StreamingCoordinator initialized (lazy initialization)")
        elif not STREAMING_AVAILABLE:
            logger.warning("Streaming components not available - limited functionality")

    def _initialize_streaming_components(self) -> None:
        """
        Initialize streaming analysis components.

        NASA Rule 4: Function under 60 lines
        NASA Rule 5: Input validation and error handling
        """
        assert STREAMING_AVAILABLE, "Streaming components not available"

        try:
            # Get global incremental cache instance
            if not self.incremental_cache:
                self.incremental_cache = get_global_incremental_cache()

            # Configure stream processor based on streaming config
            stream_config = {
                "max_queue_size": self.config.get("max_queue_size", 1000),
                "max_workers": self.config.get("max_workers", 4),
                "cache_size": self.config.get("cache_size", 10000),
            }

            # Create stream processor with factory
            if not self.stream_processor and self.analyzer_factory:
                self.stream_processor = create_stream_processor(
                    analyzer_factory=self.analyzer_factory, **stream_config
                )

            # Setup streaming callbacks if configured
            if self.stream_processor:
                if "result_callback" in self.config:
                    self.stream_processor.add_result_callback(
                        self.config["result_callback"]
                    )

                if "batch_callback" in self.config:
                    self.stream_processor.add_batch_callback(
                        self.config["batch_callback"]
                    )

            logger.info("Streaming components initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize streaming components: {e}")
            self.stream_processor = None
            self.incremental_cache = None

    def analyze_project_streaming(
        self,
        project_path: Path,
        batch_analyzer_callback: Any,
        policy_preset: str,
        options: Dict[str, Any],
    ) -> Any:
        """
        Execute streaming analysis with real-time processing.

        Args:
            project_path: Root directory to analyze
            batch_analyzer_callback: Function to perform batch analysis
            policy_preset: Policy configuration preset name
            options: Analysis options dictionary

        Returns:
            Initial analysis result from batch pass

        NASA Rule 4: Function under 60 lines
        NASA Rule 5: Input validation
        """
        assert project_path.exists(), f"project_path must exist: {project_path}"

        if not STREAMING_AVAILABLE or not self.stream_processor:
            logger.warning(
                "Streaming mode requested but not available, falling back to batch"
            )
            return batch_analyzer_callback(project_path, policy_preset, options)

        logger.info(f"Starting streaming analysis of {project_path}")

        # Start streaming processor if not already running
        if not self.stream_processor.is_running:
            self.start_streaming_analysis([project_path])

        # Process initial batch for immediate results
        initial_result = batch_analyzer_callback(project_path, policy_preset, options)

        # Set up continuous monitoring for file changes
        self.stream_processor.watch_directory(str(project_path))

        logger.info(f"Streaming analysis active for {project_path}")
        return initial_result

    def analyze_project_hybrid(
        self,
        project_path: Path,
        batch_analyzer_callback: Any,
        policy_preset: str,
        options: Dict[str, Any],
    ) -> Any:
        """
        Execute hybrid analysis combining batch and streaming.

        Args:
            project_path: Root directory to analyze
            batch_analyzer_callback: Function to perform batch analysis
            policy_preset: Policy configuration preset name
            options: Analysis options dictionary

        Returns:
            Batch analysis result (streaming continues in background)

        NASA Rule 4: Function under 60 lines
        """
        assert project_path.exists(), f"project_path must exist: {project_path}"

        if not STREAMING_AVAILABLE or not self.stream_processor:
            logger.warning(
                "Hybrid mode requested but streaming not available, using batch only"
            )
            return batch_analyzer_callback(project_path, policy_preset, options)

        logger.info(f"Starting hybrid analysis of {project_path}")

        # Run comprehensive batch analysis first
        batch_result = batch_analyzer_callback(project_path, policy_preset, options)

        # Enable streaming for incremental updates
        if not self.stream_processor.is_running:
            self.start_streaming_analysis([project_path])

        self.stream_processor.watch_directory(str(project_path))

        logger.info(
            f"Hybrid analysis complete - batch done, streaming active for {project_path}"
        )
        return batch_result

    def start_streaming_analysis(self, directories: List[Union[str, Path]]) -> None:
        """
        Start streaming analysis for specified directories.

        Args:
            directories: Directories to watch for changes

        NASA Rule 4: Function under 60 lines
        NASA Rule 5: Input validation
        """
        assert self.stream_processor, "Stream processor not initialized"
        assert directories, "directories cannot be empty"

        try:
            # Start stream processor with async event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            async def start_streaming():
                await self.stream_processor.start()
                self.stream_processor.start_watching(directories)
                logger.info(
                    f"Started streaming analysis for {len(directories)} directories"
                )

            loop.run_until_complete(start_streaming())

        except Exception as e:
            logger.error(f"Failed to start streaming analysis: {e}")

    async def stop_streaming_analysis(self) -> None:
        """
        Stop streaming analysis.

        NASA Rule 4: Function under 60 lines
        NASA Rule 7: Complete resource cleanup
        """
        if self.stream_processor:
            try:
                self.stream_processor.stop_watching()
                await self.stream_processor.stop()
                logger.info("Streaming analysis stopped")
            except Exception as e:
                logger.error(f"Failed to stop streaming analysis: {e}")

    def get_streaming_stats(self) -> Dict[str, Any]:
        """
        Get streaming performance statistics.

        Returns:
            Dictionary with streaming metrics including:
            - streaming_available: Whether streaming is supported
            - queue_size: Current event queue size
            - processed_events: Total events processed
            - cache_hits: Incremental cache hit count
            - cache_size: Current cache entry count

        NASA Rule 4: Function under 60 lines
        """
        stats = {"streaming_available": STREAMING_AVAILABLE}

        # Get stream processor statistics
        if self.stream_processor:
            try:
                stats.update(self.stream_processor.get_stats())
            except Exception as e:
                logger.debug(f"Failed to get stream processor stats: {e}")

        # Get incremental cache statistics
        if self.incremental_cache:
            try:
                stats.update(self.incremental_cache.get_cache_stats())
            except Exception as e:
                logger.debug(f"Failed to get incremental cache stats: {e}")

        return stats

    def is_streaming_available(self) -> bool:
        """
        Check if streaming functionality is available.

        Returns:
            True if streaming components are loaded and configured

        NASA Rule 4: Function under 60 lines
        """
        return STREAMING_AVAILABLE and self.stream_processor is not None

    def is_running(self) -> bool:
        """
        Check if streaming analysis is currently running.

        Returns:
            True if stream processor is active

        NASA Rule 4: Function under 60 lines
        """
        if not self.stream_processor:
            return False

        try:
            return self.stream_processor.is_running
        except Exception:
            return False
