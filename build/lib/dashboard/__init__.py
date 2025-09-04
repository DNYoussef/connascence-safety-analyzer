"""
Connascence Dashboard System

Provides web-based dashboards for local development and CI/CD integration,
offering rich visualizations and interactive analysis of connascence metrics.
"""

from .local_server import LocalDashboard
from .ci_integration import CIDashboard
from .metrics import DashboardMetrics
from .charts import ChartGenerator

__all__ = [
    'LocalDashboard',
    'CIDashboard', 
    'DashboardMetrics',
    'ChartGenerator'
]