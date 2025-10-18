# Comprehensive Codebase Audit Prompt

**Version:** 1.0
**Date:** 2025-10-10
**Purpose:** Objective assessment of development status for a solo developer working on a Saju analysis system

---

## Your Role

You are a multi-disciplinary audit team consisting of:

1. **Senior Saju Expert** (30+ years traditional practice)
2. **Software Architect** (microservices, distributed systems)
3. **Business Analyst** (SaaS product strategy, market readiness)
4. **QA Engineer** (test coverage, production readiness)
5. **DevOps Engineer** (deployment, scalability, monitoring)
6. **Technical Writer** (documentation quality, knowledge transfer)

Your job is to conduct a **brutally honest, objective assessment** of this codebase. Do not flatter, do not sugarcoat, do not be overly encouraging. Treat this like a pre-Series A technical due diligence audit where investors are considering a $2M investment.

---

## Context

**Project:** Korean Four Pillars (사주) analysis system
**Architecture:** Microservices-based (tz-time, astro, pillars, analysis, luck, llm-polish, etc.)
**Developer:** Solo developer (no team)
**Stage:** Pre-alpha, **not close to release**
**Current Work:** Building orchestration layer to connect isolated engines
**Target Market:** Korean mobile/web users seeking automated saju analysis

**Key Constraint:** This is a one-person operation. The developer is doing architecture, implementation, testing, documentation, and operations alone.

---

## Audit Instructions

### 1. Scan the Entire Codebase

Examine all directories, focusing on:

```
services/
  ├── common/
  ├── tz-time-service/
  ├── astro-service/
  ├── pillars-service/
  ├── analysis-service/
  └── (other services)

scripts/
policy/
schema/
tests/
docs/
tools/
```

### 2. Assessment Framework

For each area, use this scoring system:

- **0/10:** Non-existent or placeholder only
- **1-3/10:** Started but broken, incomplete, or fundamentally flawed
- **4-6/10:** Partially working but significant gaps, technical debt, or design issues
- **7-8/10:** Mostly working with known limitations
- **9-10/10:** Production-ready with comprehensive testing and documentation

**Be specific. Use numbers. Cite evidence.**

### 3. Evaluation Criteria

#### A. Saju Domain Correctness (Saju Expert)

Evaluate:
- **Calculation Accuracy:** Are pillars calculated correctly (LMT, zi-hour, solar terms)?
- **Relationship Logic:** Are 육합/삼합/충/형/파/해 correctly implemented?
- **Strength Evaluation:** Does the 강약 algorithm match traditional methods?
- **Yongshin Logic:** Is 용신 selection defensible by traditional standards?
- **Missing Elements:** What critical saju concepts are not implemented?

**Critical Questions:**
- Would a traditional saju master trust these calculations?
- What would cause incorrect readings that mislead users?
- Are there edge cases that produce nonsensical results?

**Output Format:**
```
Domain Correctness: X/10

Strengths:
- [Specific implementation that is correct]
- [Another correct implementation]

Critical Issues:
- [Specific calculation error with example]
- [Missing traditional concept]
- [Edge case that fails]

Missing Implementations:
- [Required feature not present]
- [Another gap]

Verdict: [1-2 sentences, no fluff]
```

---

#### B. Software Architecture (Software Architect)

Evaluate:
- **Microservice Design:** Are service boundaries logical? Do they follow SRP?
- **Data Flow:** Is the pipeline coherent? Are there circular dependencies?
- **Orchestration:** How is the missing orchestrator blocking progress?
- **API Contracts:** Are interfaces well-defined? Versioned?
- **Scalability:** Can this handle 10K users? 100K? 1M?
- **Technical Debt:** How much refactoring is needed before launch?

**Critical Questions:**
- Is the architecture fundamentally sound or does it need a rewrite?
- What are the top 3 architectural mistakes?
- How much of the "working" code is actually integration-ready?

**Output Format:**
```
Architecture Quality: X/10

Sound Decisions:
- [Specific good architectural choice]
- [Another good choice]

Architectural Flaws:
- [Critical design mistake with impact]
- [Another flaw]

Blocking Issues:
- [What must be fixed before launch]
- [Another blocker]

Estimate: [X weeks/months to production-ready architecture]
```

---

#### C. Implementation Quality (QA Engineer)

Evaluate:
- **Test Coverage:** What % of code has tests? Are tests meaningful?
- **Error Handling:** What happens when things fail? Are there silent failures?
- **Code Quality:** Is code maintainable? Are there anti-patterns?
- **Integration Status:** How many engines are actually connected vs. isolated?
- **Production Readiness:** Can this be deployed today? What breaks?

**Critical Questions:**
- How many "working" features are actually tested?
- What percentage of engines are just code files with no integration?
- Where are the ticking time bombs (race conditions, memory leaks, etc.)?

**Output Format:**
```
Implementation Quality: X/10

Test Coverage:
- Unit tests: X/Y files covered (Z%)
- Integration tests: X/Y pipelines covered
- E2E tests: [Present/Absent]

Critical Bugs:
- [Specific bug or design flaw]
- [Another issue]

Technical Debt:
- [Code smell or anti-pattern]
- [Another debt item]

Production Blockers:
- [Must-fix before launch]
- [Another blocker]

Estimate: [X weeks to acceptable quality]
```

---

#### D. Business Viability (Business Analyst)

Evaluate:
- **Feature Completeness:** Can this deliver value to users in its current state?
- **Market Readiness:** Is this 10% done? 50%? 90%?
- **Competitive Position:** How does this compare to existing saju apps?
- **Monetization Readiness:** Are token/entitlement systems implemented?
- **User Experience:** Can a user get a complete reading?

**Critical Questions:**
- Would anyone pay for this today?
- What's the MVP feature set, and what % is done?
- If you launched tomorrow, what would break?

**Output Format:**
```
Business Readiness: X/10

Completed Features:
- [Feature that works end-to-end]
- [Another complete feature]

Incomplete Features:
- [Feature that is partially done (X%)]
- [Another incomplete feature]

Missing Critical Features:
- [Must-have for launch]
- [Another must-have]

Market Assessment:
- Completion: X% of MVP
- Estimated time to beta: [X months]
- Estimated time to production: [X months]

Verdict: [Harsh reality check, 2-3 sentences]
```

---

#### E. Operational Readiness (DevOps Engineer)

Evaluate:
- **Deployment:** Can this be deployed? Docker? K8s? Cloud-ready?
- **Monitoring:** How would you know if it's broken in production?
- **Scalability:** What's the bottleneck? Can it handle real load?
- **Database:** Is there persistent storage? Migration strategy?
- **Security:** Are there glaring security issues?

**Critical Questions:**
- Can this run anywhere besides the developer's laptop?
- What happens when 1000 users hit it simultaneously?
- How do you roll back a bad deployment?

**Output Format:**
```
Operational Readiness: X/10

Deployment Status:
- [Current deployment capability]
- [Missing infrastructure]

Scalability Analysis:
- Estimated capacity: [X concurrent users]
- Bottlenecks: [Specific limitation]

Critical Gaps:
- [Must-have for production]
- [Another gap]

Estimate: [X weeks to deployable]
```

---

#### F. Documentation Quality (Technical Writer)

Evaluate:
- **Code Documentation:** Can another developer understand the code?
- **API Documentation:** Are endpoints documented? Examples present?
- **Architecture Docs:** Can someone new understand the system?
- **User Documentation:** Is there any end-user documentation?
- **Maintenance Docs:** Can the solo dev revisit this in 6 months and understand it?

**Critical Questions:**
- If the developer got hit by a bus tomorrow, could someone else continue?
- Are there undocumented assumptions that would cause bugs?
- How much tribal knowledge is locked in the developer's head?

**Output Format:**
```
Documentation Quality: X/10

Well-Documented:
- [Area with good documentation]
- [Another well-documented area]

Poorly Documented:
- [Critical gap in documentation]
- [Another gap]

Bus Factor Analysis:
- Knowledge transfer difficulty: [High/Medium/Low]
- Estimated ramp-up time for new developer: [X weeks]

Verdict: [Honest assessment]
```

---

### 4. Overall Assessment

After evaluating all areas, provide:

#### Summary Scorecard

```
┌─────────────────────────────┬───────┬──────────────┐
│ Area                        │ Score │ Priority Fix │
├─────────────────────────────┼───────┼──────────────┤
│ Saju Domain Correctness     │  X/10 │ [H/M/L]      │
│ Software Architecture       │  X/10 │ [H/M/L]      │
│ Implementation Quality      │  X/10 │ [H/M/L]      │
│ Business Viability          │  X/10 │ [H/M/L]      │
│ Operational Readiness       │  X/10 │ [H/M/L]      │
│ Documentation Quality       │  X/10 │ [H/M/L]      │
├─────────────────────────────┼───────┼──────────────┤
│ OVERALL                     │  X/10 │              │
└─────────────────────────────┴───────┴──────────────┘
```

#### Reality Check

Answer these questions with brutal honesty:

1. **If you had to launch to 1000 paying users in 30 days, what's the probability of success?**
   - [ ] 0-10%: No chance
   - [ ] 10-30%: Very unlikely
   - [ ] 30-50%: Possible but risky
   - [ ] 50-70%: Likely with intense work
   - [ ] 70-90%: Highly likely
   - [ ] 90-100%: Virtually certain

2. **What is the single biggest risk to this project?**
   - [One sentence, specific]

3. **If you were advising the developer, what would you tell them to stop doing immediately?**
   - [Specific advice]

4. **What should the developer focus on next (after orchestrator)?**
   - Priority 1: [Specific task]
   - Priority 2: [Specific task]
   - Priority 3: [Specific task]

5. **How many months until this could realistically launch as a paid beta?**
   - Optimistic: [X months]
   - Realistic: [Y months]
   - Pessimistic: [Z months]

6. **If you were a potential acquirer, what's your evaluation?**
   - [ ] Hard pass - fundamental issues
   - [ ] Maybe in 12+ months if major progress
   - [ ] Maybe in 6 months if orchestrator + testing done
   - [ ] Interested now with conditions
   - [ ] Strong interest

---

### 5. Top 10 Critical Issues

List the 10 most critical problems blocking production launch, ranked by severity:

```
1. [Issue] - Impact: [X] - Effort to fix: [Y weeks]
2. [Issue] - Impact: [X] - Effort to fix: [Y weeks]
3. [Issue] - Impact: [X] - Effort to fix: [Y weeks]
...
10. [Issue] - Impact: [X] - Effort to fix: [Y weeks]
```

---

### 6. Solo Developer Sustainability Assessment

Special section because this is a one-person project:

**Burnout Risk:** [Low/Medium/High]
**Scope Creep Risk:** [Low/Medium/High]
**Technical Debt Accumulation Rate:** [Slow/Moderate/Fast]

**Red Flags:**
- [Specific pattern suggesting unsustainable development]
- [Another red flag]

**Recommendations for Solo Dev:**
- [Specific advice for working alone]
- [Another recommendation]

---

## Output Requirements

1. **Be Specific:** Use file names, line numbers, function names
2. **Use Evidence:** Quote code, cite tests, reference documentation
3. **No Sugarcoating:** If something is broken, say it's broken
4. **No Flattery:** Don't praise effort, praise results
5. **Actionable:** Every criticism should suggest a fix
6. **Quantitative:** Use numbers wherever possible (test coverage %, line counts, time estimates)

## Example of Good vs. Bad Feedback

❌ **Bad (Too Vague, Too Nice):**
> "The analysis service looks good and has some nice features. The code quality is decent and there are tests. Keep up the good work!"

✅ **Good (Specific, Honest, Actionable):**
> "Analysis service: 4/10. StrengthEvaluator (strength.py:280) has 47 tests but isn't integrated with any orchestrator. RelationTransformer (relations.py) calculates 육합/삼합 correctly but missing 원진 detection mentioned in CLAUDE.md. Zero integration tests between engines. 8 out of 11 engines are isolated code files that can't be called in a real pipeline. Orchestrator implementation (ORCHESTRATOR_IMPLEMENTATION_PLAN.md) exists as a plan document but no actual code. Estimate: 3 weeks to working integration."

---

## Deliverable

Produce a single markdown report titled:

**"Technical Due Diligence Report: Saju Analysis System"**

Date: [Today's date]
Auditors: [List the 6 expert roles]
Subject: Pre-alpha saju analysis system by solo developer

Include:
- All 6 area assessments (A-F)
- Summary scorecard
- Reality check answers
- Top 10 critical issues
- Solo developer sustainability assessment

**Tone:** Professional, objective, data-driven, unvarnished truth. Write as if your reputation depends on accuracy, not kindness.

---

## Final Note to Auditors

The developer is NOT looking for encouragement. They are looking for truth. They need to know:

- What's actually done vs. what's just planned
- What's blocking launch
- How far from production-ready
- What to prioritize
- Whether to continue or pivot

Your job is to deliver clarity, not comfort.

**Be honest. Be thorough. Be harsh if needed.**
