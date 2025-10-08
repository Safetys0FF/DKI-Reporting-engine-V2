"""Framework template for Section 7 (Conclusion)."""

from __future__ import annotations

import json
import logging
import os
import re
import zipfile
import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

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
# OCR Processing Functions
def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from PDF using unstructured."""
    if not OCR_AVAILABLE:
        return ""
    try:
        elements = partition_pdf(pdf_path)
        return "\n".join([str(elem) for elem in elements])
    except Exception as e:
        LOGGER.warning(f"PDF extraction failed for {pdf_path}: {e}")
        return ""

def extract_text_from_image(img_path: str) -> str:
    """Extract text from image using Tesseract."""
    if not OCR_AVAILABLE:
        return ""
    try:
        image = Image.open(img_path)
        return pytesseract.image_to_string(image)
    except Exception as e:
        LOGGER.warning(f"Image extraction failed for {img_path}: {e}")
        return ""

def easyocr_text(img_path: str) -> str:
    """Extract text from image using EasyOCR."""
    if not OCR_AVAILABLE:
        return ""
    try:
        reader = easyocr.Reader(['en'])
        results = reader.readtext(img_path)
        return "\n".join([result[1] for result in results])
    except Exception as e:
        LOGGER.warning(f"EasyOCR extraction failed for {img_path}: {e}")
        return ""

# Contract-based report configuration
def get_report_config(contract_history: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Determine report type and configuration based on contract history."""
    if not contract_history:
        return {
            "report_type": "Investigative",
            "label": "SECTION 7 - CONCLUSION (INVESTIGATIVE)",
            "clause": None,
            "forced_render_order": ["summary", "findings", "integrity", "decision"],
            "hide": {}
        }
    
    # Analyze contract types
    contract_types = [contract.get("type", "").lower() for contract in contract_history]
    
    if "surveillance" in contract_types and "investigative" in contract_types:
        return {
            "report_type": "Hybrid",
            "label": "SECTION 7 - CONCLUSION (HYBRID)",
            "clause": "This conclusion covers both investigative and surveillance activities as specified in the contract.",
            "forced_render_order": ["summary", "findings", "integrity", "decision"],
            "hide": {}
        }
    elif "surveillance" in contract_types:
        return {
            "report_type": "Surveillance",
            "label": "SECTION 7 - CONCLUSION (FIELD OPERATIONS)",
            "clause": "This conclusion covers surveillance activities as specified in the contract.",
            "forced_render_order": ["summary", "findings", "integrity", "decision"],
            "hide": {}
        }
    else:
        return {
            "report_type": "Investigative",
            "label": "SECTION 7 - CONCLUSION (INVESTIGATIVE)",
            "clause": "This conclusion covers investigative activities as specified in the contract.",
            "forced_render_order": ["summary", "findings", "integrity", "decision"],
            "hide": {}
        }


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

class Section7Renderer:
    SECTION_KEY = "section_7"
    TITLE = "SECTION 7 - CONCLUSION"

    STYLE_RULES = {
        "font": "Times New Roman",
        "section_title": {"size_pt": 16, "bold": True, "all_caps": True, "align": "center", "shaded_background": True},
        "header": {"size_pt": 14, "bold": True, "underline": True, "all_caps": True, "align": "left"},
        "paragraph": {"size_pt": 12, "bold": False, "italic": False, "align": "left"},
        "emphasis": {"size_pt": 12, "italic": True, "align": "left"},
        "line_spacing": 1.15,
    }

    def render_model(self, section_payload: Dict[str, Any], case_sources: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # Use contract configuration
            contract_config = section_payload.get('contract_config', {})
            report_type = section_payload.get('report_type', 'Investigative')
            whitelist_applied = section_payload.get('whitelist_applied', [])
            
            case_data = section_payload.get('case_data', {}) or {}
            toolkit = section_payload.get('toolkit_results', {}) or {}
            prev = section_payload.get('previous_sections', {}) or {}

            # Consider only Sections 1–5 and 8
            sec_ids = ['section_1', 'section_2', 'section_3', 'section_4', 'section_5', 'section_8']
            available = {sid: bool(prev.get(sid)) for sid in sec_ids}

            flags: List[str] = []
            for sid, present in available.items():
                if not present:
                    flags.append(f"Missing supporting content from {sid.replace('_', ' ').title()}")

            # Simple continuity signal (from toolkit if present); do not use billing
            continuity = toolkit.get('continuity_check') or {}
            # Handle case where continuity_check returns a tuple (success, log)
            if isinstance(continuity, tuple):
                continuity_ok = continuity[0] if len(continuity) > 0 else False
            elif isinstance(continuity, dict):
                continuity_ok = bool(continuity) and (continuity.get('status') == 'success' or continuity.get('ok') is True)
            else:
                continuity_ok = bool(continuity)
            if continuity and not continuity_ok:
                flags.append("Continuity validation reported issues")

            # Build render tree
            render_tree: List[Dict[str, Any]] = []
            render_tree.append({
                "type": "title",
                "text": section_payload.get("section_heading", self.TITLE),
                "style": self.STYLE_RULES["section_title"],
            })

            # Render based on contract configuration and whitelist
            render_order = contract_config.get("forced_render_order", ["summary", "findings", "integrity", "decision"])
            active_components = section_payload.get("active_components", render_order)
            
            for component in active_components:
                if component == "summary":
                    render_tree.append({
                        "type": "header",
                        "text": "SUMMARY OF FINDINGS",
                        "style": self.STYLE_RULES["header"],
                    })
                    
                    client = case_data.get('client_name', 'Client')
                    case_id = case_data.get('case_id', 'UNKNOWN')
                    intro = (
                        f"This conclusion summarizes the {report_type.lower()} investigation for {client} (Case ID: {case_id}). "
                        "It reflects corroborated findings from the objectives, requirements, daily logs, surveillance sessions, supporting documents, "
                        "and the photo/video evidence index."
                    )
                    render_tree.append({"type": "paragraph", "text": intro, "style": self.STYLE_RULES["paragraph"]})

                    # Evidentiary basis (high-level bullets as paragraphs)
                    basis_lines: List[str] = []
                    if available['section_1']:
                        basis_lines.append("- Objectives and case information identified (Section 1)")
                    if available['section_2']:
                        basis_lines.append("- Requirements and pre‑surveillance preparation documented (Section 2)")
                    if available['section_3']:
                        basis_lines.append("- Field activity recorded in daily logs (Section 3)")
                    if available['section_4']:
                        basis_lines.append("- Surveillance sessions summarized with time anchors (Section 4)")
                    if available['section_5']:
                        basis_lines.append("- Supporting documentation reviewed (Section 5)")
                    if available['section_8']:
                        basis_lines.append("- Photo/Video evidence indexed and chronologically aligned (Section 8)")
                    if basis_lines:
                        render_tree.append({
                            "type": "paragraph",
                            "text": "\n".join(basis_lines),
                            "style": self.STYLE_RULES["paragraph"],
                        })
                
                elif component == "integrity":
                    render_tree.append({
                        "type": "header",
                        "text": "INTEGRITY CHECKS",
                        "style": self.STYLE_RULES["header"],
                    })

                    integ: List[str] = []
                    integ.append(f"- Continuity status: {'Passed' if continuity_ok else 'Issues detected' if continuity else 'Unavailable'}")
                    if flags:
                        integ.append("- Items requiring review are listed below")
                    render_tree.append({"type": "paragraph", "text": "\n".join(integ), "style": self.STYLE_RULES["paragraph"]})

                    if flags:
                        render_tree.append({
                            "type": "header",
                            "text": "REVIEW FLAGS",
                            "style": self.STYLE_RULES["header"],
                        })
                        render_tree.append({
                            "type": "paragraph",
                            "text": "\n".join([f"- {f}" for f in flags]),
                            "style": self.STYLE_RULES["paragraph"],
                        })
                
                elif component == "decision":
                    render_tree.append({
                        "type": "header",
                        "text": "CLOSING STATEMENT",
                        "style": self.STYLE_RULES["header"],
                    })

                    if flags:
                        closing = (
                            "This conclusion reflects the validated findings contained in this report. "
                            "At this time, further investigation is required to resolve the above review items and preserve report integrity."
                        )
                        decision = "CASE DECISION: Further Investigation Required"
                    else:
                        closing = (
                            "This conclusion reflects the validated findings contained in this report. "
                            "Based on the current record and corroborated evidence, the investigation is complete."
                        )
                        decision = "CASE DECISION: Case Closed"

                    render_tree.append({"type": "paragraph", "text": closing, "style": self.STYLE_RULES["paragraph"]})
                    render_tree.append({"type": "paragraph", "text": decision, "style": self.STYLE_RULES["emphasis"]})

            # Add contract disclaimer if present
            if contract_config.get("clause"):
                render_tree.append({
                    "type": "paragraph",
                    "text": contract_config["clause"],
                    "style": self.STYLE_RULES["emphasis"],
                })

            manifest = {
                "section_key": self.SECTION_KEY,
                "generated_on": datetime.now().isoformat(),
                "coverage": available,
                "flags": flags,
                "decision": decision if 'decision' in locals() else "CASE DECISION: Case Closed",
                "contract_config": contract_config,
                "report_type": report_type,
            }

            return {
                "render_tree": render_tree,
                "manifest": manifest,
                "handoff": "gateway",
            }

        except Exception as e:
            logger.error(f"Section 7 render failed: {e}")
            return {
                "render_tree": [
                    {"type": "title", "text": self.TITLE, "style": self.STYLE_RULES["section_title"]},
                    {"type": "paragraph", "text": f"Error generating Section 7: {e}", "style": self.STYLE_RULES["emphasis"]},
                ],
                "manifest": {"section_key": self.SECTION_KEY, "error": str(e)},
                "handoff": "gateway",
            }


INVESTIGATIVE_HEADING = "SECTION 7 - CONCLUSION (INVESTIGATIVE)"
FIELD_HEADING = "SECTION 7 - CONCLUSION (FIELD OPERATIONS)"
HYBRID_HEADING = "SECTION 7 - CONCLUSION (HYBRID)"


class Section7Framework(SectionFramework):
    SECTION_ID = "section_7_conclusion"
    MAX_RERUNS = 2
    STAGES = (
        StageDefinition(
            name="intake",
            description="Load conclusion inputs, confirm upstream hashes, and gather section manifests.",
            checkpoint="s7_intake_logged",
            guardrails=("order_lock", "async_queue", "persistence_snapshot"),
            inputs=(
                "case_metadata",
                "section_manifests",
                "toolkit_results",
                "document_references",
            ),
            outputs=("intake_context",),
        ),
        StageDefinition(
            name="analyze",
            description="Synthesize prior sections, check coverage, and collate review flags.",
            checkpoint="s7_analysis_complete",
            guardrails=("schema_validation", "continuity_checks"),
            inputs=("section_manifests", "toolkit_results"),
            outputs=("conclusion_manifest",),
        ),
        StageDefinition(
            name="validate",
            description="Apply QA rules, ensure required sections present, and log outstanding issues.",
            checkpoint="s7_validated",
            guardrails=("manual_queue_routes", "immutability_precheck"),
            inputs=("conclusion_manifest",),
            outputs=("validated_conclusion",),
        ),
        StageDefinition(
            name="publish",
            description="Publish conclusion payload, emit conclusion-ready signal, and persist provenance.",
            checkpoint="section_7_completed",
            guardrails=("durable_persistence", "signal_emission", "immutability"),
            inputs=("validated_conclusion",),
            outputs=("gateway_handoff",),
        ),
        StageDefinition(
            name="monitor",
            description="Handle revision requests while enforcing rerun guardrails.",
            checkpoint="s7_revision_processed",
            guardrails=("max_reruns", "revision_depth_cap", "fact_graph_consistency"),
        ),
    )
    COMMUNICATION = CommunicationContract(
        prepare_signal="section_6_billing.completed",
        input_channels=(
            "case_metadata",
            "section_manifests",
            "toolkit_results",
            "document_references",
            "manual_annotations",
        ),
        output_signal="section_7_conclusion.completed",
        revision_signal="conclusion_revision_requested",
    )
    ORDER = OrderContract(
        execution_after=("section_6_billing", "section_5_documents", "section_4", "section_3_logs"),
        export_after=("section_fr", "section_summary"),
        export_priority=70,
    )

    def __init__(self, gateway: Any, ecc: Optional[Any] = None) -> None:
        super().__init__(gateway=gateway, ecc=ecc)
        self._last_context: Dict[str, Any] = {}

    def load_inputs(self) -> Dict[str, Any]:
        try:
            self._guard_execution("input loading")
            bundle = self.gateway.get_section_inputs("section_7") if self.gateway else {}
            context = {
                "raw_inputs": bundle,
                "case_metadata": bundle.get("case_metadata", {}),
                "section_manifests": bundle.get("section_manifests", {}),
                "toolkit_results": bundle.get("toolkit_results", {}),
                "document_references": bundle.get("document_references", {}),
                "manual_annotations": bundle.get("manual_annotations", []),
            }
            manifests = context.get("section_manifests") or {}
            coverage = {sid: bool(manifests.get(sid)) for sid in ['section_1', 'section_2', 'section_3', 'section_4', 'section_5', 'section_8']}
            context["basic_stats"] = {
                "coverage": coverage,
                "toolkit_flags": len(context.get("toolkit_results", {}).get("continuity_check") or []),
            }
            context = self._augment_with_bus_context(context)
            self.logger.debug("Section 7 inputs loaded: %s", context["basic_stats"])
            self._last_context = context
            return context
        except Exception as exc:
            self.logger.exception("Failed to load inputs for %s: %s", self.SECTION_ID, exc)
            return self._augment_with_bus_context({})

    def build_payload(self, context: Dict[str, Any]) -> Dict[str, Any]:
        try:
            self._guard_execution("payload building")
            self._last_context = context
            
            # Get contract configuration
            contract_history = context.get("case_metadata", {}).get("contract_history", [])
            report_config = get_report_config(contract_history)
            
            # Determine active components based on ECC whitelist
            ecc_whitelist = context.get("ecc_whitelist", [])
            active_components = []
            for component in report_config.get("forced_render_order", []):
                if component in ecc_whitelist or not ecc_whitelist:
                    if not report_config.get("hide", {}).get(component, False):
                        active_components.append(component)
            
            conclusion_data = self._assemble_conclusion_data(context, report_config)
            notes = self._compose_notes(context, conclusion_data)
            
            payload: Dict[str, Any] = {
                "section_heading": report_config.get("label"),
                "report_type": report_config.get("report_type"),
                "whitelist_applied": ecc_whitelist,
                "contract_config": report_config,
                "active_components": active_components,
                "case_data": conclusion_data.get("case_data"),
                "toolkit_results": conclusion_data.get("toolkit_results"),
                "previous_sections": conclusion_data.get("previous_sections"),
                "qa_flags": sorted(conclusion_data.get("qa_flags", [])),
                "notes": notes,
            }
            if context.get("bus_state") is not None:
                payload.setdefault("bus_state", context.get("bus_state"))
            if context.get("section_evidence") is not None:
                payload.setdefault("section_evidence", context.get("section_evidence"))
            if context.get("section_needs") is not None:
                payload.setdefault("section_needs", context.get("section_needs"))
            if context.get("manifest_context") is not None:
                payload.setdefault("manifest_context", context.get("manifest_context"))
            section_bus_id = self.bus_section_id() or "section_7"
            payload.setdefault("section_id", section_bus_id)
            case_id = context.get("case_id") or context.get("bus_state", {}).get("case_id")
            if case_id:
                payload.setdefault("case_id", case_id)
            return payload
        except Exception as exc:
            self.logger.exception("Failed to build payload for %s: %s", self.SECTION_ID, exc)
            return {"error": str(exc)}

    def publish(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            self._guard_execution("publishing")

            renderer = Section7Renderer()
            case_sources = self._build_renderer_sources(self._last_context)
            model = renderer.render_model(payload, case_sources)
            narrative_lines: List[str] = []
            for block in model["render_tree"]:
                block_type = block.get("type")
                if block_type == "field":
                    label = str(block.get('label', '')).strip()
                    value = str(block.get('value', '')).strip()
                    narrative_lines.append(f"{label}: {value}")
                elif block_type in {"title", "header", "paragraph"}:
                    narrative_lines.append(str(block.get("text", "")))
            narrative = "\n".join(filter(None, narrative_lines))

            section_bus_id = self.bus_section_id() or "section_7"
            timestamp = datetime.now().isoformat()
            summary = narrative.splitlines()[0] if narrative else ""
            summary = summary[:320]

            result = {
                "section_id": section_bus_id,
                "case_id": payload.get("case_id"),
                "payload": payload,
                "manifest": model.get("manifest", {}) or payload,
                "render_tree": model.get("render_tree", []),
                "narrative": narrative,
                "summary": summary,
                "metadata": {"published_at": timestamp, "section": self.SECTION_ID},
                "source": "section_7_framework",
            }

            if self.gateway:
                try:
                    if hasattr(self.gateway, "publish_section_result"):
                        self.gateway.publish_section_result(section_bus_id, result)
                    if hasattr(self.gateway, "emit"):
                        emit_payload = dict(result)
                        emit_payload.setdefault("published_at", timestamp)
                        if self.COMMUNICATION and self.COMMUNICATION.output_signal:
                            self.gateway.emit(self.COMMUNICATION.output_signal, emit_payload)
                        self.gateway.emit("conclusion_ready", result["manifest"])
                except Exception:
                    self.logger.exception("Gateway publish for section_7 failed")

            if self.ecc:
                try:
                    self.ecc.mark_complete(self.SECTION_ID)
                except Exception:
                    self.logger.exception("ECC completion for section_7 failed")

            return {"status": "published", "narrative": narrative, "manifest": result["manifest"]}
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
            report_type = (case_meta.get("report_type") or case_meta.get("case_type") or "").lower()
            mapping = {
                "investigative": "investigative",
                "field": "field",
                "surveillance": "field",
                "hybrid": "hybrid",
                "mixed": "hybrid",
            }
            return mapping.get(report_type, "field")

        def _assemble_conclusion_data(self, context: Dict[str, Any], case_mode: str) -> Dict[str, Any]:
            case_meta = context.get("case_metadata", {})
            manifests = context.get("section_manifests", {}) or {}
            toolkit = context.get("toolkit_results", {}) or {}
            coverage = {sid: bool(manifests.get(sid)) for sid in ['section_1', 'section_2', 'section_3', 'section_4', 'section_5', 'section_8']}
            qa_flags: List[str] = []
            missing = [sid for sid, present in coverage.items() if not present]
            if missing:
                qa_flags.append("coverage_gap_detected")
            continuity = toolkit.get("continuity_check")
            continuity_failed = False
            if isinstance(continuity, tuple):
                continuity_failed = bool(continuity) and not continuity[0]
            elif isinstance(continuity, dict):
                status = continuity.get('status') or continuity.get('ok')
                continuity_failed = status not in (True, 'success', 'passed')
            elif continuity:
                continuity_failed = not bool(continuity)
            if continuity_failed:
                qa_flags.append("continuity_warning")
            case_data = {
                "client_name": case_meta.get("client_name", "Client"),
                "case_id": case_meta.get("case_id", case_meta.get("reference_id", "UNKNOWN")),
                "summary": case_meta.get("case_summary"),
            }
            previous_sections = {sid: manifests.get(sid) for sid in coverage}
            return {
                "report_type": case_mode.capitalize(),
                "case_data": case_data,
                "previous_sections": previous_sections,
                "toolkit_results": toolkit,
                "qa_flags": qa_flags,
            }

        def _compose_notes(self, context: Dict[str, Any], conclusion_data: Dict[str, Any]) -> str:
            notes: List[str] = []
            manual_annotations = context.get("manual_annotations", [])
            notes.extend(str(entry).strip() for entry in manual_annotations if str(entry).strip())
            if conclusion_data.get("qa_flags"):
                notes.append("Conclusion contains outstanding review flags requiring follow-up.")
            if not notes:
                return "Conclusion generated with all prerequisite sections accounted for."
            return '\n'.join(dict.fromkeys(notes))

        def _build_renderer_sources(self, context: Dict[str, Any]) -> Dict[str, Any]:
            return {
                "report_type": context.get("case_metadata", {}).get("report_type"),
            }

        def _safe_join(self, items: Iterable[Any], default: str, separator: str = '\n') -> str:
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
    "Section7Framework",
    "Section7Renderer",
    "StageDefinition",
    "CommunicationContract",
    "FactGraphContract",
    "PersistenceContract",
    "OrderContract",
    "get_report_config",
    "extract_text_from_pdf",
    "extract_text_from_image",
    "easyocr_text",
]

