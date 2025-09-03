#!/usr/bin/env python3
"""
MCP Integration for Grammar-Enhanced Analysis

Extends the MCP server with grammar-enhanced analysis capabilities,
providing comprehensive code quality assessment with AST-safe validation.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

class GrammarEnhancedMCPExtension:
    """MCP extension providing grammar-enhanced analysis capabilities."""
    
    def __init__(self, mcp_server):
        """Initialize with reference to main MCP server."""
        self.server = mcp_server
        
        # Initialize grammar-enhanced analyzer
        try:
            from .grammar_enhanced_analyzer import GrammarEnhancedAnalyzer, create_analyzer_for_profile
            self.enhanced_analyzer = GrammarEnhancedAnalyzer(
                enable_safety_profiles=True,
                safety_compliance=True
            )
            self.create_analyzer_for_profile = create_analyzer_for_profile
            logger.info("Grammar-enhanced analyzer initialized")
        except ImportError as e:
            logger.warning(f"Grammar-enhanced analyzer not available: {e}")
            self.enhanced_analyzer = None
            self.create_analyzer_for_profile = None
    
    def get_additional_tools(self) -> List[Dict[str, Any]]:
        """Get additional MCP tools for grammar-enhanced analysis."""
        return [
            {
                "name": "analyze_with_grammar",
                "description": "Perform comprehensive analysis with grammar backend integration",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "File or directory path to analyze"
                        },
                        "safety_profile": {
                            "type": "string",
                            "enum": ["general_safety_strict", "safety_level_1", "safety_level_3", "modern_general"],
                            "description": "Safety profile to apply"
                        },
                        "framework_profile": {
                            "type": "string",
                            "enum": ["django", "fastapi", "react", "generic"],
                            "default": "generic",
                            "description": "Framework-specific analysis profile"
                        },
                        "include_refactoring": {
                            "type": "boolean",
                            "default": True,
                            "description": "Include refactoring opportunity analysis"
                        },
                        "include_safety_compliance": {
                            "type": "boolean", 
                            "default": False,
                            "description": "Include detailed safety compliance analysis"
                        }
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "get_quality_score",
                "description": "Calculate overall quality score using all analysis methods",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string", 
                            "description": "File or directory path to score"
                        },
                        "profile": {
                            "type": "string",
                            "enum": ["general_safety_strict", "modern_general", "enterprise"],
                            "default": "modern_general",
                            "description": "Quality scoring profile"
                        },
                        "weights": {
                            "type": "object",
                            "properties": {
                                "grammar": {"type": "number", "default": 0.3},
                                "connascence": {"type": "number", "default": 0.25},
                                "cohesion": {"type": "number", "default": 0.25},
                                "magic_literals": {"type": "number", "default": 0.2}
                            },
                            "description": "Custom weights for quality score calculation"
                        }
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "suggest_grammar_fixes",
                "description": "Provide grammar-constrained fixes for code issues",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "File path to analyze and fix"
                        },
                        "safety_profile": {
                            "type": "string",
                            "enum": ["general_safety_strict", "safety_level_1", "modern_general"],
                            "description": "Safety profile for constraint generation"
                        },
                        "max_fixes": {
                            "type": "integer",
                            "default": 5,
                            "minimum": 1,
                            "maximum": 20,
                            "description": "Maximum number of fixes to suggest"
                        },
                        "confidence_threshold": {
                            "type": "number",
                            "default": 0.7,
                            "minimum": 0.0,
                            "maximum": 1.0,
                            "description": "Minimum confidence for fix suggestions"
                        },
                        "dry_run": {
                            "type": "boolean",
                            "default": True,
                            "description": "Preview fixes without applying them"
                        }
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "validate_safety_profile",
                "description": "Validate code against specific safety profile requirements",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "File or directory path to validate"
                        },
                        "profile": {
                            "type": "string",
                            "enum": ["general_safety_strict", "safety_level_1", "safety_level_3"],
                            "required": True,
                            "description": "Safety profile to validate against"
                        },
                        "generate_report": {
                            "type": "boolean",
                            "default": True,
                            "description": "Generate detailed compliance report"
                        },
                        "include_evidence": {
                            "type": "boolean",
                            "default": True,
                            "description": "Include evidence for violations and compliance"
                        }
                    },
                    "required": ["path", "profile"]
                }
            },
            {
                "name": "compare_quality_trends",
                "description": "Compare code quality trends between versions or branches", 
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Project path to analyze"
                        },
                        "baseline_ref": {
                            "type": "string",
                            "description": "Git reference for baseline (branch, tag, commit)"
                        },
                        "current_ref": {
                            "type": "string",
                            "default": "HEAD",
                            "description": "Git reference for current state"
                        },
                        "metrics": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": ["quality_score", "connascence", "cohesion", "magic_literals", "safety_compliance"]
                            },
                            "default": ["quality_score"],
                            "description": "Metrics to compare"
                        }
                    },
                    "required": ["path", "baseline_ref"]
                }
            }
        ]
    
    def handle_analyze_with_grammar(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle comprehensive grammar-enhanced analysis."""
        if not self.enhanced_analyzer:
            return {
                "error": "Grammar-enhanced analyzer not available",
                "code": "FEATURE_UNAVAILABLE"
            }
        
        try:
            path = Path(args["path"])
            safety_profile = args.get("safety_profile")
            framework_profile = args.get("framework_profile", "generic")
            
            # Create analyzer with appropriate profile
            if framework_profile != "generic":
                analyzer = self.create_analyzer_for_profile(framework_profile)
            else:
                analyzer = self.enhanced_analyzer
            
            # Perform analysis
            if path.is_file():
                result = analyzer.analyze_file(path, safety_profile)
                results = [result]
            else:
                results = analyzer.analyze_codebase(path, safety_profile)
            
            # Format results
            analysis_results = []
            for result in results:
                analysis_data = {
                    "file_path": result.file_path,
                    "language": result.language.value,
                    "quality_score": result.overall_quality_score,
                    "grammar_validation": {
                        "is_valid": result.grammar_validation.is_valid,
                        "violations": result.grammar_validation.violations,
                        "has_safety_violations": result.grammar_validation.has_safety_violations
                    }
                }
                
                # Add detailed results if requested
                if args.get("include_refactoring", True):
                    analysis_data["refactoring_opportunities"] = [
                        {
                            "technique": opp.technique.value,
                            "description": opp.description,
                            "confidence": opp.confidence,
                            "location": f"{opp.line_number}:{opp.column}"
                        } for opp in result.refactoring_opportunities
                    ]
                
                if args.get("include_safety_compliance", False):
                    analysis_data["safety_compliance"] = result.safety_profile_compliance
                
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
            logger.error(f"Grammar analysis failed: {e}")
            return {
                "error": f"Analysis failed: {str(e)}",
                "code": "ANALYSIS_ERROR"
            }
    
    def handle_get_quality_score(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle quality score calculation."""
        if not self.enhanced_analyzer:
            return {
                "error": "Grammar-enhanced analyzer not available", 
                "code": "FEATURE_UNAVAILABLE"
            }
        
        try:
            path = Path(args["path"])
            profile = args.get("profile", "modern_general")
            custom_weights = args.get("weights", {})
            
            # Use profile-specific analyzer
            analyzer = self.create_analyzer_for_profile(profile) if self.create_analyzer_for_profile else self.enhanced_analyzer
            
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
                    "overall_score": result.overall_quality_score,
                    "component_scores": {
                        "grammar": 1.0 if result.grammar_validation.is_valid else 0.5,
                        "safety": 0.0 if result.grammar_validation.has_safety_violations else 1.0
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
                
                if result.grammar_validation.has_safety_violations:
                    total_violations["safety"] += 1
                
                file_scores.append(file_score)
            
            # Calculate project-level score
            if file_scores:
                project_score = sum(f["overall_score"] for f in file_scores) / len(file_scores)
            else:
                project_score = 0.0
            
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
            logger.error(f"Quality scoring failed: {e}")
            return {
                "error": f"Quality scoring failed: {str(e)}",
                "code": "SCORING_ERROR"
            }
    
    def handle_suggest_grammar_fixes(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle grammar-constrained fix suggestions."""
        if not self.enhanced_analyzer:
            return {
                "error": "Grammar-enhanced analyzer not available",
                "code": "FEATURE_UNAVAILABLE"
            }
        
        try:
            path = Path(args["path"])
            safety_profile = args.get("safety_profile")
            max_fixes = args.get("max_fixes", 5)
            confidence_threshold = args.get("confidence_threshold", 0.7)
            dry_run = args.get("dry_run", True)
            
            if not path.is_file():
                return {
                    "error": "Path must be a single file for fix suggestions",
                    "code": "INVALID_PATH"
                }
            
            # Analyze file
            result = self.enhanced_analyzer.analyze_file(path, safety_profile)
            
            # Get grammar-constrained fixes
            fixes = self.enhanced_analyzer.suggest_grammar_constrained_fixes(result)
            
            # Filter by confidence and limit
            filtered_fixes = [
                fix for fix in fixes 
                if fix.get("confidence", 0) >= confidence_threshold
            ][:max_fixes]
            
            # Format response
            response = {
                "success": True,
                "file_path": str(path),
                "safety_profile": safety_profile,
                "dry_run": dry_run,
                "fixes_found": len(filtered_fixes),
                "fixes": filtered_fixes,
                "analysis_summary": {
                    "quality_score": result.overall_quality_score,
                    "grammar_valid": result.grammar_validation.is_valid,
                    "refactoring_opportunities": len(result.refactoring_opportunities)
                }
            }
            
            if not dry_run and filtered_fixes:
                response["warning"] = "dry_run=false specified but automatic application not implemented for safety"
            
            return response
            
        except Exception as e:
            logger.error(f"Grammar fix suggestion failed: {e}")
            return {
                "error": f"Fix suggestion failed: {str(e)}",
                "code": "FIX_ERROR"
            }
    
    def handle_validate_safety_profile(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle safety profile validation."""
        if not self.enhanced_analyzer:
            return {
                "error": "Grammar-enhanced analyzer not available",
                "code": "FEATURE_UNAVAILABLE"
            }
        
        try:
            path = Path(args["path"])
            profile = args["profile"]
            generate_report = args.get("generate_report", True)
            include_evidence = args.get("include_evidence", True)
            
            # Create General Safety-compliant analyzer
            analyzer = GrammarEnhancedAnalyzer(
                enable_safety_profiles=True,
                safety_compliance=True
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
                compliance = result.safety_profile_compliance
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
                # Group violations by type for report
                violation_types = {}
                for violation in total_violations:
                    vtype = violation.get("rule", "unknown")
                    violation_types[vtype] = violation_types.get(vtype, 0) + 1
                
                response["detailed_report"] = {
                    "violation_breakdown": violation_types,
                    "recommendations": self._generate_nasa_recommendations(violation_types),
                    "next_steps": self._get_compliance_next_steps(compliance_percentage)
                }
            
            return response
            
        except Exception as e:
            logger.error(f"Safety profile validation failed: {e}")
            return {
                "error": f"Validation failed: {str(e)}",
                "code": "VALIDATION_ERROR"
            }
    
    def _generate_nasa_recommendations(self, violation_types: Dict[str, int]) -> List[str]:
        """Generate General Safety-specific recommendations based on violation patterns."""
        recommendations = []
        
        if "nasa_rule_1" in violation_types:
            recommendations.append("Replace goto statements and recursion with structured control flow")
        
        if "nasa_rule_2" in violation_types:
            recommendations.append("Add loop bound annotations and convert infinite loops to bounded iterations")
        
        if "nasa_rule_3" in violation_types:
            recommendations.append("Move dynamic allocations to initialization phase or use pre-allocated pools")
        
        if "nasa_rule_4" in violation_types:
            recommendations.append("Break down large functions using Extract Method refactoring")
        
        if "nasa_rule_5" in violation_types:
            recommendations.append("Add parameter validation and return value checking")
        
        if len(violation_types) > 5:
            recommendations.append("Consider implementing a systematic code review process for General Safety compliance")
        
        return recommendations
    
    def _get_compliance_next_steps(self, compliance_percentage: float) -> List[str]:
        """Get next steps based on compliance percentage."""
        if compliance_percentage >= 95:
            return ["Maintain current standards", "Consider automated compliance monitoring"]
        elif compliance_percentage >= 80:
            return ["Focus on critical violations first", "Implement pre-commit hooks for compliance"]
        elif compliance_percentage >= 60:
            return ["Systematic refactoring required", "Training on General Safety coding standards recommended"]
        else:
            return ["Major compliance issues detected", "Consider professional code audit", "Implement step-by-step compliance plan"]


def extend_mcp_server_with_grammar(server):
    """Extend an existing MCP server with grammar-enhanced capabilities."""
    extension = GrammarEnhancedMCPExtension(server)
    
    # Add new tools to server's tool list
    additional_tools = extension.get_additional_tools()
    
    # Add handlers to server
    server.grammar_extension = extension
    
    # Monkey patch the tool routing to include new handlers
    original_get_tool_result = server.get_tool_result
    
    def enhanced_get_tool_result(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        # Handle grammar-enhanced tools
        if tool_name == "analyze_with_grammar":
            return extension.handle_analyze_with_grammar(arguments)
        elif tool_name == "get_quality_score":
            return extension.handle_get_quality_score(arguments) 
        elif tool_name == "suggest_grammar_fixes":
            return extension.handle_suggest_grammar_fixes(arguments)
        elif tool_name == "validate_safety_profile":
            return extension.handle_validate_safety_profile(arguments)
        else:
            # Fall back to original handler
            return original_get_tool_result(tool_name, arguments)
    
    server.get_tool_result = enhanced_get_tool_result
    
    return additional_tools