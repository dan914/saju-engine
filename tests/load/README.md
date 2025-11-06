# Rate Limit Load Testing

This directory contains scaffolding for exercising the Redis-backed rate-limiter
under concurrent load. The tooling is optional and is intended to run from a
developer workstation or CI job with Redis access.

## Prerequisites

- Python 3.11+
- `locust` 2.31 or later installed in the active virtualenv
- Accessible Redis instance seeded with the rate-limit keys under test

Install Locust locally:

```bash
pip install locust==2.31.2
```

## Running the Scenario

```bash
locust -f locust_atomic_rate_limit.py \
  --host "https://saju-staging.example.com" \
  --users 50 \
  --spawn-rate 10 \
  --run-time 5m
```

Key environment options:

- `REDIS_URL`: target Redis instance (defaults to `redis://localhost:6379/0`)
- `RATE_LIMIT_KEY`: bucket identifier to spam (defaults to `user:loadtest`)
- `TOKEN_COST`: per-request cost (defaults to `1`)
- `USE_ATOMIC_FLAG`: when set to `true`, requests include the feature flag header

The scenario uses two Locust tasks to simulate simultaneous traffic from two
service instances hitting the same key. Metrics of interest:

- proportion of 200 vs 429 responses
- `X-RateLimit-Remaining` trending toward 0 without oscillation
- absence of duplicate allowance events in the log summary

See `docs/RATE_LIMIT_LOAD_TEST_PLAN.md` for the full validation procedure.
