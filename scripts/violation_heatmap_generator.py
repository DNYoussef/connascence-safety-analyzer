#!/usr/bin/env python3
"""
Violation Heatmap Generator
Creates visual representation of the 95,395 violations across the codebase
"""

from collections import defaultdict
import json


class ViolationHeatmapGenerator:
    def __init__(self, analysis_file):
        self.analysis_file = analysis_file
        self.violations = []

    def load_violations(self):
        """Load all violations"""
        with open(self.analysis_file, encoding='utf-8') as f:
            data = json.load(f)
        self.violations = data.get('violations', [])
        return len(self.violations) > 0

    def generate_folder_heatmap(self):
        """Generate heatmap data by folder"""
        folder_stats = defaultdict(lambda: {
            'total_violations': 0,
            'critical_violations': 0,
            'violation_types': set(),
            'files_affected': set(),
            'severity_breakdown': defaultdict(int)
        })

        for violation in self.violations:
            file_path = violation.get('file_path', '')
            if file_path:
                folder = file_path.replace('..\\', '').split('\\')[0]
                severity = violation.get('severity', 'unknown')
                violation_type = violation.get('type', 'unknown')

                folder_stats[folder]['total_violations'] += 1
                folder_stats[folder]['files_affected'].add(file_path)
                folder_stats[folder]['violation_types'].add(violation_type)
                folder_stats[folder]['severity_breakdown'][severity] += 1

                if severity == 'critical':
                    folder_stats[folder]['critical_violations'] += 1

        # Convert sets to lists and calculate intensity
        heatmap_data = {}
        max_violations = max(stats['total_violations'] for stats in folder_stats.values()) if folder_stats else 1

        for folder, stats in folder_stats.items():
            intensity = stats['total_violations'] / max_violations
            heatmap_data[folder] = {
                'total_violations': stats['total_violations'],
                'critical_violations': stats['critical_violations'],
                'files_affected': len(stats['files_affected']),
                'violation_types': list(stats['violation_types']),
                'unique_violation_types': len(stats['violation_types']),
                'severity_breakdown': dict(stats['severity_breakdown']),
                'heat_intensity': round(intensity, 3),  # 0-1 scale
                'risk_level': self._calculate_risk_level(stats['critical_violations'], stats['total_violations'])
            }

        return heatmap_data

    def generate_file_heatmap(self, top_n=50):
        """Generate heatmap for top N most problematic files"""
        file_stats = defaultdict(lambda: {
            'violations': 0,
            'critical_violations': 0,
            'violation_types': set(),
            'severity_breakdown': defaultdict(int)
        })

        for violation in self.violations:
            file_path = violation.get('file_path', '')
            if file_path:
                severity = violation.get('severity', 'unknown')
                violation_type = violation.get('type', 'unknown')

                file_stats[file_path]['violations'] += 1
                file_stats[file_path]['violation_types'].add(violation_type)
                file_stats[file_path]['severity_breakdown'][severity] += 1

                if severity == 'critical':
                    file_stats[file_path]['critical_violations'] += 1

        # Get top N files by violation count
        sorted_files = sorted(
            file_stats.items(),
            key=lambda x: x[1]['violations'],
            reverse=True
        )[:top_n]

        max_violations = sorted_files[0][1]['violations'] if sorted_files else 1

        file_heatmap = {}
        for file_path, stats in sorted_files:
            intensity = stats['violations'] / max_violations
            file_heatmap[file_path] = {
                'violations': stats['violations'],
                'critical_violations': stats['critical_violations'],
                'unique_violation_types': len(stats['violation_types']),
                'severity_breakdown': dict(stats['severity_breakdown']),
                'heat_intensity': round(intensity, 3),
                'risk_level': self._calculate_risk_level(stats['critical_violations'], stats['violations'])
            }

        return file_heatmap

    def generate_violation_type_heatmap(self):
        """Generate heatmap by violation types"""
        type_stats = defaultdict(lambda: {
            'count': 0,
            'critical_count': 0,
            'files_affected': set(),
            'folders_affected': set()
        })

        for violation in self.violations:
            violation_type = violation.get('type', 'unknown')
            severity = violation.get('severity', 'unknown')
            file_path = violation.get('file_path', '')

            type_stats[violation_type]['count'] += 1
            if severity == 'critical':
                type_stats[violation_type]['critical_count'] += 1

            if file_path:
                type_stats[violation_type]['files_affected'].add(file_path)
                folder = file_path.replace('..\\', '').split('\\')[0]
                type_stats[violation_type]['folders_affected'].add(folder)

        # Calculate impact scores
        max_count = max(stats['count'] for stats in type_stats.values()) if type_stats else 1

        type_heatmap = {}
        for violation_type, stats in type_stats.items():
            impact_score = (
                (stats['count'] / max_count) * 0.4 +  # Frequency weight
                (stats['critical_count'] / max(stats['count'], 1)) * 0.4 +  # Critical ratio weight
                (len(stats['files_affected']) / max_count) * 0.2  # Spread weight
            )

            type_heatmap[violation_type] = {
                'total_violations': stats['count'],
                'critical_violations': stats['critical_count'],
                'files_affected': len(stats['files_affected']),
                'folders_affected': len(stats['folders_affected']),
                'impact_score': round(impact_score, 3),
                'critical_ratio': round(stats['critical_count'] / max(stats['count'], 1), 3)
            }

        return type_heatmap

    def _calculate_risk_level(self, critical_count, total_count):
        """Calculate risk level based on violation counts"""
        if critical_count > 0:
            return 'EXTREME'
        elif total_count > 100:
            return 'HIGH'
        elif total_count > 50:
            return 'MEDIUM'
        elif total_count > 10:
            return 'LOW'
        else:
            return 'MINIMAL'

    def generate_ascii_heatmap(self, data, title, key_field='heat_intensity'):
        """Generate ASCII heatmap visualization"""
        lines = [f"\n{title}", "=" * len(title)]

        # Sort by intensity/impact
        sorted_items = sorted(data.items(), key=lambda x: x[1].get(key_field, 0), reverse=True)

        for name, stats in sorted_items[:20]:  # Top 20
            intensity = stats.get(key_field, 0)
            bar_length = int(intensity * 50)  # Scale to 50 chars
            bar = '#' * bar_length + '-' * (50 - bar_length)

            violations = stats.get('total_violations', stats.get('violations', 0))
            critical = stats.get('critical_violations', 0)

            line = f"{name[:30]:<30} |{bar}| {violations:>6} ({critical:>3}c) [{intensity:.3f}]"
            lines.append(line)

        return '\n'.join(lines)

    def generate_comprehensive_heatmaps(self):
        """Generate all heatmap visualizations"""
        if not self.load_violations():
            return None

        folder_heatmap = self.generate_folder_heatmap()
        file_heatmap = self.generate_file_heatmap()
        type_heatmap = self.generate_violation_type_heatmap()

        # Generate ASCII visualizations
        folder_ascii = self.generate_ascii_heatmap(
            folder_heatmap,
            "FOLDER VIOLATION HEATMAP (Top 20)"
        )

        file_ascii = self.generate_ascii_heatmap(
            file_heatmap,
            "FILE VIOLATION HEATMAP (Top 20)",
            'heat_intensity'
        )

        type_ascii = self.generate_ascii_heatmap(
            type_heatmap,
            "VIOLATION TYPE IMPACT HEATMAP (Top 20)",
            'impact_score'
        )

        report = {
            'heatmaps': {
                'folder_heatmap': folder_heatmap,
                'file_heatmap': file_heatmap,
                'violation_type_heatmap': type_heatmap
            },
            'visualizations': {
                'folder_visualization': folder_ascii,
                'file_visualization': file_ascii,
                'type_visualization': type_ascii
            },
            'summary_stats': {
                'total_violations_processed': len(self.violations),
                'folders_analyzed': len(folder_heatmap),
                'top_files_analyzed': len(file_heatmap),
                'violation_types_found': len(type_heatmap),
                'highest_risk_folder': max(folder_heatmap.items(), key=lambda x: x[1]['total_violations'])[0] if folder_heatmap else None,
                'most_impacted_type': max(type_heatmap.items(), key=lambda x: x[1]['impact_score'])[0] if type_heatmap else None
            }
        }

        return report

def main():
    generator = ViolationHeatmapGenerator('FULL_CODEBASE_ANALYSIS.json')
    heatmap_report = generator.generate_comprehensive_heatmaps()

    if heatmap_report:
        # Save heatmap data
        output_file = 'docs/VIOLATION_HEATMAPS.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(heatmap_report, f, indent=2, ensure_ascii=False)

        # Print visualizations to console
        print(heatmap_report['visualizations']['folder_visualization'])
        print(heatmap_report['visualizations']['file_visualization'])
        print(heatmap_report['visualizations']['type_visualization'])

        print(f"\nHeatmap report saved to: {output_file}")
        return output_file

    return None

if __name__ == "__main__":
    main()
