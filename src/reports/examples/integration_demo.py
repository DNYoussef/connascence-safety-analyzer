"""
Unified Report System Integration Demo

Demonstrates all capabilities of the consolidated reporting system.
"""

import json
from datetime import datetime
from pathlib import Path

# Import unified reporting system
from src.reports import (
    unified_reporter,
    generate_report,
    generate_enterprise_package,
    generate_sales_package
)

def demo_unified_reporting():
    """Demonstrate unified reporting capabilities."""
    print("🚀 Unified Report System Demo")
    print("=" * 50)
    
    # Mock analysis result for demonstration
    mock_result = create_mock_analysis_result()
    
    print(f"📊 Analysis Summary:")
    print(f"  • Files Analyzed: {mock_result.total_files_analyzed}")
    print(f"  • Violations Found: {len(mock_result.violations)}")
    print(f"  • Analysis Duration: {mock_result.analysis_duration_ms}ms")
    print()
    
    # 1. Single Format Generation
    demo_single_formats(mock_result)
    
    # 2. Enterprise Package
    demo_enterprise_package(mock_result)
    
    # 3. Sales Package  
    demo_sales_package(mock_result)
    
    # 4. Custom Configurations
    demo_custom_configurations(mock_result)
    
    print("✅ Demo completed successfully!")


def demo_single_formats(result):
    """Demo single format generation."""
    print("📄 Single Format Generation")
    print("-" * 30)
    
    output_dir = Path("demo_output")
    output_dir.mkdir(exist_ok=True)
    
    formats = ["json", "sarif", "markdown", "enterprise", "sales"]
    
    for format_type in formats:
        try:
            output_file = output_dir / f"demo_report.{format_type}"
            content = generate_report(result, format_type, output_file)
            
            # Show sample content
            preview = content[:200] + "..." if len(content) > 200 else content
            print(f"  ✅ {format_type.upper()}: {len(content)} chars")
            if format_type == "markdown":
                print(f"     Preview: {preview.split(chr(10))[0]}")
        except Exception as e:
            print(f"  ❌ {format_type.upper()}: {e}")
    
    print()


def demo_enterprise_package(result):
    """Demo enterprise package generation."""
    print("🏢 Enterprise Package Generation")
    print("-" * 35)
    
    output_dir = Path("demo_output/enterprise")
    
    try:
        reports = generate_enterprise_package(
            result,
            output_dir,
            include_dashboard=True,
            include_metrics=True
        )
        
        print(f"  📊 Package generated in: {output_dir}")
        for format_name, content in reports.items():
            if content:
                print(f"    ✅ {format_name}: {len(content)} chars")
            else:
                print(f"    ❌ {format_name}: Generation failed")
                
        # Show enterprise features
        if "enterprise" in reports and reports["enterprise"]:
            enterprise_data = json.loads(reports["enterprise"])
            roi_data = enterprise_data.get("roi_analysis", {})
            print(f"  💰 ROI Analysis:")
            print(f"    • Investment: ${roi_data.get('investment_analysis', {}).get('total_cost', 0):,.0f}")
            print(f"    • Annual Savings: ${roi_data.get('savings_analysis', {}).get('annual_total_savings', 0):,.0f}")
            
    except Exception as e:
        print(f"  ❌ Enterprise package failed: {e}")
    
    print()


def demo_sales_package(result):
    """Demo sales package generation.""" 
    print("🎯 Sales Package Generation")
    print("-" * 30)
    
    output_dir = Path("demo_output/sales")
    
    try:
        reports = generate_sales_package(
            result,
            output_dir,
            company_name="Demo Corp",
            demo_mode=True
        )
        
        print(f"  🚀 Sales materials generated in: {output_dir}")
        for format_name, content in reports.items():
            if content:
                print(f"    ✅ {format_name}: {len(content)} chars")
                
                # Show sales-specific content
                if format_name == "sales" and isinstance(content, str) and content.startswith("#"):
                    lines = content.split("\n")[:5]  # First 5 lines
                    for line in lines:
                        if line.strip():
                            print(f"      {line[:60]}...")
                            break
            else:
                print(f"    ❌ {format_name}: Generation failed")
                
    except Exception as e:
        print(f"  ❌ Sales package failed: {e}")
    
    print()


def demo_custom_configurations(result):
    """Demo custom configuration options."""
    print("⚙️  Custom Configuration Demo")
    print("-" * 35)
    
    # Markdown with sales mode
    try:
        sales_config = {
            "sales_mode": True,
            "roi_emphasis": True,
            "max_violations_shown": 15
        }
        
        markdown_content = unified_reporter.generate_report(
            result, "markdown", None, sales_config
        )
        
        lines = markdown_content.split("\n")
        header = lines[0] if lines else ""
        print(f"  📝 Sales Markdown: {header}")
        
    except Exception as e:
        print(f"  ❌ Sales markdown failed: {e}")
    
    # SARIF with enterprise metadata
    try:
        sarif_config = {
            "enterprise_mode": True,
            "include_recommendations": True
        }
        
        sarif_content = unified_reporter.generate_report(
            result, "sarif", None, sarif_config
        )
        
        sarif_data = json.loads(sarif_content)
        runs = sarif_data.get("runs", [])
        if runs and "properties" in runs[0]:
            props = runs[0]["properties"]
            print(f"  🔍 Enterprise SARIF: {len(props)} metadata fields")
        
    except Exception as e:
        print(f"  ❌ Enterprise SARIF failed: {e}")
    
    print()


def create_mock_analysis_result():
    """Create mock analysis result for demonstration."""
    # Import here to avoid circular dependencies in real usage
    from analyzer.ast_engine.core_analyzer import AnalysisResult, Violation
    from analyzer.thresholds import ConnascenceType, Severity
    
    # Create mock violations
    violations = []
    
    # Critical violation
    violations.append(Violation(
        id="mock_critical_1",
        type=ConnascenceType.EXECUTION,
        severity=Severity.CRITICAL,
        weight=8.5,
        locality="cross_module",
        file_path="src/core/processor.py",
        line_number=45,
        column=8,
        description="Critical execution order dependency detected in payment processing",
        recommendation="Implement dependency injection to eliminate execution coupling",
        function_name="process_payment",
        class_name="PaymentProcessor"
    ))
    
    # High severity violations
    for i in range(5):
        violations.append(Violation(
            id=f"mock_high_{i}",
            type=ConnascenceType.MEANING,
            severity=Severity.HIGH,
            weight=4.2,
            locality="intra_module",
            file_path=f"src/utils/helpers_{i}.py",
            line_number=23 + i,
            column=12,
            description=f"Magic literal '{i * 100}' used without explanation",
            recommendation="Extract to named constant",
            function_name=f"calculate_threshold_{i}"
        ))
    
    # Medium and low violations
    for i in range(15):
        violations.append(Violation(
            id=f"mock_medium_{i}",
            type=ConnascenceType.POSITION,
            severity=Severity.MEDIUM if i < 10 else Severity.LOW,
            weight=2.1 if i < 10 else 1.2,
            locality="intra_module",
            file_path=f"src/models/data_{i}.py", 
            line_number=100 + i,
            column=4,
            description=f"Function has {4 + i % 3} positional parameters",
            recommendation="Use keyword arguments or parameter object",
            function_name=f"process_data_{i}"
        ))
    
    # Create analysis result
    return AnalysisResult(
        violations=violations,
        total_files_analyzed=87,
        analysis_duration_ms=1247,
        timestamp=datetime.now().isoformat(),
        project_root="/demo/project"
    )


if __name__ == "__main__":
    demo_unified_reporting()