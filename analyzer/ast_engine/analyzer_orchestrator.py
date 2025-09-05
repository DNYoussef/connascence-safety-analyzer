# SPDX-License-Identifier: MIT
# Analyzer orchestrator stub for backward compatibility

class AnalyzerOrchestrator:
    """Mock analyzer orchestrator for backward compatibility."""
    def __init__(self):
        pass
    
    def analyze(self, *args, **kwargs):
        return []
    
    def orchestrate_analysis(self, *args, **kwargs):
        return []

__all__ = ["AnalyzerOrchestrator"]
