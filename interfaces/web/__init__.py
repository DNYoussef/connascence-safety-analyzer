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
Connascence Dashboard System

Provides web-based dashboards for local development and CI/CD integration,
offering rich visualizations and interactive analysis of connascence metrics.
"""

try:
    from .local_server import LocalDashboard
except ImportError:
    # Optional dependency - dashboard requires Flask extras
    LocalDashboard = None

try:
    from .ci_integration import CIDashboard
except ImportError:
    CIDashboard = None

from .metrics import DashboardMetrics
from .charts import ChartGenerator

__all__ = [
    'LocalDashboard',
    'CIDashboard', 
    'DashboardMetrics',
    'ChartGenerator'
]