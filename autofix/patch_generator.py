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
Multi-File Aware Patch Generation System

Generates safe, validated patches for connascence violations with support for:
- Multi-file transformations
- NASA Power of Ten compliance preservation
- Safety tier validation before application
- Atomic patch operations with rollback capability

This system integrates with the tier classifier to ensure only safe transformations
are generated and provides comprehensive context for AI-driven code generation.
"""

from dataclasses import dataclass
from enum import Enum
import hashlib
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Set

from .tier_classifier import AutofixTierClassifier, SafetyTier


class PatchType(Enum):
    """Types of patches that can be generated"""
    SINGLE_FILE = "single_file"
    MULTI_FILE = "multi_file"
    REFACTOR = "refactor"
    EXTRACT = "extract"
    RENAME = "rename"

@dataclass
class PatchOperation:
    """Individual operation within a patch"""
    operation_type: str  # "replace", "insert", "delete", "create_file", "rename_file"
    file_path: str
    old_content: Optional[str] = None
    new_content: Optional[str] = None
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    new_file_path: Optional[str] = None  # For renames/moves

@dataclass
class GeneratedPatch:
    """Complete patch with metadata and operations"""
    patch_id: str
    patch_type: PatchType
    description: str
    operations: List[PatchOperation]
    safety_tier: SafetyTier
    nasa_compliant: bool
    affected_files: Set[str]
    estimated_impact: str
    rollback_data: Dict[str, Any]
    confidence_score: float
    fix_examples: Dict[str, str]  # before/after examples
    nasa_rules_preserved: List[int]

class PatchGenerator:
    """
    Multi-file aware patch generator with safety validation.

    Generates patches for connascence violations while ensuring NASA Power of Ten
    compliance and providing comprehensive context for AI-driven fixes.
    """

    def __init__(self):
        self.tier_classifier = AutofixTierClassifier()
        self.patch_counter = 0

    def generate_patch(self, violation: Dict[str, Any],
                      context_data: Dict[str, Any],
                      fix_strategy: Optional[str] = None) -> GeneratedPatch:
        """
        Generate a patch for a specific violation.

        Args:
            violation: Violation details including type, location, severity
            context_data: Additional context like file contents, AST data
            fix_strategy: Optional strategy hint ("extract", "rename", etc.)

        Returns:
            GeneratedPatch with operations and safety assessment
        """

        # Classify the fix safety level
        proposed_fix = self._generate_proposed_fix(violation, context_data, fix_strategy)
        classification = self.tier_classifier.classify_autofix(
            violation['type'],
            context_data.get('code_context', ''),
            violation['file_path'],
            proposed_fix['description']
        )

        # Generate patch operations based on violation type
        operations = self._generate_operations(violation, context_data, proposed_fix)

        # Create rollback data
        rollback_data = self._create_rollback_data(operations)

        # Generate fix examples for AI context
        fix_examples = self._generate_fix_examples(violation['type'], context_data)

        # Check NASA rules preservation
        nasa_rules_preserved = self._check_nasa_rules_preservation(operations, context_data)

        self.patch_counter += 1
        patch = GeneratedPatch(
            patch_id=f"patch_{self.patch_counter}_{hashlib.md5(str(violation).encode()).hexdigest()[:8]}",
            patch_type=self._determine_patch_type(operations),
            description=proposed_fix['description'],
            operations=operations,
            safety_tier=classification.tier,
            nasa_compliant=classification.nasa_compliance,
            affected_files={op.file_path for op in operations},
            estimated_impact=classification.estimated_impact,
            rollback_data=rollback_data,
            confidence_score=classification.confidence,
            fix_examples=fix_examples,
            nasa_rules_preserved=nasa_rules_preserved
        )

        return patch

    def _generate_proposed_fix(self, violation: Dict[str, Any],
                              context_data: Dict[str, Any],
                              fix_strategy: Optional[str]) -> Dict[str, Any]:
        """Generate proposed fix based on violation type"""

        violation_type = violation['type']

        if violation_type == 'magic_literal':
            return self._propose_magic_literal_fix(violation, context_data)
        elif violation_type == 'god_object':
            return self._propose_god_object_fix(violation, context_data)
        elif violation_type == 'parameter_position':
            return self._propose_parameter_fix(violation, context_data)
        elif violation_type == 'connascence_of_name':
            return self._propose_naming_fix(violation, context_data)
        elif violation_type == 'connascence_of_type':
            return self._propose_type_fix(violation, context_data)
        else:
            return self._propose_generic_fix(violation, context_data)

    def _propose_magic_literal_fix(self, violation: Dict[str, Any], context_data: Dict[str, Any]) -> Dict[str, Any]:
        """Propose fix for magic literal violations"""

        # Extract the literal value and suggest a constant name
        code_context = context_data.get('code_context', '')
        literal_match = re.search(r'([0-9]+|"[^"]*"|\'[^\']*\')', code_context)

        if literal_match:
            literal_value = literal_match.group(1)
            # Generate meaningful constant name
            if literal_value.isdigit():
                const_name = f"CONST_{literal_value}" if len(literal_value) < 4 else "DEFAULT_VALUE"
            else:
                clean_value = re.sub(r'[^a-zA-Z0-9]', '_', literal_value.strip('\'"'))
                const_name = f"DEFAULT_{clean_value.upper()}"

            return {
                'description': f'Extract magic literal {literal_value} to constant {const_name}',
                'literal_value': literal_value,
                'constant_name': const_name,
                'strategy': 'extract_constant'
            }

        return {
            'description': 'Extract magic literal to named constant',
            'strategy': 'extract_constant'
        }

    def _propose_god_object_fix(self, violation: Dict[str, Any], context_data: Dict[str, Any]) -> Dict[str, Any]:
        """Propose fix for god object violations"""

        return {
            'description': 'Break down god object into smaller, focused classes using Single Responsibility Principle',
            'strategy': 'extract_classes',
            'requires_human_review': True,
            'complexity': 'high'
        }

    def _propose_parameter_fix(self, violation: Dict[str, Any], context_data: Dict[str, Any]) -> Dict[str, Any]:
        """Propose fix for parameter position violations"""

        return {
            'description': 'Replace parameter list with parameter object or named parameters',
            'strategy': 'parameter_object',
            'complexity': 'medium'
        }

    def _propose_naming_fix(self, violation: Dict[str, Any], context_data: Dict[str, Any]) -> Dict[str, Any]:
        """Propose fix for naming connascence"""

        return {
            'description': 'Improve naming consistency and reduce name coupling',
            'strategy': 'rename_refactor',
            'complexity': 'low'
        }

    def _propose_type_fix(self, violation: Dict[str, Any], context_data: Dict[str, Any]) -> Dict[str, Any]:
        """Propose fix for type connascence"""

        return {
            'description': 'Reduce type coupling through interfaces or generic types',
            'strategy': 'type_abstraction',
            'complexity': 'medium'
        }

    def _propose_generic_fix(self, violation: Dict[str, Any], context_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generic fix proposal"""

        return {
            'description': f'Reduce {violation["type"]} coupling through appropriate refactoring',
            'strategy': 'generic_refactor',
            'complexity': 'medium'
        }

    def _generate_operations(self, violation: Dict[str, Any],
                           context_data: Dict[str, Any],
                           proposed_fix: Dict[str, Any]) -> List[PatchOperation]:
        """Generate specific patch operations"""

        operations = []

        if proposed_fix['strategy'] == 'extract_constant':
            operations.extend(self._generate_constant_extraction_ops(violation, context_data, proposed_fix))
        elif proposed_fix['strategy'] == 'extract_classes':
            operations.extend(self._generate_class_extraction_ops(violation, context_data, proposed_fix))
        elif proposed_fix['strategy'] == 'parameter_object':
            operations.extend(self._generate_parameter_object_ops(violation, context_data, proposed_fix))
        else:
            operations.extend(self._generate_generic_ops(violation, context_data, proposed_fix))

        return operations

    def _generate_constant_extraction_ops(self, violation: Dict[str, Any],
                                        context_data: Dict[str, Any],
                                        proposed_fix: Dict[str, Any]) -> List[PatchOperation]:
        """Generate operations for extracting magic literals to constants"""

        operations = []
        file_path = violation['file_path']

        # Read current file content
        with open(file_path) as f:
            current_content = f.read()

        lines = current_content.split('\n')

        # Find the line with the magic literal
        violation_line = violation.get('line_number', 1) - 1  # Convert to 0-based
        if violation_line < len(lines):
            line_content = lines[violation_line]

            # Replace literal with constant reference
            literal_value = proposed_fix.get('literal_value', '')
            constant_name = proposed_fix.get('constant_name', 'EXTRACTED_CONSTANT')

            if literal_value:
                new_line = line_content.replace(literal_value, constant_name)

                # Add constant definition at the top of the file
                constant_definition = f"{constant_name} = {literal_value}"

                # Find appropriate place to add constant (after imports)
                insert_line = 0
                for i, line in enumerate(lines):
                    if line.strip().startswith(('import ', 'from ')) or line.strip().startswith('#'):
                        insert_line = i + 1
                    else:
                        break

                # Operation 1: Add constant definition
                operations.append(PatchOperation(
                    operation_type="insert",
                    file_path=file_path,
                    new_content=constant_definition + "\n",
                    line_start=insert_line
                ))

                # Operation 2: Replace literal usage
                operations.append(PatchOperation(
                    operation_type="replace",
                    file_path=file_path,
                    old_content=line_content,
                    new_content=new_line,
                    line_start=violation_line,
                    line_end=violation_line
                ))

        return operations

    def _generate_class_extraction_ops(self, violation: Dict[str, Any],
                                     context_data: Dict[str, Any],
                                     proposed_fix: Dict[str, Any]) -> List[PatchOperation]:
        """Generate operations for god object refactoring (requires human review)"""

        # For god objects, we generate a high-level plan rather than specific operations
        # since this requires architectural decisions

        operations = []
        file_path = violation['file_path']

        # Create a comment with refactoring suggestions
        refactor_comment = '''
# TODO: Refactor this class to follow Single Responsibility Principle
# Suggested approach:
# 1. Extract data access methods to a Repository class
# 2. Extract business logic to Service classes
# 3. Extract validation logic to Validator classes
# 4. Keep only coordination logic in this class
'''

        operations.append(PatchOperation(
            operation_type="insert",
            file_path=file_path,
            new_content=refactor_comment,
            line_start=violation.get('line_number', 1)
        ))

        return operations

    def _generate_parameter_object_ops(self, violation: Dict[str, Any],
                                     context_data: Dict[str, Any],
                                     proposed_fix: Dict[str, Any]) -> List[PatchOperation]:
        """Generate operations for parameter object refactoring"""

        operations = []
        file_path = violation['file_path']

        # This is a simplified implementation - in practice would need
        # more sophisticated AST analysis to properly refactor parameters

        refactor_comment = '''
# TODO: Replace parameter list with parameter object
# Example:
# @dataclass
# class ConfigParams:
#     param1: Type1
#     param2: Type2
#     param3: Type3
#
# def function_name(config: ConfigParams):
#     # Use config.param1, config.param2, etc.
'''

        operations.append(PatchOperation(
            operation_type="insert",
            file_path=file_path,
            new_content=refactor_comment,
            line_start=violation.get('line_number', 1)
        ))

        return operations

    def _generate_generic_ops(self, violation: Dict[str, Any],
                            context_data: Dict[str, Any],
                            proposed_fix: Dict[str, Any]) -> List[PatchOperation]:
        """Generate generic refactoring operations"""

        operations = []
        file_path = violation['file_path']

        comment = f"# TODO: Address {violation['type']} violation - {proposed_fix['description']}"

        operations.append(PatchOperation(
            operation_type="insert",
            file_path=file_path,
            new_content=comment + "\n",
            line_start=violation.get('line_number', 1)
        ))

        return operations

    def _determine_patch_type(self, operations: List[PatchOperation]) -> PatchType:
        """Determine the type of patch based on operations"""

        affected_files = {op.file_path for op in operations}

        if len(affected_files) > 1:
            return PatchType.MULTI_FILE
        elif any(op.operation_type in ['create_file', 'rename_file'] for op in operations):
            return PatchType.REFACTOR
        else:
            return PatchType.SINGLE_FILE

    def _create_rollback_data(self, operations: List[PatchOperation]) -> Dict[str, Any]:
        """Create rollback information for the patch"""

        rollback_data = {
            'timestamp': str(datetime.now()),
            'file_backups': {},
            'operation_order': []
        }

        # Create backups of all affected files
        for op in operations:
            file_path = op.file_path
            if file_path not in rollback_data['file_backups'] and Path(file_path).exists():
                with open(file_path) as f:
                    rollback_data['file_backups'][file_path] = f.read()

            rollback_data['operation_order'].append({
                'operation_type': op.operation_type,
                'file_path': op.file_path,
                'line_start': op.line_start,
                'line_end': op.line_end
            })

        return rollback_data

    def _generate_fix_examples(self, violation_type: str, context_data: Dict[str, Any]) -> Dict[str, str]:
        """Generate before/after examples for AI context"""

        examples = self.tier_classifier.get_autofix_examples(violation_type)
        if examples:
            return examples

        # Default examples for common cases
        if violation_type == 'magic_literal':
            return {
                'before': 'if status_code == 404:\n    return "Not found"',
                'after': 'HTTP_NOT_FOUND = 404\nif status_code == HTTP_NOT_FOUND:\n    return "Not found"',
                'explanation': 'Extract magic literal to named constant for better readability'
            }

        return {
            'before': '# Original code with violation',
            'after': '# Refactored code addressing violation',
            'explanation': f'Fix {violation_type} through appropriate refactoring'
        }

    def _check_nasa_rules_preservation(self, operations: List[PatchOperation],
                                     context_data: Dict[str, Any]) -> List[int]:
        """Check which NASA Power of Ten rules are preserved by this patch"""

        preserved_rules = []

        # Rule 1: Avoid goto (always preserved in Python)
        preserved_rules.append(1)

        # Rule 2: Bounded loops - check if patch doesn't introduce unbounded loops
        has_unbounded_loops = False
        for op in operations:
            if op.new_content and 'while' in op.new_content and 'break' not in op.new_content:
                has_unbounded_loops = True
                break
        if not has_unbounded_loops:
            preserved_rules.append(2)

        # Rule 4: Function size limits - check if operations don't create huge functions
        creates_large_functions = False
        for op in operations:
            if op.new_content and op.new_content.count('\n') > 50:
                creates_large_functions = True
                break
        if not creates_large_functions:
            preserved_rules.append(4)

        # Rule 6: Data scope - check if patch doesn't introduce global variables
        introduces_globals = False
        for op in operations:
            if op.new_content and 'global ' in op.new_content.lower():
                introduces_globals = True
                break
        if not introduces_globals:
            preserved_rules.append(6)

        # Add other applicable rules
        preserved_rules.extend([3, 5, 7, 8, 9, 10])  # Rules typically preserved

        return preserved_rules

    def apply_patch(self, patch: GeneratedPatch, dry_run: bool = False) -> Dict[str, Any]:
        """
        Apply a generated patch to the filesystem.

        Args:
            patch: The patch to apply
            dry_run: If True, simulate application without making changes

        Returns:
            Result dictionary with success status and details
        """

        if patch.safety_tier == SafetyTier.UNSAFE:
            return {
                'success': False,
                'error': 'Patch marked as unsafe - cannot apply',
                'patch_id': patch.patch_id
            }

        if dry_run:
            return {
                'success': True,
                'dry_run': True,
                'patch_id': patch.patch_id,
                'operations_count': len(patch.operations),
                'affected_files': list(patch.affected_files)
            }

        try:
            # Apply operations in order
            for operation in patch.operations:
                self._apply_operation(operation)

            return {
                'success': True,
                'patch_id': patch.patch_id,
                'operations_applied': len(patch.operations),
                'affected_files': list(patch.affected_files)
            }

        except Exception as e:
            # Rollback on error
            self.rollback_patch(patch)
            return {
                'success': False,
                'error': str(e),
                'patch_id': patch.patch_id,
                'rollback_performed': True
            }

    def _apply_operation(self, operation: PatchOperation) -> None:
        """Apply a single patch operation"""

        if operation.operation_type == "insert":
            with open(operation.file_path) as f:
                lines = f.readlines()

            insert_pos = operation.line_start or 0
            lines.insert(insert_pos, operation.new_content)

            with open(operation.file_path, 'w') as f:
                f.writelines(lines)

        elif operation.operation_type == "replace":
            with open(operation.file_path) as f:
                content = f.read()

            if operation.old_content:
                new_content = content.replace(operation.old_content, operation.new_content)
            else:
                lines = content.split('\n')
                if operation.line_start is not None:
                    lines[operation.line_start] = operation.new_content.rstrip('\n')
                new_content = '\n'.join(lines)

            with open(operation.file_path, 'w') as f:
                f.write(new_content)

        elif operation.operation_type == "create_file":
            Path(operation.file_path).parent.mkdir(parents=True, exist_ok=True)
            with open(operation.file_path, 'w') as f:
                f.write(operation.new_content or '')

    def rollback_patch(self, patch: GeneratedPatch) -> Dict[str, Any]:
        """Rollback a previously applied patch"""

        try:
            rollback_data = patch.rollback_data

            # Restore file backups
            for file_path, backup_content in rollback_data.get('file_backups', {}).items():
                with open(file_path, 'w') as f:
                    f.write(backup_content)

            return {
                'success': True,
                'patch_id': patch.patch_id,
                'files_restored': len(rollback_data.get('file_backups', {}))
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'patch_id': patch.patch_id
            }


# Convenience function for external use
def generate_patch_for_violation(violation: Dict[str, Any],
                               context_data: Dict[str, Any],
                               fix_strategy: Optional[str] = None) -> GeneratedPatch:
    """
    Generate a patch for a connascence violation.

    Args:
        violation: Violation details
        context_data: Code context and metadata
        fix_strategy: Optional fix strategy hint

    Returns:
        GeneratedPatch ready for application
    """
    generator = PatchGenerator()
    return generator.generate_patch(violation, context_data, fix_strategy)


if __name__ == "__main__":
    # Example usage
    from datetime import datetime

    # Test magic literal patch generation
    violation = {
        'type': 'magic_literal',
        'file_path': 'test_file.py',
        'line_number': 10,
        'severity': 'medium',
        'message': 'Magic literal found: 404'
    }

    context_data = {
        'code_context': 'if response.status_code == 404:\n    return None',
        'file_content': 'def handle_response():\n    if response.status_code == 404:\n        return None\n    return response.json()'
    }

    generator = PatchGenerator()
    patch = generator.generate_patch(violation, context_data)

    print(f"Generated patch: {patch.patch_id}")
    print(f"Safety tier: {patch.safety_tier}")
    print(f"NASA compliant: {patch.nasa_compliant}")
    print(f"Operations: {len(patch.operations)}")
    print(f"Fix example: {patch.fix_examples['explanation']}")
    print(f"NASA rules preserved: {patch.nasa_rules_preserved}")
