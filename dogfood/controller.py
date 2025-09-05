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
Dogfood Controller - Main Orchestrator

This is the brain of the dogfood system that orchestrates the complete
self-improvement cycle with safety-first logic.
"""

import asyncio
import logging
import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .safety_validator import SafetyValidator
from .branch_manager import BranchManager  
from .metrics_tracker import MetricsTracker

@dataclass
class DogfoodCycleResult:
    """Result of a complete dogfood improvement cycle"""
    success: bool
    branch_name: str
    improvements_applied: List[Dict[str, Any]]
    test_results: Dict[str, Any]
    metrics_comparison: Dict[str, float]
    decision_reason: str
    timestamp: datetime
    rollback_performed: bool = False

class DogfoodController:
    """Main controller for dogfood self-improvement cycles"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.safety_validator = SafetyValidator(config)
        self.branch_manager = BranchManager(config)
        self.metrics_tracker = MetricsTracker(config)
        
        # Safety limits
        self.max_changes_per_cycle = self.config.get('max_changes_per_cycle', 3)
        self.require_approval_for_risky = self.config.get('require_approval_for_risky', True)
        
    async def run_improvement_cycle(
        self, 
        improvement_goal: str = "coupling_reduction",
        safety_mode: str = "strict"
    ) -> DogfoodCycleResult:
        """
        Run complete dogfood improvement cycle with safety-first logic.
        
        Args:
            improvement_goal: Type of improvement (nasa_compliance, coupling_reduction, etc.)
            safety_mode: Safety level (strict, moderate, experimental)
            
        Returns:
            DogfoodCycleResult with complete cycle information
        """
        cycle_start = datetime.now()
        self.logger.info(f"🚀 Starting dogfood cycle: {improvement_goal}")
        
        try:
            # Step 1: Create safe branch
            self.logger.info("📋 Step 1: Creating safe dogfood branch...")
            branch_name = await self.branch_manager.create_dogfood_branch(improvement_goal)
            
            # Step 2: Get baseline metrics
            self.logger.info("📊 Step 2: Capturing baseline metrics...")
            baseline_metrics = await self.metrics_tracker.capture_baseline()
            
            # Step 3: Run MCP analysis and get improvement suggestions
            self.logger.info("🔍 Step 3: Running MCP analysis...")
            analysis_result = await self._run_mcp_analysis(improvement_goal)
            
            # Step 4: Apply improvements via MCP tools
            self.logger.info("🛠️ Step 4: Applying improvements...")
            applied_changes = await self._apply_improvements(
                analysis_result, 
                safety_mode
            )
            
            if not applied_changes:
                return DogfoodCycleResult(
                    success=False,
                    branch_name=branch_name,
                    improvements_applied=[],
                    test_results={},
                    metrics_comparison={},
                    decision_reason="No improvements could be safely applied",
                    timestamp=cycle_start
                )
            
            # Step 5: CRITICAL - Run full test suite
            self.logger.info("🧪 Step 5: Running comprehensive test suite...")
            test_results = await self.safety_validator.run_all_tests()
            
            # Step 6: Capture new metrics
            self.logger.info("📈 Step 6: Measuring improvement metrics...")  
            new_metrics = await self.metrics_tracker.capture_current_state()
            
            # Step 7: Make merge/rollback decision
            self.logger.info("🤔 Step 7: Making merge/rollback decision...")
            decision_result = await self._make_decision(
                test_results, 
                baseline_metrics, 
                new_metrics,
                applied_changes
            )
            
            # Step 8: Execute decision
            rollback_performed = False
            if decision_result.should_merge:
                self.logger.info("✅ Decision: MERGE - Improvements successful!")
                await self.branch_manager.merge_to_main(branch_name)
            else:
                self.logger.warning(f"❌ Decision: ROLLBACK - {decision_result.reason}")
                await self.branch_manager.rollback_and_cleanup(branch_name)
                rollback_performed = True
            
            return DogfoodCycleResult(
                success=decision_result.should_merge,
                branch_name=branch_name,
                improvements_applied=applied_changes,
                test_results=test_results,
                metrics_comparison=decision_result.metrics_comparison,
                decision_reason=decision_result.reason,
                timestamp=cycle_start,
                rollback_performed=rollback_performed
            )
            
        except Exception as e:
            self.logger.error(f"💥 Dogfood cycle failed: {e}")
            # Emergency cleanup
            try:
                await self.branch_manager.emergency_cleanup()
            except:
                pass
            raise

    async def _run_mcp_analysis(self, improvement_goal: str) -> Dict[str, Any]:
        """Run MCP server analysis to identify improvement opportunities"""
        # This will integrate with the MCP server
        # For now, mock the interface
        return {
            "violations_found": [],
            "improvement_suggestions": [],
            "target_files": [],
            "estimated_impact": "medium"
        }
    
    async def _apply_improvements(
        self, 
        analysis_result: Dict[str, Any], 
        safety_mode: str
    ) -> List[Dict[str, Any]]:
        """Apply improvements via MCP tools with safety constraints"""
        applied_changes = []
        suggestions = analysis_result.get("improvement_suggestions", [])
        
        # Apply safety limits
        max_changes = self.max_changes_per_cycle
        if safety_mode == "strict":
            max_changes = min(max_changes, 2)
        
        for suggestion in suggestions[:max_changes]:
            if self._is_safe_to_apply(suggestion, safety_mode):
                # Apply via MCP tools
                change_result = await self._apply_single_change(suggestion)
                if change_result.get("success"):
                    applied_changes.append(change_result)
        
        return applied_changes
    
    def _is_safe_to_apply(self, suggestion: Dict[str, Any], safety_mode: str) -> bool:
        """Determine if a suggestion is safe to apply automatically"""
        suggestion_type = suggestion.get("type", "unknown")
        risk_level = suggestion.get("risk_level", "high")
        
        if safety_mode == "strict":
            # Only allow very safe changes
            safe_types = ["magic_literal_extraction", "variable_renaming", "comment_addition"]
            return suggestion_type in safe_types and risk_level == "low"
        elif safety_mode == "moderate":
            # Allow more changes but still be cautious
            unsafe_types = ["function_signature_change", "class_restructure"]
            return suggestion_type not in unsafe_types and risk_level != "critical"
        else:
            # Experimental mode - allow most changes
            critical_types = ["core_logic_change", "security_modification"]
            return suggestion_type not in critical_types
    
    async def _apply_single_change(self, suggestion: Dict[str, Any]) -> Dict[str, Any]:
        """Apply a single improvement suggestion"""
        # This will integrate with MCP server tools
        # For now, mock the response
        return {
            "success": True,
            "suggestion": suggestion,
            "files_modified": [],
            "changes_applied": "Mock change applied"
        }
    
    @dataclass
    class DecisionResult:
        should_merge: bool
        reason: str
        metrics_comparison: Dict[str, float]
    
    async def _make_decision(
        self,
        test_results: Dict[str, Any],
        baseline_metrics: Dict[str, float],
        new_metrics: Dict[str, float],
        applied_changes: List[Dict[str, Any]]
    ) -> 'DogfoodController.DecisionResult':
        """
        Make the critical merge/rollback decision based on safety-first logic
        """
        metrics_comparison = {}
        
        # CRITICAL RULE 1: All tests must pass
        if not test_results.get("all_passed", False):
            failed_tests = test_results.get("failed_tests", [])
            return self.DecisionResult(
                should_merge=False,
                reason=f"Tests failed: {len(failed_tests)} failures detected",
                metrics_comparison=metrics_comparison
            )
        
        # CRITICAL RULE 2: No functional regressions
        if test_results.get("functional_regressions", []):
            regressions = test_results["functional_regressions"]
            return self.DecisionResult(
                should_merge=False,
                reason=f"Functional regressions detected: {regressions}",
                metrics_comparison=metrics_comparison
            )
        
        # RULE 3: Overall connascence score must improve
        baseline_score = baseline_metrics.get("connascence_score", 0.0)
        new_score = new_metrics.get("connascence_score", 0.0)
        score_improvement = new_score - baseline_score
        
        metrics_comparison["connascence_score_change"] = score_improvement
        
        if score_improvement <= 0:
            return self.DecisionResult(
                should_merge=False,
                reason=f"Connascence score did not improve: {score_improvement:.3f}",
                metrics_comparison=metrics_comparison
            )
        
        # RULE 4: Check other quality metrics
        for metric in ["nasa_compliance", "violation_count", "code_quality"]:
            baseline_val = baseline_metrics.get(metric, 0)
            new_val = new_metrics.get(metric, 0)
            
            if metric == "violation_count":
                # Lower is better for violation count
                improvement = baseline_val - new_val
            else:
                # Higher is better for other metrics
                improvement = new_val - baseline_val
            
            metrics_comparison[f"{metric}_change"] = improvement
        
        # SUCCESS: All criteria met
        return self.DecisionResult(
            should_merge=True,
            reason=f"All criteria met: score improved by {score_improvement:.3f}",
            metrics_comparison=metrics_comparison
        )