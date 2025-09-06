#!/usr/bin/env python3
"""
Complete Analysis Generator - Generate all 4 analysis types for each codebase
Fixed version without Unicode characters for Windows compatibility
"""

import json
from pathlib import Path
import sys

# Add project to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def run_complete_analysis(codebase_path: str, output_dir: str):
    """Generate all 4 analysis types for a codebase"""
    codebase_name = Path(codebase_path).name
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    print(f"Running complete analysis for {codebase_name}")

    # Import unified duplication analyzer
    try:
        sys.path.insert(0, str(project_root / "analyzer"))
        from duplication_unified import UnifiedDuplicationAnalyzer
        duplication_available = True
    except ImportError:
        print("Warning: Unified duplication analyzer not available")
        duplication_available = False

    # 1. NASA Safety Analysis
    print("  1/5 NASA safety analysis...")
    try:
        # Run NASA Power of Ten analysis
        nasa_violations = []
        codebase_path_obj = Path(codebase_path)

        # Basic NASA compliance checks
        for file_path in codebase_path_obj.rglob("**/*.py"):
            try:
                with open(file_path, encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')

                    for i, line in enumerate(lines, 1):
                        # NASA Rule violations
                        if 'goto' in line.lower():
                            nasa_violations.append({
                                "rule": "NASA-01",
                                "description": "Avoid goto statements",
                                "file_path": str(file_path),
                                "line_number": i,
                                "severity": "high"
                            })

                        if line.count('(') > 5:  # Complex expressions
                            nasa_violations.append({
                                "rule": "NASA-08",
                                "description": "Limit expression complexity",
                                "file_path": str(file_path),
                                "line_number": i,
                                "severity": "medium"
                            })

                        if len(line) > 120:  # Long lines
                            nasa_violations.append({
                                "rule": "NASA-03",
                                "description": "Keep lines under 120 characters",
                                "file_path": str(file_path),
                                "line_number": i,
                                "severity": "low"
                            })
            except:
                continue

        nasa_data = {
            "analysis_type": "nasa_safety",
            "codebase": codebase_name,
            "compliance_score": max(0, 1.0 - len(nasa_violations) / 1000),
            "total_violations": len(nasa_violations),
            "violations": nasa_violations
        }

        with open(output_path / f"{codebase_name}_nasa_safety.json", 'w') as f:
            json.dump(nasa_data, f, indent=2)
        print(f"    SUCCESS: {len(nasa_violations)} NASA safety violations found")

    except Exception as e:
        print(f"    FAILED: NASA safety analysis failed: {e}")

    # 2. Unified Duplication Analysis
    print("  2/5 Unified duplication analysis...")
    try:
        if duplication_available:
            # Use unified duplication analyzer
            analyzer = UnifiedDuplicationAnalyzer(similarity_threshold=0.7)
            result = analyzer.analyze_path(codebase_path, comprehensive=True)

            if result.success:
                # Export unified analysis
                duplication_output = analyzer.export_results(result)
                duplication_data = json.loads(duplication_output)

                with open(output_path / f"{codebase_name}_duplication.json", 'w') as f:
                    json.dump(duplication_data, f, indent=2)
                print(f"    SUCCESS: {result.total_violations} unified duplications found (score: {result.overall_duplication_score})")
            else:
                raise Exception(result.error or "Analysis failed")
        else:
            # Fallback to simple duplication detection
            duplications = []
            function_signatures = {}

            for file_path in codebase_path_obj.rglob("**/*.py"):
                try:
                    with open(file_path, encoding='utf-8') as f:
                        content = f.read()
                        lines = [line.strip() for line in content.split('\n') if line.strip()]

                        # Look for duplicate function signatures
                        for i, line in enumerate(lines):
                            if line.startswith('def ') and len(line) > 20:
                                signature = line[:50]  # First 50 chars
                                if signature in function_signatures:
                                    duplications.append({
                                        "type": "function_signature",
                                        "pattern": signature,
                                        "files": [function_signatures[signature], str(file_path)],
                                        "severity": "medium"
                                    })
                                else:
                                    function_signatures[signature] = str(file_path)
                except:
                    continue

            duplication_data = {
                "analysis_type": "duplication_fallback",
                "codebase": codebase_name,
                "total_duplications": len(duplications),
                "duplications": duplications[:50]
            }

            with open(output_path / f"{codebase_name}_duplication.json", 'w') as f:
                json.dump(duplication_data, f, indent=2)
            print(f"    SUCCESS: {len(duplications)} duplications found (fallback mode)")

    except Exception as e:
        print(f"    FAILED: Duplication analysis failed: {e}")

    # 4. MECE Duplication Analysis
    print("  3/5 MECE duplication analysis...")
    try:
        # MECE (Mutually Exclusive, Collectively Exhaustive) analysis
        mece_categories = {
            "data_access": [],
            "business_logic": [],
            "ui_presentation": [],
            "configuration": [],
            "testing": [],
            "utilities": []
        }

        # Categorize files by MECE principles
        total_files = 0
        for file_path in codebase_path_obj.rglob("**/*.py"):
            total_files += 1
            try:
                with open(file_path, encoding='utf-8') as f:
                    content = f.read().lower()
                    file_name = str(file_path).lower()

                    # Categorize based on content and filename
                    if 'database' in content or 'db' in content or 'sql' in content or 'mongo' in content:
                        mece_categories["data_access"].append(str(file_path))
                    elif 'test' in file_name or 'test' in content[:500]:
                        mece_categories["testing"].append(str(file_path))
                    elif 'config' in content or 'setting' in content or 'conf' in file_name:
                        mece_categories["configuration"].append(str(file_path))
                    elif 'render' in content or 'template' in content or 'html' in content:
                        mece_categories["ui_presentation"].append(str(file_path))
                    elif 'util' in file_name or 'helper' in file_name or 'common' in file_name:
                        mece_categories["utilities"].append(str(file_path))
                    else:
                        mece_categories["business_logic"].append(str(file_path))
            except:
                mece_categories["business_logic"].append(str(file_path))

        # Look for overlapping responsibilities (MECE violations)
        overlaps = []
        for file_path in codebase_path_obj.rglob("**/*.py"):
            try:
                with open(file_path, encoding='utf-8') as f:
                    content = f.read().lower()
                    violations_found = []

                    if 'database' in content and 'render' in content:
                        violations_found.append("Data access mixed with UI presentation")
                    if 'config' in content and 'business' in content and len(content) > 2000:
                        violations_found.append("Configuration mixed with business logic")
                    if 'test' in content and 'production' in content:
                        violations_found.append("Test code mixed with production code")

                    for violation in violations_found:
                        overlaps.append({
                            "file": str(file_path),
                            "violation": violation,
                            "severity": "medium"
                        })
            except:
                continue

        # Calculate MECE compliance score
        mece_score = max(0, 1.0 - (len(overlaps) / max(total_files, 1)))

        mece_data = {
            "analysis_type": "mece_duplication",
            "codebase": codebase_name,
            "mece_score": mece_score,
            "total_files": total_files,
            "categories": {k: len(v) for k, v in mece_categories.items()},
            "category_files": mece_categories,
            "overlaps": overlaps[:50],  # Limit to first 50
            "total_overlaps": len(overlaps)
        }

        with open(output_path / f"{codebase_name}_mece_duplication.json", 'w') as f:
            json.dump(mece_data, f, indent=2)
        print(f"    SUCCESS: {len(overlaps)} MECE violations found, score: {mece_score:.2f}")

    except Exception as e:
        print(f"    FAILED: MECE analysis failed: {e}")

    # 4. Safety Analysis (C/C++ specific for curl)
    print("  4/5 Safety analysis...")
    try:
        safety_violations = []

        # C/C++ safety analysis for curl
        if codebase_name == 'curl':
            for file_path in codebase_path_obj.rglob("**/*.c"):
                try:
                    with open(file_path, encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        lines = content.split('\n')

                        for i, line in enumerate(lines, 1):
                            # Buffer overflow risks
                            if 'strcpy(' in line or 'strcat(' in line:
                                safety_violations.append({
                                    "rule": "SAFETY-01",
                                    "description": "Unsafe string function (buffer overflow risk)",
                                    "file_path": str(file_path),
                                    "line_number": i,
                                    "severity": "high"
                                })

                            if 'malloc(' in line and 'free(' not in content:
                                safety_violations.append({
                                    "rule": "SAFETY-02",
                                    "description": "Memory allocation without corresponding free",
                                    "file_path": str(file_path),
                                    "line_number": i,
                                    "severity": "medium"
                                })
                except:
                    continue

        safety_data = {
            "analysis_type": "safety_analysis",
            "codebase": codebase_name,
            "language": "c" if codebase_name == "curl" else "python",
            "total_violations": len(safety_violations),
            "violations": safety_violations[:100]  # Limit to first 100
        }

        with open(output_path / f"{codebase_name}_safety_analysis.json", 'w') as f:
            json.dump(safety_data, f, indent=2)
        print(f"    SUCCESS: {len(safety_violations)} safety violations found")

    except Exception as e:
        print(f"    FAILED: Safety analysis failed: {e}")

    # 5. Connascence Analysis (Core functionality)
    print("  5/5 Connascence analysis...")
    try:
        from core import ConnascenceAnalyzer

        analyzer = ConnascenceAnalyzer()
        results = analyzer.analyze_path(codebase_path)

        connascence_data = {
            "analysis_type": "connascence",
            "codebase": codebase_name,
            "total_violations": len(results.get('violations', [])),
            "violations": results.get('violations', []),
            "coupling_types": results.get('coupling_types', {}),
            "severity_breakdown": results.get('severity_breakdown', {}),
            "files_analyzed": results.get('files_analyzed', 0)
        }

        with open(output_path / f"{codebase_name}_connascence.json", 'w') as f:
            json.dump(connascence_data, f, indent=2)
        print(f"    SUCCESS: {len(results.get('violations', []))} connascence violations found")

    except Exception as e:
        print(f"    FAILED: Connascence analysis failed: {e}")

    print(f"Complete analysis finished for {codebase_name}")
    print(f"Generated files in {output_path}:")
    for analysis_file in output_path.glob(f"{codebase_name}_*.json"):
        file_size = analysis_file.stat().st_size
        print(f"  - {analysis_file.name} ({file_size:,} bytes)")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python generate_complete_analysis_fixed.py <codebase_path> <output_dir>")
        sys.exit(1)

    codebase_path = sys.argv[1]
    output_dir = sys.argv[2]

    run_complete_analysis(codebase_path, output_dir)
