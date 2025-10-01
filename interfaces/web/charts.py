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
Chart generation for connascence dashboard.

Provides chart data generation for various visualizations
including trends, distributions, and comparative analysis.
"""

from datetime import datetime
from typing import Any, Dict


class ChartGenerator:
    """Generate chart data for dashboard visualizations."""

    def __init__(self):
        self.color_schemes = {
            "severity": {"critical": "#ef4444", "high": "#f59e0b", "medium": "#3b82f6", "low": "#10b981"},
            "connascence_types": {
                "CoM": "#8b5cf6",  # Purple - Meaning
                "CoP": "#f59e0b",  # Orange - Position
                "CoT": "#06b6d4",  # Cyan - Type
                "CoA": "#ef4444",  # Red - Algorithm
                "CoN": "#84cc16",  # Lime - Name
                "CoE": "#f97316",  # Orange - Execution
                "CoTi": "#6366f1",  # Indigo - Timing
                "CoV": "#ec4899",  # Pink - Value
                "CoI": "#14b8a6",  # Teal - Identity
            },
            "quality": ["#10b981", "#f59e0b", "#ef4444"],  # Good, Warning, Critical
            "gradient": ["#3b82f6", "#8b5cf6", "#ec4899", "#f59e0b"],
        }

    def generate_chart(self, chart_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate chart data for specified chart type."""
        generators = {
            "severity_distribution": self._generate_severity_distribution,
            "type_distribution": self._generate_type_distribution,
            "trend_line": self._generate_trend_line,
            "file_heatmap": self._generate_file_heatmap,
            "complexity_scatter": self._generate_complexity_scatter,
            "timeline": self._generate_timeline,
            "comparison": self._generate_comparison,
            "radar": self._generate_radar_chart,
        }

        generator = generators.get(chart_type)
        if not generator:
            raise ValueError(f"Unknown chart type: {chart_type}")

        return generator(data)

    def _generate_severity_distribution(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate severity distribution pie/doughnut chart."""
        summary = data.get("summary", {})

        return {
            "type": "doughnut",
            "data": {
                "labels": ["Critical", "High", "Medium", "Low"],
                "datasets": [
                    {
                        "data": [
                            summary.get("critical_count", 0),
                            summary.get("high_count", 0),
                            summary.get("medium_count", 0),
                            summary.get("low_count", 0),
                        ],
                        "backgroundColor": [
                            self.color_schemes["severity"]["critical"],
                            self.color_schemes["severity"]["high"],
                            self.color_schemes["severity"]["medium"],
                            self.color_schemes["severity"]["low"],
                        ],
                        "borderWidth": 2,
                        "borderColor": "#ffffff",
                    }
                ],
            },
            "options": {
                "responsive": True,
                "plugins": {
                    "legend": {"position": "bottom"},
                    "tooltip": {
                        "callbacks": {
                            "label": 'function(context) { return context.label + ": " + context.parsed + " violations"; }'
                        }
                    },
                },
            },
        }

    def _generate_type_distribution(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate connascence type distribution bar chart."""
        summary = data.get("summary", {})
        violations_by_type = summary.get("violations_by_type", {})

        if not violations_by_type:
            return self._empty_chart("bar", "No violation types to display")

        types = list(violations_by_type.keys())
        counts = list(violations_by_type.values())
        colors = [self.color_schemes["connascence_types"].get(t, "#64748b") for t in types]

        return {
            "type": "bar",
            "data": {
                "labels": types,
                "datasets": [
                    {
                        "label": "Violations",
                        "data": counts,
                        "backgroundColor": colors,
                        "borderColor": colors,
                        "borderWidth": 1,
                    }
                ],
            },
            "options": {
                "responsive": True,
                "scales": {"y": {"beginAtZero": True, "ticks": {"precision": 0}}},
                "plugins": {
                    "legend": {"display": False},
                    "tooltip": {
                        "callbacks": {
                            "label": 'function(context) { return context.label + ": " + context.parsed.y + " violations"; }'
                        }
                    },
                },
            },
        }

    def _generate_trend_line(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate trend line chart for connascence index over time."""
        trends = data.get("trends", [])

        if not trends:
            return self._empty_chart("line", "No trend data available")

        # Sort by timestamp
        sorted_trends = sorted(trends, key=lambda x: x.get("timestamp", ""))

        labels = []
        index_values = []
        violation_counts = []

        for trend in sorted_trends:
            timestamp = trend.get("timestamp", "")
            try:
                date = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                labels.append(date.strftime("%m/%d"))
            except:
                labels.append(timestamp[:10])  # Fallback to date part

            index_values.append(trend.get("connascence_index", 0))
            violation_counts.append(trend.get("total_violations", 0))

        return {
            "type": "line",
            "data": {
                "labels": labels,
                "datasets": [
                    {
                        "label": "Connascence Index",
                        "data": index_values,
                        "borderColor": self.color_schemes["gradient"][0],
                        "backgroundColor": self.color_schemes["gradient"][0] + "20",
                        "borderWidth": 2,
                        "fill": True,
                        "tension": 0.4,
                        "yAxisID": "y",
                    },
                    {
                        "label": "Total Violations",
                        "data": violation_counts,
                        "borderColor": self.color_schemes["gradient"][1],
                        "backgroundColor": self.color_schemes["gradient"][1] + "20",
                        "borderWidth": 2,
                        "fill": False,
                        "tension": 0.4,
                        "yAxisID": "y1",
                    },
                ],
            },
            "options": {
                "responsive": True,
                "interaction": {"mode": "index", "intersect": False},
                "scales": {
                    "x": {"display": True, "title": {"display": True, "text": "Date"}},
                    "y": {
                        "type": "linear",
                        "display": True,
                        "position": "left",
                        "title": {"display": True, "text": "Connascence Index"},
                    },
                    "y1": {
                        "type": "linear",
                        "display": True,
                        "position": "right",
                        "title": {"display": True, "text": "Violations"},
                        "grid": {"drawOnChartArea": False},
                    },
                },
                "plugins": {"tooltip": {"mode": "index", "intersect": False}},
            },
        }

    def _generate_file_heatmap(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate file violation heatmap."""
        summary = data.get("summary", {})
        violations_by_file = summary.get("violations_by_file", {})

        if not violations_by_file:
            return self._empty_chart("bar", "No file data available")

        # Sort files by violation count and take top 15
        sorted_files = sorted(violations_by_file.items(), key=lambda x: x[1], reverse=True)[:15]

        file_names = [self._shorten_filename(f[0]) for f in sorted_files]
        violation_counts = [f[1] for f in sorted_files]

        # Generate colors based on violation count
        max_violations = max(violation_counts) if violation_counts else 1
        colors = []
        for count in violation_counts:
            intensity = count / max_violations
            if intensity > 0.7:
                colors.append(self.color_schemes["severity"]["critical"])
            elif intensity > 0.4:
                colors.append(self.color_schemes["severity"]["high"])
            elif intensity > 0.2:
                colors.append(self.color_schemes["severity"]["medium"])
            else:
                colors.append(self.color_schemes["severity"]["low"])

        return {
            "type": "bar",
            "data": {
                "labels": file_names,
                "datasets": [
                    {
                        "label": "Violations per File",
                        "data": violation_counts,
                        "backgroundColor": colors,
                        "borderColor": colors,
                        "borderWidth": 1,
                    }
                ],
            },
            "options": {
                "indexAxis": "y",  # Horizontal bar chart
                "responsive": True,
                "scales": {"x": {"beginAtZero": True, "ticks": {"precision": 0}}},
                "plugins": {
                    "legend": {"display": False},
                    "tooltip": {
                        "callbacks": {
                            "title": "function(context) { return context[0].label; }",
                            "label": 'function(context) { return "Violations: " + context.parsed.x; }',
                        }
                    },
                },
            },
        }

    def _generate_complexity_scatter(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate complexity vs violations scatter plot."""
        violations = data.get("violations", [])

        if not violations:
            return self._empty_chart("scatter", "No violation data available")

        # Group violations by file and calculate metrics
        file_metrics = {}
        for violation in violations:
            file_path = violation.get("file_path", "")
            if file_path not in file_metrics:
                file_metrics[file_path] = {
                    "violation_count": 0,
                    "complexity_score": 0,
                    "critical_count": 0,
                    "file_name": self._shorten_filename(file_path),
                }

            file_metrics[file_path]["violation_count"] += 1

            # Estimate complexity score based on violation type and severity
            if violation.get("connascence_type") == "CoA":  # Algorithm connascence
                file_metrics[file_path]["complexity_score"] += 2
            else:
                file_metrics[file_path]["complexity_score"] += 1

            if violation.get("severity") == "critical":
                file_metrics[file_path]["critical_count"] += 1

        # Create scatter plot data
        scatter_data = []
        for file_path, metrics in file_metrics.items():
            scatter_data.append(
                {
                    "x": metrics["violation_count"],
                    "y": metrics["complexity_score"],
                    "label": metrics["file_name"],
                    "critical_count": metrics["critical_count"],
                }
            )

        # Color points based on critical violations
        point_colors = []
        point_sizes = []
        for point in scatter_data:
            if point["critical_count"] > 0:
                point_colors.append(self.color_schemes["severity"]["critical"])
                point_sizes.append(8)
            elif point["x"] > 10:  # High violation count
                point_colors.append(self.color_schemes["severity"]["high"])
                point_sizes.append(6)
            else:
                point_colors.append(self.color_schemes["severity"]["medium"])
                point_sizes.append(4)

        return {
            "type": "scatter",
            "data": {
                "datasets": [
                    {
                        "label": "Files",
                        "data": scatter_data,
                        "backgroundColor": point_colors,
                        "borderColor": point_colors,
                        "borderWidth": 1,
                        "pointRadius": point_sizes,
                    }
                ]
            },
            "options": {
                "responsive": True,
                "scales": {
                    "x": {"title": {"display": True, "text": "Violation Count"}},
                    "y": {"title": {"display": True, "text": "Complexity Score"}},
                },
                "plugins": {
                    "legend": {"display": False},
                    "tooltip": {
                        "callbacks": {
                            "title": "function(context) { return context[0].raw.label; }",
                            "label": 'function(context) { return "Violations: " + context.parsed.x + ", Complexity: " + context.parsed.y; }',
                        }
                    },
                },
            },
        }

    def _generate_timeline(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate timeline chart showing violation introduction."""
        # This would require git history analysis
        # For now, return a placeholder
        return self._empty_chart("line", "Timeline analysis requires git integration")

    def _generate_comparison(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comparison chart between different policy presets or time periods."""
        # This would require multiple scan results
        # For now, return current vs previous if available
        current_summary = data.get("summary", {})
        previous_summary = data.get("previous_summary", {})

        if not previous_summary:
            return self._empty_chart("bar", "No previous data for comparison")

        categories = ["Critical", "High", "Medium", "Low"]
        current_data = [
            current_summary.get("critical_count", 0),
            current_summary.get("high_count", 0),
            current_summary.get("medium_count", 0),
            current_summary.get("low_count", 0),
        ]
        previous_data = [
            previous_summary.get("critical_count", 0),
            previous_summary.get("high_count", 0),
            previous_summary.get("medium_count", 0),
            previous_summary.get("low_count", 0),
        ]

        return {
            "type": "bar",
            "data": {
                "labels": categories,
                "datasets": [
                    {
                        "label": "Current",
                        "data": current_data,
                        "backgroundColor": self.color_schemes["gradient"][0],
                        "borderColor": self.color_schemes["gradient"][0],
                        "borderWidth": 1,
                    },
                    {
                        "label": "Previous",
                        "data": previous_data,
                        "backgroundColor": self.color_schemes["gradient"][1],
                        "borderColor": self.color_schemes["gradient"][1],
                        "borderWidth": 1,
                    },
                ],
            },
            "options": {"responsive": True, "scales": {"y": {"beginAtZero": True}}},
        }

    def _generate_radar_chart(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate radar chart showing connascence type distribution."""
        summary = data.get("summary", {})
        violations_by_type = summary.get("violations_by_type", {})

        if not violations_by_type:
            return self._empty_chart("radar", "No connascence type data available")

        # Standard connascence types in order
        connascence_types = ["CoM", "CoP", "CoT", "CoA", "CoN", "CoE", "CoTi", "CoV", "CoI"]
        labels = [f"{t} ({self._get_connascence_name(t)})" for t in connascence_types]

        values = [violations_by_type.get(t, 0) for t in connascence_types]

        return {
            "type": "radar",
            "data": {
                "labels": labels,
                "datasets": [
                    {
                        "label": "Violations",
                        "data": values,
                        "borderColor": self.color_schemes["gradient"][0],
                        "backgroundColor": self.color_schemes["gradient"][0] + "40",
                        "borderWidth": 2,
                        "pointBackgroundColor": self.color_schemes["gradient"][0],
                        "pointBorderColor": "#ffffff",
                        "pointBorderWidth": 2,
                        "pointRadius": 4,
                    }
                ],
            },
            "options": {
                "responsive": True,
                "scales": {"r": {"beginAtZero": True, "ticks": {"precision": 0}}},
                "plugins": {"legend": {"display": False}},
            },
        }

    def _empty_chart(self, chart_type: str, message: str) -> Dict[str, Any]:
        """Generate empty chart with message."""
        return {
            "type": chart_type,
            "data": {"labels": [], "datasets": []},
            "options": {"responsive": True, "plugins": {"title": {"display": True, "text": message}}},
        }

    def _shorten_filename(self, file_path: str, max_length: int = 30) -> str:
        """Shorten filename for display."""
        if len(file_path) <= max_length:
            return file_path

        # Get just the filename and parent directory
        parts = file_path.replace("\\", "/").split("/")
        if len(parts) > 1:
            return f".../{parts[-2]}/{parts[-1]}"
        else:
            return parts[-1][: max_length - 3] + "..."

    def _get_connascence_name(self, conn_type: str) -> str:
        """Get full name for connascence type abbreviation."""
        names = {
            "CoM": "Meaning",
            "CoP": "Position",
            "CoT": "Type",
            "CoA": "Algorithm",
            "CoN": "Name",
            "CoE": "Execution",
            "CoTi": "Timing",
            "CoV": "Value",
            "CoI": "Identity",
        }
        return names.get(conn_type, "Unknown")
