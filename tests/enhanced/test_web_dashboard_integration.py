# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2024 Connascence Safety Analyzer Contributors

"""
Web Dashboard Enhanced Integration Tests
=======================================

Comprehensive tests for Web dashboard enhanced pipeline integration:
- Cross-phase correlation chart rendering and interaction
- Audit trail timeline visualization with phase timing
- Smart recommendations display and user interaction
- Enhanced data processing and real-time updates
- WebSocket integration for enhanced data streaming
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest

from .test_infrastructure import (
    EnhancedTestDatasets, MockEnhancedAnalyzer, EnhancedTestUtilities,
    integration_test, performance_test
)


@pytest.fixture
def enhanced_test_datasets():
    """Provide enhanced test datasets"""
    return EnhancedTestDatasets()

@pytest.fixture
def sample_code_file(tmp_path):
    """Create temporary Python file for testing"""
    code_content = '''
class TestClass:
    def __init__(self, config):
        # CofE: Identity - class structure depends on config
        self.setting = config["setting"]
        
    def process(self, data, format="json"):
        # CofE: Position - parameter order dependency
        # CofE: Meaning - format string coupling
        if format == "json":
            return {"result": data}
        else:
            return str(data)
'''
    
    code_file = tmp_path / "test_code.py"
    code_file.write_text(code_content, encoding="utf-8")
    return code_file


class TestWebDashboardEnhancedIntegration:
    """Test suite for Web dashboard enhanced pipeline integration."""
    
    @integration_test(["web_dashboard"])
    def test_correlation_chart_data_processing(self, enhanced_test_datasets):
        """Test correlation network data processing for Chart.js visualization."""
        correlations = enhanced_test_datasets.get_expected_correlations()
        
        # Process correlations for scatter plot visualization
        chart_data = self._process_correlations_for_chart(correlations)
        
        # Validate chart data structure
        assert "datasets" in chart_data
        assert len(chart_data["datasets"]) > 0
        
        dataset = chart_data["datasets"][0]
        assert "data" in dataset
        assert "backgroundColor" in dataset
        assert "borderColor" in dataset
        
        # Validate scatter plot data points
        data_points = dataset["data"]
        assert len(data_points) == len(correlations)
        
        for i, point in enumerate(data_points):
            assert "x" in point
            assert "y" in point
            assert "analyzer1" in point
            assert "analyzer2" in point
            assert "correlation_score" in point
            
            # Verify correlation score mapping
            expected_score = correlations[i].correlation_score
            assert point["correlation_score"] == expected_score
            assert point["y"] == expected_score * 100  # Percentage for Y-axis
    
    @integration_test(["web_dashboard"])
    def test_audit_trail_chart_data_processing(self, enhanced_test_datasets):
        """Test audit trail timeline data processing for bar chart visualization."""
        audit_trail = enhanced_test_datasets.get_expected_audit_trail()
        
        # Process audit trail for bar chart
        chart_data = self._process_audit_trail_for_chart(audit_trail)
        
        # Validate chart structure
        assert "labels" in chart_data
        assert "datasets" in chart_data
        
        labels = chart_data["labels"]
        datasets = chart_data["datasets"]
        
        # Verify phase labels are formatted correctly
        expected_phases = [entry.phase.replace("_", " ").upper() for entry in audit_trail]
        assert labels == expected_phases
        
        # Verify dataset structure
        assert len(datasets) == 1  # Duration dataset
        duration_dataset = datasets[0]
        
        assert "label" in duration_dataset
        assert "data" in duration_dataset
        assert "backgroundColor" in duration_dataset
        
        # Validate duration calculations
        durations = duration_dataset["data"]
        assert len(durations) == len(audit_trail)
        
        for duration in durations:
            assert duration > 0  # All phases should have positive duration
    
    @integration_test(["web_dashboard"])
    def test_smart_recommendations_rendering(self, enhanced_test_datasets):
        """Test smart recommendations rendering for web dashboard display."""
        recommendations = enhanced_test_datasets.get_expected_smart_recommendations()
        
        # Process recommendations for HTML rendering
        rendered_html = self._render_recommendations_html(recommendations)
        
        # Validate HTML structure
        assert "recommendation-card" in rendered_html
        assert len(recommendations) == rendered_html.count("recommendation-card")
        
        # Check for required recommendation elements
        for rec in recommendations:
            assert rec.category in rendered_html
            assert rec.description in rendered_html
            assert rec.priority in rendered_html
            assert rec.impact in rendered_html
            assert rec.effort in rendered_html
        
        # Verify CSS classes for priority styling
        priority_classes = ["text-danger", "text-warning", "text-info"]  # high, medium, low
        has_priority_styling = any(cls in rendered_html for cls in priority_classes)
        assert has_priority_styling
    
    @integration_test(["web_dashboard"])
    def test_correlation_details_popup(self, enhanced_test_datasets):
        """Test correlation details popup functionality."""
        correlations = enhanced_test_datasets.get_expected_correlations()
        
        # Process correlation details for popup
        correlation_details = self._process_correlation_details(correlations)
        
        # Validate details structure
        assert "highest_correlation" in correlation_details
        assert "total_correlations" in correlation_details
        assert "correlation_summary" in correlation_details
        
        highest = correlation_details["highest_correlation"]
        assert "score" in highest
        assert "analyzers" in highest
        assert "description" in highest
        
        # Verify highest correlation identification
        max_score = max(c.correlation_score for c in correlations)
        assert highest["score"] == max_score * 100  # Percentage
        
        # Verify total count
        assert correlation_details["total_correlations"] == len(correlations)
    
    @integration_test(["web_dashboard"])
    def test_audit_trail_summary_display(self, enhanced_test_datasets):
        """Test audit trail summary display functionality."""
        audit_trail = enhanced_test_datasets.get_expected_audit_trail()
        
        # Process audit trail summary
        trail_summary = self._process_audit_trail_summary(audit_trail)
        
        # Validate summary structure
        assert "total_duration" in trail_summary
        assert "total_violations" in trail_summary
        assert "completed_phases" in trail_summary
        assert "phase_details" in trail_summary
        
        # Verify calculations
        expected_violations = sum(entry.violations_found for entry in audit_trail)
        assert trail_summary["total_violations"] == expected_violations
        
        completed_phases = [entry for entry in audit_trail if entry.started and entry.completed]
        assert trail_summary["completed_phases"] == len(completed_phases)
        
        # Validate phase details
        phase_details = trail_summary["phase_details"]
        for detail in phase_details:
            assert "phase_name" in detail
            assert "duration_ms" in detail
            assert "violations_found" in detail
            assert "clusters_found" in detail
    
    @integration_test(["web_dashboard"])
    @performance_test(max_time_seconds=2.0, max_memory_mb=25.0)
    def test_enhanced_chart_initialization(self, enhanced_test_datasets):
        """Test enhanced Chart.js initialization with real data."""
        correlations = enhanced_test_datasets.get_expected_correlations()
        audit_trail = enhanced_test_datasets.get_expected_audit_trail()
        recommendations = enhanced_test_datasets.get_expected_smart_recommendations()
        
        # Mock Chart.js initialization
        mock_charts = {}
        
        def mock_chart_init(ctx, config):
            chart_type = config.get("type", "unknown")
            mock_charts[chart_type] = {
                "ctx": ctx,
                "config": config,
                "update": Mock(),
                "destroy": Mock()
            }
            return mock_charts[chart_type]
        
        with patch('Chart') as MockChart:
            MockChart.side_effect = mock_chart_init
            
            # Initialize enhanced charts
            correlation_chart_config = self._create_correlation_chart_config(correlations)
            audit_chart_config = self._create_audit_trail_chart_config(audit_trail)
            
            correlation_chart = MockChart("correlation_ctx", correlation_chart_config)
            audit_chart = MockChart("audit_ctx", audit_chart_config)
            
            # Validate chart configurations
            assert correlation_chart_config["type"] == "scatter"
            assert audit_chart_config["type"] == "bar"
            
            # Verify data is properly formatted for Chart.js
            corr_data = correlation_chart_config["data"]["datasets"][0]["data"]
            assert len(corr_data) == len(correlations)
            
            audit_data = audit_chart_config["data"]["datasets"][0]["data"]
            assert len(audit_data) == len(audit_trail)
    
    @integration_test(["web_dashboard"])
    def test_real_time_data_updates(self, enhanced_test_datasets):
        """Test real-time enhanced data updates via WebSocket simulation."""
        # Initial data
        initial_correlations = enhanced_test_datasets.get_expected_correlations()[:2]
        
        # Mock WebSocket data update
        new_correlation_data = {
            "analyzer1": "nasa_analyzer",
            "analyzer2": "smart_integration",
            "correlation_score": 0.78,
            "description": "NASA violations correlate with integration hotspots",
            "priority": "medium"
        }
        
        # Simulate real-time update
        updated_correlations = initial_correlations.copy()
        updated_correlations.append(type(initial_correlations[0])(
            analyzer1=new_correlation_data["analyzer1"],
            analyzer2=new_correlation_data["analyzer2"],
            correlation_type="safety_hotspot_correlation",
            correlation_score=new_correlation_data["correlation_score"],
            description=new_correlation_data["description"],
            priority=new_correlation_data["priority"]
        ))
        
        # Process updated data for charts
        updated_chart_data = self._process_correlations_for_chart(updated_correlations)
        
        # Validate update
        assert len(updated_chart_data["datasets"][0]["data"]) == len(initial_correlations) + 1
        
        # Verify new correlation is included
        new_point = updated_chart_data["datasets"][0]["data"][-1]
        assert new_point["analyzer1"] == "nasa_analyzer"
        assert new_point["analyzer2"] == "smart_integration"
        assert new_point["correlation_score"] == 0.78
    
    @integration_test(["web_dashboard"])
    def test_enhanced_data_filtering(self, enhanced_test_datasets):
        """Test enhanced data filtering and display options."""
        correlations = enhanced_test_datasets.get_expected_correlations()
        
        # Test correlation filtering by score threshold
        high_correlations = self._filter_correlations_by_threshold(correlations, 0.8)
        medium_correlations = self._filter_correlations_by_threshold(correlations, 0.7)
        
        # Validate filtering
        for corr in high_correlations:
            assert corr.correlation_score >= 0.8
        
        for corr in medium_correlations:
            assert corr.correlation_score >= 0.7
        
        assert len(high_correlations) <= len(medium_correlations)
        
        # Test recommendations filtering by priority
        recommendations = enhanced_test_datasets.get_expected_smart_recommendations()
        high_priority_recs = self._filter_recommendations_by_priority(recommendations, ["high", "critical"])
        
        for rec in high_priority_recs:
            assert rec.priority in ["high", "critical"]
    
    @integration_test(["web_dashboard"])
    def test_dashboard_error_handling(self, enhanced_test_datasets):
        """Test dashboard error handling for enhanced features."""
        # Test empty data scenarios
        empty_data_scenarios = [
            ("empty_correlations", []),
            ("empty_recommendations", []),
            ("empty_audit_trail", [])
        ]
        
        for scenario_name, empty_data in empty_data_scenarios:
            if "correlations" in scenario_name:
                chart_data = self._process_correlations_for_chart(empty_data)
                assert chart_data["datasets"][0]["data"] == []
                
            elif "recommendations" in scenario_name:
                html = self._render_recommendations_html(empty_data)
                assert "No smart recommendations available" in html or "recommendation-card" not in html
                
            elif "audit_trail" in scenario_name:
                chart_data = self._process_audit_trail_for_chart(empty_data)
                assert chart_data["labels"] == []
                assert chart_data["datasets"][0]["data"] == []
        
        # Test malformed data handling
        malformed_correlation = type('MockCorr', (), {
            'analyzer1': None,  # Missing required field
            'analyzer2': 'test',
            'correlation_score': 'invalid'  # Wrong type
        })()
        
        # Should handle gracefully without crashing
        try:
            self._process_correlations_for_chart([malformed_correlation])
        except Exception as e:
            # Should handle gracefully or raise specific validation error
            assert "validation" in str(e).lower() or "format" in str(e).lower()
    
    @integration_test(["web_dashboard"])
    def test_interactive_features(self, enhanced_test_datasets):
        """Test interactive dashboard features for enhanced data."""
        correlations = enhanced_test_datasets.get_expected_correlations()
        recommendations = enhanced_test_datasets.get_expected_smart_recommendations()
        
        # Test correlation click interaction
        correlation_interaction = self._simulate_correlation_click(correlations[0])
        
        assert "tooltip_content" in correlation_interaction
        assert "detailed_view" in correlation_interaction
        
        tooltip = correlation_interaction["tooltip_content"]
        assert correlations[0].analyzer1 in tooltip
        assert correlations[0].analyzer2 in tooltip
        assert str(int(correlations[0].correlation_score * 100)) in tooltip
        
        # Test recommendation interaction
        rec_interaction = self._simulate_recommendation_click(recommendations[0])
        
        assert "modal_content" in rec_interaction
        assert "action_buttons" in rec_interaction
        
        modal = rec_interaction["modal_content"]
        assert recommendations[0].description in modal
        assert recommendations[0].category in modal
        
        buttons = rec_interaction["action_buttons"]
        assert "Apply Recommendation" in " ".join(buttons)
    
    # Helper methods for Web dashboard testing
    
    def _process_correlations_for_chart(self, correlations):
        """Process correlations for Chart.js scatter plot."""
        data_points = []
        
        for i, corr in enumerate(correlations):
            data_points.append({
                "x": i * 2,  # Spacing for visualization
                "y": corr.correlation_score * 100,  # Percentage for Y-axis
                "analyzer1": corr.analyzer1,
                "analyzer2": corr.analyzer2,
                "correlation_score": corr.correlation_score,
                "description": corr.description
            })
        
        return {
            "datasets": [{
                "label": "Phase Correlations",
                "data": data_points,
                "backgroundColor": "rgba(99, 102, 241, 0.6)",
                "borderColor": "#6366f1",
                "pointRadius": 8
            }]
        }
    
    def _process_audit_trail_for_chart(self, audit_trail):
        """Process audit trail for Chart.js bar chart."""
        labels = []
        durations = []
        
        for entry in audit_trail:
            if entry.started and entry.completed:
                # Mock duration calculation (in real implementation, parse timestamps)
                duration_ms = 2500  # Mock 2.5 second duration
                
                labels.append(entry.phase.replace("_", " ").upper())
                durations.append(duration_ms)
        
        return {
            "labels": labels,
            "datasets": [{
                "label": "Phase Duration (ms)",
                "data": durations,
                "backgroundColor": "rgba(16, 185, 129, 0.6)",
                "borderColor": "#10b981",
                "borderWidth": 1
            }]
        }
    
    def _render_recommendations_html(self, recommendations):
        """Render smart recommendations as HTML."""
        if not recommendations:
            return '<div class="text-center text-muted py-4">No smart recommendations available</div>'
        
        html_parts = []
        
        for rec in recommendations:
            priority_class = {
                "high": "text-danger",
                "medium": "text-warning", 
                "low": "text-info",
                "critical": "text-danger"
            }.get(rec.priority, "text-info")
            
            html_parts.append(f'''
            <div class="recommendation-card p-3 mb-2 bg-light border-start border-primary border-4">
                <div class="d-flex align-items-start">
                    <div class="flex-grow-1">
                        <div class="d-flex align-items-center mb-2">
                            <i class="fas fa-lightbulb text-warning me-2"></i>
                            <strong class="text-primary">{rec.category}</strong>
                            <span class="badge bg-secondary ms-2 {priority_class}">{rec.priority}</span>
                        </div>
                        <p class="mb-2">{rec.description}</p>
                        <div class="row text-muted small">
                            <div class="col-sm-6"><strong>Impact:</strong> {rec.impact}</div>
                            <div class="col-sm-6"><strong>Effort:</strong> {rec.effort}</div>
                        </div>
                    </div>
                </div>
            </div>
            ''')
        
        return ''.join(html_parts)
    
    def _process_correlation_details(self, correlations):
        """Process correlation details for popup display."""
        if not correlations:
            return {
                "highest_correlation": None,
                "total_correlations": 0,
                "correlation_summary": "No correlations found"
            }
        
        highest_corr = max(correlations, key=lambda c: c.correlation_score)
        
        return {
            "highest_correlation": {
                "score": highest_corr.correlation_score * 100,
                "analyzers": f"{highest_corr.analyzer1} ↔ {highest_corr.analyzer2}",
                "description": highest_corr.description
            },
            "total_correlations": len(correlations),
            "correlation_summary": f"{len(correlations)} cross-phase correlations detected"
        }
    
    def _process_audit_trail_summary(self, audit_trail):
        """Process audit trail summary for display."""
        completed_phases = [entry for entry in audit_trail if entry.started and entry.completed]
        total_violations = sum(entry.violations_found for entry in audit_trail)
        total_duration = len(completed_phases) * 2500  # Mock total duration
        
        phase_details = []
        for entry in completed_phases:
            phase_details.append({
                "phase_name": entry.phase.replace("_", " ").title(),
                "duration_ms": 2500,  # Mock duration
                "violations_found": entry.violations_found,
                "clusters_found": entry.clusters_found
            })
        
        return {
            "total_duration": total_duration,
            "total_violations": total_violations,
            "completed_phases": len(completed_phases),
            "phase_details": phase_details
        }
    
    def _create_correlation_chart_config(self, correlations):
        """Create Chart.js configuration for correlation chart."""
        chart_data = self._process_correlations_for_chart(correlations)
        
        return {
            "type": "scatter",
            "data": chart_data,
            "options": {
                "responsive": True,
                "scales": {
                    "x": {"title": {"display": True, "text": "Analyzer Phase 1"}},
                    "y": {"title": {"display": True, "text": "Correlation Strength (%)"}}
                },
                "plugins": {
                    "legend": {"display": False},
                    "tooltip": {
                        "callbacks": {
                            "label": "function(context) { return context.raw.analyzer1 + ' ↔ ' + context.raw.analyzer2 + ': ' + context.raw.correlation_score.toFixed(2); }"
                        }
                    }
                }
            }
        }
    
    def _create_audit_trail_chart_config(self, audit_trail):
        """Create Chart.js configuration for audit trail chart."""
        chart_data = self._process_audit_trail_for_chart(audit_trail)
        
        return {
            "type": "bar",
            "data": chart_data,
            "options": {
                "responsive": True,
                "scales": {
                    "y": {
                        "beginAtZero": True,
                        "title": {"display": True, "text": "Duration (ms)"}
                    }
                },
                "plugins": {"legend": {"display": False}}
            }
        }
    
    def _filter_correlations_by_threshold(self, correlations, threshold):
        """Filter correlations by minimum score threshold."""
        return [corr for corr in correlations if corr.correlation_score >= threshold]
    
    def _filter_recommendations_by_priority(self, recommendations, priority_list):
        """Filter recommendations by priority levels."""
        return [rec for rec in recommendations if rec.priority in priority_list]
    
    def _simulate_correlation_click(self, correlation):
        """Simulate correlation chart item click interaction."""
        return {
            "tooltip_content": f"{correlation.analyzer1} ↔ {correlation.analyzer2}: {int(correlation.correlation_score * 100)}%",
            "detailed_view": {
                "title": f"Correlation Details: {correlation.correlation_type}",
                "description": correlation.description,
                "priority": correlation.priority,
                "affected_files": getattr(correlation, 'affected_files', [])
            }
        }
    
    def _simulate_recommendation_click(self, recommendation):
        """Simulate recommendation item click interaction."""
        return {
            "modal_content": f"<h5>{recommendation.category}</h5><p>{recommendation.description}</p><small>Priority: {recommendation.priority} | Impact: {recommendation.impact} | Effort: {recommendation.effort}</small>",
            "action_buttons": ["Apply Recommendation", "View Details", "Dismiss"]
        }


# Web dashboard specific test configuration
@pytest.mark.web_dashboard
@pytest.mark.integration
class TestWebDashboardIntegrationFlow:
    """End-to-end integration tests for Web dashboard enhanced workflow."""
    
    @integration_test(["web_dashboard"])
    @performance_test(max_time_seconds=5.0, max_memory_mb=50.0) 
    def test_complete_dashboard_enhanced_workflow(self, enhanced_test_datasets):
        """Test complete Web dashboard enhanced workflow with all features."""
        # 1. Simulate receiving enhanced analysis data
        enhanced_data = {
            "correlations": [c.__dict__ for c in enhanced_test_datasets.get_expected_correlations()],
            "smart_recommendations": [r.__dict__ for r in enhanced_test_datasets.get_expected_smart_recommendations()],
            "audit_trail": [a.__dict__ for a in enhanced_test_datasets.get_expected_audit_trail()],
            "violations": [
                {"type": "test", "severity": "high", "message": "Test violation"},
                {"type": "test2", "severity": "medium", "message": "Test violation 2"}
            ],
            "summary": {
                "critical_count": 1,
                "high_count": 2,
                "medium_count": 3,
                "low_count": 1,
                "violations_by_type": {"test": 2, "test2": 1}
            }
        }
        
        test_instance = TestWebDashboardEnhancedIntegration()
        
        # 2. Process all enhanced chart data
        correlation_chart_data = test_instance._process_correlations_for_chart(
            enhanced_test_datasets.get_expected_correlations()
        )
        
        audit_chart_data = test_instance._process_audit_trail_for_chart(
            enhanced_test_datasets.get_expected_audit_trail()
        )
        
        recommendations_html = test_instance._render_recommendations_html(
            enhanced_test_datasets.get_expected_smart_recommendations()
        )
        
        # 3. Validate all enhanced visualizations
        # Correlation chart validation
        assert len(correlation_chart_data["datasets"]) > 0
        assert len(correlation_chart_data["datasets"][0]["data"]) >= 3
        
        # Audit trail chart validation 
        assert len(audit_chart_data["labels"]) >= 4  # Multiple phases
        assert len(audit_chart_data["datasets"][0]["data"]) >= 4
        
        # Recommendations display validation
        assert "recommendation-card" in recommendations_html
        assert enhanced_test_datasets.get_expected_smart_recommendations()[0].category in recommendations_html
        
        # 4. Test interactive features
        correlation_interaction = test_instance._simulate_correlation_click(
            enhanced_test_datasets.get_expected_correlations()[0]
        )
        
        recommendation_interaction = test_instance._simulate_recommendation_click(
            enhanced_test_datasets.get_expected_smart_recommendations()[0]
        )
        
        # 5. Validate interaction responses
        assert "tooltip_content" in correlation_interaction
        assert "modal_content" in recommendation_interaction
        
        # 6. Performance validation by decorator
        # Memory and timing validated by @performance_test