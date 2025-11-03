# Architecture Decision Records (ADR)

This directory captures key architectural decisions for the Saju backend. Each ADR documents the context, options considered, and the final decision so future contributors understand why the system looks the way it does.

## Workflow
1. **Propose** – Open a draft ADR (`NNNN-title.md`) with status `Proposed`.
2. **Review** – Circulate with backend, platform, and security stakeholders for feedback.
3. **Decide** – Update status to `Accepted` (or `Rejected`) and note approvers with date.
4. **Implement** – Link related issues/PRs; move ADR to `Superseded` if replaced later.

## Template
Use `0000-template.md` as a starting point. Copy it to the next sequential number (e.g., `0001-secret-platform.md`).

## Pending ADR Topics
- Secret management platform (Vault vs. AWS Secrets Manager vs. Azure Key Vault).
- Dependency injection strategy (FastAPI Depends vs. dependency-injector vs. Lagom).
- API versioning approach (URI vs. header vs. content negotiation).
- Observability stack & sampling strategy (OpenTelemetry collector, exporters, cost controls).
- Database migration tooling & deployment guardrails.

## Reference
- [ADR GitHub Template](https://adr.github.io/)
- [Lightweight Architectural Decision Records](https://www.thoughtworks.com/radar/techniques/lightweight-architecture-decision-records)
