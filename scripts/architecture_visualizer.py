#!/usr/bin/env python3

"""
Architecture visualization and enhanced analysis for connascence analyzer repository.
Creates visual dependency graphs, component diagrams, and detailed coupling analysis.
"""

import json
from pathlib import Path
from typing import Any, Dict


class ArchitectureVisualizer:
    """Creates visual representations and enhanced analysis of system architecture."""

    def __init__(self, analysis_report: Dict[str, Any]):
        self.report = analysis_report
        self.import_graph = analysis_report["detailed_metrics"]["import_graph"]
        self.coupling_matrix = analysis_report["detailed_metrics"]["coupling_matrix"]
        self.fan_in = analysis_report["detailed_metrics"]["fan_in"]
        self.fan_out = analysis_report["detailed_metrics"]["fan_out"]

    def generate_mermaid_dependency_graph(self) -> str:
        """Generate Mermaid diagram for dependency graph."""
        mermaid = "```mermaid\n"
        mermaid += "graph TD\n"
        mermaid += "    %% Connascence Analyzer Architecture Dependency Graph\n\n"

        # Define node styles based on coupling strength
        mermaid += "    %% Node Definitions\n"
        folders = set()
        for source, targets in self.import_graph.items():
            folders.add(source)
            folders.update(targets.keys())

        # Style nodes by their role
        core_modules = {"analyzer", "core", "utils"}
        interface_modules = {"cli", "mcp"}
        feature_modules = {"autofix", "experimental", "dashboard", "security"}

        for folder in sorted(folders):
            if folder in core_modules:
                mermaid += f"    {folder}[{folder.title()}]\n"
                mermaid += f"    class {folder} coreModule\n"
            elif folder in interface_modules:
                mermaid += f"    {folder}[{folder.upper()}]\n"
                mermaid += f"    class {folder} interfaceModule\n"
            elif folder in feature_modules:
                mermaid += f"    {folder}[{folder.title()}]\n"
                mermaid += f"    class {folder} featureModule\n"
            else:
                mermaid += f"    {folder}[{folder.title()}]\n"

        mermaid += "\n    %% Dependencies\n"

        # Add edges with weights
        for source, targets in self.import_graph.items():
            for target, weight in targets.items():
                if weight > 0:
                    coupling = self.coupling_matrix.get(source, {}).get(target, 0)
                    if coupling > 0.3:
                        mermaid += f"    {source} ---|{weight}| {target}\n"
                        mermaid += f"    linkStyle {len(mermaid.split('---')) - 1} stroke:#ff6b6b,stroke-width:3px\n"
                    elif coupling > 0.1:
                        mermaid += f"    {source} ---|{weight}| {target}\n"
                        mermaid += f"    linkStyle {len(mermaid.split('---')) - 1} stroke:#feca57,stroke-width:2px\n"
                    else:
                        mermaid += f"    {source} ---|{weight}| {target}\n"

        # Add styling
        mermaid += "\n    %% Styling\n"
        mermaid += "    classDef coreModule fill:#e3f2fd,stroke:#1976d2,stroke-width:2px\n"
        mermaid += "    classDef interfaceModule fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px\n"
        mermaid += "    classDef featureModule fill:#e8f5e8,stroke:#388e3c,stroke-width:2px\n"
        mermaid += "```\n"

        return mermaid

    def generate_c4_architecture_diagram(self) -> str:
        """Generate C4-style architecture diagram in Mermaid format."""
        c4_diagram = "```mermaid\n"
        c4_diagram += "C4Context\n"
        c4_diagram += "    title Connascence Analyzer - System Context\n\n"

        # External systems
        c4_diagram += '    Person(user, "Developer", "Uses connascence analyzer")\n'
        c4_diagram += '    System(vscode, "VS Code", "IDE with extension")\n'
        c4_diagram += '    System(ci_cd, "CI/CD Pipeline", "Automated analysis")\n\n'

        # Main system
        c4_diagram += '    System_Boundary(connascence, "Connascence Analyzer") {\n'
        c4_diagram += '        Container(cli, "CLI Interface", "Python", "Command-line tool")\n'
        c4_diagram += '        Container(mcp, "MCP Server", "Python", "Model Context Protocol")\n'
        c4_diagram += '        Container(analyzer, "Core Analyzer", "Python", "Analysis engine")\n'
        c4_diagram += '        Container(vscode_ext, "VS Code Extension", "TypeScript", "IDE integration")\n'
        c4_diagram += "    }\n\n"

        # Relationships
        c4_diagram += '    Rel(user, cli, "Runs analysis")\n'
        c4_diagram += '    Rel(user, vscode, "Uses IDE")\n'
        c4_diagram += '    Rel(vscode, vscode_ext, "Loads")\n'
        c4_diagram += '    Rel(vscode_ext, mcp, "Communicates")\n'
        c4_diagram += '    Rel(cli, analyzer, "Uses")\n'
        c4_diagram += '    Rel(mcp, analyzer, "Uses")\n'
        c4_diagram += '    Rel(ci_cd, cli, "Executes")\n'
        c4_diagram += "```\n"

        return c4_diagram

    def generate_component_interaction_matrix(self) -> str:
        """Generate detailed component interaction analysis."""
        matrix = "COMPONENT INTERACTION MATRIX\n"
        matrix += "=" * 50 + "\n\n"

        # Interaction strength analysis
        matrix += "INTERACTION STRENGTH ANALYSIS:\n"
        matrix += "-" * 35 + "\n"

        interactions = []
        for source, targets in self.coupling_matrix.items():
            for target, strength in targets.items():
                if strength > 0:
                    interactions.append((source, target, strength))

        # Sort by strength
        interactions.sort(key=lambda x: x[2], reverse=True)

        matrix += f"{'Source':>12} | {'Target':>12} | {'Strength':>10} | {'Type'}\n"
        matrix += "-" * 60 + "\n"

        for source, target, strength in interactions[:15]:
            interaction_type = (
                "CRITICAL" if strength > 0.5 else "HIGH" if strength > 0.3 else "MEDIUM" if strength > 0.1 else "LOW"
            )
            matrix += f"{source:>12} | {target:>12} | {strength:>9.2%} | {interaction_type}\n"

        # Module responsibility analysis
        matrix += "\nMODULE RESPONSIBILITY ANALYSIS:\n"
        matrix += "-" * 35 + "\n"

        for folder in sorted(self.fan_in.keys()):
            fan_in_count = self.fan_in.get(folder, 0)
            fan_out_count = self.fan_out.get(folder, 0)
            instability = fan_out_count / (fan_in_count + fan_out_count) if (fan_in_count + fan_out_count) > 0 else 0

            role = "STABLE" if instability < 0.3 else "BALANCED" if instability < 0.7 else "UNSTABLE"
            matrix += f"{folder:>12}: Fan-In={fan_in_count:>2}, Fan-Out={fan_out_count:>2}, Instability={instability:>5.2f} ({role})\n"

        return matrix

    def generate_data_flow_analysis(self) -> str:
        """Generate data flow and communication pattern analysis."""
        flow_analysis = "DATA FLOW AND COMMUNICATION PATTERNS\n"
        flow_analysis += "=" * 45 + "\n\n"

        # Identify data flow patterns
        flow_analysis += "PRIMARY DATA FLOW PATHS:\n"
        flow_analysis += "-" * 25 + "\n"

        # CLI flow
        flow_analysis += "1. CLI WORKFLOW:\n"
        flow_analysis += "   User Input → CLI → Analyzer → Reporting → Output\n"
        flow_analysis += f"   Coupling: CLI→Analyzer ({self.coupling_matrix.get('cli', {}).get('analyzer', 0):.2%})\n\n"

        # MCP flow
        flow_analysis += "2. MCP WORKFLOW:\n"
        flow_analysis += "   VS Code → MCP Server → Analyzer → Results → VS Code\n"
        flow_analysis += f"   Coupling: MCP→Analyzer ({self.coupling_matrix.get('mcp', {}).get('analyzer', 0):.2%})\n\n"

        # Analysis flow
        flow_analysis += "3. ANALYSIS WORKFLOW:\n"
        flow_analysis += "   Source Code → Core Engine → Rules/Policy → Violations → Reporting\n"
        flow_analysis += (
            f"   Coupling: Analyzer→Policy ({self.coupling_matrix.get('analyzer', {}).get('policy', 0):.2%})\n\n"
        )

        # Shared data structures
        flow_analysis += "SHARED DATA STRUCTURES:\n"
        flow_analysis += "-" * 25 + "\n"
        flow_analysis += "- ConnascenceViolation: Used across analyzer, mcp, reporting\n"
        flow_analysis += "- Configuration objects: Shared between config, analyzer, cli\n"
        flow_analysis += "- AST representations: Core to analyzer engine\n"
        flow_analysis += "- Results/Reports: Generated by analyzer, consumed by interfaces\n\n"

        # Communication bottlenecks
        flow_analysis += "COMMUNICATION BOTTLENECKS:\n"
        flow_analysis += "-" * 25 + "\n"

        # Find high fan-in modules (bottlenecks)
        bottlenecks = [(folder, count) for folder, count in self.fan_in.items() if count > 10]
        bottlenecks.sort(key=lambda x: x[1], reverse=True)

        for folder, count in bottlenecks[:5]:
            flow_analysis += f"- {folder.upper()}: {count} incoming dependencies (potential bottleneck)\n"

        return flow_analysis

    def generate_architectural_assessment(self) -> str:
        """Generate comprehensive architectural assessment."""
        assessment = "ARCHITECTURAL ASSESSMENT REPORT\n"
        assessment += "=" * 40 + "\n\n"

        # Architecture quality metrics
        total_folders = len(self.fan_in)
        high_coupling_pairs = sum(
            1 for targets in self.coupling_matrix.values() for strength in targets.values() if strength > 0.3
        )
        circular_deps = len(self.report.get("circular_dependencies", []))

        assessment += "QUALITY METRICS:\n"
        assessment += "-" * 16 + "\n"
        assessment += f"- Total Components: {total_folders}\n"
        assessment += f"- High Coupling Pairs: {high_coupling_pairs}\n"
        assessment += f"- Circular Dependencies: {circular_deps}\n"
        assessment += f"- Architectural Violations: {len(self.report.get('violations', []))}\n\n"

        # Architecture strengths
        assessment += "ARCHITECTURAL STRENGTHS:\n"
        assessment += "-" * 25 + "\n"
        assessment += "+ Clear separation of CLI and MCP interfaces\n"
        assessment += "+ Centralized analysis engine in 'analyzer' module\n"
        assessment += "+ Dedicated utility and configuration modules\n"
        assessment += "+ Modular reporting system\n"
        assessment += "+ Experimental features isolated from core\n\n"

        # Architecture weaknesses
        assessment += "ARCHITECTURAL WEAKNESSES:\n"
        assessment += "-" * 26 + "\n"
        assessment += "- High coupling between analyzer and multiple modules\n"
        assessment += "- Circular dependencies create maintenance challenges\n"
        assessment += "- Policy module tightly coupled to analyzer\n"
        assessment += "- Configuration scattered across modules\n"
        assessment += "- Limited abstraction between layers\n\n"

        # Architecture grade
        total_issues = high_coupling_pairs + circular_deps + len(self.report.get("violations", []))
        if total_issues < 5:
            grade = "A"
        elif total_issues < 15:
            grade = "B"
        elif total_issues < 25:
            grade = "C"
        else:
            grade = "D"

        assessment += f"OVERALL ARCHITECTURE GRADE: {grade}\n"
        assessment += "Based on coupling, dependencies, and violations analysis.\n"

        return assessment

    def generate_refactoring_roadmap(self) -> str:
        """Generate prioritized refactoring roadmap."""
        roadmap = "REFACTORING ROADMAP\n"
        roadmap += "=" * 20 + "\n\n"

        roadmap += "PHASE 1: CRITICAL ISSUES (Immediate - 1-2 weeks)\n"
        roadmap += "-" * 50 + "\n"
        roadmap += "1. Break circular dependencies:\n"
        for cycle in self.report.get("circular_dependencies", [])[:3]:
            cycle_str = " → ".join(cycle)
            roadmap += f"   - {cycle_str}\n"
            roadmap += "     Solution: Extract interface, use dependency injection\n"

        roadmap += "\n2. Reduce critical coupling (>50%):\n"
        critical_coupling = [
            (s, t, str) for s, targets in self.coupling_matrix.items() for t, str in targets.items() if str > 0.5
        ][:3]
        for source, target, strength in critical_coupling:
            roadmap += f"   - {source} → {target} ({strength:.1%})\n"
            roadmap += "     Solution: Introduce facade/adapter pattern\n"

        roadmap += "\nPHASE 2: HIGH PRIORITY (2-4 weeks)\n"
        roadmap += "-" * 40 + "\n"
        roadmap += "1. Refactor analyzer module (high fan-in):\n"
        roadmap += "   - Extract core interfaces\n"
        roadmap += "   - Implement plugin architecture\n"
        roadmap += "   - Reduce direct dependencies\n\n"

        roadmap += "2. Centralize configuration management:\n"
        roadmap += "   - Create unified config module\n"
        roadmap += "   - Remove config scattering\n"
        roadmap += "   - Implement config validation\n\n"

        roadmap += "PHASE 3: MEDIUM PRIORITY (1-2 months)\n"
        roadmap += "-" * 42 + "\n"
        roadmap += "1. Implement proper layering:\n"
        roadmap += "   - Define clear architectural layers\n"
        roadmap += "   - Enforce dependency direction\n"
        roadmap += "   - Add layer validation tests\n\n"

        roadmap += "2. Improve interface consistency:\n"
        roadmap += "   - Standardize error handling\n"
        roadmap += "   - Unify data structures\n"
        roadmap += "   - Document public APIs\n\n"

        roadmap += "PHASE 4: LOW PRIORITY (Long-term)\n"
        roadmap += "-" * 35 + "\n"
        roadmap += "1. Performance optimization:\n"
        roadmap += "   - Optimize hot paths\n"
        roadmap += "   - Implement caching strategies\n"
        roadmap += "   - Profile and tune\n\n"

        roadmap += "2. Enhanced modularity:\n"
        roadmap += "   - Plugin system for analyzers\n"
        roadmap += "   - Dynamic module loading\n"
        roadmap += "   - Improved extensibility\n"

        return roadmap

    def create_comprehensive_report(self) -> str:
        """Create comprehensive architectural analysis report."""
        report = "CONNASCENCE ANALYZER - COMPREHENSIVE ARCHITECTURAL ANALYSIS\n"
        report += "=" * 70 + "\n"
        report += f"Generated on: {Path().absolute()}\n\n"

        # Add all sections
        report += self.generate_architectural_assessment() + "\n\n"
        report += self.generate_component_interaction_matrix() + "\n\n"
        report += self.generate_data_flow_analysis() + "\n\n"
        report += self.generate_refactoring_roadmap() + "\n\n"

        # Add diagrams
        report += "ARCHITECTURE DIAGRAMS\n"
        report += "=" * 25 + "\n\n"
        report += "DEPENDENCY GRAPH:\n"
        report += self.generate_mermaid_dependency_graph() + "\n\n"
        report += "SYSTEM CONTEXT DIAGRAM:\n"
        report += self.generate_c4_architecture_diagram() + "\n"

        return report


def main():
    """Generate comprehensive architectural visualization and analysis."""
    root_path = Path(__file__).parent.parent
    analysis_file = root_path / "analysis" / "dependency_analysis_report.json"

    # Load analysis report
    if not analysis_file.exists():
        print(f"Error: Analysis report not found at {analysis_file}")
        print("Please run dependency_analyzer.py first")
        return

    with open(analysis_file) as f:
        analysis_report = json.load(f)

    # Create visualizer
    visualizer = ArchitectureVisualizer(analysis_report)

    # Generate comprehensive report
    comprehensive_report = visualizer.create_comprehensive_report()

    # Save reports
    output_dir = root_path / "analysis"
    output_dir.mkdir(exist_ok=True)

    # Save comprehensive report
    comprehensive_file = output_dir / "architectural_analysis_comprehensive.md"
    with open(comprehensive_file, "w", encoding="utf-8") as f:
        f.write(comprehensive_report)

    # Save individual diagrams
    diagrams = {
        "dependency_graph.mmd": visualizer.generate_mermaid_dependency_graph(),
        "c4_architecture.mmd": visualizer.generate_c4_architecture_diagram(),
    }

    for filename, content in diagrams.items():
        diagram_file = output_dir / filename
        with open(diagram_file, "w", encoding="utf-8") as f:
            f.write(content)

    print("Architecture visualization complete!")
    print(f"Comprehensive report: {comprehensive_file}")
    print(f"Diagrams saved in: {output_dir}")

    # Print summary
    print("\n" + "=" * 60)
    print("ARCHITECTURAL SUMMARY")
    print("=" * 60)
    print(visualizer.generate_architectural_assessment())


if __name__ == "__main__":
    main()
