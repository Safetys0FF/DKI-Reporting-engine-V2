# archive_pipeline.py

from archive_manager import ArchiveManager
from librarian import NarrativeAssembler
from gui_hooks import get_case_number, notify_user  # assumed utility
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def run_archival(structured_narrative, case_number=None):
    # Step 1: Pull case number from GUI if not passed
    case_number = case_number or get_case_number()
    if not case_number:
        logger.error("No case number provided. Aborting archival.")
        return False

    # Step 2: Assemble narrative (optional if already assembled)
    assembler = NarrativeAssembler()
    narrative = assembler.assemble_all(structured_narrative)  # assume method exists

    # Step 3: Archive narrative bundle
    archive = ArchiveManager()
    success = archive.store_final_report(case_number, narrative)

    if success:
        logger.info(f"Narrative for case {case_number} archived successfully.")
        notify_user(f"Case {case_number} saved to archive.")
    else:
        logger.error(f"Archival failed for case {case_number}.")
        notify_user(f"Failed to archive case {case_number}.")

    return success

# Optional CLI entry
if __name__ == "__main__":
    import json, sys
    if len(sys.argv) < 3:
        print("Usage: python archive_pipeline.py <case_number> <path_to_narrative.json>")
    else:
        with open(sys.argv[2], 'r', encoding='utf-8') as f:
            data = json.load(f)
        run_archival(data, sys.argv[1])
