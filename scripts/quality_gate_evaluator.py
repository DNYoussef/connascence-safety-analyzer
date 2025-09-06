#!/usr/bin/env python3

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
Quality Gate Evaluator - Intelligent quality control system
Evaluates quality gates, predicts failures, and makes routing decisions
"""

from dataclasses import dataclass
from datetime import datetime
import json
import logging
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Union

import yaml

# Add project root to path for imports
script_dir = Path(__file__).parent
project_root = script_dir.parent
sys.path.insert(0, str(project_root))

@dataclass
class QualityMetric:
    name: str
    value: Union[int, float]
    source: str
    timestamp: datetime

@dataclass
class GateResult:
    gate_name: str
    status: str  # PASSED, FAILED, WARNING, ERROR
    message: str
    threshold: Optional[Union[int, float]] = None
    actual_value: Optional[Union[int, float]] = None
    details: Dict[str, Any] = None

class QualityGateEvaluator:
    """Main quality gate evaluation system"""

    def __init__(self, config_path: Optional[str] = None):
        self.logger = self._setup_logging()

        # Load configuration
        if config_path is None:
            config_path = project_root / "config" / "workflows" / "quality_gates.yml"
        self.config = self._load_config(config_path)

        # Initialize components
        self.metrics = {}
        self.gate_results = []
        self.failure_prediction_score = 0.0

        self.logger.info(f"QualityGateEvaluator initialized with config: {config_path}")

    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)

    def _load_config(self, config_path: Union[str, Path]) -> Dict[str, Any]:
        """Load quality gates configuration"""
        try:
            with open(config_path, encoding='utf-8') as f:
                config = yaml.safe_load(f)
            return config.get('quality_gates', {})
        except Exception as e:
            self.logger.error(f"Failed to load config from {config_path}: {e}")
            return {}

    def collect_metrics(self, analysis_results: Dict[str, Any]) -> Dict[str, QualityMetric]:
        """Collect quality metrics from analysis results"""
        metrics = {}

        try:
            # Extract core metrics from analysis results
            violations = analysis_results.get('violations', [])

            # Count violations by severity
            critical_count = sum(1 for v in violations if v.get('severity') == 'critical')
            high_count = sum(1 for v in violations if v.get('severity') == 'high')
            sum(1 for v in violations if v.get('severity') == 'medium')
            total_count = len(violations)

            metrics['critical_violations_count'] = QualityMetric(
                'critical_violations_count', critical_count, 'unified_analyzer', datetime.now()
            )
            metrics['high_violations_count'] = QualityMetric(
                'high_violations_count', high_count, 'unified_analyzer', datetime.now()
            )

            # NASA compliance score
            nasa_violations = [v for v in violations if 'nasa' in v.get('message', '').lower()]
            nasa_score = max(0, 100 - (len(nasa_violations) * 5))
            metrics['nasa_compliance_score'] = QualityMetric(
                'nasa_compliance_score', nasa_score, 'nasa_analyzer', datetime.now()
            )

            # Overall compliance score
            penalty_score = (critical_count * 10) + (high_count * 5) + (total_count * 1)
            overall_score = max(0, 100 - penalty_score)
            metrics['overall_compliance_score'] = QualityMetric(
                'overall_compliance_score', overall_score, 'severity_classifier', datetime.now()
            )

            # MECE analysis metrics
            mece_results = analysis_results.get('mece_analysis', {})
            duplication_clusters = mece_results.get('duplication_clusters', [])
            duplication_percentage = min(len(duplication_clusters) * 5, 100)  # Rough estimate
            metrics['code_duplication_percentage'] = QualityMetric(
                'code_duplication_percentage', duplication_percentage, 'mece_analyzer', datetime.now()
            )

            # Store metrics for evaluation
            self.metrics = metrics

            self.logger.info(f"Collected {len(metrics)} quality metrics")
            return metrics

        except Exception as e:
            self.logger.error(f"Failed to collect metrics: {e}")
            return {}

    def evaluate_gates(self) -> List[GateResult]:
        """Evaluate all configured quality gates"""
        results = []

        try:
            gates_config = self.config.get('gates', {})

            for gate_name, gate_config in gates_config.items():
                result = self._evaluate_single_gate(gate_name, gate_config)
                results.append(result)

            self.gate_results = results
            self.logger.info(f"Evaluated {len(results)} quality gates")
            return results

        except Exception as e:
            self.logger.error(f"Failed to evaluate gates: {e}")
            return []

    def _evaluate_single_gate(self, gate_name: str, gate_config: Dict[str, Any]) -> GateResult:
        """Evaluate a single quality gate"""
        try:
            gate_type = gate_config.get('type', 'threshold')
            metric_name = gate_config.get('metric')
            threshold = gate_config.get('threshold')
            operator = gate_config.get('operator', 'lte')
            action = gate_config.get('action', 'warn')
            message = gate_config.get('message', f"Gate {gate_name} evaluation")

            # Get metric value
            if metric_name in self.metrics:
                actual_value = self.metrics[metric_name].value
            else:
                return GateResult(
                    gate_name=gate_name,
                    status='ERROR',
                    message=f"Metric {metric_name} not found",
                    threshold=threshold
                )

            # Evaluate condition
            if gate_type == 'threshold':
                passed = self._evaluate_threshold_condition(actual_value, threshold, operator)
            elif gate_type == 'score':
                passed = self._evaluate_score_condition(actual_value, threshold, operator)
                # Check warning threshold
                warning_threshold = gate_config.get('warning_threshold')
                if passed and warning_threshold:
                    warning_passed = self._evaluate_threshold_condition(actual_value, warning_threshold, operator)
                    if not warning_passed:
                        return GateResult(
                            gate_name=gate_name,
                            status='WARNING',
                            message=gate_config.get('warning_message', f"Warning: {gate_name}"),
                            threshold=warning_threshold,
                            actual_value=actual_value
                        )
            elif gate_type == 'composite':
                passed = self._evaluate_composite_gate(gate_config)
            elif gate_type == 'trend':
                passed = self._evaluate_trend_gate(gate_config)
            else:
                return GateResult(
                    gate_name=gate_name,
                    status='ERROR',
                    message=f"Unknown gate type: {gate_type}",
                    threshold=threshold,
                    actual_value=actual_value
                )

            # Determine status
            if passed:
                status = 'PASSED'
                result_message = f"Gate passed: {message}"
            else:
                status = 'FAILED' if action == 'fail' else 'WARNING'
                result_message = message

            return GateResult(
                gate_name=gate_name,
                status=status,
                message=result_message,
                threshold=threshold,
                actual_value=actual_value
            )

        except Exception as e:
            self.logger.error(f"Error evaluating gate {gate_name}: {e}")
            return GateResult(
                gate_name=gate_name,
                status='ERROR',
                message=f"Evaluation error: {e}",
                threshold=threshold if 'threshold' in locals() else None
            )

    def _evaluate_threshold_condition(self, value: Union[int, float], threshold: Union[int, float], operator: str) -> bool:
        """Evaluate threshold condition"""
        if operator == 'lte':
            return value <= threshold
        elif operator == 'gte':
            return value >= threshold
        elif operator == 'lt':
            return value < threshold
        elif operator == 'gt':
            return value > threshold
        elif operator == 'eq':
            return value == threshold
        else:
            raise ValueError(f"Unknown operator: {operator}")

    def _evaluate_score_condition(self, value: Union[int, float], threshold: Union[int, float], operator: str) -> bool:
        """Evaluate score condition (same as threshold for now)"""
        return self._evaluate_threshold_condition(value, threshold, operator)

    def _evaluate_composite_gate(self, gate_config: Dict[str, Any]) -> bool:
        """Evaluate composite gate with multiple metrics"""
        try:
            metrics_config = gate_config.get('metrics', [])
            composite_threshold = gate_config.get('composite_threshold', 0.8)

            weighted_score = 0.0
            total_weight = 0.0

            for metric_config in metrics_config:
                metric_name = metric_config.get('name')
                threshold = metric_config.get('threshold')
                operator = metric_config.get('operator', 'lte')
                weight = metric_config.get('weight', 1.0)

                if metric_name in self.metrics:
                    value = self.metrics[metric_name].value
                    passed = self._evaluate_threshold_condition(value, threshold, operator)
                    weighted_score += weight * (1.0 if passed else 0.0)
                    total_weight += weight

            if total_weight > 0:
                final_score = weighted_score / total_weight
                return final_score >= composite_threshold
            else:
                return False

        except Exception as e:
            self.logger.error(f"Error evaluating composite gate: {e}")
            return False

    def _evaluate_trend_gate(self, gate_config: Dict[str, Any]) -> bool:
        """Evaluate trend gate (simplified implementation)"""
        # This would require historical data - simplified for now
        return True

    def predict_failure(self) -> float:
        """Predict likelihood of build failure using heuristics"""
        try:
            # Simple failure prediction based on current metrics
            critical_count = self.metrics.get('critical_violations_count', QualityMetric('', 0, '', datetime.now())).value
            high_count = self.metrics.get('high_violations_count', QualityMetric('', 0, '', datetime.now())).value
            nasa_score = self.metrics.get('nasa_compliance_score', QualityMetric('', 100, '', datetime.now())).value
            overall_score = self.metrics.get('overall_compliance_score', QualityMetric('', 100, '', datetime.now())).value

            # Simple scoring algorithm
            failure_score = 0.0

            # Critical violations heavily impact prediction
            if critical_count > 0:
                failure_score += 0.6 + (critical_count * 0.1)

            # High violations moderately impact prediction
            if high_count > 5:
                failure_score += 0.3 + ((high_count - 5) * 0.05)

            # Low compliance scores increase failure prediction
            if nasa_score < 90:
                failure_score += (90 - nasa_score) / 100

            if overall_score < 85:
                failure_score += (85 - overall_score) / 100

            # Cap at 1.0
            self.failure_prediction_score = min(failure_score, 1.0)

            self.logger.info(f"Failure prediction score: {self.failure_prediction_score:.2f}")
            return self.failure_prediction_score

        except Exception as e:
            self.logger.error(f"Error predicting failure: {e}")
            return 0.0

    def make_routing_decisions(self) -> List[str]:
        """Make intelligent routing decisions based on analysis"""
        decisions = []

        try:
            routing_config = self.config.get('intelligent_routing', {})
            if not routing_config.get('enabled', False):
                return decisions

            rules = routing_config.get('routing_rules', {})

            for rule_name, rule_config in rules.items():
                conditions = rule_config.get('conditions', [])
                actions = rule_config.get('actions', [])

                # Evaluate conditions
                all_conditions_met = True
                for condition in conditions:
                    if not self._evaluate_routing_condition(condition):
                        all_conditions_met = False
                        break

                if all_conditions_met:
                    decisions.extend(actions)
                    self.logger.info(f"Routing rule '{rule_name}' triggered: {actions}")

            return decisions

        except Exception as e:
            self.logger.error(f"Error making routing decisions: {e}")
            return []

    def _evaluate_routing_condition(self, condition: str) -> bool:
        """Evaluate a routing condition"""
        try:
            # Simple condition parser - could be enhanced
            if '<' in condition:
                metric_name, threshold_str = condition.split('<')
                metric_name = metric_name.strip()
                threshold = float(threshold_str.strip())

                if metric_name in self.metrics:
                    return self.metrics[metric_name].value < threshold

            elif '>' in condition:
                metric_name, threshold_str = condition.split('>')
                metric_name = metric_name.strip()
                threshold = float(threshold_str.strip())

                if metric_name in self.metrics:
                    return self.metrics[metric_name].value > threshold

            return False

        except Exception as e:
            self.logger.error(f"Error evaluating condition '{condition}': {e}")
            return False

    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive quality gates report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'quality_gates_version': '2.0.0',
            'metrics': {
                name: {
                    'value': metric.value,
                    'source': metric.source,
                    'timestamp': metric.timestamp.isoformat()
                }
                for name, metric in self.metrics.items()
            },
            'gate_results': [
                {
                    'gate_name': result.gate_name,
                    'status': result.status,
                    'message': result.message,
                    'threshold': result.threshold,
                    'actual_value': result.actual_value,
                    'details': result.details or {}
                }
                for result in self.gate_results
            ],
            'failure_prediction_score': self.failure_prediction_score,
            'routing_decisions': self.make_routing_decisions(),
            'summary': self._generate_summary()
        }

        return report

    def _generate_summary(self) -> Dict[str, Any]:
        """Generate summary of quality gates evaluation"""
        total_gates = len(self.gate_results)
        passed_gates = sum(1 for r in self.gate_results if r.status == 'PASSED')
        failed_gates = sum(1 for r in self.gate_results if r.status == 'FAILED')
        warning_gates = sum(1 for r in self.gate_results if r.status == 'WARNING')
        error_gates = sum(1 for r in self.gate_results if r.status == 'ERROR')

        # Determine overall status
        if error_gates > 0:
            overall_status = 'ERROR'
        elif failed_gates > 0:
            overall_status = 'FAILED'
        elif warning_gates > 0:
            overall_status = 'WARNING'
        else:
            overall_status = 'PASSED'

        return {
            'total_gates': total_gates,
            'passed_gates': passed_gates,
            'failed_gates': failed_gates,
            'warning_gates': warning_gates,
            'error_gates': error_gates,
            'overall_status': overall_status,
            'pass_rate': (passed_gates / total_gates * 100) if total_gates > 0 else 0
        }

def main():
    """Main entry point for quality gate evaluation"""
    import argparse

    parser = argparse.ArgumentParser(description='Quality Gate Evaluator')
    parser.add_argument('--config', help='Path to quality gates configuration file')
    parser.add_argument('--input', help='Path to analysis results JSON file')
    parser.add_argument('--output', help='Path to output quality gates report')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        # Initialize evaluator
        evaluator = QualityGateEvaluator(args.config)

        # Load analysis results
        if args.input:
            with open(args.input, encoding='utf-8') as f:
                analysis_results = json.load(f)
        else:
            # Mock data for testing
            analysis_results = {
                'violations': [
                    {'severity': 'critical', 'message': 'Critical issue'},
                    {'severity': 'high', 'message': 'High priority issue'},
                    {'severity': 'medium', 'message': 'Medium issue'}
                ],
                'mece_analysis': {
                    'duplication_clusters': []
                }
            }

        # Collect metrics and evaluate gates
        evaluator.collect_metrics(analysis_results)
        evaluator.evaluate_gates()
        evaluator.predict_failure()

        # Generate report
        report = evaluator.generate_report()

        # Output results
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2)
            print(f"Quality gates report saved to: {args.output}")
        else:
            print(json.dumps(report, indent=2))

        # Set exit code based on overall status
        summary = report['summary']
        if summary['overall_status'] in ['ERROR', 'FAILED']:
            sys.exit(1)
        elif summary['overall_status'] == 'WARNING':
            sys.exit(2)
        else:
            sys.exit(0)

    except Exception as e:
        print(f"Error running quality gate evaluation: {e}", file=sys.stderr)
        sys.exit(3)

if __name__ == '__main__':
    main()
