# tool_injection_logic_board.py — Frontline + Validation Tool Orchestration

from typing import Dict, List, Any

# === Frontline Extraction Tools ===
from PIL import Image
import pytesseract
import easyocr
from unstructured.partition.pdf import partition_pdf

# === Supplemental DKI Tools ===
from mileage_tool_v_2 import audit_mileage
from northstar_protocol_tool import process_assets
from reverse_continuity_tool import ReverseContinuityTool
from billing_tool_engine import BillingTool
from cochran_match_tool import verify_identity
from metadata_tool_v_5 import process_zip


class ToolInjectionLogic:
    def __init__(self):
        self.reader = easyocr.Reader(['en'])

    # --- Frontline OCR Stack ---
    def run_ocr(self, path: str, file_type: str) -> Dict[str, Any]:
        try:
            if file_type == "image":
                text = pytesseract.image_to_string(Image.open(path))
                if text.strip():
                    return {"engine": "tesseract", "text": text.strip()}
                result = self.reader.readtext(path, detail=0)
                return {"engine": "easyocr", "text": " ".join(result)}
            elif file_type == "pdf":
                elements = partition_pdf(filename=path)
                return {"engine": "unstructured", "text": "\n".join([e.text for e in elements if hasattr(e, 'text')])}
        except Exception as e:
            return {"error": str(e)}

    # --- Injected Validation Stack ---
    def run_validation_suite(self, context: Dict[str, Any]) -> Dict[str, Any]:
        results = {}

        # Mileage Tool
        results["mileage_audit"] = audit_mileage()

        # Continuity Tool
        reverse = ReverseContinuityTool()
        text_blob = context.get("text_blob", "")
        docs = context.get("documents", [])
        assets = context.get("assets", [])
        reverse_ok, reverse_log = reverse.run_validation(text_blob, docs, assets)
        results["reverse_continuity"] = {"ok": reverse_ok, "log": reverse_log}

        # Metadata Tool
        zip_path = context.get("metadata_zip")
        output_dir = context.get("metadata_out_dir", "./metadata_out")
        if zip_path:
            results["metadata_audit"] = process_zip(zip_path, output_dir)

        # Identity Checks
        ids = []
        for subject, candidate in zip(context.get("subjects", []), context.get("candidates", [])):
            ids.append(verify_identity(subject, candidate))
        results["identity_checks"] = ids

        # Asset Classification (Northstar)
        results["northstar"] = process_assets(context.get("assets", []))

        return results


# Example test mode
if __name__ == "__main__":
    engine = ToolInjectionLogic()

    # Sample OCR test
    print("--- OCR Sample ---")
    ocr = engine.run_ocr("./samples/image_01.jpg", "image")
    print(ocr)

    # Sample validation injection
    print("--- Validation Suite ---")
    mock_context = {
        "text_blob": "Subject appeared hours later and entered a different place suddenly.",
        "documents": ["verified subject ID"],
        "assets": [{"id": "img1", "field_time": "2023-11-16T09:00:00", "received_time": "2023-11-16T09:01:00"}],
        "metadata_zip": "./samples/media_bundle.zip",
        "subjects": [{"full_name": "John Doe", "dob": "1980-01-01", "address": "100 Test St"}],
        "candidates": [{"full_name": "Johnathan Doe", "dob": "1980-01-01", "address": "100 Test St", "address_days_overlap": 90, "source": "court"}],
    }
    result = engine.run_validation_suite(mock_context)
    for k, v in result.items():
        print(f"\n{k.upper()}\n", v)
