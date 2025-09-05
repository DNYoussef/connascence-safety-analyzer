# Reproduction Commands for Verification ID: repro-1757048564
cd C:\Users\17175\Desktop\connascence

# Single command to reproduce everything:
python scripts/run_reproducible_verification.py

# Individual package analysis:
python -m analyzer.check_connascence test_packages/celery
python -m analyzer.check_connascence test_packages/curl
python -m analyzer.check_connascence test_packages/express

# Run tests:
python -m pytest tests/test_mcp_integration.py -v

# MCP server test:
python -m mcp.server

# All results are reproducible with pinned dependencies
# Verification completed at: 2025-09-05 01:02:48