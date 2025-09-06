#!/usr/bin/env python3
"""
Critical Violation Prioritizer
Analyzes and prioritizes the 93 critical violations for immediate action
"""

import json
from pathlib import Path


class CriticalViolationPrioritizer:
    def __init__(self, analysis_file):
        self.analysis_file = analysis_file
        self.critical_violations = []

    def load_critical_violations(self):
        """Load only critical violations from the massive dataset"""
        print("Loading critical violations...")

        with open(self.analysis_file, encoding='utf-8') as f:
            data = json.load(f)

        self.critical_violations = [
            v for v in data.get('violations', [])
            if v.get('severity') == 'critical'
        ]

        print(f"Loaded {len(self.critical_violations)} critical violations")
        return len(self.critical_violations) > 0

    def prioritize_violations(self):
        """Create prioritized action plan for critical violations"""

        # Group by impact categories
        security_critical = []
        performance_critical = []
        maintainability_critical = []
        coupling_critical = []
        other_critical = []

        for violation in self.critical_violations:
            desc = violation.get('description', '').lower()
            rule_id = violation.get('rule_id', '').lower()
            violation_type = violation.get('type', '').lower()

            # Categorize by business impact
            if any(keyword in desc + rule_id + violation_type for keyword in
                   ['security', 'auth', 'validation', 'injection', 'xss', 'csrf']):
                security_critical.append(violation)
            elif any(keyword in desc + rule_id + violation_type for keyword in
                     ['performance', 'memory', 'cpu', 'optimization', 'bottleneck']):
                performance_critical.append(violation)
            elif any(keyword in desc + rule_id + violation_type for keyword in
                     ['coupling', 'dependency', 'circular', 'tight']):
                coupling_critical.append(violation)
            elif any(keyword in desc + rule_id + violation_type for keyword in
                     ['complexity', 'maintainability', 'god', 'large']):
                maintainability_critical.append(violation)
            else:
                other_critical.append(violation)

        # Create prioritized action plan
        priority_plan = {
            'P0_SECURITY_CRITICAL': {
                'violations': security_critical,
                'count': len(security_critical),
                'action_required': 'IMMEDIATE - Within 24 hours',
                'business_risk': 'EXTREME - Potential security vulnerabilities'
            },
            'P1_COUPLING_CRITICAL': {
                'violations': coupling_critical,
                'count': len(coupling_critical),
                'action_required': 'HIGH - Within 1 week',
                'business_risk': 'HIGH - System stability and maintainability'
            },
            'P2_PERFORMANCE_CRITICAL': {
                'violations': performance_critical,
                'count': len(performance_critical),
                'action_required': 'MEDIUM - Within 2 weeks',
                'business_risk': 'MEDIUM - User experience and scalability'
            },
            'P3_MAINTAINABILITY_CRITICAL': {
                'violations': maintainability_critical,
                'count': len(maintainability_critical),
                'action_required': 'MEDIUM - Within 1 month',
                'business_risk': 'MEDIUM - Development velocity and quality'
            },
            'P4_OTHER_CRITICAL': {
                'violations': other_critical,
                'count': len(other_critical),
                'action_required': 'LOW - Within 2 months',
                'business_risk': 'LOW - Code quality and standards'
            }
        }

        return priority_plan

    def create_action_items(self, priority_plan):
        """Create specific action items for each critical violation"""
        action_items = []

        for priority, data in priority_plan.items():
            for violation in data['violations']:
                file_path = violation.get('file_path', '')
                line_number = violation.get('line_number', 0)
                description = violation.get('description', '')

                action_item = {
                    'priority': priority,
                    'file': file_path,
                    'line': line_number,
                    'issue': description,
                    'estimated_effort': self._estimate_effort(violation),
                    'recommended_action': self._recommend_action(violation),
                    'business_impact': data['business_risk']
                }

                action_items.append(action_item)

        return action_items

    def _estimate_effort(self, violation):
        """Estimate effort in story points"""
        violation_type = violation.get('type', '').lower()
        description = violation.get('description', '').lower()

        if any(keyword in violation_type + description for keyword in
               ['security', 'coupling', 'architecture']):
            return '8-13 SP (Large)'
        elif any(keyword in violation_type + description for keyword in
                 ['performance', 'complexity', 'god']):
            return '5-8 SP (Medium)'
        else:
            return '2-3 SP (Small)'

    def _recommend_action(self, violation):
        """Recommend specific action for violation"""
        violation_type = violation.get('type', '').lower()
        description = violation.get('description', '').lower()

        if 'coupling' in violation_type or 'coupling' in description:
            return 'Refactor to reduce dependencies, introduce interfaces/abstractions'
        elif 'god' in description or 'large' in description:
            return 'Split into smaller, focused components following SRP'
        elif 'security' in violation_type or 'security' in description:
            return 'Security review and remediation required immediately'
        elif 'performance' in violation_type or 'performance' in description:
            return 'Performance optimization and profiling needed'
        elif 'algorithm' in violation_type:
            return 'Eliminate code duplication, extract common algorithms'
        else:
            return 'Code review and refactoring based on violation specifics'

    def generate_executive_summary(self, priority_plan, action_items):
        """Generate executive summary for leadership"""
        total_critical = sum(data['count'] for data in priority_plan.values())

        # Calculate estimated effort
        effort_map = {'8-13 SP (Large)': 10, '5-8 SP (Medium)': 6, '2-3 SP (Small)': 2}
        total_story_points = sum(
            effort_map.get(item['estimated_effort'], 5) for item in action_items
        )

        # Assume 2 story points per developer day
        estimated_days = total_story_points / 2

        summary = {
            'critical_situation': {
                'total_critical_violations': total_critical,
                'security_critical': priority_plan['P0_SECURITY_CRITICAL']['count'],
                'immediate_action_required': priority_plan['P0_SECURITY_CRITICAL']['count'] +
                                           priority_plan['P1_COUPLING_CRITICAL']['count']
            },
            'resource_requirements': {
                'estimated_story_points': total_story_points,
                'estimated_development_days': round(estimated_days, 1),
                'recommended_team_size': '3-4 senior developers',
                'timeline': '2-3 sprints for P0/P1, 6 months total'
            },
            'business_impact': {
                'risk_level': 'HIGH' if priority_plan['P0_SECURITY_CRITICAL']['count'] > 0 else 'MEDIUM',
                'quality_debt': f'{total_critical} critical issues blocking production readiness',
                'recommendation': 'Immediate remediation plan required before any major releases'
            }
        }

        return summary

    def generate_report(self):
        """Generate comprehensive critical violation report"""
        if not self.load_critical_violations():
            return None

        priority_plan = self.prioritize_violations()
        action_items = self.create_action_items(priority_plan)
        executive_summary = self.generate_executive_summary(priority_plan, action_items)

        report = {
            'executive_summary': executive_summary,
            'priority_breakdown': {
                k: {
                    'count': v['count'],
                    'action_required': v['action_required'],
                    'business_risk': v['business_risk']
                } for k, v in priority_plan.items()
            },
            'action_items': action_items,
            'detailed_violations': {
                k: [{
                    'file': v.get('file_path', ''),
                    'line': v.get('line_number', 0),
                    'description': v.get('description', ''),
                    'type': v.get('type', ''),
                    'rule_id': v.get('rule_id', '')
                } for v in violations['violations']]
                for k, violations in priority_plan.items()
            }
        }

        return report

def main():
    prioritizer = CriticalViolationPrioritizer('FULL_CODEBASE_ANALYSIS.json')
    report = prioritizer.generate_report()

    if report:
        output_file = 'docs/CRITICAL_VIOLATIONS_ACTION_PLAN.json'
        Path('docs').mkdir(exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"Critical violations action plan saved to: {output_file}")
        return output_file

    return None

if __name__ == "__main__":
    main()
