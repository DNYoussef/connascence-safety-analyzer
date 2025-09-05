# SPDX-License-Identifier: MIT
"""
MECE (Mutually Exclusive, Collectively Exhaustive) duplication analyzer.
"""

import argparse
import json
import sys
import ast
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Tuple, Set
from collections import defaultdict
from dataclasses import dataclass

# Import constants
sys.path.insert(0, str(Path(__file__).parent.parent))
from constants import MECE_SIMILARITY_THRESHOLD, MECE_CLUSTER_MIN_SIZE

# Fixed: Import ConnascenceViolation from utils instead of missing mcp.server
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
try:
    from utils.config_loader import ConnascenceViolation
except ImportError:
    # Fallback for environments where utils is not available
    from dataclasses import dataclass
    
    @dataclass
    class ConnascenceViolation:
        """Fallback ConnascenceViolation class for MECE analysis."""
        violation_type: str
        severity: str
        description: str
        file_path: str
        line_number: int = 0
        column_number: int = 0


@dataclass
class CodeBlock:
    """Represents a block of code for similarity analysis."""
    file_path: str
    start_line: int
    end_line: int
    content: str
    normalized_content: str
    hash_signature: str

@dataclass
class DuplicationCluster:
    """Represents a cluster of similar code blocks."""
    id: str
    blocks: List[CodeBlock]
    similarity_score: float
    description: str

class MECEAnalyzer:
    """MECE duplication analyzer for detecting real code duplication and overlap."""
    
    def __init__(self, threshold: float = MECE_SIMILARITY_THRESHOLD):
        self.threshold = threshold
        self.min_lines = 3  # Minimum lines for a code block to be considered
        self.min_cluster_size = MECE_CLUSTER_MIN_SIZE
    
    def analyze(self, *args, **kwargs):
        """Legacy analyze method for backward compatibility."""
        return []
    
    def analyze_path(self, path: str, comprehensive: bool = False) -> Dict[str, Any]:
        """Analyze path for real MECE violations and duplications."""
        path_obj = Path(path)
        
        if not path_obj.exists():
            return {
                'success': False,
                'error': f"Path does not exist: {path}",
                'mece_score': 0.0,
                'duplications': []
            }
        
        try:
            # Extract code blocks from files
            code_blocks = self._extract_code_blocks(path_obj)
            
            # Find similar blocks
            clusters = self._find_duplication_clusters(code_blocks)
            
            # Convert clusters to output format
            duplications = [self._cluster_to_dict(cluster) for cluster in clusters]
            
            # Calculate MECE score
            mece_score = self._calculate_mece_score(code_blocks, clusters)
            
            return {
                'success': True,
                'path': str(path),
                'threshold': self.threshold,
                'comprehensive': comprehensive,
                'mece_score': mece_score,
                'duplications': duplications,
                'summary': {
                    'total_duplications': len(duplications),
                    'high_similarity_count': len([d for d in duplications if d['similarity_score'] > 0.8]),
                    'coverage_score': mece_score,
                    'files_analyzed': len(set(block.file_path for block in code_blocks)),
                    'blocks_analyzed': len(code_blocks)
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Analysis error: {str(e)}",
                'mece_score': 0.0,
                'duplications': []
            }
    
    def _extract_code_blocks(self, path_obj: Path) -> List[CodeBlock]:
        """Extract code blocks from Python files."""
        blocks = []
        
        if path_obj.is_file() and path_obj.suffix == '.py':
            blocks.extend(self._extract_blocks_from_file(path_obj))
        elif path_obj.is_dir():
            for py_file in path_obj.rglob('*.py'):
                if self._should_analyze_file(py_file):
                    blocks.extend(self._extract_blocks_from_file(py_file))
        
        return blocks
    
    def _extract_blocks_from_file(self, file_path: Path) -> List[CodeBlock]:
        """Extract code blocks (functions, classes) from a single file."""
        blocks = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.splitlines()
            
            tree = ast.parse(content)
            
            # Extract functions and methods
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    block = self._create_code_block_from_function(node, file_path, lines)
                    if block and self._is_significant_block(block):
                        blocks.append(block)
        
        except (SyntaxError, UnicodeDecodeError) as e:
            print(f"Warning: Could not parse {file_path}: {e}")
        
        return blocks
    
    def _create_code_block_from_function(self, node: ast.FunctionDef, file_path: Path, lines: List[str]) -> CodeBlock:
        """Create a code block from a function AST node."""
        start_line = node.lineno
        end_line = getattr(node, 'end_lineno', start_line + 10)
        
        # Extract content
        block_lines = lines[start_line-1:end_line]
        content = '\n'.join(block_lines)
        
        # Normalize content for similarity comparison
        normalized = self._normalize_code(content)
        
        # Create hash signature
        hash_sig = hashlib.md5(normalized.encode()).hexdigest()[:16]
        
        return CodeBlock(
            file_path=str(file_path),
            start_line=start_line,
            end_line=end_line,
            content=content,
            normalized_content=normalized,
            hash_signature=hash_sig
        )
    
    def _normalize_code(self, code: str) -> str:
        """Normalize code for similarity comparison."""
        # Remove comments and docstrings
        lines = []
        for line in code.split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                # Remove inline comments
                if '#' in line:
                    line = line.split('#')[0].strip()
                if line:
                    lines.append(line)
        
        # Join and normalize whitespace
        normalized = ' '.join(lines)
        normalized = ' '.join(normalized.split())  # Normalize whitespace
        
        return normalized
    
    def _is_significant_block(self, block: CodeBlock) -> bool:
        """Check if a code block is significant enough for analysis."""
        line_count = block.end_line - block.start_line + 1
        return line_count >= self.min_lines and len(block.normalized_content) > 50
    
    def _find_duplication_clusters(self, blocks: List[CodeBlock]) -> List[DuplicationCluster]:
        """Find clusters of similar code blocks."""
        clusters = []
        processed_blocks = set()
        
        for i, block1 in enumerate(blocks):
            if block1.hash_signature in processed_blocks:
                continue
                
            similar_blocks = [block1]
            
            for j, block2 in enumerate(blocks[i+1:], i+1):
                if block2.hash_signature in processed_blocks:
                    continue
                    
                similarity = self._calculate_similarity(block1, block2)
                
                if similarity >= self.threshold:
                    similar_blocks.append(block2)
            
            # Create cluster if we have enough similar blocks
            if len(similar_blocks) >= self.min_cluster_size:
                cluster_id = f"cluster_{len(clusters)+1}"
                avg_similarity = self._calculate_average_similarity(similar_blocks)
                
                description = f"Found {len(similar_blocks)} similar code blocks with {avg_similarity:.1%} average similarity"
                
                cluster = DuplicationCluster(
                    id=cluster_id,
                    blocks=similar_blocks,
                    similarity_score=avg_similarity,
                    description=description
                )
                
                clusters.append(cluster)
                
                # Mark blocks as processed
                for block in similar_blocks:
                    processed_blocks.add(block.hash_signature)
        
        return clusters
    
    def _calculate_similarity(self, block1: CodeBlock, block2: CodeBlock) -> float:
        """Calculate similarity between two code blocks."""
        # Don't compare blocks from the same file
        if block1.file_path == block2.file_path:
            return 0.0
        
        # Use normalized content for comparison
        content1 = block1.normalized_content
        content2 = block2.normalized_content
        
        # Simple similarity based on common words/tokens
        tokens1 = set(content1.split())
        tokens2 = set(content2.split())
        
        if not tokens1 or not tokens2:
            return 0.0
        
        intersection = len(tokens1 & tokens2)
        union = len(tokens1 | tokens2)
        
        return intersection / union if union > 0 else 0.0
    
    def _calculate_average_similarity(self, blocks: List[CodeBlock]) -> float:
        """Calculate average similarity within a group of blocks."""
        if len(blocks) < 2:
            return 1.0
        
        total_similarity = 0.0
        comparisons = 0
        
        for i, block1 in enumerate(blocks):
            for block2 in blocks[i+1:]:
                similarity = self._calculate_similarity(block1, block2)
                # For blocks in the same cluster, use their actual similarity
                if similarity == 0.0:  # Same file check failed, recalculate
                    tokens1 = set(block1.normalized_content.split())
                    tokens2 = set(block2.normalized_content.split())
                    if tokens1 and tokens2:
                        intersection = len(tokens1 & tokens2)
                        union = len(tokens1 | tokens2)
                        similarity = intersection / union if union > 0 else 0.0
                
                total_similarity += similarity
                comparisons += 1
        
        return total_similarity / comparisons if comparisons > 0 else 0.0
    
    def _calculate_mece_score(self, blocks: List[CodeBlock], clusters: List[DuplicationCluster]) -> float:
        """Calculate MECE score (higher is better, lower duplication)."""
        if not blocks:
            return 1.0
        
        # Count blocks involved in duplication
        duplicated_blocks = sum(len(cluster.blocks) for cluster in clusters)
        total_blocks = len(blocks)
        
        # Calculate score (1.0 = no duplications, 0.0 = all duplicated)
        duplication_ratio = duplicated_blocks / total_blocks
        mece_score = max(0.0, 1.0 - duplication_ratio)
        
        # Penalize high-similarity clusters more
        similarity_penalty = sum(
            cluster.similarity_score * len(cluster.blocks) / total_blocks
            for cluster in clusters
        )
        
        final_score = max(0.0, mece_score - (similarity_penalty * 0.5))
        return round(final_score, 3)
    
    def _cluster_to_dict(self, cluster: DuplicationCluster) -> Dict[str, Any]:
        """Convert duplication cluster to dictionary format."""
        return {
            'id': cluster.id,
            'similarity_score': round(cluster.similarity_score, 3),
            'block_count': len(cluster.blocks),
            'files_involved': list(set(block.file_path for block in cluster.blocks)),
            'blocks': [
                {
                    'file_path': block.file_path,
                    'start_line': block.start_line,
                    'end_line': block.end_line,
                    'lines': list(range(block.start_line, block.end_line + 1))
                }
                for block in cluster.blocks
            ],
            'description': cluster.description
        }
    
    def _should_analyze_file(self, file_path: Path) -> bool:
        """Check if a file should be analyzed."""
        # Skip test files, __pycache__, etc.
        skip_patterns = ['__pycache__', '.git', '.pytest_cache', 'test_', '_test.py']
        
        path_str = str(file_path)
        return not any(pattern in path_str for pattern in skip_patterns)


def main():
    """Main entry point for command-line usage."""
    parser = argparse.ArgumentParser(description="MECE duplication analyzer")
    parser.add_argument('--path', required=True, help='Path to analyze')
    parser.add_argument('--comprehensive', action='store_true', help='Run comprehensive analysis')
    parser.add_argument('--threshold', type=float, default=MECE_SIMILARITY_THRESHOLD, help='Similarity threshold')
    parser.add_argument('--exclude', nargs='*', default=[], help='Paths to exclude')
    parser.add_argument('--output', help='Output JSON file')
    
    args = parser.parse_args()
    
    try:
        analyzer = MECEAnalyzer(threshold=args.threshold)
        result = analyzer.analyze_path(args.path, comprehensive=args.comprehensive)
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(result, f, indent=2)
        else:
            print(json.dumps(result, indent=2))
        
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())


__all__ = ["MECEAnalyzer"]
