# Section 8 Parsing Map (Investigation Evidence Review / Photo Section)

## Purpose
Deliver the surveillance photo deck and supporting media manifest, showing capture dates, descriptions, and links back to the narrative (Sections 3 & 4) along with custody metadata.

## Data Inputs
| Evidence Element                      | Source Path(s)                                                                                       | Notes |
|--------------------------------------|------------------------------------------------------------------------------------------------------|-------|
| photo_sessions                        | `section4.manifest.windows`, `processed.images.by_session`                                           | Determines “Date of surveillance” headings and photo grouping. |
| media_items (photos/video stills)     | `processed.images`, `processed.videos.thumbnails`                                                     | Supplies file path, capture timestamp, camera metadata. |
| captions / descriptions               | `processed.manual_notes.media_captions`, `toolkit_results.session_summary.media_notes`               | One- to two-sentence description aligned with Section 4 observations. |
| evidence_ids & hashes                 | `processed.metadata.hashes`, `processed.images[].hash`                                                | Displayed for chain-of-custody and export manifest. |
| voice memo transcripts                | `processed.audio.transcripts`, `section4.manifest.voice_memos`                                       | Optional attachments listed alongside photo sessions. |
| validation status                     | `processed.manual_notes.validation`, `toolkit_results.chain_integrity`                                | Indicates media authentication outcome. |
| routing references                    | `processed.manual_notes.routing`, `section3.render_manifest.media_links`                              | Links each media asset back to narrative entries. |

## Toolkit & AI Triggers
- Media processing engine performs face/object detection, EXIF validation, and generates thumbnails.
- OpenAI `content_verification` (post_ocr) – extracts salient details for captions and flags tampering cues.
- OpenAI `chain_integrity` (pre_render) – summarises custody and highlights any breaks.

## UI Checklist
- Ensure each photo entry lists capture date/time, description, and related observation.
- Confirm hashes/custody notes exist for every media asset delivered to the client.
- Remove or flag any media not cleared for disclosure.

## Dependencies
- Section 7 references key media in findings.
- Final report export bundles these assets into the client package and Librarian archive manifest.
