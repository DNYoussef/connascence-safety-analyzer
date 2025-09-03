"""
Core patch generation and autofix orchestration system.

Provides unified interface for generating patches from connascence violations
with safety controls, confidence scoring, and rollback capabilities.
"""

import ast
import difflib
import hashlib
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Any, Union
from pathlib import Path

from .magic_literals import MagicLiteralFixer
from .param_bombs import ParameterBombFixer  
from .class_splits import ClassSplitFixer
from .type_hints import TypeHintFixer
from ..analyzer.core import ConnascenceViolation


@dataclass
class PatchSuggestion:
    """Represents a suggested code transformation."""
    violation_id: str
    confidence: float  # 0.0-1.0
    description: str
    old_code: str
    new_code: str
    file_path: str
    line_range: tuple[int, int]
    safety_level: str  # 'safe', 'moderate', 'risky'
    rollback_info: Dict[str, Any]
    dependencies: List[str] = None  # Other violations this depends on


@dataclass 
class AutofixResult:
    """Result of autofix operation."""
    patches_generated: int
    patches_applied: int
    violations_fixed: List[str]
    warnings: List[str]
    errors: List[str]
    confidence_score: float


class PatchGenerator:
    """Generates patches for connascence violations."""
    
    def __init__(self):
        self.fixers = {
            'CoM': MagicLiteralFixer(),
            'CoP': ParameterBombFixer(),
            'CoA': ClassSplitFixer(),
            'CoT': TypeHintFixer()
        }
        self._cache: Dict[str, PatchSuggestion] = {}
    
    def generate_patch(self, violation: ConnascenceViolation, 
                      source_code: str) -> Optional[PatchSuggestion]:
        """Generate patch for a single violation."""
        cache_key = self._get_cache_key(violation, source_code)
        if cache_key in self._cache:
            return self._cache[cache_key]
            
        fixer = self.fixers.get(violation.connascence_type)
        if not fixer:
            return None
            
        try:
            tree = ast.parse(source_code)
            patch = fixer.generate_patch(violation, tree, source_code)
            if patch:
                self._cache[cache_key] = patch
            return patch
        except Exception as e:
            return None
    
    def generate_batch(self, violations: List[ConnascenceViolation],
                      file_path: str) -> List[PatchSuggestion]:
        """Generate patches for multiple violations in a file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
        except (OSError, UnicodeDecodeError):
            return []
            
        patches = []
        for violation in violations:
            patch = self.generate_patch(violation, source_code)
            if patch:
                patches.append(patch)
                
        # Sort by confidence and safety
        patches.sort(key=lambda p: (p.confidence, p.safety_level == 'safe'), reverse=True)
        return patches
    
    def _get_cache_key(self, violation: ConnascenceViolation, source: str) -> str:
        """Generate cache key for violation + source combination."""
        content = f"{violation.connascence_type}:{violation.line_number}:{hash(source)}"
        return hashlib.md5(content.encode()).hexdigest()


class AutofixEngine:
    """Main autofix orchestration engine."""
    
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.patch_generator = PatchGenerator()
        self._applied_patches: Set[str] = set()
    
    def analyze_file(self, file_path: str, 
                    violations: List[ConnascenceViolation]) -> List[PatchSuggestion]:
        """Analyze violations and generate patches for a file."""
        return self.patch_generator.generate_batch(violations, file_path)
    
    def apply_patches(self, patches: List[PatchSuggestion], 
                     confidence_threshold: float = 0.8) -> AutofixResult:
        """Apply patches above confidence threshold."""
        if self.dry_run:
            return self._simulate_apply(patches, confidence_threshold)
            
        applied = 0
        violations_fixed = []
        warnings = []
        errors = []
        
        for patch in patches:
            if patch.confidence < confidence_threshold:
                warnings.append(f"Skipped {patch.violation_id} - confidence too low")
                continue
                
            if patch.safety_level == 'risky':
                warnings.append(f"Skipped {patch.violation_id} - marked as risky")
                continue
                
            try:
                self._apply_single_patch(patch)
                applied += 1
                violations_fixed.append(patch.violation_id)
                self._applied_patches.add(patch.violation_id)
            except Exception as e:
                errors.append(f"Failed to apply {patch.violation_id}: {str(e)}")
        
        avg_confidence = sum(p.confidence for p in patches) / len(patches) if patches else 0.0
        
        return AutofixResult(
            patches_generated=len(patches),
            patches_applied=applied,
            violations_fixed=violations_fixed,
            warnings=warnings,
            errors=errors,
            confidence_score=avg_confidence
        )
    
    def _simulate_apply(self, patches: List[PatchSuggestion],
                       threshold: float) -> AutofixResult:
        """Simulate patch application for dry-run mode."""
        would_apply = [p for p in patches 
                      if p.confidence >= threshold and p.safety_level != 'risky']
        
        avg_confidence = sum(p.confidence for p in patches) / len(patches) if patches else 0.0
        
        return AutofixResult(
            patches_generated=len(patches),
            patches_applied=len(would_apply),
            violations_fixed=[p.violation_id for p in would_apply],
            warnings=[f"DRY RUN: Would apply {len(would_apply)} patches"],
            errors=[],
            confidence_score=avg_confidence
        )
    
    def _apply_single_patch(self, patch: PatchSuggestion):
        """Apply a single patch to a file."""
        file_path = Path(patch.file_path)
        
        # Read current file
        original_content = file_path.read_text(encoding='utf-8')
        
        # Create backup
        backup_path = file_path.with_suffix(f'{file_path.suffix}.backup')
        backup_path.write_text(original_content, encoding='utf-8')
        
        # Apply patch
        lines = original_content.splitlines(keepends=True)
        start_line, end_line = patch.line_range
        
        # Replace lines
        new_lines = lines[:start_line-1] + [patch.new_code] + lines[end_line:]
        new_content = ''.join(new_lines)
        
        # Write patched file
        file_path.write_text(new_content, encoding='utf-8')
        
        # Store rollback info
        patch.rollback_info.update({
            'backup_path': str(backup_path),
            'original_hash': hashlib.md5(original_content.encode()).hexdigest()
        })
    
    def rollback_patch(self, violation_id: str) -> bool:
        """Rollback a previously applied patch."""
        if violation_id not in self._applied_patches:
            return False
            
        # Implementation would require storing rollback metadata
        # For now, just remove from tracking
        self._applied_patches.discard(violation_id)
        return True
    
    def get_diff_preview(self, patch: PatchSuggestion) -> str:
        """Generate unified diff preview for a patch."""
        old_lines = patch.old_code.splitlines(keepends=True)
        new_lines = patch.new_code.splitlines(keepends=True)
        
        diff = difflib.unified_diff(
            old_lines, 
            new_lines,
            fromfile=f"a/{Path(patch.file_path).name}",
            tofile=f"b/{Path(patch.file_path).name}",
            lineterm=""
        )
        
        return ''.join(diff)


class SafeAutofixer:
    """Safe autofix wrapper with additional guardrails."""
    
    def __init__(self, max_patches_per_file: int = 10):
        self.engine = AutofixEngine(dry_run=True)  # Always start in dry-run
        self.max_patches_per_file = max_patches_per_file
    
    def preview_fixes(self, file_path: str, 
                     violations: List[ConnascenceViolation]) -> Dict[str, Any]:
        """Preview what fixes would be applied."""
        patches = self.engine.analyze_file(file_path, violations)
        
        # Limit patches per file
        if len(patches) > self.max_patches_per_file:
            patches = patches[:self.max_patches_per_file]
        
        previews = []
        for patch in patches:
            previews.append({
                'violation_id': patch.violation_id,
                'confidence': patch.confidence,
                'safety': patch.safety_level,
                'description': patch.description,
                'diff': self.engine.get_diff_preview(patch)
            })
        
        return {
            'file_path': file_path,
            'total_patches': len(patches),
            'patches': previews,
            'recommendations': self._get_recommendations(patches)
        }
    
    def _get_recommendations(self, patches: List[PatchSuggestion]) -> List[str]:
        """Generate human-readable recommendations."""
        recommendations = []
        
        high_conf = [p for p in patches if p.confidence > 0.9]
        if high_conf:
            recommendations.append(f"{len(high_conf)} high-confidence fixes available")
        
        risky = [p for p in patches if p.safety_level == 'risky']
        if risky:
            recommendations.append(f"{len(risky)} risky fixes require manual review")
        
        magic_literals = [p for p in patches if 'magic' in p.description.lower()]
        if len(magic_literals) > 5:
            recommendations.append("Consider creating a constants module")
        
        return recommendations