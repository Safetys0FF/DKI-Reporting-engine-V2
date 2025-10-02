# finalize_pipeline.py

from debrief_manager import DebriefManager
from archive_manager import ArchiveManager
from user_profile import load_user_profile  # assumed utility
from gui_hooks import prompt_user_for_export  # assumed GUI interaction layer
import logging

logger = logging.getLogger(__name__)

def run_finalization(case_number):
    # Step 1: Load archived narrative from local read-only storage
    archive = ArchiveManager()
    report_data = archive.get_case_report(case_number)
    if not report_data:
        logger.error(f"No archived narrative found for case: {case_number}")
        return False

    # Step 2: Prompt user for export options (via GUI)
    export_config = prompt_user_for_export(case_number)
    if not export_config:
        logger.warning("User canceled export configuration.")
        return False

    # Step 3: Load user profile (logo, name, export prefs)
    user_profile = load_user_profile()

    # Step 4: Initialize and execute DebriefManager
    manager = DebriefManager(
        narrative=report_data,
        user_profile=user_profile,
        export_config=export_config
    )

    success = manager.run()
    if success:
        logger.info(f"Report finalized for case {case_number}")
    else:
        logger.error(f"Finalization failed for case {case_number}")

    return success

# Optional CLI entry
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python finalize_pipeline.py <case_number>")
    else:
        run_finalization(sys.argv[1])
