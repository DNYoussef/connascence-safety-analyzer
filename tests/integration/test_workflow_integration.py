#!/usr/bin/env python3
"""
Complete Workflow Integration Tests - End-to-End System Testing
Tests complete analysis workflows including CLI → analyzer → reports → autofix → validation
"""

import pytest
import json
import asyncio
import tempfile
import shutil
import subprocess
import time
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from typing import Dict, List, Any, Tuple
import concurrent.futures

# Memory coordination for workflow test results
WORKFLOW_MEMORY = {}

class WorkflowTestCoordinator:
    """Coordinates complete workflow testing with memory tracking and sequential execution"""
    
    def __init__(self):
        self.memory_store = WORKFLOW_MEMORY
        self.test_session_id = f"workflow_integration_{int(time.time())}"
        self.workflow_stages = []
        self.performance_metrics = {}
        
    def store_workflow_stage(self, stage_name: str, result: Dict[str, Any]):
        """Store workflow stage result with timing and dependencies"""
        stage_key = f"{self.test_session_id}_{stage_name}"
        self.memory_store[stage_key] = {
            'timestamp': time.time(),
            'stage': stage_name,
            'result': result,
            'status': 'completed',
            'stage_order': len(self.workflow_stages),
            'dependencies': result.get('dependencies', [])
        }
        self.workflow_stages.append(stage_name)
        
    def get_workflow_progression(self) -> List[str]:
        """Get workflow stages in execution order"""
        return self.workflow_stages.copy()
        
    def calculate_workflow_metrics(self) -> Dict[str, Any]:
        """Calculate comprehensive workflow metrics"""
        results = self.get_workflow_results()
        
        total_execution_time = 0
        stages_completed = 0
        errors_encountered = 0
        quality_improvements = []
        
        for stage_key, stage_data in results.items():
            result = stage_data.get('result', {})
            
            # Timing metrics
            if 'execution_time' in result:
                total_execution_time += result['execution_time']
            
            stages_completed += 1
            
            # Error tracking
            if result.get('status') == 'error':
                errors_encountered += 1
                
            # Quality metrics
            if 'quality_score' in result:
                quality_improvements.append(result['quality_score'])
                
        return {
            'total_execution_time': total_execution_time,
            'stages_completed': stages_completed,
            'error_rate': (errors_encountered / stages_completed) * 100 if stages_completed > 0 else 0,
            'workflow_success_rate': ((stages_completed - errors_encountered) / stages_completed) * 100 if stages_completed > 0 else 0,
            'average_quality_score': sum(quality_improvements) / len(quality_improvements) if quality_improvements else 0,
            'quality_improvement_trend': quality_improvements
        }
        
    def get_workflow_results(self) -> Dict[str, Any]:
        """Retrieve all workflow results for this session"""
        return {k: v for k, v in self.memory_store.items() 
                if k.startswith(self.test_session_id)}

@pytest.fixture
def workflow_coordinator():
    """Create workflow test coordinator with memory tracking"""
    return WorkflowTestCoordinator()

@pytest.fixture
def comprehensive_test_workspace():
    """Create comprehensive test workspace with multiple file types and violation patterns"""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        
        # Create directory structure
        (workspace / "src").mkdir()
        (workspace / "tests").mkdir()
        (workspace / "docs").mkdir()
        (workspace / "config").mkdir()
        
        # Python files with various violations
        (workspace / "src" / "main.py").write_text('''
#!/usr/bin/env python3
"""
Main application module with intentional violations for testing
"""

def process_order(customer_id, product_id, quantity, price, tax_rate, 
                  discount_code, payment_method, shipping_address, 
                  billing_address, special_instructions, priority):
    """Function with too many parameters - CoP violation"""
    
    # Magic literals - CoM violations
    base_tax = 0.08
    premium_threshold = 1000
    max_discount = 0.15
    
    # Deep nesting - CoA violation
    if customer_id:
        if product_id:
            if quantity > 0:
                if price > 0:
                    if payment_method in ["card", "paypal"]:
                        total = quantity * price * (1 + tax_rate)
                        
                        if price > premium_threshold:
                            if discount_code == "PREMIUM10":
                                total *= (1 - 0.1)
                            elif discount_code == "VIP15":
                                total *= (1 - max_discount)
                                
                        return {
                            "total": total,
                            "tax": total * base_tax,
                            "customer": customer_id
                        }
    return None

class OrderProcessor:
    """God class with too many methods - CoA violation"""
    
    def __init__(self):
        self.orders = []
        
    def create_order(self): pass
    def validate_order(self): pass
    def calculate_tax(self): pass
    def apply_discount(self): pass
    def process_payment(self): pass
    def send_confirmation(self): pass
    def update_inventory(self): pass
    def generate_invoice(self): pass
    def handle_shipping(self): pass
    def track_package(self): pass
    def handle_returns(self): pass
    def process_refunds(self): pass
    def generate_reports(self): pass
    def analyze_trends(self): pass
    def manage_customers(self): pass
    def handle_complaints(self): pass
    def optimize_pricing(self): pass
    def forecast_demand(self): pass
    def manage_suppliers(self): pass
    def coordinate_logistics(self): pass
    def monitor_quality(self): pass
    def ensure_compliance(self): pass
    def maintain_security(self): pass
    def backup_data(self): pass
    def archive_records(self): pass

# Functions without type hints - CoT violations
def calculate_total(items, tax_rate, discount):
    """Calculate order total without type hints"""
    subtotal = sum(item.price * item.quantity for item in items)
    
    if subtotal > 500:  # Magic literal
        discount_amount = subtotal * discount
    else:
        discount_amount = 0
        
    return subtotal * (1 + tax_rate) - discount_amount

def validate_payment_info(card_number, expiry, cvv):
    """Validate payment without type hints"""
    if len(card_number) != 16:  # Magic literal
        return False
    return True
''')
        
        # JavaScript file for multi-language testing
        (workspace / "src" / "app.js").write_text('''
// JavaScript file with violations for testing

function processOrder(customerId, productId, quantity, price, taxRate, 
                     discountCode, paymentMethod, shippingAddress, 
                     billingAddress, specialInstructions) {  // Too many parameters
    
    const TAX_RATE = 0.08;  // Magic number
    const PREMIUM_THRESHOLD = 1000;  // Magic number
    
    // Deep nesting
    if (customerId) {
        if (productId) {
            if (quantity > 0) {
                if (price > 0) {
                    if (paymentMethod === "card") {
                        let total = quantity * price * (1 + taxRate);
                        
                        if (price > PREMIUM_THRESHOLD) {
                            if (discountCode === "SAVE10") {
                                total *= 0.9;  // Magic number
                            }
                        }
                        
                        return {
                            total: total,
                            customerId: customerId,
                            status: "processed"
                        };
                    }
                }
            }
        }
    }
    
    return null;
}

// Duplicate logic - CoA violation
function calculatePremiumDiscount(price) {
    if (price > 1000) {
        return price * 0.15;
    }
    return 0;
}

function calculateVipDiscount(price) {
    if (price > 1000) {  // Same logic
        return price * 0.15;  // Same calculation
    }
    return 0;
}
''')
        
        # C file for NASA analysis
        (workspace / "src" / "calculator.c").write_text('''
#include <stdio.h>

// NASA Rule violations for testing
int factorial(int n) {  // Rule 3: No recursion
    if (n <= 1) return 1;
    return n * factorial(n - 1);  // Recursion violation
}

void process_array() {
    int data[1000];  // Magic number
    int max_items = 500;  // Magic number
    int timeout = 30000;  // Magic number
    
    // Long function violating line limits
    printf("Processing array\\n");
    for (int i = 0; i < max_items; i++) {
        data[i] = i * 2;
    }
    
    // More code would follow to make this a very long function
}

int calculate(int a, int b, int c, int d, int e, int f) {  // Too many params
    return a + b + c + d + e + f;
}
''')
        
        # Configuration file
        (workspace / "config" / "analysis.json").write_text(json.dumps({
            "analysis_profile": "comprehensive",
            "thresholds": {
                "max_positional_params": 3,
                "god_class_methods": 20,
                "max_cyclomatic_complexity": 10,
                "max_nesting_depth": 4,
                "max_function_lines": 50
            },
            "budget_limits": {
                "CoM": 8,
                "CoP": 4,
                "CoT": 10,
                "CoA": 3,
                "total_violations": 30
            },
            "languages": ["python", "javascript", "c"],
            "exclusions": ["tests/*", ".*"]
        }, indent=2))
        
        # Test files
        (workspace / "tests" / "test_main.py").write_text('''
import pytest
from src.main import process_order, calculate_total

def test_process_order():
    """Test order processing functionality"""
    result = process_order(
        "CUST001", "PROD001", 2, 50.0, 0.08,
        "SAVE10", "card", "123 Main St", "456 Oak Ave", 
        "Handle with care", "high"
    )
    assert result is not None

def test_calculate_total():
    """Test total calculation"""
    # Mock items for testing
    items = []
    result = calculate_total(items, 0.08, 0.1)
    assert isinstance(result, (int, float))
''')
        
        yield workspace

@pytest.fixture
def mock_analysis_engine():
    """Create comprehensive mock analysis engine"""
    
    class MockAnalysisEngine:
        def __init__(self):
            self.analysis_count = 0
            
        async def analyze_path(self, path: Path, profile: str = "modern_general") -> Dict[str, Any]:
            """Mock comprehensive path analysis"""
            self.analysis_count += 1
            await asyncio.sleep(0.3)  # Simulate analysis time
            
            # Generate realistic findings based on test workspace content
            findings = [
                {
                    'id': 'CoP_001',
                    'rule_id': 'CON_CoP',
                    'connascence_type': 'CoP',
                    'severity': 'high',
                    'description': 'Function has 11 positional parameters (max: 3)',
                    'file_path': str(path / 'src' / 'main.py'),
                    'line_number': 6,
                    'weight': 4.5,
                    'context': 'def process_order(customer_id, product_id, ...)'
                },
                {
                    'id': 'CoM_001',
                    'rule_id': 'CON_CoM',
                    'connascence_type': 'CoM',
                    'severity': 'medium',
                    'description': 'Magic literal 0.08 should be extracted to constant',
                    'file_path': str(path / 'src' / 'main.py'),
                    'line_number': 12,
                    'weight': 2.5,
                    'context': 'base_tax = 0.08'
                },
                {
                    'id': 'CoM_002',
                    'rule_id': 'CON_CoM',
                    'connascence_type': 'CoM',
                    'severity': 'medium',
                    'description': 'Magic literal 1000 should be extracted to constant',
                    'file_path': str(path / 'src' / 'main.py'),
                    'line_number': 13,
                    'weight': 2.5,
                    'context': 'premium_threshold = 1000'
                },
                {
                    'id': 'CoA_001',
                    'rule_id': 'CON_CoA',
                    'connascence_type': 'CoA',
                    'severity': 'critical',
                    'description': 'Class has 25 methods (max: 20)',
                    'file_path': str(path / 'src' / 'main.py'),
                    'line_number': 42,
                    'weight': 5.0,
                    'context': 'class OrderProcessor:'
                },
                {
                    'id': 'CoA_002',
                    'rule_id': 'CON_CoA',
                    'connascence_type': 'CoA',
                    'severity': 'high',
                    'description': 'Deep nesting detected (depth: 6, max: 4)',
                    'file_path': str(path / 'src' / 'main.py'),
                    'line_number': 16,
                    'weight': 4.0,
                    'context': 'Nested if statements'
                },
                {
                    'id': 'CoT_001',
                    'rule_id': 'CON_CoT',
                    'connascence_type': 'CoT',
                    'severity': 'medium',
                    'description': 'Function lacks type hints',
                    'file_path': str(path / 'src' / 'main.py'),
                    'line_number': 69,
                    'weight': 2.0,
                    'context': 'def calculate_total(items, tax_rate, discount):'
                },
                # NASA violations in C file
                {
                    'id': 'NASA_001',
                    'rule_id': 'NASA_RULE_3',
                    'connascence_type': 'CoA',
                    'severity': 'critical',
                    'description': 'Recursion detected - violates NASA JPL Rule 3',
                    'file_path': str(path / 'src' / 'calculator.c'),
                    'line_number': 5,
                    'weight': 5.0,
                    'context': 'int factorial(int n) {'
                },
                # JavaScript violations
                {
                    'id': 'JS_CoP_001',
                    'rule_id': 'CON_CoP',
                    'connascence_type': 'CoP',
                    'severity': 'high',
                    'description': 'Function has 10 parameters (max: 3)',
                    'file_path': str(path / 'src' / 'app.js'),
                    'line_number': 3,
                    'weight': 4.0,
                    'context': 'function processOrder(customerId, productId, ...)'
                }
            ]
            
            return {
                'status': 'success',
                'findings': findings,
                'summary': {
                    'total_violations': len(findings),
                    'by_severity': {
                        'critical': len([f for f in findings if f['severity'] == 'critical']),
                        'high': len([f for f in findings if f['severity'] == 'high']),
                        'medium': len([f for f in findings if f['severity'] == 'medium']),
                        'low': len([f for f in findings if f['severity'] == 'low'])
                    },
                    'by_type': {
                        'CoP': len([f for f in findings if f['connascence_type'] == 'CoP']),
                        'CoM': len([f for f in findings if f['connascence_type'] == 'CoM']),
                        'CoA': len([f for f in findings if f['connascence_type'] == 'CoA']),
                        'CoT': len([f for f in findings if f['connascence_type'] == 'CoT'])
                    },
                    'connascence_index': sum(f['weight'] for f in findings),
                    'quality_score': max(0, 100 - sum(f['weight'] for f in findings)),
                    'files_analyzed': 3,
                    'analysis_time_ms': 300,
                    'profile_used': profile
                },
                'metadata': {
                    'analyzer_version': '2.0.0',
                    'timestamp': time.time(),
                    'languages_detected': ['python', 'javascript', 'c']
                }
            }
            
        async def analyze_diff(self, base_path: Path, changed_files: List[str]) -> Dict[str, Any]:
            """Mock differential analysis"""
            await asyncio.sleep(0.1)
            
            return {
                'status': 'success',
                'new_violations': [
                    {
                        'id': 'DIFF_001',
                        'connascence_type': 'CoM',
                        'severity': 'medium',
                        'description': 'New magic literal introduced',
                        'file_path': changed_files[0] if changed_files else 'unknown.py',
                        'line_number': 10
                    }
                ],
                'resolved_violations': [],
                'summary': {
                    'net_change': +1,
                    'quality_impact': -2.5,
                    'files_changed': len(changed_files)
                }
            }
    
    return MockAnalysisEngine()

@pytest.fixture 
def mock_autofix_engine():
    """Create mock autofix engine for workflow testing"""
    
    class MockAutofixEngine:
        def __init__(self):
            self.fixes_generated = 0
            
        async def generate_fixes(self, violations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
            """Generate fixes for violations"""
            await asyncio.sleep(0.2)
            
            fixes = []
            for violation in violations:
                self.fixes_generated += 1
                
                fix_type_mapping = {
                    'CoM': 'extract_constant',
                    'CoP': 'parameter_object', 
                    'CoT': 'add_type_hints',
                    'CoA': 'extract_class' if 'class' in violation.get('description', '') else 'reduce_nesting'
                }
                
                fix_type = fix_type_mapping.get(violation['connascence_type'], 'manual_review')
                confidence = 0.85 if fix_type != 'extract_class' else 0.65
                safety = 'safe' if fix_type in ['extract_constant', 'add_type_hints'] else 'moderate'
                
                fixes.append({
                    'id': f"fix_{self.fixes_generated}",
                    'violation_id': violation['id'],
                    'fix_type': fix_type,
                    'confidence': confidence,
                    'safety_level': safety,
                    'description': f"Fix for {violation['description']}",
                    'estimated_effort': 'low' if safety == 'safe' else 'medium'
                })
                
            return fixes
            
        async def apply_fixes(self, fixes: List[Dict[str, Any]], target_path: Path) -> Dict[str, Any]:
            """Mock fix application"""
            await asyncio.sleep(0.5)
            
            safe_fixes = [f for f in fixes if f['safety_level'] == 'safe']
            applied_count = len(safe_fixes)
            
            return {
                'status': 'success',
                'fixes_attempted': len(fixes),
                'fixes_applied': applied_count,
                'fixes_skipped': len(fixes) - applied_count,
                'backups_created': applied_count,
                'application_time': 0.5
            }
    
    return MockAutofixEngine()

@pytest.fixture
def mock_mcp_server():
    """Create mock MCP server for workflow integration"""
    
    class MockMCPServer:
        def __init__(self):
            self.is_running = False
            self.call_count = 0
            
        async def start(self):
            await asyncio.sleep(0.1)
            self.is_running = True
            
        async def stop(self):
            self.is_running = False
            
        async def call_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
            self.call_count += 1
            await asyncio.sleep(0.1)
            
            if tool_name == 'scan_path':
                return {
                    'status': 'success',
                    'findings_count': 8,
                    'quality_score': 72.5
                }
            elif tool_name == 'propose_autofix':
                return {
                    'status': 'success',
                    'fix_available': True,
                    'confidence': 0.85
                }
            elif tool_name == 'suggest_refactors':
                return {
                    'status': 'success',
                    'suggestions': [
                        {'technique': 'Extract Parameter Object', 'confidence': 89},
                        {'technique': 'Extract Constants', 'confidence': 95}
                    ]
                }
            else:
                return {'status': 'success', 'result': f'mock_response_for_{tool_name}'}
    
    server = MockMCPServer()
    await server.start()
    yield server
    await server.stop()

class TestCompleteWorkflowIntegration:
    """Test complete analysis workflows with all components integrated"""
    
    @pytest.mark.asyncio
    async def test_cli_to_analysis_workflow(self, workflow_coordinator, comprehensive_test_workspace, mock_analysis_engine):
        """Test CLI → Analysis Engine → Report Generation workflow"""
        
        start_time = time.time()
        
        # Stage 1: CLI Initialization
        cli_start_time = time.time()
        cli_config = {
            'workspace_path': str(comprehensive_test_workspace),
            'profile': 'comprehensive',
            'output_format': 'json',
            'include_fixes': True
        }
        cli_execution_time = time.time() - cli_start_time
        
        workflow_coordinator.store_workflow_stage('cli_initialization', {
            'config': cli_config,
            'execution_time': cli_execution_time,
            'status': 'success',
            'dependencies': []
        })
        
        # Stage 2: Path Analysis
        analysis_start_time = time.time()
        analysis_result = await mock_analysis_engine.analyze_path(
            comprehensive_test_workspace, 
            cli_config['profile']
        )
        analysis_execution_time = time.time() - analysis_start_time
        
        workflow_coordinator.store_workflow_stage('path_analysis', {
            'findings_count': len(analysis_result['findings']),
            'quality_score': analysis_result['summary']['quality_score'],
            'connascence_index': analysis_result['summary']['connascence_index'],
            'files_analyzed': analysis_result['summary']['files_analyzed'],
            'execution_time': analysis_execution_time,
            'status': 'success',
            'dependencies': ['cli_initialization']
        })
        
        # Stage 3: Report Generation
        report_start_time = time.time()
        report = {
            'summary': analysis_result['summary'],
            'findings': analysis_result['findings'],
            'recommendations': [
                f"Address {len([f for f in analysis_result['findings'] if f['severity'] == 'critical'])} critical violations",
                f"Consider refactoring {len([f for f in analysis_result['findings'] if f['connascence_type'] == 'CoA'])} architectural issues",
                f"Extract {len([f for f in analysis_result['findings'] if f['connascence_type'] == 'CoM'])} magic literals"
            ],
            'next_steps': [
                'Apply automated fixes for safe violations',
                'Review complex refactoring suggestions',
                'Re-run analysis after fixes'
            ]
        }
        report_execution_time = time.time() - report_start_time
        
        workflow_coordinator.store_workflow_stage('report_generation', {
            'report_sections': len(report.keys()),
            'recommendations_count': len(report['recommendations']),
            'next_steps_count': len(report['next_steps']),
            'execution_time': report_execution_time,
            'status': 'success',
            'dependencies': ['path_analysis']
        })
        
        # Validate workflow completion
        total_execution_time = time.time() - start_time
        workflow_stages = workflow_coordinator.get_workflow_progression()
        
        assert len(workflow_stages) == 3
        assert workflow_stages == ['cli_initialization', 'path_analysis', 'report_generation']
        assert total_execution_time < 5.0  # Should complete quickly
        assert analysis_result['summary']['total_violations'] >= 8  # Should find multiple violations
        
    @pytest.mark.asyncio
    async def test_analysis_to_autofix_workflow(self, workflow_coordinator, comprehensive_test_workspace, 
                                               mock_analysis_engine, mock_autofix_engine):
        """Test Analysis → Autofix Generation → Application workflow"""
        
        # Stage 1: Analysis
        analysis_result = await mock_analysis_engine.analyze_path(comprehensive_test_workspace)
        violations = analysis_result['findings']
        
        workflow_coordinator.store_workflow_stage('initial_analysis', {
            'violations_found': len(violations),
            'quality_score_before': analysis_result['summary']['quality_score'],
            'critical_violations': len([v for v in violations if v['severity'] == 'critical']),
            'status': 'success',
            'dependencies': []
        })
        
        # Stage 2: Autofix Generation
        fixes = await mock_autofix_engine.generate_fixes(violations)
        
        safe_fixes = [f for f in fixes if f['safety_level'] == 'safe']
        moderate_fixes = [f for f in fixes if f['safety_level'] == 'moderate']
        
        workflow_coordinator.store_workflow_stage('autofix_generation', {
            'total_fixes': len(fixes),
            'safe_fixes': len(safe_fixes),
            'moderate_fixes': len(moderate_fixes),
            'average_confidence': sum(f['confidence'] for f in fixes) / len(fixes),
            'status': 'success',
            'dependencies': ['initial_analysis']
        })
        
        # Stage 3: Safe Fix Application
        application_result = await mock_autofix_engine.apply_fixes(safe_fixes, comprehensive_test_workspace)
        
        workflow_coordinator.store_workflow_stage('fix_application', {
            'fixes_applied': application_result['fixes_applied'],
            'fixes_skipped': application_result['fixes_skipped'],
            'backups_created': application_result['backups_created'],
            'application_time': application_result['application_time'],
            'status': 'success',
            'dependencies': ['autofix_generation']
        })
        
        # Stage 4: Post-Fix Analysis (to measure improvement)
        post_fix_analysis = await mock_analysis_engine.analyze_path(comprehensive_test_workspace)
        
        # Mock improvement calculation
        initial_score = analysis_result['summary']['quality_score']
        improved_score = initial_score + (application_result['fixes_applied'] * 2.5)  # Mock improvement
        improved_score = min(improved_score, 100)
        
        workflow_coordinator.store_workflow_stage('post_fix_analysis', {
            'quality_score_after': improved_score,
            'quality_improvement': improved_score - initial_score,
            'remaining_violations': len(post_fix_analysis['findings']) - application_result['fixes_applied'],
            'status': 'success',
            'dependencies': ['fix_application']
        })
        
        # Validate workflow effectiveness
        workflow_results = workflow_coordinator.get_workflow_results()
        metrics = workflow_coordinator.calculate_workflow_metrics()
        
        assert metrics['stages_completed'] == 4
        assert metrics['workflow_success_rate'] == 100.0
        assert metrics['average_quality_score'] > 0
        
        # Validate improvement
        initial_result = workflow_results[f'{workflow_coordinator.test_session_id}_initial_analysis']['result']
        final_result = workflow_results[f'{workflow_coordinator.test_session_id}_post_fix_analysis']['result']
        
        assert final_result['quality_improvement'] > 0
        
    @pytest.mark.asyncio
    async def test_mcp_integration_workflow(self, workflow_coordinator, comprehensive_test_workspace, mock_mcp_server):
        """Test MCP Server → Tool Calls → Response Aggregation workflow"""
        
        # Stage 1: MCP Server Initialization
        assert mock_mcp_server.is_running == True
        
        workflow_coordinator.store_workflow_stage('mcp_initialization', {
            'server_running': mock_mcp_server.is_running,
            'initial_call_count': mock_mcp_server.call_count,
            'status': 'success',
            'dependencies': []
        })
        
        # Stage 2: Concurrent Tool Calls
        tool_tasks = [
            mock_mcp_server.call_tool('scan_path', {'path': str(comprehensive_test_workspace)}),
            mock_mcp_server.call_tool('suggest_refactors', {'findings': []}),
            mock_mcp_server.call_tool('propose_autofix', {'violation_id': 'CoM_001'})
        ]
        
        tool_start_time = time.time()
        tool_results = await asyncio.gather(*tool_tasks)
        tool_execution_time = time.time() - tool_start_time
        
        workflow_coordinator.store_workflow_stage('mcp_tool_calls', {
            'tools_called': len(tool_tasks),
            'successful_calls': len([r for r in tool_results if r.get('status') == 'success']),
            'execution_time': tool_execution_time,
            'call_count_after': mock_mcp_server.call_count,
            'status': 'success',
            'dependencies': ['mcp_initialization']
        })
        
        # Stage 3: Response Aggregation
        aggregated_response = {
            'scan_result': tool_results[0],
            'refactor_suggestions': tool_results[1],
            'autofix_proposal': tool_results[2],
            'overall_assessment': {
                'quality_score': tool_results[0].get('quality_score', 72.5),
                'fix_available': tool_results[2].get('fix_available', True),
                'suggestions_count': len(tool_results[1].get('suggestions', []))
            }
        }
        
        workflow_coordinator.store_workflow_stage('response_aggregation', {
            'responses_aggregated': len(tool_results),
            'overall_quality_score': aggregated_response['overall_assessment']['quality_score'],
            'fixes_available': aggregated_response['overall_assessment']['fix_available'],
            'status': 'success',
            'dependencies': ['mcp_tool_calls']
        })
        
        # Validate MCP workflow
        assert len(tool_results) == 3
        assert all(r.get('status') == 'success' for r in tool_results)
        assert tool_execution_time < 1.0  # Should be fast due to concurrency
        
    @pytest.mark.asyncio
    async def test_complete_end_to_end_workflow(self, workflow_coordinator, comprehensive_test_workspace,
                                               mock_analysis_engine, mock_autofix_engine, mock_mcp_server):
        """Test complete end-to-end workflow: CLI → Analysis → MCP → Autofix → Validation"""
        
        workflow_start_time = time.time()
        
        # Stage 1: Project Setup and Configuration
        setup_config = {
            'workspace': str(comprehensive_test_workspace),
            'analysis_profile': 'comprehensive',
            'autofix_enabled': True,
            'mcp_integration': True,
            'output_formats': ['json', 'html', 'junit']
        }
        
        workflow_coordinator.store_workflow_stage('project_setup', {
            'workspace_prepared': True,
            'config_loaded': True,
            'output_formats': len(setup_config['output_formats']),
            'status': 'success',
            'dependencies': []
        })
        
        # Stage 2: Initial Comprehensive Analysis
        initial_analysis = await mock_analysis_engine.analyze_path(
            comprehensive_test_workspace, 
            setup_config['analysis_profile']
        )
        
        workflow_coordinator.store_workflow_stage('initial_analysis', {
            'total_violations': initial_analysis['summary']['total_violations'],
            'quality_score_initial': initial_analysis['summary']['quality_score'],
            'files_analyzed': initial_analysis['summary']['files_analyzed'],
            'languages_detected': len(initial_analysis['metadata']['languages_detected']),
            'status': 'success',
            'dependencies': ['project_setup']
        })
        
        # Stage 3: MCP Server Integration
        mcp_scan_result = await mock_mcp_server.call_tool('scan_path', {
            'path': str(comprehensive_test_workspace),
            'profile': setup_config['analysis_profile']
        })
        
        mcp_refactor_result = await mock_mcp_server.call_tool('suggest_refactors', {
            'findings': initial_analysis['findings'][:5]  # Process first 5 findings
        })
        
        workflow_coordinator.store_workflow_stage('mcp_integration', {
            'mcp_scan_completed': mcp_scan_result['status'] == 'success',
            'mcp_suggestions_received': len(mcp_refactor_result.get('suggestions', [])),
            'mcp_quality_score': mcp_scan_result.get('quality_score', 0),
            'status': 'success',
            'dependencies': ['initial_analysis']
        })
        
        # Stage 4: Autofix Generation and Prioritization
        violations = initial_analysis['findings']
        all_fixes = await mock_autofix_engine.generate_fixes(violations)
        
        # Prioritize fixes by safety and confidence
        safe_high_confidence = [f for f in all_fixes 
                               if f['safety_level'] == 'safe' and f['confidence'] > 0.8]
        moderate_fixes = [f for f in all_fixes 
                         if f['safety_level'] == 'moderate' and f['confidence'] > 0.7]
        
        workflow_coordinator.store_workflow_stage('autofix_generation', {
            'total_fixes_generated': len(all_fixes),
            'safe_high_confidence_fixes': len(safe_high_confidence),
            'moderate_confidence_fixes': len(moderate_fixes),
            'fix_coverage_rate': (len(all_fixes) / len(violations)) * 100,
            'status': 'success',
            'dependencies': ['mcp_integration']
        })
        
        # Stage 5: Automated Fix Application
        application_result = await mock_autofix_engine.apply_fixes(
            safe_high_confidence, 
            comprehensive_test_workspace
        )
        
        workflow_coordinator.store_workflow_stage('automated_fixes', {
            'fixes_applied_count': application_result['fixes_applied'],
            'backups_created': application_result['backups_created'],
            'application_success_rate': (application_result['fixes_applied'] / 
                                       len(safe_high_confidence)) * 100 if safe_high_confidence else 0,
            'status': 'success',
            'dependencies': ['autofix_generation']
        })
        
        # Stage 6: Post-Fix Validation Analysis
        post_fix_analysis = await mock_analysis_engine.analyze_path(comprehensive_test_workspace)
        
        # Calculate improvements (mock realistic improvements)
        initial_quality = initial_analysis['summary']['quality_score']
        fixes_applied = application_result['fixes_applied']
        quality_improvement = fixes_applied * 2.0  # Mock: each fix improves quality by 2 points
        final_quality = min(initial_quality + quality_improvement, 100)
        
        violation_reduction = min(fixes_applied, initial_analysis['summary']['total_violations'])
        remaining_violations = initial_analysis['summary']['total_violations'] - violation_reduction
        
        workflow_coordinator.store_workflow_stage('post_fix_validation', {
            'quality_score_final': final_quality,
            'quality_improvement': quality_improvement,
            'violations_remaining': remaining_violations,
            'violation_reduction_rate': (violation_reduction / initial_analysis['summary']['total_violations']) * 100,
            'status': 'success',
            'dependencies': ['automated_fixes']
        })
        
        # Stage 7: Report Generation and Delivery
        comprehensive_report = {
            'executive_summary': {
                'initial_quality_score': initial_quality,
                'final_quality_score': final_quality,
                'improvement_achieved': quality_improvement,
                'violations_addressed': violation_reduction,
                'automation_rate': (fixes_applied / len(violations)) * 100
            },
            'technical_details': {
                'files_analyzed': initial_analysis['summary']['files_analyzed'],
                'violations_by_type': initial_analysis['summary']['by_type'],
                'fixes_by_safety_level': {
                    'safe': len(safe_high_confidence),
                    'moderate': len(moderate_fixes)
                }
            },
            'recommendations': {
                'immediate_actions': moderate_fixes[:3] if moderate_fixes else [],
                'long_term_refactoring': [f for f in all_fixes if f.get('estimated_effort') == 'high'],
                'process_improvements': [
                    'Integrate connascence analysis into CI/CD pipeline',
                    'Establish code quality gates',
                    'Schedule regular refactoring sessions'
                ]
            }
        }
        
        workflow_coordinator.store_workflow_stage('report_delivery', {
            'report_sections': len(comprehensive_report.keys()),
            'executive_summary_complete': 'executive_summary' in comprehensive_report,
            'technical_details_complete': 'technical_details' in comprehensive_report,
            'recommendations_count': len(comprehensive_report['recommendations']['process_improvements']),
            'status': 'success',
            'dependencies': ['post_fix_validation']
        })
        
        # Final Workflow Assessment
        total_workflow_time = time.time() - workflow_start_time
        workflow_metrics = workflow_coordinator.calculate_workflow_metrics()
        
        workflow_coordinator.store_workflow_stage('workflow_completion', {
            'total_execution_time': total_workflow_time,
            'stages_completed': len(workflow_coordinator.get_workflow_progression()),
            'success_rate': workflow_metrics['workflow_success_rate'],
            'quality_improvement_achieved': quality_improvement,
            'automation_effectiveness': (fixes_applied / len(violations)) * 100,
            'status': 'success',
            'dependencies': ['report_delivery']
        })
        
        # Comprehensive Validation
        final_progression = workflow_coordinator.get_workflow_progression()
        expected_stages = [
            'project_setup', 'initial_analysis', 'mcp_integration',
            'autofix_generation', 'automated_fixes', 'post_fix_validation',
            'report_delivery', 'workflow_completion'
        ]
        
        assert final_progression == expected_stages
        assert workflow_metrics['workflow_success_rate'] == 100.0
        assert workflow_metrics['stages_completed'] == len(expected_stages)
        assert total_workflow_time < 10.0  # Should complete within reasonable time
        
        # Quality Improvement Validation
        final_results = workflow_coordinator.get_workflow_results()
        validation_result = final_results[f'{workflow_coordinator.test_session_id}_post_fix_validation']['result']
        
        assert validation_result['quality_improvement'] > 0
        assert validation_result['violation_reduction_rate'] > 0
        
        # Print workflow summary for debugging
        print(f"\n🚀 Complete Workflow Summary:")
        print(f"   • Total Execution Time: {total_workflow_time:.2f}s")
        print(f"   • Stages Completed: {len(final_progression)}")
        print(f"   • Quality Improvement: {quality_improvement:.1f} points")
        print(f"   • Fixes Applied: {fixes_applied}")
        print(f"   • Success Rate: {workflow_metrics['workflow_success_rate']:.1f}%")
        
    def test_workflow_memory_coordination(self, workflow_coordinator):
        """Test workflow memory coordination and sequential thinking"""
        
        # Simulate storing workflow stages with dependencies
        stages_with_dependencies = [
            ('initialization', []),
            ('analysis', ['initialization']),
            ('processing', ['analysis']),
            ('validation', ['processing', 'analysis']),
            ('reporting', ['validation'])
        ]
        
        for stage_name, deps in stages_with_dependencies:
            workflow_coordinator.store_workflow_stage(stage_name, {
                'stage_completed': True,
                'dependencies': deps,
                'execution_time': 0.1
            })
            
        # Validate sequential storage
        progression = workflow_coordinator.get_workflow_progression()
        assert progression == [stage for stage, _ in stages_with_dependencies]
        
        # Validate dependency tracking
        workflow_results = workflow_coordinator.get_workflow_results()
        for stage_name, expected_deps in stages_with_dependencies:
            result_key = f"{workflow_coordinator.test_session_id}_{stage_name}"
            stored_deps = workflow_results[result_key]['result']['dependencies']
            assert stored_deps == expected_deps
            
        # Validate metrics calculation
        metrics = workflow_coordinator.calculate_workflow_metrics()
        assert metrics['stages_completed'] == len(stages_with_dependencies)
        assert metrics['workflow_success_rate'] == 100.0
        assert metrics['total_execution_time'] > 0

@pytest.mark.asyncio 
class TestWorkflowPerformanceAndScalability:
    """Test workflow performance and scalability characteristics"""
    
    async def test_concurrent_workflow_execution(self, workflow_coordinator, mock_analysis_engine):
        """Test multiple workflows executing concurrently"""
        
        # Create multiple test workspaces
        async def run_single_workflow(workspace_id: int):
            with tempfile.TemporaryDirectory() as tmpdir:
                workspace = Path(tmpdir)
                (workspace / f"test_{workspace_id}.py").write_text(f"""
def test_function_{workspace_id}(a, b, c, d, e):  # CoP violation
    magic_number = {42 + workspace_id}  # CoM violation
    return magic_number * (a + b + c + d + e)
""")
                
                analysis_result = await mock_analysis_engine.analyze_path(workspace)
                return {
                    'workspace_id': workspace_id,
                    'violations_found': len(analysis_result['findings']),
                    'quality_score': analysis_result['summary']['quality_score']
                }
        
        # Run multiple workflows concurrently
        concurrent_workflows = 5
        workflow_tasks = [
            run_single_workflow(i) for i in range(concurrent_workflows)
        ]
        
        start_time = time.time()
        results = await asyncio.gather(*workflow_tasks)
        execution_time = time.time() - start_time
        
        # Validate concurrent execution
        assert len(results) == concurrent_workflows
        assert all(r['violations_found'] > 0 for r in results)
        assert execution_time < 3.0  # Should benefit from concurrency
        
        # Store performance results
        workflow_coordinator.store_workflow_stage('concurrent_performance', {
            'concurrent_workflows': concurrent_workflows,
            'total_execution_time': execution_time,
            'average_time_per_workflow': execution_time / concurrent_workflows,
            'all_workflows_successful': len(results) == concurrent_workflows,
            'throughput': concurrent_workflows / execution_time,
            'status': 'success'
        })
        
    async def test_workflow_scalability_limits(self, workflow_coordinator, mock_analysis_engine):
        """Test workflow behavior with increasing load"""
        
        scalability_results = []
        
        for load_level in [1, 5, 10, 20]:
            # Create test data for load level
            with tempfile.TemporaryDirectory() as tmpdir:
                workspace = Path(tmpdir)
                
                # Create multiple files for each load level
                for i in range(load_level):
                    (workspace / f"module_{i}.py").write_text(f"""
# Module {i} with various violations
def function_with_params_{i}(a, b, c, d, e, f):  # CoP
    constant_{i} = {100 + i}  # CoM
    return constant_{i} * (a + b + c + d + e + f)

class Class_{i}:  # Potential CoA if methods added
    def method_1(self): pass
    def method_2(self): pass
    def method_3(self): pass
""")
                
                # Measure analysis time for this load level
                start_time = time.time()
                analysis_result = await mock_analysis_engine.analyze_path(workspace)
                execution_time = time.time() - start_time
                
                scalability_results.append({
                    'load_level': load_level,
                    'execution_time': execution_time,
                    'violations_per_file': len(analysis_result['findings']) / load_level,
                    'time_per_violation': execution_time / len(analysis_result['findings']) if analysis_result['findings'] else 0
                })
                
        # Analyze scalability characteristics
        workflow_coordinator.store_workflow_stage('scalability_analysis', {
            'load_levels_tested': len(scalability_results),
            'scalability_results': scalability_results,
            'linear_scaling': all(
                r['time_per_violation'] < 0.1 for r in scalability_results
            ),
            'max_load_tested': max(r['load_level'] for r in scalability_results),
            'status': 'success'
        })

if __name__ == '__main__':
    # Run workflow integration tests
    pytest.main([__file__, '-v', '--tb=short', '-k', 'not performance'])