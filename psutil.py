"""Minimal psutil compatibility layer for test environments."""
from __future__ import annotations

from collections import namedtuple
from dataclasses import dataclass
import os
import time
from typing import Optional

__all__ = [
    "Process",
    "cpu_percent",
    "cpu_freq",
    "virtual_memory",
    "disk_io_counters",
    "getloadavg",
    "NoSuchProcess",
    "AccessDenied",
]


class Error(Exception):
    """Base exception for psutil compatibility errors."""


class NoSuchProcess(Error):
    """Raised when the requested process does not exist."""

    def __init__(self, pid: int):
        super().__init__(pid)
        self.pid = pid


class AccessDenied(Error):
    """Raised when the requested operation is not permitted."""

    def __init__(self, pid: int):
        super().__init__(pid)
        self.pid = pid


MemoryInfo = namedtuple("MemoryInfo", ["rss", "vms"])


@dataclass
class VirtualMemory:
    total: int
    available: int
    used: int
    percent: float


@dataclass
class DiskIOCounters:
    read_bytes: int
    write_bytes: int


@dataclass
class CpuFreq:
    current: float
    min: float
    max: float


_last_cpu_snapshot: Optional[tuple[int, int, float]] = None


def _read_system_cpu_times() -> tuple[int, int]:
    """Read aggregate CPU times (total jiffies, idle jiffies)."""
    try:
        with open("/proc/stat", encoding="utf-8") as proc_stat:
            first_line = proc_stat.readline()
    except OSError as exc:
        raise AccessDenied(os.getpid()) from exc

    if not first_line.startswith("cpu "):
        return 0, 0

    fields = [int(value) for value in first_line.split()[1:]]
    total = sum(fields)
    idle = fields[3] if len(fields) > 3 else 0
    return total, idle


def cpu_percent(interval: Optional[float] = None) -> float:
    """Approximate system-wide CPU utilization percentage."""
    global _last_cpu_snapshot

    if interval:
        time.sleep(interval)

    total, idle = _read_system_cpu_times()
    now = time.time()

    if _last_cpu_snapshot is None:
        _last_cpu_snapshot = (total, idle, now)
        return 0.0

    prev_total, prev_idle, prev_time = _last_cpu_snapshot
    delta_total = total - prev_total
    delta_idle = idle - prev_idle
    elapsed = now - prev_time

    _last_cpu_snapshot = (total, idle, now)

    if delta_total <= 0 or elapsed <= 0:
        return 0.0

    busy = delta_total - delta_idle
    percent = busy / delta_total * 100.0
    return max(0.0, min(100.0, percent))


def _read_meminfo() -> dict[str, int]:
    """Parse /proc/meminfo into a dictionary of byte values."""
    meminfo: dict[str, int] = {}
    try:
        with open("/proc/meminfo", encoding="utf-8") as meminfo_file:
            for line in meminfo_file:
                if ":" not in line:
                    continue
                key, value = line.split(":", 1)
                parts = value.strip().split()
                if not parts:
                    continue
                amount = int(parts[0])
                # Values are reported in kB
                if parts[1:] and parts[1] == "kB":
                    amount *= 1024
                meminfo[key] = amount
    except OSError:
        pass
    return meminfo


def virtual_memory() -> VirtualMemory:
    """Return a snapshot of system memory usage."""
    meminfo = _read_meminfo()
    total = meminfo.get("MemTotal", 0)
    available = meminfo.get("MemAvailable", meminfo.get("MemFree", 0))
    used = max(0, total - available)
    percent = (used / total * 100.0) if total else 0.0
    return VirtualMemory(total=total, available=available, used=used, percent=percent)


def _read_process_io(pid: int) -> tuple[int, int]:
    """Read per-process IO counters from /proc."""
    read_bytes = write_bytes = 0
    try:
        with open(f"/proc/{pid}/io", encoding="utf-8") as io_file:
            for line in io_file:
                if ":" not in line:
                    continue
                key, value = line.split(":", 1)
                if key.strip() == "read_bytes":
                    read_bytes = int(value.strip())
                elif key.strip() == "write_bytes":
                    write_bytes = int(value.strip())
    except FileNotFoundError:
        raise NoSuchProcess(pid)
    except OSError:
        pass
    return read_bytes, write_bytes


def disk_io_counters() -> DiskIOCounters:
    """Return simple disk IO counters for the current process."""
    pid = os.getpid()
    try:
        read_bytes, write_bytes = _read_process_io(pid)
    except NoSuchProcess:
        read_bytes = write_bytes = 0
    return DiskIOCounters(read_bytes=read_bytes, write_bytes=write_bytes)


def _read_cpu_mhz() -> float:
    """Attempt to read current CPU frequency in MHz."""
    # Try cpufreq scaling interface first
    scaling_path = "/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq"
    try:
        with open(scaling_path, encoding="utf-8") as freq_file:
            value = freq_file.read().strip()
            if value:
                return float(value) / 1000.0
    except OSError:
        pass

    # Fallback to /proc/cpuinfo
    try:
        with open("/proc/cpuinfo", encoding="utf-8") as cpuinfo:
            for line in cpuinfo:
                if line.lower().startswith("cpu mhz"):
                    parts = line.split(":", 1)
                    if len(parts) == 2:
                        try:
                            return float(parts[1].strip())
                        except ValueError:
                            continue
    except OSError:
        pass

    return 0.0


def cpu_freq() -> CpuFreq:
    """Return approximate CPU frequency information."""
    current = _read_cpu_mhz()
    return CpuFreq(current=current, min=0.0, max=0.0)


def getloadavg():
    """Return system load averages if available."""
    try:
        return os.getloadavg()
    except (AttributeError, OSError):
        return (0.0, 0.0, 0.0)


class Process:
    """Minimal representation of a system process."""

    def __init__(self, pid: Optional[int] = None):
        self.pid = pid or os.getpid()
        if self.pid <= 0:
            raise NoSuchProcess(self.pid)
        proc_path = f"/proc/{self.pid}"
        if not os.path.exists(proc_path):
            raise NoSuchProcess(self.pid)
        self._last_cpu_sample: Optional[tuple[float, float]] = None

    def _read_memory(self) -> MemoryInfo:
        status_path = f"/proc/{self.pid}/status"
        rss = vms = 0
        try:
            with open(status_path, encoding="utf-8") as status_file:
                for line in status_file:
                    if line.startswith("VmRSS:"):
                        parts = line.split()
                        rss = int(parts[1]) * 1024
                    elif line.startswith("VmSize:"):
                        parts = line.split()
                        vms = int(parts[1]) * 1024
        except FileNotFoundError as exc:
            raise NoSuchProcess(self.pid) from exc
        return MemoryInfo(rss=rss, vms=vms)

    def _read_cpu_times(self) -> float:
        stat_path = f"/proc/{self.pid}/stat"
        try:
            with open(stat_path, encoding="utf-8") as stat_file:
                contents = stat_file.read().strip()
        except FileNotFoundError as exc:
            raise NoSuchProcess(self.pid) from exc

        if not contents:
            return 0.0

        parts = contents.split()
        if len(parts) < 17:
            return 0.0

        try:
            utime = float(parts[13])
            stime = float(parts[14])
        except ValueError:
            return 0.0

        clk_tck = os.sysconf(os.sysconf_names.get("SC_CLK_TCK", 100))
        return (utime + stime) / float(clk_tck)

    def is_running(self) -> bool:
        return os.path.exists(f"/proc/{self.pid}")

    def memory_info(self) -> MemoryInfo:
        return self._read_memory()

    def memory_percent(self) -> float:
        mem = virtual_memory()
        info = self.memory_info()
        return (info.rss / mem.total * 100.0) if mem.total else 0.0

    def cpu_percent(self, interval: Optional[float] = None) -> float:
        if interval:
            time.sleep(interval)

        now = time.time()
        cpu_time = self._read_cpu_times()

        if self._last_cpu_sample is None:
            self._last_cpu_sample = (cpu_time, now)
            return 0.0

        last_cpu_time, last_timestamp = self._last_cpu_sample
        elapsed = now - last_timestamp
        delta = cpu_time - last_cpu_time

        self._last_cpu_sample = (cpu_time, now)

        if elapsed <= 0 or delta < 0:
            return 0.0

        cpu_count = os.cpu_count() or 1
        percent = (delta / elapsed) * 100.0 / cpu_count
        return max(0.0, min(100.0, percent))


__all__ += ["MemoryInfo", "VirtualMemory", "DiskIOCounters", "CpuFreq"]

