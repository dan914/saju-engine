# 🔍 Comprehensive Codebase Audit Prompt

Use this prompt with Claude or another LLM code analysis tool to perform a deep audit of the Saju engine codebase.

---

## Audit Prompt

```
You are conducting a comprehensive code quality and integrity audit for a Korean Four Pillars (Saju) fortune-telling engine built as a microservices architecture.

SCAN ALL FILES in the following directories:
- services/pillars-service/app/core/
- services/analysis-service/app/core/
- services/astro-service/app/core/
- services/tz-time-service/app/core/
- scripts/

For EACH Python file, identify and report:

## 1. HARDCODED DATA & MAGIC VALUES

Find all instances of:
- Hardcoded dates/times (e.g., datetime(1992, 7, 15, 23, 40))
- Hardcoded test data used in production code
- Magic numbers without explanation (e.g., mysterious offsets, thresholds, scores)
- Hardcoded user data (names, birth dates, locations)
- Hardcoded API keys, credentials, secrets
- Hardcoded file paths (absolute paths, /Users/..., /home/...)
- Hardcoded configuration that should be in config files

For each finding, report:
- File path and line number
- Code snippet
- Context (what function/class)
- Risk level (CRITICAL/HIGH/MEDIUM/LOW)
- Impact if this runs in production
- Recommended fix

## 2. STUBS & PLACEHOLDER CODE

Find all instances of:
- Functions that return hardcoded values instead of real calculations
- Classes with pass or ... as implementation
- TODO/FIXME/HACK comments
- Stub implementations marked with "stub", "placeholder", "temporary"
- Functions that always return None, empty dict, or zero
- Raise NotImplementedError
- Placeholder strings like "TBD", "placeholder", "dummy"

For each finding, report:
- File path and line number
- Code snippet
- What functionality is missing
- Is this blocking any feature?
- Recommended action (implement vs delete)

## 3. ERROR-PRONE PATTERNS

Find all instances of:
- Bare except: clauses (catching all exceptions)
- Ignored exceptions (except: pass)
- Missing error handling on critical operations (file I/O, network, parsing)
- Assertions in production code (assert statements)
- Division without zero checks
- Array/dict access without bounds/key checking
- Type coercion that could fail (int(x) without try/except)
- Missing validation on user inputs
- SQL injection risks (if any database queries)
- Command injection risks (shell=True in subprocess)

For each finding, report:
- File path and line number
- Code snippet
- What could go wrong
- Risk level
- Recommended fix

## 4. BLOCKING ISSUES & DEPENDENCIES

Find all instances of:
- Circular imports or import cycles
- Missing imports (imports that would fail)
- Cross-service imports (services importing from other services)
- Services importing from scripts/ folder
- Hacky import workarounds (importlib.util, sys.path manipulation)
- Functions that depend on missing data files
- Functions that call undefined/removed functions
- Dead code paths (unreachable code)
- Infinite loops or recursive calls without base case

For each finding, report:
- File path and line number
- Code snippet
- Why it's blocking
- Impact on system functionality
- Recommended fix

## 5. DATA INTEGRITY ISSUES

Find all instances of:
- Missing data validation
- Type mismatches (expecting str but receiving int)
- Inconsistent data formats (date formats, timezone handling)
- Missing null/None checks
- Unchecked array lengths before access
- String operations without encoding checks
- JSON parsing without error handling
- CSV/file reading without error handling
- Timezone-naive datetime objects in timezone-sensitive code

For each finding, report:
- File path and line number
- Code snippet
- What data integrity issue could occur
- Recommended fix

## 6. CONFIGURATION & POLICY ISSUES

Find all instances of:
- Policy files that are loaded but never used
- Policy files that are referenced but don't exist
- Versioned policies (v1, v2, v3) - which is actually active?
- Policy fallback chains that could fail
- Configuration loaded from wrong paths
- Environment variables without defaults
- Missing required configuration
- Conflicting configuration values

For each finding, report:
- File path and line number
- Policy/config file involved
- What's wrong
- Is it blocking functionality?
- Recommended fix

## 7. PERFORMANCE & RESOURCE ISSUES

Find all instances of:
- Files loaded on every request instead of once at startup
- Large JSON/CSV files loaded synchronously
- Inefficient loops (O(n²) or worse where avoidable)
- Memory leaks (objects never released)
- Unbounded lists/dicts that could grow indefinitely
- Synchronous I/O in async contexts
- Missing caching where beneficial

For each finding, report:
- File path and line number
- Code snippet
- Performance impact
- Recommended optimization

## 8. ARCHITECTURAL SMELLS

Find all instances of:
- God classes (classes doing too many things)
- Duplicate code (same logic in multiple places)
- Tight coupling between services
- Missing abstractions (repetitive patterns)
- Inconsistent naming conventions
- Missing docstrings on public APIs
- Overly complex functions (>50 lines, deeply nested)

For each finding, report:
- File path and line number
- Code snippet
- What's architecturally wrong
- Refactoring suggestion

## OUTPUT FORMAT

Structure your report as:

# CODEBASE AUDIT REPORT

## EXECUTIVE SUMMARY
- Total files scanned: X
- Critical issues: X
- High priority issues: X
- Medium priority issues: X
- Low priority issues: X
- Code quality grade: A/B/C/D/F

## CRITICAL ISSUES (Fix Immediately)
[List all CRITICAL findings with full details]

## HIGH PRIORITY ISSUES (Fix Before Production)
[List all HIGH findings with full details]

## MEDIUM PRIORITY ISSUES (Technical Debt)
[List all MEDIUM findings with full details]

## LOW PRIORITY ISSUES (Nice to Have)
[List all LOW findings with full details]

## RECOMMENDATIONS
1. [Prioritized action items]
2. [What to fix first]
3. [What can be deferred]

## FILES BY RISK LEVEL

### High Risk Files (need immediate attention)
[List files with most critical issues]

### Medium Risk Files
[List files with technical debt]

### Low Risk Files
[List clean files or minor issues]

---

BE THOROUGH. BE SPECIFIC. PROVIDE LINE NUMBERS AND CODE SNIPPETS.
Focus on ACTIONABLE findings that have REAL IMPACT.
Prioritize issues that could cause production failures.
```

---

## How to Use This Prompt

### Option 1: Use with Claude Code (current session)
1. Copy the prompt above
2. Paste into Claude Code and add: "Scan the codebase at /Users/yujumyeong/coding/ projects/사주/"
3. Let it run for comprehensive analysis

### Option 2: Use with Claude Sonnet 3.5 (web/API)
1. Upload key Python files from services/
2. Paste the prompt
3. Iterate through all services

### Option 3: Use with specialized tools
1. SonarQube, Pylint, Bandit for automated scanning
2. Use this prompt to guide manual review
3. Combine automated + manual findings

---

## Expected Output

A comprehensive report identifying:
- 🔴 **Critical blockers** (hardcoded test data in production, circular imports)
- 🟠 **High priority issues** (missing error handling, data validation)
- 🟡 **Medium priority tech debt** (code duplication, stubs)
- 🟢 **Low priority improvements** (documentation, style)

---

## Follow-Up Actions

After receiving the audit report:

1. **Triage**: Categorize findings by severity
2. **Plan**: Create fix tasks in priority order
3. **Fix**: Address critical issues first
4. **Test**: Verify fixes don't break existing functionality
5. **Document**: Update documentation with findings
6. **Prevent**: Add linters/tests to catch similar issues

---

## Related Documents

- `ENGINE_USAGE_AUDIT.md` - Engine inventory and orphaned code analysis
- `IMPLEMENTED_ENGINES_AND_FEATURES.md` - Feature completeness status
- Test files in `services/*/tests/` - Existing test coverage

---

**Generated**: 2025-10-07
**Purpose**: Systematic code quality audit
**Scope**: All production and script code
**Focus**: Hardcoded data, stubs, errors, blocking issues
