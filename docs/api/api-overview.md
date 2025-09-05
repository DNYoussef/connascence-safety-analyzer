# Connascence Safety Analyzer - API Documentation

## Overview

The Connascence Safety Analyzer provides multiple API interfaces for integration with external systems, IDEs, and CI/CD pipelines. This document consolidates all available APIs and integration points.

## 🔌 **API Interfaces**

### **1. MCP Server API** 
**Location:** `mcp/nasa_power_of_ten_integration.py`  
**Purpose:** Claude Code integration and tool coordination  
**Protocol:** MCP (Model Context Protocol)

### **2. REST API**
**Location:** `dashboard/ci_integration.py`  
**Purpose:** HTTP-based analysis requests and reporting  
**Protocol:** RESTful HTTP/JSON

### **3. VS Code Extension API**
**Location:** `vscode-extension/src/services/`  
**Purpose:** IDE integration with real-time analysis  
**Protocol:** VS Code Extension API + WebSocket

### **4. CLI API**
**Location:** `analyzer/core.py`  
**Purpose:** Command-line analysis and CI/CD integration  
**Protocol:** Command-line interface with JSON/SARIF output

## 🛠️ **MCP Server API**

### **Connection & Setup**

```python
# MCP Server Configuration
from mcp import MCPServer

server = MCPServer(
    name="connascence-analyzer",
    version="1.0.0",
    description="NASA-compliant connascence analysis with MECE de-duplication"
)
```

### **Available Tools**

#### **`analyze_connascence`**
**Purpose:** Primary analysis endpoint for code analysis

```python
@server.register_tool("analyze_connascence")
async def analyze_connascence(
    code: str,
    language: str = "python", 
    policy: str = "nasa_jpl_pot10",
    include_fixes: bool = True
) -> AnalysisResult:
    """
    Analyze code for connascence violations with NASA compliance
    
    Args:
        code: Source code to analyze
        language: Programming language (python|c|cpp|javascript|typescript)
        policy: Analysis policy (nasa_jpl_pot10|strict-core|enterprise-standard)
        include_fixes: Include auto-fix suggestions in response
    
    Returns:
        AnalysisResult with violations, NASA compliance, and MECE analysis
    """
```

**Response Format:**
```json
{
    "violations": [
        {
            "type": "CoM",
            "severity": "high",
            "line": 42,
            "column": 15,
            "description": "Magic number 500 used without constant",
            "suggestion": "Extract to named constant: MAX_RETRY_COUNT = 500"
        }
    ],
    "nasa_compliance": {
        "score": 0.95,
        "violations": [
            {
                "rule": 7,
                "description": "Function has 5 parameters, exceeds limit of 3",
                "location": "line 28"
            }
        ]
    },
    "mece_analysis": {
        "score": 0.85,
        "duplications": [
            {
                "type": "exact",
                "locations": ["file1.py:15-20", "file2.py:88-93"],
                "confidence": 0.95
            }
        ]
    },
    "tool_correlations": [
        {
            "connascence_violation": "CoM at line 42",
            "external_tools": ["ruff", "mypy"],
            "confidence": 0.95,
            "priority": "critical"
        }
    ]
}
```

#### **`validate_nasa_compliance`**
**Purpose:** Dedicated NASA Power of Ten rules validation

```python
@server.register_tool("validate_nasa_compliance")
async def validate_nasa_compliance(
    code: str,
    language: str = "python",
    strict_mode: bool = False
) -> ComplianceResult:
    """
    Validate code against NASA Power of Ten rules
    
    Args:
        code: Source code to validate
        language: Programming language  
        strict_mode: Enable stricter interpretation of rules
    
    Returns:
        ComplianceResult with rule-by-rule validation
    """
```

#### **`analyze_mece_duplications`**
**Purpose:** MECE analysis for duplication detection

```python
@server.register_tool("analyze_mece_duplications")  
async def analyze_mece_duplications(
    codebase_path: str,
    threshold: float = 0.8,
    include_recommendations: bool = True
) -> MECEResult:
    """
    Perform MECE analysis for code duplication detection
    
    Args:
        codebase_path: Path to codebase root
        threshold: Similarity threshold (0.0-1.0)
        include_recommendations: Include fix recommendations
    
    Returns:
        MECEResult with duplication analysis and recommendations
    """
```

#### **`correlate_tool_findings`**
**Purpose:** Cross-tool correlation with external analysis tools

```python
@server.register_tool("correlate_tool_findings")
async def correlate_tool_findings(
    connascence_results: AnalysisResult,
    external_results: Dict[str, ToolResult],
    confidence_threshold: float = 0.8
) -> CorrelatedResults:
    """
    Correlate connascence findings with external tool results
    
    Args:
        connascence_results: Results from connascence analysis
        external_results: Results from external tools (ruff, mypy, etc.)
        confidence_threshold: Minimum confidence for correlation
    
    Returns:
        CorrelatedResults with cross-tool correlations and priorities
    """
```

### **Error Handling**

```json
{
    "error": {
        "code": "ANALYSIS_ERROR",
        "message": "Failed to parse Python AST",
        "details": {
            "line": 15,
            "column": 8,
            "syntax_error": "invalid syntax"
        }
    }
}
```

## 🌐 **REST API**

### **Base URL**
```
http://localhost:8000/api/v1
```

### **Authentication**
```http
Authorization: Bearer <api_token>
```

### **Endpoints**

#### **POST /analyze**
**Purpose:** Analyze code via HTTP request

```http
POST /api/v1/analyze
Content-Type: application/json

{
    "code": "def process_data(a, b, c, d, e):\n    return a * 42 + b",
    "language": "python",
    "policy": "nasa_jpl_pot10",
    "options": {
        "include_fixes": true,
        "enable_tool_correlation": true
    }
}
```

**Response:**
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
    "analysis_id": "uuid-12345",
    "status": "completed",
    "results": { /* AnalysisResult object */ },
    "processing_time": 1.23,
    "metadata": {
        "version": "1.0.0",
        "policy_used": "nasa_jpl_pot10"
    }
}
```

#### **GET /analyze/{analysis_id}**
**Purpose:** Retrieve analysis results by ID

```http
GET /api/v1/analyze/uuid-12345
```

#### **POST /batch-analyze**
**Purpose:** Analyze multiple files or entire codebase

```http
POST /api/v1/batch-analyze
Content-Type: application/json

{
    "codebase_path": "/path/to/project",
    "policy": "nasa_jpl_pot10",
    "options": {
        "parallel": true,
        "max_files": 1000,
        "exclude_patterns": ["**/node_modules/**", "**/*.min.js"]
    }
}
```

#### **GET /policies**
**Purpose:** List available analysis policies

```http
GET /api/v1/policies
```

**Response:**
```json
{
    "policies": [
        {
            "name": "nasa_jpl_pot10",
            "description": "NASA JPL Power of Ten rules",
            "parameters": {
                "max_parameters": 3,
                "max_function_lines": 60,
                "require_assertions": true
            }
        },
        {
            "name": "strict-core", 
            "description": "Strict connascence analysis",
            "parameters": {
                "max_parameters": 2,
                "mece_threshold": 0.9
            }
        }
    ]
}
```

#### **GET /health**
**Purpose:** Health check endpoint

```http
GET /api/v1/health
```

**Response:**
```json
{
    "status": "healthy",
    "version": "1.0.0",
    "components": {
        "analyzer_engine": "operational",
        "nasa_validator": "operational", 
        "mece_analyzer": "operational",
        "tool_coordinator": "operational"
    }
}
```

#### **POST /webhook**
**Purpose:** Webhook endpoint for CI/CD integration

```http
POST /api/v1/webhook
Content-Type: application/json
X-GitHub-Event: push

{
    "repository": {
        "clone_url": "https://github.com/user/repo.git",
        "default_branch": "main"
    },
    "head_commit": {
        "id": "abc123",
        "modified": ["src/main.py", "src/utils.py"]
    }
}
```

## 📱 **VS Code Extension API**

### **Internal Services**

#### **AnalysisService**
**Location:** `vscode-extension/src/services/aiIntegrationService.ts`

```typescript
class AnalysisService {
    async analyzeDocument(document: TextDocument): Promise<Violation[]> {
        const analysisRequest = {
            code: document.getText(),
            language: document.languageId,
            policy: this.getActivePolicy(),
            realtime: true
        };
        
        return await this.mcpClient.analyze(analysisRequest);
    }
    
    async validateNASACompliance(document: TextDocument): Promise<ComplianceResult> {
        return await this.mcpClient.validateNASA({
            code: document.getText(),
            language: document.languageId
        });
    }
}
```

#### **Dashboard Service**
**Location:** `vscode-extension/src/dashboard.ts`

```typescript
class DashboardService {
    async generateDashboard(): Promise<void> {
        const analysisResults = await this.analysisService.analyzeWorkspace();
        const dashboardData = this.prepareDashboardData(analysisResults);
        
        this.webviewPanel.webview.html = this.renderDashboard(dashboardData);
    }
    
    private prepareDashboardData(results: AnalysisResult[]): DashboardData {
        return {
            totalViolations: results.reduce((sum, r) => sum + r.violations.length, 0),
            severityBreakdown: this.calculateSeverityBreakdown(results),
            nasaCompliance: this.calculateNASACompliance(results),
            meceScore: this.calculateMECEScore(results)
        };
    }
}
```

### **Commands**

#### **Extension Commands**
```json
{
    "commands": [
        {
            "command": "connascence.analyzeFile",
            "title": "Analyze Current File",
            "category": "Connascence"
        },
        {
            "command": "connascence.analyzeWorkspace", 
            "title": "Analyze Entire Workspace",
            "category": "Connascence"
        },
        {
            "command": "connascence.validateNASA",
            "title": "Validate NASA Safety Rules",
            "category": "Connascence"
        },
        {
            "command": "connascence.generateReport",
            "title": "Generate Quality Report", 
            "category": "Connascence"
        }
    ]
}
```

### **Configuration**

```json
{
    "configuration": {
        "properties": {
            "connascence.safetyProfile": {
                "type": "string",
                "enum": ["none", "nasa_jpl_pot10", "nasa_loc_1", "nasa_loc_3", "modern_general"],
                "default": "nasa_jpl_pot10",
                "description": "Safety profile for analysis"
            },
            "connascence.realTimeAnalysis": {
                "type": "boolean",
                "default": true,
                "description": "Enable real-time analysis as you type"
            },
            "connascence.maxDiagnostics": {
                "type": "number",
                "default": 1500,
                "description": "Maximum number of diagnostics to show"
            }
        }
    }
}
```

## 💻 **CLI API**

### **Basic Usage**

```bash
# Basic analysis
python -m analyzer.core --path /path/to/project --policy nasa_jpl_pot10

# Output formats
python -m analyzer.core --path . --format json --output results.json
python -m analyzer.core --path . --format sarif --output results.sarif  
python -m analyzer.core --path . --format html --output report.html

# Policy options
python -m analyzer.core --path . --policy strict-core
python -m analyzer.core --path . --policy enterprise-standard
```

### **Advanced Options**

```bash
# NASA compliance validation
python -m analyzer.core --path . --nasa-validation --strict-mode

# MECE analysis
python -m analyzer.core --path . --mece-analysis --threshold 0.8

# Tool correlation
python -m analyzer.core --path . --enable-tool-correlation --confidence-threshold 0.8

# Parallel processing
python -m analyzer.core --path . --parallel --max-workers 8

# CI/CD integration
python -m analyzer.core --path . --ci-mode --fail-on-critical --github-output
```

### **Exit Codes**

```bash
0  # Success - no critical violations
1  # Analysis completed with critical violations
2  # Configuration error
3  # Runtime error
4  # Policy validation failed
5  # NASA compliance failed
```

### **JSON Output Schema**

```json
{
    "$schema": "https://connascence.io/schemas/analysis-result-v1.json",
    "version": "1.0.0",
    "analysis_metadata": {
        "timestamp": "2024-01-15T10:30:00Z",
        "policy": "nasa_jpl_pot10",
        "processing_time": 2.45,
        "files_analyzed": 156
    },
    "violations": [ /* Violation objects */ ],
    "nasa_compliance": { /* ComplianceResult */ },
    "mece_analysis": { /* MECEResult */ },
    "tool_correlations": [ /* CorrelatedResult objects */ ],
    "summary": {
        "total_violations": 127,
        "by_severity": {
            "critical": 3,
            "high": 15,
            "medium": 89,
            "low": 20
        },
        "nasa_compliance_score": 0.92,
        "mece_score": 0.78,
        "overall_quality_score": 0.85
    }
}
```

## 🔗 **Integration Examples**

### **GitHub Actions**

```yaml
- name: Connascence Analysis
  run: |
    python -m analyzer.core \
      --path . \
      --policy nasa_jpl_pot10 \
      --format sarif \
      --output analysis.sarif \
      --github-output \
      --fail-on-critical

- name: Upload SARIF
  uses: github/codeql-action/upload-sarif@v2
  with:
    sarif_file: analysis.sarif
```

### **Pre-commit Hook**

```python
# .pre-commit-config.yaml
- repo: local
  hooks:
  - id: connascence-analysis
    name: Connascence Analysis
    entry: python -m analyzer.core
    args: ['--path', '.', '--policy', 'nasa_jpl_pot10', '--fail-on-critical']
    language: python
```

### **Docker Integration**

```dockerfile
FROM python:3.12-slim
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . /app
WORKDIR /app

ENTRYPOINT ["python", "-m", "analyzer.core"]
CMD ["--help"]
```

```bash
# Run analysis in Docker
docker run --rm -v $(pwd):/app connascence-analyzer \
  --path /app --policy nasa_jpl_pot10 --format json
```

### **Kubernetes Job**

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: connascence-analysis
spec:
  template:
    spec:
      containers:
      - name: analyzer
        image: connascence-analyzer:latest
        args: 
        - "--path"
        - "/workspace"
        - "--policy" 
        - "nasa_jpl_pot10"
        - "--format"
        - "sarif"
        - "--output"
        - "/results/analysis.sarif"
        volumeMounts:
        - name: workspace
          mountPath: /workspace
        - name: results
          mountPath: /results
      volumes:
      - name: workspace
        persistentVolumeClaim:
          claimName: source-code-pvc
      - name: results
        persistentVolumeClaim:
          claimName: analysis-results-pvc
      restartPolicy: Never
```

## 📊 **API Rate Limits & Performance**

### **Rate Limits**

- **MCP Server:** No rate limits (local processing)
- **REST API:** 100 requests/minute per API key
- **Batch Analysis:** 10 concurrent jobs per user
- **Webhook:** 50 webhook calls/hour

### **Performance Characteristics**

- **Small files (<500 lines):** ~100ms analysis time
- **Medium files (500-2000 lines):** ~500ms analysis time  
- **Large files (2000+ lines):** ~2000ms analysis time
- **Enterprise codebases:** Linear scaling with parallel processing

### **Resource Requirements**

- **Memory:** 50MB base + 10MB per 1000 lines of code
- **CPU:** Single-core sufficient for files <1000 lines
- **Storage:** 1MB cache per 10,000 lines analyzed

## 🔐 **Security & Authentication**

### **API Key Management**

```python
# Generate API key
python -m scripts.generate_api_key --user enterprise-user --permissions read,write,admin

# Use API key
curl -H "Authorization: Bearer <api_key>" \
     -X POST https://api.connascence.io/v1/analyze
```

### **Webhook Security**

```python
# Webhook signature validation
import hmac
import hashlib

def validate_webhook(payload: bytes, signature: str, secret: str) -> bool:
    expected = hmac.new(
        secret.encode(), 
        payload, 
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)
```

### **Rate Limiting**

```python
# Custom rate limiting
from functools import wraps
import time

def rate_limit(max_calls: int, period: int):
    def decorator(func):
        calls = []
        @wraps(func)
        def wrapper(*args, **kwargs):
            now = time.time()
            calls[:] = [call_time for call_time in calls if now - call_time < period]
            if len(calls) >= max_calls:
                raise RateLimitError("Too many requests")
            calls.append(now)
            return func(*args, **kwargs)
        return wrapper
    return decorator
```

---

**This API documentation provides:**
- ✅ **Complete Integration Coverage** - All API interfaces documented
- ✅ **Real-world Examples** - Practical integration patterns
- ✅ **Enterprise Features** - Authentication, rate limiting, security
- ✅ **Multi-Protocol Support** - MCP, REST, CLI, VS Code Extension APIs
- ✅ **Production-Ready** - Performance characteristics and resource requirements