"""
Tests for the MCP (Model Context Protocol) server.

Tests agent integration, tool functionality, safety controls,
and rate limiting for the connascence MCP server.
"""

import asyncio
import json
import pytest
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path

from mcp.server import ConnascenceMCPServer, MCPConnascenceTool
from analyzer.core import ConnascenceViolation


class TestConnascenceMCPServer:
    """Test the MCP server implementation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.server = ConnascenceMCPServer()
    
    def test_server_initialization(self):
        """Test server initializes correctly."""
        assert self.server.name == "connascence"
        assert self.server.version == "1.0.0"
        assert hasattr(self.server, 'analyzer')
        assert hasattr(self.server, 'rate_limiter')
        assert hasattr(self.server, 'audit_logger')
    
    def test_tools_registration(self):
        """Test that all tools are registered."""
        tools = self.server.get_tools()
        
        # Check that required tools are present
        tool_names = [tool['name'] for tool in tools]
        expected_tools = [
            'scan_path',
            'explain_finding',
            'propose_autofix',
            'list_presets',
            'validate_policy',
            'get_metrics',
            'enforce_policy'
        ]
        
        for expected_tool in expected_tools:
            assert expected_tool in tool_names
        
        # Check tool structure
        for tool in tools:
            assert 'name' in tool
            assert 'description' in tool
            assert 'inputSchema' in tool
            assert tool['inputSchema']['type'] == 'object'
    
    def test_tool_input_validation(self):
        """Test tool input schema validation."""
        tools = self.server.get_tools()
        scan_tool = next(tool for tool in tools if tool['name'] == 'scan_path')
        
        # Should have required fields
        schema = scan_tool['inputSchema']
        assert 'properties' in schema
        assert 'path' in schema['properties']
        assert 'required' in schema
        assert 'path' in schema['required']
    
    @pytest.mark.asyncio
    async def test_scan_path_tool(self):
        """Test the scan_path tool functionality."""
        with patch.object(self.server.analyzer, 'analyze_directory') as mock_analyze:
            # Mock violations
            mock_violations = [
                ConnascenceViolation(
                    id="test1", rule_id="CON_CoM", connascence_type="CoM",
                    severity="high", description="Magic literal",
                    file_path="/test/file.py", line_number=10, weight=3.0
                )
            ]
            mock_analyze.return_value = mock_violations
            
            # Execute tool
            result = await self.server.scan_path({
                'path': '/test/project',
                'policy_preset': 'strict-core'
            })
            
            # Check result structure
            assert 'summary' in result
            assert 'violations' in result
            assert 'scan_metadata' in result
            
            # Check summary
            summary = result['summary']
            assert summary['total_violations'] == 1
            assert summary['critical_count'] == 0
            assert summary['high_count'] == 1
            
            # Check violations
            violations = result['violations']
            assert len(violations) == 1
            assert violations[0]['id'] == 'test1'
            assert violations[0]['severity'] == 'high'
    
    @pytest.mark.asyncio
    async def test_explain_finding_tool(self):
        """Test the explain_finding tool."""
        result = await self.server.explain_finding({
            'rule_id': 'CON_CoM',
            'include_examples': True
        })
        
        # Should return explanation
        assert 'explanation' in result
        assert 'connascence_type' in result
        assert 'examples' in result
        
        # Check explanation content
        explanation = result['explanation']
        assert 'Connascence of Meaning' in explanation
        assert len(explanation) > 50  # Should be detailed
        
        # Check examples
        examples = result['examples']
        assert len(examples) > 0
        assert 'problem_code' in examples[0]
        assert 'solution_code' in examples[0]
    
    @pytest.mark.asyncio
    async def test_propose_autofix_tool(self):
        """Test the propose_autofix tool."""
        with patch('autofix.patch_api.PatchGenerator') as mock_generator_class:
            mock_generator = Mock()
            mock_patch = Mock()
            mock_patch.description = "Extract magic literal to constant"
            mock_patch.confidence = 0.85
            mock_patch.safety_level = "safe"
            mock_patch.old_code = "value = 100"
            mock_patch.new_code = "THRESHOLD = 100\\nvalue = THRESHOLD"
            
            mock_generator.generate_patch.return_value = mock_patch
            mock_generator_class.return_value = mock_generator
            
            # Create mock violation
            violation_data = {
                'id': 'test1',
                'rule_id': 'CON_CoM',
                'connascence_type': 'CoM',
                'severity': 'medium',
                'description': 'Magic literal',
                'file_path': '/test/file.py',
                'line_number': 10,
                'weight': 2.0
            }
            
            result = await self.server.propose_autofix({
                'violation': violation_data,
                'include_diff': True
            })
            
            # Check result structure
            assert 'patch_available' in result
            assert result['patch_available'] is True
            assert 'patch_description' in result
            assert 'confidence_score' in result
            assert 'safety_level' in result
            
            # Check patch details
            assert result['confidence_score'] == 0.85
            assert result['safety_level'] == 'safe'
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self):
        """Test rate limiting functionality."""
        # Mock rate limiter
        with patch.object(self.server.rate_limiter, 'check_rate_limit') as mock_check:
            mock_check.return_value = False  # Rate limit exceeded
            
            # Should raise rate limit error
            with pytest.raises(Exception) as exc_info:
                await self.server.scan_path({'path': '/test'})
            
            assert 'rate limit' in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_path_validation(self):
        """Test path validation and sandboxing."""
        # Test absolute path outside allowed area
        with pytest.raises(ValueError) as exc_info:
            await self.server.scan_path({'path': '/etc/passwd'})
        
        assert 'path not allowed' in str(exc_info.value).lower()
        
        # Test path traversal attempt
        with pytest.raises(ValueError) as exc_info:
            await self.server.scan_path({'path': '../../../etc/passwd'})
        
        assert 'path not allowed' in str(exc_info.value).lower()
    
    @pytest.mark.asyncio 
    async def test_audit_logging(self):
        """Test audit logging functionality."""
        with patch.object(self.server.audit_logger, 'log_request') as mock_log:
            # Execute a tool
            await self.server.list_presets({})
            
            # Should log the request
            mock_log.assert_called_once()
            call_args = mock_log.call_args[1]
            assert call_args['tool_name'] == 'list_presets'
            assert 'timestamp' in call_args
    
    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling in tools."""
        with patch.object(self.server.analyzer, 'analyze_directory') as mock_analyze:
            # Mock analyzer error
            mock_analyze.side_effect = Exception("Analysis failed")
            
            # Should handle error gracefully
            result = await self.server.scan_path({'path': '/test'})
            
            assert 'error' in result
            assert 'Analysis failed' in result['error']
    
    def test_policy_preset_validation(self):
        """Test policy preset validation."""
        valid_presets = ['strict-core', 'service-defaults', 'experimental']
        
        for preset in valid_presets:
            # Should not raise exception
            self.server._validate_policy_preset(preset)
        
        # Invalid preset should raise error
        with pytest.raises(ValueError):
            self.server._validate_policy_preset('invalid-preset')
    
    def test_security_controls(self):
        """Test security controls and limitations."""
        # Test file path restrictions
        restricted_paths = [
            '/etc',
            '/var/log', 
            '/home/other_user',
            'C:\\Windows\\System32',
            '/usr/bin'
        ]
        
        for path in restricted_paths:
            with pytest.raises(ValueError):
                self.server._validate_path(path)
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """Test handling of concurrent requests."""
        # Mock analyzer to simulate work
        with patch.object(self.server.analyzer, 'analyze_directory') as mock_analyze:
            mock_analyze.return_value = []
            
            # Create multiple concurrent requests
            tasks = []
            for i in range(5):
                task = self.server.scan_path({
                    'path': f'/test/project_{i}',
                    'policy_preset': 'service-defaults'
                })
                tasks.append(task)
            
            # Execute concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # All should complete (or be rate limited)
            assert len(results) == 5
            for result in results:
                assert isinstance(result, (dict, Exception))


class TestMCPConnascenceTool:
    """Test the base MCP tool class."""
    
    def test_tool_creation(self):
        """Test tool creation and validation."""
        tool = MCPConnascenceTool(
            name="test_tool",
            description="Test tool description",
            input_schema={
                "type": "object",
                "properties": {
                    "param1": {"type": "string"}
                },
                "required": ["param1"]
            }
        )
        
        assert tool.name == "test_tool"
        assert tool.description == "Test tool description"
        assert tool.input_schema["type"] == "object"
    
    def test_tool_validation(self):
        """Test tool input validation."""
        tool = MCPConnascenceTool(
            name="test_tool",
            description="Test tool",
            input_schema={
                "type": "object", 
                "properties": {
                    "required_param": {"type": "string"},
                    "optional_param": {"type": "number"}
                },
                "required": ["required_param"]
            }
        )
        
        # Valid input should pass
        valid_input = {"required_param": "test"}
        tool.validate_input(valid_input)  # Should not raise
        
        # Missing required param should fail
        invalid_input = {"optional_param": 123}
        with pytest.raises(ValueError):
            tool.validate_input(invalid_input)
    
    @pytest.mark.asyncio
    async def test_tool_execution(self):
        """Test tool execution with mock handler."""
        async def mock_handler(params):
            return {"result": "success", "input": params}
        
        tool = MCPConnascenceTool(
            name="test_tool",
            description="Test tool",
            input_schema={
                "type": "object",
                "properties": {"param": {"type": "string"}},
                "required": ["param"]
            },
            handler=mock_handler
        )
        
        result = await tool.execute({"param": "test_value"})
        
        assert result["result"] == "success"
        assert result["input"]["param"] == "test_value"


class TestMCPServerIntegration:
    """Integration tests for MCP server."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self):
        """Test complete MCP workflow."""
        server = ConnascenceMCPServer()
        
        # Step 1: List available presets
        presets_result = await server.list_presets({})
        assert 'presets' in presets_result
        assert len(presets_result['presets']) > 0
        
        # Step 2: Validate a policy
        policy_result = await server.validate_policy({
            'policy_preset': 'service-defaults'
        })
        assert policy_result['valid'] is True
        
        # Step 3: Get explanation for a rule
        explain_result = await server.explain_finding({
            'rule_id': 'CON_CoM'
        })
        assert 'explanation' in explain_result
    
    @pytest.mark.asyncio
    async def test_metrics_collection(self):
        """Test metrics collection and reporting."""
        server = ConnascenceMCPServer()
        
        # Execute some operations to generate metrics
        await server.list_presets({})
        await server.explain_finding({'rule_id': 'CON_CoM'})
        
        # Get metrics
        metrics_result = await server.get_metrics({})
        
        assert 'request_count' in metrics_result
        assert 'response_times' in metrics_result
        assert 'tool_usage' in metrics_result
        
        # Should show usage of tools we just called
        tool_usage = metrics_result['tool_usage']
        assert 'list_presets' in tool_usage
        assert 'explain_finding' in tool_usage
    
    @pytest.mark.asyncio
    async def test_policy_enforcement(self):
        """Test policy enforcement workflow."""
        server = ConnascenceMCPServer()
        
        # Mock violations that exceed budget
        mock_violations = [
            ConnascenceViolation(
                id=f"test{i}", rule_id="CON_CoM", connascence_type="CoM",
                severity="high", description=f"Violation {i}",
                file_path="/test/file.py", line_number=i, weight=3.0
            ) for i in range(10)  # Many violations
        ]
        
        with patch.object(server.analyzer, 'analyze_directory') as mock_analyze:
            mock_analyze.return_value = mock_violations
            
            # Enforce strict policy with low budget
            result = await server.enforce_policy({
                'policy_preset': 'strict-core',
                'budget_limits': {
                    'CoM': 5,  # Lower than violation count
                    'total_violations': 8
                }
            })
            
            assert 'budget_status' in result
            assert 'violations_over_budget' in result
            
            # Should indicate budget exceeded
            budget_status = result['budget_status']
            assert budget_status['budget_exceeded'] is True
    
    def test_server_configuration(self):
        """Test server configuration options."""
        # Test with custom config
        custom_config = {
            'max_requests_per_minute': 30,
            'allowed_paths': ['/custom/path'],
            'enable_audit_logging': False
        }
        
        server = ConnascenceMCPServer(config=custom_config)
        
        # Should apply custom configuration
        assert server.rate_limiter.max_requests == 30
        assert '/custom/path' in server.allowed_paths
        assert server.audit_logger.enabled is False
    
    @pytest.mark.asyncio
    async def test_large_codebase_handling(self):
        """Test handling of large codebase analysis."""
        server = ConnascenceMCPServer()
        
        # Mock large number of violations
        large_violations = [
            ConnascenceViolation(
                id=f"test{i}", rule_id="CON_CoM", connascence_type="CoM",
                severity="medium", description=f"Violation {i}",
                file_path=f"/test/file_{i}.py", line_number=1, weight=2.0
            ) for i in range(1000)  # Large number
        ]
        
        with patch.object(server.analyzer, 'analyze_directory') as mock_analyze:
            mock_analyze.return_value = large_violations
            
            # Should handle large result set
            result = await server.scan_path({
                'path': '/test/large_project',
                'limit_results': 100  # Should limit results
            })
            
            assert 'violations' in result
            # Should limit results for performance
            assert len(result['violations']) <= 100
            
            # Should indicate if results were limited
            if len(large_violations) > 100:
                assert result.get('results_limited', False) is True