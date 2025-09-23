# Section CP (Cover Page) - Structured Rebuild Roadmap (Draft)

> **Order Lock:** Section 1 / Gateway executes first and must never be reordered. All Section CP activities assume Section 1 is validated and published.

## 1. Mission Statement
Render the canonical cover page using authoritative metadata supplied by Section 1, enforcing branding, licensing, and investigator credentials the downstream sections will inherit.
 - Information reference guide
         "F:\DKI-Report-Engine\Report Engine\Logic files\canvas logic for report"
         "F:\DKI-Report-Engine\Report Engine\Sections\section_readme"
         "F:\DKI-Report-Engine\Report Engine\Gateway"
         "F:\DKI-Report-Engine\Report Engine\Sections\section_engines"
         "F:\DKI-Report-Engine\Report Engine\Gateway\parsing maps"
         "F:\DKI-Report-Engine\Report Engine\Gateway\section_readme"
         "F:\DKI-Report-Engine\Report Engine\dev_tracking\templates"
      
      - Boot up sequences and testing procedures
         "F:\DKI-Report-Engine\Report Engine\Start Menu"

      - Tools sets and engines
         "F:\DKI-Report-Engine\Report Engine\Plugins"

## 2. System Context
- **Ingress:** Gateway-provided `case_metadata`, `client_profile`, `agency_profile`, branding assets, and toolkit normalization snapshot.
- **Egress:** `section_cp_payload` containing `render_tree`, `cover_profile` manifest, QA flags, and provenance for reuse by Sections DP and 9.
- **Scope:** Branding enforcement, credential validation, contact/channel confirmation, signature asset staging.

## 3. Gateway Communication Contract
- `gateway.prepare_section('section_cp')` – issued immediately after Section 1 sign-off.
- `gateway.get_section_inputs('section_cp')` – returns cover inputs: `{case_metadata, client_profile, agency_profile, branding_assets, toolkit_results}`.
- `gateway.publish_section_result('section_cp', payload)` – posts structured output plus QA flags and provenance.
- `gateway.subscribe('case_metadata_revision', ...)` – Section CP listens for upstream metadata changes that require rerender.
- `gateway.emit('cover_profile_ready', manifest)` – notifies dependent sections (DP, 9, FR) once validated.

## 4. Stage Checklist & Checkpoints
| Stage | Description | Inputs | Checkpoint |
|-------|-------------|--------|------------|
| Intake | Pull gateway bundle, verify Section 1 signature, load branding assets. | `case_metadata`, assets | `cp_intake_logged` |
| Validate | Confirm investigator/license numbers, client data, contract IDs against toolkit cache. | toolkit results, repository | `cp_credentials_validated` |
| Render | Build `render_tree` with fixed layout, inject placeholders only when flagged. | validated data | `cp_render_complete` |
| QA | Run compliance checks (branding lock, contact channels, signature presence). | render output | `cp_qc_passed` or `cp_qc_failed` |
| Publish | Write payload to gateway, emit readiness signal. | payload | `section_cp_completed` |
| Monitor | Handle revision requests via gateway while enforcing ``max_reruns`` and logging ``revision_depth``. | gateway signals | `cp_revision_processed` |

## 5. Guardrails & Failsafes
- Reject if Section 1 status != validated.
- Reject if mandatory assets missing (logo, investigator name, license). Log `cp_missing_assets` and stay pending.
- Freeze layout constants (fonts, spacing) to prevent drift; hash template version in payload.
- Change control: cover data changes require dual sign-off (author + supervisor) captured in payload provenance.
- Manifest immutability: once approved, the cover manifest is locked; reopen requests require authorization and create a new archived version.

## 6. Fallback Hierarchy
1. Use toolkit-normalized values from Section 1.
2. Fall back to user profile defaults when toolkit value absent.
3. Prompt manual entry via gateway change queue if both missing.
4. Abort with `section_blocked` if legal identifiers cannot be supplied.

## 7. Sectional Staging & Call-Out Procedures
- Runs only after Section 1; completes before Sections DP and 9.
- Emits `cover_profile_ready` (manifest, hash) for DP/9/FR.
- On `request_case_revision`, rehydrate inputs, regenerate cover, update manifest hash.

## 8. Information Handlers
- **Cover manifest:** `{client_name, case_id, investigator_info, agency_branding, contact_channels, signature_assets, template_hash}`.
- **Asset registry:** Paths/hashes for logos, seals, signatures—validated on ingest.
- **Change queue:** Items requiring manual edits (e.g., missing signature) tracked until resolved.

## 9. Narrative/Copy Blueprint
- No free-form narrative; strictly formatted labels.
- Placeholder tokens (`[REVIEW REQUIRED]`) used only when manual queue entry created.
- Flag unusual casing or mismatched jurisdictions for QA review.

## 10. Dissemination & Intelligence Sharing
- Provide `cover_profile` manifest to Sections DP, 9, FR, and gateway UI.
- Update shared fact graph nodes so branding/credential references stay aligned across sections.
- Receive discrepancy reports (e.g., DP detects signature mismatch) through `cover_profile_issue` signal.
- Maintain version history of manifest for audit (hash + timestamp + approved by).
## 11. Operational & Documentation Alignment
- Authoritative docs:
  - `Sections/section_readme/Section_CP_README.md`
  - Rendering logic: `Sections/section_renderers/section_cp_renderer.py`
  - Toolkit dependencies: `UserProfileManager`, `metadata_tool_v_5.py`
  - SOP references: `dev_tracking/templates/Section_CP_Rebuild_Playbook.md`, `CoreSystem/SOP.md`
- Enforcement: Sync README/SOP whenever payload schema or workflow changes; embed doc version in payload metadata; add tests validating schema against documented contract.

## 12. Implementation To-Do (Section CP)
- [ ] Wire gateway input handling ensuring Section 1 order lock is respected.
- [ ] Implement asset validation + fallback logic tied to parsing maps.
- [ ] Define `section_cp_payload` schema with manifest + QA flags + provenance.
- [ ] Upgrade renderer to consume structured inputs, enforce static layout.
- [ ] Add automated QA checks (branding hash, license verification, signature presence).
- [ ] Add template hash/style-lint enforcement and blocked-phrase tests.
- [ ] Extend tests for rerun on metadata changes, missing assets, manual overrides while enforcing ``max_reruns``.
- [ ] Implement revision-depth guardrails and manifest immutability workflows.
- [ ] Update README/SOP with final architecture, including "Section 1 order immutable" note.
