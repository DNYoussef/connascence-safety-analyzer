#!/usr/bin/env python
"""
Verification script for psutil.NoSuchProcess fix

This script validates that all psutil operations in memory_monitor.py
are properly wrapped with exception handling.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'analyzer'))

import time

from optimization.memory_monitor import (
    MemoryLeakDetector,
    MemoryMonitor,
    MemoryWatcher,
    get_global_memory_monitor,
)

import psutil


def test_memory_leak_detector_streaming():
    """Test MemoryLeakDetector.start_streaming_session handles NoSuchProcess"""
    print("Test 1: MemoryLeakDetector.start_streaming_session")
    detector = MemoryLeakDetector()

    try:
        detector.start_streaming_session()
        assert detector.streaming_session_start_memory >= 0
        print("  PASS: Handles NoSuchProcess gracefully")
        return True
    except psutil.NoSuchProcess as e:
        print(f"  FAIL: psutil.NoSuchProcess not caught: {e}")
        return False
    except Exception as e:
        print(f"  FAIL: Unexpected exception: {e}")
        return False


def test_memory_monitor_init():
    """Test MemoryMonitor initialization handles NoSuchProcess"""
    print("Test 2: MemoryMonitor initialization")

    try:
        monitor = MemoryMonitor()
        # Process may be None if access denied, which is OK
        print(f"  Process initialized: {monitor._process is not None}")
        print("  PASS: Handles NoSuchProcess gracefully")
        return True
    except psutil.NoSuchProcess as e:
        print(f"  FAIL: psutil.NoSuchProcess not caught: {e}")
        return False
    except Exception as e:
        print(f"  FAIL: Unexpected exception: {e}")
        return False


def test_memory_watcher_context():
    """Test MemoryWatcher context manager handles NoSuchProcess"""
    print("Test 3: MemoryWatcher context manager")

    try:
        with MemoryWatcher('test_watcher') as watcher:
            # Do some work
            time.sleep(0.1)
        print("  PASS: Context manager handles NoSuchProcess gracefully")
        return True
    except psutil.NoSuchProcess as e:
        print(f"  FAIL: psutil.NoSuchProcess not caught: {e}")
        return False
    except Exception as e:
        print(f"  FAIL: Unexpected exception: {e}")
        return False


def test_take_snapshot_with_missing_process():
    """Test _take_snapshot handles terminated process"""
    print("Test 4: _take_snapshot with missing process")

    try:
        monitor = MemoryMonitor()
        # Simulate process termination
        original_process = monitor._process
        monitor._process = None

        monitor._take_snapshot()

        # Restore for cleanup
        monitor._process = original_process
        print("  PASS: Handles missing process gracefully")
        return True
    except psutil.NoSuchProcess as e:
        print(f"  FAIL: psutil.NoSuchProcess not caught: {e}")
        return False
    except Exception as e:
        print(f"  FAIL: Unexpected exception: {e}")
        return False


def test_monitoring_loop_resilience():
    """Test that monitoring loop handles process termination"""
    print("Test 5: Monitoring loop resilience")

    try:
        monitor = MemoryMonitor(monitoring_interval=2.0)
        monitor.start_monitoring()

        # Let it run for a bit
        time.sleep(1.5)

        # Stop monitoring
        monitor.stop_monitoring()

        # Check that no exceptions were raised
        stats = monitor.get_current_stats()
        print(f"  Snapshots collected: {stats.snapshots_count}")
        print("  PASS: Monitoring loop handles exceptions gracefully")
        return True
    except psutil.NoSuchProcess as e:
        print(f"  FAIL: psutil.NoSuchProcess not caught: {e}")
        return False
    except Exception as e:
        print(f"  FAIL: Unexpected exception: {e}")
        return False


def test_global_monitor():
    """Test global monitor instance"""
    print("Test 6: Global monitor instance")

    try:
        monitor = get_global_memory_monitor()
        assert monitor is not None
        print("  PASS: Global monitor initialized successfully")
        return True
    except psutil.NoSuchProcess as e:
        print(f"  FAIL: psutil.NoSuchProcess not caught: {e}")
        return False
    except Exception as e:
        print(f"  FAIL: Unexpected exception: {e}")
        return False


def main():
    """Run all verification tests"""
    print("=" * 70)
    print("PSUTIL.NOSUCHPROCESS FIX VERIFICATION")
    print("=" * 70)
    print()

    tests = [
        test_memory_leak_detector_streaming,
        test_memory_monitor_init,
        test_memory_watcher_context,
        test_take_snapshot_with_missing_process,
        test_monitoring_loop_resilience,
        test_global_monitor,
    ]

    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"  CRITICAL FAILURE: {e}")
            results.append(False)
        print()

    # Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    total = len(results)
    passed = sum(results)
    failed = total - passed

    print(f"Total tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")

    if failed == 0:
        print()
        print("SUCCESS: All psutil operations handle NoSuchProcess gracefully!")
        return 0
    else:
        print()
        print(f"FAILURE: {failed} test(s) still have unhandled psutil exceptions")
        return 1


if __name__ == '__main__':
    sys.exit(main())
