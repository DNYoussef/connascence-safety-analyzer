#!/usr/bin/env python3
"""
Complete Analysis Generator - Generate all 4 analysis types for each codebase
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

    # 1. Connascence Analysis
    print("  1/4 Connascence analysis...")
    try:
        from analyzer.check_connascence import ConnascenceAnalyzer
        connascence_analyzer = ConnascenceAnalyzer()

        # Analyze all files in codebase
        violations = []
        codebase_path_obj = Path(codebase_path)

        # Find all Python, JavaScript, and C files
        file_patterns = ["**/*.py", "**/*.js", "**/*.c", "**/*.h", "**/*.cpp", "**/*.hpp"]
        for pattern in file_patterns:
            for file_path in codebase_path_obj.rglob(pattern):
                try:
                    file_violations = connascence_analyzer.analyze_file(file_path)
                    violations.extend(file_violations)
                except Exception:
                    continue

        # Convert to JSON format
        connascence_data = {
            "analysis_type": "connascence",
            "codebase": codebase_name,
            "total_violations": len(violations),
            "violations": [
                {
                    "type": v.type,
                    "severity": v.severity,
                    "file_path": str(v.file_path),
                    "line_number": getattr(v, 'line_number', 0),
                    "description": v.description,
                    "recommendation": getattr(v, 'recommendation', ''),
                }
                for v in violations
            ]
        }

        with open(output_path / f"{codebase_name}_connascence.json", 'w') as f:
            json.dump(connascence_data, f, indent=2)
        print(f"    ✓ {len(violations)} connascence violations found")

    except Exception as e:
        print(f"    ✗ Connascence analysis failed: {e}")

    # 2. NASA Safety Analysis
    print("  2/4 NASA safety analysis...")
    try:
        # Run NASA Power of Ten analysis
        nasa_violations = []

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
            except:
                continue

        nasa_data = {
            "analysis_type": "nasa_safety",
            "codebase": codebase_name,
            "compliance_score": max(0, 1.0 - len(nasa_violations) / 100),
            "total_violations": len(nasa_violations),
            "violations": nasa_violations
        }

        with open(output_path / f"{codebase_name}_nasa_safety.json", 'w') as f:
            json.dump(nasa_data, f, indent=2)
        print(f"    ✓ {len(nasa_violations)} NASA safety violations found")

    except Exception as e:
        print(f"    ✗ NASA safety analysis failed: {e}")

    # 3. Duplication Analysis
    print("  3/4 Duplication analysis...")
    try:
        duplications = []

        # Simple duplication detection
        file_contents = {}
        for file_path in codebase_path_obj.rglob("**/*.py"):
            try:
                with open(file_path, encoding='utf-8') as f:
                    content = f.read()
                    lines = [line.strip() for line in content.split('\n') if line.strip()]

                    # Look for duplicate function signatures
                    for i, line in enumerate(lines):
                        if line.startswith('def ') and len(line) > 20:
                            signature = line[:50]  # First 50 chars
                            if signature in file_contents:
                                duplications.append({
                                    "type": "function_signature",
                                    "pattern": signature,
                                    "files": [file_contents[signature], str(file_path)],
                                    "severity": "medium"
                                })
                            else:
                                file_contents[signature] = str(file_path)
            except:
                continue

        duplication_data = {
            "analysis_type": "duplication",
            "codebase": codebase_name,
            "total_duplications": len(duplications),
            "duplications": duplications
        }

        with open(output_path / f"{codebase_name}_duplication.json", 'w') as f:
            json.dump(duplication_data, f, indent=2)
        print(f"    ✓ {len(duplications)} duplications found")

    except Exception as e:
        print(f"    ✗ Duplication analysis failed: {e}")

    # 4. MECE Duplication Analysis
    print("  4/4 MECE duplication analysis...")
    try:
        # MECE (Mutually Exclusive, Collectively Exhaustive) analysis
        mece_categories = {
            "data_access": [],
            "business_logic": [],
            "ui_presentation": [],
            "configuration": [],
            "testing": []
        }

        # Categorize files by MECE principles
        for file_path in codebase_path_obj.rglob("**/*.py"):
            try:
                with open(file_path, encoding='utf-8') as f:
                    content = f.read().lower()

                    if 'database' in content or 'db' in content or 'sql' in content:
                        mece_categories["data_access"].append(str(file_path))
                    elif 'test' in str(file_path).lower():
                        mece_categories["testing"].append(str(file_path))
                    elif 'config' in content or 'setting' in content:
                        mece_categories["configuration"].append(str(file_path))
                    elif 'render' in content or 'template' in content:
                        mece_categories["ui_presentation"].append(str(file_path))
                    else:
                        mece_categories["business_logic"].append(str(file_path))
            except:
                continue

        # Calculate MECE compliance score
        total_files = sum(len(files) for files in mece_categories.values())
        mece_score = 1.0 if total_files > 0 else 0.0

        # Look for overlapping responsibilities (MECE violations)
        overlaps = []
        for file_path in codebase_path_obj.rglob("**/*.py"):
            try:
                with open(file_path, encoding='utf-8') as f:
                    content = f.read().lower()
                    if 'database' in content and 'render' in content:
                        overlaps.append({
                            "file": str(file_path),
                            "violation": "Data access mixed with UI presentation",
                            "severity": "high"
                        })
            except:
                continue

        mece_data = {
            "analysis_type": "mece_duplication",
            "codebase": codebase_name,
            "mece_score": max(0, mece_score - len(overlaps) * 0.1),
            "categories": mece_categories,
            "overlaps": overlaps,
            "total_overlaps": len(overlaps)
        }

        with open(output_path / f"{codebase_name}_mece_duplication.json", 'w') as f:
            json.dump(mece_data, f, indent=2)
        print(f"    ✓ {len(overlaps)} MECE violations found")

    except Exception as e:
        print(f"    ✗ MECE analysis failed: {e}")

    print(f"Complete analysis finished for {codebase_name}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python generate_complete_analysis.py <codebase_path> <output_dir>")
        sys.exit(1)

    codebase_path = sys.argv[1]
    output_dir = sys.argv[2]

    run_complete_analysis(codebase_path, output_dir)
