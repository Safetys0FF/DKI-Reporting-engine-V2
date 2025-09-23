from datetime import datetime
import os
import json
import hashlib
from difflib import SequenceMatcher
from PIL import Image
import pytesseract
import easyocr
from unstructured.partition.pdf import partition_pdf

# === Contract-Based Report Type Logic ===
def get_report_config(contract_history):
    def determine_type(history):
        contracts = sorted(history, key=lambda x: x['signed_date'])
        has_investigative = any(c['type'] == "Investigative" for c in contracts)
        has_surveillance = any(c['type'] == "Surveillance" for c in contracts)

        if has_investigative and has_surveillance:
            for i, c in enumerate(contracts):
                if c['type'] == "Surveillance" and any(prev['type'] == "Investigative" for prev in contracts[:i]):
                    return "Hybrid", True
            return "Surveillance", False
        elif has_surveillance:
            return "Surveillance", True
        elif has_investigative:
            return "Investigative", True
        return "Unknown", False

    report_type, contract_order_validated = determine_type(contract_history)

    hybrid_render_order = [
        "2A_case_summary",
        "2B_subject_information",
        "2C_habits_and_POIs",
        "2B_investigative_data",
        "2D_visual_assets",
        "2E_final_planning"
    ]

    report_type_switch = {
        "Investigative": {
            "label": "SECTION 2 – INVESTIGATIVE REQUIREMENTS",
            "billing": "Flat",
            "clause": "no_surveillance",
            "modules": {
                "active": ["investigative_data"],
                "inactive": ["surveillance_logs", "route_plan", "vehicle_id", "photos", "mileage"]
            },
            "effects": {
                "hide": ["2C", "2D"],
                "tag": "Investigation Only"
            }
        },
        "Surveillance": {
            "label": "SECTION 2 – PRE-SURVEILLANCE SUMMARY",
            "billing": "Hourly",
            "clause": "field_hours",
            "modules": {
                "active": ["surveillance_logs", "vehicle_id", "poi_analysis", "photos", "mileage"],
                "inactive": ["investigative_data", "court_lookups"]
            },
            "effects": {
                "render_all": True,
                "tag": "Surveillance Ready"
            },
            "disclaimer": (
                "The following observations were made during physical surveillance activities "
                "conducted by licensed investigators operating within jurisdictional and contractual limits. "
                "This report contains no assumptions regarding subject intent or legal conclusions. "
                "If the case is prepped and not finished: an investigator has been assigned to this case as requested by the client. "
                "That investigator is operating by their own licensing and legal ability under state statutes. "
                "The investigator has been allocated 15 hours of field operation time for this case."
            )
        },
        "Hybrid": {
            "label": "SECTION 2 – HYBRID PREPARATION SUMMARY",
            "billing": "Hybrid",
            "clause": "mixed",
            "modules": {
                "active": ["investigative_data", "surveillance_logs", "vehicle_id", "poi_analysis", "photos", "mileage"],
                "inactive": []
            },
            "effects": {
                "forced_render_order": hybrid_render_order,
                "contract_order_required": True,
                "tag": "Full Stack"
            },
            "disclaimer": (
                "This report includes a combination of documented investigative research and field surveillance observations. "
                "All findings have been timestamped, source-anchored, and reviewed for continuity against the client intake. "
                "No part of this report makes conclusions beyond factual reporting or visual confirmation. "
                "If the case is prepped and not finished: an investigator has been assigned to this case as requested by the client. "
                "That investigator is operating by their own licensing and legal ability under state statutes. "
                "The investigator has been allocated 15 hours of field operation time for this case."
            )
        }
    }

    if report_type == "Hybrid" and not contract_order_validated:
        report_type = "Surveillance"
        log_msg = "Hybrid denied: Surveillance contract not signed after Investigative."
    else:
        log_msg = f"{report_type} mode selected."

    return {
        "report_type": report_type,
        "config": report_type_switch[report_type],
        "log": log_msg
    }

# === Enhanced OCR + Document Processing Functions ===

class OCRProcessor:
    """Enhanced OCR processing with error handling and batch processing"""
    
    def __init__(self):
        self.supported_image_formats = ['.jpg', '.jpeg', '.png', '.tiff', '.bmp', '.gif']
        self.supported_pdf_formats = ['.pdf']
        self.easyocr_reader = None
    
    def _get_easyocr_reader(self):
        """Lazy load EasyOCR reader"""
        if self.easyocr_reader is None:
            self.easyocr_reader = easyocr.Reader(['en'])
        return self.easyocr_reader
    
    def extract_text_from_pdf(self, path, method='unstructured'):
        """Extract text from PDF using multiple methods"""
        if not os.path.exists(path):
            return {"error": f"File not found: {path}", "text": ""}
        
        try:
            if method == 'unstructured':
                elements = partition_pdf(filename=path)
                text = "\n".join([e.text for e in elements if hasattr(e, 'text')])
            else:
                # Fallback method
                text = "PDF processing not available"
            
            return {
                "success": True,
                "text": text,
                "method": method,
                "file_size": os.path.getsize(path)
            }
        except Exception as e:
            return {
                "error": f"PDF extraction failed: {str(e)}",
                "text": "",
                "method": method
            }
    
    def extract_text_from_image(self, img_path, method='tesseract'):
        """Extract text from image using Tesseract or EasyOCR"""
        if not os.path.exists(img_path):
            return {"error": f"File not found: {img_path}", "text": ""}
        
        try:
            if method == 'tesseract':
                image = Image.open(img_path)
                text = pytesseract.image_to_string(image)
            elif method == 'easyocr':
                reader = self._get_easyocr_reader()
                result = reader.readtext(img_path, detail=0)
                text = " ".join(result)
            else:
                return {"error": f"Unknown method: {method}", "text": ""}
            
            return {
                "success": True,
                "text": text,
                "method": method,
                "file_size": os.path.getsize(img_path)
            }
        except Exception as e:
            return {
                "error": f"Image OCR failed: {str(e)}",
                "text": "",
                "method": method
            }
    
    def process_document_batch(self, file_paths, ocr_methods=['tesseract', 'easyocr']):
        """Process multiple documents with different OCR methods"""
        results = {
            "pdfs": {},
            "images": {},
            "errors": [],
            "summary": {
                "total_files": len(file_paths),
                "processed": 0,
                "failed": 0
            }
        }
        
        for file_path in file_paths:
            if not os.path.exists(file_path):
                results["errors"].append(f"File not found: {file_path}")
                continue
            
            file_ext = os.path.splitext(file_path)[1].lower()
            filename = os.path.basename(file_path)
            
            if file_ext in self.supported_pdf_formats:
                pdf_result = self.extract_text_from_pdf(file_path)
                results["pdfs"][filename] = pdf_result
                if pdf_result.get("success"):
                    results["summary"]["processed"] += 1
                else:
                    results["summary"]["failed"] += 1
            
            elif file_ext in self.supported_image_formats:
                image_results = {}
                for method in ocr_methods:
                    img_result = self.extract_text_from_image(file_path, method)
                    image_results[method] = img_result
                
                results["images"][filename] = image_results
                if any(result.get("success") for result in image_results.values()):
                    results["summary"]["processed"] += 1
                else:
                    results["summary"]["failed"] += 1
            
            else:
                results["errors"].append(f"Unsupported file type: {file_ext}")
                results["summary"]["failed"] += 1
        
        return results
    
    def extract_contract_data(self, document_path):
        """Extract contract-specific data from documents"""
        file_ext = os.path.splitext(document_path)[1].lower()
        
        if file_ext in self.supported_pdf_formats:
            result = self.extract_text_from_pdf(document_path)
        elif file_ext in self.supported_image_formats:
            result = self.extract_text_from_image(document_path)
        else:
            return {"error": "Unsupported file type for contract extraction"}
        
        if not result.get("success"):
            return result
        
        text = result["text"]
        
        # Extract contract-specific information
        contract_data = {
            "contract_type": self._extract_contract_type(text),
            "signed_date": self._extract_signed_date(text),
            "client_name": self._extract_client_name(text),
            "investigator_name": self._extract_investigator_name(text),
            "case_number": self._extract_case_number(text),
            "billing_terms": self._extract_billing_terms(text),
            "raw_text": text
        }
        
        return {
            "success": True,
            "contract_data": contract_data,
            "extraction_method": result.get("method", "unknown")
        }
    
    def _extract_contract_type(self, text):
        """Extract contract type from text"""
        text_lower = text.lower()
        if "investigative" in text_lower and "surveillance" in text_lower:
            return "Hybrid"
        elif "surveillance" in text_lower or "field" in text_lower:
            return "Surveillance"
        elif "investigative" in text_lower or "research" in text_lower:
            return "Investigative"
        return "Unknown"
    
    def _extract_signed_date(self, text):
        """Extract signed date from text"""
        import re
        date_patterns = [
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(\d{4}-\d{2}-\d{2})',
            r'(signed.*?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}))'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
    
    def _extract_client_name(self, text):
        """Extract client name from text"""
        import re
        patterns = [
            r'client[:\s]+([A-Za-z\s]+)',
            r'client name[:\s]+([A-Za-z\s]+)',
            r'between\s+([A-Za-z\s]+)\s+and'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None
    
    def _extract_investigator_name(self, text):
        """Extract investigator name from text"""
        import re
        patterns = [
            r'investigator[:\s]+([A-Za-z\s]+)',
            r'agent[:\s]+([A-Za-z\s]+)',
            r'licensed investigator[:\s]+([A-Za-z\s]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None
    
    def _extract_case_number(self, text):
        """Extract case number from text"""
        import re
        patterns = [
            r'case[:\s#]+([A-Za-z0-9-]+)',
            r'file[:\s#]+([A-Za-z0-9-]+)',
            r'reference[:\s#]+([A-Za-z0-9-]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None
    
    def _extract_billing_terms(self, text):
        """Extract billing terms from text"""
        text_lower = text.lower()
        if "flat" in text_lower or "fixed" in text_lower:
            return "Flat"
        elif "hourly" in text_lower or "per hour" in text_lower:
            return "Hourly"
        elif "hybrid" in text_lower or "mixed" in text_lower:
            return "Hybrid"
        return "Unknown"

# Initialize global OCR processor
ocr_processor = OCRProcessor()

# Convenience functions for backward compatibility
def extract_text_from_pdf(path):
    """Legacy function - use OCRProcessor for new code"""
    result = ocr_processor.extract_text_from_pdf(path)
    return result.get("text", "")

def extract_text_from_image(img_path):
    """Legacy function - use OCRProcessor for new code"""
    result = ocr_processor.extract_text_from_image(img_path)
    return result.get("text", "")

def easyocr_text(img_path):
    """Legacy function - use OCRProcessor for new code"""
    result = ocr_processor.extract_text_from_image(img_path, method='easyocr')
    return result.get("text", "")

def process_contract_documents(document_paths):
    """Process multiple contract documents and extract contract data"""
    results = []
    
    for doc_path in document_paths:
        contract_result = ocr_processor.extract_contract_data(doc_path)
        if contract_result.get("success"):
            contract_data = contract_result["contract_data"]
            # Convert to contract history format
            if contract_data["contract_type"] != "Unknown" and contract_data["signed_date"]:
                results.append({
                    "type": contract_data["contract_type"],
                    "signed_date": datetime.strptime(contract_data["signed_date"], "%m/%d/%Y") if "/" in contract_data["signed_date"] else datetime.fromisoformat(contract_data["signed_date"]),
                    "client_name": contract_data["client_name"],
                    "case_number": contract_data["case_number"],
                    "source_file": os.path.basename(doc_path)
                })
    
    return results

# === Example Usage ===
if __name__ == "__main__":
    # Test contract analysis
    contract_history = [
        {"type": "Investigative", "signed_date": datetime(2025, 5, 1)},
        {"type": "Surveillance", "signed_date": datetime(2025, 5, 21)}
    ]

    result = get_report_config(contract_history)
    print("=== Contract Analysis ===")
    print(result["log"])
    print(f"Report Type: {result['report_type']}")
    print(f"Billing: {result['config']['billing']}")
    print()

    # Test OCR processing
    print("=== OCR Processing Examples ===")
    
    # Example 1: Process single document
    # contract_doc = "contract_scan.jpg"
    # if os.path.exists(contract_doc):
    #     contract_data = ocr_processor.extract_contract_data(contract_doc)
    #     if contract_data.get("success"):
    #         print("Contract Data Extracted:")
    #         for key, value in contract_data["contract_data"].items():
    #             if key != "raw_text":
    #                 print(f"  {key}: {value}")
    
    # Example 2: Process multiple documents
    # document_paths = ["contract1.pdf", "contract2.jpg", "surveillance_agreement.png"]
    # batch_results = ocr_processor.process_document_batch(document_paths)
    # print(f"Processed {batch_results['summary']['processed']} files successfully")
    # print(f"Failed: {batch_results['summary']['failed']} files")
    
    # Example 3: Extract contract history from documents
    # contract_docs = ["investigative_contract.pdf", "surveillance_contract.jpg"]
    # extracted_contracts = process_contract_documents(contract_docs)
    # if extracted_contracts:
    #     print("Extracted Contract History:")
    #     for contract in extracted_contracts:
    #         print(f"  {contract['type']} - {contract['signed_date']} - {contract['client_name']}")
    
    # Example 4: Compare OCR methods
    # image_file = "contract_scan.jpg"
    # if os.path.exists(image_file):
    #     tesseract_result = ocr_processor.extract_text_from_image(image_file, 'tesseract')
    #     easyocr_result = ocr_processor.extract_text_from_image(image_file, 'easyocr')
    #     
    #     print("Tesseract Result:")
    #     print(tesseract_result.get("text", "Failed")[:100] + "...")
    #     print("EasyOCR Result:")
    #     print(easyocr_result.get("text", "Failed")[:100] + "...")
    
    print("OCR tools ready for use!")
    print("Uncomment the examples above to test with actual documents.")