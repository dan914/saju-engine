# Rate Limit Load Test Plan

This playbook documents how to validate the atomic Redis token bucket limiter in
staging before enabling it globally.

## Goals

- Confirm the Lua script enforces atomic token consumption across two service
  instances.
- Ensure no double allowances occur when requests race on the same bucket key.
- Capture telemetry to back a go/no-go decision for production rollout.

## Prerequisites

- Feature flag exposed via `SAJU_ENABLE_ATOMIC_RATE_LIMITER` (already plumbed
  through `saju_common.settings`).
- Staging Redis populated and accessible from the application instances.
- Locust installed locally (`pip install locust==2.31.2`).
- The helper endpoint `/internal/rate-limit/probe` available in staging (or an
  equivalent endpoint that exercises the middleware).

## Test Matrix

| Scenario | Atomic Flag | Expected Behaviour |
| --- | --- | --- |
| Control | Off | Occasional duplicate allowance is acceptable | 
| Candidate | On | Strict single allowance per refill window |

For each scenario run the Locust workload for at least five minutes with two
Locust user classes:

- `RateLimitUser`: slams the probe endpoint with a constant key/cost.
- `RateLimitNoise`: simulates background traffic to keep connections realistic.

## Procedure

1. **Baseline (Flag Off)**
   - Ensure `SAJU_ENABLE_ATOMIC_RATE_LIMITER=false` in staging.
   - Launch Locust using `tests/load/locust_atomic_rate_limit.py`.
   - Record:
     - 200 vs 429 response ratios.
     - Minimum `X-RateLimit-Remaining` observed.
     - Any duplicated allowances after the bucket should be empty.

2. **Candidate (Flag On)**
   - Flip the flag to `true` (per service deployment or environment variable).
   - Re-run Locust with identical parameters.
   - Compare metrics; double allowance rate should drop to zero.

3. **Redis Telemetry**
   - Use `redis-cli monitor` or Redis Insight to observe `EVALSHA` calls on the
     `ratelimit:*` keys during the candidate run.
   - Verify TTLs remain stable (no runaway expirations).

4. **Application Logs**
   - Tail rate-limit logs to confirm credential redaction and absence of error
     spam.

## Exit Criteria

- No duplicate allowance events while the flag is enabled.
- Stable 429 rate at or below the theoretical throughput for the configured
  bucket.
- No Redis or application errors logged during the test window.

If any check fails, disable the flag and investigate before retrying.
