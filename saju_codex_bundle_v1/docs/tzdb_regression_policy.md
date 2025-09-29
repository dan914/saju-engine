
# TZDB Update Monitoring & Regression Policy (DR-6)

**Goal:** Automatically detect behavior changes in local→UTC conversion around known historical boundaries for Asia/Seoul, Asia/Pyongyang, Asia/Tokyo, Asia/Shanghai when tzdb is upgraded.

## Threshold
- Flag if |ΔUTC| > **1 second** (ignore trivial rounding). Typical tz rule changes produce >=1800s or >=3600s.

## Samples
- 20 curated cases (see `tzdb_samples.csv`) targeting DST start/end gaps/overlaps and standard offset switches.

## Procedure
1. Convert each sample using **old tzdb** and **new tzdb** → obtain UTC or offset.
2. Compare results; if difference > 1s, **flag regression** for human review.
3. Aggregate results and emit a summary (pass/fail, counts, details).

## Alerting
- On any failure → send Slack/Email: versions compared, failed cases, magnitude, link to report.
- On pass → log/Slack info: “TZDB regression test passed, no differences.”

## Deployment Checklist
1) Run pre-deploy regression test (old vs new).  
1a) If failures → human review (check release notes, app impact) → approve or hold.  
2) Backup/rollback plan ready.  
3) Deploy new tzdb.  
4) Post-deploy verification (ensure results match pre-test).  
5) Notify outcome.  
6) Update internal docs + sign-off.  
7) Monitor logs a few days for time-related anomalies.

## Logs (result schema)
See `tzdb_result_schema.json` for per-case and summary fields.
