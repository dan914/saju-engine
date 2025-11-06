# Codebase Audit Prompt v2.0 - Comprehensive Technical Review

**Purpose:** Deep scan of the entire codebase to identify technical issues, stubs, hardcoded data, errors, and improvement opportunities.

**Context:** This application is in **early development**, nowhere near production deployment. Security concerns are **not a priority** at this stage. Focus entirely on **technical correctness**, **completeness**, and **maintainability**.

---

## Your Role

You are a **team of 5 senior software engineers** conducting a comprehensive code audit. Each engineer has a specific focus area, but all collaborate to produce a unified report.

### Team Composition:

1. **Backend Architect** - System design, service boundaries, data flow, architecture patterns
2. **Code Quality Engineer** - Stubs, TODOs, hardcoded values, dead code, duplication
3. **Python Expert** - Type hints, error handling, Pydantic models, imports, pythonic patterns
4. **Data/Policy Engineer** - Policy files, JSON schemas, data validation, consistency
5. **Testing Lead** - Test coverage, missing tests, fixture issues, test quality

---

## Project Context

**Repository:** Korean Four Pillars (사주) fortune-telling application
**Architecture:** Microservices (pillars-service, analysis-service, common package)
**Stack:** Python 3.12, FastAPI, Pydantic, pytest
**Key Docs:**
- `/claude.md` - Project structure and implementation status
- `/STUB_REPLACEMENT_COMPLETE.md` - Recent stub replacement work
- `/policy/` - Policy files (RFC-8785 signed)
- `/schema/` - JSON schemas

**Note:** The project uses policy-driven engines where JSON policy files are the source of truth, and code implements the logic defined in policies.

---

## Audit Scope

Scan the **entire codebase** across all services:

### Services to Audit:
- `services/common/` - Shared common package
- `services/pillars-service/` - Four pillars calculation
- `services/analysis-service/` - Core analysis engines (19 engines)
- `services/api-gateway/` - API gateway (skeleton only?)
- `services/llm-polish/` - LLM polishing service (skeleton only?)
- `services/llm-checker/` - LLM guard service (skeleton only?)

### Supporting Files:
- `scripts/` - Calculation scripts
- `policy/` - Policy JSON files
- `schema/` - JSON Schema files
- `tests/` - Root-level tests
- `.github/workflows/` - CI/CD configurations

---

## What to Look For

### CRITICAL Issues (🔴)

**Stubs & Placeholders:**
- [ ] Classes/functions that return dummy data (0, "unknown", empty lists/dicts)
- [ ] Methods with `pass` or `...` as body
- [ ] `raise NotImplementedError` without clear reason
- [ ] Placeholder comments like "TODO: implement later"

**Hardcoded Values:**
- [ ] Dates/times hardcoded in calculations (e.g., `datetime(1992, 7, 15)`)
- [ ] Magic numbers without explanation (e.g., `score * 0.73`)
- [ ] Paths hardcoded instead of using config (e.g., `/Users/specific/path`)
- [ ] API URLs/endpoints hardcoded in code

**Path Resolution Bugs:**
- [ ] Incorrect `parents[N]` usage (wrong directory traversal)
- [ ] Paths that go outside the repository root
- [ ] Relative paths that break when run from different directories
- [ ] Missing path existence checks before reading files

**Import Issues:**
- [ ] Circular imports
- [ ] Missing dependencies (imports that will fail)
- [ ] Incorrect sys.path.insert() paths
- [ ] Unused imports cluttering files

**Data Consistency:**
- [ ] Type mismatches between services (e.g., str vs int)
- [ ] Missing required fields in responses
- [ ] Inconsistent naming (snake_case vs camelCase within same service)
- [ ] Null/None handling missing

---

### HIGH Priority Issues (🟠)

**Error Handling:**
- [ ] Missing try/except blocks around file I/O
- [ ] Bare `except:` clauses (should specify exception type)
- [ ] Functions that can raise but don't document it
- [ ] No validation before processing external data

**Testing Gaps:**
- [ ] Critical functions with no tests
- [ ] Tests that don't actually assert anything
- [ ] Fixture data that's outdated or incorrect
- [ ] Skipped tests without explanation

**Policy/Schema Mismatches:**
- [ ] Code that doesn't match policy file structure
- [ ] Policy files without corresponding schemas
- [ ] Schemas that don't validate actual policy files
- [ ] Missing RFC-8785 signatures on policy files

**Code Duplication:**
- [ ] Same logic implemented in multiple services
- [ ] Copy-pasted functions with minor variations
- [ ] Repeated validation logic
- [ ] Duplicated constants

---

### MEDIUM Priority Issues (🟡)

**Code Quality:**
- [ ] Missing type hints (Python 3.12 should have full typing)
- [ ] Missing docstrings on public functions/classes
- [ ] Overly complex functions (>50 lines, multiple responsibilities)
- [ ] Poor variable names (x, tmp, data1, etc.)

**Configuration Issues:**
- [ ] Environment variables not documented
- [ ] Default values that don't make sense for dev
- [ ] Config spread across multiple files inconsistently
- [ ] No validation of config values

**Dead Code:**
- [ ] Commented-out code blocks (>10 lines)
- [ ] Unused functions/classes (grep to verify)
- [ ] Imports for code that was removed
- [ ] Old backup files (*.backup, *.old)

**Documentation Drift:**
- [ ] README claims features that don't exist
- [ ] Docstrings that don't match actual behavior
- [ ] Comments that contradict the code
- [ ] Outdated examples in docs

---

### LOW Priority Issues (🟢)

**Optimization Opportunities:**
- [ ] Repeated calculations that could be cached
- [ ] Loading large files multiple times
- [ ] N+1 query patterns
- [ ] Unnecessary deep copies

**Modern Python:**
- [ ] Using old string formatting (% or .format()) instead of f-strings
- [ ] Not using dataclasses where appropriate
- [ ] Missing use of match/case (Python 3.10+)
- [ ] Could use walrus operator for clarity

**Naming/Style:**
- [ ] Inconsistent naming conventions within same module
- [ ] Acronyms not defined in comments
- [ ] Korean/English mixing inconsistently
- [ ] Function names don't describe what they do

---

## Specific Things to Check

### 1. Stub Classes (🔴 CRITICAL)

Search for patterns like:
```python
class SomeCalculator:
    def calculate(self):
        return 0  # ❌ STUB

    def process(self):
        return {"result": "unknown"}  # ❌ STUB

    def get_data(self):
        return []  # ❌ STUB
```

**Context:** We just finished replacing stubs in `evidence.py`, but there may be more throughout the codebase.

---

### 2. Hardcoded Dates/Times (🔴 CRITICAL)

Search for:
```python
datetime(1992, 7, 15, 23, 40)  # ❌ Hardcoded for a specific person
birth_dt = "2000-09-14T10:00:00"  # ❌ Testing data in production code
```

**Context:** We recently fixed `engine.py:430` where a birth_dt was hardcoded. There may be more.

---

### 3. Path Traversal (🔴 CRITICAL)

Search for `parents[` and verify each one:
```python
# ❌ WRONG - goes outside repo
Path(__file__).resolve().parents[6] / "data"

# ❌ WRONG - goes outside repo
Path(__file__).resolve().parents[5] / "services"

# ✅ CORRECT - stays within repo
Path(__file__).resolve().parents[4] / "data"  # From services/X/app/core/file.py
```

**Context:** We fixed 7 instances of `parents[6]→parents[4]` and `parents[5]→parents[4]`. Make sure we got them all.

---

### 4. Missing Error Handling (🟠 HIGH)

Search for file operations without try/except:
```python
# ❌ BAD - will crash if file missing
with open("policy.json") as f:
    data = json.load(f)

# ✅ GOOD
try:
    with open("policy.json") as f:
        data = json.load(f)
except FileNotFoundError:
    logger.error(f"Policy file not found: {path}")
    raise
```

---

### 5. Skipped/Disabled Tests (🟠 HIGH)

Search for:
```python
@pytest.mark.skip(reason="...")  # Why skipped? Still relevant?
@pytest.mark.xfail  # Expected to fail - tech debt?
pytest.skip("...")  # Inside test - should be fixed or removed
```

Also check `.github/workflows/` for tests disabled via `--ignore` flags.

**Context:** We just re-enabled 8 test suites in `ci.yml`. Make sure no new ones got added.

---

### 6. Policy File Coverage (🟠 HIGH)

For each policy file in `policy/` and `saju_codex_batch_all_v2_6_signed/policies/`:
- [ ] Is there a corresponding JSON Schema in `schema/`?
- [ ] Is the schema referenced in the policy file?
- [ ] Is there code that loads and uses this policy?
- [ ] Are there tests that validate the policy?
- [ ] Does the policy have an RFC-8785 signature?

---

### 7. Service Skeletons (🟡 MEDIUM)

Check these services claimed to be "skeletons only":
- `services/api-gateway/` - Just FastAPI boilerplate?
- `services/llm-polish/` - Just imports and TODO?
- `services/llm-checker/` - Just structure, no logic?

Verify if they're truly empty or if there's hidden implementation.

---

### 8. Import Statements (🟡 MEDIUM)

For every `sys.path.insert()`:
- [ ] Is the path calculation correct?
- [ ] Is it really needed, or could we use proper package structure?
- [ ] Is it done consistently across the codebase?

For every `from X import Y`:
- [ ] Does X exist and is it installed?
- [ ] Is Y actually used in the file?

---

## Output Format

Produce a **detailed markdown report** with this structure:

```markdown
# Codebase Audit Report v2.0

**Date:** YYYY-MM-DD
**Audited By:** Backend Architect, Code Quality Engineer, Python Expert, Data/Policy Engineer, Testing Lead
**Total Files Scanned:** XXX
**Total Issues Found:** XXX

---

## Executive Summary

[3-5 paragraphs summarizing the overall health of the codebase]

**Key Findings:**
- X critical issues that block functionality
- Y high-priority technical debt items
- Z medium issues for code quality
- W low-priority optimizations

**Overall Health:** [Excellent / Good / Fair / Poor / Critical]

---

## Critical Issues (🔴)

### 1. [Issue Title] - File: path/to/file.py:LINE

**Severity:** CRITICAL
**Category:** [Stub / Hardcoded / Path Bug / Import / Data Consistency]
**Impact:** [What breaks / What data is wrong / What fails]

**Location:**
- File: `services/X/app/core/Y.py`
- Line: 123-145
- Function/Class: `ClassName.method_name()`

**Current Code:**
```python
# Show the problematic code with context
def broken_function():
    return 0  # ❌ STUB
```

**Issue:**
[Detailed explanation of why this is a problem]

**Evidence:**
- [Link to related test failure if any]
- [Link to GitHub issue if relevant]
- [Reference to documentation]

**Recommended Fix:**
```python
# Show what the code should look like
def fixed_function():
    # Real implementation here
    return calculate_real_value()
```

**Priority:** IMMEDIATE
**Effort:** [Small / Medium / Large / XL]
**Blocker:** [Yes/No - if yes, what does it block?]

---

[Repeat for all critical issues]

---

## High Priority Issues (🟠)

[Same structure as critical]

---

## Medium Priority Issues (🟡)

[Same structure, but can be more concise]

---

## Low Priority Issues (🟢)

[Brief list format acceptable here]

- File X:Y - Missing type hint on function Z
- File A:B - Could use f-string instead of .format()

---

## Statistics

### By Severity:
- 🔴 Critical: X issues
- 🟠 High: Y issues
- 🟡 Medium: Z issues
- 🟢 Low: W issues

### By Category:
- Stubs/Placeholders: X
- Hardcoded Values: Y
- Path Bugs: Z
- Error Handling: W
- Testing Gaps: V
- Code Quality: U
- Dead Code: T
- Other: S

### By Service:
- services/common/: X issues
- services/pillars-service/: Y issues
- services/analysis-service/: Z issues
- services/api-gateway/: W issues
- Other: V issues

---

## Detailed Findings

### Policy Files Audit

**Files Scanned:** XX policy files
**Issues Found:**

| Policy File | Schema | Code Usage | Tests | Signature | Status |
|-------------|--------|------------|-------|-----------|--------|
| strength_policy_v2.json | ✅ | ✅ | ✅ | ✅ | OK |
| relation_policy.json | ✅ | ✅ | ⚠️ | ✅ | Missing tests |
| unknown_policy.json | ❌ | ❌ | ❌ | ❌ | ORPHANED |

---

### Test Coverage Audit

**Test Files Scanned:** XX files
**Pass Rate:** YY% (ZZZ passed / WWW total)

**Missing Test Coverage:**
- services/X/Y.py - Function `foo()` has no tests
- services/A/B.py - Class `Bar` only has 1 test, needs more

**Problematic Tests:**
- test_X.py:45 - Skipped since 2024-XX-XX, reason unclear
- test_Y.py:78 - Always fails in CI but passes locally

---

## Recommendations

### Immediate Actions (This Week):
1. Fix all CRITICAL issues (estimated: X hours)
2. Add error handling to file I/O operations
3. Remove all stub classes or replace with real implementations
4. Fix hardcoded dates in calculation engines

### Short Term (This Month):
1. Improve test coverage for core engines
2. Add validation for all policy files
3. Clean up dead/commented code
4. Standardize import paths across services

### Long Term (Next Quarter):
1. Consider restructuring services to remove sys.path hacks
2. Add comprehensive integration tests
3. Document all policy files with schemas
4. Optimize repeated calculations

---

## Files That Need Immediate Attention

1. **services/analysis-service/app/core/engine.py**
   - 3 critical issues, 5 high priority
   - Most impactful file

2. **services/pillars-service/app/core/evidence.py**
   - Recently fixed but needs validation

3. **services/common/policy_loader.py**
   - Used everywhere, has 2 critical bugs

[Continue for top 10 files]

---

## Appendices

### A. All Stub Classes Found
[Complete list with locations]

### B. All Hardcoded Values Found
[Complete list with locations]

### C. All TODOs in Codebase
[Complete list with file:line]

### D. All Skipped Tests
[Complete list with reasons]

---

## Conclusion

[Final 2-3 paragraphs with overall assessment and next steps]
```

---

## Important Instructions

1. **Be Thorough:** Scan every `.py` file in the codebase. Don't skip any service or directory.

2. **Be Specific:** Every issue should have:
   - Exact file path and line number
   - Code snippet showing the problem
   - Clear explanation of why it's a problem
   - Suggested fix

3. **Prioritize Correctly:**
   - CRITICAL = Blocks functionality, returns wrong data, or causes crashes
   - HIGH = Technical debt that will cause problems soon
   - MEDIUM = Quality issues that make maintenance harder
   - LOW = Nice-to-haves and optimizations

4. **Verify Claims:**
   - If you find what looks like a stub, check if it's actually used
   - If you find hardcoded data, check if it's test data (acceptable) or production code (not acceptable)
   - If you find a TODO, check the git blame to see how old it is

5. **Context Matters:**
   - Code in `tests/` can have hardcoded values (that's fine)
   - Code in `scripts/` might be one-off utilities (less strict)
   - Code in `services/X/app/core/` must be production-quality

6. **Don't Report False Positives:**
   - Constants are okay (e.g., `DAYS_IN_WEEK = 7`)
   - Test fixtures are okay
   - Example data in docstrings is okay
   - Configuration defaults are okay if documented

7. **Cross-Reference:**
   - Check if issues you find are already documented in:
     - `/STATUS.md`
     - `/STUB_REPLACEMENT_COMPLETE.md`
     - GitHub issues
     - TODO comments with context

8. **Security is NOT a concern** for this audit:
   - Don't flag missing authentication (we know)
   - Don't flag exposed secrets in .env (it's gitignored)
   - Don't flag CORS wide-open (not deployed yet)
   - Focus only on **technical correctness** and **completeness**

---

## Tools/Commands to Help You

### Find all stubs:
```bash
# Search for common stub patterns
grep -r "return 0" --include="*.py" services/
grep -r 'return ""' --include="*.py" services/
grep -r "return \[\]" --include="*.py" services/
grep -r "return {}" --include="*.py" services/
grep -r "pass$" --include="*.py" services/
grep -r "NotImplementedError" --include="*.py" services/
```

### Find hardcoded dates:
```bash
grep -r "datetime(19" --include="*.py" services/
grep -r "datetime(20" --include="*.py" services/
```

### Find path traversal:
```bash
grep -r "parents\[" --include="*.py" services/
```

### Find TODOs:
```bash
grep -r "TODO" --include="*.py" services/
grep -r "FIXME" --include="*.py" services/
grep -r "XXX" --include="*.py" services/
```

### Find skipped tests:
```bash
grep -r "@pytest.mark.skip" --include="*.py" services/
grep -r "pytest.skip" --include="*.py" services/
```

---

## Success Criteria

A successful audit will:
- ✅ Scan every Python file in the repository
- ✅ Categorize issues by severity correctly
- ✅ Provide actionable fixes for critical issues
- ✅ Include file paths and line numbers for every issue
- ✅ Cross-reference with existing documentation
- ✅ Give realistic effort estimates
- ✅ Prioritize issues that block functionality over style issues
- ✅ Be detailed enough that a developer can immediately start fixing

---

## Ready? Begin the audit.

Start with the most critical services first:
1. `services/common/` (shared by all)
2. `services/analysis-service/` (19 engines, most complex)
3. `services/pillars-service/` (core calculations)
4. Then the rest

Take your time. Be thorough. Find everything.
