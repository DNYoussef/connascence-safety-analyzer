#!/usr/bin/env python3
"""
Grammar-Enhanced Analyzer Integration

Integrates the grammar backend with existing analyzers to provide:
- AST-safe validation for all code analysis
- Grammar-constrained refactoring suggestions  
- Safety profile enforcement during analysis
- Enhanced code generation with grammar constraints
"""

import ast
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Any, Tuple
import logging

logger = logging.getLogger(__name__)

# Import grammar components
try:
    from ..grammar.backends.tree_sitter_backend import TreeSitterBackend, LanguageSupport
    from ..grammar.overlay_manager import OverlayManager
    from ..grammar.constrained_generator import ConstrainedGenerator, GenerationConstraints, GenerationMode
    from ..grammar.ast_safe_refactoring import ASTSafeRefactoringEngine, RefactoringCandidate
    GRAMMAR_AVAILABLE = True
except ImportError:
    GRAMMAR_AVAILABLE = False
    import warnings
    warnings.warn("Grammar backend not available, using standard AST analysis")

# Import existing analyzers
try:
    from .connascence_analyzer import ConnascenceAnalyzer, ConnascenceViolation
    from .magic_literal_analyzer import EnhancedMagicLiteralAnalyzer, MagicLiteral, FrameworkProfile
    from .cohesion_analyzer import StatisticalGodObjectDetector, GodObjectFinding
except ImportError as e:
    logger.warning(f"Some analyzers not available: {e}")


@dataclass
class GrammarValidationResult:
    """Result of grammar validation for code analysis."""
    
    is_valid: bool
    language: LanguageSupport
    overlay_applied: Optional[str] = None
    violations: List[Dict[str, Any]] = field(default_factory=list)
    ast_tree: Optional[Any] = None
    parse_errors: List[str] = field(default_factory=list)
    
    @property
    def has_safety_violations(self) -> bool:
        """Check if there are safety-related violations."""
        return any(v.get('category') == 'safety' for v in self.violations)


@dataclass 
class EnhancedAnalysisResult:
    """Combined result from grammar-enhanced analysis."""
    
    file_path: str
    language: LanguageSupport
    grammar_validation: GrammarValidationResult
    
    # Standard analysis results
    connascence_violations: List[ConnascenceViolation] = field(default_factory=list)
    magic_literals: List[MagicLiteral] = field(default_factory=list)
    god_objects: List[GodObjectFinding] = field(default_factory=list)
    
    # Grammar-enhanced insights
    refactoring_opportunities: List[RefactoringCandidate] = field(default_factory=list)
    safety_profile_compliance: Dict[str, Any] = field(default_factory=dict)
    generation_constraints: Optional[GenerationConstraints] = None
    
    @property
    def overall_quality_score(self) -> float:
        """Calculate overall code quality score (0.0-1.0)."""
        scores = []
        
        # Grammar validation score
        grammar_score = 1.0 if self.grammar_validation.is_valid else 0.0
        if self.grammar_validation.has_safety_violations:
            grammar_score *= 0.5
        scores.append(grammar_score)
        
        # Connascence score (fewer violations = higher score)
        critical_connascence = len([v for v in self.connascence_violations if v.severity == 'CRITICAL'])
        connascence_score = max(0.0, 1.0 - (critical_connascence * 0.2))
        scores.append(connascence_score)
        
        # God object score
        critical_god_objects = len([g for g in self.god_objects if g.severity == 'critical'])
        god_object_score = max(0.0, 1.0 - (critical_god_objects * 0.3))
        scores.append(god_object_score)
        
        # Magic literal score
        critical_literals = len([m for m in self.magic_literals if m.severity == 'critical'])
        literal_score = max(0.0, 1.0 - (critical_literals * 0.1))
        scores.append(literal_score)
        
        return sum(scores) / len(scores) if scores else 0.0


class GrammarEnhancedAnalyzer:
    """Main analyzer that integrates grammar backend with all code analysis."""
    
    def __init__(self, 
                 enable_safety_profiles: bool = True,
                 framework_profile: Optional[FrameworkProfile] = None,
                 safety_compliance: bool = False):
        """Initialize the enhanced analyzer."""
        
        self.enable_safety_profiles = enable_safety_profiles
        self.framework_profile = framework_profile  
        self.safety_compliance = safety_compliance
        
        # Initialize components
        if GRAMMAR_AVAILABLE:
            self.grammar_backend = TreeSitterBackend()
            self.overlay_manager = OverlayManager(self.grammar_backend)
            self.constrained_generator = ConstrainedGenerator(
                self.grammar_backend, self.overlay_manager
            )
            self.refactoring_engine = ASTSafeRefactoringEngine(
                self.grammar_backend, self.overlay_manager
            )
        else:
            self.grammar_backend = None
            logger.warning("Grammar backend not available - using standard analysis")
        
        # Initialize standard analyzers
        self.connascence_analyzer = ConnascenceAnalyzer()
        self.god_object_detector = StatisticalGodObjectDetector()
    
    def analyze_file(self, file_path: Path, 
                    safety_profile: Optional[str] = None) -> EnhancedAnalysisResult:
        """Perform comprehensive analysis of a single file."""
        
        # Determine language
        language = self._detect_language(file_path)
        
        # Read file content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            logger.error(f"Failed to read {file_path}: {e}")
            return self._create_error_result(file_path, language, str(e))
        
        # Grammar validation with safety profile
        grammar_result = self._validate_with_grammar(content, language, safety_profile)
        
        # Standard analysis
        result = EnhancedAnalysisResult(
            file_path=str(file_path),
            language=language,
            grammar_validation=grammar_result
        )
        
        # Run connascence analysis
        try:
            result.connascence_violations = self._analyze_connascence(file_path, content)
        except Exception as e:
            logger.warning(f"Connascence analysis failed for {file_path}: {e}")
        
        # Run magic literal analysis
        try:
            result.magic_literals = self._analyze_magic_literals(file_path, content)
        except Exception as e:
            logger.warning(f"Magic literal analysis failed for {file_path}: {e}")
        
        # Grammar-enhanced analysis (if available)
        if GRAMMAR_AVAILABLE and grammar_result.is_valid:
            # Find refactoring opportunities
            result.refactoring_opportunities = self._find_refactoring_opportunities(
                content, language, grammar_result.ast_tree
            )
            
            # Check safety profile compliance
            result.safety_profile_compliance = self._check_safety_compliance(
                grammar_result, safety_profile
            )
            
            # Generate constraints for code generation
            result.generation_constraints = self._create_generation_constraints(
                language, safety_profile
            )
        
        return result
    
    def analyze_codebase(self, root_path: Path, 
                        safety_profile: Optional[str] = None) -> List[EnhancedAnalysisResult]:
        """Analyze entire codebase with grammar enhancement."""
        
        results = []
        
        # Collect all Python files
        python_files = list(root_path.rglob("*.py"))
        
        # Filter out files to skip
        python_files = [f for f in python_files if not self._should_skip_file(f)]
        
        # First, run god object analysis on the entire codebase for statistical analysis
        if self.god_object_detector:
            god_object_findings = self.god_object_detector.analyze_codebase(root_path)
            god_objects_by_file = {f.file_path: f for f in god_object_findings}
        else:
            god_objects_by_file = {}
        
        # Analyze each file
        for py_file in python_files:
            try:
                result = self.analyze_file(py_file, safety_profile)
                
                # Add god object findings for this file
                if str(py_file) in god_objects_by_file:
                    result.god_objects = [god_objects_by_file[str(py_file)]]
                
                results.append(result)
                
            except Exception as e:
                logger.error(f"Failed to analyze {py_file}: {e}")
                results.append(self._create_error_result(py_file, LanguageSupport.PYTHON, str(e)))
        
        return results
    
    def suggest_grammar_constrained_fixes(self, 
                                        result: EnhancedAnalysisResult) -> List[Dict[str, Any]]:
        """Suggest fixes using grammar-constrained generation."""
        
        if not GRAMMAR_AVAILABLE or not result.grammar_validation.is_valid:
            return []
        
        fixes = []
        
        # Generate fixes for refactoring opportunities
        for opportunity in result.refactoring_opportunities:
            if self.refactoring_engine:
                try:
                    patch = self.refactoring_engine.apply_refactoring(
                        opportunity, result.generation_constraints or GenerationConstraints(
                            language=result.language
                        )
                    )
                    
                    if patch.success:
                        fixes.append({
                            "type": "refactoring",
                            "technique": opportunity.technique.value,
                            "description": opportunity.description,
                            "patch": patch.modified_code,
                            "confidence": patch.confidence,
                            "safety_verified": patch.safety_verified
                        })
                        
                except Exception as e:
                    logger.warning(f"Failed to generate fix for {opportunity.technique}: {e}")
        
        # Generate fixes for safety violations
        for violation in result.grammar_validation.violations:
            if violation.get('category') == 'safety':
                try:
                    # Use constrained generator to suggest safe alternatives
                    safe_alternative = self._generate_safe_alternative(
                        violation, result.generation_constraints
                    )
                    
                    if safe_alternative:
                        fixes.append({
                            "type": "safety_fix",
                            "violation": violation,
                            "safe_alternative": safe_alternative,
                            "rationale": violation.get('rationale', 'Safety compliance')
                        })
                        
                except Exception as e:
                    logger.warning(f"Failed to generate safety fix: {e}")
        
        return fixes
    
    def _detect_language(self, file_path: Path) -> LanguageSupport:
        """Detect programming language from file extension."""
        suffix = file_path.suffix.lower()
        
        if suffix == '.py':
            return LanguageSupport.PYTHON
        elif suffix in {'.c', '.h'}:
            return LanguageSupport.C
        elif suffix in {'.cpp', '.cxx', '.cc', '.hpp', '.hxx'}:
            return LanguageSupport.CPP
        elif suffix in {'.js', '.mjs'}:
            return LanguageSupport.JAVASCRIPT
        elif suffix in {'.ts', '.tsx'}:
            return LanguageSupport.TYPESCRIPT
        else:
            return LanguageSupport.PYTHON  # Default fallback
    
    def _validate_with_grammar(self, content: str, language: LanguageSupport, 
                             safety_profile: Optional[str]) -> GrammarValidationResult:
        """Validate code using grammar backend with optional safety profile."""
        
        if not GRAMMAR_AVAILABLE:
            # Fallback to standard Python AST parsing
            try:
                tree = ast.parse(content)
                return GrammarValidationResult(
                    is_valid=True,
                    language=language,
                    ast_tree=tree
                )
            except SyntaxError as e:
                return GrammarValidationResult(
                    is_valid=False,
                    language=language,
                    parse_errors=[str(e)]
                )
        
        # Use grammar backend
        try:
            # Apply safety overlay if specified
            overlay = None
            if safety_profile and self.enable_safety_profiles:
                overlay = f"{language.value}_{safety_profile}"
            
            parse_result = self.grammar_backend.parse(content, language)
            
            if parse_result.success:
                # Validate with overlay if specified
                violations = []
                if overlay and self.overlay_manager:
                    overlay_result = self.overlay_manager.validate_code_against_overlay(
                        [parse_result.ast], overlay
                    )
                    violations.extend(overlay_result)
                
                return GrammarValidationResult(
                    is_valid=True,
                    language=language,
                    overlay_applied=overlay,
                    violations=violations,
                    ast_tree=parse_result.ast
                )
            else:
                return GrammarValidationResult(
                    is_valid=False,
                    language=language,
                    parse_errors=parse_result.errors
                )
                
        except Exception as e:
            logger.error(f"Grammar validation failed: {e}")
            return GrammarValidationResult(
                is_valid=False,
                language=language,
                parse_errors=[str(e)]
            )
    
    def _analyze_connascence(self, file_path: Path, content: str) -> List[ConnascenceViolation]:
        """Run connascence analysis."""
        # This would integrate with the existing connascence analyzer
        # For now, return empty list as placeholder
        return []
    
    def _analyze_magic_literals(self, file_path: Path, content: str) -> List[MagicLiteral]:
        """Run magic literal analysis with framework awareness."""
        try:
            analyzer = EnhancedMagicLiteralAnalyzer(str(file_path), self.framework_profile)
            tree = ast.parse(content)
            analyzer.visit(tree)
            return analyzer.literals
        except Exception as e:
            logger.warning(f"Magic literal analysis failed: {e}")
            return []
    
    def _find_refactoring_opportunities(self, content: str, language: LanguageSupport, 
                                      ast_tree: Any) -> List[RefactoringCandidate]:
        """Find refactoring opportunities using AST-safe analysis."""
        if not self.refactoring_engine:
            return []
        
        try:
            return self.refactoring_engine.find_refactoring_opportunities(content, language)
        except Exception as e:
            logger.warning(f"Refactoring analysis failed: {e}")
            return []
    
    def _check_safety_compliance(self, grammar_result: GrammarValidationResult, 
                               safety_profile: Optional[str]) -> Dict[str, Any]:
        """Check compliance with safety profile."""
        compliance = {
            "profile": safety_profile,
            "compliant": len(grammar_result.violations) == 0,
            "violations": grammar_result.violations,
            "nasa_compliant": False
        }
        
        if self.safety_compliance and safety_profile:
            # Check General Safety-specific compliance
            nasa_violations = [v for v in grammar_result.violations 
                             if v.get('rule', '').startswith('nasa_')]
            compliance["nasa_compliant"] = len(nasa_violations) == 0
            compliance["nasa_violations"] = nasa_violations
        
        return compliance
    
    def _create_generation_constraints(self, language: LanguageSupport, 
                                     safety_profile: Optional[str]) -> GenerationConstraints:
        """Create generation constraints based on language and safety profile."""
        
        overlays = []
        mode = GenerationMode.GUIDED
        
        if safety_profile:
            overlays.append(f"{language.value}_{safety_profile}")
            if self.safety_compliance:
                mode = GenerationMode.STRICT
        
        return GenerationConstraints(
            language=language,
            overlays=overlays,
            mode=mode,
            max_tokens=1000
        )
    
    def _generate_safe_alternative(self, violation: Dict[str, Any], 
                                 constraints: Optional[GenerationConstraints]) -> Optional[str]:
        """Generate a safe alternative for a safety violation."""
        if not self.constrained_generator or not constraints:
            return None
        
        # This would use the constrained generator to create safe alternatives
        # Implementation depends on specific violation types
        return None
    
    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if file should be skipped."""
        skip_patterns = [
            "__pycache__", ".pytest_cache", "node_modules", "venv", ".venv",
            "migrations", "test_", "_test.py"
        ]
        return any(pattern in str(file_path) for pattern in skip_patterns)
    
    def _create_error_result(self, file_path: Path, language: LanguageSupport, 
                           error: str) -> EnhancedAnalysisResult:
        """Create an error result when analysis fails."""
        return EnhancedAnalysisResult(
            file_path=str(file_path),
            language=language,
            grammar_validation=GrammarValidationResult(
                is_valid=False,
                language=language,
                parse_errors=[error]
            )
        )


def create_analyzer_for_profile(profile_name: str) -> GrammarEnhancedAnalyzer:
    """Factory function to create analyzer with specific profile."""
    
    if profile_name == "general_safety_strict":
        return GrammarEnhancedAnalyzer(
            enable_safety_profiles=True,
            safety_compliance=True
        )
    elif profile_name == "django":
        return GrammarEnhancedAnalyzer(
            framework_profile=FrameworkProfile.django_profile()
        )
    elif profile_name == "fastapi":
        return GrammarEnhancedAnalyzer(
            framework_profile=FrameworkProfile.fastapi_profile()
        )
    else:
        return GrammarEnhancedAnalyzer()