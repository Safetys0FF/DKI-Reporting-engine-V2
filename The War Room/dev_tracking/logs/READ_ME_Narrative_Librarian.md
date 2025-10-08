# Narrative & Debrief CAN-Bus Integration Plan

## Purpose
Document the exact steps required to wire the cover page, table of contents, and disclosure artifacts into the existing CAN-bus pipeline without disturbing the current Librarian or Mission Debrief behaviour.

## Current State Summary
- **Section Controllers** (F:\The Central Command\The Marshall\Evidence_Checkout\section_controller.py) already emit `section.data.updated` with enriched payloads.
- **Section Frameworks 1–8** now publish/consume via CAN, including CP/DP frameworks in the Analyst deck.
- **The Librarian** (F:\The Central Command\Command Center\Mission Debrief\The Librarian\narrative_assembler.py) subscribes to `section.data.updated` but currently caches only what it needs for narrative assembly.
- **Mission Debrief Manager** (F:\The Central Command\Command Center\Mission Debrief\Debrief\README\mission_debrief_manager.py) still builds cover/TOC/disclosure artifacts from cached manifests instead of the CAN payloads.

## Implementation Steps

### 1. Extend Librarian Cache for CP / TOC / DP
**File**: `F:\The Central Command\Command Center\Mission Debrief\The Librarian\narrative_assembler.py`

1. In `_handle_section_data_updated_signal`, persist the incoming payloads for `section_cp`, `section_toc`, and `section_dp` in a dedicated structure (e.g., `self.section_artifacts`).
2. Ensure existing narrative assembly behaviour stays untouched; this cache is additive.
3. (Optional) add helper accessors, e.g., `get_artifact_payload(section_id)` returning the latest payload.

### 2. Update Mission Debrief Manager to Prefer CAN Payloads
**File**: `F:\The Central Command\Command Center\Mission Debrief\Debrief\README\mission_debrief_manager.py`

1. Inject the Librarian cache (either via constructor parameter or by querying the Librarian module) so `_assemble_artifact_payload` can retrieve CAN-fed versions of cover/TOC/disclosure before falling back to local composition.
2. When CAN data is available, feed it straight into `_compose_cover_page`, `_compose_table_of_contents`, `_compose_disclosure_page` instead of rebuilding them from `base_payload`.
3. Maintain the existing fallback logic so reports can still be composed if the bus cache is empty.

### 3. Emit Bus Signals for Artifact Updates
**File**: same as Step 2 (`mission_debrief_manager.py`)

1. After assembling each artifact, emit a CAN bus event (e.g., `mission_debrief.artifact.updated`) with section ID and payload for downstream exporters.
2. Use the existing `_emit_bus_event` helper to stay consistent with other bus emissions.

### 4. Validation & Regression Checks
- Confirm `section.data.updated` events from CP/DP/Toc path into the Librarian cache via logging.
- Trigger a mission debrief run and ensure cover/TOC/disclosure content reflects the CAN-fed data.
- Verify exporter routines (PDF/DOCX) still receive the expected payloads via the new artifact bus events.
- Regression-test fallback behaviour by clearing the CAN cache and checking that the manager still produces artifacts using its previous logic.

## Notes
- Do **not** modify the Analyst deck versions of CP/DP/TOC frameworks further; all runtime integration happens in the Librarian and Debrief folders listed above.
- Keep changes additive and backwards-compatible to preserve current mission report generation until full validation is complete.
