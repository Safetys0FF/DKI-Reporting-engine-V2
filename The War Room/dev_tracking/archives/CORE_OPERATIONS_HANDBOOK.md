# CORE OPERATIONS HANDBOOK (Read-Only)

**Scope**
- SOPs, blueprints, PRDs, build plan, and cross‑agent handoff protocol for the DKI Engine.
- Includes authoritative file addresses for core configs, fallback references, and toolkit components.

**Agent Roles**
- POWER Agent: Owns core engine functions and 12 core configuration files; implements new features and config hygiene.
- NETWORK Agent: Owns integrations, API keys, transport, repository/data sync, and network resilience.
- DEESCALATION Agent: Owns incident/error-analysis flows, risk reporting, and regression planning.

**Authoritative File Sets**
- Core Engine (12 files):
  - `C:\Users\DTKra\OneDrive\Desktop\DKI Engine\logic\1. Section CP.txt`
  - `C:\Users\DTKra\OneDrive\Desktop\DKI Engine\logic\2. Section TOC.txt`
  - `C:\Users\DTKra\OneDrive\Desktop\DKI Engine\logic\3. Section 1=gateway controller.txt`
  - `C:\Users\DTKra\OneDrive\Desktop\DKI Engine\logic\4. Section 2.txt`
  - `C:\Users\DTKra\OneDrive\Desktop\DKI Engine\logic\5. Section 3.txt`
  - `C:\Users\DTKra\OneDrive\Desktop\DKI Engine\logic\6. Section 4.txt`
  - `C:\Users\DTKra\OneDrive\Desktop\DKI Engine\logic\7. Section 5.txt`
  - `C:\Users\DTKra\OneDrive\Desktop\DKI Engine\logic\8. Section 6 - Billing Summary.txt`
  - `C:\Users\DTKra\OneDrive\Desktop\DKI Engine\logic\9. Section 7.txt`
  - `C:\Users\DTKra\OneDrive\Desktop\DKI Engine\logic\10. Section 8.txt`
  - `C:\Users\DTKra\OneDrive\Desktop\DKI Engine\logic\11. Section DP.txt`
  - `C:\Users\DTKra\OneDrive\Desktop\DKI Engine\logic\12. Final Assembly.txt`

- Fallback Logic References:
  - `C:\Users\DTKra\OneDrive\Desktop\DKI Engine\logic\Section 1 - Investigation Objectives (updated).txt`
  - `C:\Users\DTKra\OneDrive\Desktop\DKI Engine\logic\Section 1 - Investigation Objectives with switches.txt`
  - `C:\Users\DTKra\OneDrive\Desktop\DKI Engine\logic\Section 2 - Presurveillance Logic.txt`
  - `C:\Users\DTKra\OneDrive\Desktop\DKI Engine\logic\section 2 - pres-urveillance.txt`
  - `C:\Users\DTKra\OneDrive\Desktop\DKI Engine\logic\section 3 - data logs.txt`
  - `C:\Users\DTKra\OneDrive\Desktop\DKI Engine\logic\Section 3 - Surveillance Reports - Dialy Logs.txt`
  - `C:\Users\DTKra\OneDrive\Desktop\DKI Engine\logic\Section 4 - Review of Surveillance Sessions.txt`
  - `C:\Users\DTKra\OneDrive\Desktop\DKI Engine\logic\Section 4 - review of surveillance.txt`
  - `C:\Users\DTKra\OneDrive\Desktop\DKI Engine\logic\Section 5 - review of documents Logic Overview.txt`
  - `C:\Users\DTKra\OneDrive\Desktop\DKI Engine\logic\Section 5 - Review of Supporting Docs.txt`
  - `C:\Users\DTKra\OneDrive\Desktop\DKI Engine\logic\section 6 - BILLING SUMMARY.txt`

- Toolkit Components and Renderers:
  - `C:\Users\DTKra\OneDrive\Desktop\DKI Engine\logic\section_cp_renderer.py`
  - `C:\Users\DTKra\OneDrive\Desktop\DKI Engine\logic\section_toc_renderer.py`
  - `C:\Users\DTKra\OneDrive\Desktop\DKI Engine\logic\section_1_gateway.py`
  - `C:\Users\DTKra\OneDrive\Desktop\DKI Engine\logic\section_2_renderer.py`
  - `C:\Users\DTKra\OneDrive\Desktop\DKI Engine\logic\section_3_renderer.py`
  - `C:\Users\DTKra\OneDrive\Desktop\DKI Engine\logic\section_4_renderer.py`
  - `C:\Users\DTKra\OneDrive\Desktop\DKI Engine\logic\section_5_renderer.py`
  - `C:\Users\DTKra\OneDrive\Desktop\DKI Engine\logic\section_6_renderer.py`
  - `C:\Users\DTKra\OneDrive\Desktop\DKI Engine\logic\section_7_renderer.py`
  - `C:\Users\DTKra\OneDrive\Desktop\DKI Engine\logic\section_8_renderer.py`
  - `C:\Users\DTKra\OneDrive\Desktop\DKI Engine\logic\section_9_renderer.py`
  - `C:\Users\DTKra\OneDrive\Desktop\DKI Engine\logic\TOOLBOX.txt`
  - `C:\Users\DTKra\OneDrive\Desktop\DKI Engine\logic\billing_tool_engine.py`
  - `C:\Users\DTKra\OneDrive\Desktop\DKI Engine\logic\cochran_match_tool.py`
  - `C:\Users\DTKra\OneDrive\Desktop\DKI Engine\logic\metadata_tool_v_5.py`
  - `C:\Users\DTKra\OneDrive\Desktop\DKI Engine\logic\mileage_tool_v_2.py`
  - `C:\Users\DTKra\OneDrive\Desktop\DKI Engine\logic\northstar_protocol_tool.py`

**Daily SOP**
- Start-of-day Review: Read Handshakes/ plus each agent folder. Confirm directives and blockers. Create `dev_tracking/DAILY_HANDOFFS_YYYY-MM-DD.md`.
- Pre-change: Review last 3-day analysis, cross-check fallback logic, draft recommendations in your agent folder.
- Implement: Apply surgical changes aligned with PRDs. Keep scope tight.
- Post-change: Record what/why/where/next in a change record, open handshakes, place per-agent notes with TODOs.
- Handoff: Send per-agent handoff files, wait for ACKs in Handshakes/ before dependent work.

**Blueprint**
- Gateway Controller orchestrates report type and section order.
- Unified Toolkit (MasterToolKitEngine.run_all) executes before each section; results stored as `section_context.unified_results`.
- Section Renderers generate render models; Final Assembly compiles approved sections.
- Media Engine augments Section 8; exporters produce PDFs/zips.

**PRD Essentials**
- Consistency: Single `section_id`, one `logic_switches` and `callbox_endpoints` per core file; consistent handler naming.
- Resilience: Toolkit/renderers degrade gracefully if optional integrations are unavailable; log clearly.
- Documentation: Every dependent change has a handshake and per-agent handoff note.
- 3‑Day Review: Consider today/yesterday/day-before context in dev_tracking.

**Build Plan**
- Run: `python run_dki_engine.py` or `python working_dki_engine.py`.
- Install: `pip install -r requirements.txt` (ensure `requirements_installed.flag`).
- Package: `python build_executable.py` or `make` (see `DKI_Engine.spec`).
- Installer: `python create_installer.py` (see BUILD_BLUEPRINT.md / QUICK_START.md).

**Handoff Protocol**
- Create: `dev_tracking/Handshakes/HANDSHAKE_YYYY-MM-DD_<FROM>_to_<TO>.md`.
- Place per-agent notes:
  - POWER → `dev_tracking/agent_1_POWER_CODING/ASSIGNMENTS_YYYY-MM-DD.md`
  - FEATURES → `dev_tracking/agent_2_NETWORK_CODING/REQUESTS_YYYY-MM-DD.md`
  - MODERATOR → `dev_tracking/agent_3_DEESCALATION_CODING/REVIEW_YYYY-MM-DD.md`
- Receiving agents add: ACK in Handshakes/ and local README acceptance.

**References**
- `dev_tracking/CORE_ENGINE_INDEX_*.md`, `dev_tracking/CORE_ENGINE_FALLBACK_INDEX_*.md`, `dev_tracking/TOOLKIT_COMPONENTS_INDEX_*.md`.

