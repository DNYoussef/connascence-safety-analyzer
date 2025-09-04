#  Connascence Analysis Report

**Status:** 3899 critical issues found | **Policy:** `default` | **Duration:** 11938ms

## [METRICS] Summary
**By Severity:**  **3899** critical |  **4997** high |  **32034** medium |  **5669** low
**Most Common:** **35748** CoM | **5669** CoT | **3265** CoA
**Files Affected:** 427/473

## [SEARCH] Top Issues
-  **CoA** in `cohesion_analyzer.py:278` - God Object: class 'StatisticalGodObjectDetector' has 13 methods and ~301 lines
  > [TIP] Split into smaller, focused classes following Single Responsibility Principle
-  **CoA** in `grammar_enhanced_analyzer.py:124` - God Object: class 'GrammarEnhancedAnalyzer' has 14 methods and ~350 lines
  > [TIP] Split into smaller, focused classes following Single Responsibility Principle
-  **CoA** in `magic_literal_analyzer.py:119` - God Object: class 'MagicLiteralAnalyzer' has 13 methods and ~342 lines
  > [TIP] Split into smaller, focused classes following Single Responsibility Principle
-  **CoA** in `mcp_integration.py:16` - God Object: class 'GrammarEnhancedMCPExtension' has 8 methods and ~549 lines
  > [TIP] Split into smaller, focused classes following Single Responsibility Principle
-  **CoA** in `connascence.py:56` - God Object: class 'ConnascenceCLI' has 11 methods and ~490 lines
  > [TIP] Split into smaller, focused classes following Single Responsibility Principle
-  **CoA** in `charts.py:13` - God Object: class 'ChartGenerator' has 13 methods and ~547 lines
  > [TIP] Split into smaller, focused classes following Single Responsibility Principle
-  **CoA** in `ci_integration.py:23` - God Object: class 'CIDashboard' has 15 methods and ~428 lines
  > [TIP] Split into smaller, focused classes following Single Responsibility Principle
-  **CoA** in `metrics.py:16` - God Object: class 'DashboardMetrics' has 14 methods and ~424 lines
  > [TIP] Split into smaller, focused classes following Single Responsibility Principle
-  **CoA** in `ast_safe_refactoring.py:102` - God Object: class 'ASTSafeRefactoring' has 22 methods and ~560 lines
  > [TIP] Split into smaller, focused classes following Single Responsibility Principle
-  **CoA** in `constrained_generator.py:67` - God Object: class 'ConstrainedGenerator' has 19 methods and ~374 lines
  > [TIP] Split into smaller, focused classes following Single Responsibility Principle

_...and 46589 more issues_

## [FOLDER] Files Needing Attention
- **`test_schedules.py`** - 1510 issues (3 critical | 320 high | 1069 medium | 118 low)
- **`test_canvas.py`** - 1419 issues (308 critical | 225 high | 697 medium | 189 low)
- **`test_canvas.py`** - 1028 issues (4 critical | 155 high | 678 medium | 191 low)
- **`test_app.py`** - 900 issues (153 critical | 118 high | 470 medium | 159 low)
- **`test_base.py`** - 798 issues (86 critical | 96 high | 485 medium | 131 low)

_...and 422 more files_

## [TIP] Recommendations
-  **Extract Magic Literals**: Consider creating a constants module for the numerous magic numbers and strings found.
- [CHECKLIST] **Use Keyword Arguments**: Functions with many positional parameters are hard to maintain. Consider using keyword arguments or data classes.
- [PROGRESS] **Eliminate Duplication**: Similar algorithms detected. Extract common logic into shared functions or modules.

---
_Analysis completed in 11938ms
analyzing 473 files_

**What is Connascence?** Connascence is a software engineering metric that measures the strength of coupling between components. Lower connascence leads to more maintainable code.

 [Learn More](https://connascence.io) | [TECH] [Connascence Analyzer](https://github.com/connascence/connascence-analyzer)