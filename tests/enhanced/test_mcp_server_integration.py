# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2024 Connascence Safety Analyzer Contributors

"""
MCP Server Enhanced Integration Tests
====================================

Comprehensive tests for MCP server enhanced pipeline integration:
- Enhanced pipeline context retrieval via subprocess
- Smart recommendation integration in AI fix generation
- Cross-phase correlation data in AI prompts  
- Enhanced fix and suggestion generation with architectural intelligence
- Error handling and graceful degradation
"""

import json
from unittest.mock import Mock, patch

import pytest

from .test_infrastructure import (
    EnhancedTestDatasets,
    MockEnhancedAnalyzer,
    integration_test,
    performance_test,
)


@pytest.fixture
def enhanced_test_datasets():
    """Provide enhanced test datasets"""
    return EnhancedTestDatasets()


@pytest.fixture
def sample_code_file(tmp_path):
    """Create temporary Python file for testing"""
    code_content = """
class TestClass:
    def __init__(self, config):
        # CofE: Identity - class structure depends on config
        self.setting = config["setting"]
        
    def process(self, data, format="json"):
        # CofE: Position - parameter order dependency
        # CofE: Meaning - format string coupling
        if format == "json":
            return {"result": data}
        else:
            return str(data)
"""

    code_file = tmp_path / "test_code.py"
    code_file.write_text(code_content, encoding="utf-8")
    return code_file


class TestMCPServerEnhancedIntegration:
    """Test suite for MCP server enhanced pipeline integration."""

    @integration_test(["mcp_server"])
    def test_enhanced_pipeline_context_retrieval_success(self, enhanced_test_datasets, sample_code_file):
        """Test successful enhanced pipeline context retrieval via subprocess."""
        mock_analyzer = MockEnhancedAnalyzer("success")

        # Mock subprocess for enhanced analyzer
        with patch("subprocess.spawn") as mock_spawn:
            # Setup mock process
            mock_process = Mock()
            mock_process.stdout = Mock()
            mock_process.stderr = Mock()
            mock_process.on = Mock()
            mock_spawn.return_value = mock_process

            # Simulate successful analysis result
            enhanced_result = mock_analyzer.analyze_path(
                str(sample_code_file),
                enable_cross_phase_correlation=True,
                enable_audit_trail=True,
                enable_smart_recommendations=True,
            )

            # Mock subprocess stdout with JSON result
            mock_stdout = json.dumps(enhanced_result)

            # Simulate context retrieval
            context = self._simulate_enhanced_context_retrieval(
                finding={"file": str(sample_code_file), "type": "connascence_of_literal"}, mock_stdout=mock_stdout
            )

            # Validate context structure
            assert "smart_recommendations" in context
            assert "correlations" in context
            assert "audit_trail" in context
            assert "cross_phase_analysis" in context

            # Validate content quality
            assert len(context["smart_recommendations"]) > 0
            assert len(context["correlations"]) > 0
            assert context["cross_phase_analysis"] == True

    @integration_test(["mcp_server"])
    def test_enhanced_pipeline_context_timeout_handling(self):
        """Test timeout handling in enhanced pipeline context retrieval."""
        with patch("subprocess.spawn") as mock_spawn:
            mock_process = Mock()
            mock_spawn.return_value = mock_process

            # Simulate timeout scenario
            def simulate_timeout(*args, **kwargs):
                import time

                time.sleep(35)  # Exceed 30 second timeout

            mock_process.on.side_effect = simulate_timeout

            # Should handle timeout gracefully
            context = self._simulate_enhanced_context_retrieval(
                finding={"file": "/test/path", "type": "test"}, simulate_timeout=True
            )

            # Should return empty context on timeout
            assert context["smart_recommendations"] == []
            assert context["correlations"] == []
            assert context["cross_phase_analysis"] == False
            assert context.get("timeout") == True

    @integration_test(["mcp_server"])
    def test_enhanced_pipeline_context_error_handling(self):
        """Test error handling for enhanced pipeline context retrieval."""
        error_scenarios = [
            ("process_error", "Failed to spawn process"),
            ("parse_error", "Invalid JSON output"),
            ("analyzer_failure", "Python analysis failed"),
        ]

        for scenario, expected_behavior in error_scenarios:
            with patch("subprocess.spawn") as mock_spawn:
                if scenario == "process_error":
                    mock_spawn.side_effect = Exception("Process spawn failed")
                elif scenario == "parse_error":
                    mock_process = Mock()
                    mock_process.stdout = "Invalid JSON"
                    mock_spawn.return_value = mock_process
                elif scenario == "analyzer_failure":
                    mock_process = Mock()
                    mock_process.returncode = 1
                    mock_process.stderr = "Analysis failed"
                    mock_spawn.return_value = mock_process

                context = self._simulate_enhanced_context_retrieval(
                    finding={"file": "/test/path", "type": "test"}, scenario=scenario
                )

                # Should return safe empty context
                assert context["smart_recommendations"] == []
                assert context["correlations"] == []
                assert context["cross_phase_analysis"] == False

                # Should include error information
                assert any(key in context for key in ["spawn_error", "parse_error", "error"])

    @integration_test(["mcp_server"])
    @performance_test(max_time_seconds=3.0, max_memory_mb=30.0)
    async def test_ai_fix_generation_with_enhanced_context(self, enhanced_test_datasets):
        """Test AI fix generation enhanced with smart recommendations and correlations."""
        # Mock finding with enhanced context
        finding = {
            "id": "test_001",
            "type": "connascence_of_literal",
            "severity": "high",
            "message": "Magic number detected",
            "file": "/test/sample.py",
            "line": 10,
        }

        # Mock enhanced context
        enhanced_context = {
            "correlations": [
                {
                    "analyzer1": "ast_analyzer",
                    "analyzer2": "mece_analyzer",
                    "correlation_score": 0.85,
                    "description": "Magic number correlates with algorithm duplication",
                    "priority": "high",
                    "remediation_impact": "Fixing magic numbers will reduce duplication",
                }
            ],
            "smart_recommendations": [
                {
                    "category": "Constants Extraction",
                    "description": "Extract magic numbers to named constants",
                    "priority": "high",
                    "impact": "high",
                    "effort": "low",
                    "rationale": "Multiple magic numbers detected",
                }
            ],
            "cross_phase_analysis": True,
            "canonical_policy": "standard",
        }

        # Generate enhanced fix prompt
        enhanced_prompt = self._build_enhanced_fix_prompt(finding, "test context", {}, enhanced_context)

        # Validate enhanced prompt content
        assert "ENHANCED ARCHITECTURAL ANALYSIS" in enhanced_prompt
        assert "Cross-Phase Correlations" in enhanced_prompt
        assert "Smart Architectural Recommendations" in enhanced_prompt
        assert "ast_analyzer ↔ mece_analyzer (85.0% correlation)" in enhanced_prompt
        assert "Constants Extraction" in enhanced_prompt
        assert "Account for cross-analyzer correlations" in enhanced_prompt

        # Mock AI provider response
        mock_ai_response = {
            "code": "# Extract constants\nSTATUS_ACTIVE = 1\nMAX_USERS = 100",
            "description": "Extracted magic numbers to named constants",
            "confidence": 92,
            "safety": "safe",
            "architectural_pattern": "Constants Pattern",
            "enhanced_rationale": "Based on correlation analysis and smart recommendations",
            "correlation_impact": "Reduces correlation between AST and MECE analyzers",
            "recommendation_alignment": "Implements Constants Extraction recommendation",
        }

        # Simulate AI fix generation
        with patch("ai_provider.call") as mock_ai_call:
            mock_ai_call.return_value = mock_ai_response

            fix_result = await self._simulate_ai_fix_generation(finding, enhanced_context, mock_ai_response)

            # Validate enhanced fix result
            assert fix_result["patch"] == mock_ai_response["code"]
            assert fix_result["confidence"] == 92
            assert "enhanced_recommendations" in fix_result
            assert "cross_phase_analysis" in fix_result
            assert len(fix_result["enhanced_recommendations"]) > 0

    @integration_test(["mcp_server"])
    async def test_ai_suggestion_generation_with_enhanced_context(self, enhanced_test_datasets):
        """Test AI suggestion generation enhanced with pipeline recommendations."""
        finding = {
            "type": "connascence_of_position",
            "message": "Excessive parameter coupling detected",
            "severity": "critical",
            "file": "/test/sample.py",
        }

        enhanced_context = {
            "correlations": [
                {
                    "analyzer1": "ast_analyzer",
                    "analyzer2": "nasa_analyzer",
                    "correlation_score": 0.72,
                    "description": "Parameter count violates NASA guidelines",
                }
            ],
            "smart_recommendations": [
                {
                    "category": "Parameter Refactoring",
                    "description": "Use configuration object pattern",
                    "priority": "medium",
                    "impact": "medium",
                    "effort": "medium",
                }
            ],
        }

        # Generate enhanced suggestions prompt
        enhanced_suggestions_prompt = self._build_enhanced_suggestions_prompt(
            finding, "test context", {}, enhanced_context
        )

        # Validate enhanced suggestions prompt
        assert "ENHANCED ARCHITECTURAL CONTEXT" in enhanced_suggestions_prompt
        assert "Cross-Phase Correlations:" in enhanced_suggestions_prompt
        assert "Smart Architectural Recommendations:" in enhanced_suggestions_prompt
        assert "Parameter count violates NASA guidelines" in enhanced_suggestions_prompt
        assert "Use configuration object pattern" in enhanced_suggestions_prompt

        # Mock AI suggestions response
        mock_ai_suggestions = [
            {
                "technique": "Configuration Object",
                "description": "Replace parameter list with configuration object",
                "confidence": 88,
                "complexity": "medium",
                "risk": "low",
                "coupling_impact": "reduces connascence of position",
                "architectural_pattern": "Parameter Object",
                "enhanced_rationale": "Aligns with smart recommendations for parameter reduction",
            }
        ]

        # Simulate suggestions generation with enhanced context
        suggestions_result = await self._simulate_ai_suggestions_generation(
            finding, enhanced_context, mock_ai_suggestions
        )

        # Validate enhanced suggestions
        ai_suggestions = suggestions_result["ai_suggestions"]
        pipeline_suggestions = suggestions_result["pipeline_suggestions"]

        assert len(ai_suggestions) > 0
        assert len(pipeline_suggestions) > 0

        # Verify pipeline suggestions are properly formatted
        pipeline_suggestion = pipeline_suggestions[0]
        assert pipeline_suggestion["technique"] == "Smart Rec: Parameter Refactoring"
        assert pipeline_suggestion["source"] == "enhanced_pipeline"
        assert pipeline_suggestion["complexity"] == "medium"

    @integration_test(["mcp_server"])
    def test_enhanced_prompt_building_comprehensive(self, enhanced_test_datasets):
        """Test comprehensive enhanced prompt building with all features."""
        finding = {
            "type": "connascence_of_algorithm",
            "message": "Algorithm duplication detected",
            "severity": "medium",
            "file": "/test/complex.py",
            "line": 45,
        }

        # Comprehensive enhanced context
        enhanced_context = {
            "correlations": [
                {
                    "analyzer1": "ast_analyzer",
                    "analyzer2": "mece_analyzer",
                    "correlation_score": 0.91,
                    "description": "Algorithm duplication correlates with connascence violations",
                    "priority": "high",
                    "affected_files": ["/test/complex.py", "/test/utils.py"],
                    "remediation_impact": "Strategy pattern will reduce both issues",
                }
            ],
            "smart_recommendations": [
                {
                    "category": "Design Patterns",
                    "description": "Apply Strategy pattern to eliminate duplication",
                    "priority": "high",
                    "impact": "high",
                    "effort": "medium",
                    "rationale": "Multiple algorithm variants detected",
                    "implementation_notes": "Create AlgorithmStrategy interface with concrete implementations",
                }
            ],
            "canonical_policy": "strict",
            "components_used": {
                "ast_analyzer": True,
                "mece_analyzer": True,
                "nasa_analyzer": False,
                "smart_integration": True,
            },
        }

        # Build comprehensive enhanced prompt
        comprehensive_prompt = self._build_enhanced_fix_prompt(
            finding, "Comprehensive test context", {}, enhanced_context
        )

        # Validate all enhanced features are included
        expected_sections = [
            "senior software architect",
            "ENHANCED ARCHITECTURAL ANALYSIS",
            "Cross-Phase Correlations (1 found)",
            "Smart Architectural Recommendations (1 generated)",
            "Active Policy: strict",
            "Active Analyzers: ast_analyzer, mece_analyzer, smart_integration",
            "Account for cross-analyzer correlations",
            "Align with smart architectural recommendations",
            "enhanced_rationale",
            "correlation_impact",
            "recommendation_alignment",
        ]

        for expected_section in expected_sections:
            assert expected_section in comprehensive_prompt, f"Missing expected section: {expected_section}"

        # Validate specific enhanced content
        assert "91.0% correlation" in comprehensive_prompt
        assert "Strategy pattern will reduce both issues" in comprehensive_prompt
        assert "Create AlgorithmStrategy interface" in comprehensive_prompt

    @integration_test(["mcp_server"])
    def test_mcp_ai_provider_integration(self):
        """Test MCP server AI provider integration with enhanced context."""
        # Mock multiple AI providers
        mock_providers = {"openai": Mock(), "anthropic": Mock(), "google": Mock()}

        enhanced_context = {
            "correlations": [{"analyzer1": "ast", "analyzer2": "mece", "correlation_score": 0.8}],
            "smart_recommendations": [{"category": "Test", "description": "Test recommendation"}],
        }

        finding = {"type": "test", "message": "test violation"}

        # Test each provider type
        for provider_name, mock_provider in mock_providers.items():
            # Mock successful provider response
            mock_response = {
                "code": f"# Fix from {provider_name}",
                "description": f"Generated by {provider_name}",
                "confidence": 85,
                "safety": "safe",
            }

            # Simulate provider call with enhanced context
            with patch(f"ai_provider.call_{provider_name}") as mock_call:
                mock_call.return_value = mock_response

                result = self._simulate_provider_integration(provider_name, finding, enhanced_context, mock_response)

                # Validate enhanced context is preserved
                assert "enhanced_recommendations" in result
                assert "cross_phase_analysis" in result
                assert len(result["enhanced_recommendations"]) > 0

    # Helper methods for MCP server testing

    def _simulate_enhanced_context_retrieval(self, finding, mock_stdout=None, simulate_timeout=False, scenario=None):
        """Simulate enhanced pipeline context retrieval."""
        if simulate_timeout:
            return {
                "smart_recommendations": [],
                "correlations": [],
                "audit_trail": [],
                "cross_phase_analysis": False,
                "timeout": True,
            }

        if scenario == "process_error":
            return {
                "smart_recommendations": [],
                "correlations": [],
                "audit_trail": [],
                "cross_phase_analysis": False,
                "spawn_error": "Process spawn failed",
            }

        if scenario == "parse_error":
            return {
                "smart_recommendations": [],
                "correlations": [],
                "audit_trail": [],
                "cross_phase_analysis": False,
                "parse_error": "Invalid JSON output",
            }

        if scenario == "analyzer_failure":
            return {
                "smart_recommendations": [],
                "correlations": [],
                "audit_trail": [],
                "cross_phase_analysis": False,
                "error": "Pipeline exit code: 1",
            }

        # Success scenario
        if mock_stdout:
            result = json.loads(mock_stdout)
            return {
                "smart_recommendations": result.get("smart_recommendations", []),
                "correlations": result.get("correlations", []),
                "audit_trail": result.get("audit_trail", []),
                "cross_phase_analysis": result.get("cross_phase_analysis", False),
                "canonical_policy": result.get("canonical_policy"),
                "components_used": result.get("components_used", {}),
                "policy_config": result.get("policy_config", {}),
            }

        return {"smart_recommendations": [], "correlations": [], "audit_trail": [], "cross_phase_analysis": False}

    def _build_enhanced_fix_prompt(self, finding, context, options, enhanced_context):
        """Build enhanced AI fix prompt with architectural intelligence."""
        prompt = f"""You are a senior software architect with access to advanced cross-phase connascence analysis. Generate an optimal fix for this violation:

Type: {finding['type']}
Message: {finding['message']}
Severity: {finding['severity']}
File: {finding.get('file', 'unknown')}
Line: {finding.get('line', 'unknown')}

Context:
{context}"""

        if enhanced_context.get("correlations") or enhanced_context.get("smart_recommendations"):
            prompt += "\n\n=== ENHANCED ARCHITECTURAL ANALYSIS ==="

            if enhanced_context.get("correlations"):
                correlations = enhanced_context["correlations"]
                prompt += f"\n\nCross-Phase Correlations ({len(correlations)} found):"

                for i, corr in enumerate(correlations[:5]):
                    score = corr["correlation_score"] * 100
                    priority = corr.get("priority", "medium")
                    prompt += f"\n{i+1}. [{priority.upper()}] {corr['analyzer1']} ↔ {corr['analyzer2']} ({score:.1f}% correlation)"
                    prompt += f"\n   Impact: {corr['description']}"
                    if corr.get("remediation_impact"):
                        prompt += f"\n   Remediation: {corr['remediation_impact']}"

            if enhanced_context.get("smart_recommendations"):
                recommendations = enhanced_context["smart_recommendations"]
                prompt += f"\n\nSmart Architectural Recommendations ({len(recommendations)} generated):"

                for i, rec in enumerate(recommendations[:4]):
                    prompt += (
                        f"\n{i+1}. [{rec.get('priority', 'medium').upper()} PRIORITY] {rec.get('category', 'General')}"
                    )
                    prompt += f"\n   Recommendation: {rec['description']}"
                    prompt += f"\n   Impact: {rec.get('impact', 'unknown')} | Effort: {rec.get('effort', 'unknown')}"
                    if rec.get("implementation_notes"):
                        prompt += f"\n   Implementation: {rec['implementation_notes']}"

            if enhanced_context.get("canonical_policy"):
                prompt += f"\n\nActive Policy: {enhanced_context['canonical_policy']}"

            if enhanced_context.get("components_used"):
                active_components = [k for k, v in enhanced_context["components_used"].items() if v]
                if active_components:
                    prompt += f"\nActive Analyzers: {', '.join(active_components)}"

        prompt += "\n\n=== REQUIREMENTS ==="
        prompt += "\n- Generate working code that eliminates the connascence violation"
        prompt += "\n- Preserve all functionality while reducing coupling strength"
        prompt += "\n- Apply architectural patterns identified in enhanced analysis"
        if enhanced_context.get("correlations"):
            prompt += "\n- Account for cross-analyzer correlations to prevent cascade effects"
        if enhanced_context.get("smart_recommendations"):
            prompt += "\n- Align with smart architectural recommendations for long-term maintainability"

        return prompt

    def _build_enhanced_suggestions_prompt(self, finding, context, options, enhanced_context):
        """Build enhanced AI suggestions prompt."""
        prompt = f"""Generate comprehensive refactoring suggestions for this connascence violation using advanced architectural analysis:

Type: {finding['type']}
Message: {finding['message']}
Severity: {finding['severity']}
File: {finding.get('file', 'unknown')}

Context:
{context}"""

        if enhanced_context.get("correlations") or enhanced_context.get("smart_recommendations"):
            prompt += "\n\n=== ENHANCED ARCHITECTURAL CONTEXT ==="

            if enhanced_context.get("correlations"):
                prompt += "\nCross-Phase Correlations:"
                for corr in enhanced_context["correlations"][:3]:
                    score = corr["correlation_score"] * 100
                    prompt += f"\n• {corr['analyzer1']} ↔ {corr['analyzer2']} ({score:.1f}%): {corr['description']}"

            if enhanced_context.get("smart_recommendations"):
                prompt += "\nSmart Architectural Recommendations:"
                for rec in enhanced_context["smart_recommendations"][:3]:
                    prompt += f"\n• [{rec.get('priority', 'medium')}] {rec.get('category')}: {rec['description']}"

        return prompt

    async def _simulate_ai_fix_generation(self, finding, enhanced_context, mock_response):
        """Simulate AI fix generation with enhanced context."""
        return {
            "patch": mock_response["code"],
            "confidence": mock_response["confidence"],
            "description": mock_response["description"],
            "safety": mock_response["safety"],
            "enhanced_recommendations": enhanced_context.get("smart_recommendations", []),
            "cross_phase_analysis": enhanced_context.get("correlations", []),
        }

    async def _simulate_ai_suggestions_generation(self, finding, enhanced_context, mock_ai_suggestions):
        """Simulate AI suggestions generation with enhanced context."""
        # AI generated suggestions
        ai_suggestions = mock_ai_suggestions

        # Pipeline generated suggestions (from smart recommendations)
        pipeline_suggestions = []
        if enhanced_context.get("smart_recommendations"):
            for rec in enhanced_context["smart_recommendations"][:2]:
                pipeline_suggestions.append(
                    {
                        "technique": f"Smart Rec: {rec.get('category', 'Architectural')}",
                        "description": rec["description"],
                        "confidence": 85,
                        "complexity": rec.get("effort", "medium").lower(),
                        "risk": "low" if rec.get("priority") == "high" else "medium",
                        "source": "enhanced_pipeline",
                    }
                )

        return {"ai_suggestions": ai_suggestions, "pipeline_suggestions": pipeline_suggestions}

    def _simulate_provider_integration(self, provider_name, finding, enhanced_context, mock_response):
        """Simulate AI provider integration with enhanced context."""
        return {
            "patch": mock_response["code"],
            "confidence": mock_response["confidence"],
            "description": mock_response["description"],
            "safety": mock_response["safety"],
            "provider": provider_name,
            "enhanced_recommendations": enhanced_context.get("smart_recommendations", []),
            "cross_phase_analysis": enhanced_context.get("correlations", []),
        }


# Async test configuration for MCP server
@pytest.mark.mcp_server
@pytest.mark.integration
@pytest.mark.asyncio
class TestMCPServerIntegrationFlow:
    """End-to-end integration tests for MCP server enhanced workflow."""

    @integration_test(["mcp_server"])
    @performance_test(max_time_seconds=15.0, max_memory_mb=100.0)
    async def test_complete_mcp_enhanced_workflow(self, sample_code_file, enhanced_test_datasets):
        """Test complete MCP server enhanced workflow."""
        # 1. Initialize MCP server with AI providers
        mock_server = Mock()

        # 2. Simulate enhanced context retrieval
        enhanced_context = {
            "correlations": [asdict(c) for c in enhanced_test_datasets.get_expected_correlations()],
            "smart_recommendations": [asdict(r) for r in enhanced_test_datasets.get_expected_smart_recommendations()],
            "audit_trail": [asdict(a) for a in enhanced_test_datasets.get_expected_audit_trail()],
            "cross_phase_analysis": True,
            "canonical_policy": "standard",
        }

        # 3. Generate enhanced AI fix
        finding = {
            "type": "connascence_of_literal",
            "message": "Magic number detected",
            "severity": "high",
            "file": str(sample_code_file),
            "line": 10,
        }

        test_instance = TestMCPServerEnhancedIntegration()

        mock_ai_response = {
            "code": "STATUS_ACTIVE = 1\nMAX_USERS = 100",
            "description": "Extracted magic numbers to constants",
            "confidence": 92,
            "safety": "safe",
            "architectural_pattern": "Constants Pattern",
        }

        fix_result = await test_instance._simulate_ai_fix_generation(finding, enhanced_context, mock_ai_response)

        # 4. Generate enhanced AI suggestions
        mock_ai_suggestions = [
            {
                "technique": "Extract Constants",
                "description": "Move magic numbers to named constants",
                "confidence": 90,
                "complexity": "low",
                "risk": "low",
            }
        ]

        suggestions_result = await test_instance._simulate_ai_suggestions_generation(
            finding, enhanced_context, mock_ai_suggestions
        )

        # 5. Validate complete workflow
        assert fix_result["confidence"] >= 90
        assert len(fix_result["enhanced_recommendations"]) > 0
        assert len(fix_result["cross_phase_analysis"]) > 0

        assert len(suggestions_result["ai_suggestions"]) > 0
        assert len(suggestions_result["pipeline_suggestions"]) > 0

        # 6. Performance validation by decorator
        # Memory and timing validated by @performance_test
