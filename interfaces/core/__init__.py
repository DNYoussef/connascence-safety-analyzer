# SPDX-License-Identifier: MIT
"""
Core Interface Components

Shared functionality across all interface types (CLI, Web, VSCode).
Eliminates duplication and provides consistent behavior.
"""

from .interface_base import InterfaceBase
from .shared_components import SharedAnalysisEngine, SharedFormatter, SharedValidation

__all__ = ["InterfaceBase", "SharedAnalysisEngine", "SharedFormatter", "SharedValidation"]
