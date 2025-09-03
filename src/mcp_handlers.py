#!/usr/bin/env python3
"""
MCP Handler Classes

Extracts MCP extension handlers from GrammarEnhancedMCPExtension to reduce 
God Object and improve Single Responsibility Principle compliance.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from .constants import ExitCode, SafetyProfiles, FrameworkProfiles

logger = logging.getLogger(__name__)


class BaseMCPHandler:
    """Base class for MCP handlers with common functionality."""
    
    def __init__(self, analyzer_factory=None):
        self.analyzer_factory = analyzer_factory
    
    def _handle_error(self, error_msg: str, error_code: str = "HANDLER_ERROR") -> Dict[str, Any]:
        """Standard error response format."""
        logger.error(error_msg)
        return {
            "error": error_msg,
            "code": error_code
        }
    
    def _check_analyzer_availability(self) -> bool:
        """Check if enhanced analyzer is available."""
        if not self.analyzer_factory:
            return False
        try:
            from .refactored_grammar_analyzer import GrammarEnhancedAnalyzer
            return True
        except ImportError:
            return False


class GrammarAnalysisHandler(BaseMCPHandler):
    """Handles grammar-enhanced analysis requests."""
    
    def handle_analyze_with_grammar(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle comprehensive grammar-enhanced analysis."""
        if not self._check_analyzer_availability():
            return self._handle_error(
                "Grammar-enhanced analyzer not available", 
                "FEATURE_UNAVAILABLE"
            )
        
        try:
            path = Path(args["path"])
            safety_profile = args.get("safety_profile")
            framework_profile = args.get("framework_profile", FrameworkProfiles.GENERIC)
            
            # Create analyzer with appropriate profile
            if framework_profile != FrameworkProfiles.GENERIC:
                from .refactored_grammar_analyzer import create_analyzer_for_profile
                analyzer = create_analyzer_for_profile(framework_profile)
            else:
                from .refactored_grammar_analyzer import GrammarEnhancedAnalyzer
                analyzer = GrammarEnhancedAnalyzer(
                    enable_safety_profiles=True,
                    nasa_compliance=True
                )
            
            # Perform analysis
            if path.is_file():
                results = [analyzer.analyze_file(path, safety_profile)]
            else:
                results = analyzer.analyze_codebase(path, safety_profile)
            
            # Format results
            analysis_results = []
            for result in results:
                analysis_data = {
                    "file_path": result.file_path,
                    "language": result.language,
                    "quality_score": result.quality_score,
                    "grammar_validation": {
                        "is_valid": result.validation_result.is_valid,
                        "violations": result.validation_result.violations,
                        "has_safety_violations": result.validation_result.has_safety_violations
                    }
                }
                
                # Add detailed results if requested
                if args.get("include_refactoring", True):
                    analysis_data["refactoring_opportunities"] = [
                        {
                            "technique": getattr(opp, 'technique', 'unknown'),
                            "description": getattr(opp, 'description', 'No description'),
                            "confidence": getattr(opp, 'confidence', 0.0),
                            "location": f"{getattr(opp, 'line_number', 0)}:{getattr(opp, 'column', 0)}"
                        } for opp in result.refactoring_opportunities
                    ]
                
                if args.get("include_safety_compliance", False):
                    analysis_data["safety_compliance"] = result.safety_compliance
                
                # Include violation summaries
                analysis_data["violations"] = {
                    "connascence": len(result.connascence_violations),
                    "magic_literals": len(result.magic_literals),
                    "god_objects": len(result.god_objects)
                }
                
                analysis_results.append(analysis_data)
            
            # Calculate summary statistics
            total_files = len(analysis_results)
            avg_quality_score = sum(r["quality_score"] for r in analysis_results) / total_files if total_files > 0 else 0
            files_with_violations = len([r for r in analysis_results if r["grammar_validation"]["has_safety_violations"]])
            
            return {
                "success": True,
                "summary": {
                    "total_files": total_files,
                    "average_quality_score": round(avg_quality_score, 3),
                    "files_with_violations": files_with_violations,
                    "safety_profile": safety_profile,
                    "framework_profile": framework_profile
                },
                "results": analysis_results
            }
            
        except Exception as e:
            return self._handle_error(f"Analysis failed: {str(e)}", "ANALYSIS_ERROR")


class QualityScoringHandler(BaseMCPHandler):
    """Handles quality score calculation requests."""
    
    def handle_get_quality_score(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle quality score calculation."""
        if not self._check_analyzer_availability():
            return self._handle_error(
                "Grammar-enhanced analyzer not available",
                "FEATURE_UNAVAILABLE"
            )
        
        try:
            path = Path(args["path"])
            profile = args.get("profile", "modern_general")
            custom_weights = args.get("weights", {})
            
            # Create analyzer
            from .refactored_grammar_analyzer import create_analyzer_for_profile
            analyzer = create_analyzer_for_profile(profile)
            
            # Analyze for quality scoring
            if path.is_file():
                results = [analyzer.analyze_file(path)]
            else:
                results = analyzer.analyze_codebase(path)
            
            # Calculate weighted quality scores
            default_weights = {
                "grammar": 0.3,
                "connascence": 0.25, 
                "cohesion": 0.25,
                "magic_literals": 0.2
            }
            weights = {**default_weights, **custom_weights}
            
            # Aggregate results
            file_scores = []
            total_violations = {"connascence": 0, "magic_literals": 0, "god_objects": 0, "safety": 0}
            
            for result in results:
                file_score = {
                    "file_path": result.file_path,
                    "overall_score": result.quality_score,
                    "component_scores": {
                        "grammar": 1.0 if result.validation_result.is_valid else 0.5,
                        "safety": 0.0 if result.validation_result.has_safety_violations else 1.0
                    },
                    "violations": {
                        "connascence": len(result.connascence_violations),
                        "magic_literals": len(result.magic_literals),
                        "god_objects": len(result.god_objects)
                    }
                }
                
                # Update totals
                for key, count in file_score["violations"].items():
                    total_violations[key] += count
                
                if result.validation_result.has_safety_violations:
                    total_violations["safety"] += 1
                
                file_scores.append(file_score)
            
            # Calculate project-level score
            project_score = sum(f["overall_score"] for f in file_scores) / len(file_scores) if file_scores else 0.0
            
            return {
                "success": True,
                "project_quality_score": round(project_score, 3),
                "profile": profile,
                "weights": weights,
                "summary": {
                    "total_files": len(file_scores),
                    "total_violations": total_violations,
                    "files_analyzed": len(results)
                },
                "file_scores": file_scores
            }
            
        except Exception as e:
            return self._handle_error(f"Quality scoring failed: {str(e)}", "SCORING_ERROR")


class FixSuggestionHandler(BaseMCPHandler):
    """Handles grammar-constrained fix suggestions."""
    
    def handle_suggest_grammar_fixes(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle grammar-constrained fix suggestions."""
        if not self._check_analyzer_availability():
            return self._handle_error(
                "Grammar-enhanced analyzer not available",
                "FEATURE_UNAVAILABLE"
            )
        
        try:
            path = Path(args["path"])
            safety_profile = args.get("safety_profile")
            max_fixes = args.get("max_fixes", 5)
            confidence_threshold = args.get("confidence_threshold", 0.7)
            dry_run = args.get("dry_run", True)
            
            if not path.is_file():
                return self._handle_error(
                    "Path must be a single file for fix suggestions",
                    "INVALID_PATH"
                )
            
            # Create and use analyzer
            from .refactored_grammar_analyzer import GrammarEnhancedAnalyzer
            analyzer = GrammarEnhancedAnalyzer(enable_safety_profiles=True)
            
            # Analyze file
            result = analyzer.analyze_file(path, safety_profile)
            
            # Get grammar-constrained fixes
            fixes = analyzer.suggest_grammar_constrained_fixes(result)
            
            # Filter by confidence and limit
            filtered_fixes = [
                fix for fix in fixes 
                if fix.get("confidence", 0) >= confidence_threshold
            ][:max_fixes]
            
            return {
                "success": True,
                "file_path": str(path),
                "safety_profile": safety_profile,
                "dry_run": dry_run,
                "fixes_found": len(filtered_fixes),
                "fixes": filtered_fixes,
                "analysis_summary": {
                    "quality_score": result.quality_score,
                    "grammar_valid": result.validation_result.is_valid,
                    "refactoring_opportunities": len(result.refactoring_opportunities)
                }
            }
            
        except Exception as e:
            return self._handle_error(f"Fix suggestion failed: {str(e)}", "FIX_ERROR")


class SafetyValidationHandler(BaseMCPHandler):
    """Handles safety profile validation requests."""
    
    def handle_validate_safety_profile(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle safety profile validation."""
        if not self._check_analyzer_availability():
            return self._handle_error(
                "Grammar-enhanced analyzer not available",
                "FEATURE_UNAVAILABLE"
            )
        
        try:
            path = Path(args["path"])
            profile = args["profile"]
            generate_report = args.get("generate_report", True)
            include_evidence = args.get("include_evidence", True)
            
            # Create General Safety-compliant analyzer
            from .refactored_grammar_analyzer import GrammarEnhancedAnalyzer
            analyzer = GrammarEnhancedAnalyzer(
                enable_safety_profiles=True,
                nasa_compliance=True
            )
            
            # Perform analysis with safety profile
            if path.is_file():
                results = [analyzer.analyze_file(path, profile)]
            else:
                results = analyzer.analyze_codebase(path, profile)
            
            # Aggregate compliance results
            total_files = len(results)
            compliant_files = 0
            total_violations = []
            file_results = []
            
            for result in results:
                compliance = result.safety_compliance or {}
                is_compliant = compliance.get("compliant", False)
                
                if is_compliant:
                    compliant_files += 1
                
                file_result = {
                    "file_path": result.file_path,
                    "compliant": is_compliant,
                    "violations": len(compliance.get("violations", [])),
                    "nasa_compliant": compliance.get("nasa_compliant", False)
                }
                
                if include_evidence:
                    file_result["evidence"] = {
                        "violations": compliance.get("violations", []),
                        "nasa_violations": compliance.get("nasa_violations", [])
                    }
                
                file_results.append(file_result)
                total_violations.extend(compliance.get("violations", []))
            
            # Calculate compliance percentage
            compliance_percentage = (compliant_files / total_files * 100) if total_files > 0 else 0
            
            response = {
                "success": True,
                "profile": profile,
                "compliance_summary": {
                    "total_files": total_files,
                    "compliant_files": compliant_files,
                    "compliance_percentage": round(compliance_percentage, 1),
                    "total_violations": len(total_violations)
                },
                "file_results": file_results
            }
            
            if generate_report:
                response["detailed_report"] = self._generate_compliance_report(
                    total_violations, compliance_percentage
                )
            
            return response
            
        except Exception as e:
            return self._handle_error(f"Validation failed: {str(e)}", "VALIDATION_ERROR")
    
    def _generate_compliance_report(self, total_violations: List[Dict], 
                                  compliance_percentage: float) -> Dict[str, Any]:
        """Generate detailed compliance report."""
        
        # Group violations by type
        violation_types = {}
        for violation in total_violations:
            vtype = violation.get("rule", "unknown")
            violation_types[vtype] = violation_types.get(vtype, 0) + 1
        
        # Generate General Safety-specific recommendations
        recommendations = []
        if "nasa_rule_1" in violation_types:
            recommendations.append("Replace goto statements and recursion with structured control flow")
        if "nasa_rule_2" in violation_types:
            recommendations.append("Add loop bound annotations and convert infinite loops to bounded iterations")
        if "nasa_rule_3" in violation_types:
            recommendations.append("Move dynamic allocations to initialization phase or use pre-allocated pools")
        if len(violation_types) > 5:
            recommendations.append("Consider implementing a systematic code review process for General Safety compliance")
        
        # Get next steps based on compliance
        if compliance_percentage >= 95:
            next_steps = ["Maintain current standards", "Consider automated compliance monitoring"]
        elif compliance_percentage >= 80:
            next_steps = ["Focus on critical violations first", "Implement pre-commit hooks for compliance"]
        elif compliance_percentage >= 60:
            next_steps = ["Systematic refactoring required", "Training on General Safety coding standards recommended"]
        else:
            next_steps = ["Major compliance issues detected", "Consider professional code audit", "Implement step-by-step compliance plan"]
        
        return {
            "violation_breakdown": violation_types,
            "recommendations": recommendations,
            "next_steps": next_steps
        }