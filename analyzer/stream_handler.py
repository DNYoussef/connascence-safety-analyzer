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
Stream Handler Module
=====================

Handles streaming and incremental analysis capabilities.
Extracted from unified_analyzer.py for NASA Rule 4 compliance.

Contains:
- StreamHandler: Main streaming management class
- Streaming analysis initialization
- Incremental analysis support
"""

import logging
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

# Try to import streaming components
try:
    from .streaming.incremental_cache import IncrementalCache, get_global_incremental_cache
    from .streaming.stream_processor import (
        AnalysisRequest,
        AnalysisResult,
        StreamProcessor,
        create_stream_processor,
        process_file_changes_stream,
    )
    STREAMING_AVAILABLE = True
except ImportError:
    STREAMING_AVAILABLE = False
    IncrementalCache = None
    StreamProcessor = None


class StreamHandler:
    """
    Handles streaming and incremental analysis capabilities.

    Features:
    - Streaming analysis initialization
    - Incremental analysis with file watching
    - Real-time processing callbacks
    - Hybrid batch+streaming mode support

    NASA Rule 4: All functions under 60 lines
    NASA Rule 7: Bounded resource management
    """

    def __init__(
        self,
        streaming_config: Optional[Dict[str, Any]] = None,
        streaming_coordinator: Optional[Any] = None,
    ):
        """
        Initialize stream handler with configuration.

        Args:
            streaming_config: Configuration for streaming mode
            streaming_coordinator: Architecture StreamingCoordinator instance

        NASA Rule 5: Input validation
        """
        self.streaming_config = streaming_config or {}
        self.streaming_coordinator = streaming_coordinator

        # Streaming components (initialized lazily)
        self.stream_processor: Optional[Any] = None
        self.incremental_cache: Optional[Any] = None

        # State tracking
        self._streaming_initialized = False
        self._watched_directories: List[str] = []
        self._result_callbacks: List[Callable] = []

        logger.info(f"StreamHandler initialized (streaming_available={STREAMING_AVAILABLE})")

    def is_streaming_available(self) -> bool:
        """Check if streaming components are available."""
        return STREAMING_AVAILABLE

    def initialize_streaming_components(self, analyzer_factory: Optional[Callable] = None) -> bool:
        """
        Initialize streaming analysis components.

        Args:
            analyzer_factory: Factory function to create analyzer instances

        Returns:
            True if initialization successful

        NASA Rule 4: Function under 60 lines
        NASA Rule 5: Input validation and error handling
        """
        if not STREAMING_AVAILABLE:
            logger.debug("Streaming components not available")
            return False

        if self._streaming_initialized:
            logger.debug("Streaming already initialized")
            return True

        try:
            # Get global incremental cache instance
            self.incremental_cache = get_global_incremental_cache()

            # Configure stream processor
            stream_config = {
                "max_queue_size": self.streaming_config.get("max_queue_size", 1000),
                "max_workers": self.streaming_config.get("max_workers", 4),
                "cache_size": self.streaming_config.get("cache_size", 10000),
            }

            # Create stream processor with factory if provided
            if analyzer_factory:
                self.stream_processor = create_stream_processor(
                    analyzer_factory=analyzer_factory,
                    **stream_config
                )
            else:
                self.stream_processor = create_stream_processor(**stream_config)

            # Setup streaming callbacks if configured
            if "result_callback" in self.streaming_config:
                self.stream_processor.add_result_callback(
                    self.streaming_config["result_callback"]
                )
                self._result_callbacks.append(self.streaming_config["result_callback"])

            self._streaming_initialized = True
            logger.info("Streaming components initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize streaming components: {e}")
            return False

    def start_streaming_analysis(self) -> bool:
        """
        Start the streaming processor if not already running.

        Returns:
            True if started or already running

        NASA Rule 4: Function under 60 lines
        """
        if not self.stream_processor:
            logger.warning("Stream processor not initialized")
            return False

        if self.stream_processor.is_running:
            logger.debug("Stream processor already running")
            return True

        try:
            self.stream_processor.start()
            logger.info("Streaming analysis started")
            return True
        except Exception as e:
            logger.error(f"Failed to start streaming analysis: {e}")
            return False

    def stop_streaming_analysis(self) -> bool:
        """
        Stop the streaming processor.

        Returns:
            True if stopped successfully

        NASA Rule 4: Function under 60 lines
        """
        if not self.stream_processor:
            return True

        if not self.stream_processor.is_running:
            return True

        try:
            self.stream_processor.stop()
            logger.info("Streaming analysis stopped")
            return True
        except Exception as e:
            logger.error(f"Failed to stop streaming analysis: {e}")
            return False

    def watch_directory(self, directory_path: str) -> bool:
        """
        Set up file watching for a directory.

        Args:
            directory_path: Path to directory to watch

        Returns:
            True if watching started successfully

        NASA Rule 4: Function under 60 lines
        """
        if not self.stream_processor:
            logger.warning("Stream processor not initialized - cannot watch directory")
            return False

        try:
            self.stream_processor.watch_directory(directory_path)
            self._watched_directories.append(directory_path)
            logger.info(f"Watching directory: {directory_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to watch directory {directory_path}: {e}")
            return False

    def analyze_project_streaming(
        self,
        project_path: Path,
        batch_analyzer: Callable,
        policy_preset: str,
        options: Dict[str, Any],
    ) -> Any:
        """
        Execute streaming analysis with real-time processing.

        Delegates to StreamingCoordinator if available.

        Args:
            project_path: Path to project
            batch_analyzer: Fallback batch analysis function
            policy_preset: Policy preset name
            options: Analysis options

        Returns:
            Analysis result

        NASA Rule 4: Function under 60 lines
        """
        # Delegate to coordinator if available
        if self.streaming_coordinator:
            return self.streaming_coordinator.analyze_project_streaming(
                project_path, batch_analyzer, policy_preset, options
            )

        # Fallback implementation
        if not STREAMING_AVAILABLE or not self.stream_processor:
            logger.warning("Streaming mode requested but not available, falling back to batch")
            return batch_analyzer(project_path, policy_preset, options)

        logger.info(f"Starting streaming analysis of {project_path}")

        # Start streaming processor if not already running
        if not self.stream_processor.is_running:
            self.start_streaming_analysis()

        # Process initial batch for immediate results
        initial_result = batch_analyzer(project_path, policy_preset, options)

        # Set up continuous monitoring for file changes
        self.watch_directory(str(project_path))

        logger.info(f"Streaming analysis active for {project_path}")
        return initial_result

    def analyze_project_hybrid(
        self,
        project_path: Path,
        batch_analyzer: Callable,
        policy_preset: str,
        options: Dict[str, Any],
    ) -> Any:
        """
        Execute hybrid analysis combining batch and streaming.

        Delegates to StreamingCoordinator if available.

        Args:
            project_path: Path to project
            batch_analyzer: Batch analysis function
            policy_preset: Policy preset name
            options: Analysis options

        Returns:
            Analysis result

        NASA Rule 4: Function under 60 lines
        """
        # Delegate to coordinator if available
        if self.streaming_coordinator:
            return self.streaming_coordinator.analyze_project_hybrid(
                project_path, batch_analyzer, policy_preset, options
            )

        # Fallback implementation
        if not STREAMING_AVAILABLE or not self.stream_processor:
            logger.warning("Hybrid mode requested but streaming not available, using batch only")
            return batch_analyzer(project_path, policy_preset, options)

        logger.info(f"Starting hybrid analysis of {project_path}")

        # Run comprehensive batch analysis first
        batch_result = batch_analyzer(project_path, policy_preset, options)

        # Enable streaming for incremental updates
        if not self.stream_processor.is_running:
            self.start_streaming_analysis()

        self.watch_directory(str(project_path))

        logger.info(f"Hybrid analysis complete - batch done, streaming active for {project_path}")
        return batch_result

    def add_result_callback(self, callback: Callable) -> None:
        """Add a callback for streaming results."""
        self._result_callbacks.append(callback)
        if self.stream_processor:
            self.stream_processor.add_result_callback(callback)

    def get_incremental_changes(self, since_timestamp: Optional[float] = None) -> List[Dict[str, Any]]:
        """
        Get incremental changes since a timestamp.

        Args:
            since_timestamp: Unix timestamp to get changes since

        Returns:
            List of change records
        """
        if not self.incremental_cache:
            return []

        try:
            return self.incremental_cache.get_changes(since=since_timestamp)
        except Exception as e:
            logger.error(f"Failed to get incremental changes: {e}")
            return []

    def get_stats(self) -> Dict[str, Any]:
        """Get streaming statistics."""
        stats = {
            "streaming_available": STREAMING_AVAILABLE,
            "streaming_initialized": self._streaming_initialized,
            "watched_directories": len(self._watched_directories),
            "result_callbacks": len(self._result_callbacks),
        }

        if self.stream_processor:
            stats["processor_running"] = self.stream_processor.is_running
            if hasattr(self.stream_processor, "get_stats"):
                stats["processor_stats"] = self.stream_processor.get_stats()

        return stats

    def shutdown(self) -> None:
        """Shutdown streaming components and cleanup resources."""
        try:
            self.stop_streaming_analysis()

            # Clear tracked state
            self._watched_directories.clear()
            self._result_callbacks.clear()
            self._streaming_initialized = False

            logger.info("StreamHandler shutdown complete")

        except Exception as e:
            logger.error(f"StreamHandler shutdown failed: {e}")


__all__ = ["StreamHandler", "STREAMING_AVAILABLE"]
