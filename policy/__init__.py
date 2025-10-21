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

from .baselines import BaselineComparison, BaselineManager, BaselineSnapshot
from .budgets import BudgetExceededException, BudgetStatus, BudgetTracker
from .manager import PolicyManager, PolicyViolation
from .waivers import Waiver, WaiverStatus, WaiverSystem

__all__ = [
    "BaselineComparison",
    # Baseline management
    "BaselineManager",
    "BaselineSnapshot",
    "BudgetExceededException",
    "BudgetStatus",
    # Budget management
    "BudgetTracker",
    # Core policy management
    "PolicyManager",
    "PolicyViolation",
    "Waiver",
    "WaiverStatus",
    # Waiver system
    "WaiverSystem",
]
