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