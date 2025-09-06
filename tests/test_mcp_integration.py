# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2024 Connascence Safety Analyzer Contributors

"""
Integration tests for MCP server functionality and fallback modes.
"""

from pathlib import Path

# Import project modules
import sys
import tempfile
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp.server import ConnascenceMCPServer
from utils.types import ConnascenceViolation


class TestMCPServerBasic:
    """Basic MCP server functionality tests."""

    def setup_method(self):
        """Setup test environment."""
        self.server = ConnascenceMCPServer()

    def test_server_initialization(self):
        """Test MCP server initializes correctly."""
        assert self.server.name == "connascence"
        assert self.server.version == "2.0.0"
        assert hasattr(self.server, 'analyzer')
        assert hasattr(self.server, 'rate_limiter')
        assert hasattr(self.server, 'audit_logger')

    def test_available_tools(self):
        """Test server exposes expected tools."""
        tools = self.server.get_tools()
        tool_names = [tool['name'] for tool in tools]

        expected_tools = ['scan_path', 'explain_finding', 'propose_autofix']
        for tool in expected_tools:
            assert tool in tool_names

    def test_server_info(self):
        """Test server provides correct information."""
        info = self.server.get_info()

        assert info['name'] == 'connascence'
        assert info['version'] == '2.0.0'
        assert 'tools' in info
        assert len(info['tools']) >= 3


class TestMCPToolExecution:
    """Test MCP tool execution functionality."""

    def setup_method(self):
        """Setup test environment."""
        self.server = ConnascenceMCPServer()

    def test_scan_path_tool(self):
        """Test scan_path tool execution."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test file
            test_file = Path(temp_dir) / 'test.py'
            test_file.write_text('''
def test_function():
    x = 42  # Magic literal
    return x
''')

            # Execute scan_path tool
            result = self.server.execute_tool('scan_path', {
                'path': temp_dir,
                'policy': 'default'
            })

            assert result['success'] is True
            assert 'violations' in result
            assert 'metrics' in result
            assert result['path'] == temp_dir

    def test_explain_finding_tool(self):
        """Test explain_finding tool execution."""
        result = self.server.execute_tool('explain_finding', {
            'violation_id': 'test_violation_123'
        })

        assert result['success'] is True
        assert result['violation_id'] == 'test_violation_123'
        assert 'explanation' in result
        assert 'suggestions' in result['explanation']

    def test_propose_autofix_tool(self):
        """Test propose_autofix tool execution."""
        test_violations = [
            {'id': 'violation_1', 'type': 'CoM', 'severity': 'medium'}
        ]

        result = self.server.execute_tool('propose_autofix', {
            'violations': test_violations,
            'safety_level': 'conservative'
        })

        assert result['success'] is True
        assert 'fixes' in result
        assert result['safety_level'] == 'conservative'
        assert result['total_fixes'] == len(test_violations)

    def test_invalid_tool_execution(self):
        """Test handling of invalid tool requests."""
        with pytest.raises(Exception, match="Unknown tool"):
            self.server.execute_tool('invalid_tool', {})


class TestMCPAsyncInterface:
    """Test async MCP interface methods."""

    def setup_method(self):
        """Setup test environment."""
        self.server = ConnascenceMCPServer()

    @pytest.mark.asyncio
    async def test_async_scan_path(self):
        """Test async scan_path interface."""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = await self.server.scan_path({
                'path': temp_dir,
                'policy_preset': 'default'
            })

            assert result['success'] is True
            assert 'summary' in result
            assert 'violations' in result
            assert 'scan_metadata' in result

    @pytest.mark.asyncio
    async def test_async_explain_finding(self):
        """Test async explain_finding interface."""
        result = await self.server.explain_finding({
            'violation_id': 'test_123'
        })

        assert result['success'] is True
        assert result['violation_id'] == 'test_123'

    @pytest.mark.asyncio
    async def test_async_propose_autofix(self):
        """Test async propose_autofix interface."""
        result = await self.server.propose_autofix({
            'violations': [{'id': 'test', 'type': 'CoM'}],
            'safety_level': 'safe'
        })

        assert result['success'] is True
        assert 'fixes' in result


class TestMCPRateLimiting:
    """Test MCP server rate limiting functionality."""

    def setup_method(self):
        """Setup test environment."""
        # Server with low rate limit for testing
        config = {'max_requests_per_minute': 5}
        self.server = ConnascenceMCPServer(config)

    def test_rate_limit_enforcement(self):
        """Test rate limiting prevents excessive requests."""
        # Should succeed within limit
        for i in range(5):
            result = self.server.execute_tool('explain_finding', {
                'violation_id': f'test_{i}'
            })
            assert result['success'] is True

        # Should fail when limit exceeded
        with pytest.raises(Exception, match="Rate limit exceeded"):
            self.server.execute_tool('explain_finding', {
                'violation_id': 'test_overflow'
            })

    def test_rate_limit_reset(self):
        """Test rate limit resets over time."""
        # Use up rate limit
        for i in range(5):
            self.server.execute_tool('explain_finding', {
                'violation_id': f'test_{i}'
            })

        # Clear rate limiter manually (simulating time passage)
        self.server.rate_limiter.requests.clear()

        # Should work again
        result = self.server.execute_tool('explain_finding', {
            'violation_id': 'test_after_reset'
        })
        assert result['success'] is True


class TestMCPFallbackMode:
    """Test MCP server fallback functionality."""

    def test_standalone_analyzer_fallback(self):
        """Test analyzer works without external MCP servers."""
        # This tests the core analyzer functionality without MCP dependencies
        server = ConnascenceMCPServer()

        # Mock external MCP server failure
        with patch('subprocess.run', side_effect=FileNotFoundError("MCP server not available")):
            # Analyzer should still work
            with tempfile.TemporaryDirectory() as temp_dir:
                test_file = Path(temp_dir) / 'test.py'
                test_file.write_text('x = 42; y = 42')  # Magic literals

                result = server.execute_tool('scan_path', {
                    'path': temp_dir
                })

                assert result['success'] is True
                # Core functionality should work even without external servers

    def test_graceful_degradation(self):
        """Test server degrades gracefully when dependencies unavailable."""
        config = {
            'enable_graceful_degradation': True,
            'offline_mode': True
        }

        server = ConnascenceMCPServer(config)

        # Should initialize successfully even with missing dependencies
        assert server.name == "connascence"
        assert server.version == "2.0.0"


class TestMCPConfigurationValidation:
    """Test MCP server configuration validation."""

    def test_valid_configuration(self):
        """Test server accepts valid configuration."""
        config = {
            'max_requests_per_minute': 100,
            'enable_audit_logging': True,
            'allowed_paths': ['/safe/path']
        }

        server = ConnascenceMCPServer(config)
        assert server.rate_limiter.max_requests == 100
        assert server.audit_logger.enabled is True
        assert len(server.allowed_paths) == 1

    def test_path_validation(self):
        """Test path access validation."""
        config = {'allowed_paths': ['/allowed']}
        server = ConnascenceMCPServer(config)

        assert server.validate_path('/allowed/subdir') is True
        assert server.validate_path('/forbidden') is False

    def test_empty_path_restrictions(self):
        """Test no path restrictions allows all paths."""
        server = ConnascenceMCPServer()  # No path restrictions

        assert server.validate_path('/any/path') is True
        assert server.validate_path('relative/path') is True


class TestMCPMetrics:
    """Test MCP server metrics collection."""

    def setup_method(self):
        """Setup test environment."""
        self.server = ConnascenceMCPServer()

    def test_metrics_collection(self):
        """Test server collects usage metrics."""
        # Execute some operations
        self.server.execute_tool('explain_finding', {
            'violation_id': 'test_1'
        })

        metrics = self.server.get_metrics()

        assert 'requests_processed' in metrics
        assert 'rate_limit_violations' in metrics
        assert 'audit_logs' in metrics
        assert 'uptime' in metrics
        assert metrics['requests_processed'] >= 1


class TestConnascenceViolationModel:
    """Test ConnascenceViolation model functionality."""

    def test_violation_creation(self):
        """Test violation objects can be created correctly."""
        violation = ConnascenceViolation(
            id='test_123',
            rule_id='CON_CoM',
            connascence_type='CoM',
            severity='medium',
            description='Test violation',
            file_path='/test/file.py',
            line_number=42,
            weight=2.5
        )

        assert violation.id == 'test_123'
        assert violation.rule_id == 'CON_CoM'
        assert violation.connascence_type == 'CoM'
        assert violation.severity == 'medium'
        assert violation.file_path == '/test/file.py'
        assert violation.line_number == 42
        assert violation.weight == 2.5

    def test_violation_to_dict_conversion(self):
        """Test violation objects convert to dictionaries correctly."""
        server = ConnascenceMCPServer()

        violation = ConnascenceViolation(
            id='test_456',
            rule_id='CON_CoP',
            connascence_type='CoP',
            severity='high'
        )

        violation_dict = server._violation_to_dict(violation)

        assert violation_dict['id'] == 'test_456'
        assert violation_dict['rule_id'] == 'CON_CoP'
        assert violation_dict['type'] == 'CoP'
        assert violation_dict['severity'] == 'high'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
