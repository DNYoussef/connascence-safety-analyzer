#!/usr/bin/env python3
"""
MECE (Mutually Exclusive, Collectively Exhaustive) Analyzer
===========================================================

This analyzer identifies code duplication and overlapping functionality
across the codebase using the full analysis suite. It detects when AI or
developers accidentally create duplicate implementations, partial duplicates,
or scattered functionality that should be consolidated.

Capabilities:
- Function similarity detection using AST analysis
- Module responsibility overlap detection
- Connascence-based duplication identification
- Import pattern analysis for detecting scattered implementations
- Class/method consolidation recommendations

Author: Connascence Safety Analyzer Team
"""

import ast
import hashlib
import os
import json
from typing import Dict, List, Any, Tuple, Set, Optional
from dataclasses import dataclass, field
from collections import defaultdict
import difflib
from pathlib import Path


@dataclass
class DuplicationCluster:
    """Represents a cluster of duplicated or overlapping code."""
    cluster_id: str
    duplication_type: str  # 'exact', 'similar', 'functional', 'responsibility'
    confidence: float  # 0.0-1.0
    files_involved: List[str]
    similarity_score: float
    consolidation_recommendation: str
    impact_assessment: str
    code_snippets: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FunctionSignature:
    """Represents a function's signature and characteristics."""
    name: str
    file_path: str
    line_number: int
    parameters: List[str]
    return_type: Optional[str]
    docstring: Optional[str]
    ast_hash: str  # Hash of AST structure
    body_hash: str  # Hash of function body
    complexity_metrics: Dict[str, Any]
    imports_used: Set[str]


class MECEAnalyzer:
    """
    MECE Analyzer for detecting code duplication and functional overlap.
    
    Uses multiple analysis techniques:
    1. AST-based structural similarity
    2. Semantic function analysis
    3. Import dependency analysis
    4. Responsibility overlap detection
    5. Connascence-based clustering
    """
    
    def __init__(self, analysis_suite_results: Dict[str, Any] = None):
        self.analysis_results = analysis_suite_results or {}
        self.function_registry = {}  # file_path -> List[FunctionSignature]
        self.class_registry = {}     # file_path -> List[ClassInfo] 
        self.import_registry = {}    # file_path -> Set[imports]
        self.duplication_clusters = []
        self.consolidation_recommendations = []
        
    def analyze_codebase(self, root_path: str, file_patterns: List[str] = None) -> Dict[str, Any]:
        """
        Perform comprehensive MECE analysis on the codebase.
        
        Args:
            root_path: Root directory to analyze
            file_patterns: File patterns to include (e.g., ['*.py', '*.js'])
        
        Returns:
            Comprehensive duplication analysis results
        """
        if file_patterns is None:
            file_patterns = ['*.py', '*.js', '*.ts', '*.c', '*.cpp']
            
        results = {
            'analysis_timestamp': self._get_timestamp(),
            'root_path': root_path,
            'files_analyzed': 0,
            'duplication_clusters': [],
            'consolidation_opportunities': [],
            'metrics': {},
            'recommendations': []
        }
        
        try:
            # Phase 1: Build comprehensive code registry
            print("[SEARCH] Phase 1: Building code registry...")
            self._build_code_registry(root_path, file_patterns)
            results['files_analyzed'] = len(self.function_registry)
            
            # Phase 2: Detect exact duplications
            print("[SEARCH] Phase 2: Detecting exact duplications...")
            exact_clusters = self._detect_exact_duplications()
            results['duplication_clusters'].extend(exact_clusters)
            
            # Phase 3: Detect similar functions (AST similarity)
            print("[SEARCH] Phase 3: Detecting similar functions...")
            similar_clusters = self._detect_similar_functions()
            results['duplication_clusters'].extend(similar_clusters)
            
            # Phase 4: Detect functional overlap (semantic analysis)
            print("[SEARCH] Phase 4: Detecting functional overlap...")
            functional_clusters = self._detect_functional_overlap()
            results['duplication_clusters'].extend(functional_clusters)
            
            # Phase 5: Detect responsibility overlap (module analysis)
            print("[SEARCH] Phase 5: Detecting responsibility overlap...")
            responsibility_clusters = self._detect_responsibility_overlap()
            results['duplication_clusters'].extend(responsibility_clusters)
            
            # Phase 6: Generate consolidation recommendations
            print("[SEARCH] Phase 6: Generating consolidation recommendations...")
            results['consolidation_opportunities'] = self._generate_consolidation_recommendations()
            
            # Phase 7: Calculate metrics and priority rankings
            print("[SEARCH] Phase 7: Calculating metrics...")
            results['metrics'] = self._calculate_duplication_metrics()
            
            # Phase 8: Create actionable recommendations
            results['recommendations'] = self._create_actionable_recommendations()
            
            print(f"[OK] MECE Analysis Complete: {len(results['duplication_clusters'])} clusters found")
            
        except Exception as e:
            results['error'] = f"MECE analysis failed: {str(e)}"
            print(f"[ERROR] MECE Analysis Error: {e}")
            
        return results
    
    def _build_code_registry(self, root_path: str, file_patterns: List[str]):
        """Build comprehensive registry of all code elements."""
        for file_path in self._find_files(root_path, file_patterns):
            if file_path.endswith('.py'):
                self._analyze_python_file(file_path)
            elif file_path.endswith(('.js', '.ts')):
                self._analyze_javascript_file(file_path)
            elif file_path.endswith(('.c', '.cpp')):
                self._analyze_c_file(file_path)
    
    def _analyze_python_file(self, file_path: str):
        """Analyze Python file and extract function signatures."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            functions = []
            imports = set()
            
            # Extract imports
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.add(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.add(node.module)
            
            # Extract functions
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_sig = self._extract_python_function_signature(node, file_path, content, imports)
                    functions.append(func_sig)
            
            self.function_registry[file_path] = functions
            self.import_registry[file_path] = imports
            
        except Exception as e:
            print(f"Warning: Failed to analyze {file_path}: {e}")
    
    def _extract_python_function_signature(self, node: ast.FunctionDef, file_path: str, 
                                         content: str, imports: Set[str]) -> FunctionSignature:
        """Extract detailed function signature from AST node."""
        # Get parameters
        params = [arg.arg for arg in node.args.args]
        
        # Get docstring
        docstring = ast.get_docstring(node)
        
        # Calculate AST hash (structure-based)
        ast_hash = self._calculate_ast_hash(node)
        
        # Calculate body hash (content-based)
        body_lines = content.split('\n')[node.lineno-1:node.end_lineno]
        body_content = '\n'.join(body_lines)
        body_hash = hashlib.md5(body_content.encode()).hexdigest()
        
        # Calculate complexity metrics
        complexity_metrics = {
            'cyclomatic_complexity': self._calculate_cyclomatic_complexity(node),
            'lines_of_code': node.end_lineno - node.lineno + 1,
            'parameter_count': len(params),
            'nested_depth': self._calculate_nesting_depth(node)
        }
        
        return FunctionSignature(
            name=node.name,
            file_path=file_path,
            line_number=node.lineno,
            parameters=params,
            return_type=None,  # TODO: Extract from type hints
            docstring=docstring,
            ast_hash=ast_hash,
            body_hash=body_hash,
            complexity_metrics=complexity_metrics,
            imports_used=imports
        )
    
    def _detect_exact_duplications(self) -> List[DuplicationCluster]:
        """Detect exact code duplications using hash comparison."""
        clusters = []
        hash_groups = defaultdict(list)
        
        # Group functions by body hash
        for file_path, functions in self.function_registry.items():
            for func in functions:
                hash_groups[func.body_hash].append(func)
        
        # Create clusters for groups with multiple functions
        for body_hash, functions in hash_groups.items():
            if len(functions) > 1:
                cluster = DuplicationCluster(
                    cluster_id=f"exact_{body_hash[:8]}",
                    duplication_type="exact",
                    confidence=1.0,
                    files_involved=[f.file_path for f in functions],
                    similarity_score=1.0,
                    consolidation_recommendation=self._generate_exact_dup_recommendation(functions),
                    impact_assessment=self._assess_exact_dup_impact(functions)
                )
                clusters.append(cluster)
        
        return clusters
    
    def _detect_similar_functions(self) -> List[DuplicationCluster]:
        """Detect similar functions using AST structure comparison."""
        clusters = []
        all_functions = []
        
        # Collect all functions
        for functions in self.function_registry.values():
            all_functions.extend(functions)
        
        # Compare each function with every other
        compared_pairs = set()
        for i, func1 in enumerate(all_functions):
            for j, func2 in enumerate(all_functions[i+1:], i+1):
                pair_key = tuple(sorted([func1.file_path + func1.name, func2.file_path + func2.name]))
                if pair_key in compared_pairs:
                    continue
                compared_pairs.add(pair_key)
                
                similarity = self._calculate_function_similarity(func1, func2)
                if similarity > 0.7:  # High similarity threshold
                    cluster = DuplicationCluster(
                        cluster_id=f"similar_{i}_{j}",
                        duplication_type="similar",
                        confidence=similarity,
                        files_involved=[func1.file_path, func2.file_path],
                        similarity_score=similarity,
                        consolidation_recommendation=self._generate_similarity_recommendation(func1, func2, similarity),
                        impact_assessment=self._assess_similarity_impact(func1, func2)
                    )
                    clusters.append(cluster)
        
        return clusters
    
    def _detect_functional_overlap(self) -> List[DuplicationCluster]:
        """Detect functional overlap using semantic analysis."""
        clusters = []
        
        # Group functions by semantic similarity (name, docstring, imports)
        semantic_groups = self._group_functions_by_semantics()
        
        for group_id, functions in semantic_groups.items():
            if len(functions) > 1:
                # Calculate semantic similarity
                similarity = self._calculate_semantic_similarity(functions)
                if similarity > 0.6:  # Semantic similarity threshold
                    cluster = DuplicationCluster(
                        cluster_id=f"functional_{group_id}",
                        duplication_type="functional",
                        confidence=similarity,
                        files_involved=[f.file_path for f in functions],
                        similarity_score=similarity,
                        consolidation_recommendation=self._generate_functional_recommendation(functions),
                        impact_assessment=self._assess_functional_impact(functions)
                    )
                    clusters.append(cluster)
        
        return clusters
    
    def _detect_responsibility_overlap(self) -> List[DuplicationCluster]:
        """Detect overlapping responsibilities between modules."""
        clusters = []
        
        # Analyze module responsibilities based on function names and imports
        module_responsibilities = self._analyze_module_responsibilities()
        
        # Find overlapping responsibilities
        overlap_groups = self._find_responsibility_overlaps(module_responsibilities)
        
        for overlap_id, modules in overlap_groups.items():
            if len(modules) > 1:
                cluster = DuplicationCluster(
                    cluster_id=f"responsibility_{overlap_id}",
                    duplication_type="responsibility",
                    confidence=0.8,
                    files_involved=list(modules.keys()),
                    similarity_score=0.8,
                    consolidation_recommendation=self._generate_responsibility_recommendation(modules),
                    impact_assessment=self._assess_responsibility_impact(modules)
                )
                clusters.append(cluster)
        
        return clusters
    
    def _generate_consolidation_recommendations(self) -> List[Dict[str, Any]]:
        """Generate specific consolidation recommendations."""
        recommendations = []
        
        for cluster in self.duplication_clusters:
            if cluster.confidence > 0.7:  # High confidence clusters only
                recommendation = {
                    'cluster_id': cluster.cluster_id,
                    'priority': self._calculate_consolidation_priority(cluster),
                    'consolidation_strategy': self._determine_consolidation_strategy(cluster),
                    'estimated_effort': self._estimate_consolidation_effort(cluster),
                    'benefits': self._calculate_consolidation_benefits(cluster),
                    'risks': self._assess_consolidation_risks(cluster),
                    'implementation_steps': self._generate_implementation_steps(cluster)
                }
                recommendations.append(recommendation)
        
        # Sort by priority
        recommendations.sort(key=lambda x: x['priority'], reverse=True)
        return recommendations
    
    def _calculate_function_similarity(self, func1: FunctionSignature, func2: FunctionSignature) -> float:
        """Calculate similarity score between two functions."""
        score = 0.0
        
        # AST structure similarity (40% weight)
        if func1.ast_hash == func2.ast_hash:
            score += 0.4
        
        # Name similarity (20% weight)
        name_similarity = difflib.SequenceMatcher(None, func1.name, func2.name).ratio()
        score += name_similarity * 0.2
        
        # Parameter similarity (15% weight)
        param_similarity = difflib.SequenceMatcher(None, str(func1.parameters), str(func2.parameters)).ratio()
        score += param_similarity * 0.15
        
        # Complexity similarity (10% weight)
        complexity1 = func1.complexity_metrics.get('cyclomatic_complexity', 0)
        complexity2 = func2.complexity_metrics.get('cyclomatic_complexity', 0)
        if max(complexity1, complexity2) > 0:
            complexity_similarity = 1 - abs(complexity1 - complexity2) / max(complexity1, complexity2)
            score += complexity_similarity * 0.1
        
        # Import similarity (15% weight)
        common_imports = len(func1.imports_used & func2.imports_used)
        total_imports = len(func1.imports_used | func2.imports_used)
        if total_imports > 0:
            import_similarity = common_imports / total_imports
            score += import_similarity * 0.15
        
        return min(score, 1.0)
    
    def _calculate_ast_hash(self, node: ast.AST) -> str:
        """Calculate hash based on AST structure (ignoring variable names)."""
        # Simplified AST hash - normalize node types and structure
        node_types = []
        for child in ast.walk(node):
            node_types.append(type(child).__name__)
        
        structure_str = ''.join(node_types)
        return hashlib.md5(structure_str.encode()).hexdigest()
    
    def _calculate_cyclomatic_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity of a function."""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            # Decision points increase complexity
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor, 
                                ast.ExceptHandler, ast.With, ast.AsyncWith)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                # And/Or operators
                complexity += len(child.values) - 1
        
        return complexity
    
    def _calculate_nesting_depth(self, node: ast.FunctionDef) -> int:
        """Calculate maximum nesting depth in function."""
        def get_depth(node, current_depth=0):
            max_depth = current_depth
            for child in ast.iter_child_nodes(node):
                if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor, 
                                    ast.With, ast.AsyncWith, ast.Try)):
                    child_depth = get_depth(child, current_depth + 1)
                    max_depth = max(max_depth, child_depth)
                else:
                    child_depth = get_depth(child, current_depth)
                    max_depth = max(max_depth, child_depth)
            return max_depth
        
        return get_depth(node)
    
    def _find_files(self, root_path: str, patterns: List[str]) -> List[str]:
        """Find all files matching the given patterns."""
        files = []
        root = Path(root_path)
        
        for pattern in patterns:
            files.extend([str(p) for p in root.rglob(pattern) if p.is_file()])
        
        return files
    
    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    # Placeholder methods for JavaScript/C analysis
    def _analyze_javascript_file(self, file_path: str):
        """Analyze JavaScript/TypeScript file (placeholder)."""
        # TODO: Implement JavaScript AST analysis
        pass
    
    def _analyze_c_file(self, file_path: str):
        """Analyze C/C++ file (placeholder)."""
        # TODO: Implement C/C++ analysis  
        pass
    
    # Additional helper methods (simplified implementations)
    def _group_functions_by_semantics(self) -> Dict[str, List[FunctionSignature]]:
        """Group functions by semantic similarity."""
        # Simplified implementation
        return {}
    
    def _calculate_semantic_similarity(self, functions: List[FunctionSignature]) -> float:
        """Calculate semantic similarity score."""
        return 0.7  # Placeholder
    
    def _analyze_module_responsibilities(self) -> Dict[str, Dict[str, Any]]:
        """Analyze module responsibilities."""
        return {}  # Placeholder
    
    def _find_responsibility_overlaps(self, modules: Dict) -> Dict[str, Dict]:
        """Find overlapping responsibilities.""" 
        return {}  # Placeholder
    
    # Recommendation generation methods (simplified)
    def _generate_exact_dup_recommendation(self, functions: List[FunctionSignature]) -> str:
        return f"Consolidate {len(functions)} identical functions into shared module"
    
    def _assess_exact_dup_impact(self, functions: List[FunctionSignature]) -> str:
        return f"High impact: {len(functions)} exact duplicates found"
    
    def _generate_similarity_recommendation(self, func1, func2, similarity) -> str:
        return f"Consider merging similar functions (similarity: {similarity:.2f})"
    
    def _assess_similarity_impact(self, func1, func2) -> str:
        return "Medium impact: Similar functions detected"
    
    def _generate_functional_recommendation(self, functions) -> str:
        return "Consolidate functionally overlapping code"
    
    def _assess_functional_impact(self, functions) -> str:
        return "Medium impact: Functional overlap detected"
    
    def _generate_responsibility_recommendation(self, modules) -> str:
        return "Restructure modules to separate responsibilities"
    
    def _assess_responsibility_impact(self, modules) -> str:
        return "High impact: Responsibility overlap affects architecture"
    
    def _calculate_consolidation_priority(self, cluster) -> float:
        return cluster.confidence * len(cluster.files_involved)
    
    def _determine_consolidation_strategy(self, cluster) -> str:
        strategies = {
            'exact': 'Extract to shared utility module',
            'similar': 'Parameterize differences and merge',
            'functional': 'Create abstraction layer',
            'responsibility': 'Restructure module boundaries'
        }
        return strategies.get(cluster.duplication_type, 'Manual review required')
    
    def _estimate_consolidation_effort(self, cluster) -> str:
        effort_map = {
            'exact': 'Low',
            'similar': 'Medium', 
            'functional': 'High',
            'responsibility': 'High'
        }
        return effort_map.get(cluster.duplication_type, 'Unknown')
    
    def _calculate_consolidation_benefits(self, cluster) -> List[str]:
        return [
            'Reduced code duplication',
            'Improved maintainability', 
            'Consistent behavior across codebase',
            'Easier testing and debugging'
        ]
    
    def _assess_consolidation_risks(self, cluster) -> List[str]:
        return [
            'Potential breaking changes',
            'Need for comprehensive testing',
            'Temporary development disruption'
        ]
    
    def _generate_implementation_steps(self, cluster) -> List[str]:
        return [
            '1. Create comprehensive tests for existing functionality',
            '2. Extract common functionality to shared module',
            '3. Update all references to use consolidated code',
            '4. Run full test suite to verify no regressions',
            '5. Remove duplicate code'
        ]
    
    def _calculate_duplication_metrics(self) -> Dict[str, Any]:
        """Calculate overall duplication metrics."""
        total_functions = sum(len(funcs) for funcs in self.function_registry.values())
        total_duplicates = sum(len(cluster.files_involved) for cluster in self.duplication_clusters)
        
        return {
            'total_functions_analyzed': total_functions,
            'total_duplication_clusters': len(self.duplication_clusters),
            'total_files_with_duplicates': total_duplicates,
            'duplication_percentage': (total_duplicates / total_functions * 100) if total_functions > 0 else 0,
            'exact_duplicates': len([c for c in self.duplication_clusters if c.duplication_type == 'exact']),
            'similar_functions': len([c for c in self.duplication_clusters if c.duplication_type == 'similar']),
            'functional_overlaps': len([c for c in self.duplication_clusters if c.duplication_type == 'functional']),
            'responsibility_overlaps': len([c for c in self.duplication_clusters if c.duplication_type == 'responsibility'])
        }
    
    def _create_actionable_recommendations(self) -> List[Dict[str, Any]]:
        """Create prioritized actionable recommendations."""
        recommendations = []
        
        # High priority: Exact duplicates
        exact_clusters = [c for c in self.duplication_clusters if c.duplication_type == 'exact']
        if exact_clusters:
            recommendations.append({
                'priority': 'HIGH',
                'category': 'Exact Duplicates',
                'action': f'Consolidate {len(exact_clusters)} sets of identical functions',
                'estimated_effort': 'Low',
                'impact': 'High - Immediate maintainability improvement'
            })
        
        # Medium priority: Similar functions
        similar_clusters = [c for c in self.duplication_clusters if c.duplication_type == 'similar']
        if similar_clusters:
            recommendations.append({
                'priority': 'MEDIUM',
                'category': 'Similar Functions', 
                'action': f'Review and potentially merge {len(similar_clusters)} similar function groups',
                'estimated_effort': 'Medium',
                'impact': 'Medium - Code consistency improvement'
            })
        
        # Low priority: Responsibility overlaps
        responsibility_clusters = [c for c in self.duplication_clusters if c.duplication_type == 'responsibility']
        if responsibility_clusters:
            recommendations.append({
                'priority': 'LOW',
                'category': 'Architecture',
                'action': f'Consider restructuring {len(responsibility_clusters)} modules with overlapping responsibilities',
                'estimated_effort': 'High',
                'impact': 'High - Long-term architectural improvement'
            })
        
        return recommendations


def main():
    """Main function for standalone testing."""
    analyzer = MECEAnalyzer()
    results = analyzer.analyze_codebase(".", ["*.py"])
    
    print("=== MECE Analysis Results ===")
    print(json.dumps(results, indent=2, default=str))


if __name__ == "__main__":
    main()