"""
Core AST-based Connascence Analyzer

REFACTORED VERSION: This class now delegates to AnalyzerOrchestrator to resolve God Object violation.
The original 881-line monolithic class has been split into 6 specialized components:
- BaseConnascenceAnalyzer (core functionality)
- PositionAnalyzer (CoP detection) 
- MeaningAnalyzer (CoM/CoN/CoT detection)
- AlgorithmAnalyzer (CoA/CoE/CoV/CoTi detection)
- GodObjectAnalyzer (size detection)
- AnalyzerOrchestrator (coordination)

This provides backward compatibility while using the new modular architecture.
"""

import logging
from pathlib import Path
from typing import List, Optional

from ..thresholds import (
    ThresholdConfig, WeightConfig, PolicyPreset
)
from policy.manager import PolicyManager
from .violations import Violation, AnalysisResult
from .analyzer_orchestrator import AnalyzerOrchestrator

logger = logging.getLogger(__name__)


class ConnascenceASTAnalyzer:
    """
    Enhanced AST-based connascence analyzer.
    
    REFACTORED: Now delegates to specialized analyzer components instead of 
    containing all analysis logic in a single monolithic class.
    
    This resolves the God Object violation while maintaining full backward compatibility.
    """
    
    def __init__(
        self, 
        thresholds: Optional[ThresholdConfig] = None,
        weights: Optional[WeightConfig] = None,
        policy_preset: Optional[PolicyPreset] = None,
        policy_name: Optional[str] = None,
        exclusions: Optional[List[str]] = None
    ):
        """Initialize the analyzer with delegated orchestrator."""
        # Initialize policy manager for enterprise presets
        self.policy_manager = PolicyManager()
        
        # Apply policy preset if specified by name
        if policy_name and policy_name in self.policy_manager.presets:
            policy_config = self.policy_manager.get_preset(policy_name)
            if not thresholds:
                thresholds = self._policy_to_thresholds(policy_config)
        
        # Delegate to the new modular architecture
        self._orchestrator = AnalyzerOrchestrator(
            thresholds=thresholds,
            weights=weights, 
            policy_preset=policy_preset,
            exclusions=exclusions
        )
        
        # Expose orchestrator properties for backward compatibility
        self.thresholds = self._orchestrator.thresholds
        self.weights = self._orchestrator.weights
        self.policy_preset = self._orchestrator.policy_preset
        self.exclusions = self._orchestrator.exclusions
        self.violations = self._orchestrator.violations
        self.file_stats = self._orchestrator.file_stats
        self.current_file_path = self._orchestrator.current_file_path
        self.current_source_lines = self._orchestrator.current_source_lines
        self.analysis_start_time = self._orchestrator.analysis_start_time
    
    def should_analyze_file(self, file_path: Path) -> bool:
        """Check if file should be analyzed based on exclusions."""
        return self._orchestrator.should_analyze_file(file_path)
    
    def analyze_string(self, source_code: str, filename: str = "string_input.py") -> List[Violation]:
        """Analyze source code string for connascence violations."""
        result = self._orchestrator.analyze_string(source_code, filename)
        self._sync_state_from_orchestrator()
        return result
    
    def analyze_file(self, file_path: Path) -> List[Violation]:
        """Analyze a single file for connascence violations."""
        result = self._orchestrator.analyze_file(file_path)
        self._sync_state_from_orchestrator()
        return result
    
    def analyze_directory(self, directory: Path) -> AnalysisResult:
        """Analyze all Python files in a directory tree."""
        result = self._orchestrator.analyze_directory(directory)
        self._sync_state_from_orchestrator()
        return result
    
    def _sync_state_from_orchestrator(self):
        """Synchronize state from orchestrator for backward compatibility."""
        self.violations = self._orchestrator.violations
        self.file_stats = self._orchestrator.file_stats
        self.current_file_path = self._orchestrator.current_file_path
        self.current_source_lines = self._orchestrator.current_source_lines
        self.analysis_start_time = self._orchestrator.analysis_start_time
    
    # Legacy method compatibility - delegate to orchestrator's utility methods
    def _get_code_snippet(self, node, context_lines: int = 2) -> str:
        """Legacy method for backward compatibility."""
        return self._orchestrator.get_code_snippet(node, context_lines)
    
    def _get_context_lines(self, line_number: int, context: int = 2) -> str:
        """Legacy method for backward compatibility."""
        return self._orchestrator.get_context_lines(line_number, context)
    
    def _calculate_file_stats(self, tree, violations) -> dict:
        """Legacy method for backward compatibility."""
        return self._orchestrator.calculate_file_stats(tree, violations)
    
    def _calculate_summary_metrics(self, violations) -> dict:
        """Legacy method for backward compatibility."""
        return self._orchestrator.calculate_summary_metrics(violations)
    
    def _policy_to_thresholds(self, policy_config: dict) -> ThresholdConfig:
        """Convert policy configuration to ThresholdConfig."""
        thresholds_data = policy_config.get('thresholds', {})
        return ThresholdConfig(
            max_positional_params=thresholds_data.get('max_positional_params', 6),
            god_class_methods=thresholds_data.get('god_class_methods', 25),
            max_cyclomatic_complexity=thresholds_data.get('max_cyclomatic_complexity', 15)
        )