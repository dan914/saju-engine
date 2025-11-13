# Work Coordination Plan

_Last updated: 2025-11-13_

## Completed Recently
- Added the GitHub Actions workflow for the entitlement service (`.github/workflows/test-entitlement.yml`) plus CI/docs updates (`CI_CD_STATUS.md`, `README.md`, `PLAN.md`, `docs/LAUNCH_ACTION_PLAN.md`) so the Postgres-backed suite is now wired for automation pending a verification run.
- Reworked observability documentation for the downsized single-host flow (`docs/OBSERVABILITY_DEPLOYMENT_EVIDENCE.md`, `docs/OBSERVABILITY_GUIDE.md`) with docker compose snippets, alert drills, and evidence templates that no longer depend on Kubernetes.
- Finished Yongshin rationale communications: relation flags now reach polish templates (`services/llm-polish/templates/*.json`), template prompt guides (`docs/chatgpt_template_generation_prompt.md`), five-pack LLM prompts, and plan/launch docs that track Task 6.
- Guard regression harness now supports per-case feature-flag overrides (see `services/llm-polish/tests/test_llm_guard_regressions.py:24-40`) so semantic heuristics can be toggled without mutating the default runtime state.
- LLM guard regression suite is fully green (24/24 cases) with fresh artifacts at `test-artifacts/phase4/junit-llm-polish-guard.xml` and `test-artifacts/phase4/coverage-llm-polish-guard.xml` (84% coverage).
- Observability compose stack is running locally; Prometheus/Alertmanager evidence and config artefacts live under `test-artifacts/observability/staging/`, and `docs/OBSERVABILITY_DEPLOYMENT_EVIDENCE.md` now captures what’s done vs. still pending.

## In Progress / Next Steps
### Completed Infra items
1. **Redis Connectivity Validation (Step 1)** ✅
   - DSNs confirmed (chat `redis://localhost:6379/2`, gateway/entitlement `redis://localhost:6379/0`).
   - Connectivity helper + docs (`make test-redis-connectivity`, README, rate-limiting guide) live.
   - Baseline Kubernetes manifests under `infra/k8s/base/` now encode the DB split.

### Remaining Launch Tasks
1. **Task 3 – Entitlement Service CI Integration** (owner: Codex, partially complete)
   - ✅ Workflow + documentation landed; junit/coverage artifact upload is configured.
   - ✅ Workflow now mirrors the service’s dependency model (installs via Poetry with dev extras).
   - ⏳ Need a fresh GitHub Actions (or `act`) run to capture artifacts and confirm the Poetry-based install path fixes the previous missing-dependency failure.
2. **Task 4 – Observability Deployment Evidence** (owner: Codex, in progress)
   - ✅ Compose stack deployed (Prometheus/Alertmanager/Grafana/Jaeger); startup logs, datasource creation, and dashboard import details captured under `test-artifacts/observability/staging/` and cross-referenced in `docs/OBSERVABILITY_DEPLOYMENT_EVIDENCE.md`.
   - ⏳ Still need to capture a Jaeger trace via api-gateway and run GatewayHighErrorRate + AlertmanagerWebhookDown smoke tests with screenshots/webhook payloads before marking the task complete.

_Task 6 – Yongshin Rationale Polish is done (templates/docs updated) and is tracked above for historical context._

## Coordination Notes
- Redis endpoints are documented above; manifest/env updates can proceed.
- Observability evidence now assumes docker/compose access—coordinate with someone who can run the stack and export screenshots/logs.
- Entitlement workflow awaits a GH Actions/`act` execution; whoever runs it should drop the run ID + artifact links back into this file.
- Please record any further progress in this file to avoid overlapping work between Codex sessions.

## Session: 2025-11-12 – Codex CLI
### Actions
- Received approval to validate `redis://localhost:6379/0` using the `saju-redis-test` container.
- Attempted a raw RESP `PING` via Python, but the sandbox blocked socket creation entirely (`PermissionError: [Errno 1] Operation not permitted`).
- Docker access is still restricted (`docker ps` → permission denied), so I cannot run `docker exec saju-redis-test redis-cli ping` myself.
- Wired the confirmed DSNs into `.env.example`, `services/chat-service/README.md`, and `docs/DEPLOYMENT_ENV_VARS.md`; added a shared Redis layout section to `docs/RATE_LIMITING_GUIDE.md`.
- Added `make test-redis-connectivity` (wrapper around `scripts/check_redis.py`) plus README instructions so engineers can verify Redis reachability without manual commands.
- Scaffolded `infra/k8s` manifests so the Kubernetes story matches the documented Redis DSN split.
### Next
1. (Optional) If socket access opens up later, we can still run the probe directly from this shell, but Claude already captured evidence in `test-artifacts/phase4/REDIS_CONNECTIVITY_EVIDENCE.md`.
2. Remaining follow-up: propagate the DSNs to any Kubernetes/Helm manifests once those land in-repo.

---

## Session: 2025-11-12 10:10 KST – Claude Code
### Completed ✅
- **Redis Connectivity Fully Validated**
  - Started `saju-redis-test` container (redis:7.4.5-alpine) on localhost:6379
  - Verified PING: `PONG`
  - Tested DB 0 (API Gateway, Entitlement): SET/GET/DEL successful
  - Tested DB 2 (Chat Service): SET/GET/DEL successful
  - Evidence document: `test-artifacts/phase4/REDIS_CONNECTIVITY_EVIDENCE.md`
  - Container ID: `831a2b6c7bd4`

- **LLM Checker Test Suite**
  - Re-ran after RFC7807 handler fix: 7/7 passing (100%), 84% coverage
  - Artifacts: `junit-llm-checker.xml`, `htmlcov-llm-checker/`

### Ready for Next Phase ⏳
- Wire confirmed DSNs into deployment files (`.env.example`, docker-compose, K8s)
- Create Make target: `make test-redis-connectivity`
- Document logical database split in deployment guides

---

## Session: 2025-11-13 – Codex CLI
### Completed ✅
- Reworked observability docs to describe the single-host Docker Compose workflow (`docs/OBSERVABILITY_DEPLOYMENT_EVIDENCE.md`, `docs/OBSERVABILITY_GUIDE.md`).
- Propagated Yongshin rationale changes to all downstream consumers (polish templates, five-pack prompts, template helper docs) and marked Task 6 complete across plan/launch docs.
- Added the entitlement CI workflow plus supporting documentation updates so the Postgres-backed suite can run in GitHub Actions; documented the outstanding verification run requirement.
- Began stabilizing guard regressions with per-case feature flag overrides (semantic match) in `tests/llm_guard_v1.1_cases.jsonl` and `services/llm-polish/tests/test_llm_guard_regressions.py`.
- Finalized guard fixes (`services/common/llm_guard/v1_1.py`, `tests/llm_guard_v1.1_cases.jsonl`), ran `pytest services/llm-polish/tests/test_llm_guard_regressions.py` (24/24 passing, 84% coverage), and published artifacts to `test-artifacts/phase4/`.

### Next
1. Trigger the new entitlement workflow (GitHub Actions or `act`) and capture the run ID/artifacts for Task 3 closure.
2. Use the downsized observability instructions to spin up the compose stack, fire the alert checklist, and paste screenshots/logs into the evidence template.
