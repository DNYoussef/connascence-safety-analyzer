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
Dashboard metrics collection and analysis.

Provides historical tracking, trend analysis, and performance
metrics for the connascence analysis dashboard.
"""

from datetime import datetime, timedelta
import json
from pathlib import Path
import sqlite3
import statistics
from typing import Any, Dict, List, Optional


class DashboardMetrics:
    """Dashboard metrics collection and storage."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or Path.home() / ".connascence" / "dashboard.db"
        self.db_path.parent.mkdir(exist_ok=True)
        self._init_database()

    def _init_database(self):
        """Initialize SQLite database for metrics storage."""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS scan_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    project_path TEXT NOT NULL,
                    policy_preset TEXT NOT NULL,
                    total_violations INTEGER NOT NULL,
                    critical_count INTEGER DEFAULT 0,
                    high_count INTEGER DEFAULT 0,
                    medium_count INTEGER DEFAULT 0,
                    low_count INTEGER DEFAULT 0,
                    connascence_index REAL DEFAULT 0.0,
                    violations_by_type TEXT, -- JSON
                    violations_by_file TEXT, -- JSON
                    analysis_time REAL,
                    file_count INTEGER DEFAULT 0
                )
            """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    operation_type TEXT NOT NULL,
                    duration REAL NOT NULL,
                    file_count INTEGER,
                    violation_count INTEGER,
                    memory_usage REAL
                )
            """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS violation_trends (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    connascence_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    count INTEGER NOT NULL,
                    UNIQUE(date, connascence_type, severity)
                )
            """
            )

            conn.commit()

    def record_scan(self, scan_results: Dict[str, Any]) -> int:
        """Record scan results in database."""
        with sqlite3.connect(str(self.db_path)) as conn:
            summary = scan_results.get("summary", {})

            cursor = conn.execute(
                """
                INSERT INTO scan_results (
                    timestamp, project_path, policy_preset, total_violations,
                    critical_count, high_count, medium_count, low_count,
                    connascence_index, violations_by_type, violations_by_file,
                    analysis_time, file_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    scan_results.get("timestamp", datetime.now().isoformat()),
                    scan_results.get("project_path", ""),
                    scan_results.get("policy_preset", ""),
                    summary.get("total_violations", 0),
                    summary.get("critical_count", 0),
                    summary.get("high_count", 0),
                    summary.get("medium_count", 0),
                    summary.get("low_count", 0),
                    summary.get("connascence_index", 0.0),
                    json.dumps(summary.get("violations_by_type", {})),
                    json.dumps(summary.get("violations_by_file", {})),
                    scan_results.get("analysis_time"),
                    summary.get("file_count", 0),
                ),
            )

            scan_id = cursor.lastrowid

            # Record daily violation trends
            self._update_violation_trends(scan_results.get("violations", []))

            conn.commit()
            return scan_id

    def record_performance(
        self,
        operation_type: str,
        duration: float,
        file_count: Optional[int] = None,
        violation_count: Optional[int] = None,
        memory_usage: Optional[float] = None,
    ):
        """Record performance metrics."""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute(
                """
                INSERT INTO performance_metrics (
                    timestamp, operation_type, duration, file_count,
                    violation_count, memory_usage
                ) VALUES (?, ?, ?, ?, ?, ?)
            """,
                (datetime.now().isoformat(), operation_type, duration, file_count, violation_count, memory_usage),
            )
            conn.commit()

    def get_trends(self, days: int = 30) -> Dict[str, Any]:
        """Get trend data for specified number of days."""
        start_date = (datetime.now() - timedelta(days=days)).isoformat()

        with sqlite3.connect(str(self.db_path)) as conn:
            # Get main trends
            cursor = conn.execute(
                """
                SELECT timestamp, total_violations, connascence_index,
                       critical_count, high_count, medium_count, low_count
                FROM scan_results
                WHERE timestamp >= ?
                ORDER BY timestamp
            """,
                (start_date,),
            )

            main_trends = []
            for row in cursor.fetchall():
                main_trends.append(
                    {
                        "timestamp": row[0],
                        "total_violations": row[1],
                        "connascence_index": row[2],
                        "critical_count": row[3],
                        "high_count": row[4],
                        "medium_count": row[5],
                        "low_count": row[6],
                    }
                )

            # Get violation type trends
            cursor = conn.execute(
                """
                SELECT date, connascence_type, SUM(count) as total_count
                FROM violation_trends
                WHERE date >= ?
                GROUP BY date, connascence_type
                ORDER BY date, connascence_type
            """,
                (start_date,),
            )

            type_trends = {}
            for row in cursor.fetchall():
                date, conn_type, count = row
                if date not in type_trends:
                    type_trends[date] = {}
                type_trends[date][conn_type] = count

            return {"trends": main_trends, "type_trends": type_trends, "period_days": days}

    def get_summary_stats(self, days: int = 7) -> Dict[str, Any]:
        """Get summary statistics for recent period."""
        start_date = (datetime.now() - timedelta(days=days)).isoformat()

        with sqlite3.connect(str(self.db_path)) as conn:
            # Get recent scan stats
            cursor = conn.execute(
                """
                SELECT total_violations, connascence_index, analysis_time
                FROM scan_results
                WHERE timestamp >= ?
            """,
                (start_date,),
            )

            scans = cursor.fetchall()

            if not scans:
                return {
                    "scans_count": 0,
                    "avg_violations": 0,
                    "avg_connascence_index": 0,
                    "avg_analysis_time": 0,
                    "trend_direction": "stable",
                }

            violations = [s[0] for s in scans]
            indices = [s[1] for s in scans]
            times = [s[2] for s in scans if s[2] is not None]

            # Calculate trend direction
            trend_direction = "stable"
            if len(indices) >= 2:
                recent_avg = statistics.mean(indices[-3:]) if len(indices) >= 3 else indices[-1]
                older_avg = statistics.mean(indices[:-3]) if len(indices) >= 6 else indices[0]

                if recent_avg > older_avg * 1.1:
                    trend_direction = "increasing"
                elif recent_avg < older_avg * 0.9:
                    trend_direction = "decreasing"

            return {
                "scans_count": len(scans),
                "avg_violations": statistics.mean(violations),
                "avg_connascence_index": statistics.mean(indices),
                "avg_analysis_time": statistics.mean(times) if times else 0,
                "trend_direction": trend_direction,
                "max_violations": max(violations),
                "min_violations": min(violations),
            }

    def get_performance_stats(self, operation_type: Optional[str] = None) -> Dict[str, Any]:
        """Get performance statistics."""
        with sqlite3.connect(str(self.db_path)) as conn:
            where_clause = ""
            params = []

            if operation_type:
                where_clause = "WHERE operation_type = ?"
                params.append(operation_type)

            cursor = conn.execute(
                f"""
                SELECT operation_type, duration, file_count, violation_count
                FROM performance_metrics
                {where_clause}
                ORDER BY timestamp DESC
                LIMIT 100
            """,
                params,
            )

            metrics = cursor.fetchall()

            if not metrics:
                return {"operations": 0}

            durations = [m[1] for m in metrics]

            stats = {
                "operations": len(metrics),
                "avg_duration": statistics.mean(durations),
                "min_duration": min(durations),
                "max_duration": max(durations),
                "p95_duration": self._percentile(durations, 95),
            }

            # File processing rate
            file_metrics = [(m[1], m[2]) for m in metrics if m[2] is not None]
            if file_metrics:
                file_rates = [fc / dur for dur, fc in file_metrics if dur > 0]
                if file_rates:
                    stats["avg_files_per_second"] = statistics.mean(file_rates)

            # Violation detection rate
            violation_metrics = [(m[1], m[3]) for m in metrics if m[3] is not None]
            if violation_metrics:
                violation_rates = [vc / dur for dur, vc in violation_metrics if dur > 0]
                if violation_rates:
                    stats["avg_violations_per_second"] = statistics.mean(violation_rates)

            return stats

    def get_top_violation_files(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get files with most violations."""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.execute(
                """
                SELECT violations_by_file
                FROM scan_results
                ORDER BY timestamp DESC
                LIMIT 1
            """
            )

            result = cursor.fetchone()
            if not result or not result[0]:
                return []

            try:
                violations_by_file = json.loads(result[0])

                # Sort by violation count
                sorted_files = sorted(violations_by_file.items(), key=lambda x: x[1], reverse=True)

                return [{"file_path": file_path, "violation_count": count} for file_path, count in sorted_files[:limit]]
            except (json.JSONDecodeError, TypeError):
                return []

    def get_connascence_type_distribution(self) -> Dict[str, int]:
        """Get distribution of connascence types from recent scans."""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.execute(
                """
                SELECT violations_by_type
                FROM scan_results
                ORDER BY timestamp DESC
                LIMIT 5
            """
            )

            type_counts = {}
            for row in cursor.fetchall():
                if row[0]:
                    try:
                        violations_by_type = json.loads(row[0])
                        for conn_type, count in violations_by_type.items():
                            type_counts[conn_type] = type_counts.get(conn_type, 0) + count
                    except (json.JSONDecodeError, TypeError):
                        continue

            return type_counts

    def _update_violation_trends(self, violations: List[Dict]):
        """Update daily violation trends."""
        if not violations:
            return

        date_str = datetime.now().date().isoformat()

        # Count violations by type and severity
        type_severity_counts = {}
        for violation in violations:
            conn_type = violation.get("connascence_type", "Unknown")
            severity = violation.get("severity", "medium")
            key = (conn_type, severity)
            type_severity_counts[key] = type_severity_counts.get(key, 0) + 1

        # Store in database
        with sqlite3.connect(str(self.db_path)) as conn:
            for (conn_type, severity), count in type_severity_counts.items():
                conn.execute(
                    """
                    INSERT OR REPLACE INTO violation_trends
                    (date, connascence_type, severity, count)
                    VALUES (?, ?, ?, ?)
                """,
                    (date_str, conn_type, severity, count),
                )
            conn.commit()

    def _percentile(self, data: List[float], percentile: float) -> float:
        """Calculate percentile value."""
        if not data:
            return 0.0

        sorted_data = sorted(data)
        k = (len(sorted_data) - 1) * (percentile / 100)
        f = int(k)
        c = k - f

        if f == len(sorted_data) - 1:
            return sorted_data[f]

        return sorted_data[f] * (1 - c) + sorted_data[f + 1] * c

    def cleanup_old_data(self, days_to_keep: int = 90):
        """Clean up old metrics data."""
        cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).isoformat()

        with sqlite3.connect(str(self.db_path)) as conn:
            # Clean up scan results
            cursor = conn.execute("DELETE FROM scan_results WHERE timestamp < ?", (cutoff_date,))
            scan_rows_deleted = cursor.rowcount

            # Clean up performance metrics
            cursor = conn.execute("DELETE FROM performance_metrics WHERE timestamp < ?", (cutoff_date,))
            perf_rows_deleted = cursor.rowcount

            # Clean up violation trends (keep daily aggregates longer)
            trend_cutoff = (datetime.now() - timedelta(days=days_to_keep * 2)).isoformat()
            cursor = conn.execute("DELETE FROM violation_trends WHERE date < ?", (trend_cutoff,))
            trend_rows_deleted = cursor.rowcount

            conn.commit()

            return {
                "scan_results_deleted": scan_rows_deleted,
                "performance_metrics_deleted": perf_rows_deleted,
                "violation_trends_deleted": trend_rows_deleted,
            }

    def export_metrics(self, format: str = "json", days: int = 30) -> str:
        """Export metrics data in specified format."""
        data = {
            "export_timestamp": datetime.now().isoformat(),
            "period_days": days,
            "trends": self.get_trends(days),
            "summary_stats": self.get_summary_stats(days),
            "performance_stats": self.get_performance_stats(),
            "top_violation_files": self.get_top_violation_files(),
            "type_distribution": self.get_connascence_type_distribution(),
        }

        if format == "json":
            return json.dumps(data, indent=2)
        elif format == "csv":
            return self._export_csv(data)
        else:
            raise ValueError(f"Unsupported export format: {format}")

    def _export_csv(self, data: Dict) -> str:
        """Export data as CSV format."""
        import csv
        import io

        output = io.StringIO()
        writer = csv.writer(output)

        # Write trends data
        writer.writerow(["Date", "Total Violations", "Connascence Index", "Critical", "High", "Medium", "Low"])
        for trend in data["trends"]["trends"]:
            writer.writerow(
                [
                    trend["timestamp"][:10],  # Date only
                    trend["total_violations"],
                    trend["connascence_index"],
                    trend["critical_count"],
                    trend["high_count"],
                    trend["medium_count"],
                    trend["low_count"],
                ]
            )

        return output.getvalue()
