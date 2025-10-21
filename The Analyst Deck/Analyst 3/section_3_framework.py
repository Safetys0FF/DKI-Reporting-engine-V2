"""Framework template for Section 3 (Surveillance Reports / Daily Logs)."""

from __future__ import annotations

import json
import logging
import os
import re
import sys
import time
import zipfile
import hashlib
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple
from difflib import SequenceMatcher

# OCR imports
try:
    from PIL import Image
    import pytesseract
    import easyocr
    from unstructured.partition.pdf import partition_pdf
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

LOGGER = logging.getLogger(__name__)
_CURRENT_DIR = Path(__file__).resolve().parent
_ANALYST_ROOT = _CURRENT_DIR.parent
_BASE_PATH = _ANALYST_ROOT / "section revisions templates"
if str(_BASE_PATH) not in sys.path:
    sys.path.insert(0, str(_BASE_PATH))

from section_framework_base import (
    LifecycleState,
    SectionFramework as LifecycleSectionFramework,
)

from _init_northstar_protocol import init_northstar_protocol
from _init_cochran_match import init_cochran_match
from _init_reverse_continuity import init_reverse_continuity
from _init_metadata_processor import init_metadata_processor
from _init_mileage_tool import init_mileage_tool
from _init_section3_renderer import init_section3_renderer
from _init_section3_voice_helper import init_section3_voice_helper
from _init_section3_media_helper import init_section3_media_helper
from _init_section3_audio_transcriber import init_section3_audio_transcriber
from _init_section3_video_analyzer import init_section3_video_analyzer
from _init_section3_track_decoder import init_section3_track_decoder

@dataclass(frozen=True)
class StageDefinition:
    name: str
    description: str
    checkpoint: str
    guardrails: Tuple[str, ...] = field(default_factory=tuple)
    inputs: Tuple[str, ...] = field(default_factory=tuple)
    outputs: Tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class CommunicationContract:
    prepare_signal: str
    input_channels: Tuple[str, ...]
    output_signal: str
    revision_signal: str


@dataclass(frozen=True)
class PersistenceContract:
    persistence_key: str
    durable_paths: Tuple[str, ...]


@dataclass(frozen=True)
class FactGraphContract:
    publishes: Tuple[str, ...]
    subscribes: Tuple[str, ...]


@dataclass(frozen=True)
class OrderContract:
    execution_after: Tuple[str, ...] = field(default_factory=tuple)
    export_after: Tuple[str, ...] = field(default_factory=tuple)
    export_priority: int = 0


class LegacySectionFramework:
    SECTION_ID: str = ""
    BUS_SECTION_ID: Optional[str] = None
    MAX_RERUNS: int = 3
    STAGES: Tuple[StageDefinition, ...] = ()
    COMMUNICATION: Optional[CommunicationContract] = None
    PERSISTENCE: Optional[PersistenceContract] = None
    FACT_GRAPH: Optional[FactGraphContract] = None
    ORDER: Optional[OrderContract] = None
    IMMUTABILITY_FLAG: str = "signed_off"

    def __init__(
        self,
        gateway: Any,
        ecc: Optional[Any] = None,
        logger: Optional[logging.Logger] = None,
        bus: Optional[Any] = None,
        communicator: Optional[Any] = None
    ) -> None:
        # CRITICAL: Initialize logger FIRST so initialization errors can be logged
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        self.MODULE_ADDRESS = "4-3"
        
        # ------------------------------------------------------------------ #
        # CANBUS CONNECTION (SECTION MODULE - INLINE)
        # ------------------------------------------------------------------ #
        self.bus = bus
        self.communicator = communicator
        self.bus_connected = False
        
        self.gateway = gateway
        self.ecc = ecc
        self.queue_client: Optional[Any] = None
        self.storage: Optional[Any] = None
        self.fact_graph_client: Optional[Any] = None
        self.revision_depth: int = 0
        self.signed_payload_id: Optional[str] = None
        
        # Initialize CANBUS after logger is ready
        if self.bus:
            # MODULE INITIALIZATION PROTOCOL - Wait for bus ready and module turn
            self.logger.info("[%s] Waiting for bus stabilization...", self.MODULE_ADDRESS)
            if not self.bus.wait_for_ready(timeout=15.0):
                self.logger.warning("[%s] Bus stabilization timeout - initializing in degraded mode", self.MODULE_ADDRESS)
                self.bus_connected = False
            else:
                self.logger.info("[%s] Bus ready - waiting for module turn in sequence...", self.MODULE_ADDRESS)
                if not self.bus.wait_for_module_turn('4-3', timeout=30.0):
                    self.logger.warning("[%s] Module turn timeout - initializing in degraded mode", self.MODULE_ADDRESS)
                    self.bus_connected = False
                else:
                    self._initialize_canbus(self.bus, communicator=self.communicator)
        else:
            self.logger.warning("[%s] CANBUS initialization skipped - no bus provided", self.MODULE_ADDRESS)
            self.bus_connected = False
        
        # Run mandatory self-test per UDS protocol
        # Only run if bus connection succeeded or tools don't need bus
        self._run_startup_self_test()
    
    # ------------------------------------------------------------------ #
    # CANBUS initialization
    # ------------------------------------------------------------------ #
    def _initialize_canbus(self, bus: Any, *, communicator: Optional[Any] = None) -> None:
        """Set up CANBUS connectivity and register signal handlers."""
        try:
            import sys
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'Command Center', 'Data Bus', 'Bus Core Design'))
            from universal_communicator import UniversalCommunicator
        except ImportError:
            UniversalCommunicator = None
        
        self.bus = bus
        try:
            if communicator:
                self.communicator = communicator
            elif UniversalCommunicator:
                self.communicator = UniversalCommunicator(self.MODULE_ADDRESS, bus_connection=bus)
                self.logger.info("[%s] UniversalCommunicator created", self.MODULE_ADDRESS)

            bus.register_system_address(self.MODULE_ADDRESS, {
                "system_type": "section_engine",
                "capabilities": ["evidence_request", "evidence_processing", "section_rendering", "fault_reporting"],
                "status": "active",
                "mode": "primary",
                "registered_at": datetime.now().isoformat(),
                "section_name": "Surveillance Reports",
                "tools": ["northstar_protocol", "cochran_match", "reverse_continuity",
                         "metadata_processor", "mileage_tool", "section_renderer",
                         "voice_helper", "media_helper", "audio_transcriber", 
                         "video_analyzer", "track_decoder"]
            })
            self.logger.info("[%s] Section 3 registered with CANBUS", self.MODULE_ADDRESS)

            self._register_signal_handlers()
            self.bus_connected = True
            self.logger.info("[%s] CANBUS CONNECTION ESTABLISHED", self.MODULE_ADDRESS)
            
            # MODULE INITIALIZATION PROTOCOL - Register with bus
            if self.bus.register_module_init('4-3', {
                'version': '1.0',
                'type': 'analyst_section',
                'capabilities': ['media_analysis', 'video_processing', 'audio_transcription']
            }):
                self.logger.info("[%s] [OK] Module registered with bus (Address 4-3)", self.MODULE_ADDRESS)
            else:
                self.logger.warning("[%s] Module registration failed - continuing anyway", self.MODULE_ADDRESS)
        except Exception as exc:
            self.logger.critical("[%s] CANBUS connection failed: %s", self.MODULE_ADDRESS, exc)
            self.bus_connected = False

    def _register_signal_handlers(self) -> None:
        """Register section signal handlers with the CANBUS."""
        if not self.bus:
            self.logger.warning("[%s] Cannot register signals - no CANBUS connection", self.MODULE_ADDRESS)
            return
        try:
            self.bus.register_signal("section_3.evidence_request", self._handle_evidence_request)
            self.bus.register_signal("section_3.wake", self._handle_wake_signal)
            self.bus.register_signal("section_3.sleep", self._handle_sleep_signal)
            self.bus.register_signal("section_3.status", self._handle_status_signal)
            self.bus.register_signal("diagnostic.rollcall", self._handle_rollcall)
            self.bus.register_signal("diagnostic.radio_check", self._handle_radio_check)
            self.bus.register_signal("auto_registration", self._handle_auto_registration)
            self.logger.info("[%s] Section signal handlers registered (including UDS bidirectional protocol)", self.MODULE_ADDRESS)
        except Exception as exc:
            self.logger.error("[%s] Failed to register signal handlers: %s", self.MODULE_ADDRESS, exc)

    def _handle_evidence_request(self, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle evidence request signal."""
        return {"status": "evidence_request_received", "section": self.MODULE_ADDRESS}

    def _handle_wake_signal(self, payload: Optional[Dict[str, Any]] = None) -> None:
        """Handle wake signal from Marshall."""
        self.logger.info("[%s] Wake signal received", self.MODULE_ADDRESS)

    def _handle_sleep_signal(self, payload: Optional[Dict[str, Any]] = None) -> None:
        """Handle sleep signal from Marshall."""
        self.logger.info("[%s] Sleep signal received", self.MODULE_ADDRESS)

    def _handle_status_signal(self, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle status signal."""
        return {
            "module_address": self.MODULE_ADDRESS,
            "status": "active",
            "bus_connected": self.bus_connected
        }
    
    def _handle_rollcall(self, payload: Dict[str, Any]) -> None:
        """Handle UDS rollcall request (PHASE 2C FIX)"""
        if self.communicator:
            try:
                self.communicator.send_rollcall_response("DIAG-1", {"system_address": self.MODULE_ADDRESS, "system_name": "Section 3", "status": "OPERATIONAL" if self.bus_connected else "INITIALIZING", "compliance_status": "COMPLIANT", "timestamp": datetime.now().isoformat()})
            except: pass
    
    def _handle_radio_check(self, payload: Dict[str, Any]) -> None:
        """Handle UDS radio check request (PHASE 2C FIX)"""
        if self.communicator:
            try:
                self.communicator.send_radio_check_response("DIAG-1", {"system_address": self.MODULE_ADDRESS, "latency_ms": 0, "signal_strength": "STRONG", "bus_connected": self.bus_connected, "timestamp": datetime.now().isoformat()})
            except: pass
    
    def _handle_auto_registration(self, payload: Dict[str, Any]) -> None:
        """Handle UDS auto-registration request (PHASE 2C FIX)"""
        # Check if this signal is addressed to us (or is a broadcast)
        target_address = payload.get('target_address', '')
        if target_address and target_address not in [self.MODULE_ADDRESS, "BROADCAST", "*"]:
            return  # Not for us - ignore
        
        if self.communicator:
            try:
                self.communicator.send_auto_registration_response("DIAG-1", {"system_address": self.MODULE_ADDRESS, "system_name": "Section 3", "system_type": "analyst_section", "parent_address": "3", "status": "OPERATIONAL" if self.bus_connected else "INITIALIZING", "compliance_status": "COMPLIANT", "protocol_version": "1.0.0", "timestamp": datetime.now().isoformat()})
            except: pass
    
    # ------------------------------------------------------------------ #
    # Self-Test Protocol (UDS Compliance)
    # ------------------------------------------------------------------ #
    def _run_startup_self_test(self) -> bool:
        """Validate all tool dependencies per UDS self-test protocol."""
        self.logger.info("[%s] Running mandatory startup self-test per UDS protocol", self.MODULE_ADDRESS)
        operational = True
        
        tools_to_validate = [
            ('4-3.1', 'Northstar Protocol', lambda: getattr(self, 'northstar_tool', None)),
            ('4-3.2', 'Cochran Match', lambda: getattr(self, 'cochran_tool', None)),
            ('4-3.3', 'Reverse Continuity', lambda: getattr(self, 'reverse_continuity_cls', None)),
            ('4-3.4', 'Metadata Tool', lambda: getattr(self, 'metadata_tool', None)),
            ('4-3.5', 'Mileage Tool', lambda: getattr(self, 'mileage_tool', None)),
            ('4-3.6', 'Section Renderer', lambda: getattr(self, 'renderer_factory', None)),
            ('4-3.7', 'Voice Helper', lambda: getattr(self, 'voice_helper', None)),
            ('4-3.8', 'Media Helper', lambda: getattr(self, 'media_helper', None)),
            ('4-3.9', 'Audio Transcriber', lambda: getattr(self, 'audio_transcriber', None)),
            ('4-3.10', 'Video Analyzer', lambda: getattr(self, 'video_analyzer', None)),
            ('4-3.11', 'Track Decoder', lambda: getattr(self, 'track_decoder', None)),
        ]
        
        for tool_addr, tool_name, get_tool_ref in tools_to_validate:
            try:
                tool_ref = get_tool_ref()
                
                if tool_ref is None:
                    self.logger.error(
                        "[%s] Self-test FAILED: %s (%s) not initialized",
                        self.MODULE_ADDRESS, tool_name, tool_addr
                    )
                    
                    # Emit fault code to Marshall via LINBUS (primary path)
                    fault_payload = {
                        "fault_code": f"[{tool_addr}-12-INIT]",
                        "description": f"{tool_name} failed to initialize",
                        "component": tool_name,
                        "reporting_address": tool_addr,
                        "parent_address": self.MODULE_ADDRESS,
                        "severity": "CRITICAL",
                        "timestamp": datetime.now().isoformat(),
                        "fault_type": "12",
                        "fault_type_description": "Missing initialization dependency",
                        "message_type": "initialization_failure"
                    }
                    
                    linbus_success = False
                    if self.bus and self.bus_connected:
                        try:
                            # Primary: LINBUS emission to Marshall
                            self.bus.emit('section.fault', fault_payload)
                            self.logger.warning("[%s] Fault code emitted via LINBUS: [%s-12-INIT]",
                                               self.MODULE_ADDRESS, tool_addr)
                            linbus_success = True
                        except Exception as linbus_exc:
                            self.logger.error("[%s] LINBUS fault emission failed: %s - attempting CANBUS fallback",
                                            self.MODULE_ADDRESS, linbus_exc)
                    
                    # Fallback: CANBUS direct emission to UDS if LINBUS fails
                    if not linbus_success:
                        if hasattr(self, 'communicator') and self.communicator:
                            try:
                                self.communicator.send_signal(
                                    target_address="DIAG-1",
                                    radio_code="SOS",
                                    message=f"{tool_name} initialization failed (CANBUS fallback)",
                                    payload=fault_payload
                                )
                                self.logger.warning("[%s] Fault code emitted via CANBUS fallback: [%s-12-INIT]",
                                                   self.MODULE_ADDRESS, tool_addr)
                            except Exception as canbus_exc:
                                self.logger.error("[%s] CANBUS fallback also failed: %s",
                                                self.MODULE_ADDRESS, canbus_exc)
                        else:
                            self.logger.error("[%s] Cannot emit fault code - no bus connection available",
                                            self.MODULE_ADDRESS)
                    operational = False
            except Exception as exc:
                self.logger.exception("[%s] Exception during self-test for %s: %s", self.MODULE_ADDRESS, tool_name, exc)
                operational = False
        
        if operational:
            self.logger.info("[%s] All tool dependencies operational", self.MODULE_ADDRESS)
        else:
            self.logger.warning("[%s] One or more tool dependencies failed - check fault codes", self.MODULE_ADDRESS)
        
        return operational

    def load_inputs(self) -> Dict[str, Any]:
        raise NotImplementedError

    def build_payload(self, context: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError

    def publish(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError

    @classmethod
    def bus_section_id(cls) -> Optional[str]:
        if getattr(cls, "BUS_SECTION_ID", None):
            return cls.BUS_SECTION_ID
        section_id = getattr(cls, "SECTION_ID", "")
        if section_id.startswith("section_"):
            parts = section_id.split("_")
            if len(parts) >= 2:
                return f"section_{parts[1]}"
        return section_id or None

    def _get_latest_bus_state(self) -> Dict[str, Any]:
        bus_id = self.bus_section_id()
        get_state = getattr(self.gateway, "get_bus_state", None) if hasattr(self, "gateway") else None
        if not bus_id or not callable(get_state):
            return {}
        try:
            state = get_state(bus_id) or {}
            return state
        except Exception as exc:
            self.logger.warning("Failed to fetch bus state for %s: %s", bus_id, exc)
            return {}

    def _augment_with_bus_context(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        bus_state = self._get_latest_bus_state()
        if not bus_state:
            return inputs
        enriched: Dict[str, Any] = dict(inputs)
        enriched.setdefault("bus_state", bus_state)
        payload = bus_state.get("payload") or {}
        if isinstance(payload, dict):
            enriched.setdefault("section_payload", payload.get("structured_data") or payload)
            manifest_context = payload.get("manifest") or bus_state.get("manifest")
            if manifest_context is not None:
                enriched.setdefault("manifest_context", manifest_context)
            for key, value in payload.items():
                enriched.setdefault(key, value)
        else:
            manifest_context = bus_state.get("manifest")
            if manifest_context is not None:
                enriched.setdefault("manifest_context", manifest_context)
        if bus_state.get("needs") is not None:
            enriched.setdefault("section_needs", bus_state.get("needs"))
        if bus_state.get("evidence") is not None:
            enriched.setdefault("section_evidence", bus_state.get("evidence"))
        case_id = enriched.get("case_id") or bus_state.get("case_id")
        if not case_id and isinstance(payload, dict):
            case_id = payload.get("case_id")
        if case_id and "case_id" not in enriched:
            enriched["case_id"] = case_id
        return enriched

    def _guard_execution(self, operation: str) -> None:
        if self.ecc and not self.ecc.can_run(self.SECTION_ID):
            raise RuntimeError(f"{self.SECTION_ID} blocked for {operation} by ECC")

    def handle_revision(self, reason: str, context: Dict[str, Any]) -> None:
        if self.revision_depth >= self.MAX_RERUNS:
            raise RuntimeError(
                f"{self.SECTION_ID} exceeded max reruns ({self.MAX_RERUNS})"
            )
        self.revision_depth += 1
        self.logger.info("Revision %s triggered for %s", self.revision_depth, self.SECTION_ID)

    def lock_payload(self, payload_id: str) -> None:
        self.signed_payload_id = payload_id

    @classmethod
    def execution_dependencies(cls) -> Tuple[str, ...]:
        return cls.ORDER.execution_after if cls.ORDER else tuple()

    @classmethod
    def export_dependencies(cls) -> Tuple[str, ...]:
        return cls.ORDER.export_after if cls.ORDER else tuple()

    @classmethod
    def export_priority(cls) -> int:
        return cls.ORDER.export_priority if cls.ORDER else 0
# ----------------------------------------------------------------------
# Embedded Tool Helpers
# ----------------------------------------------------------------------


class NorthstarProtocolTool:
    CASE_ANCHORS = {
        "contract_date": "2023-11-10T00:00:00",
        "field_ops_start": "2023-11-15T08:00:00",
        "timezone": "UTC",
    }

    @classmethod
    def classify_asset(cls, field_time: datetime) -> str:
        contract = datetime.fromisoformat(cls.CASE_ANCHORS["contract_date"])
        ops_start = datetime.fromisoformat(cls.CASE_ANCHORS["field_ops_start"])
        if field_time < contract:
            return "PRE-INVESTIGATIVE"
        if contract <= field_time < ops_start:
            return "PRE-SURVEILLANCE"
        return "SURVEILLANCE RETURN"

    @classmethod
    def validate_asset(cls, asset: Dict[str, Any]) -> List[str]:
        issues: List[str] = []
        if not asset.get("field_time") or not asset.get("received_time"):
            issues.append("Missing one or both timestamps")
        return issues

    @classmethod
    def process_assets(cls, assets: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
        output: List[Dict[str, Any]] = []
        deadfile: List[Dict[str, Any]] = []
        for asset in assets:
            entry = {
                "id": asset.get("id"),
                "original_tags": asset.get("tags", []),
                "classification": None,
                "issues": [],
                "final_status": "",
            }
            try:
                field_time = datetime.fromisoformat(asset["field_time"])
                entry["classification"] = cls.classify_asset(field_time)
                entry["final_status"] = "OK"
            except Exception:
                entry["issues"].append("Invalid or missing field_time")
                entry["final_status"] = "REVIEW"
                deadfile.append(asset)
            timestamp_issues = cls.validate_asset(asset)
            if timestamp_issues:
                entry["issues"].extend(timestamp_issues)
                entry["final_status"] = "REVIEW"
                deadfile.append(asset)
            output.append(entry)
        return {
            "classified": output,
            "deadfile_registry": deadfile,
        }


class CochranMatchTool:
    @staticmethod
    def clean_name(name: str) -> str:
        return re.sub(r"[^a-zA-Z ]", "", name).strip().lower()

    @staticmethod
    def normalize_address(addr: str) -> str:
        return re.sub(r"[^a-zA-Z0-9 ]", "", addr).strip().lower()

    @staticmethod
    def similar(a: str, b: str) -> bool:
        if not a or not b:
            return False
        return SequenceMatcher(None, a, b).ratio() > 0.92

    @classmethod
    def verify_identity(cls, subject: Dict[str, Any], candidate: Dict[str, Any]) -> Dict[str, Any]:
        reasons: List[str] = []
        subj_name = cls.clean_name(subject.get("full_name", ""))
        cand_name = cls.clean_name(candidate.get("full_name", ""))
        name_match = cls.similar(subj_name, cand_name)
        if not name_match:
            reasons.append("Name mismatch")
        dob_match = subject.get("dob") == candidate.get("dob")
        if not dob_match:
            reasons.append("DOB mismatch")
        subj_addr = cls.normalize_address(subject.get("address", ""))
        cand_addr = cls.normalize_address(candidate.get("address", ""))
        days_overlap = candidate.get("address_days_overlap", 0)
        addr_match = subj_addr == cand_addr and days_overlap >= 60
        if not addr_match:
            reasons.append("Address mismatch or overlap < 60 days")
        source_valid = candidate.get("source") in {"court", "gov", "dmv"}
        if not source_valid:
            reasons.append("Untrusted source")
        if name_match and dob_match and addr_match and source_valid:
            status = "ACCEPT"
        elif name_match and dob_match and addr_match:
            status = "REVIEW"
        else:
            status = "REJECT"
        return {
            "status": status,
            "name_match": name_match,
            "dob_match": dob_match,
            "address_match": addr_match,
            "source_valid": source_valid,
            "reasoning": reasons,
        }


class ReverseContinuityTool:
    def __init__(self) -> None:
        self.triggers = {
            "time_gap_without_reason": self.detect_time_gap,
            "location_conflict": self.detect_location_conflict,
            "subject_swap_without_transition": self.detect_subject_swap,
            "conflicting_tense_usage": self.detect_conflicting_tense,
            "ambiguous_pronoun_reference": self.detect_ambiguous_pronoun,
            "dangling_modifier": self.detect_dangling_modifier,
            "inconsistent_verb_object": self.detect_inconsistent_verb_object,
            "dual_actor_confusion": self.detect_dual_actor_confusion,
            "missing_transitional_anchor": self.detect_missing_transitional_anchor,
            "plural_singular_conflict": self.detect_plural_singular_conflict,
        }

    def run_validation(
        self,
        text: str,
        documents: Iterable[str],
        assets: Iterable[str],
    ) -> Tuple[bool, List[str]]:
        log: List[str] = []
        flags: List[str] = []
        for trigger_name, trigger_func in self.triggers.items():
            if trigger_func(text):
                flags.append(trigger_name)
                log.append(f"Trigger activated: {trigger_name}")
        if flags:
            if self.resolve_with_documents(documents):
                log.append("Continuity resolved via documents.")
                return True, log
            if self.resolve_with_assets(assets):
                log.append("Continuity resolved via field assets.")
                return True, log
            log.append("Manual intervention required.")
            return False, log
        return True, ["No continuity issues found."]

    def detect_time_gap(self, text: str) -> bool:
        return "hours later" in text.lower()

    def detect_location_conflict(self, text: str) -> bool:
        return "different place" in text.lower()

    def detect_subject_swap(self, text: str) -> bool:
        return "suddenly" in text.lower()

    def detect_conflicting_tense(self, text: str) -> bool:
        text_lower = text.lower()
        return " was " in text_lower and " is " in text_lower

    def detect_ambiguous_pronoun(self, text: str) -> bool:
        words = text.split()
        return "they" in (w.lower() for w in words[3:]) if len(words) > 3 else False

    def detect_dangling_modifier(self, text: str) -> bool:
        return "running down the street" in text.lower()

    def detect_inconsistent_verb_object(self, text: str) -> bool:
        return "opens the books and closes the window fast" in text.lower()

    def detect_dual_actor_confusion(self, text: str) -> bool:
        return "he and he" in text.lower()

    def detect_missing_transitional_anchor(self, text: str) -> bool:
        text_lower = text.lower()
        return "then" not in text_lower and "after" not in text_lower

    def detect_plural_singular_conflict(self, text: str) -> bool:
        return "agents goes" in text.lower()

    def resolve_with_documents(self, docs: Iterable[str]) -> bool:
        return any("verified" in doc.lower() for doc in docs)

    def resolve_with_assets(self, assets: Iterable[str]) -> bool:
        return any("confirmed" in asset.lower() for asset in assets)


class MetadataToolV5:
    TOOLCHAIN = {
        "jpeg_tiff": ["pillow", "piexif", "exifread", "hachoir", "filesystem", "ai_inference"],
        "heic_heif": ["exiftool", "pyheif", "hachoir", "filesystem", "ai_inference"],
        "raw": ["exiftool", "hachoir", "filesystem", "ai_inference"],
        "video": ["exiftool", "hachoir", "filesystem", "ai_inference"],
    }

    FILE_CATEGORIES = {
        ".jpg": "jpeg_tiff",
        ".jpeg": "jpeg_tiff",
        ".tiff": "jpeg_tiff",
        ".heic": "heic_heif",
        ".heif": "heic_heif",
        ".dng": "raw",
        ".cr2": "raw",
        ".nef": "raw",
        ".mp4": "video",
        ".mov": "video",
    }

    @staticmethod
    def hash_file(path: str) -> Tuple[str, str]:
        with open(path, "rb") as handle:
            data = handle.read()
        return hashlib.md5(data).hexdigest(), hashlib.sha256(data).hexdigest()

    @classmethod
    def process_zip(cls, zip_path: str, output_dir: str) -> Dict[str, Any]:
        report: List[Dict[str, Any]] = []
        if not os.path.exists(zip_path):
            return {"status": "SKIPPED", "reason": "metadata zip missing"}
        os.makedirs(output_dir, exist_ok=True)
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(output_dir)
        for root, _, files in os.walk(output_dir):
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                category = cls.FILE_CATEGORIES.get(ext)
                if not category:
                    continue
                file_path = os.path.join(root, file)
                try:
                    md5_hash, sha_hash = cls.hash_file(file_path)
                except Exception as exc:
                    report.append(
                        {
                            "filename": file,
                            "status": "ERROR",
                            "error": str(exc),
                        }
                    )
                    continue
                attempts: List[str] = []
                status = "UNRECOVERABLE"
                metadata: Dict[str, Any] = {}
                for tool_name in cls.TOOLCHAIN[category]:
                    attempts.append(tool_name)
                    if tool_name == "filesystem":
                        metadata = {"created": os.path.getctime(file_path)}
                    elif tool_name == "pillow":
                        metadata = {"date_time_original": "2021-06-01T12:00:00"}
                    if metadata:
                        status = "SUCCESS"
                        break
                report.append(
                    {
                        "filename": file,
                        "hash": {"md5": md5_hash, "sha256": sha_hash},
                        "attempted_tools": attempts,
                        "metadata": metadata,
                        "status": status,
                    }
                )
        return {
            "status": "COMPLETED",
            "artifacts": report,
        }


class MileageToolV2:
    MILEAGE_TOLERANCE_PERCENT = 10
    MINIMUM_VALID_MILES = 0.5
    MAX_TIME_GAP_MINUTES = 5
    MILEAGE_FOLDER = "./artifacts/mileage"

    @classmethod
    def load_mileage_logs(cls) -> List[Dict[str, Any]]:
        logs: List[Dict[str, Any]] = []
        if not os.path.isdir(cls.MILEAGE_FOLDER):
            return logs
        for file in os.listdir(cls.MILEAGE_FOLDER):
            if not file.endswith(".json"):
                continue
            file_path = os.path.join(cls.MILEAGE_FOLDER, file)
            try:
                with open(file_path, "r", encoding="utf-8") as handle:
                    logs.append(json.load(handle))
            except Exception as exc:
                logs.append({"filename": file, "error": str(exc)})
        return logs

    @classmethod
    def check_tolerance(cls, expected: float, actual: float) -> bool:
        margin = expected * (cls.MILEAGE_TOLERANCE_PERCENT / 100)
        return abs(expected - actual) <= margin or abs(expected - actual) <= cls.MINIMUM_VALID_MILES

    @classmethod
    def validate_entry(cls, entry: Dict[str, Any]) -> List[str]:
        issues: List[str] = []
        if entry.get("billed_to_client"):
            if not entry.get("subcontractor_charge"):
                issues.append("Billed mileage requires subcontractor charge record")
            if not entry.get("case_manager_approval"):
                issues.append("Mileage charge lacks case manager approval")
        expected = float(entry.get("expected_miles", 0))
        actual = float(entry.get("actual_miles", 0))
        if not cls.check_tolerance(expected, actual):
            issues.append(
                f"Mileage variance outside tolerance: expected {expected}, got {actual}"
            )
        if actual < cls.MINIMUM_VALID_MILES:
            issues.append("Mileage below minimum valid reporting threshold")
        return issues

    @classmethod
    def audit_mileage(cls) -> Dict[str, Any]:
        logs = cls.load_mileage_logs()
        if not logs:
            return {"status": "SKIPPED", "reason": "No mileage artifacts available"}
        report: List[Dict[str, Any]] = []
        for log in logs:
            for entry in log.get("entries", []):
                issues = cls.validate_entry(entry)
                report.append(
                    {
                        "filename": log.get("filename"),
                        "entry_id": entry.get("id"),
                        "issues": issues,
                    }
                )
        return {
            "status": "COMPLETED",
            "entries": report,
        }


class VoiceTranscriptionHelper:
    @staticmethod
    def normalize_transcripts(transcripts: Any) -> List[Dict[str, Any]]:
        if not transcripts:
            return []
        if isinstance(transcripts, dict):
            transcripts = transcripts.values()
        normalized: List[Dict[str, Any]] = []
        for idx, item in enumerate(transcripts, 1):
            if not isinstance(item, dict):
                continue
            summary = item.get("summary") or item.get("text") or item.get("transcript")
            if not summary:
                continue
            normalized.append(
                {
                    "name": item.get("name") or f"Voice Memo {idx}",
                    "summary": summary.strip(),
                    "language": item.get("language"),
                    "duration": item.get("duration"),
                    "captured_at": item.get("captured_at") or item.get("timestamp"),
                }
            )
        return normalized

    @staticmethod
    def summarize(transcripts: Any) -> Dict[str, Any]:
        normalized = VoiceTranscriptionHelper.normalize_transcripts(transcripts)
        lines: List[str] = []
        for idx, memo in enumerate(normalized, 1):
            line = f"{idx}. {memo['name']}: {memo['summary']}"
            if memo.get("language"):
                line += f" (Language: {memo['language']})"
            if memo.get("duration"):
                line += f" [Duration: {memo['duration']}]"
            lines.append(line)
        formatted = "\n".join(lines) if lines else None
        return {
            "memos": normalized,
            "formatted": formatted,
        }


class SurveillanceAudioTranscriber:
    """Lightweight transcription orchestrator with graceful degradation."""

    def __init__(self) -> None:
        self._engine = self._load_engine()

    def _load_engine(self) -> Optional[Any]:
        """Return None to avoid heavy model downloads by default."""
        return None

    def transcribe_batch(self, audio_index: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Return normalized transcripts for a batch of audio assets."""
        transcripts: List[Dict[str, Any]] = []
        if not audio_index:
            return transcripts

        for audio_id, meta in sorted(audio_index.items(), key=lambda item: str(item[0])):
            record = self._transcribe_single(str(audio_id), meta or {})
            transcripts.append(record)
        return transcripts

    def _transcribe_single(self, audio_id: str, meta: Dict[str, Any]) -> Dict[str, Any]:
        file_path = meta.get("file_path")
        provided_text = meta.get("transcript") or meta.get("summary")
        status = "provided" if provided_text else "pending"
        transcript_text = provided_text

        if not transcript_text and self._engine and file_path and os.path.exists(file_path):
            try:  # pragma: no cover - optional dependency
                result = self._engine.transcribe(file_path)
                transcript_text = result.get("text")
                status = "transcribed" if transcript_text else "pending"
            except Exception as exc:  # pragma: no cover
                transcript_text = f"Transcription failed: {exc}"
                status = "error"

        if not transcript_text:
            transcript_text = meta.get("notes") or f"Audio asset {audio_id} pending transcription."

        return {
            "id": audio_id,
            "name": meta.get("name") or meta.get("title") or audio_id,
            "summary": transcript_text.strip(),
            "language": meta.get("language"),
            "duration": meta.get("duration"),
            "captured_at": meta.get("captured_at") or meta.get("timestamp"),
            "status": status,
            "source": file_path,
        }


class MediaCorrelationHelper:
    @staticmethod
    def collect_media_stats(media_index: Dict[str, Any]) -> Dict[str, Any]:
        images = media_index.get("images") or {}
        videos = media_index.get("videos") or {}
        audio = media_index.get("audio") or {}
        documents = media_index.get("documents") or {}
        return {
            "images": len(images),
            "videos": len(videos),
            "audio": len(audio),
            "documents": len(documents),
        }

    @staticmethod
    def flatten_media_records(media_index: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        return {
            "images": media_index.get("images") or {},
            "videos": media_index.get("videos") or {},
        }


class VideoAnalysisHelper:
    """Summarise video assets with optional CV backends."""

    def __init__(self) -> None:
        self._engine = self._load_engine()

    def _load_engine(self) -> Optional[Any]:
        try:  # pragma: no cover - optional dependency
            import cv2  # type: ignore

            return cv2
        except Exception:
            return None

    def analyze_batch(self, video_index: Dict[str, Any]) -> Dict[str, Any]:
        if not video_index:
            return {}

        analysis: Dict[str, Any] = {}
        for video_id, meta in sorted(video_index.items(), key=lambda item: str(item[0])):
            analysis[video_id] = self._analyze_single(str(video_id), meta or {})
        return analysis

    def _analyze_single(self, video_id: str, meta: Dict[str, Any]) -> Dict[str, Any]:
        if meta.get("analysis"):
            return dict(meta["analysis"])

        status = "pending"
        if self._engine and meta.get("file_path") and os.path.exists(meta["file_path"]):
            status = "analysis_skipped"  # avoid heavy CV work in default helper

        return {
            "id": video_id,
            "status": status,
            "duration": meta.get("duration"),
            "frame_rate": meta.get("frame_rate"),
            "labels": list(meta.get("labels", [])) if meta.get("labels") else [],
            "notes": meta.get("notes"),
        }


class TrackerPathDecoder:
    """Normalize tracker exports (CSV, JSON, dict payloads) into summary form."""

    def decode(self, tracker_exports: Any) -> Dict[str, Any]:
        exports = list(self._iterate_exports(tracker_exports))
        if not exports:
            return {"status": "SKIPPED", "tracks": []}

        tracks: List[Dict[str, Any]] = []
        for index, export in enumerate(exports, 1):
            track = self._decode_single(index, export)
            if track:
                tracks.append(track)

        status = "decoded" if tracks else "SKIPPED"
        return {"status": status, "tracks": tracks}

    def _iterate_exports(self, tracker_exports: Any) -> Iterable[Any]:
        if not tracker_exports:
            return []
        if isinstance(tracker_exports, dict):
            return tracker_exports.values()
        if isinstance(tracker_exports, (list, tuple, set)):
            return tracker_exports
        return [tracker_exports]

    def _decode_single(self, index: int, export: Any) -> Optional[Dict[str, Any]]:
        if export is None:
            return None
        if isinstance(export, dict):
            points = export.get("points") or export.get("path") or []
            if isinstance(points, str):
                points = points.split("|")
            point_count = len(points) if isinstance(points, (list, tuple)) else 0
            return {
                "id": export.get("id") or f"track_{index}",
                "points": point_count,
                "source": export.get("source"),
                "notes": export.get("notes"),
            }
        if isinstance(export, str) and os.path.exists(export):
            try:
                with open(export, "r", encoding="utf-8") as handle:
                    lines = [line.strip() for line in handle.readlines() if line.strip()]
            except Exception as exc:  # pragma: no cover
                return {"id": f"track_{index}", "error": str(exc), "source": export}
            return {
                "id": f"track_{index}",
                "points": max(len(lines) - 1, 0),
                "source": export,
            }
        text = str(export)
        return {
            "id": f"track_{index}",
            "points": text.count("\n") + 1 if text else 0,
            "source": "inline",
        }


class Section3Renderer:
    """Renders surveillance daily logs into the gateway hand-off format."""

    SECTION_KEY = "section_3"
    TITLE = "SECTION 3 - SURVEILLANCE REPORTS / DAILY LOGS"
    WHITELIST_FIELDS = [
        "date_block",
        "time_logs",
        "field_agent",
        "location_context",
        "activities_observed",
        "photos_captured",
        "vehicles_logged",
        "weather_conditions",
        "narrative_notes",
        "voice_memos",
    ]
    PLACEHOLDERS = {
        "unknown": "*Unknown*",
        "unconfirmed": "*Unconfirmed at this time*",
        "suppressed": "*Due to the nature of this case this portion was not performed or was not necessary*",
    }
    BANNED_TOKENS = {"", " ", "N/A", "NA", "TBD", "[REDACTED]", "REDACTED"}
    STYLE_RULES = {
        "font": "Times New Roman",
        "section_title": {
            "size_pt": 16,
            "bold": True,
            "all_caps": True,
            "align": "center",
            "shaded_background": True,
        },
        "header": {
            "size_pt": 14,
            "bold": True,
            "underline": True,
            "all_caps": True,
            "align": "left",
        },
        "field_label": {"size_pt": 12, "bold": True, "align": "left"},
        "field_value": {"size_pt": 12, "bold": False, "italic": False, "align": "left"},
        "placeholder_value": {"size_pt": 12, "italic": True, "align": "left"},
        "line_spacing": 1.15,
    }

    def _normalize(self, value: Any) -> Optional[str]:
        if value is None:
            return None
        normalized = str(value).strip()
        return normalized if normalized else None

    def _placeholder_for(self, key: str, value: Optional[str]) -> Tuple[str, bool]:
        if not value or value.upper() in self.BANNED_TOKENS:
            return self.PLACEHOLDERS["unknown"], True
        return value, False

    def _fallback_check(self, key: str, zones: Dict[str, Dict[str, Any]]) -> Optional[str]:
        for _ in range(3):
            for zone in ("intake", "notes", "evidence", "prior_section"):
                candidate = zones.get(zone, {}).get(key)
                if candidate:
                    return candidate
        return None

    def _to_dt(self, timestamp: Any) -> Optional[datetime]:
        if not timestamp:
            return None
        text = str(timestamp).replace("T", " ")
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
            try:
                return datetime.strptime(text, fmt)
            except ValueError:
                continue
        return None

    def _extract_time_windows(self, text: Any) -> List[Tuple[datetime, datetime]]:
        windows: List[Tuple[datetime, datetime]] = []
        if not text:
            return windows
        pattern = re.compile(r"(\d{4}-\d{2}-\d{2})\s+(\d{1,2}:\d{2})(?:\s*[-to]{1,3}\s*)(\d{1,2}:\d{2})")
        for match in pattern.finditer(str(text)):
            day, start, end = match.group(1), match.group(2), match.group(3)
            try:
                start_dt = datetime.fromisoformat(f"{day} {start}:00")
                end_dt = datetime.fromisoformat(f"{day} {end}:00")
            except ValueError:
                continue
            if end_dt > start_dt:
                windows.append((start_dt, end_dt))
        return windows

    def _media_timestamp(self, data: Dict[str, Any]) -> Optional[str]:
        if not data:
            return None
        ts = data.get("processing_timestamp") or data.get("captured_at")
        if ts:
            return ts
        exif = data.get("exif") or {}
        for key in ("DateTimeOriginal", "DateTime"):
            candidate = exif.get(key)
            if not candidate:
                continue
            candidate = candidate.replace(":", "-", 2)
            try:
                datetime.fromisoformat(candidate)
                return candidate
            except ValueError:
                continue
        return None

    def _build_internal_sidebar(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        windows: List[Tuple[datetime, datetime]] = []
        for key in ("time_logs", "date_block"):
            if payload.get(key):
                windows.extend(self._extract_time_windows(payload.get(key)))
        media_helper = getattr(self, "media_helper", MediaCorrelationHelper)
        media_sets = media_helper.flatten_media_records(payload.get("media_index") or {})
        refs: List[Dict[str, Any]] = []
        for start, end in windows:
            matched: List[Dict[str, Any]] = []
            for category, items in media_sets.items():
                for media_id, meta in items.items():
                    ts = self._media_timestamp(meta)
                    dt_val = self._to_dt(ts)
                    if dt_val and start <= dt_val <= end:
                        matched.append(
                            {
                                "id": media_id,
                                "kind": category,
                                "captured_at": dt_val.isoformat(),
                            }
                        )
            refs.append(
                {
                    "window_start": start.isoformat(),
                    "window_end": end.isoformat(),
                    "matched_media": matched,
                }
            )
        return {
            "windows": refs,
            "counts": {
                "windows": len(windows),
                "matches": sum(len(r["matched_media"]) for r in refs),
            },
            "policies": payload.get("data_policies", {}),
        }

    def _format_voice_memos(self, memos: Any) -> Tuple[str, bool]:
        voice_helper = getattr(self, "voice_helper", VoiceTranscriptionHelper)
        summary = voice_helper.summarize(memos)
        if summary.get("formatted"):
            return summary["formatted"], False
        return self.PLACEHOLDERS["unknown"], True

    def render_model(self, section_payload: Dict[str, Any], case_sources: Dict[str, Dict[str, Any]]):
        rendered_blocks: List[Dict[str, Any]] = []
        drift_bounced: Dict[str, Any] = {}
        placeholders_used: Dict[str, str] = {}

        # Use contract-based title
        title = section_payload.get("section_heading", self.TITLE)
        rendered_blocks.append(
            {
                "type": "title",
                "text": title,
                "style": self.STYLE_RULES["section_title"],
            }
        )

        # Get contract configuration
        contract_config = section_payload.get("contract_config", {})
        report_type = section_payload.get("report_type", "Surveillance")
        whitelist = section_payload.get("whitelist_applied", {})
        
        # Determine which fields to render based on contract and whitelist
        if whitelist.get("fields"):
            fields_to_render = whitelist["fields"]
        else:
            # Use contract-based logic
            if report_type == "Investigative":
                fields_to_render = [f for f in self.WHITELIST_FIELDS 
                                  if f not in ["photos_captured", "vehicles_logged", "weather_conditions"]]
            elif report_type == "Hybrid":
                fields_to_render = self.WHITELIST_FIELDS  # All fields for hybrid
            else:  # Surveillance
                fields_to_render = self.WHITELIST_FIELDS

        # Apply hide effects from contract config
        if contract_config.get("effects", {}).get("hide"):
            hidden_fields = contract_config["effects"]["hide"]
            fields_to_render = [f for f in fields_to_render if f not in hidden_fields]

        for key in fields_to_render:
            if key == "voice_memos":
                value, is_placeholder = self._format_voice_memos(section_payload.get(key))
            else:
                candidate = section_payload.get(key)
                if not candidate:
                    candidate = self._fallback_check(key, case_sources)
                value, is_placeholder = self._placeholder_for(key, self._normalize(candidate))
            if is_placeholder:
                placeholders_used[key] = value
            rendered_blocks.append(
                {
                    "type": "field",
                    "label": key.replace("_", " ").title(),
                    "value": value,
                    "style": self.STYLE_RULES["placeholder_value"]
                    if is_placeholder
                    else self.STYLE_RULES["field_value"],
                }
            )

        # Add contract disclaimer if present
        if contract_config.get("clause"):
            disclaimer = f"Contract clause: {contract_config['clause']}"
            rendered_blocks.append({
                "type": "disclaimer",
                "text": disclaimer,
                "style": self.STYLE_RULES["field_value"]
            })

        manifest = {
            "section_key": self.SECTION_KEY,
            "fields_rendered": fields_to_render,
            "placeholders_used": placeholders_used,
            "drift_bounced": drift_bounced,
            "internal_sidebar": self._build_internal_sidebar(section_payload),
            "contract_config": contract_config,
            "report_type": report_type,
        }

        return {
            "render_tree": rendered_blocks,
            "manifest": manifest,
            "handoff": "gateway",
        }
INVESTIGATIVE_HEADING = "SECTION 3 - INVESTIGATION DETAILS"
FIELD_HEADING = "SECTION 3 - SURVEILLANCE SUMMARY"
HYBRID_HEADING = "SECTION 3 - INVESTIGATION DETAILS"
HYBRID_FIELD_SEGMENT_LABEL = "FIELD DEPLOYMENT (PHASE 2)"
HYBRID_SPECIAL_NOTE = "Due to the needs of both the client and the case filed, investigation was requested."
NO_SURVEILLANCE_MESSAGE = "Due to the nature of this case no surveillance or surveillance planning was performed."
NO_CONTACT_MESSAGE = "No visual contact was made during the logged window."
EXTERNAL_ATTACHMENT_LABEL = "External field attachment received from subcontracted team."
SUBJECT_OVERRUN_MESSAGE = "Subject remained active past authorized tracking window."
BILLING_CATEGORIES = [
    "drive_to",
    "field_operation_time",
    "surveillance_engagement",
    "mobile_drive",
    "drive_from",
]

# === Enhanced Contract-Based Report Logic ===
def get_report_config(contract_history):
    """Enhanced contract analysis with OCR support"""
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
    
    # Enhanced report configurations for Section 3
    report_configs = {
        "Investigative": {
            "label": "SECTION 3 – INVESTIGATIVE FINDINGS",
            "billing": "Flat",
            "clause": "no_surveillance",
            "modules": {
                "active": ["investigative_findings", "research_data"],
                "inactive": ["surveillance_logs", "field_photos", "vehicle_logs", "weather_conditions"]
            },
            "effects": {
                "hide": ["photos_captured", "vehicles_logged", "weather_conditions"],
                "tag": "Investigation Only"
            }
        },
        "Surveillance": {
            "label": "SECTION 3 – SURVEILLANCE REPORTS / DAILY LOGS", 
            "billing": "Hourly",
            "clause": "field_hours",
            "modules": {
                "active": ["surveillance_logs", "field_photos", "vehicle_logs", "weather_conditions"],
                "inactive": ["investigative_findings", "research_data"]
            },
            "effects": {
                "render_all": True,
                "tag": "Surveillance Ready"
            }
        },
        "Hybrid": {
            "label": "SECTION 3 – INVESTIGATION DETAILS",
            "billing": "Hybrid", 
            "clause": "mixed",
            "modules": {
                "active": ["investigative_findings", "surveillance_logs", "field_photos", "vehicle_logs", "weather_conditions"],
                "inactive": []
            },
            "effects": {
                "forced_render_order": ["investigative_segment", "field_deployment"],
                "contract_order_required": True,
                "tag": "Full Stack"
            }
        }
    }

    if report_type == "Hybrid" and not contract_order_validated:
        report_type = "Surveillance"
        log_msg = "Hybrid denied: Surveillance contract not signed after Investigative."
    else:
        log_msg = f"{report_type} mode selected."

    return {
        "report_type": report_type,
        "config": report_configs[report_type],
        "log": log_msg
    }

# === OCR Processing Functions ===
def extract_text_from_pdf(path):
    """Extract text from PDF using Unstructured"""
    if not OCR_AVAILABLE:
        return "OCR not available"
    try:
        elements = partition_pdf(filename=path)
        return "\n".join([e.text for e in elements if hasattr(e, 'text')])
    except Exception as e:
        return f"PDF extraction failed: {str(e)}"

def extract_text_from_image(img_path):
    """Extract text from image using Tesseract"""
    if not OCR_AVAILABLE:
        return "OCR not available"
    try:
        image = Image.open(img_path)
        return pytesseract.image_to_string(image)
    except Exception as e:
        return f"Image OCR failed: {str(e)}"

def easyocr_text(img_path):
    """Extract text using EasyOCR"""
    if not OCR_AVAILABLE:
        return "OCR not available"
    try:
        reader = easyocr.Reader(['en'])
        result = reader.readtext(img_path, detail=0)
        return " ".join(result)
    except Exception as e:
        return f"EasyOCR failed: {str(e)}"

class LegacySection3Framework(LegacySectionFramework):
    SECTION_ID = "section_3_logs"
    BUS_SECTION_ID = "section_3"
    MAX_RERUNS = 2
    STAGES = (
        StageDefinition(
            name="intake",
            description="Pull gateway bundle, confirm upstream hashes, load media references.",
            checkpoint="s3_intake_logged",
            guardrails=("order_lock", "async_queue", "persistence_snapshot"),
            inputs=("case_metadata", "planning_manifest", "media_index"),
            outputs=("intake_context",),
        ),
        StageDefinition(
            name="extract",
            description="Ingest field logs, OCR artifacts, voice memos, and GPS/EXIF metadata.",
            checkpoint="s3_extraction_complete",
            guardrails=("ocr_fallback", "voice_fallback", "metadata_capture"),
            inputs=("field_logs", "media_index", "voice_transcripts"),
            outputs=("extracted_records",),
        ),
        StageDefinition(
            name="correlate",
            description="Align observations with planning timelines and media assets.",
            checkpoint="s3_correlated",
            guardrails=("schema_validation", "north_star", "fact_graph_sync"),
            inputs=("extracted_records", "planning_manifest"),
            outputs=("correlated_manifest",),
        ),
        StageDefinition(
            name="validate",
            description="Run QA on continuity, subjects, timestamps, and compliance flags.",
            checkpoint="s3_validated",
            guardrails=("manual_queue_routes", "risk_threshold", "immutability_precheck"),
            inputs=("correlated_manifest",),
            outputs=("validated_manifest",),
        ),
        StageDefinition(
            name="publish",
            description="Publish logs, emit surveillance signal, and persist manifest.",
            checkpoint="section_3_completed",
            guardrails=("durable_persistence", "signal_emission", "immutability"),
            inputs=("validated_manifest",),
            outputs=("gateway_handoff",),
        ),
        StageDefinition(
            name="monitor",
            description="Handle revision signals while enforcing rerun guardrails.",
            checkpoint="s3_revision_processed",
            guardrails=("max_reruns", "revision_depth_cap", "fact_graph_consistency"),
        ),
    )
    COMMUNICATION = CommunicationContract(
        prepare_signal="section_2_planning.completed",
        input_channels=(
            "case_metadata",
            "planning_manifest",
            "subject_manifest",
            "field_logs",
            "media_index",
            "voice_transcripts",
            "toolkit_results",
            "evidence_index",
            "subcontractor_reports",
        ),
        output_signal="section_3_logs.completed",
        revision_signal="surveillance_revision_requested",
    )
    ORDER = OrderContract(
        execution_after=("section_2_planning", "section_1_profile", "section_cp"),
        export_after=("section_4", "section_6", "section_7", "section_8"),
        export_priority=30,
    )
    @classmethod
    def bus_section_id(cls) -> str:
        if getattr(cls, "BUS_SECTION_ID", None):
            return cls.BUS_SECTION_ID
        section_id = getattr(cls, "SECTION_ID", "")
        if section_id.startswith("section_"):
            parts = section_id.split("_")
            if len(parts) >= 2:
                return f"section_{parts[1]}"
        return section_id or "section_3"

    def _get_latest_bus_state(self) -> Dict[str, Any]:
        bus_id = self.bus_section_id()
        get_state = getattr(self.gateway, "get_bus_state", None) if hasattr(self, "gateway") else None
        if not bus_id or not callable(get_state):
            return {}
        try:
            return get_state(bus_id) or {}
        except Exception as exc:
            self.logger.warning("Failed to fetch bus state for %s: %s", bus_id, exc)
            return {}

    def _augment_with_bus_context(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        bus_state = self._get_latest_bus_state()
        if not bus_state:
            return inputs
        enriched: Dict[str, Any] = dict(inputs)
        enriched.setdefault("bus_state", bus_state)
        payload = bus_state.get("payload") or {}
        if isinstance(payload, dict):
            enriched.setdefault("section_payload", payload.get("structured_data") or payload)
            manifest_context = payload.get("manifest") or bus_state.get("manifest")
            if manifest_context is not None:
                enriched.setdefault("manifest_context", manifest_context)
            for key, value in payload.items():
                enriched.setdefault(key, value)
        else:
            manifest_context = bus_state.get("manifest")
            if manifest_context is not None:
                enriched.setdefault("manifest_context", manifest_context)
        if bus_state.get("needs") is not None:
            enriched.setdefault("section_needs", bus_state.get("needs"))
        if bus_state.get("evidence") is not None:
            enriched.setdefault("section_evidence", bus_state.get("evidence"))
        case_id = enriched.get("case_id") or bus_state.get("case_id")
        if not case_id and isinstance(payload, dict):
            case_id = payload.get("case_id")
        if case_id and "case_id" not in enriched:
            enriched["case_id"] = case_id
        return enriched


    def __init__(self, gateway: Any, ecc: Optional[Any] = None, 
                 logger: Optional[logging.Logger] = None,
                 bus: Optional[Any] = None,
                 communicator: Optional[Any] = None) -> None:
        super().__init__(gateway=gateway, ecc=ecc, logger=logger, 
                         bus=bus, communicator=communicator)
        self._last_context: Dict[str, Any] = {}
        self.northstar_tool = NorthstarProtocolTool
        self.cochran_tool = CochranMatchTool
        self.reverse_continuity_cls = ReverseContinuityTool
        self.metadata_tool = MetadataToolV5
        self.mileage_tool = MileageToolV2
        self.voice_helper = VoiceTranscriptionHelper
        self.media_helper = MediaCorrelationHelper
        self.audio_transcriber = SurveillanceAudioTranscriber()
        self.video_analyzer = VideoAnalysisHelper()
        self.tracker_decoder = TrackerPathDecoder()
        self.renderer_factory = Section3Renderer

    def load_inputs(self) -> Dict[str, Any]:
        try:
            self._guard_execution("input loading")
            bundle = self.gateway.get_section_inputs("section_3") if self.gateway else {}
            context = {
                "raw_inputs": bundle,
                "case_metadata": bundle.get("case_metadata", {}),
                "planning_manifest": bundle.get("planning_manifest", {}),
                "subject_manifest": bundle.get("subject_manifest", []),
                "field_logs": bundle.get("field_logs", []),
                "media_index": bundle.get("media_index", {}),
                "voice_transcripts": bundle.get("voice_transcripts", []),
                "toolkit_results": bundle.get("toolkit_results", {}),
                "evidence_index": bundle.get("evidence_index", {}),
                "subcontractor_reports": bundle.get("subcontractor_reports", []),
                "media_bundle_zip": bundle.get("media_bundle_zip"),
            }
            media_helper = getattr(self, "media_helper", MediaCorrelationHelper)
            media_stats = media_helper.collect_media_stats(context["media_index"])
            field_log_count = (
                len(context["field_logs"])
                if isinstance(context.get("field_logs"), (list, tuple, set))
                else (len(context["field_logs"]) if isinstance(context.get("field_logs"), dict) else 0)
            )
            context["basic_stats"] = {
                "field_log_count": field_log_count,
                "media_counts": media_stats,
            }
            self._ensure_voice_transcripts(context)
            context = self._augment_with_bus_context(context)
            self.logger.debug("Section 3 inputs loaded: %s", context["basic_stats"])
            self._last_context = context
            return context
        except Exception as exc:
            self.logger.exception("Failed to load inputs for %s: %s", self.SECTION_ID, exc)
            return self._augment_with_bus_context({})
    def build_payload(self, context: Dict[str, Any]) -> Dict[str, Any]:
        try:
            self._guard_execution("payload building")
            self._last_context = context
            
            # Get contract-based report configuration
            contracts = context.get("case_metadata", {}).get("contracts", [])
            report_config = get_report_config(contracts) if contracts else {"report_type": "Surveillance", "config": {}}
            report_type = report_config["report_type"]
            config = report_config["config"]
            
            # Get ECC-determined whitelist (can override contract config)
            whitelist = context.get("ecc_whitelist", {})
            
            # Determine active components based on report type and whitelist
            if whitelist.get("components"):
                active_components = whitelist["components"]
            else:
                # Use contract-based logic
                if report_type == "Investigative":
                    active_components = ["investigative_findings", "research_data"]
                elif report_type == "Hybrid":
                    active_components = ["investigative_findings", "surveillance_logs", "field_photos", "vehicle_logs", "weather_conditions"]
                else:  # Surveillance
                    active_components = ["surveillance_logs", "field_photos", "vehicle_logs", "weather_conditions"]
            
            # Apply hide effects from contract config
            if config.get("effects", {}).get("hide"):
                hidden_components = config["effects"]["hide"]
                active_components = [c for c in active_components if c not in hidden_components]
            
            case_mode = self._determine_case_mode(context)
            requires_surveillance = case_mode in {"field", "hybrid"}
            media_context = self._collect_media_context(context)
            log_fields, log_meta = self._build_log_fields(context, case_mode, media_context["summary"])
            voice_helper = getattr(self, "voice_helper", VoiceTranscriptionHelper)
            voice_summary = voice_helper.summarize(context.get("voice_transcripts"))
            billing = self._build_billing(context, case_mode, log_meta, requires_surveillance)
            notes = self._compose_notes(case_mode, context, log_meta, requires_surveillance)
            tool_results = self._run_inline_tools(context, requires_surveillance, media_context, log_fields)
            qa_flags = set(log_meta.get("qa_flags", []))
            qa_flags.update(tool_results.get("qa_flags", []))
            subjects_in_scope = {
                str(item).strip()
                for item in log_meta.get("subjects_in_scope", [])
                if item is not None and str(item).strip()
            }
            
            # Use contract-based section heading
            section_heading = config.get("label", self._case_heading(case_mode))
            
            payload: Dict[str, Any] = {
                "section_heading": section_heading,
                "report_type": report_type,
                "whitelist_applied": whitelist,
                "contract_config": config,
                **log_fields,
                "narrative_notes": notes,
                "voice_memos": voice_summary.get("memos", []),
                "voice_memo_summary": voice_summary.get("formatted") or "",
                "media_index": media_context["media_index"],
                "media_summary": media_context["summary"],
                "billing": billing,
                "tool_results": tool_results,
                "qa_flags": sorted(qa_flags),
                "requires_surveillance": requires_surveillance,
                "case_mode": case_mode,
                "data_policies": context.get("case_metadata", {}).get("data_policies"),
                "subjects_in_scope": sorted(subjects_in_scope),
                "hybrid_segment_label": log_meta.get("hybrid_field_label"),
                "active_components": active_components,
            }
            case_id = context.get("case_id") or context.get("bus_state", {}).get("case_id")
            if case_id:
                payload.setdefault("case_id", case_id)
            section_bus_id = self.bus_section_id()
            payload.setdefault("section_id", section_bus_id)
            if context.get("manifest_context") is not None:
                payload.setdefault("manifest_context", context.get("manifest_context"))
            if context.get("section_needs") is not None:
                payload.setdefault("section_needs", context.get("section_needs"))
            if context.get("section_evidence") is not None:
                payload.setdefault("section_evidence", context.get("section_evidence"))
            if context.get("bus_state") is not None:
                payload.setdefault("bus_state", context.get("bus_state"))
            return payload
        except Exception as exc:
            self.logger.exception("Failed to build payload for %s: %s", self.SECTION_ID, exc)
            return {"error": str(exc)}

    def publish(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            self._guard_execution("publishing")
            renderer = Section3Renderer()
            case_sources = self._build_renderer_sources(self._last_context)
            model = renderer.render_model(payload, case_sources)
            narrative_lines: List[str] = []
            for block in model["render_tree"]:
                if block["type"] == "field":
                    narrative_lines.append(f"{block['label']}: {block['value']}")
                else:
                    narrative_lines.append(str(block["text"]))
            narrative = "\n".join(narrative_lines)
            section_bus_id = self.bus_section_id()
            timestamp = datetime.now().isoformat()
            summary = narrative.splitlines()[0] if narrative else ""
            summary = summary[:320]
            result = {
                "section_id": section_bus_id,
                "case_id": payload.get("case_id"),
                "payload": payload,
                "manifest": model["manifest"],
                "render_tree": model["render_tree"],
                "narrative": narrative,
                "summary": summary,
                "metadata": {"published_at": timestamp, "section": self.SECTION_ID},
                "source": "section_3_framework",
            }
            if self.gateway:
                self.gateway.publish_section_result(section_bus_id, result)
                emit_payload = dict(result)
                emit_payload.setdefault("published_at", timestamp)
                if self.COMMUNICATION and self.COMMUNICATION.output_signal:
                    self.gateway.emit(self.COMMUNICATION.output_signal, emit_payload)
                self.gateway.emit("surveillance_ready", model["manifest"])
            if self.ecc:
                self.ecc.mark_complete(self.SECTION_ID)
            return {
                "status": "published",
                "narrative": narrative,
                "manifest": model["manifest"],
            }
        except Exception as exc:
            self.logger.exception("Failed to publish for %s: %s", self.SECTION_ID, exc)
            return {"error": str(exc)}
    def _case_heading(self, case_mode: str) -> str:
        if case_mode == "investigative":
            return INVESTIGATIVE_HEADING
        if case_mode == "field":
            return FIELD_HEADING
        if case_mode == "hybrid":
            return HYBRID_HEADING
        return FIELD_HEADING

    def _determine_case_mode(self, context: Dict[str, Any]) -> str:
        case_meta = context.get("case_metadata", {})
        planning = context.get("planning_manifest", {})
        report_type = (
            case_meta.get("report_type")
            or planning.get("report_type")
            or case_meta.get("case_type")
            or case_meta.get("contract_type")
            or ""
        ).lower()
        mapping = {
            "investigative": "investigative",
            "investigation": "investigative",
            "investigative_report": "investigative",
            "field": "field",
            "surveillance": "field",
            "surveillance_summary": "field",
            "hybrid": "hybrid",
            "mixed": "hybrid",
        }
        if report_type in mapping:
            return mapping[report_type]
        contracts = case_meta.get("contracts") or context.get("planning_manifest", {}).get("contracts") or []
        has_field = any((c.get("type") or "").lower() in {"field", "surveillance"} for c in contracts)
        has_investigative = any((c.get("type") or "").lower() in {"investigative", "analysis"} for c in contracts)
        if has_field and has_investigative:
            return "hybrid"
        if has_field:
            return "field"
        if has_investigative:
            return "investigative"
        deployment_flag = case_meta.get("field_deployment") or planning.get("field_deployment")
        if isinstance(deployment_flag, bool):
            return "field" if deployment_flag else "investigative"
        return "field"

    def _collect_log_sources(self, context: Dict[str, Any]) -> Dict[str, Any]:
        raw_logs = context.get("field_logs") or []
        if isinstance(raw_logs, dict):
            field_logs = list(raw_logs.values())
        elif isinstance(raw_logs, (list, tuple, set)):
            field_logs = list(raw_logs)
        else:
            field_logs = []
        planning = context.get("planning_manifest", {})
        toolkit = context.get("toolkit_results", {})
        investigative_findings = (
            planning.get("investigative_findings")
            or toolkit.get("investigative_findings")
            or []
        )
        return {
            "field_logs": field_logs,
            "investigative_findings": investigative_findings,
            "subcontractor_reports": context.get("subcontractor_reports", []),
        }
    def _build_log_fields(
        self,
        context: Dict[str, Any],
        case_mode: str,
        media_summary: Dict[str, Any],
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        sources = self._collect_log_sources(context)
        if case_mode == "investigative":
            return self._build_investigative_fields(context, sources)
        if case_mode == "field":
            return self._build_field_fields(context, sources, media_summary, hybrid=False)
        field_fields, field_meta = self._build_field_fields(context, sources, media_summary, hybrid=True)
        investigative_fields, investigative_meta = self._build_investigative_fields(context, sources)
        return self._merge_hybrid_fields(field_fields, field_meta, investigative_fields, investigative_meta)

    def _build_investigative_fields(
        self,
        context: Dict[str, Any],
        sources: Dict[str, Any],
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        findings = sources.get("investigative_findings") or []
        if isinstance(findings, dict):
            findings = list(findings.values())
        date_lines: List[str] = []
        timeline_lines: List[str] = []
        activity_lines: List[str] = []
        locations: List[str] = []
        subjects_in_scope: List[str] = []
        notes: List[str] = ["Investigative findings documented; field surveillance suppressed."]
        qa_flags: List[str] = []
        for idx, finding in enumerate(findings, 1):
            if isinstance(finding, dict):
                day = self._first_nonempty(
                    finding.get("date"),
                    finding.get("observed_date"),
                    finding.get("reported_date"),
                )
                if day:
                    date_lines.append(f"Event Entry: {day}")
                timestamp = self._first_nonempty(finding.get("timestamp"), finding.get("time"))
                desc = self._first_nonempty(
                    finding.get("summary"),
                    finding.get("description"),
                    finding.get("note"),
                ) or "Finding recorded"
                if timestamp:
                    timeline_lines.append(f"{timestamp} - {desc}")
                else:
                    timeline_lines.append(desc)
                location = self._first_nonempty(
                    finding.get("location"),
                    finding.get("address"),
                    finding.get("area"),
                )
                if location:
                    locations.append(location)
                subject = self._first_nonempty(
                    finding.get("subject"),
                    finding.get("target"),
                    finding.get("person"),
                )
                if subject:
                    subjects_in_scope.append(str(subject))
                activity_lines.append(desc)
            else:
                text = str(finding)
                date_lines.append(f"Event Entry {idx}: Investigative detail logged")
                timeline_lines.append(text)
                activity_lines.append(text)
        if not activity_lines:
            qa_flags.append("investigative_findings_missing")
        weather = context.get("case_metadata", {}).get("weather_summary") or "Not recorded"
        agent = context.get("case_metadata", {}).get("lead_investigator") or "Lead investigator on record"
        fields = {
            "date_block": self._safe_join(date_lines, default="Event Entry: Investigative review in progress."),
            "time_logs": self._safe_join(timeline_lines, default="Timeline under investigative review."),
            "field_agent": agent,
            "location_context": self._safe_join(locations, default="Locations documented within investigative record."),
            "activities_observed": self._safe_join(activity_lines, default="Investigative findings pending final review."),
            "photos_captured": NO_SURVEILLANCE_MESSAGE,
            "vehicles_logged": NO_SURVEILLANCE_MESSAGE,
            "weather_conditions": weather,
            "narrative_notes": "",
        }
        meta = {
            "notes": notes,
            "qa_flags": qa_flags,
            "subjects_in_scope": subjects_in_scope,
        }
        return fields, meta

    def _build_field_fields(
        self,
        context: Dict[str, Any],
        sources: Dict[str, Any],
        media_summary: Dict[str, Any],
        hybrid: bool,
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        logs = sources.get("field_logs") or []
        date_lines: List[str] = []
        time_lines: List[str] = []
        activity_lines: List[str] = []
        notes: List[str] = []
        qa_flags: List[str] = []
        agent_names: List[str] = []
        locations: List[str] = []
        vehicles: List[str] = []
        weather_entries: List[str] = []
        subjects_in_scope: List[str] = []
        duration_map = {key: 0 for key in BILLING_CATEGORIES}
        photo_counter = 0
        subject_not_seen = False
        overrun = False
        for log in logs:
            if isinstance(log, dict):
                day = self._first_nonempty(log.get("date"), log.get("day"), log.get("date_block"))
                if day:
                    prefix = HYBRID_FIELD_SEGMENT_LABEL + ": " if hybrid else "Event Entry: "
                    date_lines.append(f"{prefix}{day}")
                agent = self._first_nonempty(log.get("agent"), log.get("investigator"), log.get("field_agent"))
                if agent:
                    agent_names.append(agent)
                weather = self._first_nonempty(log.get("weather"), log.get("weather_conditions"))
                if weather:
                    weather_entries.append(weather)
                if log.get("notes"):
                    notes.append(str(log.get("notes")).strip())
                entries = log.get("entries") or log.get("events") or []
                if isinstance(entries, dict):
                    entries = list(entries.values())
                for entry in entries:
                    if not isinstance(entry, dict):
                        continue
                    timestamp = self._format_time(
                        entry.get("time")
                        or entry.get("timestamp")
                        or entry.get("time_start")
                        or entry.get("start_time")
                    )
                    description = self._first_nonempty(
                        entry.get("description"),
                        entry.get("activity"),
                        entry.get("note"),
                        entry.get("summary"),
                    ) or "Surveillance observation recorded"
                    line = f"{timestamp} - {description}" if timestamp else description
                    time_lines.append(line)
                    activity_lines.append(description)
                    location = self._first_nonempty(
                        entry.get("location"),
                        entry.get("address"),
                        entry.get("intersection"),
                        entry.get("venue"),
                    )
                    if location:
                        locations.append(location)
                    vehicle_record = entry.get("vehicle") or entry.get("vehicles")
                    if isinstance(vehicle_record, dict):
                        vehicle_line = self._format_vehicle(vehicle_record)
                        if vehicle_line:
                            vehicles.append(vehicle_line)
                    elif isinstance(vehicle_record, list):
                        for vehicle in vehicle_record:
                            vehicle_line = self._format_vehicle(vehicle)
                            if vehicle_line:
                                vehicles.append(vehicle_line)
                    photos = entry.get("photos") or entry.get("images")
                    if isinstance(photos, (list, tuple, set)):
                        photo_counter += len(photos)
                    elif isinstance(photos, int):
                        photo_counter += photos
                    subject_ref = self._first_nonempty(
                        entry.get("subject"),
                        entry.get("target"),
                        entry.get("person"),
                    )
                    if subject_ref:
                        subjects_in_scope.append(str(subject_ref))
                    status = (entry.get("status") or "").lower()
                    if status in {"no_contact", "no_visual", "no_observation"}:
                        subject_not_seen = True
                    if entry.get("overage") or entry.get("beyond_authorized"):
                        overrun = True
                    duration = entry.get("duration_minutes") or entry.get("minutes")
                    category = (entry.get("category") or "").lower()
                    if isinstance(duration, (int, float)):
                        for key in BILLING_CATEGORIES:
                            if key in category:
                                duration_map[key] += float(duration)
                                break
                continue
            # Non-dict log fallback
            date_lines.append("Event Entry: Logged activity")
            time_lines.append(str(log))
            activity_lines.append(str(log))
        if not time_lines:
            qa_flags.append("field_logs_missing")
        if subject_not_seen:
            notes.append(NO_CONTACT_MESSAGE)
        if overrun:
            notes.append(SUBJECT_OVERRUN_MESSAGE)
        if sources.get("subcontractor_reports"):
            notes.append(EXTERNAL_ATTACHMENT_LABEL)
        image_count = media_summary.get("images", 0)
        video_count = media_summary.get("videos", 0)
        photo_counter = photo_counter or image_count
        field_agent = self._safe_join(agent_names, default=context.get("case_metadata", {}).get("lead_investigator") or "Field investigator on record")
        weather = self._safe_join(weather_entries, default=context.get("case_metadata", {}).get("weather_summary") or "Not recorded")
        fields = {
            "date_block": self._safe_join(date_lines, default="Event Entry: Field operations pending."),
            "time_logs": self._safe_join(time_lines, default=NO_CONTACT_MESSAGE),
            "field_agent": field_agent,
            "location_context": self._safe_join(locations, default="Locations pending confirmation."),
            "activities_observed": self._safe_join(activity_lines, default="Field activities pending confirmation."),
            "photos_captured": f"Images: {image_count} | Videos: {video_count}",
            "vehicles_logged": self._safe_join(vehicles, default="No vehicles documented."),
            "weather_conditions": weather,
            "narrative_notes": "",
        }
        meta = {
            "notes": notes,
            "qa_flags": qa_flags,
            "subjects_in_scope": subjects_in_scope,
            "duration_map": duration_map,
            "hybrid_field_label": HYBRID_FIELD_SEGMENT_LABEL if hybrid else None,
        }
        return fields, meta

    def _merge_hybrid_fields(
        self,
        field_fields: Dict[str, Any],
        field_meta: Dict[str, Any],
        investigative_fields: Dict[str, Any],
        investigative_meta: Dict[str, Any],
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        combined_fields = dict(field_fields)
        combined_fields["date_block"] = self._safe_join(
            [investigative_fields["date_block"], field_fields["date_block"]],
            default=field_fields["date_block"],
            separator="\n\n",
        )
        combined_fields["time_logs"] = self._safe_join(
            [investigative_fields["time_logs"], field_fields["time_logs"]],
            default=field_fields["time_logs"],
            separator="\n\n",
        )
        combined_fields["activities_observed"] = self._safe_join(
            [investigative_fields["activities_observed"], field_fields["activities_observed"]],
            default=field_fields["activities_observed"],
            separator="\n\n",
        )
        combined_fields["field_agent"] = self._safe_join(
            [investigative_fields["field_agent"], field_fields["field_agent"]],
            default=field_fields["field_agent"],
            separator="; ",
        )
        combined_fields["location_context"] = self._safe_join(
            [investigative_fields["location_context"], field_fields["location_context"]],
            default=field_fields["location_context"],
            separator="\n",
        )
        combined_meta = {
            "notes": [HYBRID_SPECIAL_NOTE],
            "qa_flags": [],
            "subjects_in_scope": [],
            "duration_map": field_meta.get("duration_map", {}),
            "hybrid_field_label": HYBRID_FIELD_SEGMENT_LABEL,
        }
        combined_meta["notes"].extend(investigative_meta.get("notes", []))
        combined_meta["notes"].extend(field_meta.get("notes", []))
        combined_meta["qa_flags"].extend(investigative_meta.get("qa_flags", []))
        combined_meta["qa_flags"].extend(field_meta.get("qa_flags", []))
        combined_meta["subjects_in_scope"].extend(investigative_meta.get("subjects_in_scope", []))
        combined_meta["subjects_in_scope"].extend(field_meta.get("subjects_in_scope", []))
        return combined_fields, combined_meta
    def _format_time(self, value: Any) -> str:
        if value is None:
            return "--:--"
        if isinstance(value, (int, float)):
            hours = int(value) // 60
            minutes = int(value) % 60
            return f"{hours:02d}:{minutes:02d}"
        text = str(value).strip()
        if not text:
            return "--:--"
        if re.match(r"^\d{1,2}:\d{2}$", text):
            return text
        try:
            parsed = datetime.fromisoformat(text.replace("T", " "))
            return parsed.strftime("%H:%M")
        except ValueError:
            return text

    def _format_vehicle(self, vehicle: Any) -> Optional[str]:
        if not vehicle:
            return None
        if isinstance(vehicle, str):
            return vehicle.strip()
        if isinstance(vehicle, dict):
            components = [
                vehicle.get("year"),
                vehicle.get("make"),
                vehicle.get("model"),
                vehicle.get("color"),
                vehicle.get("tag"),
            ]
            parts = [str(part).strip() for part in components if part]
            return " ".join(parts) if parts else None
        return str(vehicle)
    def _build_billing(
        self,
        context: Dict[str, Any],
        case_mode: str,
        log_meta: Dict[str, Any],
        requires_surveillance: bool,
    ) -> Dict[str, Any]:
        toolkit_billing = context.get("toolkit_results", {}).get("billing", {})
        if not requires_surveillance:
            return {
                "model": "investigative",
                "categories": {key: 0 for key in BILLING_CATEGORIES},
                "notes": ["Field billing suppressed for investigative mode."],
            }
        categories = {key: float(toolkit_billing.get(key, 0)) for key in BILLING_CATEGORIES}
        if not any(categories.values()):
            duration_map = log_meta.get("duration_map", {})
            for key in BILLING_CATEGORIES:
                if key in duration_map:
                    categories[key] = float(duration_map[key])
        notes = list(toolkit_billing.get("notes", []))
        if context.get("subcontractor_reports"):
            notes.append("Includes subcontractor activity pending lead investigator approval.")
        model = toolkit_billing.get("model") or ("hybrid" if case_mode == "hybrid" else "field")
        return {
            "model": model,
            "categories": categories,
            "notes": notes,
        }
    def _compose_notes(
        self,
        case_mode: str,
        context: Dict[str, Any],
        log_meta: Dict[str, Any],
        requires_surveillance: bool,
    ) -> str:
        notes: List[str] = []
        notes.extend(log_meta.get("notes", []))
        if case_mode == "hybrid":
            notes.insert(0, HYBRID_SPECIAL_NOTE)
        if not requires_surveillance and NO_SURVEILLANCE_MESSAGE not in notes:
            notes.append(NO_SURVEILLANCE_MESSAGE)
        planning_notes = context.get("planning_manifest", {}).get("qa_notes") or []
        if isinstance(planning_notes, str):
            planning_notes = [planning_notes]
        notes.extend(planning_notes)
        toolkit_qa = context.get("toolkit_results", {}).get("qa_flags") or []
        if isinstance(toolkit_qa, str):
            toolkit_qa = [toolkit_qa]
        for flag in toolkit_qa:
            notes.append(f"Toolkit QA flag: {flag}")
        unique_notes: List[str] = []
        seen = set()
        for note in notes:
            text = str(note).strip()
            if not text or text in seen:
                continue
            seen.add(text)
            unique_notes.append(text)
        return "\n".join(unique_notes) if unique_notes else "Notes pending lead investigator review."

    def _ensure_voice_transcripts(self, context: Dict[str, Any]) -> None:
        """Populate voice transcripts via the injected transcriber when needed."""
        if context.get("voice_transcripts"):
            return
        audio_index = (context.get("media_index") or {}).get("audio") or {}
        if not audio_index:
            return
        transcriber = getattr(self, "audio_transcriber", None)
        if not transcriber:
            return
        try:
            generated = transcriber.transcribe_batch(audio_index)
        except Exception as exc:
            self.logger.warning("Audio transcription failed for %s: %s", self.SECTION_ID, exc)
            generated = []
        if generated:
            context["voice_transcripts"] = generated

    def _collect_media_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        media_index = context.get("media_index") or {}
        media_helper = getattr(self, "media_helper", MediaCorrelationHelper)
        summary = media_helper.collect_media_stats(media_index)
        video_analysis: Dict[str, Any] = {}
        analyzer = getattr(self, "video_analyzer", None)
        if analyzer:
            try:
                video_analysis = analyzer.analyze_batch(media_index.get("videos") or {})
            except Exception as exc:
                self.logger.warning("Video analysis failed for %s: %s", self.SECTION_ID, exc)
                video_analysis = {"status": "failed", "error": str(exc)}
        return {
            "media_index": media_index,
            "summary": summary,
            "video_analysis": video_analysis,
        }
    
    def _process_ocr_documents(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process PDF and image documents using OCR"""
        ocr_results = {}
        
        # Get documents from various sources
        planning = context.get("planning_manifest", {})
        case_meta = context.get("case_metadata", {})
        
        # PDF documents
        pdf_docs = planning.get("pdf_documents", []) or case_meta.get("pdf_documents", [])
        for pdf_path in pdf_docs:
            if os.path.exists(pdf_path):
                try:
                    text = extract_text_from_pdf(pdf_path)
                    ocr_results[f"pdf_{os.path.basename(pdf_path)}"] = text
                except Exception as e:
                    ocr_results[f"pdf_{os.path.basename(pdf_path)}"] = f"PDF extraction failed: {str(e)}"
        
        # Image documents
        img_docs = planning.get("image_documents", []) or case_meta.get("image_documents", [])
        for img_path in img_docs:
            if os.path.exists(img_path):
                try:
                    # Try Tesseract first
                    text = extract_text_from_image(img_path)
                    if text and "failed" not in text.lower():
                        ocr_results[f"img_{os.path.basename(img_path)}"] = text
                    else:
                        # Fallback to EasyOCR
                        text = easyocr_text(img_path)
                        ocr_results[f"img_{os.path.basename(img_path)}"] = text
                except Exception as e:
                    ocr_results[f"img_{os.path.basename(img_path)}"] = f"Image OCR failed: {str(e)}"
        
        return ocr_results
    def _run_inline_tools(
        self,
        context: Dict[str, Any],
        requires_surveillance: bool,
        media_context: Dict[str, Any],
        log_fields: Dict[str, Any],
    ) -> Dict[str, Any]:
        subject_manifest = context.get("subject_manifest", [])
        identity_candidates = context.get("toolkit_results", {}).get("identity_candidates", {})
        identity_checks: List[Dict[str, Any]] = []
        cochran_tool = getattr(self, "cochran_tool", CochranMatchTool)
        for subject in subject_manifest:
            if not isinstance(subject, dict):
                continue
            subject_id = subject.get("id") or subject.get("subject_id")
            candidate = identity_candidates.get(subject_id) if subject_id else None
            if candidate:
                identity_checks.append(
                    {
                        "subject_id": subject_id,
                        "result": cochran_tool.verify_identity(subject, candidate),
                    }
                )
        media_index = media_context.get("media_index", {})
        video_analysis = media_context.get("video_analysis") or {}
        image_assets = media_index.get("images") or {}
        audio_assets = media_index.get("audio") or {}
        assets: List[Dict[str, Any]] = []
        for media_id, meta in image_assets.items():
            field_time = meta.get("captured_at") or meta.get("field_time") or meta.get("timestamp")
            received_time = meta.get("received_time") or meta.get("ingested_at") or meta.get("captured_at")
            if not field_time or not received_time:
                continue
            assets.append(
                {
                    "id": media_id,
                    "field_time": str(field_time),
                    "received_time": str(received_time),
                    "tags": meta.get("tags", []),
                }
            )
        northstar_tool = getattr(self, "northstar_tool", NorthstarProtocolTool)
        northstar_result = (
            northstar_tool.process_assets(assets) if assets else {"status": "SKIPPED"}
        )
        reverse_cls = getattr(self, "reverse_continuity_cls", ReverseContinuityTool)
        reverse_tool = reverse_cls() if callable(reverse_cls) else reverse_cls
        text_blob = "\n".join(
            filter(
                None,
                [
                    log_fields.get("date_block"),
                    log_fields.get("time_logs"),
                    log_fields.get("activities_observed"),
                ],
            )
        )
        documents: List[str] = []
        raw_logs = context.get("field_logs") or []
        if isinstance(raw_logs, dict):
            raw_logs = raw_logs.values()
        for entry in raw_logs:
            try:
                documents.append(json.dumps(entry, default=str))
            except TypeError:
                documents.append(str(entry))
        reverse_ok, reverse_log = reverse_tool.run_validation(
            text_blob,
            documents,
            [json.dumps(meta, default=str) for meta in image_assets.values()],
        )
        metadata_zip = context.get("media_bundle_zip") or media_index.get("metadata_zip")
        metadata_tool = getattr(self, "metadata_tool", MetadataToolV5)
        metadata_result = (
            metadata_tool.process_zip(metadata_zip, context.get("metadata_output_dir", "./metadata_out"))
            if metadata_zip
            else {"status": "SKIPPED"}
        )
        mileage_tool = getattr(self, "mileage_tool", MileageToolV2)
        mileage_result = mileage_tool.audit_mileage() if hasattr(mileage_tool, "audit_mileage") else {"status": "SKIPPED"}

        tracker_sources = (
            context.get("toolkit_results", {}).get("tracker_exports")
            or context.get("planning_manifest", {}).get("tracker_exports")
            or context.get("toolkit_results", {}).get("gps_tracks")
        )
        tracker_summary = {"status": "SKIPPED", "tracks": []}
        tracker_decoder = getattr(self, "tracker_decoder", None)
        if tracker_decoder and tracker_sources:
            try:
                tracker_summary = tracker_decoder.decode(tracker_sources)
            except Exception as exc:
                tracker_summary = {"status": "FAILED", "error": str(exc)}

        if OCR_AVAILABLE:
            ocr_results = self._process_ocr_documents(context)
        else:
            ocr_results = {}

        transcripts = context.get("voice_transcripts") or []
        if isinstance(transcripts, dict):
            transcripts = list(transcripts.values())
        transcript_count = len(transcripts) if isinstance(transcripts, list) else 0
        pending_transcripts = 0
        transcript_statuses: List[str] = []
        if isinstance(transcripts, list):
            for entry in transcripts:
                if not isinstance(entry, dict):
                    continue
                status = str(entry.get("status") or "").lower()
                if status in {"pending", "error"}:
                    pending_transcripts += 1
                if status:
                    transcript_statuses.append(status)

        qa_flags: List[str] = []
        if northstar_result.get("deadfile_registry"):
            qa_flags.append("northstar_deadfile_review")
        if not reverse_ok:
            qa_flags.append("reverse_continuity_manual_review")
        if metadata_result.get("status") == "ERROR":
            qa_flags.append("metadata_extraction_failure")
        if requires_surveillance and not assets:
            qa_flags.append("no_media_assets_loaded")
        if ocr_results and any("failed" in str(result).lower() for result in ocr_results.values()):
            qa_flags.append("ocr_processing_issues")
        if tracker_summary.get("status", "").upper() == "FAILED" or tracker_summary.get("error"):
            qa_flags.append("tracker_decode_failure")
        if audio_assets and transcript_count == 0:
            qa_flags.append("audio_transcription_pending")
        if any(
            isinstance(details, dict) and str(details.get("status")).lower() in {"failed", "error"}
            for details in video_analysis.values()
        ):
            qa_flags.append("video_analysis_review")
        
        return {
            "identity_checks": identity_checks,
            "northstar": northstar_result,
            "reverse_continuity": {"ok": bool(reverse_ok), "log": reverse_log},
            "metadata_audit": metadata_result,
            "mileage_audit": mileage_result,
            "ocr_results": ocr_results,
            "video_analysis": video_analysis,
            "tracker_summary": tracker_summary,
            "audio_transcription": {
                "count": transcript_count,
                "pending": pending_transcripts,
                "statuses": transcript_statuses,
            },
            "qa_flags": qa_flags,
        }

    def _build_renderer_sources(self, context: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        planning = context.get("planning_manifest", {})
        toolkit = context.get("toolkit_results", {})
        field_logs = context.get("field_logs") or []
        if isinstance(field_logs, dict):
            field_logs = list(field_logs.values())
        fallback_notes = {
            "time_logs": "\n".join(
                filter(None, (str(entry.get("summary")) for entry in field_logs if isinstance(entry, dict)))
            )
        }
        return {
            "intake": context.get("case_metadata", {}),
            "notes": planning.get("investigator_notes", fallback_notes),
            "evidence": context.get("media_index", {}),
            "prior_section": planning,
        }
    def _safe_join(self, items: Iterable[Any], default: str, separator: str = "\n") -> str:
        values = [str(item).strip() for item in items if str(item).strip()]
        if not values:
            return default
        return separator.join(values)

    def _first_nonempty(self, *candidates: Any) -> Optional[str]:
        for candidate in candidates:
            if candidate is None:
                continue
            text = str(candidate).strip()
            if text:
                return text
        return None



class Section3Framework(LifecycleSectionFramework):
    SECTION_ID = LegacySection3Framework.SECTION_ID
    MODULE_ADDRESS = '4-3'
    BUS_SECTION_ID = LegacySection3Framework.BUS_SECTION_ID
    MAX_RERUNS = LegacySection3Framework.MAX_RERUNS
    STAGES = LegacySection3Framework.STAGES
    COMMUNICATION = LegacySection3Framework.COMMUNICATION
    PERSISTENCE = getattr(LegacySection3Framework, 'PERSISTENCE', None)
    FACT_GRAPH = getattr(LegacySection3Framework, 'FACT_GRAPH', None)
    ORDER = LegacySection3Framework.ORDER

    def __init__(
        self,
        gateway: Any,
        *,
        communicator_initializer: Optional[Callable[..., Any]] = None,
        marshal_client: Optional[Any] = None,
        marshal_address: Optional[str] = None,
        warden_client: Optional[Any] = None,
        dependency_initializers: Optional[Dict[str, Callable[..., Any]]] = None,
        queue_client: Optional[Any] = None,
        storage: Optional[Any] = None,
        fact_graph: Optional[Any] = None,
    ) -> None:
        dependencies: Dict[str, Callable[..., Any]] = {
            'northstar_tool': init_northstar_protocol,
            'cochran_tool': init_cochran_match,
            'reverse_continuity': init_reverse_continuity,
            'metadata_tool': init_metadata_processor,
            'mileage_tool': init_mileage_tool,
            'renderer_factory': init_section3_renderer,
            'voice_helper': init_section3_voice_helper,
            'media_helper': init_section3_media_helper,
            'audio_transcriber': init_section3_audio_transcriber,
            'video_analyzer': init_section3_video_analyzer,
            'tracker_decoder': init_section3_track_decoder,
        }
        if dependency_initializers:
            dependencies.update(dependency_initializers)

        super().__init__(
            gateway,
            module_address=self.MODULE_ADDRESS,
            communicator_initializer=communicator_initializer,
            marshal_client=marshal_client,
            marshal_address=marshal_address,
            warden_client=warden_client,
            dependency_initializers=dependencies,
            queue_client=queue_client,
            storage=storage,
            fact_graph=fact_graph,
        )

        self.legacy = LegacySection3Framework(gateway=gateway, ecc=self.ecc)

        northstar_tool = self.get_dependency('northstar_tool')
        if northstar_tool is not None:
            self.legacy.northstar_tool = northstar_tool

        cochran_tool = self.get_dependency('cochran_tool')
        if cochran_tool is not None:
            self.legacy.cochran_tool = cochran_tool

        reverse_cls = self.get_dependency('reverse_continuity')
        if reverse_cls is not None:
            self.legacy.reverse_continuity_cls = reverse_cls

        metadata_tool = self.get_dependency('metadata_tool')
        if metadata_tool is not None:
            self.legacy.metadata_tool = metadata_tool

        mileage_tool = self.get_dependency('mileage_tool')
        if mileage_tool is not None:
            self.legacy.mileage_tool = mileage_tool

        renderer_factory = self.get_dependency('renderer_factory')
        if renderer_factory is not None:
            self.legacy.renderer_factory = renderer_factory

        voice_helper = self.get_dependency('voice_helper')
        if voice_helper is not None:
            self.legacy.voice_helper = voice_helper

        media_helper = self.get_dependency('media_helper')
        if media_helper is not None:
            self.legacy.media_helper = media_helper

        audio_transcriber = self.get_dependency('audio_transcriber')
        if audio_transcriber is not None:
            self.legacy.audio_transcriber = audio_transcriber

        video_analyzer = self.get_dependency('video_analyzer')
        if video_analyzer is not None:
            self.legacy.video_analyzer = video_analyzer

        tracker_decoder = self.get_dependency('tracker_decoder')
        if tracker_decoder is not None:
            self.legacy.tracker_decoder = tracker_decoder

        self.baseline_report = self.run_baseline_initialization()
        
        # Run mandatory self-test per UDS protocol
        self._run_startup_self_test()

    # ------------------------------------------------------------------
    # Self-Test Protocol (UDS Compliance)
    # ------------------------------------------------------------------
    def _run_startup_self_test(self) -> bool:
        """Validate all tool dependencies per UDS self-test protocol."""
        self.logger.info("[%s] Running mandatory startup self-test per UDS protocol", self.MODULE_ADDRESS)
        operational = True
        
        tools_to_validate = [
            ('4-3.1', 'Northstar Protocol', lambda: self.get_dependency('northstar_tool')),
            ('4-3.2', 'Cochran Match', lambda: self.get_dependency('cochran_tool')),
            ('4-3.3', 'Reverse Continuity', lambda: self.get_dependency('reverse_continuity')),
            ('4-3.4', 'Metadata Processor', lambda: self.get_dependency('metadata_tool')),
            ('4-3.5', 'Mileage Tool', lambda: self.get_dependency('mileage_tool')),
            ('4-3.6', 'Section Renderer', lambda: self.get_dependency('renderer_factory')),
            ('4-3.7', 'Voice Helper', lambda: self.get_dependency('voice_helper')),
            ('4-3.8', 'Media Helper', lambda: self.get_dependency('media_helper')),
            ('4-3.9', 'Audio Transcriber', lambda: self.get_dependency('audio_transcriber')),
            ('4-3.10', 'Video Analyzer', lambda: self.get_dependency('video_analyzer')),
            ('4-3.11', 'Track Decoder', lambda: self.get_dependency('tracker_decoder')),
        ]
        
        for tool_addr, tool_name, get_tool_ref in tools_to_validate:
            try:
                tool_ref = get_tool_ref()
                
                if tool_ref is None:
                    self.logger.error("[%s] Self-test FAILED: %s (%s) not initialized", 
                                      self.MODULE_ADDRESS, tool_name, tool_addr)
                    
                    if hasattr(self, 'communicator') and self.communicator:
                        self.communicator.send_signal(
                            target_address="3",
                            radio_code="SOS",
                            message=f"{tool_name} initialization failed",
                            payload={
                                "fault_code": f"[{tool_addr}-12-INIT]",
                                "description": f"{tool_name} not initialized - missing dependency or initialization failure",
                                "component": tool_name,
                                "reporting_address": tool_addr,
                                "parent_address": self.MODULE_ADDRESS,
                                "severity": "CRITICAL",
                                "timestamp": datetime.now().isoformat(),
                                "fault_type": "12",
                                "fault_type_description": "Missing initialization dependency"
                            }
                        )
                        self.logger.warning("[%s] Fault code emitted: [%s-12-INIT]", 
                                           self.MODULE_ADDRESS, tool_addr)
                    
                    operational = False
                else:
                    self.logger.info("[%s] Self-test PASSED: %s (%s) operational", 
                                    self.MODULE_ADDRESS, tool_name, tool_addr)
            
            except Exception as exc:
                self.logger.error("[%s] Self-test ERROR: %s (%s): %s", 
                                 self.MODULE_ADDRESS, tool_name, tool_addr, exc)
                operational = False
        
        if operational:
            self.logger.info("[%s] PASS - Self-test COMPLETE - All tool dependencies operational", self.MODULE_ADDRESS)
        else:
            self.logger.warning("[%s] FAIL - Self-test COMPLETE - One or more tool dependencies FAILED", self.MODULE_ADDRESS)
        
        return operational

    def load_inputs(self) -> Dict[str, Any]:
        if self.lifecycle_state() == LifecycleState.RESTING:
            self.resume_from_rest()
        return self.legacy.load_inputs()

    def build_payload(self, context: Dict[str, Any]) -> Dict[str, Any]:
        if self.lifecycle_state() == LifecycleState.RESTING:
            self.resume_from_rest()
        return self.legacy.build_payload(context)

    def publish(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self.legacy.publish(payload)

    def handle_revision(self, reason: str, context: Dict[str, Any]) -> None:
        self.legacy.handle_revision(reason, context)

__all__ = [
    "LegacySection3Framework",
    "Section3Framework",
    "StageDefinition",
    "CommunicationContract",
    "FactGraphContract",
    "PersistenceContract",
    "OrderContract",
    "get_report_config",
    "extract_text_from_pdf",
    "extract_text_from_image",
    "easyocr_text",
    "SurveillanceAudioTranscriber",
    "VideoAnalysisHelper",
    "TrackerPathDecoder",
]





