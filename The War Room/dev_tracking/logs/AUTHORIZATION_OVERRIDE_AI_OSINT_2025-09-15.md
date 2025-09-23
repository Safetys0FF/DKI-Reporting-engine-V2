# Authorization Override — AI/OSINT Enablement (Scoped)

- Date: 2025-09-15
- Requested by: Product Owner (user)
- Executor: POWER agent

Decision
- Override the “no new features” directive ONLY for enabling AI/OSINT capabilities required for core functionality validation and user value.
- Scope-limited to: OpenAI-assisted analysis, OSINT lookups (Google Custom Search, Google Maps Geocoding), and SmartLookup orchestration.

Guardrails
- Cost control: No automatic batch jobs; smoke tests are key‑presence gated.
- Safety: Keys pulled from User Profile Manager or `api_keys.json`; no keys are committed.
- Observability: All invocations log to `dki_engine.log`; readiness scripts summarize status without forcing external calls.
- Reversion: Toggle `ai.enable_osint` can be reverted to `false` in `dki_config.json` after QC.

Rationale
- DEESCALATION quality gate focused on stability. With core E2E validated, enabling AI/OSINT (scoped) unlocks end‑to‑end value for entity extraction and verification while maintaining controls.

Planned Work (this session)
1) Enable OSINT in config (no keys stored in code)
2) Install light optional libs (openai, beautifulsoup4)
3) Add readiness smoke (key detection + dry checks)
4) Wire AI/OSINT toggles into run path via existing modules
5) Prepare credential entry guide and connectivity checks

Exit Criteria
- Readiness smoke reports available modules and keys status
- OpenAI client initializes when key present (no crash)
- OSINT endpoints return structured errors if keys missing; pass on presence
- SmartLookup honors lookup_order and short‑circuits

Notes
- This override applies only to AI/OSINT enablement; all other feature work remains frozen pending QC sign‑off.
