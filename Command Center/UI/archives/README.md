# Archived UI Assets

This directory tracks legacy GUI adapters that have been superseded by the
refactored Enhanced GUI. The live application now boots directly through
`Command Center/UI/enhanced_functional_gui.py` and uses the inline CAN bus
bootstrap rather than the legacy `central_plugin` facade.

---

## Archived Items

**October 10, 2025 - Major Cleanup:**
- `Enhanced_GUI_old/` – Duplicate configs, empty page files (cases.py, home.py, etc.), test files. Replaced by modular components system.
- Deleted: `Test Plans/gui support files/` – 21+ duplicate main application files (gui_main_application legacy/clean/original versions, extracted folders, zips). Valuable component files extracted to `UI/components/` before deletion.

**Earlier Archives:**
- `Command Center/Start Menu/Run Time/central_plugin.py` – launcher copy of the legacy plugin kept to document the old start-menu wiring.

---

## Current Structure

**Live Entry Point:** `Command Center/UI/enhanced_functional_gui.py` (3400+ lines)  
**Compatibility Launcher:** `Command Center/UI/gui_main_application.py` (imports from enhanced_functional_gui)  
**Modular Components:** `Command Center/UI/components/` (9 reusable widgets)

No runtime code should import from archived paths; they remain purely for audit history and can be removed once downstream scripts have been audited.
