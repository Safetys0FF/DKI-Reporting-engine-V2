"""
Section 3 Unified Toolset Script
Integrates OCR (Tesseract → EasyOCR → Unstructured) with existing local tools:
- Cochran Identity Match
- Northstar Protocol Classification
- Reverse Continuity
- Metadata v5
- Mileage v2
"""

import os
import json

# OCR imports
try:
    from PIL import Image
    import pytesseract
    import easyocr
    from unstructured.partition.pdf import partition_pdf
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

# --- OCR Helper Functions ---
def extract_text_from_image(img_path):
    try:
        image = Image.open(img_path)
        return pytesseract.image_to_string(image)
    except Exception as e:
        return f"Tesseract failed: {e}"

def easyocr_text(img_path):
    try:
        reader = easyocr.Reader(['en'])
        result = reader.readtext(img_path, detail=0)
        return " ".join(result)
    except Exception as e:
        return f"EasyOCR failed: {e}"

def extract_text_from_pdf(path):
    try:
        elements = partition_pdf(filename=path)
        return "\n".join([e.text for e in elements if hasattr(e, 'text')])
    except Exception as e:
        return f"Unstructured failed: {e}"

def run_local_ocr(path, file_type="image"):
    """Run OCR in priority order: Tesseract → EasyOCR → Unstructured"""
    results = {}
    if not OCR_AVAILABLE:
        return {"status": "OCR not available"}

    try:
        if file_type == "image":
            text = extract_text_from_image(path)
            if text and "failed" not in text.lower():
                results["tesseract"] = text
                return results
            text = easyocr_text(path)
            if text and "failed" not in text.lower():
                results["easyocr"] = text
                return results
        text = extract_text_from_pdf(path)
        if text and "failed" not in text.lower():
            results["unstructured"] = text
            return results
    except Exception as e:
        results["error"] = str(e)

    return results or {"status": "unrecoverable"}


# --- Integrated Tool Runner ---
def run_section3_tools(context, media_context, log_fields):
    from cochran_match_tool import verify_identity
    from northstar_protocol_tool import process_assets
    from reverse_continuity_tool import ReverseContinuityTool
    from metadata_tool_v_5 import process_zip
    from mileage_tool_v_2 import audit_mileage

    results = {}

    # Identity (Cochran)
    identity_checks = []
    for subject in context.get("subject_manifest", []):
        sid = subject.get("id") or subject.get("subject_id")
        candidate = context.get("toolkit_results", {}).get("identity_candidates", {}).get(sid)
        if candidate:
            identity_checks.append({"subject_id": sid, "result": verify_identity(subject, candidate)})
    results["identity_checks"] = identity_checks

    # Northstar
    image_assets = media_context.get("media_index", {}).get("images", {})
    assets = []
    for mid, meta in image_assets.items():
        if meta.get("captured_at") and meta.get("received_time"):
            assets.append({
                "id": mid,
                "field_time": str(meta.get("captured_at")),
                "received_time": str(meta.get("received_time")),
                "tags": meta.get("tags", [])
            })
    results["northstar"] = process_assets(assets) if assets else {"status": "SKIPPED"}

    # Reverse Continuity
    reverse_tool = ReverseContinuityTool()
    text_blob = "\n".join(filter(None, [
        log_fields.get("date_block"),
        log_fields.get("time_logs"),
        log_fields.get("activities_observed")
    ]))
    reverse_ok, reverse_log = reverse_tool.run_validation(text_blob, [], [])
    results["reverse_continuity"] = {"ok": reverse_ok, "log": reverse_log}

    # Metadata v5
    metadata_zip = context.get("media_bundle_zip")
    results["metadata_audit"] = process_zip(metadata_zip, "./metadata_out") if metadata_zip else {"status": "SKIPPED"}

    # Mileage v2
    results["mileage_audit"] = audit_mileage()

    # OCR (local)
    ocr_results = {}
    pdfs = context.get("planning_manifest", {}).get("pdf_documents", [])
    imgs = context.get("planning_manifest", {}).get("image_documents", [])

    for img in imgs:
        if os.path.exists(img):
            ocr_results[f"image_{os.path.basename(img)}"] = run_local_ocr(img, "image")

    for pdf in pdfs:
        if os.path.exists(pdf):
            ocr_results[f"pdf_{os.path.basename(pdf)}"] = run_local_ocr(pdf, "pdf")

    results["ocr_results"] = ocr_results

    return results
