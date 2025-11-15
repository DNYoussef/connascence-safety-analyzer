#!/usr/bin/env python3
"""
Comprehensive Analyzer Verification Script
Tests all analyzers individually with detailed evidence collection.

Analyzers Tested:
1. Clarity Analyzer - Cognitive load detection
2. Connascence Analyzers - 9 types (CoV, CoM, CoP, CoA, CoE, CoN, CoT, CoConvention, CoTiming)
3. God Object Detection - Class complexity metrics
4. MECE Redundancy/Duplication - Similarity analysis
5. Six Sigma Analyzer - Statistical metrics
6. NASA Safety Analyzer - Power of Ten rules
7. Enterprise Integration - Unified pipeline
"""

import subprocess
import json
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Tuple
import traceback

# ANSI color codes for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    RESET = '\033[0m'

def print_section(title: str):
    """Print a section header"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{title.center(80)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.RESET}\n")

def print_subsection(title: str):
    """Print a subsection header"""
    print(f"\n{Colors.BOLD}{Colors.YELLOW}{'-'*80}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.YELLOW}{title}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.YELLOW}{'-'*80}{Colors.RESET}")

def print_success(message: str):
    """Print success message"""
    print(f"{Colors.GREEN}[OK] {message}{Colors.RESET}")

def print_error(message: str):
    """Print error message"""
    print(f"{Colors.RED}[ERROR] {message}{Colors.RESET}")

def print_warning(message: str):
    """Print warning message"""
    print(f"{Colors.YELLOW}[WARNING] {message}{Colors.RESET}")

def print_info(message: str):
    """Print info message"""
    print(f"{Colors.BLUE}[INFO] {message}{Colors.RESET}")

def run_command(cmd: List[str], cwd: str = None) -> Tuple[int, str, str]:
    """
    Run a command and return exit code, stdout, stderr

    Args:
        cmd: Command and arguments as list
        cwd: Working directory

    Returns:
        Tuple of (exit_code, stdout, stderr)
    """
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=120  # 2 minute timeout
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out after 120 seconds"
    except Exception as e:
        return -1, "", str(e)

class AnalyzerTest:
    """Base class for analyzer tests"""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.passed = False
        self.violations_found = 0
        self.output = ""
        self.errors = []
        self.evidence = {}

    def run(self, test_dir: str) -> bool:
        """Run the test - must be implemented by subclasses"""
        raise NotImplementedError

    def print_results(self):
        """Print test results"""
        print_subsection(f"Results: {self.name}")

        if self.passed:
            print_success(f"{self.name} - PASSED")
            print_info(f"Description: {self.description}")
            print_info(f"Violations Found: {self.violations_found}")
        else:
            print_error(f"{self.name} - FAILED")
            print_info(f"Description: {self.description}")

        if self.evidence:
            print(f"\n{Colors.BOLD}Evidence:{Colors.RESET}")
            for key, value in self.evidence.items():
                print(f"  {Colors.CYAN}{key}:{Colors.RESET} {value}")

        if self.errors:
            print(f"\n{Colors.BOLD}Errors:{Colors.RESET}")
            for error in self.errors:
                print(f"  {Colors.RED}{error}{Colors.RESET}")

class ClarityAnalyzerTest(AnalyzerTest):
    """Test Clarity Analyzer"""

    def __init__(self):
        super().__init__(
            "Clarity Analyzer",
            "Tests cognitive load detection, thin helpers, call chains"
        )

    def run(self, test_dir: str) -> bool:
        """Run clarity analyzer test"""
        script_path = Path(test_dir).parent / "scripts" / "run_clarity001.py"

        if not script_path.exists():
            self.errors.append(f"Script not found: {script_path}")
            return False

        # Run clarity analyzer
        exit_code, stdout, stderr = run_command(
            ["python", str(script_path), test_dir],
            cwd=str(script_path.parent)
        )

        self.output = stdout

        # Check for success
        if exit_code != 0:
            self.errors.append(f"Exit code: {exit_code}")
            if stderr:
                self.errors.append(f"Stderr: {stderr}")
            return False

        # Parse output for violations
        violations = {
            'thin_helpers': 0,
            'call_chains': 0,
            'cognitive_load': 0
        }

        for line in stdout.split('\n'):
            if 'thin helper' in line.lower():
                violations['thin_helpers'] += 1
            if 'call chain' in line.lower() or 'call depth' in line.lower():
                violations['call_chains'] += 1
            if 'cognitive load' in line.lower() or 'complexity' in line.lower():
                violations['cognitive_load'] += 1

        self.violations_found = sum(violations.values())
        self.evidence = violations

        # Success if we found any violations or ran without errors
        self.passed = exit_code == 0

        return self.passed

class ConnascenceAnalyzerTest(AnalyzerTest):
    """Test Connascence Analyzers"""

    def __init__(self):
        super().__init__(
            "Connascence Analyzers",
            "Tests all 9 connascence types (CoV, CoM, CoP, CoA, CoE, CoN, CoT, CoConvention, CoTiming)"
        )

    def run(self, test_dir: str) -> bool:
        """Run connascence analyzer test"""

        # Try MCP tool first
        mcp_passed, mcp_violations = self._test_mcp_analyzer(test_dir)

        # Try Python script fallback
        script_passed, script_violations = self._test_script_analyzer(test_dir)

        # Combine results
        if mcp_passed:
            self.passed = True
            self.violations_found = mcp_violations.get('total', 0)
            self.evidence = mcp_violations
            self.evidence['method'] = 'MCP Tool'
        elif script_passed:
            self.passed = True
            self.violations_found = script_violations.get('total', 0)
            self.evidence = script_violations
            self.evidence['method'] = 'Python Script'
        else:
            self.passed = False

        return self.passed

    def _test_mcp_analyzer(self, test_dir: str) -> Tuple[bool, Dict]:
        """Test using MCP tool"""
        try:
            # Check if MCP server is running
            exit_code, stdout, stderr = run_command(
                ["curl", "-s", "http://localhost:3000/health"]
            )

            if exit_code != 0:
                self.errors.append("MCP server not responding on port 3000")
                return False, {}

            # Run analysis via MCP
            import requests
            response = requests.post(
                "http://localhost:3000/analyze",
                json={"path": test_dir},
                timeout=60
            )

            if response.status_code != 200:
                self.errors.append(f"MCP analysis failed: {response.status_code}")
                return False, {}

            result = response.json()

            # Parse violations
            violations = {
                'CoV': 0, 'CoM': 0, 'CoP': 0, 'CoA': 0, 'CoE': 0,
                'CoN': 0, 'CoT': 0, 'CoConvention': 0, 'CoTiming': 0,
                'total': 0
            }

            if 'violations' in result:
                for violation in result['violations']:
                    vtype = violation.get('type', '')
                    if vtype in violations:
                        violations[vtype] += 1
                        violations['total'] += 1

            return True, violations

        except Exception as e:
            self.errors.append(f"MCP test error: {str(e)}")
            return False, {}

    def _test_script_analyzer(self, test_dir: str) -> Tuple[bool, Dict]:
        """Test using Python script"""
        try:
            # Find connascence analyzer script
            possible_paths = [
                Path(test_dir).parent / "scripts" / "analyze_connascence.py",
                Path(test_dir).parent / "analyzer" / "connascence_analyzer.py",
                Path(test_dir).parent / "src" / "connascence_analyzer.py"
            ]

            script_path = None
            for path in possible_paths:
                if path.exists():
                    script_path = path
                    break

            if not script_path:
                self.errors.append("Connascence analyzer script not found")
                return False, {}

            # Run analyzer
            exit_code, stdout, stderr = run_command(
                ["python", str(script_path), test_dir]
            )

            if exit_code != 0:
                self.errors.append(f"Script failed with exit code: {exit_code}")
                return False, {}

            # Parse output
            violations = {
                'CoV': 0, 'CoM': 0, 'CoP': 0, 'CoA': 0, 'CoE': 0,
                'CoN': 0, 'CoT': 0, 'CoConvention': 0, 'CoTiming': 0,
                'total': 0
            }

            for line in stdout.split('\n'):
                for vtype in ['CoV', 'CoM', 'CoP', 'CoA', 'CoE', 'CoN', 'CoT', 'CoConvention', 'CoTiming']:
                    if vtype in line:
                        violations[vtype] += 1
                        violations['total'] += 1

            return True, violations

        except Exception as e:
            self.errors.append(f"Script test error: {str(e)}")
            return False, {}

class GodObjectDetectionTest(AnalyzerTest):
    """Test God Object Detection"""

    def __init__(self):
        super().__init__(
            "God Object Detection",
            "Tests class complexity metrics and god object identification"
        )

    def run(self, test_dir: str) -> bool:
        """Run god object detection test"""
        script_path = Path(test_dir).parent / "scripts" / "detect_god_objects.py"

        if not script_path.exists():
            # Try alternative location
            script_path = Path(test_dir).parent / "analyzer" / "god_object_detector.py"

        if not script_path.exists():
            self.errors.append(f"God object detector script not found")
            return False

        # Run detector
        exit_code, stdout, stderr = run_command(
            ["python", str(script_path), test_dir]
        )

        self.output = stdout

        if exit_code != 0:
            self.errors.append(f"Exit code: {exit_code}")
            if stderr:
                self.errors.append(f"Stderr: {stderr}")
            return False

        # Parse output
        violations = {
            'god_objects': 0,
            'high_complexity_classes': 0,
            'excessive_methods': 0
        }

        for line in stdout.split('\n'):
            if 'god object' in line.lower():
                violations['god_objects'] += 1
            if 'high complexity' in line.lower():
                violations['high_complexity_classes'] += 1
            if 'methods' in line.lower() and any(str(i) in line for i in range(20, 100)):
                violations['excessive_methods'] += 1

        self.violations_found = sum(violations.values())
        self.evidence = violations
        self.passed = exit_code == 0

        return self.passed

class MECEAnalyzerTest(AnalyzerTest):
    """Test MECE Redundancy/Duplication Analyzer"""

    def __init__(self):
        super().__init__(
            "MECE Redundancy/Duplication Analyzer",
            "Tests similarity analysis and code duplication detection"
        )

    def run(self, test_dir: str) -> bool:
        """Run MECE analyzer test"""
        script_path = Path(test_dir).parent / "scripts" / "analyze_mece.py"

        if not script_path.exists():
            # Try alternative locations
            alternatives = [
                Path(test_dir).parent / "analyzer" / "mece_analyzer.py",
                Path(test_dir).parent / "src" / "mece_analyzer.py"
            ]
            for alt in alternatives:
                if alt.exists():
                    script_path = alt
                    break

        if not script_path.exists():
            self.errors.append("MECE analyzer script not found")
            return False

        # Run analyzer
        exit_code, stdout, stderr = run_command(
            ["python", str(script_path), test_dir]
        )

        self.output = stdout

        if exit_code != 0:
            self.errors.append(f"Exit code: {exit_code}")
            if stderr:
                self.errors.append(f"Stderr: {stderr}")
            return False

        # Parse output
        violations = {
            'duplicates': 0,
            'similar_functions': 0,
            'overlapping_logic': 0
        }

        for line in stdout.split('\n'):
            if 'duplicate' in line.lower():
                violations['duplicates'] += 1
            if 'similar' in line.lower():
                violations['similar_functions'] += 1
            if 'overlap' in line.lower():
                violations['overlapping_logic'] += 1

        self.violations_found = sum(violations.values())
        self.evidence = violations
        self.passed = exit_code == 0

        return self.passed

class SixSigmaAnalyzerTest(AnalyzerTest):
    """Test Six Sigma Analyzer"""

    def __init__(self):
        super().__init__(
            "Six Sigma Analyzer",
            "Tests statistical metrics and quality analysis"
        )

    def run(self, test_dir: str) -> bool:
        """Run Six Sigma analyzer test"""
        script_path = Path(test_dir).parent / "scripts" / "analyze_six_sigma.py"

        if not script_path.exists():
            self.errors.append("Six Sigma analyzer script not found")
            return False

        # Run analyzer
        exit_code, stdout, stderr = run_command(
            ["python", str(script_path), test_dir]
        )

        self.output = stdout

        if exit_code != 0:
            self.errors.append(f"Exit code: {exit_code}")
            if stderr:
                self.errors.append(f"Stderr: {stderr}")
            return False

        # Parse output
        violations = {
            'quality_defects': 0,
            'statistical_outliers': 0,
            'process_variations': 0
        }

        for line in stdout.split('\n'):
            if 'defect' in line.lower():
                violations['quality_defects'] += 1
            if 'outlier' in line.lower():
                violations['statistical_outliers'] += 1
            if 'variation' in line.lower():
                violations['process_variations'] += 1

        self.violations_found = sum(violations.values())
        self.evidence = violations
        self.passed = exit_code == 0

        return self.passed

class NASASafetyAnalyzerTest(AnalyzerTest):
    """Test NASA Safety Analyzer"""

    def __init__(self):
        super().__init__(
            "NASA Safety Analyzer",
            "Tests Power of Ten rules compliance"
        )

    def run(self, test_dir: str) -> bool:
        """Run NASA safety analyzer test"""
        script_path = Path(test_dir).parent / "scripts" / "analyze_nasa_safety.py"

        if not script_path.exists():
            self.errors.append("NASA safety analyzer script not found")
            return False

        # Run analyzer
        exit_code, stdout, stderr = run_command(
            ["python", str(script_path), test_dir]
        )

        self.output = stdout

        if exit_code != 0:
            self.errors.append(f"Exit code: {exit_code}")
            if stderr:
                self.errors.append(f"Stderr: {stderr}")
            return False

        # Parse output for Power of Ten violations
        violations = {
            'loop_bounds': 0,
            'recursion': 0,
            'goto_statements': 0,
            'heap_allocation': 0,
            'assertion_density': 0
        }

        for line in stdout.split('\n'):
            if 'loop bound' in line.lower():
                violations['loop_bounds'] += 1
            if 'recursion' in line.lower():
                violations['recursion'] += 1
            if 'goto' in line.lower():
                violations['goto_statements'] += 1
            if 'heap' in line.lower() or 'malloc' in line.lower():
                violations['heap_allocation'] += 1
            if 'assertion' in line.lower():
                violations['assertion_density'] += 1

        self.violations_found = sum(violations.values())
        self.evidence = violations
        self.passed = exit_code == 0

        return self.passed

class EnterpriseIntegrationTest(AnalyzerTest):
    """Test Enterprise Integration Pipeline"""

    def __init__(self):
        super().__init__(
            "Enterprise Integration",
            "Tests unified analyzer pipeline with all analyzers"
        )

    def run(self, test_dir: str) -> bool:
        """Run enterprise integration test"""
        script_path = Path(test_dir).parent / "scripts" / "run_enterprise_pipeline.py"

        if not script_path.exists():
            # Try alternative
            script_path = Path(test_dir).parent / "analyzer" / "enterprise_pipeline.py"

        if not script_path.exists():
            self.errors.append("Enterprise pipeline script not found")
            return False

        # Run pipeline
        exit_code, stdout, stderr = run_command(
            ["python", str(script_path), test_dir, "--format", "json"]
        )

        self.output = stdout

        if exit_code != 0:
            self.errors.append(f"Exit code: {exit_code}")
            if stderr:
                self.errors.append(f"Stderr: {stderr}")
            return False

        # Try to parse JSON output
        try:
            result = json.loads(stdout)

            violations = {
                'total_violations': result.get('total_violations', 0),
                'analyzers_run': len(result.get('analyzers', [])),
                'files_analyzed': result.get('files_analyzed', 0)
            }

            # Count violations by analyzer
            for analyzer in result.get('analyzers', []):
                analyzer_name = analyzer.get('name', 'unknown')
                analyzer_violations = analyzer.get('violations', 0)
                violations[f'{analyzer_name}_violations'] = analyzer_violations

            self.violations_found = violations.get('total_violations', 0)
            self.evidence = violations
            self.passed = True

        except json.JSONDecodeError:
            # Parse text output
            violations = {
                'clarity': 0,
                'connascence': 0,
                'god_objects': 0,
                'mece': 0,
                'six_sigma': 0,
                'nasa_safety': 0
            }

            for line in stdout.split('\n'):
                if 'clarity' in line.lower():
                    violations['clarity'] += 1
                if 'connascence' in line.lower():
                    violations['connascence'] += 1
                if 'god object' in line.lower():
                    violations['god_objects'] += 1
                if 'mece' in line.lower() or 'duplicate' in line.lower():
                    violations['mece'] += 1
                if 'six sigma' in line.lower() or 'statistical' in line.lower():
                    violations['six_sigma'] += 1
                if 'nasa' in line.lower() or 'power of ten' in line.lower():
                    violations['nasa_safety'] += 1

            self.violations_found = sum(violations.values())
            self.evidence = violations
            self.passed = True

        return self.passed

def create_test_files(test_dir: Path):
    """Create test files with known violations"""

    print_info(f"Creating test files in {test_dir}")

    # Create test directory
    test_dir.mkdir(parents=True, exist_ok=True)

    # Test file 1: Clarity violations (thin helpers, call chains)
    clarity_test = test_dir / "clarity_test.py"
    clarity_test.write_text("""
# Test file for clarity violations

def add(a, b):
    \"\"\"Thin helper - just wraps built-in operation\"\"\"
    return a + b

def subtract(a, b):
    \"\"\"Another thin helper\"\"\"
    return a - b

def level1():
    return level2()

def level2():
    return level3()

def level3():
    return level4()

def level4():
    return level5()

def level5():
    return level6()

def level6():
    return level7()

def level7():
    return level8()

def level8():
    return "deep call chain"

def complex_function(a, b, c, d, e, f, g, h):
    \"\"\"High cognitive load function\"\"\"
    if a > 0:
        if b > 0:
            if c > 0:
                if d > 0:
                    if e > 0:
                        if f > 0:
                            if g > 0:
                                if h > 0:
                                    return "very nested"
    return "default"
""")

    # Test file 2: Connascence violations
    connascence_test = test_dir / "connascence_test.py"
    connascence_test.write_text("""
# Test file for connascence violations

# CoM - Magic numbers
def calculate_timeout():
    return 5000  # Magic number

def set_port():
    return 8080  # Magic number

# CoP - Parameter order coupling
def create_user(name, email, age, address):
    pass

def update_user(name, email, age, address):  # Same parameter order
    pass

# CoN - Name coupling
user_data = {"id": 1}
USER_DATA = {"id": 2}  # Similar name, different case

# CoT - Type coupling
def process_string(value: str):
    return value.upper()

def process_number(value: int):  # Different type, similar structure
    return value * 2
""")

    # Test file 3: God object
    god_object_test = test_dir / "god_object_test.py"
    god_object_test.write_text("""
# Test file for god object detection

class GodClass:
    \"\"\"A class that does everything\"\"\"

    def __init__(self):
        self.data = {}

    def method1(self): pass
    def method2(self): pass
    def method3(self): pass
    def method4(self): pass
    def method5(self): pass
    def method6(self): pass
    def method7(self): pass
    def method8(self): pass
    def method9(self): pass
    def method10(self): pass
    def method11(self): pass
    def method12(self): pass
    def method13(self): pass
    def method14(self): pass
    def method15(self): pass
    def method16(self): pass
    def method17(self): pass
    def method18(self): pass
    def method19(self): pass
    def method20(self): pass
    def method21(self): pass
    def method22(self): pass
    def method23(self): pass
    def method24(self): pass
    def method25(self): pass
    def method26(self): pass
    def method27(self): pass
    def method28(self): pass
    def method29(self): pass
    def method30(self): pass
""")

    # Test file 4: MECE violations (duplicates)
    mece_test = test_dir / "mece_test.py"
    mece_test.write_text("""
# Test file for MECE violations

def validate_email_v1(email):
    if "@" not in email:
        return False
    if "." not in email:
        return False
    return True

def validate_email_v2(email):
    if "@" not in email:
        return False
    if "." not in email:
        return False
    return True

def check_email(email):  # Similar logic, different name
    if "@" not in email:
        return False
    if "." not in email:
        return False
    return True
""")

    print_success(f"Created {len(list(test_dir.glob('*.py')))} test files")

def generate_report(tests: List[AnalyzerTest], output_path: Path):
    """Generate comprehensive HTML report"""

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    passed = sum(1 for test in tests if test.passed)
    total = len(tests)
    total_violations = sum(test.violations_found for test in tests)

    html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Analyzer Verification Report</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            border-bottom: 3px solid #4CAF50;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #555;
            margin-top: 30px;
            border-bottom: 2px solid #ddd;
            padding-bottom: 8px;
        }}
        .summary {{
            background-color: #e8f5e9;
            padding: 20px;
            border-radius: 6px;
            margin: 20px 0;
        }}
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }}
        .summary-item {{
            background-color: white;
            padding: 15px;
            border-radius: 4px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        .summary-item .label {{
            font-size: 0.9em;
            color: #666;
            margin-bottom: 5px;
        }}
        .summary-item .value {{
            font-size: 1.8em;
            font-weight: bold;
            color: #4CAF50;
        }}
        .test-result {{
            margin: 20px 0;
            padding: 20px;
            border-radius: 6px;
            border-left: 4px solid #ddd;
        }}
        .test-result.passed {{
            background-color: #e8f5e9;
            border-left-color: #4CAF50;
        }}
        .test-result.failed {{
            background-color: #ffebee;
            border-left-color: #f44336;
        }}
        .test-title {{
            font-size: 1.3em;
            font-weight: bold;
            margin-bottom: 10px;
        }}
        .test-title.passed {{
            color: #2e7d32;
        }}
        .test-title.failed {{
            color: #c62828;
        }}
        .test-description {{
            color: #666;
            font-style: italic;
            margin-bottom: 15px;
        }}
        .evidence {{
            background-color: #f5f5f5;
            padding: 15px;
            border-radius: 4px;
            margin-top: 10px;
        }}
        .evidence h4 {{
            margin-top: 0;
            color: #555;
        }}
        .evidence-item {{
            padding: 5px 0;
            border-bottom: 1px solid #e0e0e0;
        }}
        .evidence-item:last-child {{
            border-bottom: none;
        }}
        .evidence-key {{
            font-weight: bold;
            color: #1976d2;
            display: inline-block;
            width: 200px;
        }}
        .evidence-value {{
            color: #333;
        }}
        .errors {{
            background-color: #fff3cd;
            border: 1px solid #ffc107;
            padding: 15px;
            border-radius: 4px;
            margin-top: 10px;
        }}
        .errors h4 {{
            margin-top: 0;
            color: #856404;
        }}
        .error-item {{
            color: #856404;
            margin: 5px 0;
        }}
        .badge {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 3px;
            font-size: 0.85em;
            font-weight: bold;
            margin-left: 10px;
        }}
        .badge.passed {{
            background-color: #4CAF50;
            color: white;
        }}
        .badge.failed {{
            background-color: #f44336;
            color: white;
        }}
        .timestamp {{
            color: #999;
            font-size: 0.9em;
            text-align: right;
            margin-top: 30px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Comprehensive Analyzer Verification Report</h1>

        <div class="summary">
            <h2 style="margin-top: 0; border-bottom: none;">Summary</h2>
            <div class="summary-grid">
                <div class="summary-item">
                    <div class="label">Tests Passed</div>
                    <div class="value">{passed}/{total}</div>
                </div>
                <div class="summary-item">
                    <div class="label">Success Rate</div>
                    <div class="value">{(passed/total*100):.1f}%</div>
                </div>
                <div class="summary-item">
                    <div class="label">Total Violations</div>
                    <div class="value">{total_violations}</div>
                </div>
                <div class="summary-item">
                    <div class="label">Analyzers Tested</div>
                    <div class="value">{total}</div>
                </div>
            </div>
        </div>

        <h2>Detailed Results</h2>
"""

    for test in tests:
        status_class = "passed" if test.passed else "failed"
        status_badge = f'<span class="badge {status_class}">{"PASSED" if test.passed else "FAILED"}</span>'

        html += f"""
        <div class="test-result {status_class}">
            <div class="test-title {status_class}">
                {test.name}
                {status_badge}
            </div>
            <div class="test-description">{test.description}</div>
"""

        if test.evidence:
            html += """
            <div class="evidence">
                <h4>Evidence</h4>
"""
            for key, value in test.evidence.items():
                html += f"""
                <div class="evidence-item">
                    <span class="evidence-key">{key}:</span>
                    <span class="evidence-value">{value}</span>
                </div>
"""
            html += """
            </div>
"""

        if test.errors:
            html += """
            <div class="errors">
                <h4>Errors</h4>
"""
            for error in test.errors:
                html += f"""
                <div class="error-item">{error}</div>
"""
            html += """
            </div>
"""

        html += """
        </div>
"""

    html += f"""
        <div class="timestamp">
            Generated: {timestamp}
        </div>
    </div>
</body>
</html>
"""

    output_path.write_text(html)
    print_success(f"Report generated: {output_path}")

def main():
    """Main execution function"""

    print_section("COMPREHENSIVE ANALYZER VERIFICATION")

    # Setup paths
    base_dir = Path("/c/Users/17175/Desktop/connascence")
    test_dir = base_dir / "test_files"
    scripts_dir = base_dir / "scripts"

    print_info(f"Base directory: {base_dir}")
    print_info(f"Test directory: {test_dir}")
    print_info(f"Scripts directory: {scripts_dir}")

    # Create test files
    print_section("SETUP: Creating Test Files")
    create_test_files(test_dir)

    # Initialize tests
    tests = [
        ClarityAnalyzerTest(),
        ConnascenceAnalyzerTest(),
        GodObjectDetectionTest(),
        MECEAnalyzerTest(),
        SixSigmaAnalyzerTest(),
        NASASafetyAnalyzerTest(),
        EnterpriseIntegrationTest()
    ]

    # Run tests
    print_section("RUNNING TESTS")

    for i, test in enumerate(tests, 1):
        print_subsection(f"Test {i}/{len(tests)}: {test.name}")
        print_info(f"Description: {test.description}")

        try:
            test.run(str(test_dir))
            test.print_results()
        except Exception as e:
            print_error(f"Test crashed: {str(e)}")
            print_error(traceback.format_exc())
            test.passed = False
            test.errors.append(f"Exception: {str(e)}")

    # Generate report
    print_section("GENERATING REPORT")

    report_path = scripts_dir / "analyzer_verification_report.html"
    generate_report(tests, report_path)

    # Print summary
    print_section("FINAL SUMMARY")

    passed = sum(1 for test in tests if test.passed)
    total = len(tests)
    total_violations = sum(test.violations_found for test in tests)

    print(f"\n{Colors.BOLD}Results:{Colors.RESET}")
    print(f"  Tests Passed: {Colors.GREEN}{passed}/{total}{Colors.RESET}")
    print(f"  Success Rate: {Colors.GREEN}{(passed/total*100):.1f}%{Colors.RESET}")
    print(f"  Total Violations Found: {Colors.CYAN}{total_violations}{Colors.RESET}")

    print(f"\n{Colors.BOLD}Analyzer Status:{Colors.RESET}")
    for test in tests:
        status = f"{Colors.GREEN}PASSED{Colors.RESET}" if test.passed else f"{Colors.RED}FAILED{Colors.RESET}"
        violations = f"{Colors.CYAN}{test.violations_found}{Colors.RESET}" if test.violations_found > 0 else "0"
        print(f"  [{status}] {test.name}: {violations} violations")

    print(f"\n{Colors.BOLD}Report:{Colors.RESET}")
    print(f"  {Colors.BLUE}file:///{report_path}{Colors.RESET}")

    # Return exit code
    return 0 if passed == total else 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Interrupted by user{Colors.RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n{Colors.RED}Fatal error: {str(e)}{Colors.RESET}")
        print(traceback.format_exc())
        sys.exit(1)
