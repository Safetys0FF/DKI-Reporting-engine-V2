# POWER Agent Change Note - 2025-09-18

- DocumentProcessor: refreshed OCR availability after lazy loads, merged processing methods without overwriting, surfaced `ocr_results` and `scan_results.ocr_text` for downstream consumers.
- EvidencePipeline: introduced manifest creation, routing plan generation, and batch normalization so evidence cache uploads feed the processor consistently.
- Main application UI: updated `process_files` to run through the new pipeline, capture warnings, and reuse normalized paths for media analysis.
- Regression coverage: added `test_mixed_media_pipeline.py` harness; `python -m compileall` on core modules and the mixed-media test pass. `test_simple_report.py` still depends on optional `moviepy` (unchanged).
