#!/usr/bin/env python3
"""
Helper functions for duplication analysis integration.
"""

from typing import Any, Dict, List, Optional


def format_duplication_analysis(duplication_result: Optional[Any]) -> Dict[str, Any]:
    """Format duplication analysis result for core analyzer integration."""
    
    if not duplication_result or not duplication_result.success:
        return {
            'score': 1.0,  # Perfect score when no analysis or failed
            'violations': [],
            'summary': {
                'total_violations': 0,
                'similarity_violations': 0,
                'algorithm_violations': 0,
                'files_with_duplications': 0
            },
            'available': False,
            'error': getattr(duplication_result, 'error', None) if duplication_result else 'Duplication analyzer not available'
        }
    
    # Extract violations from duplication result
    all_violations = []
    
    # Add similarity violations
    for violation in duplication_result.similarity_violations:
        all_violations.append({
            'id': violation.violation_id,
            'type': 'similarity_duplication',
            'severity': violation.severity,
            'description': violation.description,
            'files_involved': violation.files_involved,
            'similarity_score': violation.similarity_score,
            'line_ranges': violation.line_ranges,
            'recommendation': violation.recommendation,
            'analysis_method': 'mece_similarity'
        })
    
    # Add algorithm violations
    for violation in duplication_result.algorithm_violations:
        all_violations.append({
            'id': violation.violation_id,
            'type': 'algorithm_duplication',
            'severity': violation.severity,
            'description': violation.description,
            'files_involved': violation.files_involved,
            'similarity_score': violation.similarity_score,
            'line_ranges': violation.line_ranges,
            'recommendation': violation.recommendation,
            'analysis_method': 'coa_algorithm'
        })
    
    return {
        'score': duplication_result.overall_duplication_score,
        'violations': all_violations,
        'summary': {
            'total_violations': duplication_result.total_violations,
            'similarity_violations': len(duplication_result.similarity_violations),
            'algorithm_violations': len(duplication_result.algorithm_violations),
            'files_with_duplications': duplication_result.summary.get('files_with_duplications', 0),
            'average_similarity': duplication_result.summary.get('average_similarity_score', 0.0),
            'priority_recommendation': duplication_result.summary.get('recommendation_priority', 'No action needed')
        },
        'available': True,
        'error': None,
        'threshold_used': getattr(duplication_result, 'similarity_threshold', 0.7),
        'analysis_methods': ['mece_similarity', 'coa_algorithm']
    }


def get_duplication_severity_counts(violations: List[Dict[str, Any]]) -> Dict[str, int]:
    """Count duplication violations by severity."""
    counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
    
    for violation in violations:
        severity = violation.get('severity', 'medium')
        if severity in counts:
            counts[severity] += 1
    
    return counts


def calculate_duplication_impact_score(violations: List[Dict[str, Any]]) -> float:
    """Calculate overall impact score for duplication violations."""
    if not violations:
        return 0.0
    
    severity_weights = {'critical': 1.0, 'high': 0.7, 'medium': 0.4, 'low': 0.2}
    
    total_impact = 0.0
    for violation in violations:
        severity = violation.get('severity', 'medium')
        similarity = violation.get('similarity_score', 0.5)
        files_count = len(violation.get('files_involved', []))
        
        # Calculate impact: severity * similarity * file_spread
        base_weight = severity_weights.get(severity, 0.4)
        file_multiplier = min(files_count / 2.0, 2.0)  # Cap at 2x for file spread
        
        violation_impact = base_weight * similarity * file_multiplier
        total_impact += violation_impact
    
    # Normalize to 0-1 scale (roughly)
    return min(total_impact / len(violations), 1.0)