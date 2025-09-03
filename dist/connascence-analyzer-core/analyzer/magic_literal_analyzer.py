#!/usr/bin/env python3
"""Enhanced Magic Literal Analyzer with Contextual Intelligence.

This analyzer implements domain-aware detection to reduce false positives
while maintaining safety for true magic literals. Features:
- Statistical outlier detection instead of fixed thresholds
- Domain-aware allowlists (time, percentages, bitmasks, powers of 2)
- Contextual analysis for usage patterns
- Framework-specific rule relaxation
- Integration with grammar layer for AST-safe analysis
"""

import ast
from dataclasses import dataclass, field
from enum import Enum
import json
import logging
import math
from pathlib import Path
import re
import statistics
from typing import Any, Dict, List, Optional, Set, Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ContextType(Enum):
    """Types of contexts for magic literal usage."""
    BITMASK = "bitmask"
    UNIT_TAGGED = "unit_tagged"
    LOOP_INDEX = "loop_index"
    TEST_SEED = "test_seed"
    PROTOCOL_BOUNDARY = "protocol_boundary"
    MATHEMATICAL = "mathematical"
    POWER_OF_TWO = "power_of_two"
    TIME_UNIT = "time_unit"
    PERCENTAGE = "percentage"
    GENERIC = "generic"


@dataclass
class DomainAllowlist:
    """Domain-specific allowlists for magic literals."""
    
    # Always safe integers
    safe_integers: Set[int] = field(default_factory=lambda: {
        -1, 0, 1, 2, 3, 4, 5, 7, 10, 12, 24, 60, 100, 1000, 1024
    })
    
    # Powers of 2 up to reasonable limits
    powers_of_two: Set[int] = field(default_factory=lambda: {
        1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192
    })
    
    # Common time units (seconds)
    time_units: Set[int] = field(default_factory=lambda: {
        60, 300, 600, 900, 1800, 3600, 7200, 86400  # 1min, 5min, 10min, 15min, 30min, 1h, 2h, 1day
    })
    
    # Common percentages as integers
    percentages: Set[int] = field(default_factory=lambda: {
        5, 10, 15, 20, 25, 30, 40, 50, 60, 70, 75, 80, 85, 90, 95
    })
    
    # Common floats
    safe_floats: Set[float] = field(default_factory=lambda: {
        0.0, 0.5, 1.0, 1.5, 2.0, -1.0, 0.1, 0.25, 0.75, 0.01, 0.001
    })
    
    # Unit suffixes that indicate intentional values
    unit_patterns: List[str] = field(default_factory=lambda: [
        r'.*_(ms|sec|min|hour|day|px|dp|pt|em|rem|mb|kb|gb|tb)\b',
        r'.*_(timeout|interval|delay|duration|size|count|limit)\b',
        r'(width|height|margin|padding|border)_.*',
    ])
    
    # Bitmask operation indicators
    bitmask_operators: Set[str] = field(default_factory=lambda: {'&', '|', '^', '<<', '>>', '~'})


@dataclass
class StatisticalThresholds:
    """Statistical thresholds for magic literal detection."""
    
    repeat_threshold: int = 2  # Flag when repeated this many times
    outlier_percentile: float = 95.0  # Flag values above this percentile
    min_usage_for_stats: int = 10  # Minimum usage count for statistical analysis
    context_similarity_threshold: float = 0.7  # How similar contexts must be


@dataclass
class MagicLiteral:
    """Represents a magic literal found in the code."""

    value: Any
    file_path: str
    line_number: int
    column: int
    context: str
    category: str = "unknown"
    severity: str = "medium"
    in_conditional: bool = False
    suggested_constant: str = ""


@dataclass
class PackageStats:
    """Statistics for a package's magic literal usage."""

    package_name: str
    total_literals: int = 0
    literals_by_category: dict[str, int] = field(default_factory=dict)
    literals_by_severity: dict[str, int] = field(default_factory=dict)
    files_with_literals: set[str] = field(default_factory=set)
    constants_modules: list[str] = field(default_factory=list)


class MagicLiteralAnalyzer(ast.NodeVisitor):
    """AST visitor to detect magic literals."""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.literals: list[MagicLiteral] = []
        self.lines = []

        # Load file content for context
        try:
            with open(file_path, encoding="utf-8") as f:
                self.lines = f.readlines()
        except Exception as e:
            logger.warning(f"Could not read {file_path}: {e}")

    def visit_Constant(self, node: ast.Constant) -> None:
        """Visit constant nodes (Python 3.8+)."""
        if self._should_analyze_literal(node.value):
            literal = self._create_magic_literal(node, node.value)
            if literal is not None:  # None means context analysis filtered it out
                self.literals.append(literal)
        self.generic_visit(node)

    def visit_Num(self, node: ast.Num) -> None:
        """Visit numeric literals (deprecated but still used)."""
        if self._should_analyze_literal(node.n):
            literal = self._create_magic_literal(node, node.n)
            if literal is not None:
                self.literals.append(literal)
        self.generic_visit(node)

    def visit_Str(self, node: ast.Str) -> None:
        """Visit string literals (deprecated but still used)."""
        if self._should_analyze_literal(node.s):
            literal = self._create_magic_literal(node, node.s)
            if literal is not None:
                self.literals.append(literal)
        self.generic_visit(node)

    def _should_analyze_literal(self, value: Any) -> bool:
        """Determine if a literal should be analyzed using contextual intelligence."""
        # Initialize domain allowlist if not exists
        if not hasattr(self, '_domain_allowlist'):
            self._domain_allowlist = DomainAllowlist()
        
        # Skip boolean, None, and empty strings
        if value in (True, False, None, ""):
            return False
        
        # Context-aware integer analysis
        if isinstance(value, int):
            # Always safe integers
            if value in self._domain_allowlist.safe_integers:
                return False
            
            # Powers of 2 in potential bitmask contexts
            if value in self._domain_allowlist.powers_of_two:
                return False  # Let context analysis decide later
            
            # Time units
            if value in self._domain_allowlist.time_units:
                return False  # Context will determine if it's time-related
            
            # Percentages
            if value in self._domain_allowlist.percentages:
                return False
            
            # Analyze other integers
            return abs(value) >= 2
        
        # Context-aware float analysis
        if isinstance(value, float):
            # Safe floats
            if value in self._domain_allowlist.safe_floats:
                return False
            
            # Mathematical constants (pi, e, etc.)
            if abs(value - math.pi) < 0.001 or abs(value - math.e) < 0.001:
                return False
            
            return abs(value) >= 2.0
        
        # String analysis
        if isinstance(value, str):
            # Skip very short strings
            if len(value) <= 2:
                return False
            
            # Skip common encodings and formats
            if value.lower() in {"utf-8", "ascii", "json", "xml", "html", "csv"}:
                return False
            
            # Skip single character repeated (like "---", "===" for formatting)
            if len(set(value)) == 1 and len(value) >= 3:
                return False
            
            return len(value) > 2
        
        return False

    def _create_magic_literal(self, node: ast.AST, value: Any) -> MagicLiteral:
        """Create a MagicLiteral object with contextual analysis."""
        context = self._get_context(node.lineno)
        context_type = self._analyze_context_type(value, context, node)
        
        # Skip if context indicates this is not magic
        if self._is_context_safe(context_type, value, context):
            return None
        
        category = self._categorize_literal(value, context, context_type)
        severity = self._assess_contextual_severity(value, context, node, context_type)
        in_conditional = self._is_in_conditional(node)

        return MagicLiteral(
            value=value,
            file_path=self.file_path,
            line_number=node.lineno,
            column=node.col_offset,
            context=context,
            category=category,
            severity=severity,
            in_conditional=in_conditional,
            suggested_constant=self._suggest_contextual_constant_name(value, context, context_type),
        )

    def _get_context(self, line_number: int) -> str:
        """Get the line context for a literal."""
        if 1 <= line_number <= len(self.lines):
            return self.lines[line_number - 1].strip()
        return ""

    def _analyze_context_type(self, value: Any, context: str, node: ast.AST) -> ContextType:
        """Analyze the context type of a magic literal."""
        context_lower = context.lower()
        
        # Check for bitmask operations
        if any(op in context for op in ['&', '|', '^', '<<', '>>', '~']):
            return ContextType.BITMASK
        
        # Check for unit-tagged variables
        domain_allowlist = getattr(self, '_domain_allowlist', DomainAllowlist())
        for pattern in domain_allowlist.unit_patterns:
            if re.search(pattern, context_lower):
                return ContextType.UNIT_TAGGED
        
        # Check for loop indices (simple heuristic)
        if any(keyword in context for keyword in ['range(', 'for i in', 'for _ in']) and isinstance(value, int) and 0 <= value <= 10:
            return ContextType.LOOP_INDEX
        
        # Check for test seeds/fixtures
        if 'test' in self.file_path.lower() and any(keyword in context_lower for keyword in ['seed', 'fixture', 'mock']):
            return ContextType.TEST_SEED
        
        # Check for protocol boundaries (HTTP codes, etc.)
        if isinstance(value, int) and (100 <= value <= 599 or value in {200, 201, 400, 401, 403, 404, 500}):
            return ContextType.PROTOCOL_BOUNDARY
        
        # Check for mathematical contexts
        if any(keyword in context_lower for keyword in ['math.', 'sqrt', 'pow', 'sin', 'cos', 'tan', 'pi', 'radius']):
            return ContextType.MATHEMATICAL
        
        # Check for powers of 2
        if isinstance(value, int) and value > 0 and (value & (value - 1)) == 0:
            return ContextType.POWER_OF_TWO
        
        # Check for time units
        if any(keyword in context_lower for keyword in ['timeout', 'interval', 'delay', 'duration', 'sleep', 'wait']):
            return ContextType.TIME_UNIT
        
        # Check for percentages
        if isinstance(value, int) and 0 <= value <= 100 and any(keyword in context_lower for keyword in ['percent', 'ratio', 'rate']):
            return ContextType.PERCENTAGE
        
        return ContextType.GENERIC
    
    def _is_context_safe(self, context_type: ContextType, value: Any, context: str) -> bool:
        """Determine if a context makes a literal safe (not magic)."""
        # These contexts generally indicate intentional, non-magic usage
        safe_contexts = {
            ContextType.BITMASK,
            ContextType.UNIT_TAGGED,
            ContextType.LOOP_INDEX,
            ContextType.TEST_SEED,
            ContextType.MATHEMATICAL,
        }
        
        if context_type in safe_contexts:
            return True
        
        # Protocol boundaries are often intentional
        if context_type == ContextType.PROTOCOL_BOUNDARY:
            return True
        
        # Powers of 2 in technical contexts are usually intentional
        if context_type == ContextType.POWER_OF_TWO and any(
            keyword in context.lower() for keyword in ['buffer', 'cache', 'memory', 'size', 'limit']
        ):
            return True
        
        return False
    
    def _categorize_literal(self, value: Any, context: str, context_type: ContextType) -> str:
        """Categorize the magic literal based on value, context, and context type."""
        context_lower = context.lower()
        
        # Use context type for initial categorization
        if context_type == ContextType.TIME_UNIT:
            return "timing"
        elif context_type == ContextType.PROTOCOL_BOUNDARY:
            return "network"
        elif context_type == ContextType.PERCENTAGE:
            return "configuration"
        
        # Security-related (highest priority)
        if any(
            keyword in context_lower for keyword in ["password", "auth", "token", "secret", "crypto", "hash", "encrypt"]
        ):
            return "security"

        # Time-related
        if any(
            keyword in context_lower
            for keyword in ["timeout", "interval", "delay", "sleep", "duration", "seconds", "minutes", "hours"]
        ):
            return "timing"

        # Configuration
        if any(
            keyword in context_lower for keyword in ["config", "setting", "option", "parameter", "limit", "max", "min"]
        ):
            return "configuration"

        # Network/API
        if any(
            keyword in context_lower for keyword in ["port", "host", "url", "endpoint", "api", "http", "connection"]
        ):
            return "network"

        # File/Path
        if any(keyword in context_lower for keyword in ["path", "file", "dir", "extension", "filename"]):
            return "file_system"

        # Business logic
        if any(keyword in context_lower for keyword in ["cost", "price", "rate", "budget", "threshold"]):
            return "business_logic"

        # Display/UI
        if any(keyword in context_lower for keyword in ["format", "message", "log", "print", "display"]):
            return "presentation"

        return "unknown"

    def _assess_contextual_severity(self, value: Any, context: str, node: ast.AST, context_type: ContextType) -> str:
        """Assess severity using contextual analysis."""
        context_lower = context.lower()
        
        # Critical: Security-related magic literals
        if any(keyword in context_lower for keyword in ["password", "secret", "key", "token", "auth"]):
            return "critical"
        
        # Critical: Protocol boundaries in security contexts
        if context_type == ContextType.PROTOCOL_BOUNDARY and any(
            keyword in context_lower for keyword in ["auth", "security", "permission", "access"]
        ):
            return "critical"
        
        # High: Configuration limits and timeouts in conditionals
        if self._is_in_conditional(node) and context_type != ContextType.LOOP_INDEX:
            return "high"
        
        # High: Large numbers that likely represent important thresholds
        if isinstance(value, (int, float)) and abs(value) > 1000 and context_type == ContextType.GENERIC:
            return "high"
        
        # Medium: Business logic and timing literals
        if context_type in {ContextType.TIME_UNIT, ContextType.PERCENTAGE} or "business" in context_lower:
            return "medium"
        
        # Low: Generic literals in non-critical contexts
        if context_type in {ContextType.LOOP_INDEX, ContextType.TEST_SEED, ContextType.MATHEMATICAL}:
            return "low"
        
        # Medium: Default for other magic literals
        return "medium"

    def _is_in_conditional(self, node: ast.AST) -> bool:
        """Check if the literal is used in a conditional statement."""
        # This is a simplified check - could be enhanced with parent node analysis
        context = self._get_context(node.lineno)
        return any(keyword in context for keyword in ["if ", "elif ", "while ", "for "])

    def _suggest_contextual_constant_name(self, value: Any, context: str, context_type: ContextType) -> str:
        """Suggest a constant name using contextual analysis."""
        # Extract meaningful words from context
        words = re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b", context)
        
        # Filter out common non-meaningful words
        stopwords = {
            "self", "def", "class", "if", "else", "for", "while", "in", "is", "and", "or", "not",
            "import", "from", "return", "with", "as", "try", "except", "finally", "raise"
        }
        
        meaningful_words = [
            w.upper()
            for w in words
            if w.lower() not in stopwords and len(w) > 1
        ]
        
        # Context-specific naming
        base_name = "_".join(meaningful_words[:3]) if meaningful_words else "DEFAULT"
        
        if context_type == ContextType.TIME_UNIT:
            return f"{base_name}_SECONDS" if "second" not in base_name else base_name
        elif context_type == ContextType.PERCENTAGE:
            return f"{base_name}_PERCENT" if "percent" not in base_name else base_name
        elif context_type == ContextType.PROTOCOL_BOUNDARY:
            return f"{base_name}_STATUS_CODE"
        elif context_type == ContextType.POWER_OF_TWO:
            return f"{base_name}_SIZE" if "size" not in base_name else base_name
        elif "timeout" in context.lower():
            return f"{base_name}_TIMEOUT_SECONDS"
        elif "interval" in context.lower():
            return f"{base_name}_INTERVAL_SECONDS"
        elif "limit" in context.lower():
            return f"{base_name}_LIMIT"
        elif "max" in context.lower():
            return f"{base_name}_MAX"
        elif "min" in context.lower():
            return f"{base_name}_MIN"
        
        # Type-specific fallbacks
        if isinstance(value, str):
            return f"{base_name}_MESSAGE" if base_name != "DEFAULT" else "DEFAULT_MESSAGE"
        elif isinstance(value, (int, float)):
            return f"{base_name}_VALUE" if base_name != "DEFAULT" else "DEFAULT_VALUE"
        
        return base_name or "UNNAMED_CONSTANT"


@dataclass
class StatisticalAnalysis:
    """Statistical analysis of magic literals across the codebase."""
    
    literal_frequencies: Dict[Any, int] = field(default_factory=dict)
    context_patterns: Dict[str, int] = field(default_factory=dict)
    usage_locations: Dict[Any, List[str]] = field(default_factory=dict)
    outlier_threshold: float = 0.0
    
    def add_literal(self, literal: MagicLiteral) -> None:
        """Add a literal to the statistical analysis."""
        self.literal_frequencies[literal.value] = self.literal_frequencies.get(literal.value, 0) + 1
        
        # Track context patterns
        context_key = self._extract_context_pattern(literal.context)
        self.context_patterns[context_key] = self.context_patterns.get(context_key, 0) + 1
        
        # Track usage locations
        if literal.value not in self.usage_locations:
            self.usage_locations[literal.value] = []
        self.usage_locations[literal.value].append(f"{literal.file_path}:{literal.line_number}")
    
    def _extract_context_pattern(self, context: str) -> str:
        """Extract a pattern from the context for similarity analysis."""
        # Normalize context by removing specific values and keeping structure
        pattern = re.sub(r'\d+', 'N', context)  # Replace numbers with N
        pattern = re.sub(r'"[^"]*"', '"STR"', pattern)  # Replace strings
        pattern = re.sub(r"'[^']*'", "'STR'", pattern)  # Replace single-quoted strings
        return pattern[:50]  # Limit length
    
    def calculate_outlier_threshold(self) -> float:
        """Calculate the statistical outlier threshold for literal frequencies."""
        if len(self.literal_frequencies) < 10:
            return 2  # Minimum threshold for small datasets
        
        frequencies = list(self.literal_frequencies.values())
        try:
            mean_freq = statistics.mean(frequencies)
            stdev_freq = statistics.stdev(frequencies)
            
            # Use 95th percentile as threshold
            self.outlier_threshold = mean_freq + (2 * stdev_freq)
            return self.outlier_threshold
        except statistics.StatisticsError:
            return 2  # Fallback
    
    def is_repeated_literal(self, value: Any, threshold: int = 2) -> bool:
        """Check if a literal is repeated above the threshold."""
        return self.literal_frequencies.get(value, 0) >= threshold
    
    def get_similar_contexts(self, pattern: str, threshold: float = 0.7) -> List[str]:
        """Find contexts similar to the given pattern."""
        similar = []
        for context_pattern, count in self.context_patterns.items():
            if self._similarity_score(pattern, context_pattern) >= threshold:
                similar.append(context_pattern)
        return similar
    
    def _similarity_score(self, s1: str, s2: str) -> float:
        """Calculate similarity score between two context patterns."""
        # Simple Jaccard similarity on words
        words1 = set(s1.split())
        words2 = set(s2.split())
        
        if not words1 and not words2:
            return 1.0
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        return intersection / union if union > 0 else 0.0


@dataclass
class FrameworkProfile:
    """Framework-specific configuration for magic literal detection."""
    
    name: str
    relaxed_categories: Set[str] = field(default_factory=set)
    allowed_patterns: List[str] = field(default_factory=list)
    context_exceptions: List[str] = field(default_factory=list)
    
    # Built-in framework profiles
    @classmethod
    def django_profile(cls) -> 'FrameworkProfile':
        return cls(
            name="django",
            relaxed_categories={"configuration", "network"},
            allowed_patterns=[
                r".*_BACKEND\s*=.*",  # Django backends
                r".*_APPS\s*=.*",     # Django apps
                r"MIDDLEWARE.*=.*",    # Middleware config
            ],
            context_exceptions=[
                "settings.py",
                "urls.py",
                "admin.py",
            ]
        )
    
    @classmethod
    def fastapi_profile(cls) -> 'FrameworkProfile':
        return cls(
            name="fastapi",
            relaxed_categories={"network", "presentation"},
            allowed_patterns=[
                r"status_code\s*=\s*\d+",  # HTTP status codes
                r"@app\.(get|post|put|delete).*",  # Route decorators
            ],
            context_exceptions=[
                "main.py",
                "routers/",
            ]
        )
    
    @classmethod
    def react_profile(cls) -> 'FrameworkProfile':
        return cls(
            name="react",
            relaxed_categories={"presentation", "configuration"},
            allowed_patterns=[
                r"useState\(\d+\)",     # React hooks with initial values
                r"setTimeout\(.*\d+.*\)",  # Timeouts
            ],
            context_exceptions=[
                "components/",
                "hooks/",
            ]
        )


class EnhancedMagicLiteralAnalyzer(MagicLiteralAnalyzer):
    """Enhanced analyzer with statistical analysis and framework awareness."""
    
    def __init__(self, file_path: str, framework_profile: Optional[FrameworkProfile] = None):
        super().__init__(file_path)
        self.framework_profile = framework_profile
        self.statistics = StatisticalAnalysis()
        self.thresholds = StatisticalThresholds()
    
    def _create_magic_literal(self, node: ast.AST, value: Any) -> Optional[MagicLiteral]:
        """Enhanced creation with framework and statistical awareness."""
        literal = super()._create_magic_literal(node, value)
        if literal is None:
            return None
        
        # Add to statistical analysis
        self.statistics.add_literal(literal)
        
        # Apply framework-specific filtering
        if self.framework_profile and self._is_framework_exception(literal):
            return None
        
        return literal
    
    def _is_framework_exception(self, literal: MagicLiteral) -> bool:
        """Check if literal should be ignored due to framework profile."""
        if not self.framework_profile:
            return False
        
        # Check category relaxation
        if literal.category in self.framework_profile.relaxed_categories:
            return True
        
        # Check pattern matching
        for pattern in self.framework_profile.allowed_patterns:
            if re.search(pattern, literal.context, re.IGNORECASE):
                return True
        
        # Check context exceptions
        for exception in self.framework_profile.context_exceptions:
            if exception in literal.file_path:
                return True
        
        return False


def analyze_package_with_context(package_path: Path, 
                                framework_profile: Optional[FrameworkProfile] = None) -> PackageStats:
    """Analyze a package with contextual intelligence."""
    package_name = package_path.name
    stats = PackageStats(package_name=package_name)
    global_statistics = StatisticalAnalysis()

    # Find constants modules
    for constants_file in package_path.rglob("constants.py"):
        stats.constants_modules.append(str(constants_file.relative_to(package_path)))

    # First pass: collect all literals for statistical analysis
    all_literals = []
    
    # Analyze Python files
    for py_file in package_path.rglob("*.py"):
        if py_file.name.startswith(".") or "test" in py_file.name:
            continue

        try:
            analyzer = EnhancedMagicLiteralAnalyzer(str(py_file), framework_profile)
            with open(py_file, encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=str(py_file))

            analyzer.visit(tree)
            all_literals.extend(analyzer.literals)
            
        except Exception as e:
            logger.warning(f"Error analyzing {py_file}: {e}")
    
    # Build global statistics
    for literal in all_literals:
        global_statistics.add_literal(literal)
    
    outlier_threshold = global_statistics.calculate_outlier_threshold()
    
    # Second pass: filter using statistical analysis
    for literal in all_literals:
        # Skip if not repeated above threshold and not high severity
        if (literal.severity not in {"critical", "high"} and 
            not global_statistics.is_repeated_literal(literal.value, 2)):
            continue
        
        # Add to stats
        file_rel_path = str(Path(literal.file_path).relative_to(package_path))
        stats.files_with_literals.add(file_rel_path)
        stats.total_literals += 1
        
        # Update category counts
        stats.literals_by_category[literal.category] = (
            stats.literals_by_category.get(literal.category, 0) + 1
        )
        
        # Update severity counts
        stats.literals_by_severity[literal.severity] = (
            stats.literals_by_severity.get(literal.severity, 0) + 1
        )

    return stats


def analyze_package(package_path: Path) -> PackageStats:
    """Legacy analyze function - now uses contextual analysis."""
    return analyze_package_with_context(package_path)


def generate_reduction_report(packages_stats: list[PackageStats]) -> dict[str, Any]:
    """Generate a comprehensive magic literal reduction report."""
    total_literals = sum(stats.total_literals for stats in packages_stats)
    total_files = sum(len(stats.files_with_literals) for stats in packages_stats)

    # Calculate category distribution
    category_totals = {}
    severity_totals = {}

    for stats in packages_stats:
        for category, count in stats.literals_by_category.items():
            category_totals[category] = category_totals.get(category, 0) + count

        for severity, count in stats.literals_by_severity.items():
            severity_totals[severity] = severity_totals.get(severity, 0) + count

    # Find packages with constants modules
    packages_with_constants = [stats for stats in packages_stats if stats.constants_modules]

    # Calculate reduction metrics
    target_reduction = 0.38  # 38% reduction target
    baseline_estimate = 32739  # From original analysis
    current_estimate = total_literals
    reduction_achieved = max(0, (baseline_estimate - current_estimate) / baseline_estimate)

    report = {
        "summary": {
            "total_magic_literals": total_literals,
            "files_with_literals": total_files,
            "packages_analyzed": len(packages_stats),
            "packages_with_constants": len(packages_with_constants),
            "baseline_estimate": baseline_estimate,
            "reduction_target": target_reduction,
            "reduction_achieved": reduction_achieved,
            "target_met": reduction_achieved >= target_reduction,
        },
        "category_distribution": category_totals,
        "severity_distribution": severity_totals,
        "package_breakdown": [
            {
                "package": stats.package_name,
                "literals": stats.total_literals,
                "files": len(stats.files_with_literals),
                "constants_modules": len(stats.constants_modules),
                "categories": stats.literals_by_category,
                "severities": stats.literals_by_severity,
            }
            for stats in sorted(packages_stats, key=lambda s: s.total_literals, reverse=True)
        ],
        "recommendations": generate_recommendations(packages_stats, category_totals),
    }

    return report


def generate_recommendations(packages_stats: list[PackageStats], category_totals: dict[str, int]) -> list[str]:
    """Generate actionable recommendations for magic literal reduction."""
    recommendations = []

    # High-priority categories
    if category_totals.get("security", 0) > 0:
        recommendations.append(
            f"CRITICAL: Replace {category_totals['security']} security-related magic literals immediately"
        )

    if category_totals.get("configuration", 0) > 0:
        recommendations.append(
            f"HIGH: Create configuration constants for {category_totals['configuration']} config literals"
        )

    # Packages without constants modules
    packages_without_constants = [
        stats for stats in packages_stats if not stats.constants_modules and stats.total_literals > 10
    ]

    for stats in packages_without_constants[:5]:  # Top 5
        recommendations.append(
            f"Create constants.py module for {stats.package_name} package ({stats.total_literals} literals)"
        )

    # Category-specific recommendations
    if category_totals.get("timing", 0) > 0:
        recommendations.append(
            f"Replace {category_totals['timing']} timing-related magic literals with named constants"
        )

    if category_totals.get("business_logic", 0) > 0:
        recommendations.append(
            f"Extract {category_totals['business_logic']} business logic literals to domain constants"
        )

    return recommendations


def main():
    """Main analysis function."""
    logger.info("Starting magic literal analysis...")

    # Analyze major packages
    packages_to_analyze = ["core", "infrastructure", "apps"]

    packages_stats = []

    for package_path_str in packages_to_analyze:
        package_path = Path(package_path_str)
        if package_path.exists():
            logger.info(f"Analyzing {package_path}...")
            stats = analyze_package(package_path)
            packages_stats.append(stats)
            logger.info(f"Found {stats.total_literals} magic literals in {len(stats.files_with_literals)} files")

    # Generate comprehensive report
    report = generate_reduction_report(packages_stats)

    # Save report
    report_path = Path("quality_reports/magic_literal_analysis.json")
    report_path.parent.mkdir(exist_ok=True)

    with open(report_path, "w") as f:
        json.dump(report, f, indent=2, default=str)

    # Print summary
    print("\n" + "=" * 60)
    print("MAGIC LITERAL REDUCTION ANALYSIS")
    print("=" * 60)
    print(f"Total magic literals found: {report['summary']['total_magic_literals']:,}")
    print(f"Files with literals: {report['summary']['files_with_literals']:,}")
    print(f"Reduction achieved: {report['summary']['reduction_achieved']:.1%}")
    print(f"Target (38%): {'MET' if report['summary']['target_met'] else 'NOT MET'}")

    print("\nTop categories:")
    for category, count in sorted(report["category_distribution"].items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"  {category}: {count:,} literals")

    print("\nRecommendations:")
    for i, rec in enumerate(report["recommendations"][:5], 1):
        print(f"  {i}. {rec}")

    print(f"\nDetailed report saved to: {report_path}")

    logger.info("Magic literal analysis completed!")


if __name__ == "__main__":
    main()
