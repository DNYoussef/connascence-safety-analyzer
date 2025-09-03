/**
 * NASA/JPL Power of Ten Rules Compliant Code
 * 
 * This file demonstrates proper adherence to NASA/JPL coding standards.
 * Shows the corrected version of violations from sample_violations.c
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>

// Configuration constants (Rule 6 - minimize globals, use constants)
#define MAX_BUFFER_SIZE 1024
#define MAX_FACTORIAL 12  // Safe limit for factorial calculation
#define MAX_LOOP_ITERATIONS 1000
#define INIT_COMPLETE_MARKER 0xDEADBEEF

// Limited global state with clear purpose (Rule 6)
static int system_init_marker = 0;

// Pre-allocated memory pools (Rule 3 - no heap after init)
static char message_buffer[MAX_BUFFER_SIZE];
static int calculation_results[100];
static int buffer_index = 0;

// Rule 1 COMPLIANT: Iterative factorial instead of recursive
int safe_factorial(int n) {
    // Rule 5: Parameter validation with assertions
    assert(n >= 0);
    assert(n <= MAX_FACTORIAL);  // Prevent overflow
    
    if (n <= 1) return 1;
    
    int result = 1;
    // Rule 2: Bounded loop with clear upper limit
    for (int i = 2; i <= n && i <= MAX_FACTORIAL; i++) {
        result *= i;
        // Rule 5: Check for overflow
        assert(result > 0);  // Simple overflow detection
    }
    
    return result;
}

// Rule 4 COMPLIANT: Short, focused function
// Rule 7 COMPLIANT: Parameter validation
int validate_and_copy_data(const char* source, char* dest, int dest_size) {
    // Rule 5: Multiple assertions for parameter validation
    assert(source != NULL);
    assert(dest != NULL);
    assert(dest_size > 0);
    assert(dest_size <= MAX_BUFFER_SIZE);
    
    int source_len = strlen(source);
    
    // Rule 7: Check boundaries
    if (source_len >= dest_size) {
        return -1;  // Error: insufficient space
    }
    
    // Safe copy with bounds checking
    strncpy(dest, source, dest_size - 1);
    dest[dest_size - 1] = '\0';  // Ensure null termination
    
    return source_len;
}

// Rule 4 COMPLIANT: Process data in smaller functions
int count_valid_chars(const char* data, int len) {
    assert(data != NULL);
    assert(len >= 0);
    assert(len <= MAX_BUFFER_SIZE);
    
    int valid_count = 0;
    
    // Rule 2: Bounded loop with explicit limit
    for (int i = 0; i < len && i < MAX_BUFFER_SIZE; i++) {
        if (data[i] >= 32 && data[i] <= 126) {  // Printable ASCII
            valid_count++;
        }
    }
    
    return valid_count;
}

// Rule 4 COMPLIANT: Extract error handling to separate function
int handle_processing_errors(const char* data, int position) {
    assert(data != NULL);
    assert(position >= 0);
    
    // Log error safely
    if (position < MAX_BUFFER_SIZE) {
        fprintf(stderr, "Processing error at position %d, char: 0x%02X\n", 
                position, (unsigned char)data[position]);
    }
    
    return 1;  // Error count
}

// Rule 1 & 4 COMPLIANT: Structured control flow, reasonable size
int process_data_safely(const char* data, int len) {
    assert(data != NULL);
    assert(len >= 0);
    assert(len <= MAX_BUFFER_SIZE);
    
    int errors = 0;
    int processed = 0;
    
    // Rule 2: Bounded loop with clear termination
    for (int i = 0; i < len && i < MAX_BUFFER_SIZE && processed < MAX_BUFFER_SIZE - 1; i++) {
        if (data[i] == '\0') {
            errors += handle_processing_errors(data, i);
            continue;  // Structured control flow instead of goto
        }
        
        if (data[i] >= 32) {  // Valid character
            message_buffer[processed++] = data[i];
        }
    }
    
    message_buffer[processed] = '\0';  // Null terminate
    buffer_index = processed;
    
    return errors;
}

// Rule 4 COMPLIANT: Broken into smaller functions
typedef struct {
    int param1;
    int param2; 
    const char* param3;
    float param4;
} ProcessingParams;

// Rule 7 COMPLIANT: Parameter validation
static int validate_processing_params(const ProcessingParams* params) {
    assert(params != NULL);
    
    if (params->param1 < 0 || params->param1 > 100) return 0;
    if (params->param2 < 0 || params->param2 > 50) return 0;  
    if (params->param3 == NULL) return 0;
    if (params->param4 < 0.0 || params->param4 > 10.0) return 0;
    
    return 1;  // Valid parameters
}

// Rule 4 COMPLIANT: Smaller, focused function
static int calculate_result_matrix(const ProcessingParams* params, int* result_buffer, int buffer_size) {
    assert(params != NULL);
    assert(result_buffer != NULL);
    assert(buffer_size > 0);
    
    int total_result = 0;
    int buffer_pos = 0;
    
    // Rule 2: Bounded nested loops with explicit limits
    for (int i = 0; i < params->param1 && i < 20; i++) {
        for (int j = 0; j < params->param2 && j < 10; j++) {
            if (buffer_pos >= buffer_size) break;  // Bounds check
            
            // Simplified calculation
            int value = (i * j) + (int)(params->param4 * 10);
            result_buffer[buffer_pos++] = value;
            total_result += value;
        }
    }
    
    return total_result;
}

// Rule 4 COMPLIANT: Main processing function - reasonable size
int safe_processing_function(const ProcessingParams* params) {
    // Rule 5: Parameter validation
    assert(params != NULL);
    
    if (!validate_processing_params(params)) {
        return -1;  // Invalid parameters
    }
    
    // Pre-allocated buffer (Rule 3)
    int temp_results[100];
    
    int result = calculate_result_matrix(params, temp_results, 100);
    
    // Store results in global buffer
    if (result > 0 && result < 100) {
        calculation_results[0] = result;
    }
    
    return result;
}

// Rule 3 COMPLIANT: Initialization phase allocation only
void system_initialization(void) {
    // Mark system as initializing
    system_init_marker = 0;
    
    // All allocations happen here during init
    memset(message_buffer, 0, sizeof(message_buffer));
    memset(calculation_results, 0, sizeof(calculation_results));
    buffer_index = 0;
    
    // Mark initialization complete
    system_init_marker = INIT_COMPLETE_MARKER;
}

// Rule 3 COMPLIANT: No runtime allocation after init
int process_runtime_request(const char* request_data) {
    // Rule 5: Verify system is initialized
    assert(system_init_marker == INIT_COMPLETE_MARKER);
    assert(request_data != NULL);
    
    // Use pre-allocated buffers only
    return validate_and_copy_data(request_data, message_buffer, MAX_BUFFER_SIZE);
}

// Rule 5 COMPLIANT: Proper assertions and error handling
int safe_array_operation(int* array, int size, int multiplier) {
    // Rule 5: Multiple assertions for safety
    assert(array != NULL);
    assert(size > 0);
    assert(size <= 1000);  // Reasonable upper bound
    assert(multiplier >= 0);
    assert(multiplier <= 100);  // Prevent overflow
    
    // Rule 2: Bounded loop
    for (int i = 0; i < size; i++) {
        // Rule 5: Check for potential overflow
        assert(array[i] <= (INT_MAX / multiplier));
        array[i] *= multiplier;
    }
    
    return 0;  // Success
}

// Rule 7 COMPLIANT: Check all return values
int safe_file_operation(const char* filename) {
    assert(filename != NULL);
    
    // Rule 7: Check file open return value
    FILE* file = fopen(filename, "r");
    if (file == NULL) {
        fprintf(stderr, "Failed to open file: %s\n", filename);
        return -1;
    }
    
    char buffer[256];
    // Rule 7: Check read return value
    if (fgets(buffer, sizeof(buffer), file) == NULL) {
        fprintf(stderr, "Failed to read from file: %s\n", filename);
        fclose(file);
        return -2;
    }
    
    // Rule 7: Check close return value
    if (fclose(file) != 0) {
        fprintf(stderr, "Failed to close file: %s\n", filename);
        return -3;
    }
    
    return 0;  // Success
}

// Rule 8 COMPLIANT: Simple preprocessor usage
#define MAX(a, b) ((a) > (b) ? (a) : (b))
#define MIN(a, b) ((a) < (b) ? (a) : (b))
#define CLAMP(val, min_val, max_val) MIN(MAX(val, min_val), max_val)

// Rule 8 COMPLIANT: Replace complex macro with inline function
static inline void log_processing_step(int step, int value) {
    if (step >= 1 && step <= 3) {
        printf("Step %d: Value = %d\n", step, value);
    }
}

// Rule 9 COMPLIANT: Single level pointers only, no function pointers
void safe_pointer_usage(char* string_buffer) {
    assert(string_buffer != NULL);
    
    // Single level indirection only
    int len = strlen(string_buffer);
    
    // Array indexing instead of pointer arithmetic
    for (int i = 0; i < len && i < MAX_BUFFER_SIZE - 1; i++) {
        if (string_buffer[i] == ' ') {
            string_buffer[i] = '_';  // Replace spaces with underscores
        }
    }
}

// Rule 9 COMPLIANT: Avoid function pointers, use switch instead
typedef enum {
    OPERATION_ADD,
    OPERATION_SUBTRACT,
    OPERATION_MULTIPLY
} operation_type_t;

int perform_operation(int a, int b, operation_type_t op) {
    assert(a >= 0 && a <= 1000);
    assert(b >= 0 && b <= 1000);
    
    switch (op) {
        case OPERATION_ADD:
            return a + b;
        case OPERATION_SUBTRACT:
            return a - b;
        case OPERATION_MULTIPLY:
            assert(a <= (INT_MAX / b));  // Overflow check
            return a * b;
        default:
            assert(0);  // Invalid operation
            return 0;
    }
}

// Rule 10 COMPLIANT: Warning-free code
int warning_free_function(int input) {
    assert(input >= 0);
    
    char buffer[20];
    int result = input * 2;
    
    // Proper format string
    snprintf(buffer, sizeof(buffer), "Result: %d", result);
    
    // Use all declared variables
    printf("%s\n", buffer);
    
    // Correct comparison (not assignment)
    if (result == 10) {
        printf("Special case detected\n");
    }
    
    return result;  // Consistent return type
}

// Compliant main function
int main(void) {
    // Initialize system first (Rule 3)
    system_initialization();
    
    // Rule 1: No recursion - use iterative factorial
    int fact = safe_factorial(5);
    printf("Factorial of 5: %d\n", fact);
    
    // Rule 4: Use smaller, focused functions
    ProcessingParams params = {10, 5, "test", 2.5};
    int processing_result = safe_processing_function(&params);
    
    // Rule 5 & 7: Check return values and validate
    if (processing_result >= 0) {
        printf("Processing successful: %d\n", processing_result);
    } else {
        printf("Processing failed\n");
        return 1;
    }
    
    // Rule 3: Use pre-allocated buffers only
    process_runtime_request("Sample runtime data");
    
    // Rule 5: Safe array operations with assertions
    int test_array[] = {1, 2, 3, 4, 5};
    safe_array_operation(test_array, 5, 3);
    
    // Rule 7: Check file operations
    int file_result = safe_file_operation("test.txt");
    if (file_result != 0) {
        printf("File operation failed with code: %d\n", file_result);
    }
    
    // Rule 8: Use simple macros
    int max_val = MAX(10, 20);
    printf("Maximum value: %d\n", max_val);
    
    // Rule 9: Safe pointer usage
    char test_string[] = "Hello World";
    safe_pointer_usage(test_string);
    printf("Modified string: %s\n", test_string);
    
    // Rule 9: Switch instead of function pointers
    int math_result = perform_operation(15, 3, OPERATION_MULTIPLY);
    printf("Math result: %d\n", math_result);
    
    // Rule 10: Warning-free code
    warning_free_function(5);
    
    return 0;
}