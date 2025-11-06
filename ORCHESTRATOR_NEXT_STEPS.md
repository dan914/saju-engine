# What We Have To Do Now

**Status:** LuckCalculator fixed ✅, but orchestrator bundle doesn't match your codebase engines

---

## The Problem

**The orchestrator bundle expects:**
```python
strength.evaluate(pillars=dict, season=str)
relations.evaluate(pillars=dict)
```

**But your actual engines use:**
```python
strength.evaluate(
    month_branch=str,
    day_pillar=str,
    branch_roots=list,
    stem_exposures=list,
    ...  # 10+ keyword-only parameters
)

relations.evaluate(ctx=RelationContext)  # Object, not dict
```

**This is a fundamental API mismatch** - the bundle is for a different version of the engines.

---

## Your Options

### Option 1: Don't Use The Bundle Orchestrator (RECOMMENDED)

**Why:** Your engines are already working and well-tested (631/657 tests passing)

**What to do:**
1. Write a simple orchestrator yourself that matches YOUR engine APIs
2. It's only ~100 lines to wire together your existing engines
3. You control the API design

**Pros:**
- ✅ Works with your actual engines
- ✅ No version conflicts
- ✅ Clean, maintainable code
- ✅ You understand exactly how it works

**Cons:**
- Takes 1-2 hours to write

**Time:** 1-2 hours

---

### Option 2: Fix The Bundle Orchestrator

**What to do:**
Update all the `_call_*()` methods in `master_orchestrator_real.py` to properly call your engines with the right parameters

**Example fix needed:**
```python
def _call_strength(self, pillars: Dict[str,str], season: str) -> Dict[str,Any]:
    # Extract what strength.evaluate actually needs
    month_branch = pillars["month"][1]  # Get branch from pillar
    day_pillar = pillars["day"]
    branch_roots = [p[1] for p in pillars.values()]  # All branches
    # ... extract other 10+ parameters

    return self.strength.evaluate(
        month_branch=month_branch,
        day_pillar=day_pillar,
        branch_roots=branch_roots,
        stem_exposures=stem_exposures,
        element_counts=element_counts,
        # ... all other parameters
    )
```

**Pros:**
- Uses the provided bundle

**Cons:**
- ❌ Complex - need to adapt 8+ engines
- ❌ Need to understand what each engine parameter means
- ❌ Easy to make mistakes in parameter extraction
- ❌ Maintenance burden

**Time:** 4-6 hours

---

### Option 3: Write Adapter Wrappers

**What to do:**
Add simple wrapper methods to each engine that accept the orchestrator's expected parameters

**Example:**
```python
class StrengthEvaluator:
    # Your existing method
    def evaluate(self, *, month_branch, day_pillar, ...):
        ...

    # NEW: Adapter for orchestrator
    def evaluate_simple(self, pillars: dict, season: str):
        # Extract parameters from pillars dict
        return self.evaluate(
            month_branch=pillars["month"][1],
            day_pillar=pillars["day"],
            ...
        )
```

**Pros:**
- ✅ Keeps existing engines unchanged
- ✅ Works with bundle orchestrator

**Cons:**
- ❌ Adds complexity to each engine
- ❌ Still need to figure out parameter mapping

**Time:** 3-4 hours

---

## What I Recommend

**Option 1: Write your own simple orchestrator**

**Why:**
1. Your engines work great (96% tests passing)
2. You understand your engine APIs
3. Writing orchestrator is straightforward
4. Total control over the design

**What it looks like:**
```python
class SajuOrchestrator:
    def __init__(self):
        self.strength = StrengthEvaluator.from_files()
        self.relations = RelationTransformer.from_file()
        self.climate = ClimateEvaluator.from_file()
        self.yongshin = YongshinSelector()
        self.luck = LuckCalculator()
        # ... other engines

    def analyze(self, pillars: dict, birth_context: dict) -> dict:
        # 1. Call strength engine
        strength_result = self.strength.evaluate(
            month_branch=pillars["month"][1],
            day_pillar=pillars["day"],
            # ... proper parameters
        )

        # 2. Call relations engine
        relation_ctx = RelationContext(...)
        relations_result = self.relations.evaluate(relation_ctx)

        # 3. Call other engines...

        # 4. Return combined results
        return {
            "status": "success",
            "strength": strength_result,
            "relations": relations_result,
            # ...
        }
```

**Time:** 1-2 hours
**Lines of code:** ~150-200
**Difficulty:** Low (just calling your existing engines)

---

## My Suggestion

**Don't use the bundle orchestrator.** It's for a different version of your engines.

Instead:
1. Write a simple orchestrator that calls YOUR engines correctly
2. Test it with your 2000-09-14 birth data
3. You'll have full control and understanding

**Want me to write it?** I can create a working orchestrator for your actual engines in ~30 minutes.

---

## Bottom Line

**You have 2 paths:**

### Path A: Use Your Engines (RECOMMENDED)
- Write simple orchestrator (~100 lines)
- Call your well-tested engines
- Done in 1-2 hours
- ✅ Clean, maintainable

### Path B: Adapt To Bundle
- Fix bundle orchestrator OR add wrappers
- Complex parameter mapping
- 3-6 hours of work
- ⚠️ Fragile, maintenance burden

**I recommend Path A.**

---

**Question for you:** Should I write a simple orchestrator that works with your actual engines?
