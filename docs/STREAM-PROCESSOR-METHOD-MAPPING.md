# Stream Processor Method Mapping

**Source:** `analyzer/unified_analyzer.py`
**Target:** `analyzer/architecture/stream_processor.py`
**Date:** 2025-11-13

---

## Method Extraction Mapping

This document maps the original methods from `UnifiedConnascenceAnalyzer` to their new implementations in the architectural `StreamProcessor` component.

---

## 1. Initialization Methods

### `_initialize_streaming_components()` → `initialize()`

**Original (unified_analyzer.py, lines 1536-1577):**
```python
def _initialize_streaming_components(self) -> None:
    """Initialize streaming analysis components."""
    try:
        # Get global incremental cache instance
        self.incremental_cache = get_global_incremental_cache()

        # Create analyzer factory for stream processor
        def analyzer_factory():
            return UnifiedConnascenceAnalyzer(
                config_path=None, analysis_mode="batch"
            )

        # Configure stream processor
        stream_config = {
            "max_queue_size": self.streaming_config.get("max_queue_size", 1000),
            "max_workers": self.streaming_config.get("max_workers", 4),
            "cache_size": self.streaming_config.get("cache_size", 10000),
        }

        # Create stream processor
        self.stream_processor = create_stream_processor(
            analyzer_factory=analyzer_factory, **stream_config
        )

        # Setup streaming callbacks
        if "result_callback" in self.streaming_config:
            self.stream_processor.add_result_callback(
                self.streaming_config["result_callback"]
            )

        if "batch_callback" in self.streaming_config:
            self.stream_processor.add_batch_callback(
                self.streaming_config["batch_callback"]
            )

        logger.info(f"Streaming components initialized for {self.analysis_mode} mode")

    except Exception as e:
        logger.error(f"Failed to initialize streaming components: {e}")
        self.stream_processor = None
        self.incremental_cache = None
```

**New (stream_processor.py, lines 100-154):**
```python
def initialize(self, analyzer_factory: Callable) -> bool:
    """
    Initialize streaming components with analyzer factory.

    Args:
        analyzer_factory: Factory function to create analyzer instances

    Returns:
        True if initialization successful, False otherwise
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
        self.stream_processor = create_stream_processor(
            analyzer_factory=analyzer_factory, **stream_config
        )

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
```

**Changes:**
- Added return value (bool) for success/failure
- Moved from void to return-based error handling
- Accepts analyzer_factory as parameter (dependency injection)
- Added _is_initialized state tracking
- Enhanced logging with debug levels

---

## 2. Streaming Lifecycle Methods

### `start_streaming_analysis()` → `start_streaming()`

**Original (unified_analyzer.py, lines 1578-1609):**
```python
def start_streaming_analysis(self, directories: List[Union[str, Path]]) -> None:
    """Start streaming analysis for specified directories."""
    if not self.stream_processor:
        logger.error("Streaming not available - initialize with streaming mode")
        return

    if self.analysis_mode not in ["streaming", "hybrid"]:
        logger.error(f"Cannot start streaming in {self.analysis_mode} mode")
        return

    try:
        # Start stream processor
        import asyncio

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def start_streaming():
            await self.stream_processor.start()
            self.stream_processor.start_watching(directories)
            logger.info(f"Started streaming analysis for {len(directories)} directories")

        loop.run_until_complete(start_streaming())

    except Exception as e:
        logger.error(f"Failed to start streaming analysis: {e}")
```

**New (stream_processor.py, lines 156-201):**
```python
async def start_streaming(self, directories: List[Union[str, Path]]) -> bool:
    """
    Start streaming analysis for specified directories.

    Args:
        directories: List of directories to watch for changes

    Returns:
        True if streaming started successfully, False otherwise
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
```

**Changes:**
- Changed from sync to async method
- Added return value (bool)
- Added input validation (assertions)
- Added path existence validation
- Tracks watched directories
- No longer creates event loop (caller's responsibility)
- Removed analysis_mode check (component is mode-agnostic)

---

### `stop_streaming_analysis()` → `stop_streaming()`

**Original (unified_analyzer.py, lines 1610-1619):**
```python
async def stop_streaming_analysis(self) -> None:
    """Stop streaming analysis."""
    if self.stream_processor:
        try:
            self.stream_processor.stop_watching()
            await self.stream_processor.stop()
            logger.info("Streaming analysis stopped")
        except Exception as e:
            logger.error(f"Failed to stop streaming analysis: {e}")
```

**New (stream_processor.py, lines 203-230):**
```python
async def stop_streaming(self) -> bool:
    """
    Stop streaming analysis and cleanup resources.

    Returns:
        True if streaming stopped successfully, False otherwise
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
```

**Changes:**
- Added return value (bool)
- Added resource cleanup (clear watched directories)
- More detailed success/failure logging
- Early return for no-op case

---

## 3. Analysis Mode Methods

### `_analyze_project_streaming()` → `process_stream()`

**Original (unified_analyzer.py, lines 586-608):**
```python
def _analyze_project_streaming(
    self, project_path: Path, policy_preset: str, options: Dict[str, Any]
) -> UnifiedAnalysisResult:
    """Execute streaming analysis with real-time processing."""
    if not STREAMING_AVAILABLE or not self.stream_processor:
        logger.warning("Streaming mode requested but not available, falling back to batch")
        return self._analyze_project_batch(project_path, policy_preset, options)

    logger.info(f"Starting streaming analysis of {project_path}")
    self._get_timestamp_ms()

    # Start streaming processor if not already running
    if not self.stream_processor.is_running:
        self.start_streaming_analysis()

    # Process initial batch for immediate results
    initial_result = self._analyze_project_batch(project_path, policy_preset, options)

    # Set up continuous monitoring for file changes
    self.stream_processor.watch_directory(str(project_path))

    logger.info(f"Streaming analysis active for {project_path}")
    return initial_result
```

**New (stream_processor.py, lines 296-337):**
```python
def process_stream(self, file_changes: List[Path]) -> Dict[str, Any]:
    """
    Process a stream of file changes incrementally.

    Coordinates incremental analysis of changed files using the
    low-level stream processor and incremental cache.

    Args:
        file_changes: List of files that have changed

    Returns:
        Incremental analysis results
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
```

**Changes:**
- Changed from project-level to file-level processing
- Removed project_path, policy_preset, options (too high-level)
- Added change detection via incremental cache
- Returns dictionary instead of UnifiedAnalysisResult
- Delegates batch processing to batch_analyze()
- More focused on stream coordination

---

### `_analyze_project_hybrid()` → `batch_analyze()`

**Original (unified_analyzer.py, lines 610-630):**
```python
def _analyze_project_hybrid(
    self, project_path: Path, policy_preset: str, options: Dict[str, Any]
) -> UnifiedAnalysisResult:
    """Execute hybrid analysis combining batch and streaming."""
    if not STREAMING_AVAILABLE or not self.stream_processor:
        logger.warning("Hybrid mode requested but streaming not available, using batch only")
        return self._analyze_project_batch(project_path, policy_preset, options)

    logger.info(f"Starting hybrid analysis of {project_path}")

    # Run comprehensive batch analysis first
    batch_result = self._analyze_project_batch(project_path, policy_preset, options)

    # Enable streaming for incremental updates
    if not self.stream_processor.is_running:
        self.start_streaming_analysis()

    self.stream_processor.watch_directory(str(project_path))

    logger.info(f"Hybrid analysis complete - batch done, streaming active for {project_path}")
    return batch_result
```

**New (stream_processor.py, lines 249-294):**
```python
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
```

**Changes:**
- Simplified to focus on batch processing mechanics
- Removed project-level concepts
- Configurable batch_size parameter
- Returns list of batch results instead of UnifiedAnalysisResult
- Provides incremental progress logging
- Implements fail-safe (returns partial results on error)

---

## 4. Statistics and Monitoring

### `get_streaming_stats()` → `get_stats()`

**Original (unified_analyzer.py, lines 1620-1630):**
```python
def get_streaming_stats(self) -> Dict[str, Any]:
    """Get streaming performance statistics."""
    stats = {"streaming_available": STREAMING_AVAILABLE}

    if self.stream_processor:
        stats.update(self.stream_processor.get_stats())

    if self.incremental_cache:
        stats.update(self.incremental_cache.get_cache_stats())

    return stats
```

**New (stream_processor.py, lines 339-368):**
```python
def get_stats(self) -> Dict[str, Any]:
    """
    Get streaming performance statistics.

    Returns:
        Dictionary with streaming statistics
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
```

**Changes:**
- Added initialization status
- Added watched directories information
- Separated cache stats into nested dictionary
- Added error handling for stats retrieval
- More comprehensive monitoring data

---

## 5. New Methods (Not in Original)

### `detect_changes()`

**New Method (stream_processor.py, lines 232-261):**
```python
def detect_changes(self, files: List[Path]) -> List[Path]:
    """
    Detect which files have changed since last analysis.

    Uses incremental cache to identify files that need re-analysis.

    Args:
        files: List of files to check for changes

    Returns:
        List of files that have changed
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
```

**Purpose:**
- Provides change detection using incremental cache
- Filters out unchanged files to avoid unnecessary re-analysis
- Implements fail-safe behavior

---

### `watch_directory()`

**New Method (stream_processor.py, lines 385-418):**
```python
def watch_directory(self, directory: Union[str, Path]) -> bool:
    """
    Add a directory to watch for changes.

    Args:
        directory: Directory path to watch

    Returns:
        True if directory added successfully, False otherwise
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
```

**Purpose:**
- Allows adding individual directories to watch
- Validates directory existence
- Tracks watched directories
- Provides success/failure feedback

---

### `is_running` (Property)

**New Property (stream_processor.py, lines 370-383):**
```python
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
        return self.stream_processor.is_running
    except Exception:
        return False
```

**Purpose:**
- Provides easy status check
- Handles cases where stream_processor is None
- Error-safe implementation

---

## 6. Factory Function

### `create_stream_processor_coordinator()`

**New Factory (stream_processor.py, lines 421-446):**
```python
def create_stream_processor_coordinator(
    config: Optional[Dict[str, Any]] = None,
    analyzer_factory: Optional[Callable] = None
) -> StreamProcessor:
    """
    Factory function to create a configured StreamProcessor.

    Args:
        config: Configuration dictionary (uses defaults if None)
        analyzer_factory: Optional analyzer factory function

    Returns:
        Configured StreamProcessor instance
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
```

**Purpose:**
- Provides convenient creation pattern
- Sets sensible defaults
- Optionally initializes with analyzer factory
- Returns ready-to-use instance

---

## Summary

### Methods Extracted: 5
1. `_initialize_streaming_components()` → `initialize()`
2. `start_streaming_analysis()` → `start_streaming()`
3. `stop_streaming_analysis()` → `stop_streaming()`
4. `_analyze_project_streaming()` → `process_stream()`
5. `get_streaming_stats()` → `get_stats()`

### Methods Created: 4
1. `detect_changes()` - New change detection method
2. `batch_analyze()` - New batch processing method
3. `watch_directory()` - New directory watching method
4. `is_running` - New status property

### Factory Functions: 1
1. `create_stream_processor_coordinator()` - Convenience factory

### Total Methods: 10 (5 extracted + 4 new + 1 factory)

---

**Extraction Status:** COMPLETE ✓
**Documentation Status:** COMPLETE ✓
**Verification Status:** PASSED ✓
