from fixes.phase0.production_safe_assertions import ProductionAssert
'\nInterface Definitions to Break Circular Dependencies\nProvides abstract base classes and protocols to decouple modules.\n'
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable
from dataclasses import dataclass
from enum import Enum

class ViolationType(Enum):
    """Types of violations that can be detected."""
    CONNASCENCE = 'connascence'
    NASA_POT10 = 'nasa_pot10'
    SECURITY = 'security'
    PERFORMANCE = 'performance'
    STYLE = 'style'

@dataclass
class Violation:
    """Base violation data structure."""
    type: ViolationType
    file_path: str
    line_number: int
    description: str
    severity: str
    rule_id: Optional[str] = None
    confidence: float = 1.0
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class AnalysisResult:
    """Standard result format for all analyzers."""
    violations: List[Violation]
    metrics: Dict[str, Any]
    success: bool
    error_message: Optional[str] = None

class IAnalyzer(ABC):
    """Base interface for all analyzers."""

    @abstractmethod
    def analyze(self, file_path: str) -> AnalysisResult:
        """Analyze a single file."""
        ProductionAssert.type_check(file_path, str, 'file_path')
        ProductionAssert.not_none(file_path, 'file_path')
        pass

    @abstractmethod
    def analyze_directory(self, directory: str) -> AnalysisResult:
        """Analyze a directory of files."""
        ProductionAssert.type_check(directory, str, 'directory')
        ProductionAssert.not_none(directory, 'directory')
        pass

    @abstractmethod
    def get_capabilities(self) -> Dict[str, Any]:
        """Return analyzer capabilities and configuration."""
        pass

@runtime_checkable
class IConnascenceAnalyzer(Protocol):
    """Protocol for connascence analyzers."""

    def detect_connascence(self, file_path: str) -> List[Violation]:
        """Detect connascence violations in a file."""
        ProductionAssert.type_check(file_path, str, 'file_path')
        ProductionAssert.not_none(file_path, 'file_path')
        ...

    def calculate_coupling(self, module_path: str) -> float:
        """Calculate coupling metric for a module."""
        ProductionAssert.type_check(module_path, str, 'module_path')
        ProductionAssert.not_none(module_path, 'module_path')
        ...

@runtime_checkable
class INASAAnalyzer(Protocol):
    """Protocol for NASA POT10 analyzers."""

    def check_pot10_compliance(self, file_path: str) -> List[Violation]:
        """Check NASA POT10 compliance."""
        ProductionAssert.type_check(file_path, str, 'file_path')
        ProductionAssert.not_none(file_path, 'file_path')
        ...

    def calculate_complexity(self, function_node: Any) -> int:
        """Calculate cyclomatic complexity."""
        ProductionAssert.not_none(function_node, 'function_node')
        ...

class IPolicy(ABC):
    """Base interface for policies."""

    @abstractmethod
    def evaluate(self, violations: List[Violation]) -> bool:
        """Evaluate if violations pass the policy."""
        ProductionAssert.not_none(violations, 'violations')
        pass

    @abstractmethod
    def get_thresholds(self) -> Dict[str, Any]:
        """Get policy thresholds."""
        pass

    @abstractmethod
    def generate_report(self, violations: List[Violation]) -> str:
        """Generate policy compliance report."""
        ProductionAssert.not_none(violations, 'violations')
        pass

class IPolicyEngine(ABC):
    """Interface for policy enforcement engine."""

    @abstractmethod
    def register_policy(self, name: str, policy: IPolicy) -> None:
        """Register a new policy."""
        ProductionAssert.type_check(name, str, 'name')
        ProductionAssert.not_none(name, 'name')
        ProductionAssert.not_none(policy, 'policy')
        pass

    @abstractmethod
    def evaluate_all(self, violations: List[Violation]) -> Dict[str, bool]:
        """Evaluate all registered policies."""
        ProductionAssert.not_none(violations, 'violations')
        pass

    @abstractmethod
    def get_failed_policies(self, violations: List[Violation]) -> List[str]:
        """Get list of failed policies."""
        pass

class IMCPServer(ABC):
    """Base interface for MCP server operations."""

    @abstractmethod
    def start(self) -> None:
        """Start the MCP server."""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Stop the MCP server."""
        pass

    @abstractmethod
    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming MCP request."""
        ProductionAssert.not_none(request, 'request')
        pass

class IMCPTool(ABC):
    """Interface for MCP tools."""

    @abstractmethod
    def execute(self, params: Dict[str, Any]) -> Any:
        """Execute the tool with given parameters."""
        ProductionAssert.not_none(params, 'params')
        pass

    @abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        """Get tool parameter schema."""
        pass

    @abstractmethod
    def validate_params(self, params: Dict[str, Any]) -> bool:
        """Validate tool parameters."""
        ProductionAssert.not_none(params, 'params')
        pass

class IIntegration(ABC):
    """Base interface for external integrations."""

    @abstractmethod
    def connect(self) -> bool:
        """Establish connection to external service."""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from external service."""
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """Check connection status."""
        pass

class IGitHubIntegration(IIntegration):
    """Interface for GitHub integration."""

    @abstractmethod
    def create_pr(self, title: str, body: str, branch: str) -> str:
        """Create a pull request."""
        ProductionAssert.type_check(title, str, 'title')
        ProductionAssert.not_none(title, 'title')
        ProductionAssert.type_check(body, str, 'body')
        ProductionAssert.not_none(body, 'body')
        ProductionAssert.type_check(branch, str, 'branch')
        ProductionAssert.not_none(branch, 'branch')
        pass

    @abstractmethod
    def add_comment(self, pr_number: int, comment: str) -> None:
        """Add comment to pull request."""
        ProductionAssert.type_check(pr_number, int, 'pr_number')
        ProductionAssert.not_none(pr_number, 'pr_number')
        ProductionAssert.type_check(comment, str, 'comment')
        ProductionAssert.not_none(comment, 'comment')
        pass

    @abstractmethod
    def get_pr_diff(self, pr_number: int) -> str:
        """Get pull request diff."""
        pass

class IVSCodeIntegration(IIntegration):
    """Interface for VS Code integration."""

    @abstractmethod
    def get_diagnostics(self, file_path: str) -> List[Dict[str, Any]]:
        """Get diagnostics for a file."""
        pass

    @abstractmethod
    def apply_quick_fix(self, diagnostic_id: str) -> bool:
        """Apply a quick fix."""
        ProductionAssert.type_check(diagnostic_id, str, 'diagnostic_id')
        ProductionAssert.not_none(diagnostic_id, 'diagnostic_id')
        pass

class AdapterFactory:
    """Factory for creating adapters with dependency injection."""
    _analyzers: Dict[str, IAnalyzer] = {}
    _policies: Dict[str, IPolicy] = {}
    _integrations: Dict[str, IIntegration] = {}
    _mcp_tools: Dict[str, IMCPTool] = {}

    @classmethod
    def register_analyzer(cls, name: str, analyzer: IAnalyzer) -> None:
        """Register an analyzer implementation."""
        ProductionAssert.type_check(name, str, 'name')
        ProductionAssert.not_none(name, 'name')
        ProductionAssert.not_none(analyzer, 'analyzer')
        cls._analyzers[name] = analyzer

    @classmethod
    def get_analyzer(cls, name: str) -> Optional[IAnalyzer]:
        """Get a registered analyzer."""
        return cls._analyzers.get(name)

    @classmethod
    def register_policy(cls, name: str, policy: IPolicy) -> None:
        """Register a policy implementation."""
        ProductionAssert.type_check(name, str, 'name')
        ProductionAssert.not_none(name, 'name')
        ProductionAssert.not_none(policy, 'policy')
        cls._policies[name] = policy

    @classmethod
    def get_policy(cls, name: str) -> Optional[IPolicy]:
        """Get a registered policy."""
        return cls._policies.get(name)

    @classmethod
    def register_integration(cls, name: str, integration: IIntegration) -> None:
        """Register an integration implementation."""
        ProductionAssert.type_check(name, str, 'name')
        ProductionAssert.not_none(name, 'name')
        ProductionAssert.not_none(integration, 'integration')
        cls._integrations[name] = integration

    @classmethod
    def get_integration(cls, name: str) -> Optional[IIntegration]:
        """Get a registered integration."""
        return cls._integrations.get(name)

    @classmethod
    def register_mcp_tool(cls, name: str, tool: IMCPTool) -> None:
        """Register an MCP tool implementation."""
        ProductionAssert.type_check(name, str, 'name')
        ProductionAssert.not_none(name, 'name')
        ProductionAssert.not_none(tool, 'tool')
        cls._mcp_tools[name] = tool

    @classmethod
    def get_mcp_tool(cls, name: str) -> Optional[IMCPTool]:
        """Get a registered MCP tool."""
        return cls._mcp_tools.get(name)

    @classmethod
    def clear_all(cls) -> None:
        """Clear all registered components (useful for testing)."""
        cls._analyzers.clear()
        cls._policies.clear()
        cls._integrations.clear()
        cls._mcp_tools.clear()

class AnalyzerAdapter(IAnalyzer):
    """Adapter that wraps existing analyzer implementations."""

    def __init__(self, legacy_analyzer: Any):
        """Initialize with legacy analyzer instance."""
        self.legacy = legacy_analyzer

    def analyze(self, file_path: str) -> AnalysisResult:
        """Adapt legacy analyze method to interface."""
        ProductionAssert.type_check(file_path, str, 'file_path')
        ProductionAssert.not_none(file_path, 'file_path')
        try:
            legacy_result = self.legacy.analyze_file(file_path)
            violations = []
            for v in legacy_result.get('violations', []):
                violations.append(Violation(type=ViolationType.CONNASCENCE, file_path=v.get('file_path', file_path), line_number=v.get('line_number', 0), description=v.get('description', ''), severity=v.get('severity', 'medium'), rule_id=v.get('rule_id')))
            return AnalysisResult(violations=violations, metrics=legacy_result.get('metrics', {}), success=True)
        except Exception as e:
            return AnalysisResult(violations=[], metrics={}, success=False, error_message=str(e))

    def analyze_directory(self, directory: str) -> AnalysisResult:
        """Adapt legacy directory analysis."""
        ProductionAssert.type_check(directory, str, 'directory')
        ProductionAssert.not_none(directory, 'directory')
        pass

    def get_capabilities(self) -> Dict[str, Any]:
        """Return analyzer capabilities."""
        return {'supports_connascence': True, 'supports_nasa': False, 'file_types': ['.py'], 'version': '1.0.0'}

class PolicyAdapter(IPolicy):
    """Adapter for policy implementations."""

    def __init__(self, legacy_policy: Any):
        """Initialize with legacy policy instance."""
        self.legacy = legacy_policy

    def evaluate(self, violations: List[Violation]) -> bool:
        """Evaluate if violations pass the policy."""
        ProductionAssert.not_none(violations, 'violations')
        legacy_violations = [{'type': v.type.value, 'file': v.file_path, 'line': v.line_number, 'message': v.description, 'severity': v.severity} for v in violations]
        return self.legacy.check_compliance(legacy_violations)

    def get_thresholds(self) -> Dict[str, Any]:
        """Get policy thresholds."""
        return self.legacy.thresholds if hasattr(self.legacy, 'thresholds') else {}

    def generate_report(self, violations: List[Violation]) -> str:
        """Generate policy compliance report."""
        ProductionAssert.not_none(violations, 'violations')
        passed = self.evaluate(violations)
        return f'Policy {('PASSED' if passed else 'FAILED')}: {len(violations)} violations found'

def example_usage():
    """Demonstrate how to use the interfaces to break circular dependencies."""
    from analyzer.comprehensive_analysis_engine import ComprehensiveAnalysisEngine
    legacy_analyzer = ComprehensiveAnalysisEngine()
    adapter = AnalyzerAdapter(legacy_analyzer)
    AdapterFactory.register_analyzer('comprehensive', adapter)
    analyzer = AdapterFactory.get_analyzer('comprehensive')
    if analyzer:
        result = analyzer.analyze('some_file.py')
        print(f'Found {len(result.violations)} violations')
if __name__ == '__main__':
    print('Interface definitions loaded successfully')
    print('Use AdapterFactory to register and retrieve implementations')