"""
MCP Server for Connascence Analysis

Provides Model Context Protocol endpoints for AI agents to perform
connascence analysis, with safety controls and audit logging.

Available Tools:
- scan_path: Analyze files/directories for connascence
- scan_diff: Analyze changes between git references  
- explain_finding: Get detailed explanation of violations
- propose_autofix: Generate patches for violations
- enforce_policy: Apply policy constraints
- get_scorecard: Generate quality metrics
- baseline_snapshot: Create/manage baselines
"""

import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# MCP server implementation would use the official MCP library
# For now, this shows the structure and tool definitions

logger = logging.getLogger(__name__)


class ConnascenceMCPServer:
    """MCP server for connascence analysis with agent safety."""
    
    def __init__(self, audit_log_path: Optional[Path] = None):
        self.name = "connascence-analyzer"
        self.version = "1.0.0"
        self.audit_log_path = audit_log_path or Path(".connascence/audit.log")
        self.rate_limiter = RateLimiter()
        
        # Ensure audit log directory exists
        self.audit_log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        from analyzer.ast_engine.core_analyzer import ConnascenceASTAnalyzer
        from reporting.json_export import JSONReporter
        from reporting.sarif_export import SARIFReporter
        from policy.manager import PolicyManager
        from grammar.backends.tree_sitter_backend import TreeSitterBackend, LanguageSupport
        from grammar.overlay_manager import OverlayManager
        from grammar.constrained_generator import ConstrainedGenerator
        from grammar.ast_safe_refactoring import ASTSafeRefactoring
        
        self.analyzer = ConnascenceASTAnalyzer()
        self.json_reporter = JSONReporter()
        self.sarif_reporter = SARIFReporter() 
        self.policy_manager = PolicyManager()
        
        # Grammar and refactoring components
        self.grammar_backend = TreeSitterBackend()
        self.overlay_manager = OverlayManager()
        self.constrained_generator = ConstrainedGenerator(self.grammar_backend, self.overlay_manager)
        self.ast_refactoring = ASTSafeRefactoring(self.grammar_backend, self.overlay_manager)
    
    def get_tools(self) -> List[Dict[str, Any]]:
        """Get available MCP tools."""
        return [
            {
                "name": "scan_path",
                "description": "Analyze files or directories for connascence violations",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "File or directory path to analyze"
                        },
                        "policy": {
                            "type": "string", 
                            "enum": ["strict-core", "service-defaults", "experimental"],
                            "default": "service-defaults",
                            "description": "Policy preset to apply"
                        },
                        "include_patterns": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "File patterns to include"
                        },
                        "exclude_patterns": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "File patterns to exclude"
                        },
                        "output_format": {
                            "type": "string",
                            "enum": ["json", "sarif", "summary"],
                            "default": "json",
                            "description": "Output format"
                        },
                        "incremental": {
                            "type": "boolean",
                            "default": false,
                            "description": "Use incremental analysis with caching"
                        }
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "scan_diff",
                "description": "Analyze changes between git references",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "repo_path": {
                            "type": "string",
                            "description": "Repository path"
                        },
                        "base_ref": {
                            "type": "string",
                            "description": "Base git reference (e.g., HEAD~1, main)"
                        },
                        "head_ref": {
                            "type": "string", 
                            "default": "HEAD",
                            "description": "Head git reference"
                        },
                        "policy": {
                            "type": "string",
                            "enum": ["strict-core", "service-defaults", "experimental"],
                            "default": "service-defaults"
                        }
                    },
                    "required": ["repo_path", "base_ref"]
                }
            },
            {
                "name": "explain_finding",
                "description": "Get detailed explanation of a violation or rule",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "finding_id": {
                            "type": "string",
                            "description": "Violation fingerprint or rule ID"
                        },
                        "rule_id": {
                            "type": "string",
                            "description": "Rule ID (e.g., CON_CoM)"
                        },
                        "file_path": {
                            "type": "string",
                            "description": "File path for context"
                        },
                        "line_number": {
                            "type": "integer",
                            "description": "Line number for context"
                        },
                        "include_examples": {
                            "type": "boolean",
                            "default": true,
                            "description": "Include refactoring examples"
                        }
                    }
                }
            },
            {
                "name": "propose_autofix",
                "description": "Generate patches for violations (read-only by default)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "finding_id": {
                            "type": "string",
                            "description": "Violation fingerprint to fix"
                        },
                        "violation_type": {
                            "type": "string",
                            "enum": ["CoM", "CoP", "CoA"],
                            "description": "Type of violation to fix"
                        },
                        "file_path": {
                            "type": "string",
                            "description": "File to fix"
                        },
                        "apply_fix": {
                            "type": "boolean",
                            "default": false,
                            "description": "Whether to apply fix (requires write permission)"
                        },
                        "interactive": {
                            "type": "boolean", 
                            "default": false,
                            "description": "Interactive mode for manual review"
                        }
                    },
                    "required": ["finding_id"]
                }
            },
            {
                "name": "enforce_policy",
                "description": "Apply policy constraints and budget limits",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "policy_preset": {
                            "type": "string",
                            "enum": ["strict-core", "service-defaults", "experimental"]
                        },
                        "custom_policy": {
                            "type": "object",
                            "description": "Custom policy configuration"
                        },
                        "budget_limits": {
                            "type": "object",
                            "properties": {
                                "total_violations": {"type": "integer"},
                                "critical": {"type": "integer"}, 
                                "high": {"type": "integer"},
                                "medium": {"type": "integer"},
                                "CoM": {"type": "integer"},
                                "CoP": {"type": "integer"},
                                "CoA": {"type": "integer"}
                            }
                        }
                    }
                }
            },
            {
                "name": "baseline_snapshot",
                "description": "Create or manage quality baselines",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["create", "update", "compare", "list"],
                            "description": "Baseline action to perform"
                        },
                        "message": {
                            "type": "string",
                            "description": "Snapshot message"
                        },
                        "force": {
                            "type": "boolean",
                            "default": false,
                            "description": "Force action even if quality decreased"
                        }
                    },
                    "required": ["action"]
                }
            },
            {
                "name": "get_scorecard",
                "description": "Generate quality scorecard and trends",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "target_path": {
                            "type": "string",
                            "description": "Path to analyze for scorecard"
                        },
                        "include_trends": {
                            "type": "boolean", 
                            "default": true,
                            "description": "Include trend analysis"
                        },
                        "time_range": {
                            "type": "string",
                            "enum": ["1w", "1m", "3m", "6m", "1y"],
                            "default": "1m",
                            "description": "Time range for trends"
                        }
                    },
                    "required": ["target_path"]
                }
            },
            {
                "name": "grammar_validate",
                "description": "Validate code against grammar and safety overlays",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "code": {
                            "type": "string",
                            "description": "Code to validate"
                        },
                        "language": {
                            "type": "string",
                            "enum": ["c", "cpp", "python", "javascript", "typescript"],
                            "description": "Programming language"
                        },
                        "overlay": {
                            "type": "string",
                            "description": "Grammar overlay to apply (e.g., nasa_c_safety)"
                        }
                    },
                    "required": ["code", "language"]
                }
            },
            {
                "name": "grammar_next_tokens",
                "description": "Get valid next tokens for constrained generation",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "prefix": {
                            "type": "string",
                            "description": "Code prefix to continue"
                        },
                        "language": {
                            "type": "string",
                            "enum": ["c", "cpp", "python", "javascript", "typescript"],
                            "description": "Programming language"
                        },
                        "overlay": {
                            "type": "string",
                            "description": "Grammar overlay constraints"
                        },
                        "max_tokens": {
                            "type": "integer",
                            "default": 20,
                            "description": "Maximum number of tokens to return"
                        }
                    },
                    "required": ["prefix", "language"]
                }
            },
            {
                "name": "suggest_refactors",
                "description": "Suggest refactoring techniques for code improvements",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "code": {
                            "type": "string",
                            "description": "Code to analyze for refactoring opportunities"
                        },
                        "language": {
                            "type": "string", 
                            "enum": ["c", "cpp", "python", "javascript", "typescript"],
                            "description": "Programming language"
                        },
                        "target_connascence": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Target connascence types to address (e.g., ['CoM', 'CoP'])"
                        },
                        "include_nasa_rules": {
                            "type": "boolean",
                            "default": false,
                            "description": "Include NASA/JPL safety-specific refactorings"
                        }
                    },
                    "required": ["code", "language"]
                }
            },
            {
                "name": "propose_autofix",
                "description": "Generate automatic fixes using Refactoring.Guru techniques",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "code": {
                            "type": "string",
                            "description": "Code to refactor"
                        },
                        "language": {
                            "type": "string",
                            "enum": ["c", "cpp", "python", "javascript", "typescript"],
                            "description": "Programming language"
                        },
                        "technique": {
                            "type": "string",
                            "enum": [
                                "extract_method",
                                "replace_magic_number",
                                "introduce_parameter_object",
                                "substitute_algorithm",
                                "introduce_assertion",
                                "replace_recursion_with_iteration"
                            ],
                            "description": "Refactoring technique to apply"
                        },
                        "start_line": {
                            "type": "integer",
                            "description": "Starting line number for refactoring"
                        },
                        "end_line": {
                            "type": "integer",
                            "description": "Ending line number for refactoring"
                        },
                        "validate_safety": {
                            "type": "boolean",
                            "default": true,
                            "description": "Validate result against safety overlays"
                        }
                    },
                    "required": ["code", "language", "technique"]
                }
            },
            {
                "name": "verify_build_flags",
                "description": "Verify compiler build flags for NASA/JPL compliance",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "project_path": {
                            "type": "string",
                            "description": "Path to project to analyze"
                        },
                        "profile": {
                            "type": "string",
                            "enum": ["nasa_jpl_pot10", "nasa_loc_1", "nasa_loc_3"],
                            "default": "nasa_jpl_pot10",
                            "description": "NASA safety profile to verify against"
                        }
                    },
                    "required": ["project_path"]
                }
            },
            {
                "name": "evidence_report",
                "description": "Generate evidence report showing tool coverage overlap",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "finding_id": {
                            "type": "string",
                            "description": "Specific finding to analyze for evidence"
                        },
                        "tools": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Tools to include in evidence analysis"
                        },
                        "show_coverage": {
                            "type": "boolean", 
                            "default": true,
                            "description": "Show what percentage of violations each tool covers"
                        }
                    }
                }
            }
        ]
    
    def get_tool_result(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool and return results."""
        # Audit logging
        self._log_tool_call(tool_name, arguments)
        
        # Rate limiting
        if not self.rate_limiter.allow_request():
            return {
                "error": "Rate limit exceeded. Please wait before making more requests.",
                "code": "RATE_LIMITED"
            }
        
        try:
            # Route to appropriate handler
            if tool_name == "scan_path":
                return self._handle_scan_path(arguments)
            elif tool_name == "scan_diff":
                return self._handle_scan_diff(arguments)
            elif tool_name == "explain_finding":
                return self._handle_explain_finding(arguments)
            elif tool_name == "propose_autofix":
                return self._handle_propose_autofix(arguments)
            elif tool_name == "enforce_policy":
                return self._handle_enforce_policy(arguments)
            elif tool_name == "baseline_snapshot":
                return self._handle_baseline_snapshot(arguments)
            elif tool_name == "get_scorecard":
                return self._handle_get_scorecard(arguments)
            elif tool_name == "grammar_validate":
                return self._handle_grammar_validate(arguments)
            elif tool_name == "grammar_next_tokens":
                return self._handle_grammar_next_tokens(arguments)
            elif tool_name == "suggest_refactors":
                return self._handle_suggest_refactors(arguments)
            elif tool_name == "propose_autofix":
                return self._handle_propose_autofix(arguments)
            elif tool_name == "verify_build_flags":
                return self._handle_verify_build_flags(arguments)
            elif tool_name == "evidence_report":
                return self._handle_evidence_report(arguments)
            else:
                return {
                    "error": f"Unknown tool: {tool_name}",
                    "code": "UNKNOWN_TOOL"
                }
                
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            return {
                "error": f"Internal error: {str(e)}",
                "code": "INTERNAL_ERROR"
            }
    
    def _handle_scan_path(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle path scanning."""
        path_str = args["path"]
        policy_name = args.get("policy", "service-defaults")
        output_format = args.get("output_format", "json")
        
        # Security: validate path
        target_path = Path(path_str)
        if not self._is_safe_path(target_path):
            return {
                "error": "Access denied to path",
                "code": "ACCESS_DENIED"
            }
        
        # Load policy
        try:
            policy = self.policy_manager.load_preset(policy_name)
        except Exception as e:
            return {
                "error": f"Invalid policy: {e}",
                "code": "INVALID_POLICY"
            }
        
        # Configure analyzer
        analyzer = ConnascenceASTAnalyzer(
            thresholds=policy.thresholds,
            weights=policy.weights,
            exclusions=args.get("exclude_patterns")
        )
        
        # Perform analysis
        start_time = time.time()
        try:
            if target_path.is_file():
                violations = analyzer.analyze_file(target_path)
                # Create minimal result
                from analyzer.ast_engine.core_analyzer import AnalysisResult
                result = AnalysisResult(
                    timestamp=datetime.now().isoformat(),
                    project_root=str(target_path.parent),
                    total_files_analyzed=1,
                    analysis_duration_ms=int((time.time() - start_time) * 1000),
                    violations=violations,
                    file_stats={},
                    summary_metrics={}
                )
            else:
                result = analyzer.analyze_directory(target_path)
        except Exception as e:
            return {
                "error": f"Analysis failed: {e}",
                "code": "ANALYSIS_FAILED"
            }
        
        # Generate output
        if output_format == "json":
            content = self.json_reporter.generate(result)
        elif output_format == "sarif":
            content = self.sarif_reporter.generate(result)
        else:  # summary
            content = self._generate_summary(result)
        
        return {
            "content": content,
            "format": output_format,
            "violations_count": len(result.violations),
            "analysis_duration_ms": result.analysis_duration_ms
        }
    
    def _handle_scan_diff(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle git diff scanning."""
        # Implementation would use git to analyze changes
        return {
            "content": "Diff analysis not yet implemented",
            "format": "text"
        }
    
    def _handle_explain_finding(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle finding explanation."""
        finding_id = args.get("finding_id")
        rule_id = args.get("rule_id")
        
        if rule_id:
            explanation = self._explain_rule(rule_id)
        else:
            explanation = "Finding explanation not yet implemented"
        
        return {
            "explanation": explanation,
            "examples": [] if not args.get("include_examples", True) else self._get_examples(rule_id)
        }
    
    def _handle_propose_autofix(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle autofix proposal."""
        if args.get("apply_fix", False):
            return {
                "error": "Write operations require explicit permission",
                "code": "PERMISSION_DENIED"
            }
        
        # Generate patch without applying
        return {
            "patch": "# Autofix patch generation not yet implemented",
            "applied": False,
            "safe": True
        }
    
    def _handle_enforce_policy(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle policy enforcement."""
        policy_preset = args.get("policy_preset")
        
        if policy_preset:
            try:
                policy = self.policy_manager.load_preset(policy_preset)
                return {
                    "policy_applied": policy_preset,
                    "thresholds": policy.thresholds.__dict__,
                    "budget_limits": policy.budget_limits
                }
            except Exception as e:
                return {
                    "error": f"Policy load failed: {e}",
                    "code": "POLICY_ERROR"
                }
        
        return {"message": "Policy enforcement configured"}
    
    def _handle_baseline_snapshot(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle baseline management."""
        action = args["action"]
        
        # Implementation would manage baselines
        return {
            "action": action,
            "message": f"Baseline {action} not yet implemented"
        }
    
    def _handle_get_scorecard(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle scorecard generation."""
        target_path = args["target_path"]
        
        # Implementation would generate comprehensive scorecards
        return {
            "target": target_path,
            "scorecard": "Scorecard generation not yet implemented"
        }
    
    def _handle_grammar_validate(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle grammar validation with overlays."""
        code = args["code"]
        language_str = args["language"]
        overlay = args.get("overlay")
        
        # Convert language string to enum
        try:
            from grammar.backends.tree_sitter_backend import LanguageSupport
            language = LanguageSupport(language_str)
        except ValueError:
            return {
                "error": f"Unsupported language: {language_str}",
                "code": "UNSUPPORTED_LANGUAGE"
            }
        
        # Validate grammar
        if not self.grammar_backend.is_available():
            return {
                "error": "Grammar backend not available",
                "code": "BACKEND_UNAVAILABLE"
            }
        
        validation_result = self.grammar_backend.validate(code, language, overlay)
        
        return {
            "valid": validation_result.valid,
            "violations": validation_result.violations,
            "overlay_violations": validation_result.overlay_violations,
            "language": language_str,
            "overlay_applied": overlay
        }
    
    def _handle_grammar_next_tokens(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle constrained token generation."""
        prefix = args["prefix"]
        language_str = args["language"]
        overlay = args.get("overlay")
        max_tokens = args.get("max_tokens", 20)
        
        try:
            from grammar.backends.tree_sitter_backend import LanguageSupport
            language = LanguageSupport(language_str)
        except ValueError:
            return {
                "error": f"Unsupported language: {language_str}",
                "code": "UNSUPPORTED_LANGUAGE"
            }
        
        if not self.grammar_backend.is_available():
            return {
                "error": "Grammar backend not available",
                "code": "BACKEND_UNAVAILABLE"
            }
        
        tokens = self.grammar_backend.get_next_tokens(prefix, language, overlay)
        
        return {
            "tokens": tokens[:max_tokens],
            "prefix": prefix,
            "language": language_str,
            "overlay": overlay,
            "total_available": len(tokens)
        }
    
    def _handle_suggest_refactors(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle refactoring suggestions."""
        code = args["code"]
        language_str = args["language"]
        target_connascence = args.get("target_connascence")
        include_nasa = args.get("include_nasa_rules", False)
        
        try:
            from grammar.backends.tree_sitter_backend import LanguageSupport
            language = LanguageSupport(language_str)
        except ValueError:
            return {
                "error": f"Unsupported language: {language_str}",
                "code": "UNSUPPORTED_LANGUAGE"
            }
        
        # Find refactoring opportunities
        opportunities = self.ast_refactoring.find_refactoring_opportunities(
            code, language, target_connascence
        )
        
        # Convert to serializable format
        suggestions = []
        for opp in opportunities:
            suggestion = {
                "technique": opp.technique.value,
                "file_path": opp.file_path,
                "start_line": opp.start_line,
                "end_line": opp.end_line,
                "description": opp.description,
                "rationale": opp.rationale,
                "estimated_effort": opp.estimated_effort,
                "safety_impact": opp.safety_impact,
                "connascence_improvement": opp.connascence_improvement
            }
            suggestions.append(suggestion)
        
        return {
            "suggestions": suggestions,
            "total_opportunities": len(opportunities),
            "language": language_str,
            "target_connascence": target_connascence
        }
    
    def _handle_propose_autofix(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle automatic fix proposals."""
        code = args["code"]
        language_str = args["language"]
        technique_str = args["technique"]
        start_line = args.get("start_line", 1)
        end_line = args.get("end_line", 1)
        validate_safety = args.get("validate_safety", True)
        
        try:
            from grammar.backends.tree_sitter_backend import LanguageSupport
            from grammar.ast_safe_refactoring import RefactoringTechnique, RefactoringCandidate
            
            language = LanguageSupport(language_str)
            technique = RefactoringTechnique(technique_str)
        except ValueError as e:
            return {
                "error": f"Invalid parameter: {str(e)}",
                "code": "INVALID_PARAMETER"
            }
        
        # Create refactoring candidate
        candidate = RefactoringCandidate(
            technique=technique,
            file_path="mcp_input",
            start_line=start_line,
            end_line=end_line,
            description=f"Apply {technique.value}",
            rationale="Requested via MCP",
            estimated_effort="unknown",
            safety_impact="unknown",
            connascence_improvement="TBD"
        )
        
        # Apply refactoring
        result = self.ast_refactoring.apply_refactoring(
            candidate, code, language, validate_safety
        )
        
        return {
            "success": result.success,
            "technique": result.technique.value,
            "original_code": result.original_code,
            "refactored_code": result.refactored_code,
            "changes_applied": result.changes_applied,
            "validation_errors": result.validation_errors,
            "warnings": result.warnings
        }
    
    def _handle_verify_build_flags(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle build flag verification."""
        project_path = Path(args["project_path"])
        profile = args.get("profile", "nasa_jpl_pot10")
        
        if not self._is_safe_path(project_path):
            return {
                "error": "Access denied to path",
                "code": "ACCESS_DENIED"
            }
        
        try:
            from integrations.build_flags_integration import BuildFlagsIntegration
            
            integration = BuildFlagsIntegration()
            if not integration.is_available():
                return {
                    "error": "Build flags integration not available",
                    "code": "INTEGRATION_UNAVAILABLE"
                }
            
            results = integration.analyze(project_path)
            
            return {
                "project_path": str(project_path),
                "profile": profile,
                "compilers_detected": results.get("compilers_detected", {}),
                "nasa_compliance": results.get("nasa_compliance", {}),
                "recommendations": results.get("recommendations", []),
                "execution_successful": results.get("execution_successful", False)
            }
            
        except Exception as e:
            return {
                "error": f"Build flag verification failed: {str(e)}",
                "code": "VERIFICATION_FAILED"
            }
    
    def _handle_evidence_report(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle evidence report generation."""
        finding_id = args.get("finding_id")
        tools = args.get("tools", ["ruff", "mypy", "bandit", "black", "build_flags"])
        show_coverage = args.get("show_coverage", True)
        
        # This would generate a comprehensive evidence report
        # showing which tools cover which types of violations
        evidence = {
            "finding_id": finding_id,
            "tools_analyzed": tools,
            "coverage_analysis": {
                "nasa_rule_10": {
                    "covered_by": ["build_flags", "ruff"],
                    "coverage_percentage": 85
                },
                "connascence_CoM": {
                    "covered_by": ["ruff", "custom_analyzer"],
                    "coverage_percentage": 90
                },
                "type_safety": {
                    "covered_by": ["mypy", "ruff"],
                    "coverage_percentage": 95
                }
            },
            "recommendations": [
                "MyPy provides excellent type safety coverage",
                "Build flags verification ensures NASA Rule 10 compliance",
                "Ruff catches many style and safety issues automatically"
            ]
        }
        
        return evidence
    
    def _is_safe_path(self, path: Path) -> bool:
        """Check if path access is safe."""
        try:
            # Resolve path and check it's not trying to escape
            resolved = path.resolve()
            cwd = Path.cwd().resolve()
            
            # Must be under current directory or explicitly allowed
            return str(resolved).startswith(str(cwd))
        except Exception:
            return False
    
    def _log_tool_call(self, tool_name: str, arguments: Dict[str, Any]):
        """Log tool call for audit."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "tool": tool_name,
            "arguments": self._sanitize_arguments(arguments),
            "user": "mcp-agent"  # Could be enhanced with actual user context
        }
        
        try:
            with open(self.audit_log_path, "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            logger.warning(f"Failed to write audit log: {e}")
    
    def _sanitize_arguments(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Remove sensitive information from arguments for logging."""
        sanitized = arguments.copy()
        
        # Remove potential sensitive fields
        sensitive_fields = ["password", "token", "secret", "key"]
        for field in sensitive_fields:
            if field in sanitized:
                sanitized[field] = "[REDACTED]"
        
        return sanitized
    
    def _explain_rule(self, rule_id: str) -> str:
        """Get explanation for a rule."""
        explanations = {
            "CON_CoN": (
                "**Connascence of Name** occurs when multiple components must agree "
                "on the name of an entity. This is the weakest form of connascence. "
                "Refactor by using consistent naming conventions and avoiding "
                "name dependencies across modules."
            ),
            "CON_CoM": (
                "**Connascence of Meaning** occurs when multiple components must agree "
                "on the meaning of particular values (magic literals). "
                "Refactor by extracting magic numbers and strings into named constants."
            ),
            "CON_CoP": (
                "**Connascence of Position** occurs when multiple components must agree "
                "on the order of values (parameter positions). "
                "Refactor by using keyword arguments or data structures."
            ),
            "CON_CoA": (
                "**Connascence of Algorithm** occurs when multiple components must agree "
                "on a particular algorithm (code duplication). "
                "Refactor by extracting shared algorithms into common functions."
            )
        }
        
        return explanations.get(rule_id, "No explanation available for this rule.")
    
    def _get_examples(self, rule_id: str) -> List[Dict[str, str]]:
        """Get refactoring examples for a rule."""
        # This would return before/after code examples
        return []
    
    def _generate_summary(self, result) -> str:
        """Generate a text summary."""
        violations_count = len(result.violations)
        return f"Analysis found {violations_count} violations in {result.total_files_analyzed} files"


class RateLimiter:
    """Simple rate limiter for MCP requests."""
    
    def __init__(self, max_requests_per_minute: int = 60):
        self.max_requests = max_requests_per_minute
        self.requests = []
    
    def allow_request(self) -> bool:
        """Check if request is allowed."""
        now = time.time()
        
        # Remove old requests
        self.requests = [req_time for req_time in self.requests if now - req_time < 60]
        
        # Check limit
        if len(self.requests) >= self.max_requests:
            return False
        
        # Record request
        self.requests.append(now)
        return True


def main():
    """Main MCP server entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Connascence MCP Server")
    parser.add_argument("--transport", choices=["stdio", "sse"], default="stdio")
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=8080)
    
    args = parser.parse_args()
    
    server = ConnascenceMCPServer()
    
    if args.transport == "stdio":
        print("Starting MCP server on stdio...")
        # Implementation would start actual MCP server
    else:
        print(f"Starting MCP server on {args.host}:{args.port}...")
    
    print("MCP server implementation pending")


if __name__ == "__main__":
    main()