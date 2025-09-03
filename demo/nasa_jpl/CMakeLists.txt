# NASA/JPL Power of Ten Compliant Build Configuration
# Demonstrates proper compiler flags and build system integration

cmake_minimum_required(VERSION 3.16)
project(NASA_JPL_Demo VERSION 1.0.0 LANGUAGES C)

# Set C standard for consistency
set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_C_EXTENSIONS OFF)

# NASA/JPL Rule 10: Compiler warnings as errors
# Enable comprehensive warning detection and treat as errors
set(NASA_WARNING_FLAGS
    -Wall                    # Enable most warning messages
    -Wextra                  # Enable extra warning messages  
    -Werror                  # Treat warnings as errors
    -Wpedantic               # Pedantic ISO C compliance
    -Wstrict-prototypes      # Warn about missing prototypes
    -Wmissing-declarations   # Warn about missing declarations
    -Wformat=2               # Check printf/scanf format strings
    -Wformat-security        # Warn about security issues in format
    -Wnull-dereference       # Warn about null pointer dereferences
    -Wstack-protector        # Warn when stack protection is used
    -Wtrampolines            # Warn about trampolines for nested functions
    -Walloca                 # Warn about alloca usage
    -Wvla                    # Warn about variable length arrays
    -Warray-bounds=2         # Warn about array bounds violations
    -Wimplicit-fallthrough=3 # Warn about implicit switch fallthrough
    -Wshift-overflow=2       # Warn about shift overflow
    -Wcast-qual              # Warn about casts that remove qualifiers
    -Wcast-align=strict      # Warn about casts that increase alignment
    -Wwrite-strings          # Warn when string literals are written to
    -Wconversion             # Warn about type conversions
    -Wdangling-else          # Warn about ambiguous else statements
    -Wdate-time              # Warn when __DATE__ or __TIME__ is used
    -Wempty-body             # Warn about empty body in if/else statements
    -Wignored-qualifiers     # Warn when type qualifiers are ignored
    -Wsign-conversion        # Warn about sign conversions
    -Wfloat-equal            # Warn about floating point equality comparisons
    -Wpointer-arith          # Warn about pointer arithmetic
    -Wtype-limits            # Warn when comparison is always true/false
    -Wundef                  # Warn when undefined identifier is used in #if
    -Wshadow                 # Warn when variable shadows another variable
    -Wstrict-overflow=5      # Warn about optimizations based on strict overflow
    -Wswitch-default         # Warn when switch has no default case
    -Wswitch-enum            # Warn about missing enum cases in switch
    -Wunreachable-code       # Warn about unreachable code
    -Winline                 # Warn when inline functions cannot be inlined
)

# Additional NASA-specific flags
set(NASA_SAFETY_FLAGS
    -fstack-protector-strong # Enable stack protection
    -fno-omit-frame-pointer  # Keep frame pointers for debugging
    -fno-common              # Place uninitialized globals in BSS
    -fstrict-aliasing        # Enable strict aliasing optimizations
    -Wstrict-aliasing=3      # Warn about strict aliasing violations
)

# Optimization flags appropriate for safety-critical code
set(NASA_OPTIMIZATION_FLAGS
    -O2                      # Moderate optimization for production
    -fno-delete-null-pointer-checks  # Don't optimize null pointer checks
    -fwrapv                  # Define signed integer overflow behavior
)

# Debug information for analysis tools
set(NASA_DEBUG_FLAGS
    -g3                      # Maximum debug information
    -gdwarf-4               # Use DWARF version 4 debug format
    -fno-eliminate-unused-debug-types  # Keep all debug type info
)

# Combine all NASA-compliant flags
set(NASA_COMPILE_FLAGS 
    ${NASA_WARNING_FLAGS}
    ${NASA_SAFETY_FLAGS}
    ${NASA_OPTIMIZATION_FLAGS}
    ${NASA_DEBUG_FLAGS}
)

# Apply NASA flags to all C compilation
add_compile_options(${NASA_COMPILE_FLAGS})

# NASA Rule 10: Static analysis integration
# Enable additional static analysis tools
option(ENABLE_STATIC_ANALYSIS "Enable static analysis tools" ON)

if(ENABLE_STATIC_ANALYSIS)
    # Enable clang-tidy for additional checks
    set(CMAKE_C_CLANG_TIDY 
        clang-tidy
        -checks=-*,
        readability-*,
        modernize-*,
        clang-analyzer-*,
        bugprone-*,
        performance-*,
        portability-*,
        cert-*
    )
    
    # Enable cppcheck
    find_program(CPPCHECK cppcheck)
    if(CPPCHECK)
        set(CMAKE_C_CPPCHECK ${CPPCHECK}
            --enable=all
            --inconclusive
            --std=c11
            --suppress=missingIncludeSystem
            --error-exitcode=1
        )
    endif()
endif()

# Define executables
add_executable(violations_demo sample_violations.c)
add_executable(compliant_demo sample_compliant.c)

# NASA-compliant linking flags
set(NASA_LINK_FLAGS
    -Wl,--warn-common         # Warn about common symbols
    -Wl,--fatal-warnings      # Treat linker warnings as errors
    -Wl,-z,relro             # Read-only relocations
    -Wl,-z,now               # Immediate binding
    -Wl,--no-undefined       # No undefined symbols
)

target_link_options(violations_demo PRIVATE ${NASA_LINK_FLAGS})
target_link_options(compliant_demo PRIVATE ${NASA_LINK_FLAGS})

# Custom targets for NASA compliance checking
find_program(CONNASCENCE_CLI connascence)

if(CONNASCENCE_CLI)
    # NASA compliance analysis
    add_custom_target(nasa-compliance-check
        COMMAND ${CONNASCENCE_CLI} analyze ${CMAKE_CURRENT_SOURCE_DIR} 
                --profile nasa_jpl_pot10 
                --output json 
                --output-file ${CMAKE_BINARY_DIR}/nasa_compliance.json
        WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}
        COMMENT "Running NASA/JPL Power of Ten compliance analysis"
    )
    
    # Build flags verification
    add_custom_target(verify-build-flags
        COMMAND ${CONNASCENCE_CLI} verify-build-flags ${CMAKE_CURRENT_SOURCE_DIR}
                --profile nasa_jpl_pot10
                --cmake-file ${CMAKE_CURRENT_SOURCE_DIR}/CMakeLists.txt
        WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}
        COMMENT "Verifying NASA-compliant compiler flags"
    )
    
    # Quality scorecard generation
    add_custom_target(quality-scorecard
        COMMAND ${CONNASCENCE_CLI} scorecard ${CMAKE_CURRENT_SOURCE_DIR}
                --profile nasa_jpl_pot10
                --output html
                --output-file ${CMAKE_BINARY_DIR}/quality_scorecard.html
        WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}
        COMMENT "Generating code quality scorecard"
    )
    
    # Comprehensive NASA analysis
    add_custom_target(nasa-full-analysis
        DEPENDS nasa-compliance-check verify-build-flags quality-scorecard
        COMMENT "Running comprehensive NASA/JPL analysis"
    )
else()
    message(WARNING "Connascence CLI not found - NASA compliance targets disabled")
    message(STATUS "Install connascence analyzer to enable NASA compliance checking")
endif()

# Integration with CTest for automated testing
enable_testing()

# Test that compliant code passes NASA analysis
if(CONNASCENCE_CLI)
    add_test(NAME nasa_compliant_analysis
        COMMAND ${CONNASCENCE_CLI} analyze sample_compliant.c 
                --profile nasa_jpl_pot10 
                --exit-code-on-violations
        WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
    )
    
    # Test that violations are properly detected
    add_test(NAME nasa_violations_detected  
        COMMAND ${CONNASCENCE_CLI} analyze sample_violations.c 
                --profile nasa_jpl_pot10 
                --expect-violations
        WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
    )
    
    # Test build flags compliance
    add_test(NAME build_flags_compliance
        COMMAND ${CONNASCENCE_CLI} verify-build-flags .
                --profile nasa_jpl_pot10
                --cmake-file CMakeLists.txt
        WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
    )
endif()

# Documentation generation
find_program(DOXYGEN doxygen)
if(DOXYGEN)
    # NASA documentation standards
    configure_file(${CMAKE_CURRENT_SOURCE_DIR}/Doxyfile.in 
                   ${CMAKE_CURRENT_BINARY_DIR}/Doxyfile @ONLY)
    
    add_custom_target(nasa-docs
        COMMAND ${DOXYGEN} ${CMAKE_CURRENT_BINARY_DIR}/Doxyfile
        WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}
        COMMENT "Generating NASA-compliant documentation"
    )
endif()

# IDE integration helpers
set_property(GLOBAL PROPERTY USE_FOLDERS ON)
set_target_properties(violations_demo compliant_demo PROPERTIES FOLDER "Demo")

# Export compilation database for IDE integration
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# Summary of NASA compliance features
message(STATUS "NASA/JPL Power of Ten Compliance Configuration:")
message(STATUS "  - Compiler warnings as errors: ENABLED")
message(STATUS "  - Stack protection: ENABLED") 
message(STATUS "  - Static analysis: ${ENABLE_STATIC_ANALYSIS}")
message(STATUS "  - Debug information: ENABLED")
message(STATUS "  - Compliance checking: ${CONNASCENCE_CLI}")
message(STATUS "  - Test integration: ENABLED")

# Build type specific configurations
if(CMAKE_BUILD_TYPE STREQUAL "Debug")
    message(STATUS "  - Build type: DEBUG (additional safety checks enabled)")
    target_compile_definitions(violations_demo PRIVATE DEBUG_BUILD=1)
    target_compile_definitions(compliant_demo PRIVATE DEBUG_BUILD=1)
    
    # Additional debug flags for NASA compliance
    target_compile_options(violations_demo PRIVATE -fsanitize=address -fsanitize=undefined)
    target_compile_options(compliant_demo PRIVATE -fsanitize=address -fsanitize=undefined)
    target_link_options(violations_demo PRIVATE -fsanitize=address -fsanitize=undefined)
    target_link_options(compliant_demo PRIVATE -fsanitize=address -fsanitize=undefined)
    
elseif(CMAKE_BUILD_TYPE STREQUAL "Release")
    message(STATUS "  - Build type: RELEASE (production-ready NASA compliance)")
    target_compile_definitions(violations_demo PRIVATE NDEBUG=1)
    target_compile_definitions(compliant_demo PRIVATE NDEBUG=1)
    
    # Production hardening flags
    target_compile_options(violations_demo PRIVATE -D_FORTIFY_SOURCE=2)
    target_compile_options(compliant_demo PRIVATE -D_FORTIFY_SOURCE=2)
endif()

# Installation for enterprise deployment
install(TARGETS compliant_demo
    RUNTIME DESTINATION bin
    COMPONENT nasa_demos
)

install(FILES README.md
    DESTINATION share/doc/nasa-jpl-demo
    COMPONENT documentation
)

# CPack configuration for distribution
set(CPACK_PACKAGE_NAME "NASA-JPL-Compliance-Demo")
set(CPACK_PACKAGE_VERSION "${PROJECT_VERSION}")
set(CPACK_PACKAGE_DESCRIPTION_SUMMARY "NASA/JPL Power of Ten Rules Compliance Demo")
set(CPACK_PACKAGE_VENDOR "Connascence Analysis System")
set(CPACK_RESOURCE_FILE_LICENSE "${CMAKE_CURRENT_SOURCE_DIR}/LICENSE")
set(CPACK_RESOURCE_FILE_README "${CMAKE_CURRENT_SOURCE_DIR}/README.md")

include(CPack)