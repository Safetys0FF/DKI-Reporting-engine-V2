"""Framework template for Section 6 (Billing Summary)."""

from __future__ import annotations

import json
import logging
import os
import re
import zipfile
import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple, Set
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


class SectionFramework:
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
    ) -> None:
        self.gateway = gateway
        self.ecc = ecc
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        self.queue_client: Optional[Any] = None
        self.storage: Optional[Any] = None
        self.fact_graph_client: Optional[Any] = None
        self.revision_depth: int = 0
        self.signed_payload_id: Optional[str] = None

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

# === Section 6 Specialized Components ===

class BodyTextSwitchboard:
    """Controls narrative injection and field rendering logic for Section 6"""
    
    def __init__(self, mode: str):
        self.mode = mode.upper()
        self.logic = self._build_logic()

    def _build_logic(self) -> Dict[str, Any]:
        if self.mode == "INVESTIGATIVE":
            return {
                "title": "SECTION 6 – BILLING SUMMARY (INVESTIGATIVE)",
                "sections": [
                    "Investigation Overview",
                    "Research & Analysis", 
                    "Documentation Time",
                    "Compliance Notes"
                ],
                "summary_rules": ["Include contract terms, PO, background steps taken."],
                "field_visibility": False,
                "voice_notes_included": True,
                "mileage_statement": None,
            }

        elif self.mode == "FIELD":
            return {
                "title": "SECTION 6 – BILLING SUMMARY (FIELD OPERATIONS)",
                "sections": [
                    "Surveillance Summary",
                    "Field Logs Verified",
                    "Prep Allocation", 
                    "Documentation Fee"
                ],
                "summary_rules": ["Ensure time in/out aligns with Section 3.", "Match narrative with visuals."],
                "field_visibility": True,
                "voice_notes_included": True,
                "mileage_statement": "Mileage was waived as a professional courtesy.",
            }

        elif self.mode == "HYBRID":
            return {
                "title": "SECTION 6 – BILLING SUMMARY (HYBRID SERVICES)",
                "sections": [
                    "Investigation Findings",
                    "Surveillance Results",
                    "Joint Documentation",
                    "Compliance and Review"
                ],
                "summary_rules": [
                    "Tie Sections 2–5 together.",
                    "Flag any overages or field time gaps.",
                    "Mark recon as visible but not billed."
                ],
                "field_visibility": True,
                "voice_notes_included": True,
                "mileage_statement": "Mileage was waived as a professional courtesy.",
            }

        return {
            "title": "SECTION 6 – BILLING SUMMARY",
            "sections": ["Billing Narrative Not Specified"],
            "summary_rules": ["Fallback mode. Check upstream inputs."],
            "field_visibility": False,
            "voice_notes_included": False,
            "mileage_statement": None,
        }

    def get_narrative_blocks(self) -> List[str]:
        return self.logic.get("sections", [])

    def get_title(self) -> str:
        return self.logic.get("title")

    def include_voice_notes(self) -> bool:
        return self.logic.get("voice_notes_included", False)

    def show_mileage_statement(self) -> str:
        return self.logic.get("mileage_statement") or ""

    def get_summary_rules(self) -> List[str]:
        return self.logic.get("summary_rules", [])

    def is_field_visible(self) -> bool:
        return self.logic.get("field_visibility", False)


class ToolInjectionLogic:
    """Frontline + Validation Tool Orchestration for Section 6"""
    
    def __init__(self):
        self.reader = None
        if OCR_AVAILABLE:
            try:
                self.reader = easyocr.Reader(['en'])
            except Exception:
                self.reader = None

    def run_ocr(self, path: str, file_type: str) -> Dict[str, Any]:
        """Run OCR on documents"""
        if not OCR_AVAILABLE:
            return {"error": "OCR not available"}
            
        try:
            if file_type == "image":
                text = pytesseract.image_to_string(Image.open(path))
                if text.strip():
                    return {"engine": "tesseract", "text": text.strip()}
                if self.reader:
                    result = self.reader.readtext(path, detail=0)
                    return {"engine": "easyocr", "text": " ".join(result)}
            elif file_type == "pdf":
                elements = partition_pdf(filename=path)
                return {"engine": "unstructured", "text": "\n".join([e.text for e in elements if hasattr(e, 'text')])}
        except Exception as e:
            return {"error": str(e)}
        return {"error": "OCR processing failed"}

    def run_validation_suite(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Run comprehensive validation suite"""
        results = {}

        # Mileage Tool
        results["mileage_audit"] = MileageToolV2.audit_mileage()

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
            results["metadata_audit"] = MetadataToolV5.process_zip(zip_path, output_dir)

        # Identity Checks
        ids = []
        subjects = context.get("subjects", [])
        candidates = context.get("candidates", [])
        for subject, candidate in zip(subjects, candidates):
            ids.append(CochranMatchTool.verify_identity(subject, candidate))
        results["identity_checks"] = ids

        # Asset Classification (Northstar)
        results["northstar"] = NorthstarProtocolTool.process_assets(context.get("assets", []))

        return results

# === Timestamp Management and Billing Adjustment System ===

class TimestampAdjustmentEngine:
    """Handles timestamp conversion to 24hr format and +/- 30 minute billing adjustments"""
    
    def __init__(self):
        self.travel_buffer_minutes = 30
        self.adjustment_log = []
        
    def convert_to_24hr_format(self, timestamp_str: str) -> str:
        """Convert any timestamp format to 24-hour format"""
        try:
            # Handle various input formats
            if isinstance(timestamp_str, datetime):
                return timestamp_str.strftime("%H:%M")
            
            timestamp_str = str(timestamp_str).strip()
            
            # Parse different formats
            for fmt in ["%H:%M", "%I:%M %p", "%I:%M%p", "%H:%M:%S", "%I:%M:%S %p"]:
                try:
                    dt = datetime.strptime(timestamp_str, fmt)
                    return dt.strftime("%H:%M")
                except ValueError:
                    continue
            
            # If no format matches, try to extract time components
            import re
            time_match = re.search(r'(\d{1,2}):(\d{2})(?::(\d{2}))?\s*(am|pm)?', timestamp_str.lower())
            if time_match:
                hour, minute, second, period = time_match.groups()
                hour = int(hour)
                minute = int(minute)
                
                if period == 'pm' and hour != 12:
                    hour += 12
                elif period == 'am' and hour == 12:
                    hour = 0
                    
                return f"{hour:02d}:{minute:02d}"
            
            return timestamp_str  # Return original if can't parse
            
        except Exception as e:
            return timestamp_str  # Return original on error
    
    def apply_travel_buffer(self, start_time: str, end_time: str, operation_type: str = "surveillance") -> Dict[str, str]:
        """Apply +/- 30 minute travel buffer to surveillance times"""
        try:
            start_24hr = self.convert_to_24hr_format(start_time)
            end_24hr = self.convert_to_24hr_format(end_time)
            
            # Parse times
            start_dt = datetime.strptime(start_24hr, "%H:%M")
            end_dt = datetime.strptime(end_24hr, "%H:%M")
            
            # Apply travel buffer
            pre_surveillance = start_dt - timedelta(minutes=self.travel_buffer_minutes)
            post_surveillance = end_dt + timedelta(minutes=self.travel_buffer_minutes)
            
            adjusted_start = pre_surveillance.strftime("%H:%M")
            adjusted_end = post_surveillance.strftime("%H:%M")
            
            # Log the adjustment
            adjustment_record = {
                "original_start": start_24hr,
                "original_end": end_24hr,
                "adjusted_start": adjusted_start,
                "adjusted_end": adjusted_end,
                "operation_type": operation_type,
                "buffer_minutes": self.travel_buffer_minutes,
                "timestamp": datetime.now().isoformat()
            }
            self.adjustment_log.append(adjustment_record)
            
            return {
                "start_time": adjusted_start,
                "end_time": adjusted_end,
                "original_start": start_24hr,
                "original_end": end_24hr,
                "adjustment_applied": True
            }
            
        except Exception as e:
            return {
                "start_time": start_time,
                "end_time": end_time,
                "adjustment_applied": False,
                "error": str(e)
            }
    
    def verify_timestamp_consistency(self, section3_times: List[Dict], section4_times: List[Dict]) -> Dict[str, Any]:
        """Verify timestamp consistency between Section 3 and Section 4"""
        verification_results = {
            "consistent": True,
            "discrepancies": [],
            "total_hours_section3": 0,
            "total_hours_section4": 0,
            "recommended_adjustments": []
        }
        
        try:
            # Calculate total hours for each section
            section3_total = self._calculate_total_hours(section3_times)
            section4_total = self._calculate_total_hours(section4_times)
            
            verification_results["total_hours_section3"] = section3_total
            verification_results["total_hours_section4"] = section4_total
            
            # Check for discrepancies
            if abs(section3_total - section4_total) > 0.1:  # Allow 6 minute tolerance
                verification_results["consistent"] = False
                verification_results["discrepancies"].append({
                    "type": "hour_mismatch",
                    "section3_hours": section3_total,
                    "section4_hours": section4_total,
                    "difference": abs(section3_total - section4_total)
                })
            
            # Check individual session consistency
            for i, (s3_session, s4_session) in enumerate(zip(section3_times, section4_times)):
                s3_start = self.convert_to_24hr_format(s3_session.get("start_time", ""))
                s3_end = self.convert_to_24hr_format(s3_session.get("end_time", ""))
                s4_start = self.convert_to_24hr_format(s4_session.get("start_time", ""))
                s4_end = self.convert_to_24hr_format(s4_session.get("end_time", ""))
                
                if s3_start != s4_start or s3_end != s4_end:
                    verification_results["consistent"] = False
                    verification_results["discrepancies"].append({
                        "type": "session_mismatch",
                        "session_index": i,
                        "section3": {"start": s3_start, "end": s3_end},
                        "section4": {"start": s4_start, "end": s4_end}
                    })
            
            # Generate recommended adjustments
            if not verification_results["consistent"]:
                verification_results["recommended_adjustments"] = self._generate_adjustment_recommendations(
                    verification_results["discrepancies"]
                )
            
        except Exception as e:
            verification_results["error"] = str(e)
            verification_results["consistent"] = False
        
        return verification_results
    
    def _calculate_total_hours(self, time_sessions: List[Dict]) -> float:
        """Calculate total hours from time sessions"""
        total_minutes = 0
        
        for session in time_sessions:
            try:
                start_time = self.convert_to_24hr_format(session.get("start_time", ""))
                end_time = self.convert_to_24hr_format(session.get("end_time", ""))
                
                start_dt = datetime.strptime(start_time, "%H:%M")
                end_dt = datetime.strptime(end_time, "%H:%M")
                
                # Handle overnight sessions
                if end_dt < start_dt:
                    end_dt += timedelta(days=1)
                
                session_minutes = (end_dt - start_dt).total_seconds() / 60
                total_minutes += session_minutes
                
            except Exception:
                continue
        
        return round(total_minutes / 60, 2)
    
    def _generate_adjustment_recommendations(self, discrepancies: List[Dict]) -> List[Dict]:
        """Generate specific adjustment recommendations"""
        recommendations = []
        
        for discrepancy in discrepancies:
            if discrepancy["type"] == "hour_mismatch":
                recommendations.append({
                    "action": "align_total_hours",
                    "description": f"Adjust Section 3 or Section 4 to match total hours",
                    "priority": "high"
                })
            elif discrepancy["type"] == "session_mismatch":
                recommendations.append({
                    "action": "sync_session_times",
                    "description": f"Synchronize start/end times for session {discrepancy['session_index']}",
                    "priority": "medium"
                })
        
        return recommendations
    
    def get_adjustment_log(self) -> List[Dict]:
        """Get complete log of all timestamp adjustments"""
        return self.adjustment_log.copy()
    
    def clear_adjustment_log(self):
        """Clear the adjustment log (use with caution)"""
        self.adjustment_log.clear()

# === Enhanced Contract-Based Report Logic ===
def get_report_config(contract_history):
    """Enhanced contract analysis with Section 6-specific configurations"""
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
    
    # Section 6-specific report configurations
    report_configs = {
        "Investigative": {
            "label": "SECTION 6 – BILLING SUMMARY (INVESTIGATIVE)",
            "billing": "Flat",
            "clause": "investigation_only",
            "modules": {
                "active": ["investigation_overview", "research_analysis", "documentation_time", "compliance_notes"],
                "inactive": ["surveillance_summary", "field_logs", "prep_allocation"]
            },
            "effects": {
                "hide": ["field_operations", "surveillance_billing"],
                "tag": "Investigation Billing"
            }
        },
        "Surveillance": {
            "label": "SECTION 6 – BILLING SUMMARY (FIELD OPERATIONS)", 
            "billing": "Hourly",
            "clause": "field_operations",
            "modules": {
                "active": ["surveillance_summary", "field_logs_verified", "prep_allocation", "documentation_fee"],
                "inactive": []
            },
            "effects": {
                "render_all": True,
                "tag": "Field Operations Billing"
            }
        },
        "Hybrid": {
            "label": "SECTION 6 – BILLING SUMMARY (HYBRID SERVICES)",
            "billing": "Hybrid", 
            "clause": "mixed_billing",
            "modules": {
                "active": ["investigation_findings", "surveillance_results", "joint_documentation", "compliance_review"],
                "inactive": []
            },
            "effects": {
                "forced_render_order": ["investigation_segment", "field_operations"],
                "contract_order_required": True,
                "tag": "Hybrid Services Billing"
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

class Section6BillingRenderer:
    """Renders Section 6 - Billing Summary with contract-based logic"""

    def __init__(self):
        self.section_id = "section_6"
        # ASCII-only to avoid encoding issues across logs/exports
        self.section_title = "SECTION 6 - BILLING SUMMARY"
        self.hourly_rate = 100.00
        self.planning_budget = 500.00
        self.documentation_fee = 100.00
        logger.info("Section 6 Billing Renderer initialized")

    def render_data_model(self, processed_data: Dict[str, Any], report_type: str) -> Dict[str, Any]:
        """Generate billing data model based on processed data and report type"""

        logger.info(f"Generating billing data model for {report_type}")

        # Extract contract and billing information
        contract_total = float(processed_data.get('contract_total', 3000.00))
        prep_cost = float(processed_data.get('prep_cost', 500.00))
        subcontractor_cost = float(processed_data.get('subcontractor_cost', 1275.00))

        # Calculate remaining operations budget
        remaining_ops = contract_total - prep_cost - subcontractor_cost

        # Generate billing sections based on report type
        billing_sections = self._generate_billing_sections(
            report_type, contract_total, prep_cost, subcontractor_cost, remaining_ops
        )

        # Calculate totals and margins
        total_costs = prep_cost + subcontractor_cost
        internal_margin = remaining_ops - total_costs if remaining_ops > total_costs else 0.0

        billing_data = {
            'contract_total': contract_total,
            'prep_cost': prep_cost,
            'subcontractor_cost': subcontractor_cost,
            'remaining_ops_budget': remaining_ops,
            'total_costs': total_costs,
            'internal_margin': internal_margin,
            'billing_sections': billing_sections,
            'report_type': report_type,
            'generated_at': datetime.now().isoformat(),
            'notes': self._generate_billing_notes(report_type, remaining_ops, total_costs),
        }

        logger.info(
            f"Billing data model generated: contract=${contract_total:,.2f} margin=${internal_margin:,.2f}"
        )
        return billing_data

    def _generate_billing_sections(
        self,
        report_type: str,
        contract_total: float,
        prep_cost: float,
        subcontractor_cost: float,
        remaining_ops: float,
    ) -> List[Dict[str, Any]]:
        """Generate billing breakdown sections based on report type"""

        if report_type == "Investigative":
            return [
                {
                    'category': 'Investigation Planning',
                    'description': 'Case analysis, strategy development, resource allocation',
                    'amount': prep_cost,
                    'type': 'fixed',
                },
                {
                    'category': 'Field Investigation',
                    'description': 'On-site investigation, surveillance, interviews',
                    'amount': subcontractor_cost * 0.7,
                    'type': 'variable',
                },
                {
                    'category': 'Research & Analysis',
                    'description': 'Background checks, public records, data analysis',
                    'amount': subcontractor_cost * 0.3,
                    'type': 'variable',
                },
                {
                    'category': 'Documentation & Reporting',
                    'description': 'Report compilation, evidence organization, final documentation',
                    'amount': self.documentation_fee,
                    'type': 'fixed',
                },
            ]

        if report_type in {"Field", "Surveillance"}:
            return [
                {
                    'category': 'Field Operations',
                    'description': 'On-site surveillance, evidence collection, photography',
                    'amount': subcontractor_cost * 0.8,
                    'type': 'variable',
                },
                {
                    'category': 'Travel & Logistics',
                    'description': 'Transportation, equipment, operational support',
                    'amount': subcontractor_cost * 0.2,
                    'type': 'variable',
                },
                {
                    'category': 'Planning & Coordination',
                    'description': 'Operation planning, team coordination, briefings',
                    'amount': prep_cost,
                    'type': 'fixed',
                },
            ]

        # Hybrid by default
        return [
            {
                'category': 'Investigation Planning',
                'description': 'Combined planning across investigative and field operations',
                'amount': prep_cost * 0.6,
                'type': 'fixed',
            },
            {
                'category': 'Field Operations',
                'description': 'Surveillance, interviews, evidence collection',
                'amount': subcontractor_cost * 0.6,
                'type': 'variable',
            },
            {
                'category': 'Research & Analysis',
                'description': 'Background investigation, data analysis, verification',
                'amount': subcontractor_cost * 0.4,
                'type': 'variable',
            },
            {
                'category': 'Administrative',
                'description': 'Documentation, reporting, client coordination',
                'amount': prep_cost * 0.4,
                'type': 'fixed',
            },
        ]

    def _generate_billing_notes(self, report_type: str, remaining_ops: float, total_costs: float) -> List[str]:
        """Generate billing notes and observations"""

        notes: List[str] = []

        if remaining_ops > total_costs:
            notes.append("No overage. Standard $500 applied clean.")
        elif remaining_ops == total_costs:
            notes.append("Budget utilized at 100% efficiency.")
        else:
            overage = total_costs - remaining_ops
            notes.append(f"Overage of ${overage:.2f} requires client approval.")

        if report_type == "Investigative":
            notes.append("Investigation-focused billing structure applied.")
        elif report_type in {"Field", "Surveillance"}:
            notes.append("Field operations billing structure applied.")
        else:
            notes.append("Hybrid investigation/field billing structure applied.")

        return notes

    # Gateway-compatible rendering API
    def render_model(self, section_payload: Dict[str, Any], case_sources: Dict[str, Any] = None) -> Dict[str, Any]:
        """Return a structured render model for Gateway/ReportGenerator using specialized switchboard logic."""

        payload = section_payload or {}
        report_meta = payload.get('report_meta', {})
        report_type = (
            report_meta.get('report_type')
            or (case_sources or {}).get('report_type')
            or 'Investigative'
        )

        # Use specialized BodyTextSwitchboard for Section 6
        switchboard = BodyTextSwitchboard(report_type)
        
        billing_hint = payload.get('billing_data') or {}
        processed = {
            'contract_total': payload.get('contract_total') or billing_hint.get('contract_total') or 3000.00,
            'prep_cost': payload.get('prep_cost') or billing_hint.get('prep_cost') or 500.00,
            'subcontractor_cost': payload.get('subcontractor_cost') or billing_hint.get('subcontractor_cost') or 1275.00,
        }

        model = self.render_data_model(processed, report_type)

        blocks: List[Dict[str, Any]] = []
        
        # Use switchboard title
        blocks.append({
            'type': 'title',
            'text': switchboard.get_title(),
            'style': {"font": "Times New Roman", "size_pt": 16, "bold": True,
                      "all_caps": True, "align": "center", "spacing": 1.15},
        })

        # Contract overview
        blocks.append({'type': 'header', 'text': 'CONTRACT OVERVIEW'})
        blocks.append({'type': 'field', 'label': 'Total Contract Value', 'value': f"${model['contract_total']:,.2f}"})
        blocks.append({'type': 'field', 'label': 'Report Type', 'value': model['report_type']})

        # Use switchboard narrative blocks
        narrative_blocks = switchboard.get_narrative_blocks()
        blocks.append({'type': 'header', 'text': 'BILLING BREAKDOWN'})
        
        for i, section in enumerate(narrative_blocks):
            if i < len(model.get('billing_sections', [])):
                sec = model['billing_sections'][i]
                blocks.append({'type': 'field', 'label': section, 'value': f"${sec.get('amount', 0):,.2f}"})
                if sec.get('description'):
                    blocks.append({'type': 'paragraph', 'text': sec['description']})
            else:
                blocks.append({'type': 'field', 'label': section, 'value': '$0.00'})

        # Financial summary
        blocks.append({'type': 'header', 'text': 'FINANCIAL SUMMARY'})
        blocks.append({'type': 'field', 'label': 'Preparation Costs', 'value': f"${model['prep_cost']:,.2f}"})
        blocks.append({'type': 'field', 'label': 'Subcontractor Costs', 'value': f"${model['subcontractor_cost']:,.2f}"})
        blocks.append({'type': 'field', 'label': 'Total Direct Costs', 'value': f"${model['total_costs']:,.2f}"})
        blocks.append({'type': 'field', 'label': 'Remaining Operations Budget', 'value': f"${model['remaining_ops_budget']:,.2f}"})
        blocks.append({'type': 'field', 'label': 'Internal Margin', 'value': f"${model['internal_margin']:,.2f}"})

        # Add mileage statement if applicable
        mileage_statement = switchboard.show_mileage_statement()
        if mileage_statement:
            blocks.append({'type': 'paragraph', 'text': mileage_statement})

        # Notes
        notes = model.get('notes') or []
        if notes:
            blocks.append({'type': 'header', 'text': 'BILLING NOTES'})
            for n in notes:
                blocks.append({'type': 'paragraph', 'text': f"- {n}"})

        # Add summary rules from switchboard
        summary_rules = switchboard.get_summary_rules()
        if summary_rules:
            blocks.append({'type': 'header', 'text': 'COMPLIANCE NOTES'})
            for rule in summary_rules:
                blocks.append({'type': 'paragraph', 'text': f"• {rule}"})

        manifest = {
            'section_key': self.section_id,
            'title': switchboard.get_title(),
            'fields_rendered': [
                'contract_total', 'prep_cost', 'subcontractor_cost',
                'remaining_ops_budget', 'internal_margin'
            ],
            'generated_at': model.get('generated_at'),
            'switchboard_mode': report_type,
            'field_visibility': switchboard.is_field_visible(),
            'voice_notes_included': switchboard.include_voice_notes(),
        }

        return {
            'render_tree': blocks,
            'manifest': manifest,
            'billing_model': model,
            'handoff': 'gateway',
        }

    def render_docx_section(self, billing_data: Dict[str, Any]) -> str:
        """Render Section 6 as formatted text for DOCX insertion (text-only)."""

        logger.info("Rendering Section 6 billing summary for DOCX")

        content: List[str] = []
        content.append(self.section_title)
        content.append("=" * len(self.section_title))
        content.append("")

        # Contract Overview
        content.append("CONTRACT OVERVIEW")
        content.append("-" * 17)
        content.append(f"Total Contract Value: ${billing_data['contract_total']:,.2f}")
        content.append(f"Report Type: {billing_data['report_type']}")
        content.append("")

        # Billing Breakdown
        content.append("BILLING BREAKDOWN")
        content.append("-" * 16)

        for section in billing_data.get('billing_sections', []) or []:
            content.append(f"{section['category']}: ${section['amount']:,.2f}")
            if section.get('description'):
                content.append(f"  {section['description']}")
            content.append("")

        # Financial Summary
        content.append("FINANCIAL SUMMARY")
        content.append("-" * 16)
        content.append(f"Preparation Costs: ${billing_data['prep_cost']:,.2f}")
        content.append(f"Subcontractor Costs: ${billing_data['subcontractor_cost']:,.2f}")
        content.append(f"Total Direct Costs: ${billing_data['total_costs']:,.2f}")
        content.append(f"Remaining Operations Budget: ${billing_data['remaining_ops_budget']:,.2f}")
        content.append(f"Internal Margin: ${billing_data['internal_margin']:,.2f}")
        content.append("")

        # Notes
        if billing_data.get('notes'):
            content.append("BILLING NOTES")
            content.append("-" * 12)
            for note in billing_data['notes']:
                content.append(f"- {note}")
            content.append("")

        # Footer
        content.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        return "\n".join(content)


# Test the renderer
if __name__ == "__main__":
    test_data = {
        'contract_total': 3000.00,
        'prep_cost': 500.00,
        'subcontractor_cost': 1275.00,
    }
    renderer = Section6BillingRenderer()
    for report_type in ["Investigative", "Field", "Surveillance", "Hybrid"]:
        print(f"\n=== Testing {report_type} Report ===")
        billing_data = renderer.render_data_model(test_data, report_type)
        print(f"Contract Total: ${billing_data['contract_total']:.2f}")
        print(f"Prep Cost: ${billing_data['prep_cost']:.2f}")
        print(f"Subcontractor Cost: ${billing_data['subcontractor_cost']:.2f}")
        print(f"Remaining Ops Budget: ${billing_data['remaining_ops_budget']:.2f}")
        print(f"Internal Margin: ${billing_data['internal_margin']:.2f}")
        print(f"Notes: {billing_data['notes']}")


INVESTIGATIVE_HEADING = "SECTION 6 - BILLING SUMMARY (INVESTIGATIVE)"
FIELD_HEADING = "SECTION 6 - BILLING SUMMARY (FIELD OPERATIONS)"
HYBRID_HEADING = "SECTION 6 - BILLING SUMMARY (HYBRID SERVICES)"
STANDARD_RATES = {
    'hourly_rate': 100.0,
    'planning_budget': 500.0,
    'documentation_fee': 100.0,
    'mileage_rate': 0.0,
}


class Section6Framework(SectionFramework):
    SECTION_ID = "section_6_billing"
    BUS_SECTION_ID = "section_6"
    MAX_RERUNS = 2
    STAGES = (
        StageDefinition(
            name="intake",
            description="Pull billing bundle, confirm upstream hashes, and load contract terms.",
            checkpoint="s6_intake_logged",
            guardrails=("order_lock", "async_queue", "persistence_snapshot"),
            inputs=("case_metadata", "contract_terms", "planning_manifest", "surveillance_manifest"),
            outputs=("intake_context",),
        ),
        StageDefinition(
            name="aggregate",
            description="Compute hours, mileage, subcontractor, and preparation costs.",
            checkpoint="s6_aggregate_complete",
            guardrails=("schema_validation", "mileage_validation", "cochran_check"),
            inputs=("surveillance_manifest", "mileage_data", "toolkit_results"),
            outputs=("aggregated_totals",),
        ),
        StageDefinition(
            name="validate",
            description="Apply contract rules, scope compliance, and QA checks.",
            checkpoint="s6_validated",
            guardrails=("manual_queue_routes", "risk_threshold", "immutability_precheck"),
            inputs=("aggregated_totals", "document_references"),
            outputs=("validated_billing",),
        ),
        StageDefinition(
            name="publish",
            description="Publish billing payload, emit billing signal, and persist audit log.",
            checkpoint="section_6_completed",
            guardrails=("durable_persistence", "signal_emission", "immutability"),
            inputs=("validated_billing",),
            outputs=("gateway_handoff",),
        ),
        StageDefinition(
            name="monitor",
            description="Handle revisions and manual adjustments within rerun limits.",
            checkpoint="s6_revision_processed",
            guardrails=("max_reruns", "revision_depth_cap", "fact_graph_consistency"),
        ),
    )
    COMMUNICATION = CommunicationContract(
        prepare_signal="section_3_logs.completed",
        input_channels=(
            "case_metadata",
            "contract_terms",
            "planning_manifest",
            "surveillance_manifest",
            "mileage_data",
            "toolkit_results",
            "document_references",
            "manual_annotations",
        ),
        output_signal="section_6_billing.completed",
        revision_signal="billing_revision_requested",
    )
    ORDER = OrderContract(
        execution_after=("section_3_logs", "section_2_planning", "section_1_profile", "section_5_documents"),
        export_after=("section_7", "section_fr", "section_finance"),
        export_priority=60,
    )

    def __init__(self, gateway: Any, ecc: Optional[Any] = None) -> None:
        super().__init__(gateway=gateway, ecc=ecc)
        self._last_context: Dict[str, Any] = {}
        self.timestamp_engine = TimestampAdjustmentEngine()

    def load_inputs(self) -> Dict[str, Any]:
        try:
            self._guard_execution("input loading")
            bundle = self.gateway.get_section_inputs("section_6") if self.gateway else {}
            context = {
                "raw_inputs": bundle,
                "case_metadata": bundle.get("case_metadata", {}),
                "contract_terms": bundle.get("contract_terms", {}),
                "planning_manifest": bundle.get("planning_manifest", {}),
                "surveillance_manifest": bundle.get("surveillance_manifest", {}),
                "mileage_data": bundle.get("mileage_data", {}),
                "toolkit_results": bundle.get("toolkit_results", {}),
                "document_references": bundle.get("document_references", {}),
                "manual_annotations": bundle.get("manual_annotations", []),
            }
            sessions = context.get("surveillance_manifest", {}).get("sessions") or []
            if isinstance(sessions, dict):
                sessions = list(sessions.values())
            context["surveillance_manifest"]["sessions"] = sessions
            context["basic_stats"] = {
                "session_count": len(sessions),
                "contract_total": context.get("contract_terms", {}).get("contract_total"),
            }
            context = self._augment_with_bus_context(context)
            self.logger.debug("Section 6 inputs loaded: %s", context["basic_stats"])
            self._last_context = context
            return context
        except Exception as exc:
            self.logger.exception("Failed to load inputs for %s: %s", self.SECTION_ID, exc)
            return {}

    def build_payload(self, context: Dict[str, Any]) -> Dict[str, Any]:
        try:
            self._guard_execution("payload building")
            self._last_context = context
            
            # Get contract-based report configuration
            contract_history = context.get("case_metadata", {}).get("contracts", [])
            report_config = get_report_config(contract_history)
            report_type = report_config["report_type"]
            contract_config = report_config["config"]
            
            # Determine active components based on contract and ECC whitelist
            ecc_whitelist = getattr(self.ecc, 'whitelist', []) if self.ecc else []
            modules_config = contract_config.get("modules", {})
            active_modules = modules_config.get("active", [])
            
            # Apply whitelist filtering
            active_components = []
            for module in active_modules:
                if not ecc_whitelist or module in ecc_whitelist:
                    active_components.append(module)
            
            # Apply hide effects
            hide_effects = contract_config.get("effects", {}).get("hide", [])
            if "field_operations" in hide_effects:
                active_components = [comp for comp in active_components if "surveillance" not in comp.lower()]
            
            case_mode = self._determine_case_mode(context)
            billing_data, meta = self._aggregate_billing(context, case_mode)
            notes = self._compose_notes(case_mode, context, meta)
            tool_results = self._run_inline_tools(context, billing_data)
            qa_flags = set(meta.get("qa_flags", []))
            qa_flags.update(tool_results.get("qa_flags", []))
            
            payload: Dict[str, Any] = {
                "section_heading": contract_config.get("label", self._case_heading(case_mode)),
                "report_type": report_type,
                "whitelist_applied": active_components,
                "contract_config": contract_config,
                "active_components": active_components,
                "contract_total": billing_data.get("contract_total"),
                "prep_cost": billing_data.get("prep_cost"),
                "subcontractor_cost": billing_data.get("subcontractor_cost"),
                "billing_data": billing_data,
                "report_meta": {"report_type": case_mode.capitalize()},
                "qa_flags": sorted(qa_flags),
                "notes": notes,
                "tool_results": tool_results,
                "manual_queue": meta.get("manual_queue", []),
            }
            if context.get("bus_state") is not None:
                payload.setdefault("bus_state", context.get("bus_state"))
            if context.get("section_evidence") is not None:
                payload.setdefault("section_evidence", context.get("section_evidence"))
            if context.get("section_needs") is not None:
                payload.setdefault("section_needs", context.get("section_needs"))
            if context.get("manifest_context") is not None:
                payload.setdefault("manifest_context", context.get("manifest_context"))
            section_bus_id = self.bus_section_id()
            if section_bus_id:
                payload.setdefault("section_id", section_bus_id)
            case_id = context.get("case_id") or context.get("bus_state", {}).get("case_id")
            if case_id:
                payload.setdefault("case_id", case_id)
            return payload
        except Exception as exc:
            self.logger.exception("Failed to build payload for %s: %s", self.SECTION_ID, exc)
            return {"error": str(exc)}

    def publish(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        self.ensure_section_available("publish")

        narrative = None
        manifest: Dict[str, Any] = {}

        if Section6BillingRenderer:
            try:
                renderer = Section6BillingRenderer()
                model = renderer.render_model(payload, case_sources={})
                manifest = model.get("manifest", {})
                narrative = self._render_narrative(model)
            except Exception:
                self.logger.exception("Section 6 renderer failed; falling back to summary")

        if narrative is None:
            narrative = self._fallback_narrative(payload)

        section_bus_id = self.bus_section_id() or "section_6"
        timestamp = datetime.now().isoformat()
        summary = narrative.splitlines()[0] if narrative else ""
        summary = summary[:320]

        result = {
            "section_id": section_bus_id,
            "case_id": payload.get("case_id"),
            "payload": payload,
            "manifest": manifest or payload,
            "narrative": narrative,
            "summary": summary,
            "metadata": {"published_at": timestamp, "section": self.SECTION_ID},
            "source": "section_6_framework",
        }

        try:
            if hasattr(self.gateway, "publish_section_result"):
                self.gateway.publish_section_result(section_bus_id, result)
            if hasattr(self.gateway, "emit"):
                emit_payload = dict(result)
                emit_payload.setdefault("published_at", timestamp)
                if self.COMMUNICATION and self.COMMUNICATION.output_signal:
                    self.gateway.emit(self.COMMUNICATION.output_signal, emit_payload)
                self.gateway.emit("billing_ready", manifest or payload)
        except Exception:
            self.logger.exception("Gateway publish for section_6 failed")

        if self.ecc:
            try:
                self.ecc.mark_complete(self.SECTION_ID)
            except Exception:
                self.logger.exception("ECC completion for section_6 failed")

        return {"status": "published", "narrative": narrative, "manifest": manifest or payload}
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
            "hybrid": "hybrid",
            "mixed": "hybrid",
        }
        if report_type in mapping:
            return mapping[report_type]
        contracts = context.get("contract_terms", {}).get("contracts") or []
        has_field = any((c.get("type") or "").lower() in {"field", "surveillance"} for c in contracts)
        has_investigative = any((c.get("type") or "").lower() in {"investigative", "analysis"} for c in contracts)
        if has_field and has_investigative:
            return "hybrid"
        if has_field:
            return "field"
        if has_investigative:
            return "investigative"
        return "field"

    def _aggregate_billing(self, context: Dict[str, Any], case_mode: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        contract_terms = context.get("contract_terms", {})
        contract_total = float(contract_terms.get("contract_total") or contract_terms.get("contract_value") or 3000.0)
        planning_budget = STANDARD_RATES['planning_budget']
        hourly_rate = STANDARD_RATES['hourly_rate']
        documentation_fee = STANDARD_RATES['documentation_fee']

        planning_manifest = context.get("planning_manifest", {})
        surveillance_manifest = context.get("surveillance_manifest", {})
        toolkit_results = context.get("toolkit_results", {})
        mileage_data = context.get("mileage_data", {})

        sessions = surveillance_manifest.get("sessions") or []
        total_minutes = 0.0
        adjusted_sessions = []
        
        for session in sessions:
            if not isinstance(session, dict):
                continue
            
            # Convert timestamps to 24hr format and apply travel buffer
            start_time = session.get("start_time") or session.get("time_in")
            end_time = session.get("end_time") or session.get("time_out")
            
            if start_time and end_time:
                # Apply +/- 30 minute travel buffer
                adjusted_times = self.timestamp_engine.apply_travel_buffer(
                    start_time, end_time, "surveillance"
                )
                
                if adjusted_times.get("adjustment_applied"):
                    # Use adjusted times for billing calculation
                    adjusted_start = adjusted_times["start_time"]
                    adjusted_end = adjusted_times["end_time"]
                    
                    # Calculate duration using adjusted times
                    start_dt = datetime.strptime(adjusted_start, "%H:%M")
                    end_dt = datetime.strptime(adjusted_end, "%H:%M")
                    
                    # Handle overnight sessions
                    if end_dt < start_dt:
                        end_dt += timedelta(days=1)
                    
                    session_minutes = (end_dt - start_dt).total_seconds() / 60
                    total_minutes += session_minutes
                    
                    # Store adjusted session data
                    adjusted_session = session.copy()
                    adjusted_session.update({
                        "original_start_time": start_time,
                        "original_end_time": end_time,
                        "billed_start_time": adjusted_start,
                        "billed_end_time": adjusted_end,
                        "travel_buffer_applied": True
                    })
                    adjusted_sessions.append(adjusted_session)
                else:
                    # Fallback to original calculation if adjustment fails
                    duration = (
                        session.get("billed_minutes")
                        or session.get("duration_minutes")
                        or session.get("minutes")
                    )
                    if duration is None and session.get("billed_hours") is not None:
                        duration = float(session.get("billed_hours")) * 60
                    if isinstance(duration, (int, float)):
                        total_minutes += float(duration)
                    
                    adjusted_sessions.append(session)
            else:
                # Use existing duration calculation
                duration = (
                    session.get("billed_minutes")
                    or session.get("duration_minutes")
                    or session.get("minutes")
                )
                if duration is None and session.get("billed_hours") is not None:
                    duration = float(session.get("billed_hours")) * 60
                if isinstance(duration, (int, float)):
                    total_minutes += float(duration)
                
                adjusted_sessions.append(session)
        
        field_hours = round(total_minutes / 60.0, 2)

        authorized_hours = float(planning_manifest.get("authorized_hours") or planning_manifest.get("max_field_hours") or 0)
        qa_flags: List[str] = []
        manual_queue: List[str] = []
        if authorized_hours and field_hours > authorized_hours + 0.5:
            qa_flags.append("field_hours_exceed_scope")
            manual_queue.append("Review field hour overage")

        subcontractor_cost = float(toolkit_results.get("subcontractor_cost") or toolkit_results.get("subcontractor_totals") or 0.0)
        prep_cost = float(toolkit_results.get("prep_cost") or planning_manifest.get("planning_cost") or planning_budget)
        documentation_cost = documentation_fee

        mileage_miles = float(mileage_data.get("total_miles") or 0.0)
        mileage_cost_internal = mileage_miles * STANDARD_RATES['mileage_rate']

        surveillance_cost = field_hours * hourly_rate

        billing_sections: List[Dict[str, Any]] = []
        if case_mode == "investigative":
            billing_sections.append({
                "category": "Investigative Services",
                "amount": prep_cost,
                "description": "Investigative preparation and research activities."
            })
            billing_sections.append({
                "category": "Documentation & Compliance",
                "amount": documentation_cost,
                "description": "Compilation of supporting documents and compliance review."
            })
        elif case_mode == "field":
            billing_sections.append({
                "category": "Surveillance Operations",
                "amount": surveillance_cost,
                "description": f"Billed field hours ({field_hours:.2f} @ ${hourly_rate:.2f}/hr)."
            })
            billing_sections.append({
                "category": "Planning Allocation",
                "amount": prep_cost,
                "description": "Surveillance planning allocation per contract."
            })
            billing_sections.append({
                "category": "Documentation Fee",
                "amount": documentation_cost,
                "description": "Report documentation and delivery fee."
            })
        else:  # hybrid
            billing_sections.append({
                "category": "Investigative Services",
                "amount": prep_cost,
                "description": "Investigative phase charges as authorized."
            })
            billing_sections.append({
                "category": "Surveillance Operations",
                "amount": surveillance_cost,
                "description": f"Field operations ({field_hours:.2f} hrs @ ${hourly_rate:.2f}/hr)."
            })
            billing_sections.append({
                "category": "Documentation Fee",
                "amount": documentation_cost,
                "description": "Final documentation and compliance review."
            })

        if subcontractor_cost:
            billing_sections.append({
                "category": "Subcontractor Services",
                "amount": subcontractor_cost,
                "description": "Approved subcontractor billing passed through to client."
            })

        if mileage_cost_internal:
            billing_sections.append({
                "category": "Mileage (Internal)",
                "amount": 0.0,
                "description": "Mileage tracked internally; waived as professional courtesy."
            })

        remaining_ops_budget = contract_total - prep_cost - subcontractor_cost
        total_costs = prep_cost + subcontractor_cost
        internal_margin = remaining_ops_budget - total_costs if remaining_ops_budget > total_costs else 0.0

        # Verify timestamp consistency between sections
        section3_times = context.get("section3_times", [])
        section4_times = context.get("section4_times", [])
        timestamp_verification = self.timestamp_engine.verify_timestamp_consistency(
            section3_times, section4_times
        )
        
        billing_data = {
            "contract_total": contract_total,
            "prep_cost": prep_cost,
            "subcontractor_cost": subcontractor_cost,
            "remaining_ops_budget": remaining_ops_budget,
            "total_costs": total_costs,
            "internal_margin": internal_margin,
            "billing_sections": billing_sections,
            "field_hours": field_hours,
            "authorized_hours": authorized_hours,
            "documentation_fee": documentation_cost,
            "mileage_miles": mileage_miles,
            "mileage_statement": "Mileage was tracked internally and waived as a professional courtesy.",
            "adjusted_sessions": adjusted_sessions,
            "timestamp_verification": timestamp_verification,
            "travel_buffer_applied": any(session.get("travel_buffer_applied") for session in adjusted_sessions),
        }

        meta = {
            "qa_flags": qa_flags,
            "manual_queue": manual_queue,
        }
        return billing_data, meta

    def _compose_notes(self, case_mode: str, context: Dict[str, Any], meta: Dict[str, Any]) -> str:
        notes: List[str] = []
        contract_terms = context.get("contract_terms", {})
        if contract_terms.get("po_number"):
            notes.append(f"PO Reference: {contract_terms['po_number']}")
        if meta.get("manual_queue"):
            notes.append("Manual review required for one or more billing items.")
        manual_annotations = context.get("manual_annotations", [])
        notes.extend(str(entry).strip() for entry in manual_annotations if str(entry).strip())
        if case_mode == "investigative":
            notes.append("Billing reflects investigative services only; no field operations billed.")
        elif case_mode == "field":
            notes.append("Billing reflects field operations verified against surveillance logs.")
        else:
            notes.append("Hybrid billing combines investigative and field operations in accordance with contract scope.")
        if not notes:
            return "Billing generated with no additional remarks."
        return "\n".join(dict.fromkeys(notes))

    def _run_inline_tools(self, context: Dict[str, Any], billing_data: Dict[str, Any]) -> Dict[str, Any]:
        toolkit_results = context.get("toolkit_results", {})
        mileage_audit = MileageToolV2.audit_mileage()
        continuity_notes = toolkit_results.get("continuity") or []
        qa_flags: List[str] = []
        if isinstance(continuity_notes, str):
            continuity_notes = [continuity_notes]
        reverse_tool = ReverseContinuityTool()
        planning_summary = json.dumps(context.get("planning_manifest", {}), default=str)
        surveillance_summary = json.dumps(context.get("surveillance_manifest", {}), default=str)
        text_blob = "\n".join([
            f"Contract Total: {billing_data['contract_total']}",
            f"Field Hours: {billing_data['field_hours']}",
        ])
        reverse_ok, reverse_log = reverse_tool.run_validation(
            text_blob,
            [planning_summary],
            [surveillance_summary],
        )
        if not reverse_ok:
            qa_flags.append("reverse_continuity_manual_review")
        if mileage_audit.get("status") == "COMPLETED":
            for entry in mileage_audit.get("entries", []):
                if entry.get("issues"):
                    qa_flags.append("mileage_issue_detected")
                    break
        metadata_zip = context.get("contract_terms", {}).get("metadata_zip")
        metadata_result = (
            MetadataToolV5.process_zip(metadata_zip, context.get("metadata_output_dir", "./metadata_out"))
            if metadata_zip
            else {"status": "SKIPPED"}
        )
        if metadata_result.get("status") == "ERROR":
            qa_flags.append("metadata_extraction_failure")
        # Add timestamp verification results
        timestamp_verification = billing_data.get("timestamp_verification", {})
        if not timestamp_verification.get("consistent", True):
            qa_flags.append("timestamp_inconsistency_detected")
        
        # Add adjustment log
        adjustment_log = self.timestamp_engine.get_adjustment_log()
        
        return {
            "reverse_continuity": {"ok": bool(reverse_ok), "log": reverse_log},
            "mileage_audit": mileage_audit,
            "metadata_audit": metadata_result,
            "timestamp_verification": timestamp_verification,
            "adjustment_log": adjustment_log,
            "qa_flags": qa_flags,
        }

    def _build_renderer_sources(self, context: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        return {
            "report_type": context.get("case_metadata", {}).get("report_type"),
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


__all__ = [
"Section6Framework",
"StageDefinition",
"CommunicationContract",
"FactGraphContract",
"PersistenceContract",
"OrderContract",
"BodyTextSwitchboard",
"ToolInjectionLogic",
"TimestampAdjustmentEngine",
"get_report_config",
"extract_text_from_pdf",
"extract_text_from_image",
"easyocr_text",
]

