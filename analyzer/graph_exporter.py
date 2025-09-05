"""
Graph Exporter for Coupling Analysis and Hotspot Detection

Exports connascence analysis results as coupling graphs with:
- Node-edge representations of file/class/function relationships
- Weighted edges for connascence strength and type
- Hotspot ranking based on coupling × churn × test failures
- Multiple export formats (JSON, GEXF, GraphML)
- Integration with graph analysis tools

This enables sophisticated refactoring target identification and
architectural analysis based on actual coupling measurements.
"""

import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict
import hashlib
import math

@dataclass
class GraphNode:
    """Represents a node in the coupling graph"""
    id: str
    label: str
    node_type: str  # "file", "class", "function", "module"
    file_path: Optional[str] = None
    line_count: Optional[int] = None
    complexity: Optional[float] = None
    test_coverage: Optional[float] = None
    churn_rate: Optional[float] = None
    violation_count: int = 0
    nasa_violations: int = 0
    hotspot_score: Optional[float] = None

@dataclass
class GraphEdge:
    """Represents an edge (relationship) in the coupling graph"""
    source_id: str
    target_id: str
    edge_type: str  # connascence type: "name", "type", "meaning", etc.
    weight: float
    severity: str
    locality: str  # "same_function", "same_class", "same_module", "cross_module"
    line_references: List[Tuple[int, int]]  # (source_line, target_line) pairs

@dataclass
class CouplingGraph:
    """Complete coupling graph with metadata"""
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    metadata: Dict[str, Any]
    hotspots: List[Dict[str, Any]]
    statistics: Dict[str, float]

class GraphExporter:
    """
    Exports connascence analysis results as coupling graphs with hotspot analysis.
    """
    
    def __init__(self):
        self.connascence_weights = {
            'connascence_of_name': 1.0,
            'connascence_of_type': 1.2,
            'connascence_of_meaning': 1.5,
            'connascence_of_position': 2.0,
            'connascence_of_algorithm': 3.0,
            'connascence_of_execution': 2.5,
            'connascence_of_timing': 3.5,
            'connascence_of_value': 2.2,
            'connascence_of_identity': 4.0,
            'god_object': 5.0
        }
        
        self.locality_multipliers = {
            'same_function': 0.8,
            'same_class': 1.0,
            'same_module': 1.3,
            'cross_module': 2.0
        }
    
    def export_coupling_graph(self, analysis_results: Dict[str, Any],
                            churn_data: Optional[Dict[str, float]] = None,
                            test_data: Optional[Dict[str, Dict]] = None) -> CouplingGraph:
        """
        Export analysis results as a coupling graph.
        
        Args:
            analysis_results: Results from connascence analysis
            churn_data: Optional file churn rates (commits/time period)
            test_data: Optional test coverage and failure data
            
        Returns:
            CouplingGraph with nodes, edges, and hotspot analysis
        """
        
        # Extract nodes from analysis results
        nodes = self._extract_nodes(analysis_results, churn_data, test_data)
        
        # Extract edges (relationships) from violations
        edges = self._extract_edges(analysis_results, nodes)
        
        # Calculate hotspot scores
        hotspots = self._calculate_hotspots(nodes, edges)
        
        # Generate statistics
        statistics = self._generate_statistics(nodes, edges)
        
        # Create metadata
        metadata = {
            'export_timestamp': str(datetime.now()),
            'total_files_analyzed': len(set(v.get('file_path') for v in analysis_results.get('violations', []))),
            'total_violations': len(analysis_results.get('violations', [])),
            'graph_version': '1.0',
            'analysis_scope': analysis_results.get('scope', 'unknown')
        }
        
        return CouplingGraph(
            nodes=nodes,
            edges=edges,
            metadata=metadata,
            hotspots=hotspots,
            statistics=statistics
        )
    
    def _extract_nodes(self, analysis_results: Dict[str, Any],
                      churn_data: Optional[Dict[str, float]] = None,
                      test_data: Optional[Dict[str, Dict]] = None) -> List[GraphNode]:
        """Extract nodes from analysis results"""
        
        nodes_dict = {}
        violations = analysis_results.get('violations', [])
        
        # Create nodes from violations
        for violation in violations:
            file_path = violation.get('file_path', 'unknown')
            
            # File-level node
            file_id = self._generate_node_id('file', file_path)
            if file_id not in nodes_dict:
                nodes_dict[file_id] = GraphNode(
                    id=file_id,
                    label=Path(file_path).name,
                    node_type='file',
                    file_path=file_path,
                    line_count=self._get_line_count(file_path),
                    churn_rate=churn_data.get(file_path) if churn_data else None,
                    test_coverage=self._get_test_coverage(file_path, test_data),
                    violation_count=0,
                    nasa_violations=0
                )
            
            # Update violation counts
            nodes_dict[file_id].violation_count += 1
            if self._is_nasa_violation(violation):
                nodes_dict[file_id].nasa_violations += 1
            
            # Class-level node (if applicable)
            class_name = violation.get('class_name')
            if class_name:
                class_id = self._generate_node_id('class', f"{file_path}::{class_name}")
                if class_id not in nodes_dict:
                    nodes_dict[class_id] = GraphNode(
                        id=class_id,
                        label=class_name,
                        node_type='class',
                        file_path=file_path,
                        violation_count=0,
                        nasa_violations=0
                    )
                
                nodes_dict[class_id].violation_count += 1
                if self._is_nasa_violation(violation):
                    nodes_dict[class_id].nasa_violations += 1
            
            # Function-level node (if applicable)
            function_name = violation.get('function_name')
            if function_name:
                function_id = self._generate_node_id('function', f"{file_path}::{class_name or 'module'}::{function_name}")
                if function_id not in nodes_dict:
                    nodes_dict[function_id] = GraphNode(
                        id=function_id,
                        label=function_name,
                        node_type='function',
                        file_path=file_path,
                        complexity=violation.get('complexity'),
                        violation_count=0,
                        nasa_violations=0
                    )
                
                nodes_dict[function_id].violation_count += 1
                if self._is_nasa_violation(violation):
                    nodes_dict[function_id].nasa_violations += 1
        
        return list(nodes_dict.values())
    
    def _extract_edges(self, analysis_results: Dict[str, Any], nodes: List[GraphNode]) -> List[GraphEdge]:
        """Extract edges (relationships) from violations"""
        
        edges = []
        violations = analysis_results.get('violations', [])
        
        # Create a lookup for nodes by file/class/function
        node_lookup = {node.id: node for node in nodes}
        
        for violation in violations:
            # Create edges based on violation type and references
            violation_edges = self._create_violation_edges(violation, node_lookup)
            edges.extend(violation_edges)
        
        # Deduplicate and aggregate edges
        edges = self._aggregate_edges(edges)
        
        return edges
    
    def _create_violation_edges(self, violation: Dict[str, Any], node_lookup: Dict[str, GraphNode]) -> List[GraphEdge]:
        """Create edges for a specific violation"""
        
        edges = []
        violation_type = violation.get('type', 'unknown')
        file_path = violation.get('file_path', 'unknown')
        
        # Get base weight for this violation type
        base_weight = self.connascence_weights.get(violation_type, 1.0)
        
        # Determine locality
        locality = self._determine_locality(violation)
        locality_multiplier = self.locality_multipliers.get(locality, 1.0)
        
        # Calculate final weight
        final_weight = base_weight * locality_multiplier
        
        # Create edges based on violation context
        if violation_type == 'god_object':
            # God objects create internal coupling edges
            class_name = violation.get('class_name', 'unknown')
            class_id = self._generate_node_id('class', f"{file_path}::{class_name}")
            
            # Self-referencing edge for god object
            edges.append(GraphEdge(
                source_id=class_id,
                target_id=class_id,
                edge_type=violation_type,
                weight=final_weight,
                severity=violation.get('severity', 'medium'),
                locality=locality,
                line_references=[(violation.get('line_number', 0), violation.get('line_number', 0))]
            ))
        
        elif 'references' in violation:
            # Handle violations with explicit references
            source_id = self._get_node_id_for_location(violation, node_lookup)
            
            for ref in violation['references']:
                target_id = self._get_node_id_for_reference(ref, node_lookup)
                if source_id and target_id and source_id != target_id:
                    edges.append(GraphEdge(
                        source_id=source_id,
                        target_id=target_id,
                        edge_type=violation_type,
                        weight=final_weight,
                        severity=violation.get('severity', 'medium'),
                        locality=locality,
                        line_references=[(
                            violation.get('line_number', 0),
                            ref.get('line_number', 0)
                        )]
                    ))
        
        else:
            # Generic violation - create file-level edge
            file_id = self._generate_node_id('file', file_path)
            edges.append(GraphEdge(
                source_id=file_id,
                target_id=file_id,
                edge_type=violation_type,
                weight=final_weight,
                severity=violation.get('severity', 'medium'),
                locality=locality,
                line_references=[(violation.get('line_number', 0), violation.get('line_number', 0))]
            ))
        
        return edges
    
    def _aggregate_edges(self, edges: List[GraphEdge]) -> List[GraphEdge]:
        """Aggregate duplicate edges by summing weights"""
        
        edge_map = {}
        
        for edge in edges:
            key = (edge.source_id, edge.target_id, edge.edge_type)
            
            if key in edge_map:
                existing = edge_map[key]
                existing.weight += edge.weight
                existing.line_references.extend(edge.line_references)
            else:
                edge_map[key] = edge
        
        return list(edge_map.values())
    
    def _calculate_hotspots(self, nodes: List[GraphNode], edges: List[GraphEdge]) -> List[Dict[str, Any]]:
        """Calculate hotspot scores for refactoring prioritization"""
        
        hotspots = []
        
        # Create coupling strength map
        coupling_map = defaultdict(float)
        for edge in edges:
            coupling_map[edge.source_id] += edge.weight
            if edge.source_id != edge.target_id:
                coupling_map[edge.target_id] += edge.weight * 0.5  # Incoming coupling weight
        
        for node in nodes:
            if node.node_type in ['file', 'class']:  # Focus on higher-level hotspots
                
                # Coupling score (normalized)
                coupling_score = coupling_map.get(node.id, 0.0)
                
                # Churn score (higher churn = more volatile)
                churn_score = node.churn_rate or 0.0
                
                # Test failure risk (lower coverage = higher risk)
                test_risk_score = 1.0 - (node.test_coverage or 0.5)
                
                # Complexity score
                complexity_score = node.complexity or 1.0
                
                # NASA violations weight (safety-critical)
                nasa_weight = 2.0 if node.nasa_violations > 0 else 1.0
                
                # Calculate hotspot score using weighted formula
                hotspot_score = (
                    coupling_score * 0.4 +
                    churn_score * 0.3 +
                    test_risk_score * 0.2 +
                    math.log(complexity_score + 1) * 0.1
                ) * nasa_weight
                
                node.hotspot_score = hotspot_score
                
                hotspots.append({
                    'node_id': node.id,
                    'label': node.label,
                    'file_path': node.file_path,
                    'node_type': node.node_type,
                    'hotspot_score': hotspot_score,
                    'coupling_score': coupling_score,
                    'churn_rate': churn_score,
                    'test_risk': test_risk_score,
                    'complexity': complexity_score,
                    'violation_count': node.violation_count,
                    'nasa_violations': node.nasa_violations,
                    'priority': self._classify_priority(hotspot_score)
                })
        
        # Sort by hotspot score (highest first)
        hotspots.sort(key=lambda x: x['hotspot_score'], reverse=True)
        
        return hotspots
    
    def _generate_statistics(self, nodes: List[GraphNode], edges: List[GraphEdge]) -> Dict[str, float]:
        """Generate graph statistics"""
        
        total_nodes = len(nodes)
        total_edges = len(edges)
        
        # Node type distribution
        node_types = defaultdict(int)
        for node in nodes:
            node_types[node.node_type] += 1
        
        # Edge type distribution
        edge_types = defaultdict(int)
        total_weight = 0.0
        for edge in edges:
            edge_types[edge.edge_type] += 1
            total_weight += edge.weight
        
        # Calculate density
        max_edges = total_nodes * (total_nodes - 1)
        density = total_edges / max_edges if max_edges > 0 else 0.0
        
        # Calculate average coupling strength
        avg_coupling = total_weight / total_edges if total_edges > 0 else 0.0
        
        # NASA violations statistics
        nasa_violation_nodes = sum(1 for node in nodes if node.nasa_violations > 0)
        nasa_violation_rate = nasa_violation_nodes / total_nodes if total_nodes > 0 else 0.0
        
        return {
            'total_nodes': total_nodes,
            'total_edges': total_edges,
            'graph_density': density,
            'average_coupling_strength': avg_coupling,
            'nasa_violation_rate': nasa_violation_rate,
            'file_nodes': node_types['file'],
            'class_nodes': node_types['class'],
            'function_nodes': node_types['function'],
            'most_common_edge_type': max(edge_types.items(), key=lambda x: x[1])[0] if edge_types else 'none'
        }
    
    # Export format methods
    
    def export_to_json(self, graph: CouplingGraph, output_path: str) -> None:
        """Export graph to JSON format"""
        
        graph_dict = {
            'metadata': graph.metadata,
            'statistics': graph.statistics,
            'nodes': [asdict(node) for node in graph.nodes],
            'edges': [asdict(edge) for edge in graph.edges],
            'hotspots': graph.hotspots
        }
        
        with open(output_path, 'w') as f:
            json.dump(graph_dict, f, indent=2, default=str)
    
    def export_to_gexf(self, graph: CouplingGraph, output_path: str) -> None:
        """Export graph to GEXF format (Gephi compatible)"""
        
        # Create GEXF XML structure
        gexf = ET.Element('gexf')
        gexf.set('xmlns', 'http://www.gexf.net/1.2draft')
        gexf.set('version', '1.2')
        
        meta = ET.SubElement(gexf, 'meta')
        ET.SubElement(meta, 'creator').text = 'Connascence Safety Analyzer'
        ET.SubElement(meta, 'description').text = 'Coupling graph from connascence analysis'
        
        graph_elem = ET.SubElement(gexf, 'graph')
        graph_elem.set('mode', 'static')
        graph_elem.set('defaultedgetype', 'directed')
        
        # Node attributes
        attributes_elem = ET.SubElement(graph_elem, 'attributes')
        attributes_elem.set('class', 'node')
        
        attr_defs = [
            ('node_type', 'string'),
            ('violation_count', 'integer'),
            ('nasa_violations', 'integer'),
            ('hotspot_score', 'double'),
            ('churn_rate', 'double'),
            ('test_coverage', 'double')
        ]
        
        for attr_id, (attr_name, attr_type) in enumerate(attr_defs):
            attr_elem = ET.SubElement(attributes_elem, 'attribute')
            attr_elem.set('id', str(attr_id))
            attr_elem.set('title', attr_name)
            attr_elem.set('type', attr_type)
        
        # Nodes
        nodes_elem = ET.SubElement(graph_elem, 'nodes')
        for node in graph.nodes:
            node_elem = ET.SubElement(nodes_elem, 'node')
            node_elem.set('id', node.id)
            node_elem.set('label', node.label)
            
            # Node attributes
            attvalues = ET.SubElement(node_elem, 'attvalues')
            attrs = [
                (0, node.node_type),
                (1, str(node.violation_count)),
                (2, str(node.nasa_violations)),
                (3, str(node.hotspot_score or 0.0)),
                (4, str(node.churn_rate or 0.0)),
                (5, str(node.test_coverage or 0.0))
            ]
            
            for attr_id, value in attrs:
                attvalue = ET.SubElement(attvalues, 'attvalue')
                attvalue.set('for', str(attr_id))
                attvalue.set('value', value)
        
        # Edges
        edges_elem = ET.SubElement(graph_elem, 'edges')
        for edge_id, edge in enumerate(graph.edges):
            edge_elem = ET.SubElement(edges_elem, 'edge')
            edge_elem.set('id', str(edge_id))
            edge_elem.set('source', edge.source_id)
            edge_elem.set('target', edge.target_id)
            edge_elem.set('weight', str(edge.weight))
            edge_elem.set('label', edge.edge_type)
        
        # Write to file
        tree = ET.ElementTree(gexf)
        tree.write(output_path, encoding='utf-8', xml_declaration=True)
    
    # Helper methods
    
    def _generate_node_id(self, node_type: str, identifier: str) -> str:
        """Generate unique node ID"""
        return f"{node_type}_{hashlib.md5(identifier.encode()).hexdigest()[:8]}"
    
    def _get_line_count(self, file_path: str) -> Optional[int]:
        """Get line count for a file"""
        try:
            with open(file_path, 'r') as f:
                return len(f.readlines())
        except:
            return None
    
    def _get_test_coverage(self, file_path: str, test_data: Optional[Dict]) -> Optional[float]:
        """Get test coverage for a file"""
        if test_data and file_path in test_data:
            return test_data[file_path].get('coverage', None)
        return None
    
    def _is_nasa_violation(self, violation: Dict[str, Any]) -> bool:
        """Check if violation relates to NASA Power of Ten rules"""
        nasa_types = {
            'god_object', 'unbounded_loop', 'dynamic_allocation',
            'large_function', 'deep_nesting', 'global_data',
            'unchecked_return', 'complex_expressions'
        }
        return violation.get('type') in nasa_types
    
    def _determine_locality(self, violation: Dict[str, Any]) -> str:
        """Determine locality of a violation"""
        # This would be enhanced with actual scope analysis
        if violation.get('function_name'):
            return 'same_function'
        elif violation.get('class_name'):
            return 'same_class'
        elif violation.get('file_path'):
            return 'same_module'
        else:
            return 'cross_module'
    
    def _get_node_id_for_location(self, violation: Dict[str, Any], node_lookup: Dict) -> Optional[str]:
        """Get node ID for violation location"""
        file_path = violation.get('file_path')
        class_name = violation.get('class_name')
        function_name = violation.get('function_name')
        
        if function_name and class_name:
            return self._generate_node_id('function', f"{file_path}::{class_name}::{function_name}")
        elif class_name:
            return self._generate_node_id('class', f"{file_path}::{class_name}")
        elif file_path:
            return self._generate_node_id('file', file_path)
        return None
    
    def _get_node_id_for_reference(self, ref: Dict[str, Any], node_lookup: Dict) -> Optional[str]:
        """Get node ID for a reference"""
        return self._get_node_id_for_location(ref, node_lookup)
    
    def _classify_priority(self, hotspot_score: float) -> str:
        """Classify hotspot priority level"""
        if hotspot_score >= 5.0:
            return 'critical'
        elif hotspot_score >= 3.0:
            return 'high'
        elif hotspot_score >= 1.5:
            return 'medium'
        else:
            return 'low'


# Convenience function for external use
def export_connascence_graph(analysis_results: Dict[str, Any],
                           output_path: str,
                           format: str = 'json',
                           churn_data: Optional[Dict[str, float]] = None,
                           test_data: Optional[Dict[str, Dict]] = None) -> CouplingGraph:
    """
    Export connascence analysis as a coupling graph.
    
    Args:
        analysis_results: Results from connascence analysis
        output_path: Path to save the graph
        format: Export format ('json', 'gexf')
        churn_data: Optional churn rate data
        test_data: Optional test coverage data
        
    Returns:
        CouplingGraph object
    """
    from datetime import datetime
    
    exporter = GraphExporter()
    graph = exporter.export_coupling_graph(analysis_results, churn_data, test_data)
    
    if format.lower() == 'json':
        exporter.export_to_json(graph, output_path)
    elif format.lower() == 'gexf':
        exporter.export_to_gexf(graph, output_path)
    else:
        raise ValueError(f"Unsupported format: {format}")
    
    return graph


if __name__ == "__main__":
    # Example usage
    sample_results = {
        'violations': [
            {
                'type': 'magic_literal',
                'file_path': 'src/handlers.py',
                'line_number': 42,
                'severity': 'medium',
                'class_name': 'RequestHandler',
                'function_name': 'handle_request'
            },
            {
                'type': 'god_object',
                'file_path': 'src/user_manager.py',
                'line_number': 1,
                'severity': 'critical',
                'class_name': 'UserManager'
            }
        ],
        'scope': 'src/'
    }
    
    graph = export_connascence_graph(sample_results, 'coupling_graph.json')
    
    print(f"Exported graph with {len(graph.nodes)} nodes and {len(graph.edges)} edges")
    print(f"Top hotspot: {graph.hotspots[0]['label'] if graph.hotspots else 'None'}")
    print(f"Graph density: {graph.statistics['graph_density']:.3f}")