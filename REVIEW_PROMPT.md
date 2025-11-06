# Senior Development Team Code Review Prompt

## Context

You are a **senior development team** conducting a comprehensive code review of the saju-engine project after completing Week 4 Backend Integrity Sweep (8 tasks completed). Your team consists of:

- **Senior Architect** - Systems design, architecture patterns, scalability
- **Backend Engineer** - API design, data integrity, performance
- **DevOps Engineer** - Infrastructure, deployment, observability
- **Security Engineer** - Vulnerability assessment, compliance
- **QA Engineer** - Testing coverage, edge cases, quality gates
- **Tech Lead** - Code quality, maintainability, technical debt

## Your Mission

Conduct a **thorough audit** of all work completed in Week 4 to identify:

1. ✅ **Completeness Issues** - Missing implementations, incomplete features, TODO comments
2. 🐛 **Bugs & Errors** - Logic errors, edge cases, error handling gaps
3. ⚠️ **Placeholders** - Hardcoded values, mock data, temporary solutions
4. 🔒 **Security Risks** - Vulnerabilities, credential exposure, unsafe patterns
5. 📊 **Performance Issues** - Bottlenecks, inefficient algorithms, resource leaks
6. 🧪 **Testing Gaps** - Untested code paths, missing edge cases, low coverage
7. 📝 **Documentation Debt** - Outdated docs, missing examples, unclear guides
8. 🏗️ **Architecture Concerns** - Design flaws, tight coupling, scalability limits
9. 🔧 **Configuration Issues** - Missing env vars, hardcoded paths, deployment gaps
10. 🚨 **Production Readiness** - Logging, monitoring, error recovery, rollback plans

## Week 4 Tasks Completed

### Task 1-3 (Previous Session)
- ✅ Dependency container module (`services/common/saju_common/container.py`)
- ✅ Refactored services off `@lru_cache` singletons
- ✅ Retired `sitecustomize.py` path hacks (documented blockers)

### Task 4: DevShell Helper
- **File**: `scripts/devshell.py` (354 lines)
- **Changes**: Fixed IPython Config object usage
- **Docs**: `docs/DEVSHELL_GUIDE.md` (592 lines)
- **Tests**: Manual testing only

### Task 5: Pydantic Settings
- **Files**:
  - `services/common/saju_common/settings.py` (173 lines)
  - Refactored `policy_loader.py` (50 lines)
- **Tests**: `test_settings.py` (153 lines, 13/13 passing)
- **Critical**: Resolved sitecustomize.py blocker

### Task 6: Policy Consolidation
- **Files**:
  - `docs/POLICY_CONSOLIDATION_PLAN.md` (300+ lines)
  - `scripts/audit_policy_files.py` (200+ lines)
  - `docs/POLICY_CONSOLIDATION_SUMMARY.md` (170+ lines)
- **Decision**: No immediate consolidation (status quo working)

### Task 7: OpenTelemetry Integration
- **Files**:
  - `services/common/saju_common/tracing.py` (373 lines)
  - Fixed imports in `test_error_handling.py`
- **Tests**: `test_tracing.py` (178 lines, 18/18 passing)
- **Docs**: `docs/OBSERVABILITY_GUIDE.md` (547 lines)

### Task 8: Rate Limiting
- **Files**:
  - `services/common/saju_common/rate_limit.py` (443 lines)
  - Updated `settings.py` with rate limiting config
- **Tests**: `test_rate_limit.py` (320 lines, 17/17 passing)
- **Docs**: `docs/RATE_LIMITING_GUIDE.md` (632 lines)

## Review Instructions

### Step 1: Read All Implementation Files
Use parallel Read operations to examine:
- `services/common/saju_common/container.py`
- `services/common/saju_common/settings.py`
- `services/common/saju_common/policy_loader.py`
- `services/common/saju_common/tracing.py`
- `services/common/saju_common/rate_limit.py`
- `services/common/saju_common/__init__.py`
- `scripts/devshell.py`
- `scripts/audit_policy_files.py`

### Step 2: Review All Test Files
Use parallel Read operations to examine:
- `services/common/tests/test_settings.py`
- `services/common/tests/test_tracing.py`
- `services/common/tests/test_rate_limit.py`
- `services/common/tests/test_error_handling.py`

### Step 3: Search for Red Flags
Use Grep to search for:
```bash
# Placeholders and TODOs
pattern: "TODO|FIXME|XXX|HACK|PLACEHOLDER|TEMPORARY"

# Hardcoded values
pattern: "localhost|127\.0\.0\.1|hardcode|mock"

# Security risks
pattern: "password|secret|key|token|api_key" (check if properly handled)

# Error suppression
pattern: "except:\s*pass|except Exception:\s*pass"

# Print debugging
pattern: "print\(|console\.log"
```

### Step 4: Architecture Analysis
**Senior Architect reviews:**
- Dependency injection patterns in `container.py`
- Settings management architecture in `settings.py`
- Tracing integration design in `tracing.py`
- Rate limiting algorithm choice in `rate_limit.py`

**Questions to answer:**
- Is the container pattern scalable?
- Are there circular dependency risks?
- Does settings handle all edge cases?
- Is rate limiting distributed-ready?
- Are there single points of failure?

### Step 5: Security Audit
**Security Engineer reviews:**
- Credential handling in settings
- Redis connection security in rate_limit.py
- Policy file access controls
- Error messages (information leakage?)
- Logging (sensitive data exposure?)

**Questions to answer:**
- Can attackers bypass rate limiting?
- Are Redis credentials properly secured?
- Is there PII in logs?
- Are error messages safe for production?

### Step 6: Performance Analysis
**Backend Engineer reviews:**
- Token bucket algorithm efficiency
- Redis connection pooling
- Settings caching strategy
- Policy file lookup performance
- Middleware overhead

**Questions to answer:**
- Are there N+1 query patterns?
- Is Redis properly pooled?
- Can settings cause startup delays?
- Are there memory leaks?

### Step 7: Testing Coverage Analysis
**QA Engineer reviews:**
- Test coverage percentages
- Edge cases tested
- Error path coverage
- Integration test gaps
- E2E scenario coverage

**Questions to answer:**
- Are all error paths tested?
- Are there untested edge cases?
- Is async code properly tested?
- Are there race condition risks?

### Step 8: Production Readiness Check
**DevOps Engineer reviews:**
- Configuration management
- Environment variable handling
- Deployment documentation
- Monitoring/alerting setup
- Rollback procedures

**Questions to answer:**
- Can we deploy to production today?
- Are all configs documented?
- Is monitoring in place?
- Do we have rollback plans?

### Step 9: Code Quality Assessment
**Tech Lead reviews:**
- Code duplication (DRY violations)
- Function complexity (cyclomatic)
- Naming consistency
- Type hints coverage
- Documentation quality

**Questions to answer:**
- Is code maintainable?
- Are abstractions appropriate?
- Is there technical debt?
- Are patterns consistent?

## Output Format

Provide your review as a **structured report** with:

### Executive Summary
- Overall assessment (Ready/Not Ready for production)
- Critical issues count
- High/Medium/Low priority issues
- Recommendations summary

### Findings by Category

For each issue found, provide:
```yaml
issue_id: ISSUE-001
severity: critical|high|medium|low
category: completeness|bug|placeholder|security|performance|testing|docs|architecture|config|production
title: "Brief description"
location: "file:line or file:function"
description: "Detailed explanation of the issue"
impact: "What could go wrong if not fixed"
recommendation: "How to fix it"
effort: "Estimated hours to fix"
priority: "1-5 (1=highest)"
```

### Risk Assessment
- **Critical Risks** (must fix before production)
- **High Risks** (fix before next release)
- **Medium Risks** (fix in sprint)
- **Low Risks** (backlog)

### Positive Findings
- What was done exceptionally well
- Best practices followed
- Quality highlights

### Action Items
Prioritized list of specific tasks to address findings:
1. [CRITICAL] Fix X in Y (2h)
2. [HIGH] Add tests for Z (4h)
3. [MEDIUM] Refactor A in B (8h)
...

### Metrics Dashboard
```
Total Issues Found: X
├── Critical: X
├── High: X
├── Medium: X
└── Low: X

Test Coverage: X%
Code Quality Score: X/10
Documentation Score: X/10
Production Readiness: X/10
```

## Review Checklist

### Completeness ✓
- [ ] All TODOs/FIXMEs addressed or documented
- [ ] All functions fully implemented (no stubs)
- [ ] All error cases handled
- [ ] All edge cases considered

### Security ✓
- [ ] No hardcoded credentials
- [ ] Proper input validation
- [ ] Safe error messages
- [ ] No SQL injection risks
- [ ] No sensitive data in logs

### Performance ✓
- [ ] No N+1 queries
- [ ] Proper connection pooling
- [ ] Efficient algorithms
- [ ] No memory leaks
- [ ] Appropriate caching

### Testing ✓
- [ ] Unit tests for all functions
- [ ] Integration tests for workflows
- [ ] Edge cases tested
- [ ] Error paths tested
- [ ] >80% code coverage

### Documentation ✓
- [ ] All public APIs documented
- [ ] Examples provided
- [ ] Deployment guides complete
- [ ] Troubleshooting sections
- [ ] Architecture diagrams

### Production ✓
- [ ] Configuration externalized
- [ ] Logging comprehensive
- [ ] Monitoring hooks present
- [ ] Health checks implemented
- [ ] Rollback procedures documented

## Start Your Review

Begin by reading the implementation files in parallel, then systematically work through each review step. Be thorough, critical, and constructive. Your goal is to ensure **production-grade quality** before deployment.

**Remember:** You're not just looking for bugs—you're validating that this code is:
- **Secure** - No vulnerabilities or data exposure
- **Reliable** - Handles errors gracefully
- **Performant** - Scales under load
- **Maintainable** - Easy to understand and modify
- **Observable** - Can be monitored and debugged
- **Deployable** - Ready for production

Focus on **evidence-based findings** with specific file locations and code examples. Be specific, be thorough, and be honest about what you find.

---

**Good luck with your review! 🔍**
