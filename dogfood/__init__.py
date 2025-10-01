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
Dogfood System - Self-Improvement Controller

This package implements the complete dogfood self-improvement system
for the Connascence Safety Analyzer.
"""

from .branch_manager import BranchManager
from .controller import DogfoodController
from .metrics_tracker import MetricsTracker
from .safety_validator import SafetyValidator

__all__ = ["BranchManager", "DogfoodController", "MetricsTracker", "SafetyValidator"]
