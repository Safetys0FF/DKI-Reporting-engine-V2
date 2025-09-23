# Section Smoke - Asset Gaps (2025-09-19)

Synthetic run of `run_section_bundle_smoke.py` surfaced the following asset gaps and environment warnings. Populate these before the next regression pass:

## Missing Media Files

- `Tests/_tust bundles/photo_001.jpg`
- `Tests/_tust bundles/photo_002.jpg`
- `Tests/_tust bundles/photo_stakeout_3.png`
- `Tests/_tust bundles/dashcam_clip_01.mp4`
- `Tests/_tust bundles/voice_memo_1.wav`

Without these files, media processing emits "Media file not found" warnings and Section 8 manifests remain sparse. Drop sample assets matching the filenames or adjust the JSON references.

## Optional Dependencies

- **MoviePy** - Install to enable video thumbnail extraction during media analysis (`pip install moviepy`).

## Data Enhancements

- Add subject metadata to the document payloads to avoid Section 5 placeholders (`subject_name`, `record_date`).
- Supply evidence timestamps and routing metadata so Section 8 can build dated timelines; this clears the Section 7 "Missing supporting content" flag.
- Populate manual note fields (`manual_notes.validation`, `manual_notes.routing`) with representative values for each evidence item.

## Next Regression Pass

1. Stage the assets listed above (or update the JSON references to available files).
2. Install MoviePy if video support is required for the test harness.
3. Re-run `run_section_bundle_smoke.py` and archive the refreshed results alongside test evidence for DEESCALATION review.
