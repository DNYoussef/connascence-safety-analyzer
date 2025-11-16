import asyncio
from pathlib import Path

from mcp.enhanced_server import EnhancedConnascenceMCPServer


def run_async(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def test_mcp_server_uses_cli_schema(tmp_path):
    server = EnhancedConnascenceMCPServer({})
    sample_file = Path('tests') / 'sample_for_cli.py'
    assert sample_file.exists()

    response = run_async(server.analyze_file(str(sample_file)))
    assert response['success'] is True
    assert 'metadata' in response
    assert response['metadata'].get('schema_version') == '2024-08-01'
    assert 'violations' in response
    assert response['summary']['total_violations'] == len(response['violations'])
