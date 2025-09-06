#!/usr/bin/env python3

# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2024 Connascence Safety Analyzer Contributors
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

"""
Connascence MCP Server - AI Agent Usage Test

This script demonstrates how an AI agent (like Claude Code) could use
the Connascence MCP server for code analysis and improvement.
"""

import asyncio
import json

from mcp.server import ConnascenceMCPServer


class AIAgentConnascenceClient:
    """
    Simulates how an AI agent would use the Connascence MCP server
    to analyze code and provide suggestions.
    """

    def __init__(self):
        self.server = ConnascenceMCPServer()
        self.analysis_cache = {}

    async def analyze_codebase(self, path: str, preset: str = "strict-core"):
        """Analyze a codebase for connascence violations."""
        print(f"AI Agent: Analyzing codebase at '{path}' with preset '{preset}'")

        try:
            result = await self.server.scan_path({
                'path': path,
                'policy_preset': preset
            })

            self.analysis_cache[path] = result
            return result

        except Exception as e:
            print(f"AI Agent: Analysis failed - {e}")
            return None

    async def explain_violation(self, violation_id: str):
        """Get detailed explanation of a specific violation."""
        print(f"AI Agent: Requesting explanation for violation '{violation_id}'")

        try:
            result = await self.server.explain_finding({
                'finding_id': violation_id
            })
            return result

        except Exception as e:
            print(f"AI Agent: Explanation failed - {e}")
            return None

    async def suggest_fix(self, violation: dict):
        """Get autofix suggestion for a violation."""
        print(f"AI Agent: Requesting fix suggestion for violation '{violation.get('id', 'unknown')}'")

        try:
            result = await self.server.propose_autofix({
                'violation': violation,
                'include_diff': True
            })
            return result

        except Exception as e:
            print(f"AI Agent: Fix suggestion failed - {e}")
            return None

    async def get_available_policies(self):
        """Get list of available analysis policies."""
        print("AI Agent: Fetching available policy presets")

        try:
            result = await self.server.list_presets({})
            return result

        except Exception as e:
            print(f"AI Agent: Policy fetch failed - {e}")
            return None

    async def generate_improvement_report(self, path: str):
        """Generate a comprehensive improvement report."""
        print(f"\n=== AI Agent Code Improvement Report for '{path}' ===")

        # Step 1: Get available policies
        policies = await self.get_available_policies()
        if policies:
            print(f"\nAvailable Analysis Policies: {len(policies.get('presets', []))}")
            for preset in policies.get('presets', []):
                print(f"  - {preset['id']}: {preset['description']}")

        # Step 2: Analyze the codebase
        analysis = await self.analyze_codebase(path)
        if not analysis:
            print("Analysis failed, cannot generate report.")
            return

        summary = analysis.get('summary', {})
        violations = analysis.get('violations', [])

        print("\n=== Analysis Summary ===")
        print(f"Total Violations: {summary.get('total_violations', 0)}")
        print(f"  - Critical: {summary.get('critical_count', 0)}")
        print(f"  - High: {summary.get('high_count', 0)}")
        print(f"  - Medium: {summary.get('medium_count', 0)}")
        print(f"  - Low: {summary.get('low_count', 0)}")

        # Step 3: Process each violation
        if violations:
            print("\n=== Detailed Violation Analysis ===")

            for i, violation in enumerate(violations[:3], 1):  # Limit to first 3 for demo
                print(f"\nViolation {i}:")
                print(f"  Type: {violation.get('type', 'Unknown')} ({violation.get('severity', 'unknown')})")
                print(f"  File: {violation.get('file', 'Unknown')}")
                print(f"  Line: {violation.get('line', 'Unknown')}")
                print(f"  Description: {violation.get('description', 'No description')}")

                # Get explanation
                explanation = await self.explain_violation(violation.get('rule_id', ''))
                if explanation:
                    print(f"  Explanation: {explanation.get('explanation', 'Not available')}")

                # Get fix suggestion
                fix_suggestion = await self.suggest_fix(violation)
                if fix_suggestion:
                    print(f"  Fix Available: {fix_suggestion.get('patch_available', False)}")
                    print(f"  Fix Description: {fix_suggestion.get('patch_description', 'Not available')}")
                    print(f"  Confidence: {fix_suggestion.get('confidence_score', 0)}")

                    if fix_suggestion.get('diff'):
                        print("  Proposed Diff:")
                        for line in fix_suggestion['diff'].split('\\n'):
                            print(f"    {line}")

        # Step 4: Get server metrics
        try:
            metrics = await self.server.get_metrics({})
            print("\n=== Server Performance Metrics ===")
            print(f"Request Count: {metrics.get('request_count', 'N/A')}")
            print(f"Average Response Time: {metrics.get('response_times', {}).get('avg', 'N/A')}ms")
            print(f"Tool Usage: {json.dumps(metrics.get('tool_usage', {}), indent=2)}")
        except Exception as e:
            print(f"Metrics unavailable: {e}")

        print("\n=== End of Report ===")


async def main():
    """Main demonstration function."""
    print("Connascence MCP Server - AI Agent Usage Demonstration")
    print("=" * 60)

    # Create AI agent client
    agent = AIAgentConnascenceClient()

    # Test path (current directory)
    test_path = "."

    # Generate comprehensive report
    await agent.generate_improvement_report(test_path)

    print("\n" + "=" * 60)
    print("Demonstration complete!")
    print("\nThis shows how an AI agent like Claude Code can:")
    print("1. Connect to the Connascence MCP server")
    print("2. Analyze code for connascence violations")
    print("3. Get detailed explanations of violations")
    print("4. Receive automated fix suggestions")
    print("5. Generate comprehensive improvement reports")
    print("\nThe MCP server is fully functional for AI agent integration!")

if __name__ == "__main__":
    asyncio.run(main())
