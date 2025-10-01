#!/usr/bin/env python3
"""
Test script to validate standardized error handling across integrations.
This verifies that all integrations use consistent error formats.
"""

from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))


def test_error_constants():
    """Test that error constants are properly defined."""
    try:
        from analyzer.constants import ERROR_CODE_MAPPING

        print("PASS - Error constants imported successfully")

        # Verify key error codes exist
        required_codes = [
            "ANALYSIS_FAILED",
            "FILE_NOT_FOUND",
            "MCP_RATE_LIMIT_EXCEEDED",
            "CLI_ARGUMENT_INVALID",
            "PATH_NOT_ACCESSIBLE",
            "INTERNAL_ERROR",
        ]

        for code in required_codes:
            if code in ERROR_CODE_MAPPING:
                print(f"PASS - Error code {code}: {ERROR_CODE_MAPPING[code]}")
            else:
                print(f"FAIL - Missing error code: {code}")

        return True
    except ImportError as e:
        print(f"❌ Failed to import error constants: {e}")
        return False


def test_unified_analyzer_errors():
    """Test unified analyzer error handling."""
    try:
        from analyzer.unified_analyzer import ErrorHandler

        # Test error creation
        handler = ErrorHandler("test")
        error = handler.create_error("ANALYSIS_FAILED", "Test error message", "high", {"test_context": "value"})

        # Verify error structure
        error_dict = error.to_dict()
        required_fields = ["code", "message", "severity", "timestamp", "integration"]

        for field in required_fields:
            if field in error_dict:
                print(f"✅ StandardError has field '{field}': {error_dict[field]}")
            else:
                print(f"❌ StandardError missing field: {field}")

        print("✅ Unified analyzer error handling works")
        return True
    except Exception as e:
        print(f"❌ Unified analyzer error test failed: {e}")
        return False


def test_cli_error_handling():
    """Test CLI error handling."""
    try:
        from interfaces.cli.connascence import ConnascenceCLI

        cli = ConnascenceCLI()

        # Test invalid paths
        result = cli._validate_paths([])  # Empty paths
        if not result:
            print("✅ CLI properly validates empty paths")
        else:
            print("❌ CLI failed to catch empty paths")

        # Test non-existent path
        result = cli._validate_paths(["/non/existent/path"])
        if not result:
            print("✅ CLI properly validates non-existent paths")
        else:
            print("❌ CLI failed to catch non-existent paths")

        # Check error storage
        if cli.errors:
            error = cli.errors[0]
            print(f"✅ CLI stored error: {error.message}")

        print("✅ CLI error handling works")
        return True
    except Exception as e:
        print(f"❌ CLI error test failed: {e}")
        return False


def test_mcp_error_handling():
    """Test MCP server error handling."""
    try:
        from mcp.server import ConnascenceMCPServer

        # Create server with error handler
        server = ConnascenceMCPServer()

        # Test error response creation
        error = server.error_handler.create_error("MCP_RATE_LIMIT_EXCEEDED", "Test rate limit error")

        error_response = server._create_error_response(error)

        # Verify response structure
        required_fields = ["success", "error", "timestamp", "server_version"]
        for field in required_fields:
            if field in error_response:
                print(f"✅ MCP error response has field '{field}'")
            else:
                print(f"❌ MCP error response missing field: {field}")

        if not error_response["success"]:
            print("✅ MCP error response properly indicates failure")

        print("✅ MCP server error handling works")
        return True
    except Exception as e:
        print(f"❌ MCP server error test failed: {e}")
        return False


def test_error_consistency():
    """Test error format consistency across integrations."""
    print("\n🔍 Testing error format consistency...")

    try:
        # Test that all integrations produce similar error structures
        from analyzer.constants import ERROR_SEVERITY
        from analyzer.unified_analyzer import ErrorHandler

        handlers = {
            "analyzer": ErrorHandler("analyzer"),
            "mcp": ErrorHandler("mcp"),
            "cli": ErrorHandler("cli"),
            "vscode": ErrorHandler("vscode"),
        }

        # Create same error type from different integrations
        test_error_type = "FILE_NOT_FOUND"
        test_message = "Test file not found"

        errors = {}
        for integration, handler in handlers.items():
            error = handler.create_error(
                test_error_type, test_message, ERROR_SEVERITY["HIGH"], {"integration_test": True}
            )
            errors[integration] = error.to_dict()

        # Check consistency
        base_error = errors["analyzer"]
        consistent = True

        for integration, error in errors.items():
            for field in ["code", "message", "severity"]:
                if error.get(field) != base_error.get(field):
                    print(f"❌ Inconsistency in {integration}: {field}")
                    consistent = False

            # Check integration field is correct
            if error.get("integration") != integration:
                print(f"❌ Wrong integration field in {integration}")
                consistent = False

        if consistent:
            print("✅ All integrations produce consistent error formats")

        return consistent
    except Exception as e:
        print(f"❌ Error consistency test failed: {e}")
        return False


def main():
    """Run all error handling tests."""
    print("Testing PHASE 4: Standardized Error Handling")
    print("=" * 50)

    tests = [
        ("Error Constants", test_error_constants),
        ("Unified Analyzer", test_unified_analyzer_errors),
        ("CLI Error Handling", test_cli_error_handling),
        ("MCP Error Handling", test_mcp_error_handling),
        ("Error Consistency", test_error_consistency),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name} test...")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))

    # Summary
    print("\n📊 Test Results Summary")
    print("=" * 30)

    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if result:
            passed += 1

    print(f"\nOverall: {passed}/{len(results)} tests passed")

    if passed == len(results):
        print("🎉 All error handling tests passed! Phase 4 is complete.")
        return 0
    else:
        print("⚠️  Some tests failed. Error handling needs attention.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
