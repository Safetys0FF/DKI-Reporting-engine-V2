# HANDSHAKE — SYSTEM SCHEMATIC + CHANGE DISPATCH REQUEST

**Date:** 2025-09-18  
**From:** USER  
**To:** POWER Agent  
**Task:** Generate a full schematic of the current directory and list all system changes in a dispatch file

## Directives
1. Scan and map the entire directory tree under:
   `F:\DKI-Report-Engine\Report Engine\`
2. Generate a `SYSTEM_SCHEMATIC.md` with:
   - Directory tree structure
   - File names + relative paths
   - Timestamps of last modification
   - Ownership tags (if applicable)
3. Compare against the last logged schematic (if available).
4. Produce a `CHANGE_DISPATCH.md` with:
   - New files added
   - Files removed
   - Files renamed or relocated
   - Folders added/removed
   - Summary of path realignments
5. Store both files in:
   `F:\DKI-Report-Engine\Report Engine\dev_tracking\archives`
6. Emit a `HANDSHAKE_ACK.md` confirming schematic and dispatch creation.
7. Notify NETWORK and DEESCALATION by posting a reference log in:
   `F:\DKI-Report-Engine\Report Engine\dev_tracking\Handshakes`

## Output Requirements
- `SYSTEM_SCHEMATIC_2025-09-18.md`
- `CHANGE_DISPATCH_2025-09-18.md`
- Both must be read-only for audit.
