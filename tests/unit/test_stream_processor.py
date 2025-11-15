"""
Comprehensive Unit Tests for StreamProcessor
============================================

Tests for the high-level stream processing coordinator that manages
streaming analysis workflows and integrates batch analysis with real-time
incremental updates.

Coverage target: 90%+ for StreamProcessor class

Test categories:
1. Initialization and Configuration
2. Lifecycle Management (initialize, start_streaming, stop_streaming)
3. File Change Detection
4. Batch Processing
5. Stream Processing
6. Statistics and State Tracking
7. Directory Watching
8. Error Handling and Edge Cases

NASA Compliance:
- All test functions under 60 lines
- Comprehensive input validation testing
- Error condition testing
"""

from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

# Import the component under test
from analyzer.architecture.stream_processor import (
    StreamProcessor,
    create_stream_processor_coordinator,
)


class TestStreamProcessorInitialization:
    """Test StreamProcessor initialization and configuration."""

    def test_init_with_valid_config(self):
        """Test initialization with valid configuration dictionary."""
        config = {
            "max_queue_size": 500,
            "max_workers": 8,
            "cache_size": 5000,
        }
        processor = StreamProcessor(config)

        assert processor.config == config
        assert processor.max_queue_size == 500
        assert processor.max_workers == 8
        assert processor.cache_size == 5000
        assert not processor._is_initialized
        assert processor._watched_directories == []

    def test_init_with_default_values(self):
        """Test initialization uses default values when not specified."""
        config = {}
        processor = StreamProcessor(config)

        assert processor.max_queue_size == 1000
        assert processor.max_workers == 4
        assert processor.cache_size == 10000

    def test_init_with_callbacks(self):
        """Test initialization with result and batch callbacks."""
        result_callback = Mock()
        batch_callback = Mock()
        config = {
            "result_callback": result_callback,
            "batch_callback": batch_callback,
        }
        processor = StreamProcessor(config)

        assert "result_callback" in processor.config
        assert "batch_callback" in processor.config

    def test_init_validates_config_not_none(self):
        """Test initialization validates config is not None."""
        with pytest.raises(AssertionError, match="config cannot be None"):
            StreamProcessor(None)

    def test_init_validates_config_is_dict(self):
        """Test initialization validates config is a dictionary."""
        with pytest.raises(AssertionError, match="config must be a dictionary"):
            StreamProcessor("invalid_config")


class TestStreamProcessorLifecycle:
    """Test StreamProcessor lifecycle management methods."""

    @patch("analyzer.architecture.stream_processor.STREAMING_AVAILABLE", True)
    @patch("analyzer.architecture.stream_processor.get_global_incremental_cache")
    @patch("analyzer.architecture.stream_processor.create_stream_processor")
    def test_initialize_success(self, mock_create_processor, mock_get_cache):
        """Test successful initialization of streaming components."""
        # Setup mocks
        mock_cache = Mock()
        mock_get_cache.return_value = mock_cache
        mock_processor = Mock()
        mock_create_processor.return_value = mock_processor
        analyzer_factory = Mock()

        config = {"max_queue_size": 500}
        processor = StreamProcessor(config)

        # Initialize
        result = processor.initialize(analyzer_factory)

        assert result is True
        assert processor._is_initialized is True
        assert processor.incremental_cache == mock_cache
        assert processor.stream_processor == mock_processor
        mock_create_processor.assert_called_once()

    @patch("analyzer.architecture.stream_processor.STREAMING_AVAILABLE", False)
    def test_initialize_when_streaming_unavailable(self):
        """Test initialization fails gracefully when streaming unavailable."""
        config = {}
        processor = StreamProcessor(config)
        analyzer_factory = Mock()

        result = processor.initialize(analyzer_factory)

        assert result is False
        assert not processor._is_initialized

    @patch("analyzer.architecture.stream_processor.STREAMING_AVAILABLE", True)
    @patch("analyzer.architecture.stream_processor.get_global_incremental_cache")
    def test_initialize_already_initialized(self, mock_get_cache):
        """Test initialization returns True if already initialized."""
        config = {}
        processor = StreamProcessor(config)
        processor._is_initialized = True

        analyzer_factory = Mock()
        result = processor.initialize(analyzer_factory)

        assert result is True
        mock_get_cache.assert_not_called()

    @patch("analyzer.architecture.stream_processor.STREAMING_AVAILABLE", True)
    @patch("analyzer.architecture.stream_processor.get_global_incremental_cache")
    def test_initialize_handles_exceptions(self, mock_get_cache):
        """Test initialization handles exceptions gracefully."""
        mock_get_cache.side_effect = Exception("Cache initialization failed")

        config = {}
        processor = StreamProcessor(config)
        analyzer_factory = Mock()

        result = processor.initialize(analyzer_factory)

        assert result is False
        assert not processor._is_initialized
        assert processor.stream_processor is None
        assert processor.incremental_cache is None

    @pytest.mark.asyncio
    async def test_start_streaming_success(self, tmp_path):
        """Test successful start of streaming for directories."""
        # Create test directories
        dir1 = tmp_path / "dir1"
        dir2 = tmp_path / "dir2"
        dir1.mkdir()
        dir2.mkdir()

        # Setup processor with mock stream processor
        config = {}
        processor = StreamProcessor(config)
        processor._is_initialized = True
        processor.stream_processor = Mock()
        processor.stream_processor.start = AsyncMock()
        processor.stream_processor.start_watching = Mock()

        # Start streaming
        result = await processor.start_streaming([str(dir1), str(dir2)])

        assert result is True
        processor.stream_processor.start.assert_called_once()
        assert processor.stream_processor.start_watching.call_count == 2
        assert len(processor._watched_directories) == 2

    @pytest.mark.asyncio
    async def test_start_streaming_validates_directories(self):
        """Test start_streaming validates directories parameter."""
        config = {}
        processor = StreamProcessor(config)

        with pytest.raises(AssertionError, match="directories cannot be None"):
            await processor.start_streaming(None)

        with pytest.raises(AssertionError, match="directories list cannot be empty"):
            await processor.start_streaming([])

    @pytest.mark.asyncio
    async def test_start_streaming_not_initialized(self):
        """Test start_streaming fails if not initialized."""
        config = {}
        processor = StreamProcessor(config)

        result = await processor.start_streaming(["/some/path"])

        assert result is False

    @pytest.mark.asyncio
    async def test_start_streaming_nonexistent_directory(self, tmp_path):
        """Test start_streaming fails for nonexistent directory."""
        config = {}
        processor = StreamProcessor(config)
        processor._is_initialized = True
        processor.stream_processor = Mock()

        nonexistent = tmp_path / "nonexistent"
        result = await processor.start_streaming([str(nonexistent)])

        assert result is False

    @pytest.mark.asyncio
    async def test_start_streaming_handles_exceptions(self, tmp_path):
        """Test start_streaming handles exceptions gracefully."""
        test_dir = tmp_path / "testdir"
        test_dir.mkdir()

        config = {}
        processor = StreamProcessor(config)
        processor._is_initialized = True
        processor.stream_processor = Mock()
        processor.stream_processor.start = AsyncMock(
            side_effect=Exception("Start failed")
        )

        result = await processor.start_streaming([str(test_dir)])

        assert result is False

    @pytest.mark.asyncio
    async def test_stop_streaming_success(self):
        """Test successful stop of streaming."""
        config = {}
        processor = StreamProcessor(config)
        processor.stream_processor = Mock()
        processor.stream_processor.stop_watching = Mock()
        processor.stream_processor.stop = AsyncMock()
        processor._watched_directories = [Path("/dir1"), Path("/dir2")]

        result = await processor.stop_streaming()

        assert result is True
        processor.stream_processor.stop_watching.assert_called_once()
        processor.stream_processor.stop.assert_called_once()
        assert len(processor._watched_directories) == 0

    @pytest.mark.asyncio
    async def test_stop_streaming_no_processor(self):
        """Test stop_streaming returns True when no processor active."""
        config = {}
        processor = StreamProcessor(config)
        processor.stream_processor = None

        result = await processor.stop_streaming()

        assert result is True

    @pytest.mark.asyncio
    async def test_stop_streaming_handles_exceptions(self):
        """Test stop_streaming handles exceptions gracefully."""
        config = {}
        processor = StreamProcessor(config)
        processor.stream_processor = Mock()
        processor.stream_processor.stop_watching = Mock(
            side_effect=Exception("Stop failed")
        )

        result = await processor.stop_streaming()

        assert result is False


class TestStreamProcessorFileChangeDetection:
    """Test file change detection functionality."""

    def test_detect_changes_with_cache(self):
        """Test change detection with incremental cache."""
        config = {}
        processor = StreamProcessor(config)
        mock_cache = Mock()
        processor.incremental_cache = mock_cache

        # Mock cache to return modified for some files
        mock_cache.is_file_modified.side_effect = [True, False, True]

        files = [Path("file1.py"), Path("file2.py"), Path("file3.py")]
        changed = processor.detect_changes(files)

        assert len(changed) == 2
        assert Path("file1.py") in changed
        assert Path("file3.py") in changed
        assert mock_cache.is_file_modified.call_count == 3

    def test_detect_changes_without_cache(self):
        """Test change detection returns all files when cache unavailable."""
        config = {}
        processor = StreamProcessor(config)
        processor.incremental_cache = None

        files = [Path("file1.py"), Path("file2.py")]
        changed = processor.detect_changes(files)

        assert changed == files

    def test_detect_changes_validates_files_not_none(self):
        """Test detect_changes validates files parameter."""
        config = {}
        processor = StreamProcessor(config)

        with pytest.raises(AssertionError, match="files cannot be None"):
            processor.detect_changes(None)

    def test_detect_changes_handles_exceptions(self):
        """Test detect_changes handles exceptions and returns all files."""
        config = {}
        processor = StreamProcessor(config)
        mock_cache = Mock()
        processor.incremental_cache = mock_cache
        mock_cache.is_file_modified.side_effect = Exception("Cache error")

        files = [Path("file1.py")]
        changed = processor.detect_changes(files)

        assert changed == files


class TestStreamProcessorBatchProcessing:
    """Test batch processing functionality."""

    def test_batch_analyze_success(self):
        """Test successful batch analysis of files."""
        config = {}
        processor = StreamProcessor(config)

        files = [Path(f"file{i}.py") for i in range(25)]
        results = processor.batch_analyze(files, batch_size=10)

        assert len(results) == 3  # 25 files / 10 per batch = 3 batches
        assert all(isinstance(r, dict) for r in results)

    def test_batch_analyze_validates_parameters(self):
        """Test batch_analyze validates input parameters."""
        config = {}
        processor = StreamProcessor(config)

        with pytest.raises(AssertionError, match="files cannot be None"):
            processor.batch_analyze(None)

        with pytest.raises(AssertionError, match="batch_size must be positive"):
            processor.batch_analyze([Path("file.py")], batch_size=0)

    def test_batch_analyze_empty_files(self):
        """Test batch_analyze handles empty file list."""
        config = {}
        processor = StreamProcessor(config)

        results = processor.batch_analyze([])

        assert results == []

    def test_batch_analyze_single_batch(self):
        """Test batch_analyze with files fitting in single batch."""
        config = {}
        processor = StreamProcessor(config)

        files = [Path(f"file{i}.py") for i in range(5)]
        results = processor.batch_analyze(files, batch_size=10)

        assert len(results) == 1

    def test_batch_analyze_handles_exceptions(self):
        """Test batch_analyze handles exceptions gracefully."""
        config = {}
        processor = StreamProcessor(config)

        # Mock _analyze_batch to raise exception
        with patch.object(
            processor, "_analyze_batch", side_effect=Exception("Analysis failed")
        ):
            files = [Path("file.py")]
            results = processor.batch_analyze(files)

            assert isinstance(results, list)

    def test_analyze_batch_placeholder(self):
        """Test _analyze_batch returns expected structure."""
        config = {}
        processor = StreamProcessor(config)

        batch = [Path("file1.py"), Path("file2.py")]
        result = processor._analyze_batch(batch)

        assert result["batch_size"] == 2
        assert len(result["files"]) == 2
        assert "timestamp" in result


class TestStreamProcessorStreamProcessing:
    """Test stream processing coordination."""

    def test_process_stream_success(self):
        """Test successful stream processing."""
        config = {}
        processor = StreamProcessor(config)
        processor._is_initialized = True

        # Mock dependencies
        mock_cache = Mock()
        processor.incremental_cache = mock_cache
        mock_cache.is_file_modified.return_value = True

        files = [Path("file1.py"), Path("file2.py")]
        result = processor.process_stream(files)

        assert result["status"] == "success"
        assert result["files_changed"] == 2
        assert result["files_checked"] == 2
        assert "batches_processed" in result

    def test_process_stream_no_changes(self):
        """Test process_stream when no files changed."""
        config = {}
        processor = StreamProcessor(config)
        processor._is_initialized = True

        mock_cache = Mock()
        processor.incremental_cache = mock_cache
        mock_cache.is_file_modified.return_value = False

        files = [Path("file1.py")]
        result = processor.process_stream(files)

        assert result["status"] == "no_changes"
        assert result["files_checked"] == 1

    def test_process_stream_validates_file_changes(self):
        """Test process_stream validates file_changes parameter."""
        config = {}
        processor = StreamProcessor(config)

        with pytest.raises(AssertionError, match="file_changes cannot be None"):
            processor.process_stream(None)

    def test_process_stream_not_initialized(self):
        """Test process_stream fails if not initialized."""
        config = {}
        processor = StreamProcessor(config)

        result = processor.process_stream([Path("file.py")])

        assert "error" in result
        assert "not initialized" in result["error"].lower()

    def test_process_stream_handles_exceptions(self):
        """Test process_stream handles exceptions gracefully."""
        config = {}
        processor = StreamProcessor(config)
        processor._is_initialized = True

        # Mock detect_changes to raise exception
        with patch.object(
            processor, "detect_changes", side_effect=Exception("Detection failed")
        ):
            result = processor.process_stream([Path("file.py")])

            assert "error" in result


class TestStreamProcessorStatistics:
    """Test statistics and state tracking."""

    def test_get_stats_basic(self):
        """Test get_stats returns basic statistics."""
        config = {}
        processor = StreamProcessor(config)

        stats = processor.get_stats()

        assert "streaming_available" in stats
        assert "initialized" in stats
        assert "watched_directories" in stats
        assert "directories" in stats
        assert stats["initialized"] is False

    def test_get_stats_with_processor(self):
        """Test get_stats includes stream processor statistics."""
        config = {}
        processor = StreamProcessor(config)
        processor._is_initialized = True

        mock_processor = Mock()
        mock_processor.get_stats.return_value = {"queue_size": 100}
        processor.stream_processor = mock_processor

        stats = processor.get_stats()

        assert stats["initialized"] is True
        assert "queue_size" in stats

    def test_get_stats_with_cache(self):
        """Test get_stats includes cache statistics."""
        config = {}
        processor = StreamProcessor(config)

        mock_cache = Mock()
        mock_cache.get_cache_stats.return_value = {"hit_rate": 0.85}
        processor.incremental_cache = mock_cache

        stats = processor.get_stats()

        assert "cache" in stats
        assert stats["cache"]["hit_rate"] == 0.85

    def test_get_stats_handles_processor_exceptions(self):
        """Test get_stats handles processor stat exceptions."""
        config = {}
        processor = StreamProcessor(config)

        mock_processor = Mock()
        mock_processor.get_stats.side_effect = Exception("Stats failed")
        processor.stream_processor = mock_processor

        stats = processor.get_stats()

        assert isinstance(stats, dict)  # Should still return stats

    def test_is_running_property_true(self):
        """Test is_running property returns True when processor running."""
        config = {}
        processor = StreamProcessor(config)

        mock_processor = Mock()
        mock_processor.is_running = True
        processor.stream_processor = mock_processor

        assert processor.is_running is True

    def test_is_running_property_false(self):
        """Test is_running property returns False when processor not running."""
        config = {}
        processor = StreamProcessor(config)

        mock_processor = Mock()
        mock_processor.is_running = False
        processor.stream_processor = mock_processor

        assert processor.is_running is False

    def test_is_running_property_no_processor(self):
        """Test is_running property returns False when no processor."""
        config = {}
        processor = StreamProcessor(config)
        processor.stream_processor = None

        assert processor.is_running is False

    def test_is_running_property_handles_exceptions(self):
        """Test is_running property handles exceptions."""
        config = {}
        processor = StreamProcessor(config)

        mock_processor = Mock()
        mock_processor.is_running = property(Mock(side_effect=Exception("Error")))
        processor.stream_processor = mock_processor

        # Should not raise exception
        assert processor.is_running is False


class TestStreamProcessorDirectoryWatching:
    """Test directory watching functionality."""

    def test_watch_directory_success(self, tmp_path):
        """Test successful directory watching."""
        test_dir = tmp_path / "testdir"
        test_dir.mkdir()

        config = {}
        processor = StreamProcessor(config)
        processor._is_initialized = True

        mock_processor = Mock()
        mock_processor.start_watching = Mock()
        processor.stream_processor = mock_processor

        result = processor.watch_directory(str(test_dir))

        assert result is True
        mock_processor.start_watching.assert_called_once()
        assert test_dir in processor._watched_directories

    def test_watch_directory_validates_directory(self):
        """Test watch_directory validates directory parameter."""
        config = {}
        processor = StreamProcessor(config)

        with pytest.raises(AssertionError, match="directory cannot be None"):
            processor.watch_directory(None)

    def test_watch_directory_not_initialized(self):
        """Test watch_directory fails if not initialized."""
        config = {}
        processor = StreamProcessor(config)

        result = processor.watch_directory("/some/path")

        assert result is False

    def test_watch_directory_nonexistent(self, tmp_path):
        """Test watch_directory fails for nonexistent directory."""
        config = {}
        processor = StreamProcessor(config)
        processor._is_initialized = True
        processor.stream_processor = Mock()

        nonexistent = tmp_path / "nonexistent"
        result = processor.watch_directory(str(nonexistent))

        assert result is False

    def test_watch_directory_handles_exceptions(self, tmp_path):
        """Test watch_directory handles exceptions gracefully."""
        test_dir = tmp_path / "testdir"
        test_dir.mkdir()

        config = {}
        processor = StreamProcessor(config)
        processor._is_initialized = True

        mock_processor = Mock()
        mock_processor.start_watching.side_effect = Exception("Watch failed")
        processor.stream_processor = mock_processor

        result = processor.watch_directory(str(test_dir))

        assert result is False


class TestStreamProcessorFactory:
    """Test factory function for creating StreamProcessor."""

    def test_create_stream_processor_coordinator_defaults(self):
        """Test factory creates processor with default configuration."""
        processor = create_stream_processor_coordinator()

        assert isinstance(processor, StreamProcessor)
        assert processor.max_queue_size == 1000
        assert processor.max_workers == 4
        assert processor.cache_size == 10000

    def test_create_stream_processor_coordinator_custom_config(self):
        """Test factory creates processor with custom configuration."""
        config = {
            "max_queue_size": 500,
            "max_workers": 8,
            "cache_size": 5000,
        }
        processor = create_stream_processor_coordinator(config=config)

        assert processor.max_queue_size == 500
        assert processor.max_workers == 8
        assert processor.cache_size == 5000

    @patch("analyzer.architecture.stream_processor.STREAMING_AVAILABLE", True)
    @patch("analyzer.architecture.stream_processor.get_global_incremental_cache")
    @patch("analyzer.architecture.stream_processor.create_stream_processor")
    def test_create_stream_processor_coordinator_with_factory(
        self, mock_create_processor, mock_get_cache
    ):
        """Test factory initializes processor with analyzer factory."""
        mock_cache = Mock()
        mock_get_cache.return_value = mock_cache
        mock_processor = Mock()
        mock_create_processor.return_value = mock_processor

        analyzer_factory = Mock()
        processor = create_stream_processor_coordinator(
            analyzer_factory=analyzer_factory
        )

        assert processor._is_initialized is True
        mock_create_processor.assert_called_once()

    @patch("analyzer.architecture.stream_processor.STREAMING_AVAILABLE", False)
    def test_create_stream_processor_coordinator_init_failure(self):
        """Test factory handles initialization failure gracefully."""
        analyzer_factory = Mock()
        processor = create_stream_processor_coordinator(
            analyzer_factory=analyzer_factory
        )

        # Should still create processor instance
        assert isinstance(processor, StreamProcessor)
        assert not processor._is_initialized


class TestStreamProcessorIntegration:
    """Integration tests for StreamProcessor workflows."""

    @pytest.mark.asyncio
    @patch("analyzer.architecture.stream_processor.STREAMING_AVAILABLE", True)
    @patch("analyzer.architecture.stream_processor.get_global_incremental_cache")
    @patch("analyzer.architecture.stream_processor.create_stream_processor")
    async def test_full_streaming_lifecycle(
        self, mock_create_processor, mock_get_cache, tmp_path
    ):
        """Test complete streaming lifecycle from init to stop."""
        # Setup mocks
        mock_cache = Mock()
        mock_cache.is_file_modified.return_value = True
        mock_get_cache.return_value = mock_cache

        mock_processor = Mock()
        mock_processor.start = AsyncMock()
        mock_processor.stop = AsyncMock()
        mock_processor.start_watching = Mock()
        mock_processor.stop_watching = Mock()
        mock_processor.is_running = True
        mock_create_processor.return_value = mock_processor

        # Create test directory
        test_dir = tmp_path / "testdir"
        test_dir.mkdir()

        # Initialize processor
        analyzer_factory = Mock()
        config = {"max_queue_size": 500}
        processor = StreamProcessor(config)

        # Test lifecycle
        init_result = processor.initialize(analyzer_factory)
        assert init_result is True

        start_result = await processor.start_streaming([str(test_dir)])
        assert start_result is True

        # Process some files
        files = [Path("file1.py"), Path("file2.py")]
        process_result = processor.process_stream(files)
        assert process_result["status"] == "success"

        # Check stats
        stats = processor.get_stats()
        assert stats["initialized"] is True

        # Stop streaming
        stop_result = await processor.stop_streaming()
        assert stop_result is True
        assert len(processor._watched_directories) == 0

    def test_batch_processing_with_change_detection(self):
        """Test batch processing integrates with change detection."""
        config = {}
        processor = StreamProcessor(config)
        processor._is_initialized = True

        # Mock cache to mark some files as changed
        mock_cache = Mock()
        mock_cache.is_file_modified.side_effect = [True, False, True, True, False]
        processor.incremental_cache = mock_cache

        # Process files
        files = [Path(f"file{i}.py") for i in range(5)]
        changed = processor.detect_changes(files)
        assert len(changed) == 3

        # Batch analyze changed files
        results = processor.batch_analyze(changed, batch_size=2)
        assert len(results) == 2  # 3 files / 2 per batch = 2 batches


# Run tests with: pytest tests/unit/test_stream_processor.py -v
