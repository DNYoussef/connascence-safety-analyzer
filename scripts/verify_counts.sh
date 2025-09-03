#!/bin/bash
# Connascence Safety Analyzer - Shell Verification Script
# ======================================================
# 
# Shell wrapper for the Python verification script with additional CI/CD features
# Provides memory coordination and sequential thinking validation
#
# Usage:
#   ./verify_counts.sh [--verbose] [--report-only]
#   
# Exit codes:
#   0 - Success (all validations passed)
#   1 - Validation failed (counts don't match)
#   2 - Configuration error (missing files/invalid setup)
#   3 - Runtime error (script failure)

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PYTHON_SCRIPT="$SCRIPT_DIR/verify_counts.py"
DEMO_ARTIFACTS_DIR="$PROJECT_ROOT/DEMO_ARTIFACTS"
MEMORY_COORDINATION_FILE="$DEMO_ARTIFACTS_DIR/memory_coordination.json"

# Exit codes (matching Python script)
EXIT_SUCCESS=0
EXIT_VALIDATION_FAILED=1
EXIT_CONFIG_ERROR=2
EXIT_RUNTIME_ERROR=3

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check prerequisites
check_prerequisites() {
    log_info "🔍 Checking prerequisites..."
    
    # Check Python is available
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is required but not installed"
        exit $EXIT_CONFIG_ERROR
    fi
    
    # Check Python script exists
    if [[ ! -f "$PYTHON_SCRIPT" ]]; then
        log_error "Python verification script not found: $PYTHON_SCRIPT"
        exit $EXIT_CONFIG_ERROR
    fi
    
    # Check project structure
    if [[ ! -f "$PROJECT_ROOT/README.md" ]]; then
        log_error "README.md not found in project root: $PROJECT_ROOT"
        exit $EXIT_CONFIG_ERROR
    fi
    
    # Check DEMO_ARTIFACTS directory
    if [[ ! -d "$DEMO_ARTIFACTS_DIR" ]]; then
        log_warning "DEMO_ARTIFACTS directory not found, will be created"
        mkdir -p "$DEMO_ARTIFACTS_DIR"
    fi
    
    log_success "Prerequisites check passed"
}

# Function to setup memory coordination
setup_memory_coordination() {
    log_info "💾 Setting up memory coordination..."
    
    local session_id="verification-$(date +%Y%m%d-%H%M%S)"
    local timestamp=$(date -Iseconds)
    
    # Create initial memory coordination file if it doesn't exist
    if [[ ! -f "$MEMORY_COORDINATION_FILE" ]]; then
        cat > "$MEMORY_COORDINATION_FILE" <<EOF
{
  "coordination_system": "flow-nexus-memory",
  "version": "2.0.0",
  "validation_session": {
    "session_id": "$session_id",
    "start_time": "$timestamp",
    "memory_keys": []
  },
  "sequential_thinking": {
    "step_1": "Parse README.md for violation counts",
    "step_2": "Parse DEMO_ARTIFACTS/index.json for expected counts",
    "step_3": "Validate individual artifact files exist and parse correctly",
    "step_4": "Cross-reference all counts for consistency",
    "step_5": "Generate comprehensive validation report",
    "step_6": "Store results in memory for CI coordination"
  },
  "memory_storage": {
    "shell_wrapper": {
      "started": "$timestamp",
      "session_id": "$session_id",
      "script_path": "$0"
    }
  }
}
EOF
        log_success "Memory coordination initialized"
    else
        log_info "Using existing memory coordination file"
    fi
}

# Function to validate expected counts (shell-based parsing)
validate_shell_parsing() {
    log_info "🔍 Shell-based validation (backup parsing)..."
    
    local readme_file="$PROJECT_ROOT/README.md"
    local errors=0
    
    if [[ -f "$readme_file" ]]; then
        # Extract violation counts using shell tools
        local celery_count=$(grep -E "[0-9,]+.*violations.*Celery" "$readme_file" | head -1 | grep -oE "[0-9,]+" | head -1 | tr -d ',')
        local curl_count=$(grep -E "[0-9,]+.*violations.*curl" "$readme_file" | head -1 | grep -oE "[0-9,]+" | head -1 | tr -d ',')
        local express_count=$(grep -E "[0-9,]+.*violations.*Express" "$readme_file" | head -1 | grep -oE "[0-9,]+" | head -1 | tr -d ',')
        local total_count=$(grep -E "detected.*[0-9,]+.*violations" "$readme_file" | head -1 | grep -oE "[0-9,]+" | head -1 | tr -d ',')
        
        # Expected values
        local expected_celery=4630
        local expected_curl=1061
        local expected_express=52
        local expected_total=5743
        
        # Validation
        log_info "Shell parsing results:"
        log_info "  Celery: $celery_count (expected: $expected_celery)"
        log_info "  curl: $curl_count (expected: $expected_curl)"
        log_info "  Express: $express_count (expected: $expected_express)"
        log_info "  Total: $total_count (expected: $expected_total)"
        
        # Check each count
        [[ "$celery_count" != "$expected_celery" ]] && { log_error "Celery count mismatch"; ((errors++)); }
        [[ "$curl_count" != "$expected_curl" ]] && { log_error "curl count mismatch"; ((errors++)); }
        [[ "$express_count" != "$expected_express" ]] && { log_error "Express count mismatch"; ((errors++)); }
        [[ "$total_count" != "$expected_total" ]] && { log_error "Total count mismatch"; ((errors++)); }
        
        if [[ $errors -eq 0 ]]; then
            log_success "Shell validation passed"
            return 0
        else
            log_error "Shell validation failed with $errors errors"
            return 1
        fi
    else
        log_error "README.md not found for shell parsing"
        return 1
    fi
}

# Function to run Python validation
run_python_validation() {
    log_info "🐍 Running Python validation script..."
    
    local python_args=("--base-path" "$PROJECT_ROOT")
    
    # Add verbose flag if requested
    if [[ "${1:-}" == "--verbose" ]]; then
        python_args+=("--verbose")
    fi
    
    # Add report-only flag if requested
    if [[ "${1:-}" == "--report-only" || "${2:-}" == "--report-only" ]]; then
        python_args+=("--report-only")
    fi
    
    # Run Python validation
    if python3 "$PYTHON_SCRIPT" "${python_args[@]}"; then
        log_success "Python validation completed successfully"
        return 0
    else
        local exit_code=$?
        case $exit_code in
            $EXIT_VALIDATION_FAILED)
                log_error "Python validation failed - counts don't match"
                ;;
            $EXIT_CONFIG_ERROR)
                log_error "Python validation failed - configuration error"
                ;;
            $EXIT_RUNTIME_ERROR)
                log_error "Python validation failed - runtime error"
                ;;
            *)
                log_error "Python validation failed with unexpected exit code: $exit_code"
                ;;
        esac
        return $exit_code
    fi
}

# Function to generate summary report
generate_summary() {
    log_info "📊 Generating validation summary..."
    
    local validation_report="$DEMO_ARTIFACTS_DIR/validation_report.json"
    local memory_file="$MEMORY_COORDINATION_FILE"
    
    echo "=============================================================="
    echo "CONNASCENCE SAFETY ANALYZER - VALIDATION SUMMARY"
    echo "=============================================================="
    echo "Timestamp: $(date -Iseconds)"
    echo "Project Root: $PROJECT_ROOT"
    echo "Session ID: $(jq -r '.validation_session.session_id // "unknown"' "$memory_file" 2>/dev/null || echo "unknown")"
    echo ""
    
    # Show validation results if available
    if [[ -f "$validation_report" ]]; then
        echo "Validation Results:"
        echo "  Total Tests: $(jq -r '.summary.total_tests // "N/A"' "$validation_report" 2>/dev/null || echo "N/A")"
        echo "  Passed: $(jq -r '.summary.passed // "N/A"' "$validation_report" 2>/dev/null || echo "N/A")"
        echo "  Failed: $(jq -r '.summary.failed // "N/A"' "$validation_report" 2>/dev/null || echo "N/A")"
        echo "  Errors: $(jq -r '.summary.errors // "N/A"' "$validation_report" 2>/dev/null || echo "N/A")"
        echo "  Success Rate: $(jq -r '.summary.success_rate // "N/A"' "$validation_report" 2>/dev/null || echo "N/A")%"
        echo ""
        
        # Show expected vs actual counts
        echo "Expected Counts:"
        echo "  Celery: 4,630 violations"
        echo "  curl: 1,061 violations" 
        echo "  Express: 52 violations"
        echo "  Total: 5,743 violations"
        echo ""
    fi
    
    echo "Files Generated:"
    [[ -f "$validation_report" ]] && echo "  ✅ $validation_report"
    [[ -f "$memory_file" ]] && echo "  ✅ $memory_file"
    [[ -f "$DEMO_ARTIFACTS_DIR/index.json" ]] && echo "  ✅ $DEMO_ARTIFACTS_DIR/index.json"
    echo ""
    
    echo "=============================================================="
}

# Function to handle cleanup on exit
cleanup() {
    local exit_code=$?
    
    if [[ $exit_code -ne 0 ]]; then
        log_error "Script exiting with code $exit_code"
        
        # Update memory coordination with failure status
        if [[ -f "$MEMORY_COORDINATION_FILE" ]] && command -v jq &> /dev/null; then
            local timestamp=$(date -Iseconds)
            local temp_file=$(mktemp)
            jq --arg ts "$timestamp" --arg code "$exit_code" \
               '.memory_storage.shell_wrapper.exit_timestamp = $ts | .memory_storage.shell_wrapper.exit_code = ($code | tonumber)' \
               "$MEMORY_COORDINATION_FILE" > "$temp_file" && mv "$temp_file" "$MEMORY_COORDINATION_FILE"
        fi
    fi
}

# Main execution function
main() {
    local verbose=false
    local report_only=false
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --verbose)
                verbose=true
                shift
                ;;
            --report-only)
                report_only=true
                shift
                ;;
            --help|-h)
                echo "Usage: $0 [--verbose] [--report-only] [--help]"
                echo ""
                echo "Options:"
                echo "  --verbose      Enable verbose logging"
                echo "  --report-only  Generate report without validation"
                echo "  --help, -h     Show this help message"
                echo ""
                echo "Exit codes:"
                echo "  0 - Success (all validations passed)"
                echo "  1 - Validation failed (counts don't match)"
                echo "  2 - Configuration error (missing files/invalid setup)"
                echo "  3 - Runtime error (script failure)"
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                echo "Use --help for usage information"
                exit $EXIT_CONFIG_ERROR
                ;;
        esac
    done
    
    # Set up cleanup handler
    trap cleanup EXIT
    
    log_info "🚀 Starting Connascence Safety Analyzer Verification"
    log_info "Project Root: $PROJECT_ROOT"
    
    # Run prerequisite checks
    check_prerequisites
    
    # Setup memory coordination
    setup_memory_coordination
    
    # Run validation steps
    local validation_success=true
    local shell_args=""
    
    [[ "$verbose" == true ]] && shell_args="--verbose"
    [[ "$report_only" == true ]] && shell_args="$shell_args --report-only"
    
    # Run shell-based validation as backup
    if ! validate_shell_parsing; then
        validation_success=false
        log_warning "Shell validation failed, continuing with Python validation"
    fi
    
    # Run Python validation (primary method)
    if ! run_python_validation $shell_args; then
        validation_success=false
    fi
    
    # Generate summary report
    generate_summary
    
    # Final result
    if [[ "$validation_success" == true ]]; then
        log_success "🎯 All validations completed successfully!"
        
        # Update memory coordination with success status
        if [[ -f "$MEMORY_COORDINATION_FILE" ]] && command -v jq &> /dev/null; then
            local timestamp=$(date -Iseconds)
            local temp_file=$(mktemp)
            jq --arg ts "$timestamp" \
               '.memory_storage.shell_wrapper.completion_timestamp = $ts | .memory_storage.shell_wrapper.status = "success"' \
               "$MEMORY_COORDINATION_FILE" > "$temp_file" && mv "$temp_file" "$MEMORY_COORDINATION_FILE"
        fi
        
        exit $EXIT_SUCCESS
    else
        log_error "❌ Validation failed!"
        exit $EXIT_VALIDATION_FAILED
    fi
}

# Execute main function with all arguments
main "$@"