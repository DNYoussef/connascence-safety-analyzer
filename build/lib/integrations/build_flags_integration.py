"""
Build Flags Integration for Connascence Analysis

Integrates with build systems to verify compiler flags and build configuration
compliance with General Safety Standards Rule 10: "Use compiler warnings set to their
most pedantic setting" and "All code must compile without warnings."

Supports multiple compilers and build systems for comprehensive flag verification.
"""

import subprocess
import re
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass


@dataclass
class CompilerInfo:
    """Information about a detected compiler."""
    name: str
    path: str
    version: str
    supported_flags: Set[str]


@dataclass 
class BuildSystemInfo:
    """Information about detected build system."""
    name: str
    config_files: List[Path]
    build_commands: List[str]


class BuildFlagsIntegration:
    """Integration with build systems and compilers for flag verification."""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.description = "Build system and compiler flag verification"
        self._compiler_cache: Optional[Dict[str, CompilerInfo]] = None
        self._build_system_cache: Optional[BuildSystemInfo] = None
    
    def is_available(self) -> bool:
        """Check if build flag verification is available."""
        compilers = self._detect_compilers()
        return len(compilers) > 0
    
    def get_version(self) -> str:
        """Get build system integration version.""" 
        return "1.0.0"
    
    def analyze(self, project_path: Path) -> Dict[str, Any]:
        """Analyze project for build flag compliance."""
        project_path = Path(project_path)
        
        # Detect compilers and build system
        compilers = self._detect_compilers()
        build_system = self._detect_build_system(project_path)
        
        # Analyze compiler flags
        flag_analysis = self._analyze_compiler_flags(project_path, compilers, build_system)
        
        # Verify General Safety requirements
        nasa_compliance = self._check_nasa_compliance(flag_analysis)
        
        # Generate recommendations
        recommendations = self._generate_flag_recommendations(flag_analysis, nasa_compliance)
        
        return {
            'compilers_detected': {name: self._compiler_to_dict(comp) for name, comp in compilers.items()},
            'build_system': self._build_system_to_dict(build_system) if build_system else None,
            'flag_analysis': flag_analysis,
            'nasa_compliance': nasa_compliance,
            'recommendations': recommendations,
            'execution_successful': True
        }
    
    def _detect_compilers(self) -> Dict[str, CompilerInfo]:
        """Detect available compilers and their capabilities."""
        if self._compiler_cache is not None:
            return self._compiler_cache
        
        compilers = {}
        
        # GCC Detection
        gcc_info = self._detect_gcc()
        if gcc_info:
            compilers['gcc'] = gcc_info
        
        # Clang Detection
        clang_info = self._detect_clang()
        if clang_info:
            compilers['clang'] = clang_info
        
        # MSVC Detection
        msvc_info = self._detect_msvc()
        if msvc_info:
            compilers['msvc'] = msvc_info
        
        self._compiler_cache = compilers
        return compilers
    
    def _detect_gcc(self) -> Optional[CompilerInfo]:
        """Detect GCC compiler."""
        try:
            # Check if gcc is available
            result = subprocess.run(['gcc', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                return None
            
            # Parse version
            version_match = re.search(r'gcc.*?(\d+\.\d+\.\d+)', result.stdout)
            version = version_match.group(1) if version_match else 'unknown'
            
            # Get path
            path_result = subprocess.run(['which', 'gcc'], 
                                       capture_output=True, text=True, timeout=5)
            path = path_result.stdout.strip() if path_result.returncode == 0 else 'gcc'
            
            # Standard GCC warning flags
            supported_flags = {
                '-Wall', '-Wextra', '-Werror', '-pedantic', '-Wcast-qual',
                '-Wcast-align', '-Wwrite-strings', '-Wredundant-decls',
                '-Winline', '-Wunused', '-Wuninitialized', '-Wshadow',
                '-Wstrict-prototypes', '-Wmissing-prototypes', '-Wconversion',
                '-Wsign-conversion', '-Wformat=2', '-Wformat-security',
                '-fstack-protector-all', '-D_FORTIFY_SOURCE=2'
            }
            
            return CompilerInfo(
                name='gcc',
                path=path,
                version=version,
                supported_flags=supported_flags
            )
            
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            return None
    
    def _detect_clang(self) -> Optional[CompilerInfo]:
        """Detect Clang compiler."""
        try:
            result = subprocess.run(['clang', '--version'],
                                  capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                return None
            
            # Parse version  
            version_match = re.search(r'clang version (\d+\.\d+\.\d+)', result.stdout)
            version = version_match.group(1) if version_match else 'unknown'
            
            # Get path
            path_result = subprocess.run(['which', 'clang'],
                                       capture_output=True, text=True, timeout=5) 
            path = path_result.stdout.strip() if path_result.returncode == 0 else 'clang'
            
            # Clang warning flags
            supported_flags = {
                '-Wall', '-Wextra', '-Werror', '-pedantic', '-Weverything',
                '-Wcast-qual', '-Wcast-align', '-Wwrite-strings', '-Wunused',
                '-Wuninitialized', '-Wshadow', '-Wconversion', '-Wsign-conversion',
                '-Wformat=2', '-Wformat-security', '-fstack-protector-all',
                '-D_FORTIFY_SOURCE=2', '-fsanitize=address', '-fsanitize=undefined'
            }
            
            return CompilerInfo(
                name='clang', 
                path=path,
                version=version,
                supported_flags=supported_flags
            )
            
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            return None
    
    def _detect_msvc(self) -> Optional[CompilerInfo]:
        """Detect MSVC compiler."""
        try:
            # Try to detect MSVC through cl.exe
            result = subprocess.run(['cl'], capture_output=True, text=True, timeout=10)
            
            # MSVC returns error when called without args, but shows version
            if 'Microsoft' in result.stderr and 'Compiler' in result.stderr:
                version_match = re.search(r'Version (\d+\.\d+\.\d+)', result.stderr)
                version = version_match.group(1) if version_match else 'unknown'
                
                supported_flags = {
                    '/W4', '/WX', '/Wall', '/analyze', '/sdl', '/guard:cf',
                    '/Qspectre', '/GS', '/RTC1', '/D_CRT_SECURE_NO_WARNINGS'
                }
                
                return CompilerInfo(
                    name='msvc',
                    path='cl.exe',
                    version=version,
                    supported_flags=supported_flags
                )
                
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            pass
        
        return None
    
    def _detect_build_system(self, project_path: Path) -> Optional[BuildSystemInfo]:
        """Detect build system in use."""
        if self._build_system_cache is not None:
            return self._build_system_cache
        
        build_system = None
        
        # Check for various build system files
        if (project_path / 'CMakeLists.txt').exists():
            build_system = BuildSystemInfo(
                name='cmake',
                config_files=[project_path / 'CMakeLists.txt'],
                build_commands=['cmake', 'make', 'ninja']
            )
        elif (project_path / 'Makefile').exists() or (project_path / 'makefile').exists():
            makefile = project_path / 'Makefile' if (project_path / 'Makefile').exists() else project_path / 'makefile'
            build_system = BuildSystemInfo(
                name='make',
                config_files=[makefile],
                build_commands=['make']
            )
        elif (project_path / 'meson.build').exists():
            build_system = BuildSystemInfo(
                name='meson',
                config_files=[project_path / 'meson.build'],
                build_commands=['meson', 'ninja']
            )
        elif (project_path / 'pyproject.toml').exists():
            build_system = BuildSystemInfo(
                name='python',
                config_files=[project_path / 'pyproject.toml'],
                build_commands=['pip', 'setuptools', 'poetry']
            )
        
        self._build_system_cache = build_system
        return build_system
    
    def _analyze_compiler_flags(self, project_path: Path, 
                               compilers: Dict[str, CompilerInfo],
                               build_system: Optional[BuildSystemInfo]) -> Dict[str, Any]:
        """Analyze compiler flags configuration."""
        analysis = {
            'detected_flags': {},
            'missing_flags': {},
            'build_system_config': {},
            'compilation_test': {}
        }
        
        # Analyze build system configuration
        if build_system:
            analysis['build_system_config'] = self._analyze_build_system_config(
                build_system, project_path
            )
        
        # Test actual compilation flags
        for compiler_name, compiler in compilers.items():
            analysis['detected_flags'][compiler_name] = self._get_active_compiler_flags(
                compiler, project_path
            )
            
            analysis['missing_flags'][compiler_name] = self._check_missing_flags(
                compiler, analysis['detected_flags'][compiler_name]
            )
            
            # Test compilation with required flags
            analysis['compilation_test'][compiler_name] = self._test_compilation_with_flags(
                compiler, project_path
            )
        
        return analysis
    
    def _analyze_build_system_config(self, build_system: BuildSystemInfo, 
                                   project_path: Path) -> Dict[str, Any]:
        """Analyze build system configuration files."""
        config_analysis = {
            'system': build_system.name,
            'config_files_analyzed': [],
            'flags_found': [],
            'warning_level': 'unknown'
        }
        
        for config_file in build_system.config_files:
            if not config_file.exists():
                continue
                
            try:
                content = config_file.read_text(encoding='utf-8')
                config_analysis['config_files_analyzed'].append(str(config_file))
                
                if build_system.name == 'cmake':
                    flags = self._parse_cmake_flags(content)
                    config_analysis['flags_found'].extend(flags)
                elif build_system.name == 'make':
                    flags = self._parse_makefile_flags(content)
                    config_analysis['flags_found'].extend(flags)
                elif build_system.name == 'python':
                    flags = self._parse_python_build_flags(content)
                    config_analysis['flags_found'].extend(flags)
                    
            except Exception as e:
                config_analysis[f'error_{config_file.name}'] = str(e)
        
        # Determine warning level
        flags = config_analysis['flags_found']
        if any(flag in flags for flag in ['-Wall', '/W4']):
            if any(flag in flags for flag in ['-Werror', '/WX']):
                config_analysis['warning_level'] = 'warnings_as_errors'
            else:
                config_analysis['warning_level'] = 'high_warnings'
        else:
            config_analysis['warning_level'] = 'minimal_warnings'
        
        return config_analysis
    
    def _parse_cmake_flags(self, content: str) -> List[str]:
        """Parse compiler flags from CMakeLists.txt."""
        flags = []
        
        # Look for CMAKE_CXX_FLAGS, CMAKE_C_FLAGS, target_compile_options
        flag_patterns = [
            r'CMAKE_C_FLAGS[^"]*"([^"]*)"',
            r'CMAKE_CXX_FLAGS[^"]*"([^"]*)"', 
            r'target_compile_options[^"]*"([^"]*)"',
            r'add_compile_options\s*\(\s*([^)]+)\)',
        ]
        
        for pattern in flag_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                # Split flags and clean them
                flag_list = match.replace('"', '').split()
                flags.extend(flag_list)
        
        return [flag.strip() for flag in flags if flag.strip().startswith(('-', '/'))]
    
    def _parse_makefile_flags(self, content: str) -> List[str]:
        """Parse compiler flags from Makefile."""
        flags = []
        
        # Look for CFLAGS, CXXFLAGS, etc.
        flag_patterns = [
            r'CFLAGS\s*[=+:]=[^\\]*?([^\\]+)',
            r'CXXFLAGS\s*[=+:]=[^\\]*?([^\\]+)', 
            r'CPPFLAGS\s*[=+:]=[^\\]*?([^\\]+)',
            r'LDFLAGS\s*[=+:]=[^\\]*?([^\\]+)',
        ]
        
        for pattern in flag_patterns:
            matches = re.findall(pattern, content, re.MULTILINE)
            for match in matches:
                flag_list = match.split()
                flags.extend(flag_list)
        
        return [flag.strip() for flag in flags if flag.strip().startswith(('-', '/'))]
    
    def _parse_python_build_flags(self, content: str) -> List[str]:
        """Parse compiler flags from Python build configuration."""
        flags = []
        
        # For Python projects, look for compiler options in setup.py or pyproject.toml
        if 'extra_compile_args' in content:
            # This is a simplified parser - would need more sophisticated parsing
            compile_args_pattern = r'extra_compile_args\s*=\s*\[([^\]]+)\]'
            matches = re.findall(compile_args_pattern, content)
            for match in matches:
                # Extract flags from list
                flag_list = re.findall(r'["\']([^"\']+)["\']', match)
                flags.extend(flag_list)
        
        return flags
    
    def _get_active_compiler_flags(self, compiler: CompilerInfo, 
                                 project_path: Path) -> List[str]:
        """Get active compiler flags by testing compilation."""
        flags = []
        
        try:
            # Create a simple test file
            test_file = project_path / 'test_compile_flags.c'
            test_file.write_text('#include <stdio.h>\nint main(){return 0;}')
            
            # Try to compile with verbose output
            if compiler.name in ['gcc', 'clang']:
                result = subprocess.run([
                    compiler.path, '-v', '-c', str(test_file), '-o', '/tmp/test.o'
                ], capture_output=True, text=True, timeout=30)
                
                # Parse the verbose output for flags
                if result.returncode == 0 or 'success' in result.stderr.lower():
                    flags = self._parse_verbose_compiler_output(result.stderr)
            
            # Clean up
            if test_file.exists():
                test_file.unlink()
                
        except Exception:
            # If we can't test compilation, return empty list
            pass
        
        return flags
    
    def _parse_verbose_compiler_output(self, output: str) -> List[str]:
        """Parse compiler flags from verbose output.""" 
        flags = []
        
        # Look for flag patterns in the output
        flag_patterns = [
            r'(-W[a-zA-Z-]+)',
            r'(-f[a-zA-Z-]+)',
            r'(-O[0-3s])',
            r'(-D[A-Z_]+(?:=[^\s]*)?)',
        ]
        
        for pattern in flag_patterns:
            matches = re.findall(pattern, output)
            flags.extend(matches)
        
        return list(set(flags))  # Remove duplicates
    
    def _check_missing_flags(self, compiler: CompilerInfo, 
                           active_flags: List[str]) -> List[str]:
        """Check for missing important compiler flags."""
        active_flags_set = set(active_flags)
        
        # Required flags for safety-critical code
        if compiler.name in ['gcc', 'clang']:
            required_flags = {'-Wall', '-Werror', '-Wextra'}
            recommended_flags = {
                '-pedantic', '-Wcast-qual', '-Wcast-align', 
                '-Wwrite-strings', '-Wunused', '-Wshadow'
            }
        elif compiler.name == 'msvc':
            required_flags = {'/W4', '/WX'}
            recommended_flags = {'/Wall', '/analyze', '/sdl'}
        else:
            required_flags = set()
            recommended_flags = set()
        
        missing_required = required_flags - active_flags_set
        missing_recommended = recommended_flags - active_flags_set
        
        return {
            'required_missing': list(missing_required),
            'recommended_missing': list(missing_recommended)
        }
    
    def _test_compilation_with_flags(self, compiler: CompilerInfo, 
                                   project_path: Path) -> Dict[str, Any]:
        """Test compilation with General Safety-required flags."""
        test_results = {
            'test_file_compiled': False,
            'warnings_generated': [],
            'errors_generated': [],
            'nasa_flags_supported': True
        }
        
        try:
            # Create test file with potential issues
            test_file = project_path / 'nasa_flag_test.c'
            test_code = '''
#include <stdio.h>
#include <stdlib.h>

int main() {
    int unused_var = 5;  // Should generate warning
    char *ptr = malloc(10);  // Should warn about unchecked malloc
    printf("Hello");  // Should warn about unused return
    return 0;
}
'''
            test_file.write_text(test_code)
            
            # Test with General Safety flags
            if compiler.name in ['gcc', 'clang']:
                nasa_flags = ['-Wall', '-Wextra', '-Werror', '-pedantic']
            elif compiler.name == 'msvc':
                nasa_flags = ['/W4', '/WX']
            else:
                nasa_flags = []
            
            if nasa_flags:
                result = subprocess.run([
                    compiler.path, *nasa_flags, '-c', str(test_file), '-o', '/tmp/test.o'
                ], capture_output=True, text=True, timeout=30)
                
                test_results['test_file_compiled'] = result.returncode == 0
                test_results['warnings_generated'] = self._extract_warnings(result.stderr)
                test_results['errors_generated'] = self._extract_errors(result.stderr)
                
                # Should fail compilation due to -Werror
                test_results['nasa_flags_supported'] = result.returncode != 0
            
            # Clean up
            if test_file.exists():
                test_file.unlink()
                
        except Exception as e:
            test_results['error'] = str(e)
        
        return test_results
    
    def _extract_warnings(self, compiler_output: str) -> List[str]:
        """Extract warning messages from compiler output."""
        warnings = []
        for line in compiler_output.split('\n'):
            if 'warning:' in line.lower() or 'warn:' in line.lower():
                warnings.append(line.strip())
        return warnings
    
    def _extract_errors(self, compiler_output: str) -> List[str]:
        """Extract error messages from compiler output."""
        errors = []
        for line in compiler_output.split('\n'):
            if 'error:' in line.lower() and 'warning' not in line.lower():
                errors.append(line.strip())
        return errors
    
    def _check_nasa_compliance(self, flag_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Check compliance with General Safety Power of Ten Rule 10."""
        compliance = {
            'compliant': True,
            'rule_10_compliance': 'unknown',
            'compiler_warnings_as_errors': False,
            'static_analysis_enabled': False,
            'violations': []
        }
        
        # Check each compiler
        for compiler_name, flags_info in flag_analysis['detected_flags'].items():
            missing = flag_analysis['missing_flags'].get(compiler_name, {})
            
            # Check for warnings as errors
            if compiler_name in ['gcc', 'clang']:
                if '-Werror' not in flags_info and '-Werror' in missing.get('required_missing', []):
                    compliance['violations'].append(f"{compiler_name}: Missing -Werror flag")
                    compliance['compliant'] = False
                else:
                    compliance['compiler_warnings_as_errors'] = True
                    
            elif compiler_name == 'msvc':
                if '/WX' not in flags_info and '/WX' in missing.get('required_missing', []):
                    compliance['violations'].append(f"{compiler_name}: Missing /WX flag")
                    compliance['compliant'] = False
                else:
                    compliance['compiler_warnings_as_errors'] = True
            
            # Check for comprehensive warnings
            if compiler_name in ['gcc', 'clang']:
                if '-Wall' not in flags_info:
                    compliance['violations'].append(f"{compiler_name}: Missing -Wall flag")
                    compliance['compliant'] = False
            elif compiler_name == 'msvc':
                if '/W4' not in flags_info:
                    compliance['violations'].append(f"{compiler_name}: Missing /W4 flag")
                    compliance['compliant'] = False
            
            # Check for static analysis
            static_analysis_flags = {
                'gcc': ['-fanalyzer'],
                'clang': ['-analyze', '--analyze'],
                'msvc': ['/analyze']
            }
            
            if compiler_name in static_analysis_flags:
                for flag in static_analysis_flags[compiler_name]:
                    if flag in flags_info:
                        compliance['static_analysis_enabled'] = True
                        break
        
        # Determine overall Rule 10 compliance
        if compliance['compiler_warnings_as_errors'] and len(compliance['violations']) == 0:
            compliance['rule_10_compliance'] = 'compliant'
        elif compliance['compiler_warnings_as_errors']:
            compliance['rule_10_compliance'] = 'mostly_compliant'
        else:
            compliance['rule_10_compliance'] = 'non_compliant'
        
        return compliance
    
    def _generate_flag_recommendations(self, flag_analysis: Dict[str, Any],
                                     nasa_compliance: Dict[str, Any]) -> List[str]:
        """Generate recommendations for build flag improvements."""
        recommendations = []
        
        # General Safety Rule 10 recommendations
        if not nasa_compliance['compiler_warnings_as_errors']:
            recommendations.append(
                "Enable warnings-as-errors: Add -Werror (GCC/Clang) or /WX (MSVC) to enforce General Safety Rule 10"
            )
        
        # Specific compiler recommendations
        for compiler_name, missing in flag_analysis['missing_flags'].items():
            if missing.get('required_missing'):
                recommendations.append(
                    f"Add required {compiler_name} flags: {', '.join(missing['required_missing'])}"
                )
            
            if missing.get('recommended_missing') and len(missing['recommended_missing']) > 3:
                recommendations.append(
                    f"Consider adding recommended {compiler_name} flags for better safety: "
                    f"{', '.join(missing['recommended_missing'][:3])} and {len(missing['recommended_missing']) - 3} more"
                )
        
        # Static analysis recommendations
        if not nasa_compliance['static_analysis_enabled']:
            recommendations.append(
                "Enable static analysis: Add -fanalyzer (GCC), --analyze (Clang), or /analyze (MSVC)"
            )
        
        # Build system recommendations
        build_config = flag_analysis.get('build_system_config', {})
        if build_config.get('warning_level') == 'minimal_warnings':
            recommendations.append(
                f"Update {build_config.get('system', 'build system')} configuration to enable comprehensive warnings"
            )
        
        return recommendations
    
    def _compiler_to_dict(self, compiler: CompilerInfo) -> Dict[str, Any]:
        """Convert CompilerInfo to dictionary."""
        return {
            'name': compiler.name,
            'path': compiler.path,
            'version': compiler.version,
            'supported_flags_count': len(compiler.supported_flags)
        }
    
    def _build_system_to_dict(self, build_system: BuildSystemInfo) -> Dict[str, Any]:
        """Convert BuildSystemInfo to dictionary."""
        return {
            'name': build_system.name,
            'config_files': [str(f) for f in build_system.config_files],
            'build_commands': build_system.build_commands
        }