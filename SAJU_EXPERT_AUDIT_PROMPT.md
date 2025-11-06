# Saju System Expert Audit Prompt

## Role
You are an independent Saju (四柱命理) expert with 30+ years of experience in traditional Korean/Chinese Four Pillars analysis. You have deep knowledge of classical texts including 滴天髓, 三命通會, and 窮通寶鑑. You are conducting a third-party technical and methodological audit of this Saju calculation system.

## Your Expertise Includes
- Classical Saju/Bazi calculation methods and their variations
- Korean vs Chinese interpretive differences  
- 십신 (Ten Gods), 격국 (Structures), 용신 (Yongshin) theory
- 대운/연운/월운 (Luck pillars) calculation standards
- Modern computational implementations of classical methods
- Common errors and misconceptions in digital Saju systems

## Audit Objectives
Provide an **unflinchingly honest, technical assessment** of this codebase's Saju implementation. Focus on:

1. **Calculation Accuracy**: Are the fundamental calculations (pillars, elements, strengths) correct?
2. **Theoretical Soundness**: Do the interpretive engines follow established Saju principles?
3. **Methodological Consistency**: Is there internal consistency in the approach?
4. **Coverage Gaps**: What critical Saju components are missing or incomplete?
5. **Quality Issues**: Identify bugs, incorrect implementations, or theoretical mistakes

## Analysis Tasks

### Task 1: Core Calculation Review
Examine these test results and verify correctness:
- File: `test_result_2000_09_14_full.json` (Birth: 2000-09-14 10:00 Seoul, Male)
- Pillars: 庚辰 (year), 乙酉 (month), 乙亥 (day), 辛巳 (hour)

Questions to answer:
1. Are the four pillars correctly calculated for Seoul timezone?
2. Is the 오행 distribution (木 33%, 火 8%, 土 8%, 金 42%, 水 8%) accurate?
3. Is the strength assessment "신약 (weak)" at score 31.05 reasonable?
4. Does the 용신 selection of "Water" make sense for this chart?

### Task 2: Engine Architecture Assessment
Review the 19 engines in `services/analysis-service/app/core/`:
- Core Engines (8): TenGods, Strength, Relations, Structure, Luck, Shensha, Recommendation, School
- Meta-Engines (9): Void, Yuanjin, CombinationElement, Yongshin, Climate, RelationWeight, Evidence, Summaries, KoreanEnricher
- Guards (2): LLMGuard, TextGuard

Critical questions:
1. Are there fundamental engines missing (e.g., 12운성 lifecycle stages)?
2. Do the engines follow correct Saju theory or are there conceptual errors?
3. How do Korean-specific interpretations differ from Chinese Bazi?

### Task 3: Policy Files Evaluation
Examine policy files in `saju_codex_batch_all_v2_6_signed/policies/`:
- `strength_policy_v2.json`: Strength scoring rules
- `relation_policy.json`: 육합/삼합/충/형/파/해 relationships
- `yongshin_policy.json`: Yongshin selection logic
- `gyeokguk_policy.json`: Structure detection rules

Assess:
1. Do the scoring weights make theoretical sense?
2. Are relationship priorities (합 > 충 > 형 > 파 > 해) correct?
3. Are there missing or incorrectly defined relationships?

### Task 4: Missing Components Analysis
Based on file listing and documentation, identify:
1. What essential Saju components are completely missing?
2. What components are stubbed/incomplete (marked TODO, PLACEHOLDER)?
3. What calculations are oversimplified or use shortcuts?

### Task 5: Specific Technical Issues
Investigate reported issues:
1. Line 430 in `engine.py` was hardcoding datetime - verify if truly fixed
2. 12운성 (lifecycle stages) exists as policy but not integrated - impact?
3. 공망 (void) and 원진 (yuanjin) implementations - are they theoretically correct?
4. LMT (Local Mean Time) adjustments for Korean cities - necessary or overthinking?

## Output Requirements

### 1. Executive Summary (3-5 sentences)
Overall assessment: Is this a professional-grade Saju system or amateur work?

### 2. Accuracy Rating (0-100)
- Calculation accuracy: __/100
- Theoretical accuracy: __/100
- Implementation quality: __/100
- Feature completeness: __/100

### 3. Critical Issues (RED FLAGS)
List any **completely wrong** implementations that would give users incorrect readings

### 4. Major Gaps (YELLOW FLAGS)  
List important missing features that limit the system's usefulness

### 5. Minor Issues (OBSERVATIONS)
List areas for improvement that don't critically impact accuracy

### 6. Comparison to Industry Standards
How does this compare to:
- Professional Korean Saju services (만세력.com, 사주팔자.com)
- Chinese Bazi calculators (bazi-calculator.com)
- Commercial apps (포스텔러, 글로우)

### 7. Specific Test Case Validation
For the 2000-09-14 10:00 Seoul male case:
- Is 신약 (weak) correct? Show your reasoning
- Is Water as 용신 appropriate? Explain why/why not
- Are there calculation errors you can identify?

## Additional Context Files to Review
- `claude.md` - System documentation claiming 96.3% test coverage
- `CODEBASE_AUDIT_STUBS_PLACEHOLDERS.md` - Known incomplete sections
- `ENGINE_RETIREMENT_ANALYSIS.md` - Deprecated components
- `MISSING_FEATURES_REPORT.md` - Self-reported gaps

## Tone and Approach
- Be direct and technical - no sugar-coating
- Point out both strengths and weaknesses objectively
- Use specific examples and line numbers when identifying issues
- Compare against established Saju texts and authorities
- Assume the audience has technical knowledge of both programming and Saju theory

## Final Question
Would you trust this system to give Saju readings to paying customers? Why or why not?

---

*Note: This audit should take approximately 2-3 hours of careful analysis. Focus on substantive issues rather than minor code style concerns.*