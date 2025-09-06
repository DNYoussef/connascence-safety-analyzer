# SPDX-License-Identifier: MIT
# AST Engine module stub for backward compatibility
from mcp.server import ConnascenceViolation


class ConnascenceASTAnalyzer:
    """Mock AST analyzer for backward compatibility."""

    def __init__(self):
        pass

    def analyze_file(self, file_path):
        return []

    def analyze_directory(self, dir_path):
        return []


class AnalysisResult:
    """Mock analysis result."""

    def __init__(self, violations=None):
        self.violations = violations or []


class Violation:
    """Mock violation class."""

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


__all__ = ["ConnascenceASTAnalyzer", "AnalysisResult", "Violation", "ConnascenceViolation"]
