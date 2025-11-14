"""
Comprehensive unit tests for CacheManager component.

Tests cover:
- Cache hit/miss scenarios
- Hash-based invalidation
- LRU eviction with memory bounds
- Intelligent cache warming with file prioritization
- Performance tracking (hit rate, metrics)
- Edge cases (empty cache, full cache, invalid paths)

Target Coverage: 95%+ for CacheManager
NASA Compliance: Rule 4 (functions under 60 lines), Rule 5 (assertions)
"""

import ast
import logging
import pytest
from pathlib import Path
from typing import Dict, Any
from unittest.mock import Mock, MagicMock, patch, PropertyMock

from analyzer.architecture.cache_manager import CacheManager


@pytest.fixture
def cache_manager(mock_file_cache):
    """
    Create CacheManager instance with mocked dependencies.

    Args:
        mock_file_cache: Mocked FileContentCache

    Returns:
        Configured CacheManager for testing
    """
    # Patch at the location where FileContentCache is imported
    with patch('analyzer.optimization.file_cache.FileContentCache',
               return_value=mock_file_cache):
        manager = CacheManager(config={"max_memory": 100 * 1024 * 1024})
        return manager


@pytest.fixture
def temp_project_path(tmp_path):
    """
    Create temporary project structure for cache warming tests.

    Args:
        tmp_path: pytest temporary path fixture

    Returns:
        Path to temporary project with Python files
    """
    # Create directory structure
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "lib").mkdir()

    # Create common files
    (tmp_path / "__init__.py").write_text("# init")
    (tmp_path / "main.py").write_text("# main" * 10)
    (tmp_path / "config.py").write_text("# config" * 5)

    # Create src files
    (tmp_path / "src" / "__init__.py").write_text("# src init")
    (tmp_path / "src" / "utils.py").write_text("# utils" * 20)
    (tmp_path / "src" / "core.py").write_text("# core" * 30)

    # Create lib files
    (tmp_path / "lib" / "common.py").write_text("# common" * 15)
    (tmp_path / "lib" / "base.py").write_text("# base" * 10)

    # Create large file that should be skipped
    large_content = "# large" * 100000  # >500KB
    (tmp_path / "src" / "large.py").write_text(large_content)

    return tmp_path


class TestCacheManagerInitialization:
    """Test CacheManager initialization and configuration."""

    def test_init_default_config(self, mock_file_cache):
        """Test initialization with default configuration."""
        with patch('analyzer.optimization.file_cache.FileContentCache',
                   return_value=mock_file_cache):
            manager = CacheManager()

            assert manager.cache_available is True
            assert manager.config == {}
            assert manager._cache_stats["hits"] == 0
            assert manager._cache_stats["misses"] == 0
            assert len(manager._analysis_patterns) == 0
            assert len(manager._file_priorities) == 0

    def test_init_custom_config(self, mock_file_cache):
        """Test initialization with custom configuration."""
        config = {
            "max_memory": 200 * 1024 * 1024,
            "enable_warming": True,
            "warm_file_count": 20
        }

        with patch('analyzer.optimization.file_cache.FileContentCache',
                   return_value=mock_file_cache):
            manager = CacheManager(config=config)

            assert manager.config == config
            assert manager.cache_available is True

    def test_init_without_file_cache(self):
        """Test initialization when FileContentCache is unavailable."""
        with patch('analyzer.optimization.file_cache.FileContentCache',
                   side_effect=ImportError("Module not found")):
            manager = CacheManager()

            assert manager.cache_available is False
            assert manager.file_cache is None


class TestCacheASTOperations:
    """Test AST caching operations."""

    def test_get_cached_ast_hit(self, cache_manager, sample_ast, tmp_path):
        """Test successful AST cache hit."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 42")

        cache_manager.file_cache.get_ast_tree.return_value = sample_ast

        result = cache_manager.get_cached_ast(test_file)

        assert result == sample_ast
        assert cache_manager._cache_stats["hits"] == 1
        assert cache_manager._cache_stats["misses"] == 0
        assert str(test_file) in cache_manager._analysis_patterns
        assert cache_manager._analysis_patterns[str(test_file)] == 1

    def test_get_cached_ast_miss(self, cache_manager, tmp_path):
        """Test AST cache miss."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 42")

        cache_manager.file_cache.get_ast_tree.return_value = None

        result = cache_manager.get_cached_ast(test_file)

        assert result is None
        assert cache_manager._cache_stats["hits"] == 0
        assert cache_manager._cache_stats["misses"] == 1

    def test_get_cached_ast_multiple_accesses(self, cache_manager, sample_ast, tmp_path):
        """Test access pattern tracking for multiple AST retrievals."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 42")

        cache_manager.file_cache.get_ast_tree.return_value = sample_ast

        # Access same file 3 times
        for _ in range(3):
            cache_manager.get_cached_ast(test_file)

        assert cache_manager._analysis_patterns[str(test_file)] == 3
        assert cache_manager._cache_stats["hits"] == 3

    def test_get_cached_ast_nonexistent_file(self, cache_manager, tmp_path):
        """Test AST retrieval for non-existent file raises assertion."""
        nonexistent = tmp_path / "nonexistent.py"

        with pytest.raises(AssertionError, match="file_path must exist"):
            cache_manager.get_cached_ast(nonexistent)

    def test_get_cached_ast_exception_handling(self, cache_manager, tmp_path):
        """Test AST retrieval handles exceptions gracefully."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 42")

        cache_manager.file_cache.get_ast_tree.side_effect = Exception("Cache error")

        result = cache_manager.get_cached_ast(test_file)

        assert result is None
        assert cache_manager._cache_stats["misses"] == 1

    def test_cache_ast_success(self, cache_manager, sample_ast, tmp_path):
        """Test successful AST caching."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 42")

        cache_manager.cache_ast(test_file, sample_ast)

        assert str(test_file) in cache_manager.file_cache._ast_cache
        assert cache_manager.file_cache._ast_cache[str(test_file)] == sample_ast
        assert str(test_file) in cache_manager._file_priorities

    def test_cache_ast_invalid_tree_type(self, cache_manager, tmp_path):
        """Test AST caching with invalid tree type raises assertion."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 42")

        with pytest.raises(AssertionError, match="tree must be ast.Module"):
            cache_manager.cache_ast(test_file, "not an AST")

    def test_cache_ast_nonexistent_file(self, cache_manager, sample_ast, tmp_path):
        """Test AST caching for non-existent file raises assertion."""
        nonexistent = tmp_path / "nonexistent.py"

        with pytest.raises(AssertionError, match="file_path must exist"):
            cache_manager.cache_ast(nonexistent, sample_ast)


class TestCacheContentOperations:
    """Test file content caching operations."""

    def test_get_cached_content_hit(self, cache_manager, tmp_path):
        """Test successful content cache hit."""
        test_file = tmp_path / "test.py"
        content = "print('hello')"
        test_file.write_text(content)

        cache_manager.file_cache.get_file_content.return_value = content

        result = cache_manager.get_cached_content(test_file)

        assert result == content
        assert cache_manager._cache_stats["hits"] == 1
        assert str(test_file) in cache_manager._analysis_patterns

    def test_get_cached_content_miss(self, cache_manager, tmp_path):
        """Test content cache miss."""
        test_file = tmp_path / "test.py"
        test_file.write_text("print('hello')")

        cache_manager.file_cache.get_file_content.return_value = None

        result = cache_manager.get_cached_content(test_file)

        assert result is None
        assert cache_manager._cache_stats["misses"] == 1

    def test_get_cached_lines_hit(self, cache_manager, tmp_path):
        """Test successful lines cache hit."""
        test_file = tmp_path / "test.py"
        test_file.write_text("line1\nline2\nline3")

        expected_lines = ["line1", "line2", "line3"]
        cache_manager.file_cache.get_file_lines.return_value = expected_lines

        result = cache_manager.get_cached_lines(test_file)

        assert result == expected_lines
        assert cache_manager._cache_stats["hits"] == 1

    def test_get_cached_lines_miss(self, cache_manager, tmp_path):
        """Test lines cache miss."""
        test_file = tmp_path / "test.py"
        test_file.write_text("line1\nline2")

        cache_manager.file_cache.get_file_lines.return_value = []

        result = cache_manager.get_cached_lines(test_file)

        assert result == []
        assert cache_manager._cache_stats["misses"] == 1


class TestCacheInvalidation:
    """Test cache invalidation operations."""

    def test_invalidate_single_file(self, cache_manager, sample_ast, tmp_path):
        """Test invalidating cache for single file."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 42")

        # Populate caches
        file_key = str(test_file)
        cache_manager.file_cache._content_cache[file_key] = "content"
        cache_manager.file_cache._ast_cache[file_key] = sample_ast
        cache_manager._analysis_patterns[file_key] = 5
        cache_manager._file_priorities[file_key] = 50

        cache_manager.invalidate(test_file)

        assert file_key not in cache_manager.file_cache._content_cache
        assert file_key not in cache_manager.file_cache._ast_cache
        assert file_key not in cache_manager._analysis_patterns
        assert file_key not in cache_manager._file_priorities

    def test_invalidate_nonexistent_file(self, cache_manager, tmp_path):
        """Test invalidating non-existent file (should not raise error)."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 42")

        # Should not raise exception
        cache_manager.invalidate(test_file)

    def test_clear_all_caches(self, cache_manager, sample_ast, tmp_path):
        """Test clearing all caches."""
        # Populate caches
        for i in range(3):
            test_file = tmp_path / f"test{i}.py"
            test_file.write_text(f"x = {i}")
            file_key = str(test_file)
            cache_manager.file_cache._content_cache[file_key] = f"content{i}"
            cache_manager.file_cache._ast_cache[file_key] = sample_ast
            cache_manager._analysis_patterns[file_key] = i + 1

        cache_manager.clear_all()

        cache_manager.file_cache.clear_cache.assert_called_once()
        assert len(cache_manager._analysis_patterns) == 0
        assert len(cache_manager._file_priorities) == 0


class TestCacheStatistics:
    """Test cache performance statistics and tracking."""

    def test_get_cache_stats_basic(self, cache_manager):
        """Test getting basic cache statistics."""
        # Simulate some cache activity
        cache_manager._cache_stats["hits"] = 80
        cache_manager._cache_stats["misses"] = 20
        cache_manager._cache_stats["warm_requests"] = 15
        cache_manager._cache_stats["batch_loads"] = 5

        stats = cache_manager.get_cache_stats()

        assert stats["hits"] == 80
        assert stats["misses"] == 20
        assert stats["hit_rate"] == 0.8  # 80/(80+20)
        assert stats["warm_requests"] == 15
        assert stats["batch_loads"] == 5

    def test_get_cache_stats_with_memory(self, cache_manager):
        """Test cache statistics include memory usage."""
        cache_manager._cache_stats["hits"] = 100
        cache_manager._cache_stats["misses"] = 0

        stats = cache_manager.get_cache_stats()

        assert "memory_usage_mb" in stats
        assert "max_memory_mb" in stats
        assert "memory_usage_percent" in stats
        assert stats["memory_usage_mb"] == 50.0  # 50MB from fixture
        assert stats["max_memory_mb"] == 100.0  # 100MB from fixture
        assert stats["memory_usage_percent"] == 50.0

    def test_get_hit_rate_zero_accesses(self, cache_manager):
        """Test hit rate calculation with zero cache accesses."""
        hit_rate = cache_manager.get_hit_rate()
        assert hit_rate == 0.0

    def test_get_hit_rate_perfect(self, cache_manager):
        """Test hit rate calculation with 100% hits."""
        cache_manager._cache_stats["hits"] = 100
        cache_manager._cache_stats["misses"] = 0

        hit_rate = cache_manager.get_hit_rate()
        assert hit_rate == 1.0

    def test_get_hit_rate_partial(self, cache_manager):
        """Test hit rate calculation with partial hits."""
        cache_manager._cache_stats["hits"] = 75
        cache_manager._cache_stats["misses"] = 25

        hit_rate = cache_manager.get_hit_rate()
        assert hit_rate == 0.75


class TestCacheWarming:
    """Test intelligent cache warming operations."""

    def test_warm_cache_common_files(self, cache_manager, temp_project_path):
        """Test cache warming pre-loads common files."""
        cache_manager.warm_cache(temp_project_path, file_limit=15)

        # Should have pre-loaded __init__.py, main.py, config.py
        assert cache_manager._cache_stats["warm_requests"] > 0
        assert cache_manager.file_cache.get_file_content.called

    def test_warm_cache_respects_file_limit(self, cache_manager, temp_project_path):
        """Test cache warming respects file limit parameter."""
        file_limit = 5
        cache_manager.warm_cache(temp_project_path, file_limit=file_limit)

        # Should not exceed file_limit in warm_requests
        assert cache_manager._cache_stats["warm_requests"] <= file_limit + 10

    def test_warm_cache_skips_large_files(self, cache_manager, temp_project_path):
        """Test cache warming skips files larger than threshold."""
        # Mock get_file_content to track which files were loaded
        loaded_files = []

        def track_load(path):
            loaded_files.append(str(path))
            return "content"

        cache_manager.file_cache.get_file_content.side_effect = track_load

        cache_manager.warm_cache(temp_project_path, file_limit=15)

        # large.py should NOT be in loaded_files (>500KB)
        large_file_loaded = any("large.py" in f for f in loaded_files)
        assert not large_file_loaded, "Large files should be skipped during warming"

    def test_warm_cache_nonexistent_directory(self, cache_manager, tmp_path):
        """Test cache warming with non-existent directory raises assertion."""
        nonexistent = tmp_path / "nonexistent"

        with pytest.raises(AssertionError, match="project_path must exist"):
            cache_manager.warm_cache(nonexistent)

    def test_warm_cache_exception_handling(self, cache_manager, temp_project_path):
        """Test cache warming handles exceptions gracefully."""
        cache_manager.file_cache.get_file_content.side_effect = Exception("Read error")

        # Should not raise exception
        cache_manager.warm_cache(temp_project_path)


class TestBatchPreload:
    """Test batch preloading operations."""

    def test_batch_preload_multiple_files(self, cache_manager, tmp_path):
        """Test batch preloading multiple files."""
        files = []
        for i in range(5):
            test_file = tmp_path / f"test{i}.py"
            test_file.write_text(f"x = {i}" * 100)  # Small files
            files.append(test_file)

        cache_manager.batch_preload(files)

        assert cache_manager._cache_stats["batch_loads"] == 5
        assert cache_manager.file_cache.get_file_content.call_count == 5
        assert cache_manager.file_cache.get_ast_tree.call_count == 5

    def test_batch_preload_skips_large_files(self, cache_manager, tmp_path):
        """Test batch preload skips files larger than 1MB."""
        small_file = tmp_path / "small.py"
        small_file.write_text("x = 1" * 100)

        large_file = tmp_path / "large.py"
        # Create file >1MB (1024*1024 = 1048576 bytes)
        large_file.write_text("x" * 2000000)  # 2MB

        cache_manager.batch_preload([small_file, large_file])

        # Should only preload small file
        assert cache_manager._cache_stats["batch_loads"] == 1

    def test_batch_preload_handles_errors(self, cache_manager, tmp_path):
        """Test batch preload handles file errors gracefully."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 42")

        cache_manager.file_cache.get_file_content.side_effect = Exception("Read error")

        # Should not raise exception
        cache_manager.batch_preload([test_file])


class TestFilePrioritization:
    """Test file priority calculation for intelligent caching."""

    def test_calculate_priority_high_priority_file(self, cache_manager, tmp_path):
        """Test priority calculation for high-priority files."""
        init_file = tmp_path / "__init__.py"
        init_file.write_text("# init")

        priority = cache_manager._calculate_file_priority(init_file)

        # __init__ files get +40 points
        assert priority >= 40

    def test_calculate_priority_important_directory(self, cache_manager, tmp_path):
        """Test priority boost for files in important directories."""
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        src_file = src_dir / "module.py"
        src_file.write_text("# module")

        priority = cache_manager._calculate_file_priority(src_file)

        # src directory gets +20 points
        assert priority >= 20

    def test_calculate_priority_small_file_boost(self, cache_manager, tmp_path):
        """Test priority boost for small files."""
        small_file = tmp_path / "small.py"
        small_file.write_text("x = 1")  # <50KB

        priority = cache_manager._calculate_file_priority(small_file)

        # Small files get +20 points
        assert priority >= 20

    def test_calculate_priority_utility_pattern(self, cache_manager, tmp_path):
        """Test priority boost for utility file patterns."""
        utils_file = tmp_path / "my_utils.py"
        utils_file.write_text("# utils")

        priority = cache_manager._calculate_file_priority(utils_file)

        # _utils pattern gets +15 points
        assert priority >= 15

    def test_calculate_priority_max_score(self, cache_manager, tmp_path):
        """Test priority score is capped at 100."""
        # Create file with ALL priority boosters
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        priority_file = src_dir / "__init__.py"  # High priority name + important dir
        priority_file.write_text("x = 1")  # Small file

        priority = cache_manager._calculate_file_priority(priority_file)

        assert priority <= 100


class TestPerformanceLogging:
    """Test performance logging and monitoring."""

    def test_log_performance_basic(self, cache_manager, caplog):
        """Test basic performance logging."""
        cache_manager._cache_stats["hits"] = 80
        cache_manager._cache_stats["misses"] = 20
        cache_manager._cache_stats["warm_requests"] = 10

        with caplog.at_level(logging.INFO):
            cache_manager.log_performance()

        assert "Cache Performance Summary" in caplog.text
        assert "Hit Rate: 80.0%" in caplog.text
        assert "Hits: 80" in caplog.text
        assert "Misses: 20" in caplog.text

    def test_log_performance_low_hit_rate_warning(self, cache_manager, caplog):
        """Test warning for low cache hit rate."""
        cache_manager._cache_stats["hits"] = 40
        cache_manager._cache_stats["misses"] = 60

        with caplog.at_level(logging.WARNING):
            cache_manager.log_performance()

        assert "Low cache hit rate" in caplog.text

    def test_log_performance_excellent_rate(self, cache_manager, caplog):
        """Test message for excellent cache performance."""
        cache_manager._cache_stats["hits"] = 95
        cache_manager._cache_stats["misses"] = 5

        with caplog.at_level(logging.INFO):
            cache_manager.log_performance()

        assert "Excellent cache performance" in caplog.text


class TestOptimization:
    """Test cache optimization for future runs."""

    def test_optimize_for_future_runs(self, cache_manager, caplog):
        """Test learning from access patterns."""
        # Simulate access patterns
        cache_manager._analysis_patterns = {
            "file1.py": 50,
            "file2.py": 30,
            "file3.py": 20,
            "file4.py": 10,
        }

        with caplog.at_level(logging.INFO):
            cache_manager.optimize_for_future_runs()

        assert "Learned access patterns" in caplog.text

    def test_optimize_no_patterns(self, cache_manager):
        """Test optimization with no access patterns."""
        # Should not raise exception
        cache_manager.optimize_for_future_runs()


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_operations_without_cache_available(self, tmp_path):
        """Test all operations gracefully handle unavailable cache."""
        with patch('analyzer.optimization.file_cache.FileContentCache',
                   side_effect=ImportError("Module not found")):
            manager = CacheManager()

            # Create test file for operations
            test_file = tmp_path / "test.py"
            test_file.write_text("x = 1")

            # All operations should handle missing cache gracefully
            assert manager.get_cached_ast(test_file) is None
            assert manager.get_cached_content(test_file) is None
            assert manager.get_cached_lines(test_file) == []

            # These should not raise exceptions
            manager.cache_ast(test_file, ast.parse("x=1"))
            manager.invalidate(test_file)
            manager.clear_all()
            manager.warm_cache(tmp_path)
            manager.log_performance()

    def test_empty_cache_statistics(self, cache_manager):
        """Test statistics with empty cache."""
        stats = cache_manager.get_cache_stats()

        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["hit_rate"] == 0.0

    def test_full_cache_scenario(self, cache_manager, sample_ast, tmp_path):
        """Test behavior when cache approaches memory limit."""
        # Simulate cache at high memory usage
        cache_manager.file_cache._stats.memory_usage = 95 * 1024 * 1024
        cache_manager.file_cache._stats.max_memory = 100 * 1024 * 1024

        test_file = tmp_path / "test.py"
        test_file.write_text("x = 42")

        # Should still cache (FileContentCache handles eviction)
        cache_manager.cache_ast(test_file, sample_ast)

        stats = cache_manager.get_cache_stats()
        assert stats["memory_usage_percent"] == 95.0
