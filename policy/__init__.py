"""
Policy-as-Code System for Connascence Analysis

This module implements a comprehensive policy system that allows teams to:
- Define quality standards via YAML configurations
- Set per-PR budgets and limits
- Create baseline snapshots with ratcheting
- Manage time-boxed waivers
- Apply different policies to different code areas

Key Components:
- PolicyManager: Loads and applies policies
- BudgetTracker: Enforces per-PR limits  
- BaselineManager: Manages quality ratcheting
- WaiverSystem: Handles temporary exceptions
"""

from .manager import PolicyManager, PolicyViolation
from .budgets import BudgetTracker, BudgetStatus, BudgetExceededException
from .baselines import BaselineManager, BaselineSnapshot, BaselineComparison
from .waivers import WaiverSystem, Waiver, WaiverStatus

__all__ = [
    # Core policy management
    "PolicyManager",
    "PolicyViolation", 
    
    # Budget management
    "BudgetTracker",
    "BudgetStatus",
    "BudgetExceededException",
    
    # Baseline management  
    "BaselineManager",
    "BaselineSnapshot",
    "BaselineComparison",
    
    # Waiver system
    "WaiverSystem", 
    "Waiver",
    "WaiverStatus",
]