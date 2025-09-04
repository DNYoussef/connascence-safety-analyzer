"""
Local web dashboard for interactive connascence analysis.

Provides a Flask-based web interface for developers to explore
connascence violations, trends, and autofix suggestions locally.
"""

import json
import sys
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit
import webbrowser

# Updated imports for unified analyzer
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.core.unified_analyzer import UnifiedConnascenceAnalyzer, UnifiedAnalysisResult
from autofix.patch_api import SafeAutofixer
from policy.manager import PolicyManager
from dashboard.metrics import DashboardMetrics
from dashboard.charts import ChartGenerator


class LocalDashboard:
    """Local web dashboard for connascence analysis."""
    
    def __init__(self, port: int = 8080, auto_open: bool = True):
        self.port = port
        self.auto_open = auto_open
        self.app = Flask(__name__, template_folder='templates', static_folder='static')
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        
        # Core components - using unified analyzer
        self.analyzer = UnifiedConnascenceAnalyzer()
        self.autofixer = SafeAutofixer()
        self.policy_manager = PolicyManager()
        self.metrics = DashboardMetrics()
        self.chart_generator = ChartGenerator()
        
        # Dashboard state
        self.current_project: Optional[Path] = None
        self.scan_results: Dict[str, Any] = {}
        self.unified_results: Optional[UnifiedAnalysisResult] = None
        self.historical_data: List[Dict] = []
        
        self._setup_routes()
        self._setup_websocket_handlers()
    
    def _setup_routes(self):
        """Set up Flask routes."""
        
        @self.app.route('/')
        def dashboard():
            """Main dashboard page."""
            return render_template('dashboard.html', 
                                 project_path=str(self.current_project) if self.current_project else None,
                                 scan_results=self.scan_results)
        
        @self.app.route('/api/scan', methods=['POST'])
        def scan_project():
            """Scan project for connascence violations."""
            data = request.get_json()
            project_path = Path(data.get('path', '.'))
            policy_preset = data.get('policy_preset', 'service-defaults')
            
            try:
                # Start background scan
                self._start_background_scan(project_path, policy_preset)
                return jsonify({'status': 'started', 'message': 'Scan initiated'})
            except Exception as e:
                return jsonify({'status': 'error', 'message': str(e)}), 500
        
        @self.app.route('/api/autofix/preview', methods=['POST'])
        def preview_autofix():
            """Preview autofix suggestions."""
            data = request.get_json()
            file_path = data.get('file_path')
            violations = data.get('violations', [])
            
            try:
                # Convert dict violations back to objects
                violation_objects = [self._dict_to_violation(v) for v in violations]
                preview = self.autofixer.preview_fixes(file_path, violation_objects)
                return jsonify(preview)
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/metrics/trends')
        def get_trends():
            """Get historical trend data."""
            days = request.args.get('days', 30, type=int)
            return jsonify(self.metrics.get_trends(days))
        
        @self.app.route('/api/charts/<chart_type>')
        def get_chart(chart_type):
            """Generate chart data."""
            if not self.scan_results:
                return jsonify({'error': 'No scan results available'}), 404
            
            try:
                chart_data = self.chart_generator.generate_chart(
                    chart_type, self.scan_results
                )
                return jsonify(chart_data)
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/policy/presets')
        def get_policy_presets():
            """Get available policy presets."""
            presets = self.policy_manager.list_presets()
            return jsonify(presets)
        
        @self.app.route('/api/export/<format>')
        def export_results(format):
            """Export scan results in various formats."""
            if not self.scan_results:
                return jsonify({'error': 'No scan results available'}), 404
            
            if format == 'json':
                return jsonify(self.scan_results)
            elif format == 'csv':
                csv_data = self._export_csv()
                return csv_data, 200, {'Content-Type': 'text/csv'}
            else:
                return jsonify({'error': 'Unsupported format'}), 400
        
        @self.app.route('/static/<path:filename>')
        def static_files(filename):
            """Serve static files."""
            return send_from_directory('static', filename)
    
    def _setup_websocket_handlers(self):
        """Set up WebSocket event handlers."""
        
        @self.socketio.on('connect')
        def handle_connect():
            """Handle client connection."""
            emit('connected', {'message': 'Connected to Connascence Dashboard'})
        
        @self.socketio.on('request_live_update')
        def handle_live_update():
            """Handle request for live updates."""
            if self.scan_results:
                emit('scan_update', self.scan_results)
        
        @self.socketio.on('scan_file')
        def handle_file_scan(data):
            """Handle individual file scan request."""
            file_path = Path(data['file_path'])
            try:
                file_results = self.analyzer.analyze_file(file_path)
                file_results['timestamp'] = datetime.now().isoformat()
                emit('file_scan_complete', file_results)
            except Exception as e:
                emit('scan_error', {'error': str(e), 'file_path': str(file_path)})
    
    def _start_background_scan(self, project_path: Path, policy_preset: str):
        """Start background project scan."""
        def scan_worker():
            try:
                self.current_project = project_path
                
                # Emit scan started
                self.socketio.emit('scan_started', {
                    'project_path': str(project_path),
                    'policy_preset': policy_preset
                })
                
                # Perform unified analysis
                self.unified_results = self.analyzer.analyze_project(
                    project_path, policy_preset=policy_preset
                )
                
                # Generate dashboard summary
                dashboard_summary = self.analyzer.get_dashboard_summary(self.unified_results)
                
                # Process results for dashboard compatibility
                self.scan_results = {
                    'project_path': str(project_path),
                    'policy_preset': policy_preset,
                    'timestamp': self.unified_results.timestamp,
                    'violations': self.unified_results.connascence_violations,
                    'duplication_clusters': self.unified_results.duplication_clusters,
                    'nasa_violations': self.unified_results.nasa_violations,
                    'summary': {
                        'total_violations': self.unified_results.total_violations,
                        'critical_count': self.unified_results.critical_count,
                        'high_count': self.unified_results.high_count,
                        'medium_count': self.unified_results.medium_count,
                        'low_count': self.unified_results.low_count,
                        'violations_by_type': self._group_by_type_from_dict(self.unified_results.connascence_violations),
                        'violations_by_file': self._group_by_file_from_dict(self.unified_results.connascence_violations),
                        'connascence_index': self.unified_results.connascence_index,
                        'nasa_compliance_score': self.unified_results.nasa_compliance_score,
                        'duplication_score': self.unified_results.duplication_score,
                        'overall_quality_score': self.unified_results.overall_quality_score
                    },
                    'recommendations': {
                        'priority_fixes': self.unified_results.priority_fixes,
                        'improvement_actions': self.unified_results.improvement_actions
                    }
                }
                
                # Store historical data
                self.metrics.record_scan(self.scan_results)
                
                # Emit scan complete
                self.socketio.emit('scan_complete', self.scan_results)
                
            except Exception as e:
                self.socketio.emit('scan_error', {'error': str(e)})
        
        # Start background thread
        thread = threading.Thread(target=scan_worker)
        thread.daemon = True
        thread.start()
    
    def _violation_to_dict(self, violation) -> Dict:
        """Convert violation object to dictionary."""
        return {
            'id': violation.id,
            'rule_id': violation.rule_id,
            'connascence_type': violation.connascence_type,
            'severity': violation.severity,
            'description': violation.description,
            'file_path': violation.file_path,
            'line_number': violation.line_number,
            'weight': violation.weight
        }
    
    def _dict_to_violation(self, data: Dict):
        """Convert dictionary to violation object."""
        from analyzer.core import ConnascenceViolation
        return ConnascenceViolation(
            id=data['id'],
            rule_id=data['rule_id'],
            connascence_type=data['connascence_type'],
            severity=data['severity'],
            description=data['description'],
            file_path=data['file_path'],
            line_number=data['line_number'],
            weight=data['weight']
        )
    
    def _group_by_type_from_dict(self, violations) -> Dict[str, int]:
        """Group violations by connascence type from dict format."""
        groups = {}
        for violation in violations:
            conn_type = violation.get('type', 'unknown')
            groups[conn_type] = groups.get(conn_type, 0) + 1
        return groups
    
    def _group_by_file_from_dict(self, violations) -> Dict[str, int]:
        """Group violations by file from dict format."""
        groups = {}
        for violation in violations:
            file_path = Path(violation.get('file_path', '')).name
            groups[file_path] = groups.get(file_path, 0) + 1
        return groups
    
    def _group_by_type(self, violations) -> Dict[str, int]:
        """Group violations by connascence type (legacy compatibility)."""
        groups = {}
        for violation in violations:
            conn_type = getattr(violation, 'connascence_type', getattr(violation, 'type', 'unknown'))
            groups[conn_type] = groups.get(conn_type, 0) + 1
        return groups
    
    def _group_by_file(self, violations) -> Dict[str, int]:
        """Group violations by file (legacy compatibility)."""
        groups = {}
        for violation in violations:
            file_path = Path(getattr(violation, 'file_path', '')).name
            groups[file_path] = groups.get(file_path, 0) + 1
        return groups
    
    def _calculate_connascence_index(self, violations) -> float:
        """Calculate connascence index."""
        if not violations:
            return 0.0
        
        weights = {'critical': 10, 'high': 5, 'medium': 2, 'low': 1}
        total_weight = sum(weights.get(v.severity, 1) * v.weight for v in violations)
        return round(total_weight, 2)
    
    def _export_csv(self) -> str:
        """Export results as CSV."""
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow([
            'File Path', 'Line Number', 'Connascence Type', 'Severity',
            'Description', 'Weight', 'Rule ID'
        ])
        
        # Data rows
        for violation in self.scan_results.get('violations', []):
            writer.writerow([
                violation['file_path'],
                violation['line_number'],
                violation['connascence_type'],
                violation['severity'],
                violation['description'],
                violation['weight'],
                violation['rule_id']
            ])
        
        return output.getvalue()
    
    def start_server(self):
        """Start the dashboard server."""
        if self.auto_open:
            # Open browser after short delay
            def open_browser():
                time.sleep(1.5)
                webbrowser.open(f'http://localhost:{self.port}')
            
            browser_thread = threading.Thread(target=open_browser)
            browser_thread.daemon = True
            browser_thread.start()
        
        print(f"[RELEASE] Connascence Dashboard starting on http://localhost:{self.port}")
        self.socketio.run(self.app, host='0.0.0.0', port=self.port, debug=False)
    
    def stop_server(self):
        """Stop the dashboard server."""
        self.socketio.stop()


def main():
    """CLI entry point for local dashboard."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Connascence Local Dashboard')
    parser.add_argument('--port', type=int, default=8080, help='Server port')
    parser.add_argument('--no-browser', action='store_true', help='Don\'t open browser automatically')
    parser.add_argument('--project', help='Initial project path to scan')
    
    args = parser.parse_args()
    
    dashboard = LocalDashboard(port=args.port, auto_open=not args.no_browser)
    
    if args.project:
        dashboard.current_project = Path(args.project)
    
    try:
        dashboard.start_server()
    except KeyboardInterrupt:
        print("\n Dashboard stopped")


if __name__ == '__main__':
    main()