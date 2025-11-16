import asyncio

from mcp.enhanced_server import EnhancedConnascenceMCPServer


def test_mcp_server_uses_cli_schema(tmp_path):
    source = tmp_path / "contract.py"
    source.write_text(
        """def example(alpha, beta, gamma, delta, epsilon):\n    return alpha + beta + gamma\n""",
        encoding="utf-8",
    )

    server = EnhancedConnascenceMCPServer()
    result = asyncio.run(server.analyze_file(str(source)))

    assert result["success"] is True
    assert result["target"].endswith("contract.py")
    assert "findings" in result
    assert "summary" in result
