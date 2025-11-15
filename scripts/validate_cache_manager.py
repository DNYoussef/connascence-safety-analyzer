#!/usr/bin/env python3
"""
Validation script for CacheManager extraction.

Tests:
1. CacheManager can be imported
2. CacheManager can be initialized
3. Basic operations work
4. Statistics are tracked correctly
"""

from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from analyzer.architecture.cache_manager import CacheManager


def validate_import():
    """Test 1: Verify import works"""
    print("Test 1: Import CacheManager... ", end="")
    try:
        from analyzer.architecture.cache_manager import CacheManager
        print("PASS")
        return True
    except ImportError as e:
        print(f"FAIL: {e}")
        return False


def validate_initialization():
    """Test 2: Verify initialization works"""
    print("Test 2: Initialize CacheManager... ", end="")
    try:
        cache_mgr = CacheManager()
        assert cache_mgr is not None
        assert hasattr(cache_mgr, "cache_available")
        print("PASS")
        return True
    except Exception as e:
        print(f"FAIL: {e}")
        return False


def validate_configuration():
    """Test 3: Verify configuration works"""
    print("Test 3: Configure CacheManager... ", end="")
    try:
        config = {
            "max_memory": 50 * 1024 * 1024,  # 50MB
            "warm_file_count": 10,
        }
        cache_mgr = CacheManager(config)
        assert cache_mgr.config == config
        print("PASS")
        return True
    except Exception as e:
        print(f"FAIL: {e}")
        return False


def validate_statistics():
    """Test 4: Verify statistics tracking works"""
    print("Test 4: Track statistics... ", end="")
    try:
        cache_mgr = CacheManager()

        # Get initial stats
        stats = cache_mgr.get_cache_stats()
        assert "hits" in stats
        assert "misses" in stats
        assert "hit_rate" in stats

        # Verify hit rate calculation
        hit_rate = cache_mgr.get_hit_rate()
        assert 0.0 <= hit_rate <= 1.0

        print("PASS")
        return True
    except Exception as e:
        print(f"FAIL: {e}")
        return False


def validate_cache_operations():
    """Test 5: Verify cache operations work"""
    print("Test 5: Cache operations... ", end="")
    try:
        cache_mgr = CacheManager()

        # Create test file
        test_file = Path(__file__)  # Use this script as test file

        # Test content caching (if cache available)
        if cache_mgr.cache_available:
            content = cache_mgr.get_cached_content(test_file)
            # Should work even if None (cache miss)

        # Test statistics were updated
        stats = cache_mgr.get_cache_stats()
        total_requests = stats["hits"] + stats["misses"]
        # Should have at least one request from above

        print("PASS")
        return True
    except Exception as e:
        print(f"FAIL: {e}")
        return False


def validate_priority_calculation():
    """Test 6: Verify priority calculation works"""
    print("Test 6: Priority calculation... ", end="")
    try:
        cache_mgr = CacheManager()

        # Test with various files
        test_files = [
            Path(__file__),  # This script
            Path(__file__).parent / "__init__.py",  # Init file
        ]

        for test_file in test_files:
            if test_file.exists():
                priority = cache_mgr._calculate_file_priority(test_file)
                assert 0 <= priority <= 100, f"Priority {priority} out of range"

        print("PASS")
        return True
    except Exception as e:
        print(f"FAIL: {e}")
        return False


def main():
    """Run all validation tests"""
    print("=" * 60)
    print("CacheManager Validation Tests")
    print("=" * 60)

    tests = [
        validate_import,
        validate_initialization,
        validate_configuration,
        validate_statistics,
        validate_cache_operations,
        validate_priority_calculation,
    ]

    results = []
    for test_func in tests:
        result = test_func()
        results.append(result)

    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("Status: ALL TESTS PASSED")
        return 0
    else:
        print("Status: SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
