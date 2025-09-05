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
Class split fixer for Connascence of Algorithm (CoA) violations.

Automatically identifies god objects and generates patches to split them
into smaller, more cohesive classes following single responsibility principle.
"""

import ast
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass
from collections import defaultdict

from .patch_api import PatchSuggestion
from mcp.server import ConnascenceViolation


@dataclass
class MethodGroup:
    """Group of related methods that could form a separate class."""
    name: str
    methods: List[str]
    shared_attributes: Set[str]
    cohesion_score: float
    suggested_class_name: str


@dataclass
class ClassAnalysis:
    """Analysis result for a class."""
    name: str
    method_count: int
    attribute_count: int
    method_groups: List[MethodGroup]
    complexity_score: float
    splitting_confidence: float


class ClassSplitFixer:
    """Fixes Connascence of Algorithm violations by splitting large classes."""
    
    def __init__(self):
        self.god_class_method_threshold = 20
        self.min_methods_per_group = 3
        self.cohesion_threshold = 0.6
    
    def generate_patch(self, violation: ConnascenceViolation,
                      tree: ast.AST, source_code: str) -> Optional[PatchSuggestion]:
        """Generate patch for a god class violation."""
        class_analysis = self._analyze_class(violation, tree)
        if not class_analysis:
            return None
        
        if class_analysis.splitting_confidence < 0.7:
            return None
        
        best_split = self._find_best_split(class_analysis)
        if not best_split:
            return None
        
        old_code = self._get_class_code(violation, source_code)
        new_code = self._generate_split_code(class_analysis, best_split, source_code)
        
        return PatchSuggestion(
            violation_id=violation.id,
            confidence=class_analysis.splitting_confidence,
            description=f"Split {class_analysis.name} into {best_split.suggested_class_name} + slimmed original",
            old_code=old_code,
            new_code=new_code,
            file_path=violation.file_path,
            line_range=self._get_class_line_range(violation, tree),
            safety_level='moderate',  # Class splitting is inherently risky
            rollback_info={}
        )
    
    def _analyze_class(self, violation: ConnascenceViolation, 
                      tree: ast.AST) -> Optional[ClassAnalysis]:
        """Analyze class structure for potential splits."""
        class_finder = ClassFinder(violation.line_number)
        class_finder.visit(tree)
        
        if not class_finder.found_class:
            return None
        
        class_node = class_finder.found_class
        
        # Extract methods and their attributes
        method_analyzer = MethodAnalyzer()
        method_analyzer.visit(class_node)
        
        # Group methods by shared attributes
        method_groups = self._group_methods_by_cohesion(
            method_analyzer.methods,
            method_analyzer.method_attributes
        )
        
        # Calculate complexity and splitting confidence
        complexity = self._calculate_complexity(method_analyzer)
        confidence = self._calculate_splitting_confidence(method_analyzer, method_groups)
        
        return ClassAnalysis(
            name=class_node.name,
            method_count=len(method_analyzer.methods),
            attribute_count=len(method_analyzer.all_attributes),
            method_groups=method_groups,
            complexity_score=complexity,
            splitting_confidence=confidence
        )
    
    def _group_methods_by_cohesion(self, methods: List[str],
                                  method_attributes: Dict[str, Set[str]]) -> List[MethodGroup]:
        """Group methods by their attribute usage patterns."""
        # Calculate attribute similarity between methods
        similarity_matrix = {}
        method_list = list(methods)
        
        for i, method1 in enumerate(method_list):
            for j, method2 in enumerate(method_list[i+1:], i+1):
                attrs1 = method_attributes.get(method1, set())
                attrs2 = method_attributes.get(method2, set())
                
                if not attrs1 and not attrs2:
                    similarity = 0.1  # Low similarity for methods with no attributes
                else:
                    # Jaccard similarity
                    intersection = len(attrs1 & attrs2)
                    union = len(attrs1 | attrs2)
                    similarity = intersection / union if union > 0 else 0
                
                similarity_matrix[(method1, method2)] = similarity
        
        # Find cohesive groups using simple clustering
        groups = []
        processed_methods = set()
        
        for method in method_list:
            if method in processed_methods:
                continue
            
            # Find methods with high similarity to this one
            group_methods = [method]
            group_attributes = method_attributes.get(method, set()).copy()
            
            for other_method in method_list:
                if other_method == method or other_method in processed_methods:
                    continue
                
                similarity = similarity_matrix.get((method, other_method)) or \
                           similarity_matrix.get((other_method, method), 0)
                
                if similarity > self.cohesion_threshold:
                    group_methods.append(other_method)
                    group_attributes.update(method_attributes.get(other_method, set()))
            
            # Only consider groups with enough methods
            if len(group_methods) >= self.min_methods_per_group:
                cohesion = self._calculate_group_cohesion(group_methods, method_attributes)
                suggested_name = self._suggest_class_name(group_methods, group_attributes)
                
                groups.append(MethodGroup(
                    name=f"group_{len(groups)}",
                    methods=group_methods,
                    shared_attributes=group_attributes,
                    cohesion_score=cohesion,
                    suggested_class_name=suggested_name
                ))
                
                processed_methods.update(group_methods)
        
        return groups
    
    def _calculate_group_cohesion(self, methods: List[str], 
                                 method_attributes: Dict[str, Set[str]]) -> float:
        """Calculate cohesion score for a method group."""
        if len(methods) < 2:
            return 0.0
        
        # Calculate average pairwise similarity
        total_similarity = 0.0
        pairs = 0
        
        for i, method1 in enumerate(methods):
            for method2 in methods[i+1:]:
                attrs1 = method_attributes.get(method1, set())
                attrs2 = method_attributes.get(method2, set())
                
                if attrs1 or attrs2:
                    intersection = len(attrs1 & attrs2)
                    union = len(attrs1 | attrs2)
                    similarity = intersection / union if union > 0 else 0
                    total_similarity += similarity
                    pairs += 1
        
        return total_similarity / pairs if pairs > 0 else 0.0
    
    def _suggest_class_name(self, methods: List[str], 
                           attributes: Set[str]) -> str:
        """Suggest a name for the new class based on methods and attributes."""
        # Extract common prefixes/suffixes from method names
        method_words = []
        for method in methods:
            # Split camelCase and snake_case
            words = []
            current_word = ""
            for char in method:
                if char.isupper() and current_word:
                    words.append(current_word.lower())
                    current_word = char.lower()
                elif char == '_':
                    if current_word:
                        words.append(current_word.lower())
                    current_word = ""
                else:
                    current_word += char.lower()
            if current_word:
                words.append(current_word)
            method_words.extend(words)
        
        # Find most common words
        word_counts = defaultdict(int)
        for word in method_words:
            if len(word) > 2:  # Skip short words
                word_counts[word] += 1
        
        if word_counts:
            most_common = max(word_counts.items(), key=lambda x: x[1])
            base_name = most_common[0].title()
        else:
            base_name = "Component"
        
        return f"{base_name}Handler"
    
    def _calculate_complexity(self, analyzer: 'MethodAnalyzer') -> float:
        """Calculate overall class complexity score."""
        method_count_factor = min(analyzer.method_count / 10.0, 2.0)  # Cap at 2x
        attribute_factor = min(len(analyzer.all_attributes) / 15.0, 1.5)  # Cap at 1.5x
        
        # Factor in method complexity
        avg_method_complexity = sum(analyzer.method_complexity.values()) / len(analyzer.method_complexity) if analyzer.method_complexity else 1.0
        complexity_factor = min(avg_method_complexity / 5.0, 2.0)
        
        return method_count_factor + attribute_factor + complexity_factor
    
    def _calculate_splitting_confidence(self, analyzer: 'MethodAnalyzer',
                                       groups: List[MethodGroup]) -> float:
        """Calculate confidence in splitting the class."""
        confidence = 0.5  # Base confidence
        
        # Increase confidence for larger classes
        if analyzer.method_count > 25:
            confidence += 0.2
        elif analyzer.method_count > 20:
            confidence += 0.1
        
        # Increase confidence if we found cohesive groups
        if groups:
            avg_cohesion = sum(g.cohesion_score for g in groups) / len(groups)
            confidence += avg_cohesion * 0.3
            
            # Bonus for multiple good groups
            if len(groups) > 1:
                confidence += 0.1
        
        # Reduce confidence if class is already well-structured
        if analyzer.method_count < self.god_class_method_threshold:
            confidence -= 0.2
        
        return min(confidence, 0.9)  # Cap at 90%
    
    def _find_best_split(self, analysis: ClassAnalysis) -> Optional[MethodGroup]:
        """Find the best method group to split into a new class."""
        if not analysis.method_groups:
            return None
        
        # Score groups by cohesion and size
        best_group = None
        best_score = 0.0
        
        for group in analysis.method_groups:
            # Score based on cohesion and method count
            score = group.cohesion_score * 0.7 + (len(group.methods) / 10.0) * 0.3
            
            if score > best_score:
                best_score = score
                best_group = group
        
        return best_group if best_score > 0.5 else None
    
    def _get_class_code(self, violation: ConnascenceViolation, source: str) -> str:
        """Extract the class code."""
        lines = source.splitlines()
        # This is simplified - in practice would need better parsing
        return '\n'.join(lines[violation.line_number-1:violation.line_number+50])
    
    def _get_class_line_range(self, violation: ConnascenceViolation, 
                             tree: ast.AST) -> Tuple[int, int]:
        """Get the line range of the class."""
        class_finder = ClassFinder(violation.line_number)
        class_finder.visit(tree)
        
        if class_finder.found_class:
            cls = class_finder.found_class
            start = cls.lineno
            end = getattr(cls, 'end_lineno', start + 50)  # Fallback
            return (start, end)
        
        return (violation.line_number, violation.line_number + 20)
    
    def _generate_split_code(self, analysis: ClassAnalysis, 
                            split_group: MethodGroup, source_code: str) -> str:
        """Generate code for the split class."""
        # This is a simplified implementation
        new_class_code = f"""
class {split_group.suggested_class_name}:
    \"\"\"Extracted component from {analysis.name}.\"\"\"
    
    def __init__(self):
        # TODO: Initialize shared attributes
        {chr(10).join(f'        self.{attr} = None' for attr in split_group.shared_attributes)}
    
    # TODO: Move these methods from {analysis.name}:
    {chr(10).join(f'    # - {method}' for method in split_group.methods)}
    
    pass


# TODO: Update {analysis.name} to use {split_group.suggested_class_name}
# TODO: Remove extracted methods from {analysis.name}
# TODO: Add composition relationship
"""
        
        return new_class_code


class ClassFinder(ast.NodeVisitor):
    """AST visitor to find classes on specific lines."""
    
    def __init__(self, target_line: int):
        self.target_line = target_line
        self.found_class = None
    
    def visit_ClassDef(self, node):
        if hasattr(node, 'lineno') and node.lineno <= self.target_line:
            end_line = getattr(node, 'end_lineno', node.lineno + 100)
            if self.target_line <= end_line:
                self.found_class = node
        self.generic_visit(node)


class MethodAnalyzer(ast.NodeVisitor):
    """Analyzes methods and their attribute usage in a class."""
    
    def __init__(self):
        self.methods = []
        self.method_attributes = defaultdict(set)
        self.method_complexity = defaultdict(int)
        self.all_attributes = set()
        self.method_count = 0
        self._current_method = None
    
    def visit_FunctionDef(self, node):
        self.methods.append(node.name)
        self.method_count += 1
        self._current_method = node.name
        
        # Simple complexity measure
        complexity = 1  # Base complexity
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.Try)):
                complexity += 1
        self.method_complexity[node.name] = complexity
        
        self.generic_visit(node)
        self._current_method = None
    
    def visit_Attribute(self, node):
        if self._current_method and isinstance(node.value, ast.Name) and node.value.id == 'self':
            attr_name = node.attr
            self.method_attributes[self._current_method].add(attr_name)
            self.all_attributes.add(attr_name)
        self.generic_visit(node)