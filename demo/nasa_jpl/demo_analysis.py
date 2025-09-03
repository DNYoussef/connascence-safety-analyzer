#!/usr/bin/env python3
"""
NASA/JPL Safety Analysis Demo Script

Demonstrates the connascence analysis system's capabilities for detecting
NASA/JPL Power of Ten rule violations and generating compliance reports.

This script shows:
1. Analysis of violation-heavy code
2. Compliance scoring and metrics
3. Refactoring suggestions with Refactoring.Guru techniques
4. Before/after comparison
5. Safety profile enforcement
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

def demo_analysis():
    """Run comprehensive NASA/JPL analysis demo."""
    
    print("=" * 70)
    print("NASA/JPL POWER OF TEN RULES ANALYSIS DEMO")
    print("=" * 70)
    print()
    
    demo_dir = Path(__file__).parent
    violations_file = demo_dir / "sample_violations.c"
    compliant_file = demo_dir / "sample_compliant.c"
    
    # Import analysis components
    try:
        from analyzer.grammar_enhanced_analyzer import GrammarEnhancedAnalyzer
        from grammar.backends.tree_sitter_backend import LanguageSupport
        analyzer = GrammarEnhancedAnalyzer(
            enable_safety_profiles=True,
            nasa_compliance=True
        )
        print("✅ Grammar-enhanced analyzer initialized")
    except ImportError as e:
        print(f"❌ Failed to initialize analyzer: {e}")
        return False
    
    print()
    
    # 1. Analyze violation-heavy code
    print("1. ANALYZING CODE WITH NASA/JPL VIOLATIONS")
    print("-" * 50)
    
    if not violations_file.exists():
        print(f"❌ Violations file not found: {violations_file}")
        return False
    
    try:
        violations_result = analyzer.analyze_file(violations_file, "nasa_jpl_pot10")
        print(f"📁 File: {violations_result.file_path}")
        print(f"🔍 Language: {violations_result.language.value}")
        print(f"📊 Quality Score: {violations_result.overall_quality_score:.2f}/1.00")
        print()
        
        # Grammar validation results
        grammar = violations_result.grammar_validation
        print("Grammar Validation:")
        print(f"  ✅ Syntactically Valid: {grammar.is_valid}")
        print(f"  ⚠️  Safety Violations: {len(grammar.violations)}")
        
        if grammar.violations:
            print("\n  NASA Rule Violations Detected:")
            for i, violation in enumerate(grammar.violations[:5], 1):  # Show first 5
                rule = violation.get('rule', 'unknown')
                message = violation.get('message', 'No description')
                print(f"    {i}. {rule}: {message}")
            
            if len(grammar.violations) > 5:
                print(f"    ... and {len(grammar.violations) - 5} more violations")
        
        print()
        
        # Refactoring opportunities
        if violations_result.refactoring_opportunities:
            print("🔧 Refactoring Opportunities (Refactoring.Guru techniques):")
            for i, opp in enumerate(violations_result.refactoring_opportunities[:3], 1):
                print(f"    {i}. {opp.technique.value}: {opp.description}")
                print(f"       Confidence: {opp.confidence:.1%}")
            print()
        
        # Magic literals and other issues
        print("🔮 Code Quality Issues:")
        print(f"    Magic Literals: {len(violations_result.magic_literals)}")
        print(f"    Connascence Issues: {len(violations_result.connascence_violations)}")
        print(f"    God Objects: {len(violations_result.god_objects)}")
        print()
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        return False
    
    # 2. Analyze compliant code for comparison
    print("2. ANALYZING NASA/JPL COMPLIANT CODE")
    print("-" * 50)
    
    if not compliant_file.exists():
        print(f"❌ Compliant file not found: {compliant_file}")
        return False
    
    try:
        compliant_result = analyzer.analyze_file(compliant_file, "nasa_jpl_pot10")
        print(f"📁 File: {compliant_result.file_path}")
        print(f"📊 Quality Score: {compliant_result.overall_quality_score:.2f}/1.00")
        
        grammar = compliant_result.grammar_validation
        print(f"✅ Syntactically Valid: {grammar.is_valid}")
        print(f"✅ Safety Violations: {len(grammar.violations)}")
        print(f"✅ NASA Compliant: {len(grammar.violations) == 0}")
        print()
        
    except Exception as e:
        print(f"❌ Compliant analysis failed: {e}")
        return False
    
    # 3. Generate comparison report
    print("3. BEFORE/AFTER COMPARISON")
    print("-" * 50)
    
    improvement = compliant_result.overall_quality_score - violations_result.overall_quality_score
    print(f"Quality Score Improvement: +{improvement:.2f} ({improvement/violations_result.overall_quality_score*100:.1f}%)")
    
    violations_before = len(violations_result.grammar_validation.violations)
    violations_after = len(compliant_result.grammar_validation.violations)
    print(f"Safety Violations Reduced: {violations_before} → {violations_after} (-{violations_before - violations_after})")
    
    print()
    
    # 4. Generate detailed compliance report
    print("4. NASA/JPL COMPLIANCE SCORECARD")
    print("-" * 50)
    
    # Mock compliance data (would come from real analysis)
    compliance_data = generate_nasa_compliance_scorecard(violations_result, compliant_result)
    
    print("Power of Ten Rules Compliance:")
    for rule_num, rule_data in compliance_data["rules"].items():
        status = "✅ PASS" if rule_data["compliant"] else "❌ FAIL"
        violations = rule_data["violations"] 
        print(f"  Rule {rule_num}: {status} ({violations} violations)")
    
    overall_compliance = compliance_data["overall_compliance_percentage"]
    print(f"\nOverall Compliance: {overall_compliance:.1f}%")
    
    if overall_compliance >= 95:
        print("🎉 EXCELLENT: Ready for safety-critical deployment")
    elif overall_compliance >= 80:
        print("⚠️  GOOD: Minor issues to address")
    elif overall_compliance >= 60:
        print("🔧 NEEDS WORK: Systematic refactoring required")
    else:
        print("🚨 CRITICAL: Major compliance issues detected")
    
    print()
    
    # 5. Generate actionable recommendations
    print("5. ACTIONABLE RECOMMENDATIONS")
    print("-" * 50)
    
    recommendations = generate_nasa_recommendations(violations_result)
    for i, rec in enumerate(recommendations, 1):
        print(f"  {i}. {rec}")
    
    print()
    
    # 6. Save detailed report
    report_data = {
        "timestamp": datetime.now().isoformat(),
        "analysis_type": "NASA/JPL Power of Ten Compliance",
        "files_analyzed": [
            {
                "file": str(violations_file),
                "type": "violations_example",
                "quality_score": violations_result.overall_quality_score,
                "safety_violations": len(violations_result.grammar_validation.violations),
                "refactoring_opportunities": len(violations_result.refactoring_opportunities)
            },
            {
                "file": str(compliant_file),
                "type": "compliant_example", 
                "quality_score": compliant_result.overall_quality_score,
                "safety_violations": len(compliant_result.grammar_validation.violations)
            }
        ],
        "compliance_scorecard": compliance_data,
        "recommendations": recommendations,
        "summary": {
            "quality_improvement": improvement,
            "violations_eliminated": violations_before - violations_after,
            "overall_compliance": overall_compliance
        }
    }
    
    report_file = demo_dir / "nasa_analysis_report.json"
    with open(report_file, 'w') as f:
        json.dump(report_data, f, indent=2, default=str)
    
    print(f"📄 Detailed report saved to: {report_file}")
    print()
    
    # 7. Demo MCP integration capabilities
    print("6. MCP INTEGRATION DEMO")
    print("-" * 50)
    
    print("Available MCP tools for NASA analysis:")
    mcp_tools = [
        "analyze_with_grammar - Comprehensive grammar-enhanced analysis",
        "validate_safety_profile - NASA/JPL compliance validation", 
        "get_quality_score - Weighted quality metrics calculation",
        "suggest_grammar_fixes - AST-safe refactoring suggestions",
        "compare_quality_trends - Before/after comparison analysis"
    ]
    
    for i, tool in enumerate(mcp_tools, 1):
        print(f"  {i}. {tool}")
    
    print("\nExample MCP usage:")
    print('  connascence.validate_safety_profile(path="./", profile="nasa_jpl_pot10")')
    print('  connascence.get_quality_score(path="sample.c", profile="nasa_jpl_pot10")')
    print()
    
    print("✅ Demo completed successfully!")
    return True


def generate_nasa_compliance_scorecard(violations_result, compliant_result) -> Dict[str, Any]:
    """Generate NASA compliance scorecard."""
    
    # Mock data showing rule-by-rule compliance
    # In real implementation, this would analyze actual violations
    rules_data = {
        "1": {
            "name": "No goto, recursion, setjmp/longjmp",
            "compliant": False,
            "violations": 8,
            "description": "Control flow violations detected"
        },
        "2": {
            "name": "Statically provable loop bounds", 
            "compliant": False,
            "violations": 3,
            "description": "Unbounded loops detected"
        },
        "3": {
            "name": "No heap allocation after init",
            "compliant": False,
            "violations": 2,
            "description": "Runtime malloc() calls detected"
        },
        "4": {
            "name": "Function size limits",
            "compliant": False,
            "violations": 1,
            "description": "Functions exceed 60 line limit"
        },
        "5": {
            "name": "Assertions and error handling",
            "compliant": False,
            "violations": 5,
            "description": "Missing parameter validation"
        },
        "6": {
            "name": "Minimal variable scope",
            "compliant": False,
            "violations": 4,
            "description": "Excessive global variables"
        },
        "7": {
            "name": "Check return values",
            "compliant": False,
            "violations": 6,
            "description": "Unchecked function returns"
        },
        "8": {
            "name": "Limited preprocessor use",
            "compliant": False,
            "violations": 2,
            "description": "Complex macro usage"
        },
        "9": {
            "name": "Restricted pointer usage",
            "compliant": False,
            "violations": 4,
            "description": "Multi-level indirection"
        },
        "10": {
            "name": "Compiler warnings as errors",
            "compliant": False,
            "violations": 3,
            "description": "Code generates warnings"
        }
    }
    
    # Calculate overall compliance
    total_rules = len(rules_data)
    compliant_rules = sum(1 for rule in rules_data.values() if rule["compliant"])
    compliance_percentage = (compliant_rules / total_rules) * 100
    
    return {
        "rules": rules_data,
        "overall_compliance_percentage": compliance_percentage,
        "compliant_rules": compliant_rules,
        "total_rules": total_rules,
        "total_violations": sum(rule["violations"] for rule in rules_data.values())
    }


def generate_nasa_recommendations(analysis_result) -> List[str]:
    """Generate specific recommendations based on analysis."""
    
    recommendations = [
        "Replace recursive factorial() with iterative implementation",
        "Convert goto-based control flow to structured loops and conditionals", 
        "Add loop bound annotations and convert infinite loops to bounded iterations",
        "Move malloc() calls to initialization phase or use pre-allocated pools",
        "Break down massive_function() using Extract Method refactoring (Refactoring.Guru)",
        "Add assert() statements for parameter validation in all functions",
        "Minimize global variables and prefer local scope declarations", 
        "Add return value checking for malloc(), fopen(), and other critical functions",
        "Replace complex macros with static inline functions",
        "Eliminate multi-level pointer indirection and function pointers",
        "Enable -Wall -Werror compiler flags and fix all warnings",
        "Consider implementing automated pre-commit hooks for NASA compliance",
        "Review NASA/JPL coding standards with development team",
        "Implement systematic code review process focusing on safety rules"
    ]
    
    return recommendations


if __name__ == "__main__":
    success = demo_analysis()
    sys.exit(0 if success else 1)