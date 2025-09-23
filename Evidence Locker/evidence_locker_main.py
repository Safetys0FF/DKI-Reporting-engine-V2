# evidence_locker_main.py

import os
import logging
from pathlib import Path
import json
from datetime import datetime
from typing import Dict, List, Any, Optional

# Heavyweight toolkits
try:
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

try:
    from moviepy.editor import VideoFileClip
    VIDEO_AVAILABLE = True
except ImportError:
    VIDEO_AVAILABLE = False

try:
    from unstructured.partition.auto import partition
    UNSTRUCTURED_AVAILABLE = True
except ImportError:
    UNSTRUCTURED_AVAILABLE = False

# System Controller Interfaces (to be injected)
ECC = None
GATEWAY = None

logger = logging.getLogger("EvidenceLocker")
logging.basicConfig(level=logging.INFO)


class EvidenceLocker:
    def __init__(self, ecc=None, gateway=None, bus=None):
        global ECC, GATEWAY
        ECC = ecc
        GATEWAY = gateway
        self.bus = bus

        # Initialize core systems
        self.evidence_index = {}
        self.evidence_classes = {}
        self.processing_log = []
        
        # Initialize with bus if available
        if bus:
            self.initialize_with_bus(bus)
        elif ecc:
            # Fallback to direct ECC registration for backward compatibility
            self.initialize_with_ecc(ecc)
        
        logger.info("[EVIDENCE] Evidence Locker initialized with Central Command architecture")

    def store(self, file_info: Dict[str, Any]) -> Dict[str, Any]:
        """Store evidence metadata and trigger processing"""
        try:
            if not isinstance(file_info, dict):
                raise ValueError("file_info must be a dictionary")
            file_path = file_info.get("path") or file_info.get("file_path")
            if not file_path:
                raise ValueError("file_info must include 'path' or 'file_path'")
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
            evidence_id = self.scan_file(file_path)
            if not evidence_id:
                raise RuntimeError("Failed to register evidence")
            record = self.evidence_index.get(evidence_id, {})
            record.update({
                "file_path": file_path,
                "metadata": file_info,
                "stored_at": datetime.now().isoformat()
            })
            self.evidence_index[evidence_id] = record
            if self.bus:
                self.bus.emit("evidence.stored", {
                    "evidence_id": evidence_id,
                    "file_path": file_path,
                    "metadata": file_info,
                    "timestamp": datetime.now().isoformat()
                })
            logger.info(f"[EVIDENCE] Stored: {evidence_id}")
            return {
                "status": "stored",
                "evidence_id": evidence_id,
                "file_path": file_path
            }
        except Exception as e:
            logger.error(f"Failed to store evidence: {e}")
            return {"status": "error", "error": str(e)}

    
    def initialize_with_bus(self, bus):
        """Initialize Evidence Locker with Central Command Bus"""
        try:
            self.bus = bus
            
            # Register signal handlers with bus
            bus.register_signal("evidence.scan", self.scan_file)
            bus.register_signal("evidence.classify", self.classify_evidence)
            bus.register_signal("evidence.index", self.index_evidence)
            bus.register_signal("evidence.process_comprehensive", self.process_evidence_comprehensive)
            
            logger.info("[EVIDENCE] Evidence Locker registered with Central Command Bus")
            
        except Exception as e:
            logger.error(f"Failed to initialize with bus: {e}")
    
    def initialize_with_ecc(self, ecc):
        """Fallback initialization with ECC (backward compatibility)"""
        try:
            if hasattr(ecc, 'register_signal'):
                ecc.register_signal("evidence.scan", self.scan_file)
                ecc.register_signal("evidence.classify", self.classify_evidence)
                ecc.register_signal("evidence.index", self.index_evidence)
                logger.info("[EVIDENCE] Evidence Locker registered with ECC (fallback)")
        except Exception as e:
            logger.error(f"Failed to initialize with ECC: {e}")

    def scan_file(self, file_path):
        """Analyze and register evidence using Central Command architecture"""
        logger.info(f"[SCAN] Scanning file: {file_path}")
        
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return None

        # Classify evidence (only labeling/tagging, not section assignment)
        classification = self.classify_evidence(file_path)
        section_hint = classification.get("assigned_section", "unassigned")

        # Index evidence with classification
        evidence_id = self.index_evidence(file_path, classification)
        
        # Log processing
        self.processing_log.append({
            "timestamp": datetime.now().isoformat(),
            "file_path": file_path,
            "section_hint": section_hint,
            "evidence_id": evidence_id,
            "classification": classification
        })

        # HANDOFF TO GATEWAY CONTROLLER (let ECC decide section assignment)
        self._handoff_to_gateway(file_path, evidence_id, section_hint, classification)

        # Emit evidence tagged event for ECC/Gateway
        if hasattr(self, "bus") and self.bus:
            self.bus.emit("evidence.tagged", {
                "evidence_id": evidence_id,
                "file_path": file_path,
                "tags": classification.get("tags", []),
                "section_hint": section_hint
            })

        logger.info(f"[EVIDENCE] File {file_path} classified and indexed as {evidence_id} (section hint: {section_hint})")
        return evidence_id

    def classify_evidence(self, file_path):
        """Classify evidence based on file type and content"""
        file_ext = Path(file_path).suffix.lower()
        
        # Basic classification logic
        if file_ext in ['.pdf', '.doc', '.docx', '.txt']:
            return {"assigned_section": "section_1", "evidence_type": "document"}
        elif file_ext in ['.jpg', '.jpeg', '.png', '.bmp']:
            return {"assigned_section": "section_8", "evidence_type": "image"}
        elif file_ext in ['.mp4', '.avi', '.mov', '.wmv']:
            return {"assigned_section": "section_8", "evidence_type": "video"}
        elif file_ext in ['.mp3', '.wav', '.m4a']:
            return {"assigned_section": "section_8", "evidence_type": "audio"}
        else:
            return {"assigned_section": "unassigned", "evidence_type": "unknown"}

    def index_evidence(self, file_path, classification):
        """Index evidence in the Central Command system"""
        evidence_id = f"evidence_{len(self.evidence_index) + 1:04d}"
        
        self.evidence_index[evidence_id] = {
            "file_path": file_path,
            "classification": classification,
            "timestamp": datetime.now().isoformat(),
            "status": "indexed"
        }
        
        return evidence_id

    def extract_text_from_image(self, file_path):
        """Use Tesseract OCR to extract text"""
        if not OCR_AVAILABLE:
            logger.warning("OCR not available - pytesseract not installed")
            return ""
            
        try:
            text = pytesseract.image_to_string(file_path)
            logger.info(f"[OCR] Extracted text from {file_path}: {text[:100]}")
            return text
        except Exception as e:
            logger.error(f"OCR failed: {e}")
            return ""

    def extract_frames_from_video(self, file_path):
        """Use moviepy to get duration and key frames"""
        if not VIDEO_AVAILABLE:
            logger.warning("Video processing not available - moviepy not installed")
            return {}
            
        try:
            clip = VideoFileClip(file_path)
            duration = clip.duration
            logger.info(f"[VIDEO] Video {file_path} duration: {duration:.2f}s")
            return {"duration": duration}
        except Exception as e:
            logger.error(f"Video analysis failed: {e}")
            return {}

    def extract_structure_from_document(self, file_path):
        """Use unstructured to extract document layout"""
        if not UNSTRUCTURED_AVAILABLE:
            logger.warning("Document structure extraction not available - unstructured not installed")
            return []
            
        try:
            elements = partition(filename=file_path)
            logger.info(f"[DOC] Extracted {len(elements)} structural blocks from {file_path}")
            return elements
        except Exception as e:
            logger.error(f"Structure extraction failed: {e}")
            return []

    def build_manifest(self, output_path, case_id=None):
        """Build case manifest for Central Command system"""
        manifest = {
            "case_id": case_id or f"case_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "timestamp": datetime.now().isoformat(),
            "evidence_count": len(self.evidence_index),
            "evidence_index": self.evidence_index,
            "processing_log": self.processing_log,
            "system_status": {
                "ocr_available": OCR_AVAILABLE,
                "video_available": VIDEO_AVAILABLE,
                "unstructured_available": UNSTRUCTURED_AVAILABLE
            }
        }
        
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w') as f:
                json.dump(manifest, f, indent=2)
            logger.info(f"[MANIFEST] Saved manifest to {output_path}")
            return manifest
        except Exception as e:
            logger.error(f"Failed to save manifest: {e}")
            return None

    def process_evidence_comprehensive(self, file_path: str) -> Dict[str, Any]:
        """Comprehensive evidence processing using all available OCR tools"""
        try:
            file_ext = os.path.splitext(file_path)[1].lower()
            processing_result = {
                'file_path': file_path,
                'file_type': file_ext,
                'processed_at': datetime.now().isoformat(),
                'ocr_text': '',
                'video_analysis': {},
                'document_structure': [],
                'classification': {},
                'tools_used': []
            }
            
            # OCR Processing for images and PDFs
            if file_ext in ['.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.pdf']:
                if OCR_AVAILABLE:
                    ocr_text = self.extract_text_from_image(file_path)
                    processing_result['ocr_text'] = ocr_text
                    processing_result['tools_used'].append('tesseract')
                    logger.info(f"[OCR] Processed {file_path}")
            
            # Video Analysis
            if file_ext in ['.mp4', '.avi', '.mov', '.wmv']:
                if VIDEO_AVAILABLE:
                    video_analysis = self.extract_frames_from_video(file_path)
                    processing_result['video_analysis'] = video_analysis
                    processing_result['tools_used'].append('moviepy')
                    logger.info(f"[VIDEO] Analyzed {file_path}")
            
            # Document Structure Analysis
            if file_ext in ['.pdf', '.docx', '.doc', '.txt']:
                if UNSTRUCTURED_AVAILABLE:
                    document_structure = self.extract_structure_from_document(file_path)
                    processing_result['document_structure'] = document_structure
                    processing_result['tools_used'].append('unstructured')
                    logger.info(f"[DOC] Structure extracted from {file_path}")
            
            # Auto-classification based on content
            classification = self.classify_evidence(file_path)
            processing_result['classification'] = classification
            
            # Index the evidence
            evidence_id = self.index_evidence(file_path, classification)
            processing_result['evidence_id'] = evidence_id
            
            # Log the processing
            self.processing_log.append({
                'timestamp': datetime.now().isoformat(),
                'file_path': file_path,
                'evidence_id': evidence_id,
                'tools_used': processing_result['tools_used'],
                'status': 'processed'
            })
            
            logger.info(f"[EVIDENCE] Comprehensive processing completed for {file_path}")
            return processing_result
            
        except Exception as e:
            logger.error(f"Comprehensive processing failed for {file_path}: {e}")
            return {'error': str(e), 'file_path': file_path}
    
    def get_status(self):
        """Get Evidence Locker status for Central Command"""
        return {
            "evidence_count": len(self.evidence_index),
            "processing_log_count": len(self.processing_log),
            "capabilities": {
                "ocr": OCR_AVAILABLE,
                "video": VIDEO_AVAILABLE,
                "unstructured": UNSTRUCTURED_AVAILABLE
            },
            "last_activity": self.processing_log[-1]["timestamp"] if self.processing_log else None
        }
    
    def _call_out_to_ecc(self, operation: str, data: Dict[str, Any]) -> bool:
        """Call out to ECC for permission to perform operation"""
        try:
            # Use bus if available, otherwise fallback to direct ECC
            if self.bus:
                call_out_data = {
                    "operation": operation,
                    "source": "evidence_locker_main",
                    "data": data,
                    "timestamp": datetime.now().isoformat()
                }
                self.bus.emit("evidence_locker.call_out", call_out_data)
                logger.info(f" Called out via bus for operation: {operation}")
                return True
            elif ECC and hasattr(ECC, 'emit'):
                call_out_data = {
                    "operation": operation,
                    "source": "evidence_locker_main",
                    "data": data,
                    "timestamp": datetime.now().isoformat()
                }
                ECC.emit("evidence_locker.call_out", call_out_data)
                logger.info(f" Called out to ECC for operation: {operation}")
                return True
            else:
                logger.warning("Neither bus nor ECC available for call-out")
                return False
                
        except Exception as e:
            logger.error(f"Failed to call out: {e}")
            return False
    
    def _wait_for_ecc_confirm(self, timeout: int = 30) -> bool:
        """Wait for ECC confirmation"""
        try:
            # In a real implementation, this would wait for ECC response
            # For now, we'll simulate immediate confirmation
            logger.info("Waiting for ECC confirmation...")
            # Simulate confirmation delay
            import time
            time.sleep(0.1)  # Brief delay to simulate processing
            logger.info("ECC confirmation received")
            return True
            
        except Exception as e:
            logger.error(f"ECC confirmation timeout or error: {e}")
            return False
    
    def _send_message(self, message_type: str, data: Dict[str, Any]) -> bool:
        """Send message via bus or ECC"""
        try:
            message_data = {
                "message_type": message_type,
                "source": "evidence_locker_main",
                "data": data,
                "timestamp": datetime.now().isoformat()
            }
            
            # Use bus if available, otherwise fallback to direct ECC
            if self.bus:
                self.bus.emit(f"evidence_locker.{message_type}", message_data)
                logger.info(f" Sent message via bus: {message_type}")
                return True
            elif ECC and hasattr(ECC, 'emit'):
                ECC.emit(f"evidence_locker.{message_type}", message_data)
                logger.info(f" Sent message to ECC: {message_type}")
                return True
            else:
                logger.warning("Neither bus nor ECC available for message sending")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return False
    
    def _send_accept_signal(self, operation: str) -> bool:
        """Send accept signal via bus or ECC"""
        try:
            accept_data = {
                "operation": operation,
                "source": "evidence_locker_main",
                "status": "accepted",
                "timestamp": datetime.now().isoformat()
            }
            
            # Use bus if available, otherwise fallback to direct ECC
            if self.bus:
                self.bus.emit("evidence_locker.accept", accept_data)
                logger.info(f"Sent accept signal via bus for operation: {operation}")
                return True
            elif ECC and hasattr(ECC, 'emit'):
                ECC.emit("evidence_locker.accept", accept_data)
                logger.info(f"Sent accept signal to ECC for operation: {operation}")
                return True
            else:
                logger.warning("Neither bus nor ECC available for accept signal")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send accept signal: {e}")
            return False
    
    def _complete_handoff(self, operation: str, status: str) -> bool:
        """Complete handoff process"""
        try:
            handoff_data = {
                "operation": operation,
                "source": "evidence_locker_main",
                "status": status,
                "timestamp": datetime.now().isoformat()
            }
            
            # Log handoff completion
            self.processing_log.append({
                "timestamp": datetime.now().isoformat(),
                "operation": operation,
                "status": status,
                "type": "handoff_completion"
            })
            
            logger.info(f"[HANDOFF] Completed {operation} with status {status}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to complete handoff: {e}")
            return False
    
    def _handoff_to_gateway(self, file_path, evidence_id, section_hint, classification):
        """Handoff processed evidence to Gateway Controller using full protocol"""
        try:
            # Step 1: Call out to ECC for permission
            if not self._call_out_to_ecc("evidence_handoff", {
                "file_path": file_path,
                "evidence_id": evidence_id,
                "section_hint": section_hint,  # Hint, not final assignment
                "classification": classification
            }):
                logger.error("ECC permission denied for evidence handoff")
                return False
            
            # Step 2: Wait for ECC confirmation
            if not self._wait_for_ecc_confirm():
                logger.error("ECC confirmation timeout for evidence handoff")
                return False
            
            # Step 3: Prepare handoff data
            handoff_data = {
                "operation": "evidence_locker_processing_complete",
                "file_path": file_path,
                "evidence_id": evidence_id,
                "section_hint": section_hint,  # Hint for ECC to make final decision
                "classification": classification,
                "evidence_index": self.evidence_index.get(evidence_id, {}),
                "processing_log": self.processing_log[-1] if self.processing_log else {},
                "timestamp": datetime.now().isoformat()
            }
            
            # Step 4: Send message to Gateway Controller
            if not self._send_message("evidence_handoff", handoff_data):
                logger.error("Failed to send evidence handoff message")
                return False
            
            # Step 5: Send accept signal
            if not self._send_accept_signal("evidence_handoff"):
                logger.error("Failed to send accept signal")
                return False
            
            # Step 6: Register handoff with Gateway Controller
            if GATEWAY and hasattr(GATEWAY, 'register_evidence_locker_handoff'):
                GATEWAY.register_evidence_locker_handoff(
                    from_module="evidence_locker_main",
                    to_module="gateway_controller", 
                    handoff_data=handoff_data
                )
            
            # Step 7: Complete handoff
            self._complete_handoff("evidence_handoff", "success")
            
            logger.info(f"[HANDOFF] Evidence {evidence_id} handed to Gateway Controller (hint: {section_hint})")
            return True
                
        except Exception as e:
            logger.error(f"Failed to handoff to Gateway Controller: {e}")
            self._complete_handoff("evidence_handoff", "error")
            return False


# Bootstrap for Central Command
if __name__ == "__main__":
    # Mock Central Command bus for testing
    class MockBus:
        def register_signal(self, signal, handler):
            logger.info(f"Mock bus registered signal: {signal}")
    
    mock_bus = MockBus()
    locker = EvidenceLocker(mock_bus, mock_bus)
    
    # Test functionality
    test_file = "sample.pdf"  # Replace with an actual file path
    if os.path.exists(test_file):
        evidence_id = locker.scan_file(test_file)
        if evidence_id:
            locker.extract_text_from_image(test_file)
            locker.extract_structure_from_document(test_file)
            locker.build_manifest("./output/manifest.json")
    else:
        logger.info("No test file found - Evidence Locker ready for Central Command integration")
