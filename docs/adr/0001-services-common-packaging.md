# ADR 0001 – Packaging Strategy for `services/common`

- **Status:** Proposed
- **Date:** 2025-11-02
- **Deciders:** @backend-lead, @platform-eng, @qa-lead
- **Tags:** backend, packaging, dependency-injection

## Context

Phase 2 of the backend cleanup program requires us to eliminate ad-hoc `sys.path` manipulation and singleton patterns. The shared utilities under `saju-engine/services/common` are currently imported via manual path injections across services, scripts, and tests. A duplicate legacy copy still lives at the repository root (`services/common`).

We need a packaging strategy that:
- Allows all services to import shared utilities without mutating `sys.path`.
- Works with Poetry-based workspace tooling and existing CI environments.
- Supports gradual refactoring of service dependencies and tests.

Two viable approaches emerged:

1. Promote `services/common` to a distributable package (editable install) referenced by each service.
2. Convert `saju-engine/services` into a namespace package so subpackages are automatically discoverable.

## Decision

We will package `services/common` as an editable package within the `saju-engine` project. The root `pyproject.toml` already exposes `packages = [{ include = "services" }]`; we will formalize this by:

- Removing the legacy top-level `services/common` directory.
- Ensuring `saju-engine/services/common` is included in the Poetry project metadata.
- Updating service imports to use standard package paths (e.g., `from services.common import create_service_app`).
- Adding a lightweight installer (editable/install path) so scripts/tests outside `saju-engine` can `pip install -e saju-engine` when necessary.

Rationale:

- Aligns with existing project structure and avoids Poetry namespace limitations.
- Keeps shared utilities tied to the `saju-engine` release cadence.
- Supports gradual migration—services already import `services.common`, so removing `sys.path` edits becomes a matter of cleaning fallbacks.

## Consequences

Positive:
- Eliminates custom path hacks; imports resolve via standard packaging.
- Simplifies developer onboarding (Poetry install provides shared utilities).
- Enables future extraction of `services/common` into its own wheel if needed.

Negative:
- Requires careful cleanup of legacy `services/common` copies to avoid shadowing.
- Scripts/tests that currently run outside the Poetry environment need updated instructions (`poetry run` or editable install).

Neutral:
- No impact on runtime packaging for services deployed as containers—the package lives inside the repo image.

## Alternatives Considered

1. **Namespace package for `saju-engine/services`**
   - *Pros:* Minimal metadata changes; allows multiple subpackages under `services`.
   - *Cons:* Namespace support in Poetry is still rough (requires implicit namespace packaging); risk of import ambiguity; harder to enforce package boundaries.

2. **Standalone wheel for `services-common`**
   - *Pros:* Clear versioning; could be reused across repos.
   - *Cons:* Overhead of build/publish pipeline; increases release complexity for Phase 2 timeline.

## Follow-up Actions
- [ ] Remove the legacy top-level `services/common` directory after confirming no unique content remains.
- [ ] Update `saju-engine/pyproject.toml` to declare `services.common` explicitly and ensure `poetry build` includes it (owner: Platform, due: 2025-11-09).
- [ ] Replace `sys.path` fallback blocks in service entrypoints and scripts once packaging is verified (owner: Backend, due: 2025-11-16).
- [ ] Update developer onboarding docs to reference `poetry run` usage and editable installs for CLI tools (owner: DevRel, due: 2025-11-16).

## References
- `grand audit/phase2_dependency_plan.md`
- `grand audit/backend_cleanup_plan.md:52-61`
- `saju-engine/docs/poetry-migration-strategy.md`
