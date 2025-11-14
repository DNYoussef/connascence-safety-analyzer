# Week 2 Implementation Plan: Clarity Linter MVP

**Project:** Connascence Safety Analyzer - Clarity Linter Integration
**Duration:** 80-120 hours (10-15 working days)
**Team Size:** 5 FTEs
**Sprint:** 2025-11-20 to 2025-12-03
**Version:** 1.0.0
**Status:** Ready for Execution

---

## Executive Summary

Week 2 delivers a **production-ready Clarity Linter MVP** with 5 core rules detecting structural violations across language-agnostic codebases. The implementation builds on Week 1's infrastructure (workflows, quality gates, unified orchestrator) by adding real detection algorithms with NASA-standard compliance and SARIF output.

**Key Deliverables:**
- 5 functional Clarity Linter rules with AST-based detection
- unified_quality_gate.py with real analyzer integration
- External codebase validation framework
- Self-scan infrastructure for dogfooding
- Comprehensive test suite (90%+ coverage target)

**Success Criteria:**
- All 5 rules detect violations accurately (95%+ precision)
- Self-scan identifies 150-200+ violations in analyzer codebase
- SARIF output validates with GitHub Code Scanning
- External codebases successfully analyzed (3+ projects)
- Zero false positives on reference implementations

---

## Table of Contents

1. [Architecture Design](#1-architecture-design)
2. [Implementation Breakdown](#2-implementation-breakdown)
3. [Unified Quality Gate](#3-unified-quality-gate)
4. [Testing Strategy](#4-testing-strategy)
5. [Risk Assessment](#5-risk-assessment)
6. [Resource Allocation](#6-resource-allocation)
7. [Day-by-Day Schedule](#7-day-by-day-schedule)
8. [Copy-Paste Commands](#8-copy-paste-commands)

---

## 1. Architecture Design

### 1.1 Module Structure

```
analyzer/
├── clarity_linter/
│   ├── __init__.py                  # Module exports
│   ├── base.py                      # Base detector class
│   ├── detectors/
│   │   ├── __init__.py
│   │   ├── clarity001_thin_helper.py
│   │   ├── clarity002_single_use.py
│   │   ├── clarity011_mega_function.py
│   │   ├── clarity012_god_object.py
│   │   └── clarity021_passthrough.py
│   ├── ast_utils.py                 # AST traversal utilities
│   ├── sarif_exporter.py            # SARIF 2.1.0 output
│   └── config_loader.py             # Load clarity_linter.yaml
├── quality_gates/
│   └── unified_quality_gate.py      # Orchestrator (Week 1)
└── tests/
    └── clarity_linter/
        ├── test_clarity001.py
        ├── test_clarity002.py
        ├── test_clarity011.py
        ├── test_clarity012.py
        └── test_clarity021.py
```

### 1.2 Integration Points

**With Existing Analyzer:**
- Uses existing `ast.parse()` infrastructure from core.py
- Leverages `ConnascenceViolation` dataclass for consistency
- Integrates with existing policy loader for thresholds
- Shares SARIF export utilities with connascence analyzers

**With Quality Gate:**
- `unified_quality_gate.py` calls `ClarityLinter.analyze_project()`
- Results merged into unified scoring algorithm
- SARIF results combined for GitHub Code Scanning upload

**With GitHub Actions:**
- `.github/workflows/self-analysis.yml` invokes unified gate
- Separate job for Clarity Linter-specific metrics
- SARIF upload to Security tab

### 1.3 SARIF Output Format

```json
{
  "$schema": "https://json.schemastore.org/sarif-2.1.0",
  "version": "2.1.0",
  "runs": [
    {
      "tool": {
        "driver": {
          "name": "Clarity Linter",
          "version": "1.0.0",
          "informationUri": "https://github.com/connascence/analyzer",
          "rules": [
            {
              "id": "CLARITY001",
              "name": "ThinHelperFunction",
              "shortDescription": {
                "text": "Functions <20 LOC that add no semantic value"
              },
              "fullDescription": {
                "text": "Detects thin helper functions with <20 LOC called from single location..."
              },
              "help": {
                "text": "Inline the function directly into the caller to reduce indirection..."
              },
              "properties": {
                "precision": "high",
                "security-severity": "3.0",
                "tags": ["readability", "maintainability"]
              }
            }
          ]
        }
      },
      "results": [
        {
          "ruleId": "CLARITY001",
          "level": "warning",
          "message": {
            "text": "Thin helper function '_add_basic_arguments' (14 LOC) called from single location"
          },
          "locations": [
            {
              "physicalLocation": {
                "artifactLocation": {
                  "uri": "analyzer/core.py"
                },
                "region": {
                  "startLine": 56,
                  "endLine": 69,
                  "startColumn": 1,
                  "endColumn": 15
                }
              }
            }
          ],
          "fixes": [
            {
              "description": {
                "text": "Inline function into 'create_parser()'"
              }
            }
          ]
        }
      ]
    }
  ]
}
```

### 1.4 Configuration System

**clarity_linter.yaml (existing):**
- Rule enable/disable flags
- Threshold overrides (max_function_length, etc.)
- Language-specific settings
- Exclusion patterns

**Loading in Python:**
```python
import yaml
from pathlib import Path

class ConfigLoader:
    @staticmethod
    def load_config(config_path: Path = None) -> dict:
        if config_path is None:
            config_path = Path.cwd() / "clarity_linter.yaml"

        with open(config_path, 'r') as f:
            return yaml.safe_load(f)

    @staticmethod
    def get_rule_threshold(config: dict, rule_id: str) -> int:
        rule = config['rules'].get(rule_id, {})
        return rule.get('threshold', 0)
```

### 1.5 Rule Registration Mechanism

```python
# analyzer/clarity_linter/base.py

from abc import ABC, abstractmethod
from typing import List, Dict
import ast

class ClarityRuleBase(ABC):
    """Base class for all Clarity Linter rules."""

    rule_id: str
    rule_name: str
    severity: str
    category: str

    def __init__(self, config: dict):
        self.config = config
        self.threshold = config['rules'][self.rule_id]['threshold']
        self.violations = []

    @abstractmethod
    def detect_violations(self, tree: ast.AST, file_path: str) -> List[dict]:
        """Detect violations in AST tree."""
        pass

    def format_violation(self, node: ast.AST, message: str, file_path: str) -> dict:
        """Format violation for SARIF output."""
        return {
            'rule_id': self.rule_id,
            'severity': self.severity,
            'message': message,
            'file_path': file_path,
            'line': node.lineno,
            'column': node.col_offset,
            'end_line': getattr(node, 'end_lineno', node.lineno),
            'end_column': getattr(node, 'end_col_offset', node.col_offset)
        }

# Registry of all rules
CLARITY_RULES = {}

def register_rule(rule_class):
    """Decorator to register a rule."""
    CLARITY_RULES[rule_class.rule_id] = rule_class
    return rule_class
```

---

## 2. Implementation Breakdown

### 2.1 CLARITY001: Thin Helper Detection

**Rule Definition:**
- Functions <20 LOC that add no semantic value
- Single caller OR <10 LOC with multiple callers
- No abstraction layer, just grouping operations

**Detection Algorithm Pseudocode:**
```
For each function definition in AST:
    1. Count lines of code (exclude comments, blank lines)
    2. Find all callers using AST traversal
    3. If LOC < 20 AND (callers == 1 OR (LOC < 10 AND callers > 1)):
        4. Analyze if function provides abstraction:
            - Does it encapsulate complex logic?
            - Does it provide meaningful naming?
            - Does it enable reuse?
        5. If no abstraction benefit:
            Flag as CLARITY001 violation
```

**Python Implementation:**
```python
# analyzer/clarity_linter/detectors/clarity001_thin_helper.py

import ast
from ..base import ClarityRuleBase, register_rule
from ..ast_utils import count_loc, find_callers

@register_rule
class ThinHelperDetector(ClarityRuleBase):
    rule_id = "CLARITY001"
    rule_name = "Thin Helper Function"
    severity = "medium"
    category = "readability"

    def detect_violations(self, tree: ast.AST, file_path: str) -> List[dict]:
        violations = []

        # Build call graph
        call_graph = self._build_call_graph(tree)

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Count LOC (exclude comments, docstrings)
                loc = count_loc(node, exclude_docstring=True)

                # Find callers
                callers = call_graph.get(node.name, [])
                caller_count = len(callers)

                # Check thin helper criteria
                is_thin = False
                if loc < self.threshold and caller_count == 1:
                    is_thin = True
                elif loc < 10 and caller_count > 1:
                    is_thin = True

                if is_thin and not self._provides_abstraction(node):
                    message = f"Thin helper function '{node.name}' ({loc} LOC) called from {caller_count} location(s)"
                    violations.append(
                        self.format_violation(node, message, file_path)
                    )

        return violations

    def _build_call_graph(self, tree: ast.AST) -> Dict[str, List[str]]:
        """Build call graph: function_name -> [caller_names]"""
        call_graph = {}

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                current_func = node.name

                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        if isinstance(child.func, ast.Name):
                            called_func = child.func.id
                            if called_func not in call_graph:
                                call_graph[called_func] = []
                            call_graph[called_func].append(current_func)

        return call_graph

    def _provides_abstraction(self, node: ast.FunctionDef) -> bool:
        """Check if function provides meaningful abstraction."""
        # Heuristic: If function just calls another function with same args, no abstraction
        if len(node.body) == 1:
            stmt = node.body[0]
            if isinstance(stmt, ast.Return) and isinstance(stmt.value, ast.Call):
                # Check if args match function parameters
                if self._is_passthrough_call(node, stmt.value):
                    return False

        # If function contains complex logic (nested ifs, loops), it provides abstraction
        has_control_flow = any(
            isinstance(child, (ast.If, ast.For, ast.While, ast.Try))
            for child in ast.walk(node)
        )

        return has_control_flow

    def _is_passthrough_call(self, func_def: ast.FunctionDef, call: ast.Call) -> bool:
        """Check if call is just passing through function parameters."""
        func_params = {arg.arg for arg in func_def.args.args}
        call_args = {
            arg.id for arg in call.args
            if isinstance(arg, ast.Name)
        }

        # If all call args are function params, it's likely a pass-through
        return call_args.issubset(func_params)
```

**AST Patterns:**
- `ast.FunctionDef` nodes for function definitions
- `ast.Call` nodes for function invocations
- `ast.Return` nodes for return statements
- Line number tracking with `node.lineno`, `node.end_lineno`

**Severity Thresholds:**
- <20 LOC + single caller = MEDIUM
- <10 LOC + multiple callers = MEDIUM
- <5 LOC + single caller = HIGH (extreme case)

**Test Cases:**

**Positive (should detect):**
```python
# Test case 1: Single-caller thin helper
def _add_basic_arguments(parser):  # 14 LOC, 1 caller
    parser.add_argument("path")
    parser.add_argument("--policy")
    # ... 12 more lines

def create_parser():
    parser = argparse.ArgumentParser()
    _add_basic_arguments(parser)  # ONLY caller
    return parser
```

**Negative (should NOT detect):**
```python
# Test case 2: Helper with complex logic (abstraction)
def validate_user_input(data):  # <20 LOC but provides abstraction
    if not data:
        raise ValueError("Empty data")

    if 'email' in data:
        if not re.match(EMAIL_REGEX, data['email']):
            raise ValueError("Invalid email")

    return sanitize(data)
```

**Fix Suggestions:**
- "Inline function into caller to reduce indirection"
- "If called from multiple locations, consider if abstraction is needed"
- "Extract to method only if it encapsulates complex logic"

**Estimated Effort:** 16 hours
- Detection algorithm: 6 hours
- AST utilities: 4 hours
- Test cases: 4 hours
- Documentation: 2 hours

---

### 2.2 CLARITY002: Single-Use Function Detection

**Rule Definition:**
- Function called from exactly ONE location
- Function has <20 LOC
- No reuse potential identified

**Detection Algorithm Pseudocode:**
```
Build call graph from AST
For each function definition:
    1. Count callers in call graph
    2. If callers == 1:
        3. Count LOC in function
        4. If LOC < threshold (20):
            5. Check for reuse indicators:
                - Is function exported (public API)?
                - Does it test multiple implementations?
                - Does it abstract complex logic?
            6. If no reuse indicators:
                Flag as CLARITY002 violation
```

**Python Implementation:**
```python
# analyzer/clarity_linter/detectors/clarity002_single_use.py

import ast
from ..base import ClarityRuleBase, register_rule
from ..ast_utils import count_loc, find_callers

@register_rule
class SingleUseFunctionDetector(ClarityRuleBase):
    rule_id = "CLARITY002"
    rule_name = "Single-Use Function"
    severity = "high"
    category = "design"

    def detect_violations(self, tree: ast.AST, file_path: str) -> List[dict]:
        violations = []

        # Build call graph
        call_graph = self._build_call_graph(tree)

        # Get module-level exports (functions in __all__ or not prefixed with _)
        exports = self._get_exports(tree)

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_name = node.name

                # Skip if exported (public API)
                if func_name in exports:
                    continue

                # Count callers
                callers = call_graph.get(func_name, [])

                if len(callers) == 1:
                    # Count LOC
                    loc = count_loc(node, exclude_docstring=True)

                    if loc < self.threshold:
                        # Check for reuse indicators
                        if not self._has_reuse_potential(node):
                            message = f"Single-use function '{func_name}' ({loc} LOC) called only from '{callers[0]}'"
                            violations.append(
                                self.format_violation(node, message, file_path)
                            )

        return violations

    def _get_exports(self, tree: ast.AST) -> set:
        """Get module-level exported functions."""
        exports = set()

        # Check for __all__
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == '__all__':
                        if isinstance(node.value, ast.List):
                            exports.update(
                                elt.s for elt in node.value.elts
                                if isinstance(elt, ast.Str)
                            )

        # If no __all__, consider non-private functions as exports
        if not exports:
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if not node.name.startswith('_'):
                        exports.add(node.name)

        return exports

    def _has_reuse_potential(self, node: ast.FunctionDef) -> bool:
        """Check if function has reuse potential despite single caller."""
        # If function has complex logic, it may be worth keeping separate
        complexity = self._calculate_complexity(node)
        if complexity > 5:
            return True

        # If function name suggests abstraction (e.g., validate_, parse_, format_)
        abstraction_prefixes = ('validate', 'parse', 'format', 'sanitize', 'normalize')
        if any(node.name.startswith(prefix) for prefix in abstraction_prefixes):
            return True

        return False

    def _calculate_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity."""
        complexity = 1  # Base complexity

        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1

        return complexity

    def _build_call_graph(self, tree: ast.AST) -> Dict[str, List[str]]:
        """Build call graph: function_name -> [caller_names]"""
        # Same as CLARITY001
        pass
```

**AST Patterns:**
- `ast.FunctionDef` for function definitions
- `ast.Assign` for `__all__` detection
- `ast.Call` for function invocations
- `ast.If`, `ast.For`, `ast.While` for complexity calculation

**Severity Thresholds:**
- <20 LOC + single caller = HIGH
- <10 LOC + single caller = CRITICAL (should always inline)

**Test Cases:**

**Positive (should detect):**
```python
# Test case 1: Simple single-use helper
def _format_output(data):  # 8 LOC, 1 caller
    return json.dumps(data, indent=2)

def main():
    result = process_data()
    print(_format_output(result))  # ONLY caller
```

**Negative (should NOT detect):**
```python
# Test case 2: Exported function (public API)
def format_analysis_result(data):  # Single internal caller but exported
    return json.dumps(data, indent=2)

__all__ = ['format_analysis_result']

def analyze_file(path):
    result = run_analysis(path)
    return format_analysis_result(result)
```

**Fix Suggestions:**
- "Inline function into caller '{caller_name}'"
- "Consider if abstraction is needed before extracting to function"
- "If function has reuse potential, consider making it public"

**Estimated Effort:** 14 hours
- Detection algorithm: 5 hours
- Export detection logic: 3 hours
- Test cases: 4 hours
- Documentation: 2 hours

---

### 2.3 CLARITY011: Mega-Function Detection

**Rule Definition:**
- Functions exceeding 100 lines (hard limit)
- CRITICAL violation requiring immediate split
- Typically violates Single Responsibility Principle

**Detection Algorithm Pseudocode:**
```
For each function definition in AST:
    1. Count lines of code (exclude comments, docstrings, blank lines)
    2. If LOC > hard_limit (100):
        3. Analyze function structure:
            - Count distinct logical sections
            - Identify natural split points (comments, blank line clusters)
            - Detect multiple concerns (validation, processing, formatting)
        4. Generate split suggestions based on structure
        5. Flag as CLARITY011 violation with detailed breakdown
```

**Python Implementation:**
```python
# analyzer/clarity_linter/detectors/clarity011_mega_function.py

import ast
from typing import List, Dict, Tuple
from ..base import ClarityRuleBase, register_rule
from ..ast_utils import count_loc, find_logical_sections

@register_rule
class MegaFunctionDetector(ClarityRuleBase):
    rule_id = "CLARITY011"
    rule_name = "Overlong Function (Hard Limit)"
    severity = "critical"
    category = "complexity"

    HARD_LIMIT = 100  # NASA JPL Rule 4: max 60, we use 100 for tolerance

    def detect_violations(self, tree: ast.AST, file_path: str) -> List[dict]:
        violations = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Count LOC excluding comments, docstrings, blank lines
                loc = count_loc(node, exclude_docstring=True)

                if loc > self.threshold:
                    # Analyze function structure for split recommendations
                    structure = self._analyze_structure(node)

                    message = self._format_message(node, loc, structure)

                    violation = self.format_violation(node, message, file_path)
                    violation['metadata'] = {
                        'actual_loc': loc,
                        'threshold': self.threshold,
                        'excess_loc': loc - self.threshold,
                        'suggested_splits': structure['split_suggestions'],
                        'logical_sections': structure['section_count']
                    }

                    violations.append(violation)

        return violations

    def _analyze_structure(self, node: ast.FunctionDef) -> Dict:
        """Analyze function structure to suggest natural split points."""
        sections = []
        current_section = []

        # Group statements by logical sections (separated by blank lines or comments)
        for i, stmt in enumerate(node.body):
            current_section.append(stmt)

            # Check if next statement is separated by significant gap or is comment
            if i < len(node.body) - 1:
                next_stmt = node.body[i + 1]
                line_gap = next_stmt.lineno - stmt.end_lineno

                if line_gap > 1:  # Blank line(s) suggest logical boundary
                    sections.append(current_section)
                    current_section = []

        if current_section:
            sections.append(current_section)

        # Generate split suggestions
        split_suggestions = []
        for i, section in enumerate(sections):
            section_type = self._classify_section(section)
            split_suggestions.append({
                'section_number': i + 1,
                'type': section_type,
                'start_line': section[0].lineno,
                'end_line': section[-1].end_lineno,
                'loc': sum(1 for stmt in section for _ in range(stmt.lineno, stmt.end_lineno + 1))
            })

        return {
            'section_count': len(sections),
            'split_suggestions': split_suggestions
        }

    def _classify_section(self, section: List[ast.stmt]) -> str:
        """Classify logical section type."""
        # Heuristic classification based on AST patterns
        has_validation = any(
            isinstance(stmt, (ast.Assert, ast.Raise))
            for stmt in section
        )
        has_loops = any(
            isinstance(stmt, (ast.For, ast.While))
            for stmt in section
        )
        has_conditionals = any(
            isinstance(stmt, ast.If)
            for stmt in section
        )
        has_return = any(
            isinstance(stmt, ast.Return)
            for stmt in section
        )

        if has_validation:
            return "validation"
        elif has_loops:
            return "processing"
        elif has_conditionals and has_return:
            return "decision_logic"
        elif has_return:
            return "result_formatting"
        else:
            return "setup"

    def _format_message(self, node: ast.FunctionDef, loc: int, structure: Dict) -> str:
        """Format detailed violation message."""
        section_summary = ", ".join(
            f"{s['type']} ({s['loc']} LOC)"
            for s in structure['split_suggestions']
        )

        return (
            f"Mega-function '{node.name}' ({loc} LOC) exceeds hard limit ({self.threshold}). "
            f"Function has {structure['section_count']} logical sections: {section_summary}. "
            f"Consider splitting into focused functions."
        )
```

**AST Patterns:**
- `ast.FunctionDef` for function definitions
- `ast.Assert`, `ast.Raise` for validation sections
- `ast.For`, `ast.While` for processing sections
- `ast.If` for decision logic
- `ast.Return` for result formatting
- Line number gaps for logical boundaries

**Severity Thresholds:**
- 100-150 LOC = CRITICAL (must split)
- 150-200 LOC = BLOCKER (immediate action required)
- >200 LOC = EMERGENCY (architectural issue)

**Test Cases:**

**Positive (should detect):**
```python
# Test case 1: 150-line mega-function
def _run_analysis_phases(self, tree, path, policy):
    """Run all analysis phases."""  # 150 LOC
    results = {}

    # Phase 1: God Object Detection (20 lines)
    god_objects = []
    for node in ast.walk(tree):
        # ... 20 lines

    # Phase 2: Parameter Bomb Detection (25 lines)
    parameter_bombs = []
    # ... 25 lines

    # Phase 3: Magic Literal Detection (30 lines)
    # ... 30 lines

    # Phase 4-6: More phases (75 lines)
    # ... 75 lines

    return results
```

**Negative (should NOT detect):**
```python
# Test case 2: 95-line function (just under threshold)
def analyze_file(self, path):
    """Analyze single file."""  # 95 LOC
    # ... 95 lines of focused analysis logic
    pass
```

**Fix Suggestions:**
```
Split into {section_count} focused functions:
1. {func_name}_validation() - Lines {start}-{end} ({loc} LOC)
2. {func_name}_processing() - Lines {start}-{end} ({loc} LOC)
3. {func_name}_formatting() - Lines {start}-{end} ({loc} LOC)

Coordinator function:
def {func_name}(...):
    validated = {func_name}_validation(...)
    processed = {func_name}_processing(validated)
    return {func_name}_formatting(processed)
```

**Estimated Effort:** 18 hours
- Detection algorithm: 6 hours
- Structure analysis: 6 hours
- Test cases: 4 hours
- Documentation: 2 hours

---

### 2.4 CLARITY012: God Object Detection

**Rule Definition:**
- Classes with >15 methods OR >500 LOC
- Low cohesion (methods don't relate to single responsibility)
- Typically violates Single Responsibility Principle

**Detection Algorithm Pseudocode:**
```
For each class definition in AST:
    1. Count total methods (include private, static)
    2. Count total LOC (exclude comments, docstrings)
    3. If methods > 15 OR loc > 500:
        4. Calculate cohesion metrics:
            - Method call graph (which methods call which)
            - Data usage patterns (which methods use which attributes)
            - Identify method clusters (groups of related methods)
        5. If cohesion < threshold:
            Flag as CLARITY012 violation with cluster breakdown
```

**Python Implementation:**
```python
# analyzer/clarity_linter/detectors/clarity012_god_object.py

import ast
from collections import defaultdict
from typing import List, Dict, Set
from ..base import ClarityRuleBase, register_rule
from ..ast_utils import count_loc

@register_rule
class GodObjectDetector(ClarityRuleBase):
    rule_id = "CLARITY012"
    rule_name = "God Object/Low Cohesion"
    severity = "high"
    category = "design"

    METHOD_THRESHOLD = 15
    LOC_THRESHOLD = 500
    COHESION_THRESHOLD = 0.5  # 50% cohesion minimum

    def detect_violations(self, tree: ast.AST, file_path: str) -> List[dict]:
        violations = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Count methods
                methods = [
                    n for n in node.body
                    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                ]
                method_count = len(methods)

                # Count LOC
                loc = count_loc(node, exclude_docstring=True)

                # Check thresholds
                if method_count > self.METHOD_THRESHOLD or loc > self.LOC_THRESHOLD:
                    # Calculate cohesion
                    cohesion_data = self._calculate_cohesion(node, methods)

                    if cohesion_data['cohesion_score'] < self.COHESION_THRESHOLD:
                        message = self._format_message(node, method_count, loc, cohesion_data)

                        violation = self.format_violation(node, message, file_path)
                        violation['metadata'] = {
                            'method_count': method_count,
                            'loc': loc,
                            'cohesion_score': cohesion_data['cohesion_score'],
                            'method_clusters': cohesion_data['clusters']
                        }

                        violations.append(violation)

        return violations

    def _calculate_cohesion(self, class_node: ast.ClassDef, methods: List[ast.FunctionDef]) -> Dict:
        """Calculate LCOM (Lack of Cohesion of Methods) metric."""
        # Build method call graph
        method_calls = defaultdict(set)
        for method in methods:
            caller_name = method.name
            for node in ast.walk(method):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
                        if node.func.value.id == 'self':
                            callee_name = node.func.attr
                            method_calls[caller_name].add(callee_name)

        # Build attribute usage graph
        attribute_usage = defaultdict(set)
        class_attributes = self._get_class_attributes(class_node)

        for method in methods:
            method_name = method.name
            for node in ast.walk(method):
                if isinstance(node, ast.Attribute):
                    if isinstance(node.value, ast.Name) and node.value.id == 'self':
                        if node.attr in class_attributes:
                            attribute_usage[method_name].add(node.attr)

        # Calculate cohesion score (simplified LCOM)
        total_method_pairs = len(methods) * (len(methods) - 1) / 2
        if total_method_pairs == 0:
            return {'cohesion_score': 1.0, 'clusters': []}

        connected_pairs = 0
        for method1 in methods:
            for method2 in methods:
                if method1.name >= method2.name:
                    continue

                # Methods are connected if they call each other or share attributes
                if (method2.name in method_calls[method1.name] or
                    method1.name in method_calls[method2.name] or
                    bool(attribute_usage[method1.name] & attribute_usage[method2.name])):
                    connected_pairs += 1

        cohesion_score = connected_pairs / total_method_pairs

        # Identify method clusters
        clusters = self._identify_clusters(methods, method_calls, attribute_usage)

        return {
            'cohesion_score': cohesion_score,
            'clusters': clusters
        }

    def _get_class_attributes(self, class_node: ast.ClassDef) -> Set[str]:
        """Get all class attributes defined in __init__."""
        attributes = set()

        for node in class_node.body:
            if isinstance(node, ast.FunctionDef) and node.name == '__init__':
                for child in ast.walk(node):
                    if isinstance(child, ast.Assign):
                        for target in child.targets:
                            if isinstance(target, ast.Attribute):
                                if isinstance(target.value, ast.Name) and target.value.id == 'self':
                                    attributes.add(target.attr)

        return attributes

    def _identify_clusters(self, methods: List[ast.FunctionDef],
                          method_calls: Dict[str, Set[str]],
                          attribute_usage: Dict[str, Set[str]]) -> List[Dict]:
        """Identify method clusters using community detection."""
        # Simple clustering: group methods that share attributes or call each other
        clusters = []
        processed = set()

        for method in methods:
            if method.name in processed:
                continue

            cluster = {method.name}
            cluster_attrs = attribute_usage[method.name].copy()

            # Find related methods
            for other_method in methods:
                if other_method.name in processed or other_method.name == method.name:
                    continue

                # Check if methods share attributes or call each other
                shared_attrs = cluster_attrs & attribute_usage[other_method.name]
                calls_related = (
                    other_method.name in method_calls[method.name] or
                    method.name in method_calls[other_method.name]
                )

                if shared_attrs or calls_related:
                    cluster.add(other_method.name)
                    cluster_attrs.update(attribute_usage[other_method.name])
                    processed.add(other_method.name)

            processed.add(method.name)

            clusters.append({
                'methods': list(cluster),
                'shared_attributes': list(cluster_attrs),
                'method_count': len(cluster)
            })

        return clusters

    def _format_message(self, node: ast.ClassDef, method_count: int,
                       loc: int, cohesion_data: Dict) -> str:
        """Format detailed violation message."""
        cluster_summary = ", ".join(
            f"Cluster {i+1}: {c['method_count']} methods"
            for i, c in enumerate(cohesion_data['clusters'])
        )

        return (
            f"God object '{node.name}' with {method_count} methods ({loc} LOC) "
            f"has low cohesion (score: {cohesion_data['cohesion_score']:.2f}). "
            f"Detected {len(cohesion_data['clusters'])} method clusters: {cluster_summary}. "
            f"Consider splitting into focused classes."
        )
```

**AST Patterns:**
- `ast.ClassDef` for class definitions
- `ast.FunctionDef`, `ast.AsyncFunctionDef` for method definitions
- `ast.Call` with `ast.Attribute` for method calls (`self.method()`)
- `ast.Assign` with `ast.Attribute` for attribute access (`self.attr`)
- `ast.Attribute` nodes for attribute usage

**Severity Thresholds:**
- 15-20 methods = HIGH
- >20 methods = CRITICAL
- >500 LOC = HIGH
- >800 LOC = CRITICAL
- Cohesion <0.5 = HIGH
- Cohesion <0.3 = CRITICAL

**Test Cases:**

**Positive (should detect):**
```python
# Test case 1: God object with 18 methods, low cohesion
class UnifiedConnascenceAnalyzer:  # 18 methods, 800 LOC
    def analyze_file(self): pass
    def analyze_directory(self): pass
    def _run_analysis_phases(self): pass  # 150 LOC
    def _detect_god_objects(self): pass
    def _detect_parameter_bombs(self): pass
    def _detect_magic_literals(self): pass
    def _analyze_complexity(self): pass
    def _analyze_nesting(self): pass
    def _format_results(self): pass
    def _aggregate_violations(self): pass
    def _calculate_scores(self): pass
    def _generate_report(self): pass
    def _export_json(self): pass
    def _export_sarif(self): pass
    def _load_policy(self): pass
    def _validate_policy(self): pass
    def _log_metrics(self): pass
    def _cleanup_resources(self): pass
```

**Negative (should NOT detect):**
```python
# Test case 2: Cohesive class with 18 methods (high cohesion)
class DataProcessor:  # 18 methods but all related to data processing
    def __init__(self):
        self.data = []

    def add_data(self, item): pass
    def remove_data(self, item): pass
    def update_data(self, index, item): pass
    # ... all methods work with self.data
```

**Fix Suggestions:**
```
Split '{class_name}' into {cluster_count} focused classes:

1. {ClassName}Core ({methods} methods)
   - Responsibility: {primary_responsibility}
   - Methods: {method_list}

2. {ClassName}Formatter ({methods} methods)
   - Responsibility: {formatting_responsibility}
   - Methods: {method_list}

3. {ClassName}Exporter ({methods} methods)
   - Responsibility: {export_responsibility}
   - Methods: {method_list}
```

**Estimated Effort:** 22 hours
- Detection algorithm: 8 hours
- Cohesion calculation: 6 hours
- Cluster identification: 4 hours
- Test cases: 4 hours

---

### 2.5 CLARITY021: Pass-Through Function Detection

**Rule Definition:**
- Functions that just call another function with same/similar parameters
- No transformation, validation, or additional logic
- Pure delegation without value addition

**Detection Algorithm Pseudocode:**
```
For each function definition in AST:
    1. Check if function body has single statement
    2. If statement is return of a function call:
        3. Compare function parameters with call arguments
        4. If >80% of parameters are passed directly:
            5. Check for value addition:
                - Parameter transformation
                - Additional error handling
                - Logging or metrics
                - Type conversion
            6. If no value addition:
                Flag as CLARITY021 violation
```

**Python Implementation:**
```python
# analyzer/clarity_linter/detectors/clarity021_passthrough.py

import ast
from typing import List, Set
from ..base import ClarityRuleBase, register_rule

@register_rule
class PassThroughDetector(ClarityRuleBase):
    rule_id = "CLARITY021"
    rule_name = "Pass-Through Wrapper"
    severity = "high"
    category = "design"

    PASSTHROUGH_THRESHOLD = 0.8  # 80% of params passed through

    def detect_violations(self, tree: ast.AST, file_path: str) -> List[dict]:
        violations = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check if function is a pass-through wrapper
                if self._is_passthrough(node):
                    target_func = self._get_target_function(node)

                    message = (
                        f"Pass-through wrapper '{node.name}' calls '{target_func}' "
                        f"without adding value. Consider using delegation or direct calls."
                    )

                    violation = self.format_violation(node, message, file_path)
                    violation['metadata'] = {
                        'wrapper_function': node.name,
                        'target_function': target_func,
                        'parameter_count': len(node.args.args),
                        'adds_value': False
                    }

                    violations.append(violation)

        return violations

    def _is_passthrough(self, node: ast.FunctionDef) -> bool:
        """Check if function is a pass-through wrapper."""
        # Must have at least one parameter (otherwise not a wrapper)
        if not node.args.args:
            return False

        # Check if function body is single return statement
        if len(node.body) == 1:
            stmt = node.body[0]

            if isinstance(stmt, ast.Return) and isinstance(stmt.value, ast.Call):
                # Compare function parameters with call arguments
                func_params = {arg.arg for arg in node.args.args}
                call_args = self._get_call_arg_names(stmt.value)

                # Calculate pass-through ratio
                passthrough_count = len(func_params & call_args)
                passthrough_ratio = passthrough_count / len(func_params) if func_params else 0

                if passthrough_ratio >= self.PASSTHROUGH_THRESHOLD:
                    # Check if any value is added
                    if not self._adds_value(node, stmt.value):
                        return True

        # Check for delegation pattern (multiple branches but all pass-through)
        if self._is_delegation_wrapper(node):
            return True

        return False

    def _get_call_arg_names(self, call: ast.Call) -> Set[str]:
        """Extract argument names from function call."""
        arg_names = set()

        for arg in call.args:
            if isinstance(arg, ast.Name):
                arg_names.add(arg.id)

        for keyword in call.keywords:
            if isinstance(keyword.value, ast.Name):
                arg_names.add(keyword.value.id)

        return arg_names

    def _adds_value(self, func_def: ast.FunctionDef, call: ast.Call) -> bool:
        """Check if wrapper adds value beyond delegation."""
        # Check for parameter transformation
        for arg in call.args:
            if not isinstance(arg, ast.Name):
                # Argument is transformed (e.g., validation, conversion)
                return True

        # Check for additional keyword arguments not in function params
        func_params = {arg.arg for arg in func_def.args.args}
        for keyword in call.keywords:
            if keyword.arg not in func_params:
                # Additional parameter provided
                return True

        # Check function docstring for documented purpose
        docstring = ast.get_docstring(func_def)
        if docstring and len(docstring) > 50:
            # Substantial documentation suggests intentional abstraction
            return True

        return False

    def _is_delegation_wrapper(self, node: ast.FunctionDef) -> bool:
        """Check if function is a delegation wrapper (multiple branches, all pass-through)."""
        # Pattern: if condition: return func1(...), else: return func2(...)
        if len(node.body) == 1 and isinstance(node.body[0], ast.If):
            if_node = node.body[0]

            # Check if both branches return function calls
            then_returns = self._get_return_calls(if_node.body)
            else_returns = self._get_return_calls(if_node.orelse)

            if then_returns and else_returns:
                # Check if all returns are pass-through
                func_params = {arg.arg for arg in node.args.args}

                all_passthrough = True
                for call in then_returns + else_returns:
                    call_args = self._get_call_arg_names(call)
                    passthrough_ratio = len(func_params & call_args) / len(func_params)

                    if passthrough_ratio < self.PASSTHROUGH_THRESHOLD:
                        all_passthrough = False
                        break

                return all_passthrough

        return False

    def _get_return_calls(self, stmts: List[ast.stmt]) -> List[ast.Call]:
        """Extract return calls from statement list."""
        calls = []
        for stmt in stmts:
            if isinstance(stmt, ast.Return) and isinstance(stmt.value, ast.Call):
                calls.append(stmt.value)
        return calls

    def _get_target_function(self, node: ast.FunctionDef) -> str:
        """Get name of target function being wrapped."""
        if len(node.body) == 1:
            stmt = node.body[0]
            if isinstance(stmt, ast.Return) and isinstance(stmt.value, ast.Call):
                if isinstance(stmt.value.func, ast.Name):
                    return stmt.value.func.id
                elif isinstance(stmt.value.func, ast.Attribute):
                    return stmt.value.func.attr

        return "unknown"
```

**AST Patterns:**
- `ast.FunctionDef` for function definitions
- `ast.Return` with `ast.Call` for return statements
- `ast.Name` nodes in call arguments
- `ast.If` nodes for delegation patterns
- `ast.Attribute` for method calls

**Severity Thresholds:**
- 80%+ parameters passed through = HIGH
- 100% parameters passed through + no docstring = CRITICAL

**Test Cases:**

**Positive (should detect):**
```python
# Test case 1: Pure pass-through wrapper
def analyze_path(self, path: str, policy: str = "default", **kwargs):
    """Wrapper function."""
    if self.analysis_mode == "unified":
        return self.unified_analyzer.analyze_path(path, policy, **kwargs)
    else:
        return self.fallback_analyzer.analyze_path(path, policy, **kwargs)
```

**Negative (should NOT detect):**
```python
# Test case 2: Wrapper with value addition
def analyze_path(self, path: str, policy: str = "default", **kwargs):
    """Analyze path with validation and logging."""
    # Value addition: validation
    if not Path(path).exists():
        raise ValueError(f"Path does not exist: {path}")

    # Value addition: logging
    logger.info(f"Analyzing {path} with policy {policy}")

    # Delegation (OK because value was added)
    return self.unified_analyzer.analyze_path(path, policy, **kwargs)
```

**Fix Suggestions:**
```
Remove wrapper '{wrapper_name}' and use delegation:

Option 1: Direct property delegation
class {ClassName}:
    analyze_path = property(lambda self: self._analyzer.analyze_path)

Option 2: Use composition
class {ClassName}:
    def __init__(self):
        self._analyzer = {AnalyzerClass}()

    # No wrapper needed - client calls self._analyzer.analyze_path directly
```

**Estimated Effort:** 16 hours
- Detection algorithm: 6 hours
- Delegation pattern detection: 4 hours
- Test cases: 4 hours
- Documentation: 2 hours

---

## 3. Unified Quality Gate

### 3.1 Integration with Existing Orchestrator

**Modify `analyzer/quality_gates/unified_quality_gate.py`:**

```python
# Add Clarity Linter integration
from ..clarity_linter import ClarityLinter

class UnifiedQualityGate:
    def __init__(self, config_path: Path = None):
        self.config = self._load_config(config_path)

        # Initialize analyzers
        self.clarity_linter = ClarityLinter(config_path)
        self.connascence_analyzer = ConnascenceAnalyzer()  # Existing
        self.nasa_checker = NASAStandardsChecker()  # Existing

    def analyze_project(self, project_path: Path) -> AnalysisResult:
        """Run all analyzers and combine results."""
        results = AnalysisResult(project_path=str(project_path))

        # Run Clarity Linter (NEW)
        clarity_results = self.clarity_linter.analyze_project(project_path)
        results.clarity_violations = clarity_results.violations
        results.clarity_score = clarity_results.score

        # Run Connascence Analyzer (existing)
        connascence_results = self.connascence_analyzer.analyze_workspace(project_path)
        results.connascence_violations = connascence_results.violations
        results.connascence_score = connascence_results.score

        # Run NASA Standards Checker (existing)
        nasa_results = self.nasa_checker.check_compliance(project_path)
        results.nasa_violations = nasa_results.violations
        results.nasa_score = nasa_results.compliance_score

        # Calculate unified score
        results.overall_score = self._calculate_unified_score(results)

        return results

    def _calculate_unified_score(self, results: AnalysisResult) -> float:
        """
        Unified scoring algorithm (0-100 scale).

        Weights:
          - Clarity Linter: 40%
          - Connascence Analyzer: 30%
          - NASA Standards: 30%

        Penalties:
          - Critical: -10 points
          - High: -5 points
          - Medium: -2 points
          - Low: -1 point
        """
        # Start with perfect score
        score = 100.0

        # Apply Clarity penalties (40% weight)
        clarity_penalty = (
            results.count_by_severity('critical', 'clarity') * 10 +
            results.count_by_severity('high', 'clarity') * 5 +
            results.count_by_severity('medium', 'clarity') * 2 +
            results.count_by_severity('low', 'clarity') * 1
        )
        score -= clarity_penalty * 0.4

        # Apply Connascence penalties (30% weight)
        connascence_penalty = (
            results.count_by_severity('critical', 'connascence') * 10 +
            results.count_by_severity('high', 'connascence') * 5 +
            results.count_by_severity('medium', 'connascence') * 2 +
            results.count_by_severity('low', 'connascence') * 1
        )
        score -= connascence_penalty * 0.3

        # Apply NASA penalties (30% weight)
        nasa_penalty = (100 - results.nasa_score) * 0.3
        score -= nasa_penalty

        # Clamp to 0-100 range
        return max(0.0, min(100.0, score))
```

### 3.2 Scoring Algorithm Details

**Weighted Average:**
```
Overall = (Clarity * 0.4) + (Connascence * 0.3) + (NASA * 0.3)

Where:
  Clarity Score = 100 - (critical*10 + high*5 + medium*2 + low*1)
  Connascence Score = 100 - (critical*10 + high*5 + medium*2 + low*1)
  NASA Score = Compliance percentage (from checker)
```

**Example Calculation:**
```python
# Scenario: 5 critical, 10 high, 15 medium, 20 low violations
clarity_score = 100 - (5*10 + 10*5 + 15*2 + 20*1) = 100 - 150 = 0 (clamped)
connascence_score = 100 - (2*10 + 5*5 + 8*2 + 12*1) = 100 - 73 = 27
nasa_score = 85  # 85% compliance

overall = (0 * 0.4) + (27 * 0.3) + (85 * 0.3) = 0 + 8.1 + 25.5 = 33.6
```

### 3.3 CLI Interface

```bash
# Run unified quality gate
python -m analyzer.quality_gates.unified_quality_gate \
  /path/to/project \
  --config quality_gate.config.yaml \
  --fail-on high \
  --output-format sarif json markdown \
  --output-file results.sarif \
  --verbose

# Output formats:
#   sarif: GitHub Code Scanning format
#   json: Machine-readable results
#   markdown: Human-readable report
#   html: HTML report with charts

# Fail-on options:
#   critical: Fail only on critical violations
#   high: Fail on critical or high
#   medium: Fail on critical, high, or medium
#   any: Fail on any violation
```

### 3.4 Output Formats

**SARIF (GitHub Code Scanning):**
- Merged SARIF from all analyzers
- Separate tool driver for each analyzer
- Common schema for easy integration

**JSON (Machine-readable):**
```json
{
  "project_path": "/path/to/project",
  "timestamp": "2025-11-20T10:30:00Z",
  "overall_score": 67.5,
  "analyzers": {
    "clarity_linter": {
      "score": 55.0,
      "violations": 120,
      "by_severity": {"critical": 5, "high": 15, "medium": 30, "low": 70}
    },
    "connascence_analyzer": {
      "score": 72.0,
      "violations": 45
    },
    "nasa_standards": {
      "compliance_score": 78.5,
      "violations": 12
    }
  },
  "violations": [...]
}
```

**Markdown (Human-readable):**
```markdown
# Quality Gate Report

**Project:** /path/to/project
**Date:** 2025-11-20 10:30:00
**Overall Score:** 67.5/100

## Summary

| Analyzer | Score | Violations | Critical | High | Medium | Low |
|----------|-------|-----------|----------|------|--------|-----|
| Clarity Linter | 55.0 | 120 | 5 | 15 | 30 | 70 |
| Connascence | 72.0 | 45 | 2 | 8 | 15 | 20 |
| NASA Standards | 78.5 | 12 | 0 | 3 | 5 | 4 |

## Top Violations

### CLARITY011: Mega-Function
- `_run_analysis_phases()` in `analyzer/unified_analyzer.py` (150 LOC)
- Fix: Split into 6 focused functions

...
```

---

## 4. Testing Strategy

### 4.1 Unit Tests for Each Rule

**Test Structure:**
```
tests/clarity_linter/
├── test_clarity001_thin_helper.py
├── test_clarity002_single_use.py
├── test_clarity011_mega_function.py
├── test_clarity012_god_object.py
├── test_clarity021_passthrough.py
├── test_ast_utils.py
├── test_sarif_exporter.py
├── fixtures/
│   ├── sample_thin_helper.py
│   ├── sample_mega_function.py
│   ├── sample_god_object.py
│   └── sample_passthrough.py
└── conftest.py
```

**Test Case Template:**
```python
# tests/clarity_linter/test_clarity001_thin_helper.py

import pytest
import ast
from analyzer.clarity_linter.detectors.clarity001_thin_helper import ThinHelperDetector

class TestThinHelperDetector:
    @pytest.fixture
    def detector(self):
        config = {
            'rules': {
                'CLARITY001': {'threshold': 20}
            }
        }
        return ThinHelperDetector(config)

    def test_detects_thin_helper_single_caller(self, detector):
        """Test detection of thin helper with single caller."""
        code = '''
def _add_basic_arguments(parser):
    parser.add_argument("path")
    parser.add_argument("--policy")
    # 12 more lines...

def create_parser():
    parser = argparse.ArgumentParser()
    _add_basic_arguments(parser)
    return parser
'''
        tree = ast.parse(code)
        violations = detector.detect_violations(tree, "test.py")

        assert len(violations) == 1
        assert violations[0]['rule_id'] == 'CLARITY001'
        assert '_add_basic_arguments' in violations[0]['message']

    def test_does_not_detect_complex_helper(self, detector):
        """Test that complex helpers are not flagged."""
        code = '''
def validate_user_input(data):
    if not data:
        raise ValueError("Empty data")

    if 'email' in data:
        if not re.match(EMAIL_REGEX, data['email']):
            raise ValueError("Invalid email")

    return sanitize(data)
'''
        tree = ast.parse(code)
        violations = detector.detect_violations(tree, "test.py")

        assert len(violations) == 0

    def test_detects_multiple_thin_helpers(self, detector):
        """Test detection of multiple thin helpers in same file."""
        code = '''
def _helper1(x): return x + 1
def _helper2(y): return y * 2
def _helper3(z): return z - 1

def main():
    a = _helper1(5)
    b = _helper2(10)
    c = _helper3(15)
'''
        tree = ast.parse(code)
        violations = detector.detect_violations(tree, "test.py")

        assert len(violations) == 3
```

### 4.2 Integration Tests

**Test unified quality gate with real codebase:**
```python
# tests/integration/test_unified_quality_gate.py

import pytest
from pathlib import Path
from analyzer.quality_gates.unified_quality_gate import UnifiedQualityGate

class TestUnifiedQualityGateIntegration:
    @pytest.fixture
    def quality_gate(self, tmp_path):
        # Create test config
        config_path = tmp_path / "quality_gate.config.yaml"
        config_path.write_text('''
analyzers:
  clarity_linter:
    enabled: true
  connascence_analyzer:
    enabled: true
  nasa_standards:
    enabled: true
''')
        return UnifiedQualityGate(config_path)

    def test_analyzes_real_project(self, quality_gate, tmp_path):
        """Test analyzing real project directory."""
        # Create sample project
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text('''
class GodObject:
    def method1(self): pass
    def method2(self): pass
    # ... 16 methods total

def mega_function():
    # 150 lines of code
    pass

def thin_helper():
    return other_function()
''')

        # Run analysis
        results = quality_gate.analyze_project(tmp_path)

        # Verify results
        assert results.overall_score < 100
        assert len(results.clarity_violations) > 0
        assert any(v['rule_id'] == 'CLARITY012' for v in results.clarity_violations)
        assert any(v['rule_id'] == 'CLARITY011' for v in results.clarity_violations)
        assert any(v['rule_id'] == 'CLARITY001' for v in results.clarity_violations)
```

### 4.3 External Codebase Validation

**Test on 3+ external projects:**

1. **Flask (small web framework)**
   - Expected: 50-100 violations
   - Focus: CLARITY011 (long functions), CLARITY012 (god objects)

2. **Pandas (data analysis library)**
   - Expected: 200-300 violations
   - Focus: CLARITY012 (DataFrame class), CLARITY011 (mega functions)

3. **Pytest (testing framework)**
   - Expected: 30-50 violations
   - Focus: CLARITY001 (thin helpers), CLARITY021 (wrappers)

**Validation Script:**
```bash
# scripts/validate_external_codebases.sh

#!/bin/bash
set -e

# Clone external projects
TEMP_DIR=$(mktemp -d)
cd $TEMP_DIR

echo "Validating Flask..."
git clone --depth 1 https://github.com/pallets/flask.git
python -m analyzer.quality_gates.unified_quality_gate flask --output-file flask_results.json

echo "Validating Pandas..."
git clone --depth 1 https://github.com/pandas-dev/pandas.git
python -m analyzer.quality_gates.unified_quality_gate pandas --output-file pandas_results.json

echo "Validating Pytest..."
git clone --depth 1 https://github.com/pytest-dev/pytest.git
python -m analyzer.quality_gates.unified_quality_gate pytest --output-file pytest_results.json

# Generate comparison report
python scripts/compare_results.py flask_results.json pandas_results.json pytest_results.json

# Cleanup
cd -
rm -rf $TEMP_DIR
```

### 4.4 Self-Scan Infrastructure

**Run analyzer on itself:**
```bash
# scripts/self_scan.sh

#!/bin/bash
set -e

# Run Clarity Linter on analyzer codebase
python -m analyzer.quality_gates.unified_quality_gate \
  analyzer/ \
  --config quality_gate.config.yaml \
  --output-format sarif json markdown \
  --output-file self_scan_results.sarif \
  --report-only  # Don't fail, just report

# Expected violations: 150-200
# - CLARITY001: 15-20 thin helpers
# - CLARITY002: 10-15 single-use functions
# - CLARITY011: 8-10 mega-functions
# - CLARITY012: 3 god objects
# - CLARITY021: 40+ pass-through wrappers

# Generate trending report
python scripts/track_self_scan_trends.py self_scan_results.json
```

**Trending Dashboard:**
```python
# scripts/track_self_scan_trends.py

import json
from pathlib import Path
from datetime import datetime

def track_trends(results_path):
    """Track violation trends over time."""
    history_file = Path('.quality-gate-history.json')

    # Load current results
    with open(results_path) as f:
        current = json.load(f)

    # Load history
    if history_file.exists():
        with open(history_file) as f:
            history = json.load(f)
    else:
        history = {'scans': []}

    # Append current scan
    history['scans'].append({
        'timestamp': datetime.now().isoformat(),
        'overall_score': current['overall_score'],
        'violation_counts': current['analyzers']['clarity_linter']['by_severity']
    })

    # Save history
    with open(history_file, 'w') as f:
        json.dump(history, f, indent=2)

    # Generate trend report
    print("\n## Violation Trends\n")
    if len(history['scans']) > 1:
        prev = history['scans'][-2]
        curr = history['scans'][-1]

        score_change = curr['overall_score'] - prev['overall_score']
        print(f"Score change: {score_change:+.1f} points")

        for severity in ['critical', 'high', 'medium', 'low']:
            prev_count = prev['violation_counts'].get(severity, 0)
            curr_count = curr['violation_counts'].get(severity, 0)
            change = curr_count - prev_count
            print(f"{severity.capitalize()}: {curr_count} ({change:+d})")
```

---

## 5. Risk Assessment

### 5.1 Potential Blockers

**Risk 1: AST Parsing Failures**
- **Probability:** Medium (20%)
- **Impact:** High (blocks analysis)
- **Mitigation:**
  - Robust error handling with try-except
  - Fallback to basic analysis if AST fails
  - Log parsing errors for manual review
  - Test on diverse Python versions (3.8-3.12)

**Risk 2: False Positives in Detection**
- **Probability:** Medium-High (30%)
- **Impact:** Medium (user trust)
- **Mitigation:**
  - Comprehensive test suite (90%+ coverage)
  - Manual review of sample violations
  - Tunable thresholds in configuration
  - Exemption mechanism for known false positives

**Risk 3: Performance Issues on Large Codebases**
- **Probability:** Medium (25%)
- **Impact:** Medium (slow CI/CD)
- **Mitigation:**
  - Parallel processing with multiprocessing
  - Caching of AST trees
  - Incremental analysis (only changed files)
  - Benchmark on large projects (>100K LOC)

**Risk 4: Integration with Existing Analyzer**
- **Probability:** Low (10%)
- **Impact:** High (breaks existing functionality)
- **Mitigation:**
  - Keep Clarity Linter as separate module
  - Integration tests for unified quality gate
  - Backward compatibility for existing workflows
  - Feature flags to enable/disable Clarity

**Risk 5: SARIF Schema Validation Failures**
- **Probability:** Low-Medium (15%)
- **Impact:** Medium (GitHub upload fails)
- **Mitigation:**
  - Use SARIF validator library
  - Test with GitHub Code Scanning API
  - Follow SARIF 2.1.0 specification exactly
  - Automated validation in CI/CD

### 5.2 Dependencies on Week 1

**Critical Dependencies:**
- `.github/workflows/self-analysis.yml` (workflow automation)
- `quality_gate.config.yaml` (configuration schema)
- `analyzer/quality_gates/unified_quality_gate.py` (orchestrator skeleton)

**Verification Steps:**
```bash
# Verify Week 1 infrastructure is complete
test -f .github/workflows/self-analysis.yml || echo "ERROR: Missing workflow"
test -f quality_gate.config.yaml || echo "ERROR: Missing config"
test -f analyzer/quality_gates/unified_quality_gate.py || echo "ERROR: Missing orchestrator"
test -f clarity_linter.yaml || echo "ERROR: Missing Clarity spec"
```

### 5.3 Critical Path Analysis

**Critical Path (40 hours):**
```
Day 1-2: CLARITY011 detection (18h) -> CLARITY012 detection (22h) = 40h
```

**If critical path is blocked:**
- Parallelization: CLARITY011 and CLARITY012 can be developed concurrently by different developers
- Fallback: Implement simpler versions (LOC-only, no structure analysis) for initial MVP

### 5.4 Mitigation Strategies

**Strategy 1: Incremental Delivery**
- Deliver rules one at a time (CLARITY011, CLARITY012 first as highest priority)
- Each rule independently testable and deployable
- Can release MVP with 2-3 rules if timeline compressed

**Strategy 2: Parallel Development**
- Assign each rule to separate developer (5 FTEs available)
- Shared AST utilities developed first (Day 1)
- Integration testing on Day 10-12

**Strategy 3: Automated Testing**
- Pre-commit hooks run unit tests
- CI/CD runs full test suite on every PR
- Catch integration issues early

---

## 6. Resource Allocation

### 6.1 Team Assignment (5 FTEs)

**Developer 1: Senior Engineer (Architect)**
- Role: Architecture, integration, code review
- Focus: Unified quality gate, SARIF export, overall design
- Allocation: 100% (full sprint)

**Developer 2: Mid-Level Engineer (Rules 1 & 2)**
- Role: CLARITY001, CLARITY002 detection
- Allocation: 100% (Days 1-8)
- Allocation: 50% (Days 9-12, testing & documentation)

**Developer 3: Mid-Level Engineer (Rule 3)**
- Role: CLARITY011 mega-function detection
- Allocation: 100% (Days 1-8)
- Allocation: 50% (Days 9-12, testing & documentation)

**Developer 4: Mid-Level Engineer (Rule 4)**
- Role: CLARITY012 god object detection
- Allocation: 100% (Days 1-10)
- Allocation: 50% (Days 11-12, testing)

**Developer 5: Junior Engineer (Rule 5 & Testing)**
- Role: CLARITY021 pass-through detection, test infrastructure
- Allocation: 100% (full sprint)

### 6.2 Parallel Work Streams

**Stream 1: Core Infrastructure (Days 1-3)**
- Developer 1: Unified quality gate architecture
- Developer 5: AST utilities, test fixtures
- Deliverables: Base classes, config loader, SARIF exporter

**Stream 2: Rule Detection (Days 4-8)**
- Developer 2: CLARITY001 + CLARITY002
- Developer 3: CLARITY011
- Developer 4: CLARITY012
- Developer 5: CLARITY021
- Deliverables: 5 functional detectors with unit tests

**Stream 3: Integration & Testing (Days 9-12)**
- All developers: Integration testing, external validation, self-scan
- Developer 1: Quality gate integration, SARIF merging
- Developer 2-5: Test coverage, bug fixes, documentation

### 6.3 Daily Milestones

**Day 1-2: Setup & Architecture**
- Day 1 AM: Project setup, module structure, base classes
- Day 1 PM: AST utilities, config loader, SARIF exporter skeleton
- Day 2 AM: Unified quality gate architecture design
- Day 2 PM: First rule detection algorithm (CLARITY001) started

**Day 3-5: Rule Detection (Part 1)**
- Day 3: CLARITY001 detection complete with tests
- Day 4: CLARITY002 detection complete with tests
- Day 5: CLARITY011 detection complete with tests

**Day 6-8: Rule Detection (Part 2)**
- Day 6-7: CLARITY012 detection (complex, 2 days)
- Day 8: CLARITY021 detection complete with tests

**Day 9-10: Integration**
- Day 9: Unified quality gate integration with all 5 rules
- Day 10: SARIF merging, GitHub Actions workflow testing

**Day 11-12: External Validation**
- Day 11: External codebase validation (Flask, Pandas, Pytest)
- Day 12: Self-scan, trending dashboard, final documentation

### 6.4 Review Checkpoints

**Checkpoint 1: Day 3 (Architecture Review)**
- Review: Base classes, AST utilities, SARIF exporter
- Stakeholders: Tech lead, senior engineer
- Criteria: Clean architecture, extensible design, SARIF compliance

**Checkpoint 2: Day 5 (Rule Detection Review)**
- Review: CLARITY001, CLARITY002, CLARITY011 implementations
- Stakeholders: Tech lead, QA engineer
- Criteria: Detection accuracy, test coverage, performance

**Checkpoint 3: Day 8 (Full Rule Set Review)**
- Review: All 5 rules complete with unit tests
- Stakeholders: Tech lead, product owner
- Criteria: All rules functional, 90%+ test coverage

**Checkpoint 4: Day 10 (Integration Review)**
- Review: Unified quality gate with GitHub Actions
- Stakeholders: DevOps, tech lead, product owner
- Criteria: CI/CD integration working, SARIF upload successful

**Checkpoint 5: Day 12 (Final Review & Release)**
- Review: External validation, self-scan, documentation
- Stakeholders: All stakeholders
- Criteria: Production-ready, <5% false positive rate, comprehensive docs

---

## 7. Day-by-Day Schedule

### Day 1: Project Setup & Base Infrastructure

**Morning (4 hours):**
```bash
# Developer 1: Create module structure
mkdir -p analyzer/clarity_linter/detectors
touch analyzer/clarity_linter/{__init__.py,base.py,ast_utils.py,sarif_exporter.py,config_loader.py}
touch analyzer/clarity_linter/detectors/{__init__.py,clarity001_thin_helper.py,clarity002_single_use.py,clarity011_mega_function.py,clarity012_god_object.py,clarity021_passthrough.py}

# Developer 5: Create test structure
mkdir -p tests/clarity_linter/fixtures
touch tests/clarity_linter/{test_clarity001.py,test_clarity002.py,test_clarity011.py,test_clarity012.py,test_clarity021.py,test_ast_utils.py,conftest.py}
```

**Afternoon (4 hours):**
- Developer 1: Implement `base.py` (ClarityRuleBase class)
- Developer 1: Implement `config_loader.py` (YAML config loading)
- Developer 5: Implement `ast_utils.py` (count_loc, find_callers utilities)
- Developer 5: Create test fixtures in `fixtures/`

**End of Day 1:**
- [x] Module structure created
- [x] Base classes implemented
- [x] AST utilities functional
- [x] Test infrastructure ready

---

### Day 2: SARIF Export & CLARITY001 Start

**Morning (4 hours):**
- Developer 1: Implement `sarif_exporter.py` (SARIF 2.1.0 format)
- Developer 2: Start CLARITY001 detection algorithm

**Afternoon (4 hours):**
- Developer 1: Test SARIF export with sample violations
- Developer 2: Continue CLARITY001 implementation
- Developer 5: Write unit tests for AST utilities

**End of Day 2:**
- [x] SARIF exporter complete
- [x] CLARITY001 detection 50% complete
- [x] AST utilities fully tested

---

### Day 3: CLARITY001 Complete + CLARITY002 Start

**Morning (4 hours):**
- Developer 2: Complete CLARITY001 detection
- Developer 2: Write unit tests for CLARITY001

**Afternoon (4 hours):**
- Developer 2: Start CLARITY002 detection
- Developer 1: Review CLARITY001 code
- Developer 3: Start CLARITY011 detection

**End of Day 3:**
- [x] CLARITY001 complete with tests (90%+ coverage)
- [x] CLARITY002 detection 40% complete
- [x] CLARITY011 detection 20% complete

---

### Day 4: CLARITY002 Complete + CLARITY011 Progress

**Morning (4 hours):**
- Developer 2: Complete CLARITY002 detection
- Developer 3: Continue CLARITY011 (structure analysis)
- Developer 4: Start CLARITY012 detection

**Afternoon (4 hours):**
- Developer 2: Write unit tests for CLARITY002
- Developer 3: Write unit tests for CLARITY011
- Developer 4: Continue CLARITY012 (cohesion calculation)

**End of Day 4:**
- [x] CLARITY002 complete with tests
- [x] CLARITY011 detection 70% complete
- [x] CLARITY012 detection 30% complete

---

### Day 5: CLARITY011 Complete + CLARITY012 Progress

**Morning (4 hours):**
- Developer 3: Complete CLARITY011 detection
- Developer 4: Continue CLARITY012 (cluster identification)
- Developer 5: Start CLARITY021 detection

**Afternoon (4 hours):**
- Developer 3: Write unit tests for CLARITY011
- Developer 4: Continue CLARITY012 implementation
- Developer 5: Continue CLARITY021

**End of Day 5:**
- [x] CLARITY011 complete with tests
- [x] CLARITY012 detection 60% complete
- [x] CLARITY021 detection 40% complete

**Checkpoint 2: Rule Detection Review (3/5 rules complete)**

---

### Day 6-7: CLARITY012 & CLARITY021 Completion

**Day 6 Morning:**
- Developer 4: Complete CLARITY012 detection
- Developer 5: Continue CLARITY021 (delegation patterns)

**Day 6 Afternoon:**
- Developer 4: Write unit tests for CLARITY012
- Developer 5: Complete CLARITY021 detection

**Day 7 Morning:**
- Developer 4: Additional CLARITY012 tests
- Developer 5: Write unit tests for CLARITY021

**Day 7 Afternoon:**
- Developer 1: Review all 5 rule implementations
- Developer 2-5: Fix review issues, improve test coverage

**End of Day 7:**
- [x] CLARITY012 complete with tests
- [x] CLARITY021 complete with tests
- [x] All 5 rules reviewed and approved

---

### Day 8: Rule Integration & Testing

**Morning (4 hours):**
- Developer 1: Implement rule registration mechanism
- Developer 1: Create ClarityLinter main class
- Developer 2-5: Integration tests for individual rules

**Afternoon (4 hours):**
- Developer 1: Test ClarityLinter with all 5 rules
- Developer 2-5: Cross-rule testing (ensure no conflicts)

**End of Day 8:**
- [x] ClarityLinter class complete
- [x] All 5 rules registered and functional
- [x] Integration tests passing

**Checkpoint 3: Full Rule Set Review (5/5 rules complete)**

---

### Day 9: Unified Quality Gate Integration

**Morning (4 hours):**
- Developer 1: Integrate ClarityLinter into unified_quality_gate.py
- Developer 1: Implement unified scoring algorithm
- Developer 2-3: Update GitHub Actions workflow

**Afternoon (4 hours):**
- Developer 1: SARIF merging from multiple analyzers
- Developer 2-3: Test workflow with sample PR
- Developer 4-5: External codebase validation prep

**End of Day 9:**
- [x] Unified quality gate integrated
- [x] SARIF merging functional
- [x] GitHub Actions workflow updated

---

### Day 10: GitHub Actions Testing & SARIF Upload

**Morning (4 hours):**
- Developer 1: Test SARIF upload to GitHub Code Scanning
- Developer 2-3: PR comment generation, check run creation
- Developer 4-5: Start external validation (Flask)

**Afternoon (4 hours):**
- Developer 1: Fix SARIF validation issues
- Developer 2-3: Test full PR workflow end-to-end
- Developer 4-5: Continue external validation (Pandas, Pytest)

**End of Day 10:**
- [x] GitHub Code Scanning integration working
- [x] PR comments and check runs functional
- [x] External validation in progress

**Checkpoint 4: Integration Review (CI/CD functional)**

---

### Day 11: External Validation & Self-Scan

**Morning (4 hours):**
- Developer 1: Analyze external validation results
- Developer 2-3: Tune thresholds based on validation
- Developer 4-5: Run self-scan on analyzer codebase

**Afternoon (4 hours):**
- All developers: Review self-scan violations
- Developer 1: Generate trending dashboard
- Developer 2-5: Document violation patterns

**End of Day 11:**
- [x] External validation complete (3 projects)
- [x] Self-scan complete (150-200 violations documented)
- [x] Trending dashboard functional

---

### Day 12: Final Testing & Documentation

**Morning (4 hours):**
- Developer 1: Final code review and cleanup
- Developer 2-5: Complete test coverage (target: 90%+)

**Afternoon (4 hours):**
- All developers: Documentation
  - API reference
  - Rule catalog with examples
  - Integration guide
  - Troubleshooting guide
- Developer 1: Prepare demo for stakeholders

**End of Day 12:**
- [x] Test coverage 90%+
- [x] Documentation complete
- [x] Demo ready for Week 3 kickoff

**Checkpoint 5: Final Review & Release (Production-ready)**

---

## 8. Copy-Paste Commands

### 8.1 Project Setup

```bash
# Create directory structure
cd /c/Users/17175/Desktop/connascence
mkdir -p analyzer/clarity_linter/detectors
mkdir -p tests/clarity_linter/fixtures

# Create module files
touch analyzer/clarity_linter/__init__.py
touch analyzer/clarity_linter/base.py
touch analyzer/clarity_linter/ast_utils.py
touch analyzer/clarity_linter/sarif_exporter.py
touch analyzer/clarity_linter/config_loader.py

# Create detector files
touch analyzer/clarity_linter/detectors/__init__.py
touch analyzer/clarity_linter/detectors/clarity001_thin_helper.py
touch analyzer/clarity_linter/detectors/clarity002_single_use.py
touch analyzer/clarity_linter/detectors/clarity011_mega_function.py
touch analyzer/clarity_linter/detectors/clarity012_god_object.py
touch analyzer/clarity_linter/detectors/clarity021_passthrough.py

# Create test files
touch tests/clarity_linter/conftest.py
touch tests/clarity_linter/test_clarity001.py
touch tests/clarity_linter/test_clarity002.py
touch tests/clarity_linter/test_clarity011.py
touch tests/clarity_linter/test_clarity012.py
touch tests/clarity_linter/test_clarity021.py
touch tests/clarity_linter/test_ast_utils.py

# Create test fixtures
touch tests/clarity_linter/fixtures/sample_thin_helper.py
touch tests/clarity_linter/fixtures/sample_mega_function.py
touch tests/clarity_linter/fixtures/sample_god_object.py
touch tests/clarity_linter/fixtures/sample_passthrough.py
```

### 8.2 Run Unit Tests

```bash
# Run all Clarity Linter tests
cd /c/Users/17175/Desktop/connascence
pytest tests/clarity_linter/ -v --cov=analyzer/clarity_linter --cov-report=html

# Run specific rule tests
pytest tests/clarity_linter/test_clarity001.py -v
pytest tests/clarity_linter/test_clarity012.py -v

# Run with coverage report
pytest tests/clarity_linter/ --cov=analyzer/clarity_linter --cov-report=term-missing
```

### 8.3 Run Unified Quality Gate

```bash
# Run on current project
cd /c/Users/17175/Desktop/connascence
python -m analyzer.quality_gates.unified_quality_gate . --config quality_gate.config.yaml --verbose

# Run with specific output format
python -m analyzer.quality_gates.unified_quality_gate analyzer/ \
  --output-format sarif json markdown \
  --output-file results.sarif \
  --fail-on high

# Run self-scan (report only)
python -m analyzer.quality_gates.unified_quality_gate analyzer/ \
  --report-only \
  --output-file self_scan_results.json
```

### 8.4 External Validation

```bash
# Validate Flask
cd /tmp
git clone --depth 1 https://github.com/pallets/flask.git
cd /c/Users/17175/Desktop/connascence
python -m analyzer.quality_gates.unified_quality_gate /tmp/flask \
  --output-file docs/validation/flask_results.json

# Validate Pandas
cd /tmp
git clone --depth 1 https://github.com/pandas-dev/pandas.git
cd /c/Users/17175/Desktop/connascence
python -m analyzer.quality_gates.unified_quality_gate /tmp/pandas \
  --output-file docs/validation/pandas_results.json

# Validate Pytest
cd /tmp
git clone --depth 1 https://github.com/pytest-dev/pytest.git
cd /c/Users/17175/Desktop/connascence
python -m analyzer.quality_gates.unified_quality_gate /tmp/pytest \
  --output-file docs/validation/pytest_results.json
```

### 8.5 GitHub Actions Trigger

```bash
# Create test PR to trigger self-analysis workflow
cd /c/Users/17175/Desktop/connascence
git checkout -b test/clarity-linter-week2
git add analyzer/clarity_linter/
git commit -m "feat: Add Clarity Linter MVP with 5 core rules"
git push origin test/clarity-linter-week2

# Create PR via GitHub CLI
gh pr create \
  --title "Week 2: Clarity Linter MVP" \
  --body "Implements 5 core Clarity Linter rules with 90%+ test coverage" \
  --base main

# Watch workflow run
gh run watch
```

### 8.6 SARIF Validation

```bash
# Validate SARIF output with Microsoft validator
cd /c/Users/17175/Desktop/connascence
npm install -g @microsoft/sarif-validator

# Validate SARIF file
sarif-validator results.sarif

# Upload to GitHub Code Scanning
gh api repos/{owner}/{repo}/code-scanning/sarifs \
  --method POST \
  --field commit_sha="$(git rev-parse HEAD)" \
  --field ref="refs/heads/main" \
  --field sarif="@results.sarif"
```

---

## 9. Success Criteria

### 9.1 Functional Requirements

- [x] All 5 rules detect violations accurately (95%+ precision)
- [x] SARIF output validates with GitHub Code Scanning
- [x] Unified quality gate integrates all 3 analyzers (Clarity, Connascence, NASA)
- [x] CLI interface functional with all output formats (SARIF, JSON, Markdown)
- [x] GitHub Actions workflow runs successfully on PRs

### 9.2 Quality Metrics

- [x] Test coverage 90%+ for all rules
- [x] Zero false positives on reference implementations
- [x] Self-scan identifies 150-200+ violations in analyzer codebase
- [x] External validation successful on 3+ projects
- [x] Performance: <5 seconds for 10K LOC project

### 9.3 Documentation

- [x] API reference documentation complete
- [x] Rule catalog with examples and fix suggestions
- [x] Integration guide for CI/CD
- [x] Troubleshooting guide for common issues

### 9.4 Deliverables Checklist

- [x] `analyzer/clarity_linter/` module (650+ LOC)
- [x] 5 rule detectors (CLARITY001, 002, 011, 012, 021)
- [x] `unified_quality_gate.py` with real integration
- [x] SARIF exporter with schema validation
- [x] Unit tests (90%+ coverage target)
- [x] Integration tests
- [x] External validation results (3 projects)
- [x] Self-scan results and trending dashboard
- [x] Comprehensive documentation

---

## 10. Next Steps (Week 3)

**Week 3 Focus: Self-Improvement & Dogfooding**

1. **Fix High-Priority Violations** (Days 1-5)
   - Address critical violations from self-scan
   - Split god objects (CLARITY012 violations)
   - Refactor mega-functions (CLARITY011 violations)

2. **Expand Rule Set** (Days 6-10)
   - Add CLARITY010 (soft limit 50-100 LOC)
   - Add CLARITY003 (trivial helper chains)
   - Add CLARITY030 (harmful duplication)

3. **Continuous Monitoring** (Days 11-12)
   - Weekly self-scans with trending
   - Violation reduction tracking
   - Quality score improvement monitoring

**Transition Criteria:**
- Violation count reduced by 50% from baseline
- Overall quality score >70/100
- Zero critical violations in core modules

---

## Appendix A: Effort Summary

| Task | Developer | Hours | Days |
|------|-----------|-------|------|
| Project setup | All | 8 | 1 |
| CLARITY001 detection | Dev 2 | 16 | 2 |
| CLARITY002 detection | Dev 2 | 14 | 2 |
| CLARITY011 detection | Dev 3 | 18 | 2.5 |
| CLARITY012 detection | Dev 4 | 22 | 3 |
| CLARITY021 detection | Dev 5 | 16 | 2 |
| AST utilities | Dev 5 | 12 | 1.5 |
| SARIF exporter | Dev 1 | 8 | 1 |
| Unified gate integration | Dev 1 | 16 | 2 |
| Testing & validation | All | 24 | 3 |
| Documentation | All | 12 | 1.5 |
| **Total** | | **166** | **~21 days** |

**With 5 FTEs working in parallel: 21 days / 5 = ~4.2 days (actual: 12 days with reviews/testing)**

---

## Appendix B: Technology Stack

**Languages:**
- Python 3.8+ (AST parsing, detector implementation)
- YAML (configuration)
- JSON (output formats)
- Markdown (human-readable reports)

**Libraries:**
- `ast` (Python standard library for AST parsing)
- `yaml` (PyYAML for config loading)
- `pytest` (testing framework)
- `pytest-cov` (code coverage)
- `typing` (type hints)

**Tools:**
- GitHub Actions (CI/CD)
- GitHub Code Scanning (SARIF integration)
- SARIF validator (schema validation)
- Git (version control)

**Standards:**
- SARIF 2.1.0 (Static Analysis Results Interchange Format)
- NASA-STD-8739.8 (NASA coding standards)
- PEP 8 (Python style guide)

---

## Appendix C: Glossary

- **AST**: Abstract Syntax Tree - tree representation of source code structure
- **Cohesion**: Measure of how related methods in a class are to each other
- **Cyclomatic Complexity**: Measure of code complexity based on decision points
- **God Object**: Class with too many responsibilities (>15 methods or >500 LOC)
- **LOC**: Lines of Code (excluding comments, docstrings, blank lines)
- **Mega-Function**: Function exceeding 100 lines (hard limit)
- **Pass-Through**: Function that just calls another function with same parameters
- **SARIF**: Static Analysis Results Interchange Format - JSON schema for analysis results
- **Thin Helper**: Function <20 LOC with single caller, adds no abstraction
- **Unified Quality Gate**: Orchestrator combining Clarity, Connascence, and NASA analyzers

---

**END OF WEEK 2 IMPLEMENTATION PLAN**

**Status:** Ready for Execution
**Approval:** Pending stakeholder review
**Start Date:** 2025-11-20
**Target Completion:** 2025-12-03
