# Reproduction Commands for Verification ID: repro-1757127137
cd C:\Users\17175\Desktop\connascence

# Single command to reproduce everything:
python scripts/run_reproducible_verification.py

# Individual package analysis:
cd analyzer && python core.py --path ../test_packages/celery --format json
cd analyzer && python core.py --path ../test_packages/curl --format json
cd analyzer && python core.py --path ../test_packages/express --format json

# Core analysis commands (working validated commands):
cd analyzer && python core.py --path .. --format json --output ../reports/connascence_analysis_report.json
cd analyzer && python core.py --path .. --policy nasa_jpl_pot10 --format json --output ../reports/nasa_compliance_report.json
cd analyzer && python -m dup_detection.mece_analyzer --path .. --comprehensive --output ../reports/mece_duplication_report.json
cd analyzer && python core.py --path .. --format sarif --output ../reports/connascence_analysis.sarif

# Run tests:
python -m pytest tests/test_mcp_integration.py -v

# MCP server test:
python -m mcp.server

# All results are reproducible with pinned dependencies
# Verification completed at: 2025-09-05 22:52:36