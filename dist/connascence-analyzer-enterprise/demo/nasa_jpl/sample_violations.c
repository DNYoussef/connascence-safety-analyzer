/**
 * NASA/JPL Power of Ten Rules Violation Examples
 * 
 * This file contains deliberate violations of NASA/JPL coding standards
 * to demonstrate the analysis system's detection capabilities.
 * 
 * IMPORTANT: This is demonstration code only - never use in production!
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// VIOLATION: Rule 6 - Global variables (should minimize)
int global_counter = 0;
char global_buffer[1024];
static int system_state = 0;
int debug_flags = 0xFF;
float calculation_cache[100];

// VIOLATION: Rule 1 - Recursion (factorial function)
int factorial(int n) {
    if (n <= 1) return 1;
    return n * factorial(n - 1);  // Direct recursion forbidden
}

// VIOLATION: Rule 1 - Function contains goto statements
int process_data(char* data, int len) {
    int i = 0;
    int errors = 0;
    
    start_processing:  // Label for goto
        if (i >= len) goto end_processing;
        
        if (data[i] == '\0') {
            errors++;
            goto error_handling;
        }
        
        if (data[i] < 32) {
            goto skip_char;  // Another goto
        }
        
        // Process valid character
        global_buffer[global_counter++] = data[i];
        
        skip_char:
            i++;
            goto start_processing;  // Loop using goto
        
    error_handling:
        printf("Error at position %d\n", i);
        i++;
        goto start_processing;
        
    end_processing:
        return errors;
}

// VIOLATION: Rule 4 - Function too long (>60 lines)
int massive_function(int param1, int param2, char* param3, float param4, 
                    int param5, int param6, char* param7) {
    // This function violates multiple rules:
    // - Too many parameters (Rule 7 - parameter validation)
    // - Too many lines (Rule 4)
    // - High complexity
    
    int local_var1, local_var2, local_var3;
    int result = 0;
    int temp_array[500];  // Large stack allocation
    
    // No parameter validation (Rule 7 violation)
    
    for (int i = 0; i < param1; i++) {
        for (int j = 0; j < param2; j++) {
            for (int k = 0; k < param5; k++) {
                if (i > 10 && j < 5) {
                    if (k % 2 == 0) {
                        if (param4 > 3.14) {
                            temp_array[i*j + k] = param6 * 42;
                        } else {
                            temp_array[i*j + k] = param6 * 24;
                        }
                    } else {
                        if (param3[k % strlen(param3)] == 'x') {
                            temp_array[i*j + k] = 100;
                        } else {
                            temp_array[i*j + k] = 200;
                        }
                    }
                } else {
                    if (param7 && strlen(param7) > k) {
                        temp_array[i*j + k] = param7[k];
                    } else {
                        temp_array[i*j + k] = 0;
                    }
                }
                
                // More nested conditions (complexity++)
                if (temp_array[i*j + k] > 150) {
                    result += temp_array[i*j + k] * 2;
                } else if (temp_array[i*j + k] > 75) {
                    result += temp_array[i*j + k] + 10;
                } else {
                    result += temp_array[i*j + k] / 2;
                }
            }
        }
    }
    
    // More processing to make function longer...
    for (int m = 0; m < 20; m++) {
        global_counter += m;
        if (global_counter > 1000) global_counter = 0;
    }
    
    // VIOLATION: Rule 7 - Not checking malloc return value
    char* dynamic_data = malloc(256);
    strcpy(dynamic_data, "test data");  // No null check!
    
    // VIOLATION: Rule 2 - Unbounded loop
    while (1) {
        if (system_state == 5) break;  // Infinite loop condition
        system_state++;
        if (system_state > 10) system_state = 0;
    }
    
    free(dynamic_data);  // At least we free it
    return result;
}

// VIOLATION: Rule 3 - Dynamic allocation after initialization
void runtime_allocation() {
    // This simulates allocation after system init
    static int init_complete = 1;
    
    if (init_complete) {
        // FORBIDDEN: malloc after initialization phase
        void* runtime_buffer = malloc(512);
        if (runtime_buffer) {
            memset(runtime_buffer, 0, 512);
            // Use buffer...
            free(runtime_buffer);
        }
    }
}

// VIOLATION: Rule 5 - Missing assertions and error handling
void unsafe_function(int* ptr, int size) {
    // No assertions or parameter validation
    // Should have: assert(ptr != NULL);
    // Should have: assert(size > 0 && size < MAX_SIZE);
    
    for (int i = 0; i < size; i++) {
        ptr[i] = i * 2;  // Could crash if ptr is NULL
    }
    
    // VIOLATION: Rule 7 - Not checking return values
    FILE* file = fopen("data.txt", "r");  // Return value not checked
    fprintf(file, "Writing data\n");      // Could crash if fopen failed
    fclose(file);
}

// VIOLATION: Rule 8 - Complex preprocessor usage
#define COMPLEX_MACRO(a, b, c) do { \
    if ((a) > (b)) { \
        for (int _i = 0; _i < (c); _i++) { \
            printf("Loop %d: %d\n", _i, (a) + (b)); \
        } \
    } else { \
        switch (c) { \
            case 1: printf("Case 1\n"); break; \
            case 2: printf("Case 2\n"); break; \
            default: printf("Default\n"); \
        } \
    } \
} while(0)

// VIOLATION: Rule 9 - Multiple levels of pointer indirection
void pointer_nightmare(int*** triple_ptr, char** string_array) {
    // Triple indirection violates rule 9
    ***triple_ptr = 42;
    
    // Function pointer (also rule 9 violation)
    void (*func_ptr)(int) = NULL;
    
    // Pointer arithmetic (rule 9)
    char* str = string_array[0];
    str += 10;  // Pointer arithmetic
    *(str + 5) = 'x';  // More pointer arithmetic
}

// VIOLATION: Rule 10 - Code that would generate warnings
void warning_generator() {
    int unused_variable;  // -Wunused-variable
    
    char buffer[10];
    strcpy(buffer, "This string is way too long");  // Buffer overflow
    
    int x = 5;
    if (x = 3) {  // Assignment in condition (-Wparentheses)
        printf("Condition met\n");
    }
    
    return 42;  // -Wreturn-type (void function returning value)
}

// Main function with violations
int main() {
    // Rule 1 violation: calling recursive function
    int fact = factorial(10);
    
    // Rule 3 violation: runtime allocation
    runtime_allocation();
    
    // Rule 4 violation: calling massive function
    massive_function(10, 20, "test", 3.14, 5, 6, "hello");
    
    // Rule 5 violation: calling unsafe function without validation
    int* null_ptr = NULL;
    unsafe_function(null_ptr, -5);  // Dangerous call
    
    // Rule 7 violation: ignoring return values
    process_data("test data", 9);  // Return value ignored
    
    // Rule 8 violation: using complex macro
    COMPLEX_MACRO(5, 3, 2);
    
    // Rule 9 violation: complex pointer usage
    int value = 10;
    int* ptr1 = &value;
    int** ptr2 = &ptr1;
    int*** ptr3 = &ptr2;
    pointer_nightmare(&ptr3, NULL);
    
    return 0;  // At least this follows convention!
}