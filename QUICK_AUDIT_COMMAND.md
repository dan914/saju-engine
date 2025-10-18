# 🚀 Quick Audit Command

Run this immediately to find critical issues:

```bash
# Quick scan for hardcoded data
echo "=== HARDCODED DATES/TIMES ==="
grep -rn "datetime(" services/*/app/core/*.py | grep -E "[0-9]{4}, [0-9]"

echo ""
echo "=== HARDCODED TEST DATA ==="
grep -rn "test\|placeholder\|dummy\|stub" services/*/app/core/*.py | grep -v "# test"

echo ""
echo "=== TODO/FIXME/HACK ==="
grep -rn "TODO\|FIXME\|HACK\|XXX" services/*/app/core/*.py

echo ""
echo "=== BARE EXCEPT CLAUSES ==="
grep -rn "except:" services/*/app/core/*.py

echo ""
echo "=== HARDCODED PATHS ==="
grep -rn "/Users/\|/home/\|C:\\\\" services/*/app/core/*.py

echo ""
echo "=== MAGIC NUMBERS ==="
grep -rn "= [0-9]\+\(\.[0-9]\+\)\?" services/*/app/core/*.py | grep -v "= 0\|= 1\|= -1" | head -20

echo ""
echo "=== IMPORT FROM SCRIPTS ==="
grep -rn "from scripts\|import scripts" services/*/app/core/*.py

echo ""
echo "=== CROSS-SERVICE IMPORTS ==="
grep -rn "from.*service.*import\|import.*service" services/*/app/core/*.py

echo ""
echo "=== ALWAYS RETURNS NONE ==="
grep -rn "return None" services/*/app/core/*.py | head -20
```

## Or use grep patterns individually:

```bash
# Find all hardcoded datetimes
grep -rn "datetime(19\|datetime(20" services/*/app/core/

# Find placeholder/stub code
grep -rn "pass$\|NotImplementedError\|raise.*Stub" services/*/app/core/

# Find missing error handling
grep -rn "json.load\|open(\|csv.reader" services/*/app/core/ | grep -v "try:\|except"

# Find potential blocking imports
grep -rn "^from scripts\|^import scripts" services/

# Find hardcoded user data
grep -rn "1992.*7.*15\|seoul\|busan" services/*/app/core/ -i
```

## Critical Files to Check First

Based on ENGINE_USAGE_AUDIT.md findings:

1. **services/analysis-service/app/core/engine.py:430**
   - KNOWN ISSUE: Hardcoded datetime(1992, 7, 15, 23, 40)

2. **services/pillars-service/app/core/engine.py:11**
   - KNOWN ISSUE: Imports from scripts/

3. **services/analysis-service/app/core/luck.py:14-48**
   - KNOWN ISSUE: Hacky importlib.util workaround

4. **services/tz-time-service/app/core/events.py:9**
   - KNOWN ISSUE: Imports from scripts/

## Use with Agent

Copy this into Claude Code:

```
Scan the Saju engine codebase for hardcoded data, stubs, and blocking issues.

Focus on these 8 categories:
1. Hardcoded dates/times/test data
2. Stub/placeholder implementations
3. Missing error handling
4. Circular/cross-service imports
5. Magic numbers without explanation
6. Bare except clauses
7. Missing null checks
8. Functions that always return hardcoded values

For EACH finding, report:
- File:line number
- Code snippet
- Severity (CRITICAL/HIGH/MEDIUM/LOW)
- What breaks if this runs in production
- Recommended fix

Start with these high-risk files:
- services/analysis-service/app/core/engine.py
- services/analysis-service/app/core/luck.py
- services/pillars-service/app/core/engine.py
- services/pillars-service/app/core/strength.py
- scripts/calculate_pillars_traditional.py

Then scan all other files in services/*/app/core/

Create a prioritized report with action items.
```
