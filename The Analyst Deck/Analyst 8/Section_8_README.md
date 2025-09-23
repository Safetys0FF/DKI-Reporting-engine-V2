# Section 8 – Photo / Evidence Index Guide

## Overview
Section 8 consolidates all photo, video, and audio evidence gathered during the case. It groups assets by surveillance date, enforces minimum quality thresholds, reconciles timestamps with Section 3 logs, and supplements entries with geolocation context. The renderer also integrates voice memo clips so audio evidence appears alongside visual artifacts.

## Required Inputs & Extraction Workflow
- **Media Processing Engine:** `MediaProcessingEngine.process_media_batch()` analyzes images, videos, and audio. It produces metadata (dimensions, EXIF, GPS, processing timestamps, speech segments, audio features) consumed here.
- **Voice Transcription Utility:** `voice_transcription.py` (Whisper + soundfile/ffmpeg) transcribes standalone audio and video audio tracks; Section 8 renders summarized transcripts for each clip.
- **Toolkit Cache:** `MasterToolKitEngine` provides lookup caches, data policies, and geocoder keys. If Google Maps keys are available, the renderer attempts reverse geocoding via `smart_lookup` or `geocoding_util` for “Observed near…” statements.
- **Section References:** `previous_sections['section_3']` and `['section_4']` supply narrative context; relevance filters ensure only media tied to logged events appear.

## Data Handling & Filtering
- `_collect_media()` gathers normalized records for images, videos, and audio. Each item stores file hash, timestamps, metadata, and any toolkit annotations.
- `_filter_low_quality()` removes images below resolution thresholds (640x480) and skips duplicates.
- `_dedupe_items()` guards against near-duplicate captures within a narrow time window.
- `_is_relevant()` requires alignment with Section 3/4 continuity (timestamp overlap) before media appears in the index.
- Groups items by capture date, listing photos first, then videos, then audio memos for each day. Manual notes from UI prompts attach to matching entries.

## Cross-Reference & Validation
- Media IDs and timestamps are used by Section 3 (internal sidebar) and Section 4 narratives to confirm evidence support.
- Reverse geocoding integrates with Section 2 (planning) for location validation; if keys are missing, placeholders remind reviewers to verify addresses manually.
- Billing module can reference media counts (photos/videos/audio) to allocate documentation costs in Section 6.

## Reporting Expectations
- Present a daily index: “DATE OF SURVEILLANCE: …” followed by numbered photo, video, and audio entries with concise descriptions.
- Highlight manual investigator notes and audio transcript summaries, ensuring sensitive data is handled according to policies.
- Avoid exposing raw file paths; rely on descriptive names and metadata.

## Inter-Section & Gateway Flow
- Output manifest lists counts per date (`photos`, `videos`, `audio`) so the gateway and final assembly know how many panels to render.
- When approvals occur, the gateway archives associated media references for chain-of-custody tracking.
- Section 8 does not transcode media itself; exporters rely on the manifest to embed thumbnails or link to external evidence packages.

## Presentation Guidelines
- Maintain 2x2 grid layout expectation for exporters; text fallback lists entries in order.
- Use “Observed near …” phrasing for GPS-derived locations, falling back to field notes when reverse geocoding is unavailable.
- Audio memo entries should note language and duration alongside transcript summaries to guide reviewers.
