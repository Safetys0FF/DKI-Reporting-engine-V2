"""Framework template for Section 8 (Photo / Evidence Index)."""

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
            "label": "SECTION 8 - PHOTO / EVIDENCE INDEX (INVESTIGATIVE)",
            "clause": None,
            "forced_render_order": ["media_index", "chronological", "metadata"],
            "hide": {}
        }
    
    # Analyze contract types
    contract_types = [contract.get("type", "").lower() for contract in contract_history]
    
    if "surveillance" in contract_types and "investigative" in contract_types:
        return {
            "report_type": "Hybrid",
            "label": "SECTION 8 - PHOTO / EVIDENCE INDEX (HYBRID)",
            "clause": "This evidence index covers both investigative and surveillance activities as specified in the contract.",
            "forced_render_order": ["media_index", "chronological", "metadata", "continuity"],
            "hide": {}
        }
    elif "surveillance" in contract_types:
        return {
            "report_type": "Surveillance",
            "label": "SECTION 8 - PHOTO / EVIDENCE INDEX (FIELD OPERATIONS)",
            "clause": "This evidence index covers surveillance activities as specified in the contract.",
            "forced_render_order": ["media_index", "chronological", "metadata", "continuity"],
            "hide": {}
        }
    else:
        return {
            "report_type": "Investigative",
            "label": "SECTION 8 - PHOTO / EVIDENCE INDEX (INVESTIGATIVE)",
            "clause": "This evidence index covers investigative activities as specified in the contract.",
            "forced_render_order": ["media_index", "chronological", "metadata"],
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

class Section8Renderer:
    SECTION_KEY = "section_8"
    TITLE = "8. Photo / Evidence Index"

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
            images: Dict[str, Dict[str, Any]] = section_payload.get('images', {}) or {}
            videos: Dict[str, Dict[str, Any]] = section_payload.get('videos', {}) or {}
            previous_sections: Dict[str, Any] = section_payload.get('previous_sections', {}) or {}
            manual_notes: Dict[str, str] = section_payload.get('manual_notes', {}) or {}
            api_keys: Dict[str, str] = section_payload.get('api_keys', {}) or {}
            policies: Dict[str, Any] = section_payload.get('data_policies', {}) or {}
            field_notes: Dict[str, Any] = case_sources.get('notes', {}) if isinstance(case_sources, dict) else {}
            # Prepare geocoder from API keys if available
            self._geocoder_key = None
            self._api_keys = api_keys
            try:
                from geocoding_util import extract_google_maps_key
                self._geocoder_key = extract_google_maps_key(api_keys)
            except Exception:
                self._geocoder_key = None

            # Collect and normalize media items
            items: List[Dict[str, Any]] = []
            items.extend(self._collect_media(images, kind='image'))
            items.extend(self._collect_media(videos, kind='video'))
            audio_clips: Dict[str, Any] = section_payload.get('audio', {}) or {}
            items.extend(self._collect_media(audio_clips, kind='audio'))

            # Filter: low-quality and duplicates
            items = self._filter_low_quality(items)
            items = self._dedupe_items(items)

            # Enforce relevance via continuity (Sec 3 / Sec 4) + metadata alignment
            sec3 = previous_sections.get('section_3', {})
            sec4 = previous_sections.get('section_4', {})
            items = [it for it in items if self._is_relevant(it, sec3, sec4)]

            # Group by date string
            grouped: Dict[str, List[Dict[str, Any]]] = {}
            for it in items:
                dt = it.get('captured_at') or it.get('processing_timestamp')
                date_key = self._date_key(dt)
                grouped.setdefault(date_key, []).append(it)

            # Build render tree
            render_tree: List[Dict[str, Any]] = []
            render_tree.append({
                "type": "title",
                "text": self.TITLE,
                "style": self.STYLE_RULES["section_title"],
            })

            manifest: Dict[str, Any] = {
                "section_key": self.SECTION_KEY,
                "dates": list(grouped.keys()),
                "counts": {},
            }

            # Sort dates chronologically
            for date_key in sorted(grouped.keys(), key=lambda d: self._date_parse(d)):
                day_items = grouped[date_key]
                # Split photos then videos, each sorted chronologically
                photos = sorted([i for i in day_items if i['kind'] == 'image'], key=lambda x: x.get('captured_at') or x.get('processing_timestamp') or '')
                videos_k = sorted([i for i in day_items if i['kind'] == 'video'], key=lambda x: x.get('captured_at') or x.get('processing_timestamp') or '')
                audios = sorted([i for i in day_items if i['kind'] == 'audio'], key=lambda x: x.get('captured_at') or x.get('processing_timestamp') or '')

                manifest["counts"][date_key] = {"photos": len(photos), "videos": len(videos_k), "audio": len(audios)}

                # Date header
                render_tree.append({
                    "type": "header",
                    "text": f"DATE OF SURVEILLANCE: {date_key}",
                    "style": self.STYLE_RULES["header"],
                })

                # Numbering per day
                pnum, vnum = 1, 1

                # Photos first
                for it in photos:
                    caption = f"Photo {pnum}"
                    render_tree.extend(self._image_block(it, caption, manual_notes, field_notes))
                    pnum += 1

                # Videos after (with mid-point thumbnail if available)
                for it in videos_k:
                    caption = f"Video {vnum}"
                    render_tree.extend(self._image_block(it, caption, manual_notes, field_notes, is_video=True))
                    vnum += 1

                # Audio memos
                anum = 1
                for it in audios:
                    caption = f"Audio Memo {anum}"
                    render_tree.extend(self._audio_block(it, caption))
                    anum += 1

            return {
                "render_tree": render_tree,
                "manifest": manifest,
                "handoff": "gateway",
            }

        except Exception as e:
            logger.error(f"Section 8 render failed: {e}")
            return {
                "render_tree": [
                    {"type": "title", "text": self.TITLE, "style": self.STYLE_RULES["section_title"]},
                    {"type": "paragraph", "text": f"Error generating Section 8: {e}", "style": self.STYLE_RULES["emphasis"]},
                ],
                "manifest": {"section_key": self.SECTION_KEY, "error": str(e)},
                "handoff": "gateway",
            }

    # -------------------- Helpers -------------------- #
    def _collect_media(self, media_map: Dict[str, Dict[str, Any]], kind: str) -> List[Dict[str, Any]]:
        items = []
        for mid, data in media_map.items():
            try:
                fi = (data or {}).get('file_info', {})
                dims = data.get('dimensions') or data.get('resolution')
                w, h = (dims if isinstance(dims, (tuple, list)) and len(dims) == 2 else (None, None))
                exif = data.get('exif', {}) if isinstance(data.get('exif'), dict) else {}
                metadata = data.get('metadata', {})
                ts = self._select_timestamp(data, exif, fi)
                item = {
                    'id': mid,
                    'kind': kind,
                    'path': fi.get('path'),
                    'file_hash': data.get('file_hash'),
                    'dimensions': (w, h) if w and h else None,
                    'captured_at': ts,
                    'processing_timestamp': data.get('processing_timestamp'),
                    'exif': exif,
                    'metadata': metadata,
                }

                if kind == 'audio':
                    transcription_payload = data.get('transcription') if isinstance(data.get('transcription'), dict) else {}
                    item['transcript'] = data.get('summary') or data.get('transcript') or transcription_payload.get('summary') or transcription_payload.get('text')
                    item['language'] = data.get('transcript_language') or transcription_payload.get('language')
                    item['duration'] = data.get('duration')
                    item['segments'] = data.get('transcription_segments') or transcription_payload.get('segments')
                    item['metadata'] = metadata or {}
                    generated = data.get('transcription_generated_at') or transcription_payload.get('generated_at')
                    if generated and not item.get('captured_at'):
                        item['captured_at'] = generated
                # Compute video thumbnail lazily in exporters; we keep placeholder
                items.append(item)
            except Exception:
                continue
        return items

    def _filter_low_quality(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        ok = []
        for it in items:
            dims = it.get('dimensions')
            if it['kind'] == 'image' and dims:
                w, h = dims
                if w < MIN_WIDTH or h < MIN_HEIGHT:
                    continue
            ok.append(it)
        return ok

    def _dedupe_items(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        seen_hash = set()
        kept: List[Dict[str, Any]] = []
        for it in sorted(items, key=lambda x: (x.get('captured_at') or x.get('processing_timestamp') or '')):
            fh = it.get('file_hash')
            dims = it.get('dimensions')
            ts = self._to_dt(it.get('captured_at') or it.get('processing_timestamp'))
            if fh and fh in seen_hash:
                continue
            near_dup = False
            for prev in kept:
                if dims and prev.get('dimensions') == dims:
                    pts = self._to_dt(prev.get('captured_at') or prev.get('processing_timestamp'))
                    if ts and pts and abs((ts - pts).total_seconds()) <= 2:
                        near_dup = True
                        break
            if near_dup:
                continue
            if fh:
                seen_hash.add(fh)
            kept.append(it)
        return kept

    def _is_relevant(self, item: Dict[str, Any], sec3: Dict[str, Any], sec4: Dict[str, Any]) -> bool:
        # Heuristic continuity: if capture time falls within any session/log window extracted from text
        # Parse render_tree content text blocks for time anchors
        try:
            ts = self._to_dt(item.get('captured_at') or item.get('processing_timestamp'))
            if not ts:
                return False
            windows = []
            for sec in (sec3, sec4):
                content = ''
                if isinstance(sec, dict):
                    content = (sec.get('content') or '')
                windows.extend(self._extract_time_windows(content))
            for start, end in windows:
                if start <= ts <= end:
                    return True
            return False
        except Exception:
            return False

    def _image_block(self, it: Dict[str, Any], caption: str, manual_notes: Dict[str, str], field_notes: Dict[str, Any], is_video: bool = False) -> List[Dict[str, Any]]:
        blocks: List[Dict[str, Any]] = []
        # Compose per-item text
        ts_str = self._fmt_ts(it.get('captured_at') or it.get('processing_timestamp'))
        # Resolve address lazily; exporter may attempt API geocode; here we provide placeholder text
        address_line = self._resolve_address_text(it, field_notes)
        user_note = manual_notes.get(it.get('id') or '', '')
        if user_note:
            user_note = user_note.strip()[:150]

        # Emit an image block for exporters, plus a text fallback paragraph
        img_path = it.get('path')
        if is_video and img_path:
            thumb = self._ensure_video_thumbnail(img_path)
            if thumb:
                img_path = thumb
        blocks.append({
            "type": "image",
            "path": img_path,
            "is_video": is_video,
            "label": caption,
            "timestamp": ts_str,
            "address": address_line,
            "note": f"* {user_note}" if user_note else None,
        })

        # Fallback text in content rendering
        lines = [f"{caption}"]
        if ts_str:
            lines.append(f"  Time: {ts_str}")
        if address_line:
            lines.append(f"  {address_line}")
        if user_note:
            lines.append(f"  * {user_note}")
        blocks.append({
            "type": "paragraph",
            "text": "\n".join(lines),
            "style": self.STYLE_RULES["paragraph"],
        })
        return blocks

    # -------------------- Utilities -------------------- #    def _audio_block(self, it: Dict[str, Any], caption: str) -> List[Dict[str, Any]]:
        blocks: List[Dict[str, Any]] = []
        transcript = it.get('transcript') or it.get('summary')
        if transcript:
            blocks.append({
                "type": "paragraph",
                "text": f"{caption}: {transcript}",
                "style": self.STYLE_RULES["paragraph"]
            })
        else:
            blocks.append({
                "type": "paragraph",
                "text": f"{caption}: *No transcript available*",
                "style": self.STYLE_RULES["emphasis"]
            })

        meta_parts = []
        if it.get('language'):
            meta_parts.append(f"Language: {it['language']}")
        if it.get('duration'):
            meta_parts.append(f"Duration: {it['duration']}")
        if meta_parts:
            blocks.append({
                "type": "paragraph",
                "text": ' | '.join(meta_parts),
                "style": self.STYLE_RULES["emphasis"]
            })

        return blocks


    def _select_timestamp(self, data: Dict[str, Any], exif: Dict[str, Any], file_info: Dict[str, Any]) -> Optional[str]:
        # EXIF DateTimeOriginal -> OCR overlay timestamp (from OCR text heuristics) -> file modified time
        for key in ("DateTimeOriginal", "DateTime"):
            if key in exif and exif[key]:
                try:
                    # Common EXIF format: 'YYYY:MM:DD HH:MM:SS'
                    t = exif[key].replace(':', '-', 2)
                    dt = datetime.fromisoformat(t)
                    return dt.isoformat()
                except Exception:
                    pass
        # OCR overlay timestamp heuristic (best-effort)
        ocr_text = (data.get('text') or '').strip()
        if ocr_text:
            ts = self._find_timestamp_in_text(ocr_text)
            if ts:
                return ts
        # File modified time from file_info if available
        try:
            p = file_info.get('path')
            if p and os.path.exists(p):
                mtime = datetime.fromtimestamp(os.path.getmtime(p))
                return mtime.isoformat()
        except Exception:
            pass
        # Fallback to processing timestamp
        return data.get('processing_timestamp')

    def _find_timestamp_in_text(self, text: str) -> Optional[str]:
        import re
        patterns = [
            r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})",
            r"(\d{2}/\d{2}/\d{4} \d{1,2}:\d{2}(:\d{2})?)",
        ]
        for pat in patterns:
            m = re.search(pat, text)
            if m:
                s = m.group(1)
                # Normalize to ISO
                try:
                    if '/' in s:
                        # MM/DD/YYYY HH:MM[:SS]
                        parts = s.split(' ')
                        md, y = parts[0], parts[1:]
                        m1, d1, y1 = md.split('/')
                        rest = ' '.join(y)
                        dt = datetime.fromisoformat(f"{y1}-{int(m1):02d}-{int(d1):02d} {rest}")
                    else:
                        dt = datetime.fromisoformat(s)
                    return dt.isoformat()
                except Exception:
                    return s
        return None

    def _date_key(self, ts: Optional[str]) -> str:
        dt = self._to_dt(ts) or datetime.now()
        return dt.strftime(DATE_FMT_HEADING)

    def _fmt_ts(self, ts: Optional[str]) -> Optional[str]:
        if not ts:
            return None
        try:
            dt = self._to_dt(ts)
            return dt.strftime("%Y-%m-%d %H:%M:%S") if dt else None
        except Exception:
            return ts

    def _to_dt(self, ts: Optional[str]) -> Optional[datetime]:
        if not ts:
            return None
        try:
            # Support 'YYYY-MM-DD HH:MM:SS' or ISO
            s = ts.replace('T', ' ')
            return datetime.fromisoformat(s)
        except Exception:
            return None

    def _date_parse(self, date_key: str) -> datetime:
        try:
            return datetime.strptime(date_key, DATE_FMT_HEADING)
        except Exception:
            return datetime.min

    def _extract_time_windows(self, content: str) -> List[Tuple[datetime, datetime]]:
        """Heuristically extract time windows (start/end) from section content text."""
        import re
        windows: List[Tuple[datetime, datetime]] = []
        # Match ranges like 2025-09-13 08:00 - 10:30
        pat = re.compile(r"(\d{4}-\d{2}-\d{2})\s+(\d{1,2}:\d{2})(?:\s*[-to]{1,3}\s*)(\d{1,2}:\d{2})")
        for m in pat.finditer(content or ""):
            day, s1, s2 = m.group(1), m.group(2), m.group(3)
            try:
                start = datetime.fromisoformat(f"{day} {s1}:00")
                end = datetime.fromisoformat(f"{day} {s2}:00")
                if end > start:
                    windows.append((start, end))
            except Exception:
                continue
        return windows

    def _resolve_address_text(self, item: Dict[str, Any], field_notes: Dict[str, Any]) -> Optional[str]:
        # Placeholder: exporters may attempt actual geocoding via profile API keys
        # If API keys provided, attempt reverse geocoding via Google Maps
        try:
            exif = item.get('exif') or {}
            latlon = self._extract_latlon(exif)
            if latlon:
                # Orchestrated lookup: ChatGPT -> Copilot -> Google Maps
                try:
                    from smart_lookup import SmartLookupResolver
                    sl = SmartLookupResolver(api_keys=(self._api_keys if hasattr(self, '_api_keys') else {}),
                                             policies=section_payload.get('data_policies', {}),
                                             cache=section_payload.get('lookup_cache'))
                    addr = sl.reverse_geocode(latlon[0], latlon[1])
                    if addr:
                        return f"Observed near, {addr}"
                except Exception:
                    pass
                # Fallback Google-only if policy keys were collected separately
                if getattr(self, '_geocoder_key', None):
                    try:
                        from geocoding_util import ReverseGeocoder
                        rg = ReverseGeocoder(self._geocoder_key)
                        addr = rg.reverse(latlon[0], latlon[1])
                        if addr:
                            return f"Observed near, {addr}"
                    except Exception:
                        pass
                # No API or failed; generic placeholder
                return "Observed near, [nearest mailing address]"
            # Fallback to field notes
            loc = field_notes.get('location') if isinstance(field_notes, dict) else None
            if loc:
                return f"Observed near, {loc}"
        except Exception:
            pass
        return None

    def _extract_latlon(self, exif: Dict[str, Any]) -> Optional[Tuple[float, float]]:
        try:
            # Handle flattened EXIF fields
            if 'GPSLatitude' in exif and 'GPSLongitude' in exif:
                lat = self._convert_gps(exif.get('GPSLatitude'), exif.get('GPSLatitudeRef', 'N'))
                lon = self._convert_gps(exif.get('GPSLongitude'), exif.get('GPSLongitudeRef', 'E'))
                return (lat, lon)
            # Handle nested GPSInfo dict
            gps = exif.get('GPSInfo')
            if isinstance(gps, dict):
                # Standard GPS tags
                lat = gps.get(2)  # GPSLatitude
                lat_ref = gps.get(1, 'N')
                lon = gps.get(4)  # GPSLongitude
                lon_ref = gps.get(3, 'E')
                if lat and lon:
                    return (self._convert_gps(lat, lat_ref), self._convert_gps(lon, lon_ref))
        except Exception:
            pass
        return None

    def _convert_gps(self, value, ref) -> float:
        # Convert EXIF GPS rationals to decimal degrees
        try:
            def to_float(x):
                try:
                    return float(x[0]) / float(x[1]) if isinstance(x, tuple) else float(x)
                except Exception:
                    return float(x)
            if isinstance(value, (list, tuple)) and len(value) >= 3:
                d = to_float(value[0])
                m = to_float(value[1])
                s = to_float(value[2])
                dec = d + m/60.0 + s/3600.0
            else:
                dec = float(value)
            if isinstance(ref, bytes):
                ref = ref.decode(errors='ignore')
            ref = str(ref)
            if ref in ('S', 'W'):
                dec = -dec
            return dec
        except Exception:
            return 0.0

    def _ensure_video_thumbnail(self, video_path: str) -> Optional[str]:
        """Create a mid-point thumbnail for a video if possible. Returns path or None."""
        try:
            import cv2
            import tempfile
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS) or 0
            total = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0
            if total <= 0 or fps <= 0:
                cap.release()
                return None
            mid_frame = int(total // 2)
            cap.set(cv2.CAP_PROP_POS_FRAMES, mid_frame)
            ok, frame = cap.read()
            cap.release()
            if not ok:
                return None
            # Write thumbnail to temp file
            thumb_dir = os.path.join(tempfile.gettempdir(), 'dki_thumbs')
            os.makedirs(thumb_dir, exist_ok=True)
            base = os.path.splitext(os.path.basename(video_path))[0]
            out_path = os.path.join(thumb_dir, f"{base}_mid.jpg")
            cv2.imwrite(out_path, frame)
            return out_path if os.path.exists(out_path) else None
        except Exception:
            return None


INVESTIGATIVE_HEADING = "SECTION 8 - PHOTO / EVIDENCE INDEX (INVESTIGATIVE)"
FIELD_HEADING = "SECTION 8 - PHOTO / EVIDENCE INDEX (FIELD OPERATIONS)"
HYBRID_HEADING = "SECTION 8 - PHOTO / EVIDENCE INDEX (HYBRID)"


class Section8Framework(SectionFramework):
    SECTION_ID = "section_8_evidence"
    BUS_SECTION_ID = "section_8"
    MAX_RERUNS = 2
    STAGES = (
        StageDefinition(
            name="intake",
            description="Load media archive, confirm upstream hashes, and gather manifest references.",
            checkpoint="s8_intake_logged",
            guardrails=("order_lock", "async_queue", "persistence_snapshot"),
            inputs=(
                "case_metadata",
                "media_index",
                "section_manifests",
                "toolkit_results",
            ),
            outputs=("intake_context",),
        ),
        StageDefinition(
            name="filter",
            description="Validate media quality, deduplicate, and align with surveillance timeline.",
            checkpoint="s8_media_filtered",
            guardrails=("quality_threshold", "continuity_checks", "metadata_capture"),
            inputs=("media_index", "section_manifests"),
            outputs=("filtered_media",),
        ),
        StageDefinition(
            name="validate",
            description="Apply chain-of-custody rules and assemble evidence manifest.",
            checkpoint="s8_validated",
            guardrails=("manual_queue_routes", "immutability_precheck"),
            inputs=("filtered_media", "toolkit_results"),
            outputs=("validated_media",),
        ),
        StageDefinition(
            name="publish",
            description="Publish evidence index, emit media-ready signal, and persist provenance.",
            checkpoint="section_8_completed",
            guardrails=("durable_persistence", "signal_emission", "immutability"),
            inputs=("validated_media",),
            outputs=("gateway_handoff",),
        ),
        StageDefinition(
            name="monitor",
            description="Handle media revisions while enforcing rerun guardrails.",
            checkpoint="s8_revision_processed",
            guardrails=("max_reruns", "revision_depth_cap", "fact_graph_consistency"),
        ),
    )
    COMMUNICATION = CommunicationContract(
        prepare_signal="section_4_review.completed",
        input_channels=(
            "case_metadata",
            "media_index",
            "section_manifests",
            "toolkit_results",
            "manual_annotations",
            "api_keys",
        ),
        output_signal="section_8_evidence.completed",
        revision_signal="evidence_revision_requested",
    )
    ORDER = OrderContract(
        execution_after=("section_4", "section_3_logs", "section_5_documents"),
        export_after=("section_9", "section_fr"),
        export_priority=80,
    )

    def __init__(self, gateway: Any, ecc: Optional[Any] = None) -> None:
        super().__init__(gateway=gateway, ecc=ecc)
        self._last_context: Dict[str, Any] = {}

    def load_inputs(self) -> Dict[str, Any]:
        try:
            self._guard_execution("input loading")
            bundle = self.gateway.get_section_inputs("section_8") if self.gateway else {}
            context = {
                "raw_inputs": bundle,
                "case_metadata": bundle.get("case_metadata", {}),
                "media_index": bundle.get("media_index", {}),
                "section_manifests": bundle.get("section_manifests", {}),
                "toolkit_results": bundle.get("toolkit_results", {}),
                "manual_annotations": bundle.get("manual_annotations", []),
                "api_keys": bundle.get("api_keys", {}),
            }
            media_index = context.get("media_index") or {}
            image_count = len(media_index.get("images") or {})
            video_count = len(media_index.get("videos") or {})
            audio_count = len(media_index.get("audio") or {})
            context["basic_stats"] = {
                "images": image_count,
                "videos": video_count,
                "audio": audio_count,
            }
            context = self._augment_with_bus_context(context)
            self.logger.debug("Section 8 inputs loaded: %s", context["basic_stats"])
            self._last_context = context
            return context
        except Exception as exc:
            self.logger.exception("Failed to load inputs for %s: %s", self.SECTION_ID, exc)
            return {}

    def build_payload(self, context: Dict[str, Any]) -> Dict[str, Any]:
        try:
            self._guard_execution("payload building")
            self._last_context = context
            
            # Get contract-based configuration
            contract_history = context.get("case_metadata", {}).get("contract_history", [])
            report_config = get_report_config(contract_history)
            
            # Determine active components based on ECC whitelist
            ecc_whitelist = context.get("ecc_whitelist", [])
            active_components = []
            for component in report_config.get("forced_render_order", []):
                if component in ecc_whitelist or not ecc_whitelist:
                    if not report_config.get("hide", {}).get(component, False):
                        active_components.append(component)
            
            case_mode = self._determine_case_mode(context)
            media_payload, meta = self._build_media_payload(context)
            notes = self._compose_notes(context, meta)
            
            payload: Dict[str, Any] = {
                "section_heading": report_config.get("label", "SECTION 8 - PHOTO / EVIDENCE INDEX"),
                "report_type": report_config.get("report_type", "Investigative"),
                "whitelist_applied": ecc_whitelist,
                "contract_config": report_config,
                "active_components": active_components,
                **media_payload,
                "qa_flags": sorted(meta.get("qa_flags", [])),
                "notes": notes,
                "data_policies": context.get("toolkit_results", {}).get("data_policies"),
                "manual_notes": meta.get("manual_notes", {}),
                "api_keys": context.get("api_keys", {}),
            }
            if context.get("bus_state") is not None:
                payload.setdefault("bus_state", context.get("bus_state"))
            if context.get("section_evidence") is not None:
                payload.setdefault("section_evidence", context.get("section_evidence"))
            if context.get("section_needs") is not None:
                payload.setdefault("section_needs", context.get("section_needs"))
            if context.get("manifest_context") is not None:
                payload.setdefault("manifest_context", context.get("manifest_context"))
            section_bus_id = self.bus_section_id() or "section_8"
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

            renderer = Section8Renderer()
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

            section_bus_id = self.bus_section_id() or "section_8"
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
                "source": "section_8_framework",
            }

            try:
                if hasattr(self.gateway, "publish_section_result"):
                    self.gateway.publish_section_result(section_bus_id, result)
                if hasattr(self.gateway, "emit"):
                    emit_payload = dict(result)
                    emit_payload.setdefault("published_at", timestamp)
                    if self.COMMUNICATION and self.COMMUNICATION.output_signal:
                        self.gateway.emit(self.COMMUNICATION.output_signal, emit_payload)
                    self.gateway.emit("section_8_ready", result["manifest"])
            except Exception:
                self.logger.exception("Gateway publish for section_8 failed")

            if self.ecc:
                try:
                    self.ecc.mark_complete(self.SECTION_ID)
                except Exception:
                    self.logger.exception("ECC completion for section_8 failed")

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
            "investigation": "investigative",
            "field": "field",
            "surveillance": "field",
            "hybrid": "hybrid",
            "mixed": "hybrid",
        }
        return mapping.get(report_type, "field")

    def _build_media_payload(self, context: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        media_index = context.get("media_index") or {}
        manifests = context.get("section_manifests") or {}
        toolkit = context.get("toolkit_results") or {}
        manual_annotations = context.get("manual_annotations", [])
        images = media_index.get("images") or {}
        videos = media_index.get("videos") or {}
        audio = media_index.get("audio") or {}
        normalized_images = {mid: self._normalize_media_record(mid, record, 'image') for mid, record in images.items()}
        normalized_videos = {mid: self._normalize_media_record(mid, record, 'video') for mid, record in videos.items()}
        normalized_audio = {mid: self._normalize_media_record(mid, record, 'audio') for mid, record in audio.items()}
        qa_flags: List[str] = []
        manual_notes = {f"note_{i}": ann for i, ann in enumerate(manual_annotations, start=1)}
        if not normalized_images and not normalized_videos:
            qa_flags.append("no_media_available")
        previous_sections = {
            'section_3': manifests.get('section_3'),
            'section_4': manifests.get('section_4'),
        }
        media_payload = {
            "images": normalized_images,
            "videos": normalized_videos,
            "audio": normalized_audio,
            "previous_sections": previous_sections,
            "toolkit_results": toolkit,
            "manual_notes": manual_notes,
        }
        meta = {
            "qa_flags": qa_flags,
            "manual_notes": manual_notes,
        }
        return media_payload, meta

    def _normalize_media_record(self, media_id: str, record: Dict[str, Any], kind: str) -> Dict[str, Any]:
        normalized: Dict[str, Any] = dict(record or {})
        normalized['kind'] = kind
        normalized.setdefault('media_id', media_id)
        captured_at = normalized.get('captured_at') or normalized.get('timestamp')
        if captured_at:
            try:
                normalized['captured_at'] = datetime.fromisoformat(str(captured_at)).isoformat()
            except Exception:
                normalized['captured_at'] = str(captured_at)
        processing_ts = normalized.get('processing_timestamp')
        if processing_ts:
            try:
                normalized['processing_timestamp'] = datetime.fromisoformat(str(processing_ts)).isoformat()
            except Exception:
                normalized['processing_timestamp'] = str(processing_ts)
        label = normalized.get('label') or normalized.get('description') or normalized.get('title')
        if label:
            normalized['label'] = str(label)
        location = normalized.get('location') or normalized.get('geo_hint')
        if location:
            normalized['location'] = str(location)
        return normalized

    def _compose_notes(self, context: Dict[str, Any], meta: Dict[str, Any]) -> str:
        notes: List[str] = []
        if meta.get("qa_flags"):
            notes.append("Evidence index contains outstanding QA flags requiring review.")
        manual_annotations = context.get("manual_annotations", [])
        notes.extend(str(entry).strip() for entry in manual_annotations if str(entry).strip())
        if not notes:
            return "Evidence index prepared with available media assets and continuity alignment."
        return "\n".join(dict.fromkeys(notes))

    def _build_renderer_sources(self, context: Dict[str, Any]) -> Dict[str, Any]:
        manifests = context.get("section_manifests", {}) or {}
        return {
            "notes": {
                "location": manifests.get("section_3", {}).get("primary_location"),
            }
        }

    def _safe_join(self, items: Iterable[Any], default: str, separator: str = '\n') -> str:
        values = [str(item).strip() for item in items if str(item).strip()]
        if not values:
            return default
        return separator.join(values)

    def _run_inline_tools(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Run embedded tools for Section 8."""
        toolkit_results = {}
        
        # Northstar Protocol Tool
        try:
            assets = context.get("case_metadata", {}).get("assets", [])
            northstar_result = NorthstarProtocolTool.process_assets(assets)
            toolkit_results["northstar_classification"] = northstar_result
        except Exception as e:
            self.logger.warning(f"Northstar tool failed: {e}")
            toolkit_results["northstar_classification"] = {"error": str(e)}
        
        # Cochran Match Tool
        try:
            subjects = context.get("case_metadata", {}).get("subjects", [])
            candidates = context.get("case_metadata", {}).get("candidates", [])
            cochran_results = []
            for subject in subjects:
                for candidate in candidates:
                    result = CochranMatchTool.verify_identity(subject, candidate)
                    cochran_results.append(result)
            toolkit_results["cochran_verification"] = cochran_results
        except Exception as e:
            self.logger.warning(f"Cochran tool failed: {e}")
            toolkit_results["cochran_verification"] = {"error": str(e)}
        
        # Reverse Continuity Tool
        try:
            narratives = context.get("surveillance_narratives", [])
            documents = context.get("document_references", [])
            assets = context.get("case_metadata", {}).get("assets", [])
            
            continuity_tool = ReverseContinuityTool()
            continuity_results = []
            for narrative in narratives:
                success, log = continuity_tool.run_validation(narrative, documents, assets)
                continuity_results.append({"success": success, "log": log})
            
            toolkit_results["continuity_check"] = continuity_results
        except Exception as e:
            self.logger.warning(f"Continuity tool failed: {e}")
            toolkit_results["continuity_check"] = {"error": str(e)}
        
        # Metadata Tool
        try:
            metadata_zip = context.get("case_metadata", {}).get("metadata_zip")
            if metadata_zip:
                metadata_result = MetadataToolV5.process_zip(metadata_zip, "./temp/metadata")
                toolkit_results["metadata_processing"] = metadata_result
            else:
                toolkit_results["metadata_processing"] = {"status": "SKIPPED", "reason": "No metadata zip provided"}
        except Exception as e:
            self.logger.warning(f"Metadata tool failed: {e}")
            toolkit_results["metadata_processing"] = {"error": str(e)}
        
        # Mileage Tool
        try:
            mileage_result = MileageToolV2.audit_mileage()
            toolkit_results["mileage_audit"] = mileage_result
        except Exception as e:
            self.logger.warning(f"Mileage tool failed: {e}")
            toolkit_results["mileage_audit"] = {"error": str(e)}
        
        # OCR Processing (if available)
        if OCR_AVAILABLE:
            try:
                ocr_results = self._process_ocr_documents(context)
                toolkit_results["ocr_results"] = ocr_results
            except Exception as e:
                self.logger.warning(f"OCR processing failed: {e}")
                toolkit_results["ocr_processing_issues"] = str(e)
        
        return toolkit_results
    
    def _process_ocr_documents(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process documents using OCR for Section 8."""
        ocr_results = {}
        
        # Get media from case bundle
        media_index = context.get("media_index", {})
        images = media_index.get("images", {})
        videos = media_index.get("videos", {})
        
        # Process images
        for img_id, img_data in images.items():
            try:
                img_path = img_data.get("file_info", {}).get("path")
                if img_path and os.path.exists(img_path):
                    text = extract_text_from_image(img_path)
                    if text:
                        ocr_results[img_id] = {
                            "type": "image",
                            "text": text[:1000] + "..." if len(text) > 1000 else text,
                            "status": "success"
                        }
            except Exception as e:
                ocr_results[img_id] = {
                    "type": "image",
                    "error": str(e),
                    "status": "failed"
                }
        
        return ocr_results


__all__ = [
"Section8Framework",
"Section8Renderer",
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

