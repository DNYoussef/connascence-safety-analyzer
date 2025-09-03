#!/usr/bin/env python3
"""
Grammar Analysis Service Classes

Split from GrammarEnhancedAnalyzer to reduce God Object anti-pattern.
Each service has a focused responsibility for specific analysis aspects.
"""

import ast
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set, Any, Tuple

logger = logging.getLogger(__name__)

# Import constants
from .constants import (
    SeverityLevel, ConnascenceType, AnalysisLimits, 
    FileSizeThresholds, SafetyProfiles, FrameworkProfiles
)


@dataclass
class ValidationResult:
    """Result of grammar validation."""
    is_valid: bool
    language: str
    overlay_applied: Optional[str] = None
    violations: List[Dict[str, Any]] = None
    ast_tree: Optional[Any] = None
    parse_errors: List[str] = None
    
    def __post_init__(self):
        if self.violations is None:
            self.violations = []
        if self.parse_errors is None:
            self.parse_errors = []
    
    @property
    def has_safety_violations(self) -> bool:
        """Check if there are safety-related violations."""
        return any(v.get('category') == 'safety' for v in self.violations)


@dataclass
class AnalysisReport:
    """Combined analysis report from all services."""
    file_path: str
    language: str
    validation_result: ValidationResult
    connascence_violations: List = None
    magic_literals: List = None
    god_objects: List = None
    refactoring_opportunities: List = None
    safety_compliance: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.connascence_violations is None:
            self.connascence_violations = []
        if self.magic_literals is None:
            self.magic_literals = []
        if self.god_objects is None:
            self.god_objects = []
        if self.refactoring_opportunities is None:
            self.refactoring_opportunities = []
        if self.safety_compliance is None:
            self.safety_compliance = {}
    
    @property
    def quality_score(self) -> float:
        """Calculate overall quality score (0.0-1.0)."""
        scores = []
        
        # Grammar validation score
        grammar_score = 1.0 if self.validation_result.is_valid else 0.0
        if self.validation_result.has_safety_violations:
            grammar_score *= 0.5
        scores.append(grammar_score)
        
        # Connascence score (fewer violations = higher score)
        critical_connascence = len([v for v in self.connascence_violations 
                                  if getattr(v, 'severity', 'low') == SeverityLevel.CRITICAL.value])
        connascence_score = max(0.0, 1.0 - (critical_connascence * 0.2))
        scores.append(connascence_score)
        
        # God object score
        critical_god_objects = len([g for g in self.god_objects 
                                  if getattr(g, 'severity', 'low') == SeverityLevel.CRITICAL.value])
        god_object_score = max(0.0, 1.0 - (critical_god_objects * 0.3))
        scores.append(god_object_score)
        
        # Magic literal score
        critical_literals = len([m for m in self.magic_literals 
                               if getattr(m, 'severity', 'low') == SeverityLevel.CRITICAL.value])
        literal_score = max(0.0, 1.0 - (critical_literals * 0.1))
        scores.append(literal_score)
        
        return sum(scores) / len(scores) if scores else 0.0


class LanguageDetectionService:
    """Service for detecting programming languages from file paths."""
    
    @staticmethod
    def detect_language(file_path: Path) -> str:
        """Detect programming language from file extension."""
        suffix = file_path.suffix.lower()
        
        if suffix == '.py':
            return 'python'
        elif suffix in {'.c', '.h'}:
            return 'c'
        elif suffix in {'.cpp', '.cxx', '.cc', '.hpp', '.hxx'}:
            return 'cpp'
        elif suffix in {'.js', '.mjs'}:
            return 'javascript'
        elif suffix in {'.ts', '.tsx'}:
            return 'typescript'
        else:
            return 'python'  # Default fallback


class GrammarValidationService:
    """Service for validating code using grammar backend."""
    
    def __init__(self):
        self.grammar_available = self._check_grammar_backend()
    
    def _check_grammar_backend(self) -> bool:
        """Check if grammar backend is available."""
        try:
            from ..grammar.backends.tree_sitter_backend import TreeSitterBackend
            return True
        except ImportError:
            logger.warning("Grammar backend not available - using standard analysis")
            return False
    
    def validate_code(self, content: str, language: str, 
                     safety_profile: Optional[str] = None) -> ValidationResult:
        """Validate code using grammar backend with optional safety profile."""
        
        if not self.grammar_available:
            # Fallback to standard Python AST parsing
            try:
                tree = ast.parse(content)
                return ValidationResult(
                    is_valid=True,
                    language=language,
                    ast_tree=tree
                )
            except SyntaxError as e:
                return ValidationResult(
                    is_valid=False,
                    language=language,
                    parse_errors=[str(e)]
                )
        
        # Use grammar backend
        try:
            from ..grammar.backends.tree_sitter_backend import TreeSitterBackend, LanguageSupport
            from ..grammar.overlay_manager import OverlayManager
            
            backend = TreeSitterBackend()
            overlay_manager = OverlayManager(backend)
            
            # Convert language string to enum
            lang_support = getattr(LanguageSupport, language.upper(), LanguageSupport.PYTHON)
            
            # Apply safety overlay if specified
            overlay = None
            if safety_profile:
                overlay = f"{language}_{safety_profile}"
            
            parse_result = backend.parse(content, lang_support)
            
            if parse_result.success:
                # Validate with overlay if specified
                violations = []
                if overlay and overlay_manager:
                    overlay_result = overlay_manager.validate_code_against_overlay(
                        [parse_result.ast], overlay
                    )
                    violations.extend(overlay_result)
                
                return ValidationResult(
                    is_valid=True,
                    language=language,
                    overlay_applied=overlay,
                    violations=violations,
                    ast_tree=parse_result.ast
                )
            else:
                return ValidationResult(
                    is_valid=False,
                    language=language,
                    parse_errors=parse_result.errors
                )
                
        except Exception as e:
            logger.error(f"Grammar validation failed: {e}")
            return ValidationResult(
                is_valid=False,
                language=language,
                parse_errors=[str(e)]
            )


class ConnascenceAnalysisService:
    """Service for connascence analysis."""
    
    def analyze_file(self, file_path: Path, content: str) -> List[Any]:
        """Analyze file for connascence violations."""
        # Import here to avoid circular dependencies
        try:
            from ..analyzer.connascence_analyzer import ConnascenceAnalyzer
            analyzer = ConnascenceAnalyzer()
            return analyzer._analyze_file(file_path)
        except ImportError:
            logger.warning("ConnascenceAnalyzer not available")
            return []
        except Exception as e:
            logger.warning(f"Connascence analysis failed: {e}")
            return []


class MagicLiteralAnalysisService:
    """Service for magic literal analysis."""
    
    def __init__(self, framework_profile: Optional[str] = None):
        self.framework_profile = framework_profile
    
    def analyze_file(self, file_path: Path, content: str) -> List[Any]:
        """Analyze file for magic literals."""
        try:
            from ..analyzer.magic_literal_analyzer import EnhancedMagicLiteralAnalyzer, FrameworkProfile
            
            # Get framework profile if specified
            profile = None
            if self.framework_profile == FrameworkProfiles.DJANGO:
                profile = FrameworkProfile.django_profile()
            elif self.framework_profile == FrameworkProfiles.FASTAPI:
                profile = FrameworkProfile.fastapi_profile()
            
            analyzer = EnhancedMagicLiteralAnalyzer(str(file_path), profile)
            tree = ast.parse(content)
            analyzer.visit(tree)
            return analyzer.literals
        except ImportError:
            logger.warning("MagicLiteralAnalyzer not available")
            return []
        except Exception as e:
            logger.warning(f"Magic literal analysis failed: {e}")
            return []


class RefactoringAnalysisService:
    """Service for refactoring opportunity analysis."""
    
    def __init__(self):
        self.refactoring_available = self._check_refactoring_backend()
    
    def _check_refactoring_backend(self) -> bool:
        """Check if refactoring backend is available."""
        try:
            from ..grammar.ast_safe_refactoring import ASTSafeRefactoringEngine
            return True
        except ImportError:
            return False
    
    def find_opportunities(self, content: str, language: str, 
                         ast_tree: Any = None) -> List[Any]:
        """Find refactoring opportunities using AST-safe analysis."""
        if not self.refactoring_available:
            return []
        
        try:
            from ..grammar.ast_safe_refactoring import ASTSafeRefactoringEngine
            from ..grammar.backends.tree_sitter_backend import TreeSitterBackend, LanguageSupport
            from ..grammar.overlay_manager import OverlayManager
            
            backend = TreeSitterBackend()
            overlay_manager = OverlayManager(backend)
            engine = ASTSafeRefactoringEngine(backend, overlay_manager)
            
            lang_support = getattr(LanguageSupport, language.upper(), LanguageSupport.PYTHON)
            return engine.find_refactoring_opportunities(content, lang_support)
        except Exception as e:
            logger.warning(f"Refactoring analysis failed: {e}")
            return []


class SafetyComplianceService:
    """Service for safety profile compliance checking."""
    
    def check_compliance(self, validation_result: ValidationResult, 
                        safety_profile: Optional[str] = None) -> Dict[str, Any]:
        """Check compliance with safety profile."""
        compliance = {
            "profile": safety_profile,
            "compliant": len(validation_result.violations) == 0,
            "violations": validation_result.violations,
            "nasa_compliant": False
        }
        
        if safety_profile and safety_profile.startswith('nasa_'):
            # Check NASA-specific compliance
            nasa_violations = [v for v in validation_result.violations 
                             if v.get('rule', '').startswith('nasa_')]
            compliance["nasa_compliant"] = len(nasa_violations) == 0
            compliance["nasa_violations"] = nasa_violations
        
        return compliance


class FiltersService:
    """Service for filtering analysis results."""
    
    @staticmethod
    def should_skip_file(file_path: Path) -> bool:
        """Check if file should be skipped during analysis."""
        from .constants import SkipPatterns
        return any(pattern in str(file_path) for pattern in SkipPatterns.PATTERNS)
    
    @staticmethod
    def filter_by_size(file_path: Path) -> str:
        """Categorize file by size."""
        try:
            size_lines = len(file_path.read_text().splitlines())
            
            if size_lines <= FileSizeThresholds.SMALL_FILE:
                return "small"
            elif size_lines <= FileSizeThresholds.MEDIUM_FILE:
                return "medium"
            elif size_lines <= FileSizeThresholds.LARGE_FILE:
                return "large"
            else:
                return "god_object_candidate"
        except Exception:
            return "unknown"
    
    @staticmethod
    def filter_by_severity(violations: List, min_severity: str) -> List:
        """Filter violations by minimum severity."""
        from .constants import SEVERITY_ORDER
        
        min_level = SEVERITY_ORDER.get(SeverityLevel(min_severity), 0)
        
        return [
            v for v in violations 
            if SEVERITY_ORDER.get(SeverityLevel(getattr(v, 'severity', SeverityLevel.LOW)), 0) >= min_level
        ]