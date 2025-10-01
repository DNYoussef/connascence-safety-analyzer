"""
Enterprise-Grade Analysis Features for Connascence Analyzer
============================================================

This module provides defense industry and enterprise compliance features:
- NASA POT10 Enhanced: Weighted scoring with 95%+ certification target
- Six Sigma Integration: CTQ calculator, DPMO, SPC charts
- Theater Detection: Performance theater pattern detection
- Supply Chain Security: SBOM generation, SLSA attestation
- ML Modules: AI-powered quality prediction and compliance forecasting
- Enterprise Compliance: SOC2, ISO27001, NIST-SSDF alignment
"""

from .nasa_pot10_enhanced import (
    EnhancedNASAPowerOfTenAnalyzer,
    EnhancedComplianceMetrics,
    MultiCategoryCompliance,
    WeightedScoringEngine
)

__all__ = [
    'EnhancedNASAPowerOfTenAnalyzer',
    'EnhancedComplianceMetrics',
    'MultiCategoryCompliance',
    'WeightedScoringEngine'
]

__version__ = '2.0.0'