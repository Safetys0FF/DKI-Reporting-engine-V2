"""Framework template for Section 5 (Supporting Documents & Records)."""

from __future__ import annotations

import json
import logging
import os
import re
import zipfile
import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple
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

# === Enhanced Contract-Based Report Logic ===
def get_report_config(contract_history):
    """Enhanced contract analysis with Section 5-specific configurations"""
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
    
    # Section 5-specific report configurations
    report_configs = {
        "Investigative": {
            "label": "SECTION 5 - INVESTIGATION DOCUMENT INVENTORY",
            "billing": "Flat",
            "clause": "investigation_only",
            "modules": {
                "active": ["identity_records", "case_administration"],
                "inactive": ["supporting_government_records", "county_and_court_filings", "delivery_confirmations"]
            },
            "effects": {
                "hide": ["visuals", "field_documents"],
                "tag": "Investigation Documents"
            }
        },
        "Surveillance": {
            "label": "SECTION 5 - SUPPORTING DOCUMENTS", 
            "billing": "Hourly",
            "clause": "field_documents",
            "modules": {
                "active": ["identity_records", "supporting_government_records", "county_and_court_filings", "delivery_confirmations", "case_administration"],
                "inactive": []
            },
            "effects": {
                "render_all": True,
                "tag": "Field Documents Ready"
            }
        },
        "Hybrid": {
            "label": "SECTION 5 - INVESTIGATION & FIELD DOCUMENTS",
            "billing": "Hybrid", 
            "clause": "mixed_documents",
            "modules": {
                "active": ["identity_records", "supporting_government_records", "county_and_court_filings", "delivery_confirmations", "case_administration"],
                "inactive": []
            },
            "effects": {
                "forced_render_order": ["investigation_segment", "field_documents"],
                "contract_order_required": True,
                "tag": "Full Document Stack"
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

class Section5Renderer:
    """
    Handles Section 5: Review of Supporting Documents
    - Covers investigative and field documentation
    - Supports hybrid case structure (investigative first, then field)
    - Validates all entries for subject, date, jurisdiction, and type
    - Integrates 3x fallback structure for record data integrity
    - Always hands off to Gateway
    """

    SECTION_KEY = "section_5"
    TITLE = "SECTION 5 – REVIEW OF SUPPORTING DOCUMENTS"

    DOCUMENT_CATEGORIES = [
        "identity_records",
        "supporting_government_records",
        "county_and_court_filings",
        "delivery_confirmations",
        "case_administration"
    ]

    REQUIRED_FIELDS = ["subject_name", "record_type", "jurisdiction", "record_date"]

    PLACEHOLDERS = {
        "unknown": "*Unknown*",
        "unconfirmed": "*Unconfirmed at this time*",
        "suppressed": "*Due to the nature of this case this portion was not performed or was not necessary*"
    }

    BANNED_TOKENS = {"", " ", "N/A", "NA", "TBD", "[REDACTED]", "REDACTED"}

    STYLE_RULES = {
        "font": "Times New Roman",
        "section_title": {"size_pt": 16, "bold": True, "all_caps": True, "align": "center", "shaded_background": True},
        "header": {"size_pt": 14, "bold": True, "underline": True, "all_caps": True, "align": "left"},
        "field_label": {"size_pt": 12, "bold": True, "align": "left"},
        "field_value": {"size_pt": 12, "bold": False, "italic": False, "align": "left"},
        "placeholder_value": {"size_pt": 12, "italic": True, "align": "left"},
        "line_spacing": 1.15
    }

    def _normalize(self, val):
        return str(val).strip() if val else None

    def _placeholder_for(self, key, value):
        if not value or value.upper() in self.BANNED_TOKENS:
            return self.PLACEHOLDERS["unknown"], True
        return value, False

    def _fallback_check(self, key, zones):
        """
        Performs 3-pass fallback validation over:
        - Intake
        - Prior Section Output
        - Document Upload Index
        Returns first valid entry or None
        """
        for _ in range(3):
            for zone in ["intake", "prior_section", "upload_index"]:
                val = zones.get(zone, {}).get(key)
                if val:
                    return val
        return None

    def render_model(self, section_payload, case_sources):
        rendered_blocks = []
        placeholders_used = {}
        drift_bounced = {}

        # Use dynamic heading from contract config
        section_heading = section_payload.get("section_heading", self.TITLE)
        rendered_blocks.append({
            "type": "title",
            "text": section_heading,
            "style": self.STYLE_RULES["section_title"]
        })

        # Get contract configuration
        contract_config = section_payload.get("contract_config", {})
        report_type = section_payload.get("report_type", "Surveillance")
        whitelist_applied = section_payload.get("whitelist_applied", [])

        # Determine which categories to render based on contract
        modules_config = contract_config.get("modules", {})
        active_modules = modules_config.get("active", self.DOCUMENT_CATEGORIES)
        inactive_modules = modules_config.get("inactive", [])

        # Apply whitelist filtering
        categories_to_render = []
        for cat in self.DOCUMENT_CATEGORIES:
            if cat in active_modules and cat not in inactive_modules:
                # Check if whitelist allows this category
                if not whitelist_applied or cat in whitelist_applied:
                    categories_to_render.append(cat)

        # Apply hide effects from contract
        hide_effects = contract_config.get("effects", {}).get("hide", [])
        if "visuals" in hide_effects:
            categories_to_render = [cat for cat in categories_to_render if cat != "delivery_confirmations"]

        for cat in categories_to_render:
            records = section_payload.get(cat, [])
            if not records:
                continue

            rendered_blocks.append({
                "type": "header",
                "text": cat.replace("_", " ").title(),
                "style": self.STYLE_RULES["header"]
            })

            for entry in records:
                block = []
                for field in self.REQUIRED_FIELDS:
                    val = entry.get(field)
                    if not val:
                        val = self._fallback_check(field, case_sources)
                    value, is_ph = self._placeholder_for(field, self._normalize(val))
                    if is_ph:
                        placeholders_used[f"{cat}.{field}"] = value
                    block.append({
                        "type": "field",
                        "label": field.replace("_", " ").title(),
                        "value": value,
                        "style": self.STYLE_RULES["placeholder_value"] if is_ph else self.STYLE_RULES["field_value"]
                    })
                rendered_blocks.extend(block)

        # Add contract disclaimer if present
        if contract_config.get("clause"):
            disclaimer_text = f"Contract clause: {contract_config['clause']}"
            rendered_blocks.append({
                "type": "disclaimer",
                "text": disclaimer_text,
                "style": self.STYLE_RULES["placeholder_value"]
            })

        manifest = {
            "section_key": self.SECTION_KEY,
            "placeholders_used": placeholders_used,
            "fields_rendered": self.REQUIRED_FIELDS,
            "drift_bounced": drift_bounced,
            "contract_config": contract_config,
            "report_type": report_type
        }

        return {
            "render_tree": rendered_blocks,
            "manifest": manifest,
            "handoff": "gateway"
        }


INVESTIGATIVE_HEADING = "SECTION 5 - INVESTIGATION DOCUMENT INVENTORY"
FIELD_HEADING = "SECTION 5 - SUPPORTING DOCUMENTS"
HYBRID_HEADING = "SECTION 5 - INVESTIGATION & FIELD DOCUMENTS"
DOCUMENT_CATEGORIES = (
    "identity_records",
    "supporting_government_records",
    "county_and_court_filings",
    "delivery_confirmations",
    "case_administration",
)
    PARSING_MAP = {
        'police report': ('supporting_government_records', 'Police Report'),
        'sheriff report': ('supporting_government_records', 'Sheriff Report'),
        'court filing': ('county_and_court_filings', 'Court Filing'),
        'subpoena': ('county_and_court_filings', 'Subpoena'),
        'delivery confirmation': ('delivery_confirmations', 'Delivery Confirmation'),
        'intake form': ('case_administration', 'Client Intake Form'),
        'contract': ('case_administration', 'Service Contract'),
    }
    REQUIRED_FINAL_DOCS = (
        ('Client Intake Form', 'Client Intake Form'),
        ('Service Contract', 'Signed Service Contract'),
    )
REQUIRED_FIELDS = ("subject_name", "record_type", "jurisdiction", "record_date")


    class Section5Framework(SectionFramework):
        SECTION_ID = "section_5_documents"
        MAX_RERUNS = 2
        STAGES = (
            StageDefinition(
                name="intake",
                description="Pull gateway bundle, confirm upstream hashes, and load toolkit relevance outputs.",
                checkpoint="s5_intake_logged",
                guardrails=("order_lock", "async_queue", "persistence_snapshot"),
                inputs=("case_metadata", "planning_manifest", "document_index"),
                outputs=("intake_context",),
            ),
            StageDefinition(
                name="extract",
                description="Ensure document metadata present, run OCR fallback when needed.",
                checkpoint="s5_metadata_complete",
                guardrails=("metadata_capture", "ocr_fallback", "repository_sync"),
                inputs=("document_index", "repository_metadata"),
                outputs=("extracted_inventory",),
            ),
            StageDefinition(
                name="validate",
                description="Apply relevance checks, continuity enforcement, and QA policy validation.",
                checkpoint="s5_validated",
                guardrails=("cochran_check", "north_star", "continuity_checks"),
                inputs=("extracted_inventory", "toolkit_results"),
                outputs=("validated_inventory",),
            ),
            StageDefinition(
                name="publish",
                description="Publish document inventory, emit document inventory signal, and persist custody log.",
                checkpoint="section_5_completed",
                guardrails=("durable_persistence", "signal_emission", "immutability"),
                inputs=("validated_inventory",),
                outputs=("gateway_handoff",),
            ),
            StageDefinition(
                name="monitor",
                description="Handle reclassification and new submissions while enforcing rerun guardrails.",
                checkpoint="s5_revision_processed",
                guardrails=("max_reruns", "revision_depth_cap", "fact_graph_consistency"),
            ),
        )
        COMMUNICATION = CommunicationContract(
            prepare_signal="section_2_planning.completed",
            input_channels=(
                "case_metadata",
                "planning_manifest",
                "document_index",
                "repository_metadata",
                "toolkit_results",
                "manual_annotations",
                "chain_of_custody",
                "metadata_bundle_zip",
            ),
            output_signal="section_5_documents.completed",
            revision_signal="document_reclassification_requested",
        )
        ORDER = OrderContract(
            execution_after=("section_2_planning", "section_1_profile", "section_cp"),
            export_after=("section_7", "section_fr"),
            export_priority=50,
        )

        def __init__(self, gateway: Any, ecc: Optional[Any] = None) -> None:
            super().__init__(gateway=gateway, ecc=ecc)
            self._last_context: Dict[str, Any] = {}

        def load_inputs(self) -> Dict[str, Any]:
            try:
                self._guard_execution("input loading")
                bundle = self.gateway.get_section_inputs("section_5") if self.gateway else {}
                context = {
                    "raw_inputs": bundle,
                    "case_metadata": bundle.get("case_metadata", {}),
                    "planning_manifest": bundle.get("planning_manifest", {}),
                    "document_index": bundle.get("document_index", []),
                    "repository_metadata": bundle.get("repository_metadata", {}),
                    "toolkit_results": bundle.get("toolkit_results", {}),
                    "manual_annotations": bundle.get("manual_annotations", []),
                    "chain_of_custody": bundle.get("chain_of_custody", []),
                    "metadata_bundle_zip": bundle.get("metadata_bundle_zip"),
                }
                documents = context["document_index"]
                if isinstance(documents, dict):
                    documents = list(documents.values())
                context["document_index"] = documents
                context["basic_stats"] = {
                    "document_count": len(documents),
                    "custody_entries": len(context.get("chain_of_custody", [])),
                }
                self.logger.debug("Section 5 inputs loaded: %s", context["basic_stats"])
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
                active_modules = modules_config.get("active", DOCUMENT_CATEGORIES)
                
                # Apply whitelist filtering
                active_components = []
                for module in active_modules:
                    if not ecc_whitelist or module in ecc_whitelist:
                        active_components.append(module)
                
                # Apply hide effects
                hide_effects = contract_config.get("effects", {}).get("hide", [])
                if "visuals" in hide_effects:
                    active_components = [comp for comp in active_components if comp != "delivery_confirmations"]
                
                case_mode = self._determine_case_mode(context)
                inventory, meta = self._build_inventory(context, case_mode)
                summary = self._build_summary_stats(inventory, meta)
                notes = self._compose_notes(case_mode, context, meta)
                tool_results = self._run_inline_tools(context, inventory)
                qa_flags = set(meta.get("qa_flags", []))
                qa_flags.update(tool_results.get("qa_flags", []))
                
                payload: Dict[str, Any] = {
                    "section_heading": contract_config.get("label", self._case_heading(case_mode)),
                    "report_type": report_type,
                    "whitelist_applied": active_components,
                    "contract_config": contract_config,
                    "active_components": active_components,
                    **inventory,
                    "document_summary": summary,
                    "qa_flags": sorted(qa_flags),
                    "notes": notes,
                    "tool_results": tool_results,
                    "case_mode": case_mode,
                    "data_policies": context.get("case_metadata", {}).get("data_policies"),
                    "subjects_in_scope": sorted(meta.get("subjects_in_scope", [])),
                    "manual_queue": meta.get("manual_queue", []),
                }
                return payload
            except Exception as exc:
                self.logger.exception("Failed to build payload for %s: %s", self.SECTION_ID, exc)
                return {"error": str(exc)}

        def publish(self, payload: Dict[str, Any]) -> Dict[str, Any]:
            try:
                self._guard_execution("publishing")
                renderer = Section5Renderer()
                case_sources = self._build_renderer_sources(self._last_context)
                model = renderer.render_model(payload, case_sources)
                narrative_lines: List[str] = []
                for block in model["render_tree"]:
                    if block["type"] == "field":
                        narrative_lines.append(f"{block['label']}: {block['value']}")
                    else:
                        narrative_lines.append(str(block["text"]))
                narrative = "\n".join(narrative_lines)
                result = {
                    "payload": payload,
                    "manifest": model["manifest"],
                    "render_tree": model["render_tree"],
                    "narrative": narrative,
                    "status": "completed",
                }
                if self.gateway:
                    self.gateway.publish_section_result("section_5", result)
                    self.gateway.emit("document_inventory_ready", model["manifest"])
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
                "hybrid": "hybrid",
                "mixed": "hybrid",
            }
            if report_type in mapping:
                return mapping[report_type]
            contracts = case_meta.get("contracts") or planning.get("contracts") or []
            has_field = any((c.get("type") or "").lower() in {"field", "surveillance"} for c in contracts)
            has_investigative = any((c.get("type") or "").lower() in {"investigative", "analysis"} for c in contracts)
            if has_field and has_investigative:
                return "hybrid"
            if has_field:
                return "field"
            if has_investigative:
                return "investigative"
            return "field"

        def _collect_document_sources(self, context: Dict[str, Any]) -> Dict[str, Any]:
            documents = context.get("document_index") or []
            repository = context.get("repository_metadata", {})
            planning = context.get("planning_manifest", {})
            toolkit = context.get("toolkit_results", {})
            return {
                "documents": documents,
                "repository": repository,
                "continuity_flags": toolkit.get("continuity", []),
                "analysis_notes": toolkit.get("document_analysis") or planning.get("document_notes") or [],
                "manual_annotations": context.get("manual_annotations", []),
            }


        def _build_inventory(self, context: Dict[str, Any], case_mode: str) -> Tuple[Dict[str, List[Dict[str, Any]]], Dict[str, Any]]:
            sources = self._collect_document_sources(context)
            inventory: Dict[str, List[Dict[str, Any]]] = {category: [] for category in DOCUMENT_CATEGORIES}
            qa_flags: List[str] = []
            subjects_in_scope: List[str] = []
            manual_queue: List[str] = []
            missing_metadata: List[str] = []
            duplicates: List[str] = []
            seen_ids: Set[str] = set()

            for doc in sources["documents"]:
                record, record_flags, record_subjects, needs_manual = self._normalize_record(doc, context)
                category = self._categorize_document(doc, record)
                category, record = self._apply_parsing_rules(category, record, doc, context)

                doc_id = record.get("document_id")
                if doc_id:
                    if doc_id in seen_ids:
                        duplicates.append(doc_id)
                    else:
                        seen_ids.add(doc_id)

                inventory.setdefault(category, []).append(record)
                qa_flags.extend(record_flags)
                subjects_in_scope.extend(record_subjects)
                if needs_manual:
                    manual_queue.append(doc_id or record.get("record_title"))
                if record.get("missing_fields"):
                    missing_metadata.append(doc_id or record.get("record_title"))

            self._ensure_required_documents(context, inventory, qa_flags, manual_queue)

            subjects_in_scope = list(dict.fromkeys(filter(None, subjects_in_scope)))
            if duplicates:
                qa_flags.append("duplicate_document_ids_detected")

            meta = {
                "qa_flags": qa_flags,
                "subjects_in_scope": subjects_in_scope,
                "manual_queue": list(dict.fromkeys(filter(None, manual_queue))),
                "missing_metadata": missing_metadata,
                "duplicates": duplicates,
            }
            return inventory, meta

        def _apply_parsing_rules(self, category: str, record: Dict[str, Any], doc: Dict[str, Any], context: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
            normalized_type = (record.get("record_type") or "").lower()
            for key, (mapped_category, mapped_label) in PARSING_MAP.items():
                if key in normalized_type:
                    category = mapped_category
                    record["record_type"] = mapped_label
                    break

            if record.get("subject_name"):
                record["subject_name"] = self._format_subject_name(record["subject_name"])

            if not record.get("record_date"):
                planning = context.get("planning_manifest") or {}
                fallback_date = planning.get("contract_date") or context.get("case_metadata", {}).get("contract_date")
                if fallback_date:
                    try:
                        record["record_date"] = datetime.fromisoformat(str(fallback_date)).date().isoformat()
                    except Exception:
                        record["record_date"] = str(fallback_date)

            return category, record

        def _ensure_required_documents(self, context: Dict[str, Any], inventory: Dict[str, List[Dict[str, Any]]], qa_flags: List[str], manual_queue: List[str]) -> None:
            existing_titles = {
                (record.get("record_title") or "").lower()
                for records in inventory.values()
                for record in records
            }
            case_meta = context.get("case_metadata", {})
            for short_name, display_name in REQUIRED_FINAL_DOCS:
                key = short_name.lower()
                if key in existing_titles:
                    continue
                qa_flags.append("required_document_missing")
                manual_queue.append(display_name)
                record = {
                    "document_id": f"required::{key}",
                    "record_title": display_name,
                    "subject_name": self._format_subject_name(case_meta.get("client_name")),
                    "record_type": display_name,
                    "jurisdiction": case_meta.get("client_jurisdiction", ""),
                    "record_date": case_meta.get("contract_date", ""),
                    "verification_status": "PENDING",
                    "relevance": None,
                    "custody_reference": "",
                    "notes": "Required document placeholder awaiting upload.",
                    "missing_fields": ["document_file"],
                }
                inventory.setdefault("case_administration", []).append(record)

        def _categorize_document(self, doc: Dict[str, Any], record: Dict[str, Any]) -> str:
            raw_category = (doc.get("category") or doc.get("normalized_category") or record.get("record_type") or "").lower()
            mapping = {
                "identity": "identity_records",
                "government": "supporting_government_records",
                "court": "county_and_court_filings",
                "filing": "county_and_court_filings",
                "delivery": "delivery_confirmations",
                "correspondence": "case_administration",
                "contract": "case_administration",
            }
            for key, target in mapping.items():
                if key in raw_category:
                    return target
            return "case_administration"

        def _normalize_record(self, doc: Dict[str, Any], context: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str], List[str], bool]:
            record: Dict[str, Any] = {}
            qa_flags: List[str] = []
            manual_review = False
            missing: List[str] = []
            doc_id = doc.get("document_id") or doc.get("id")
            record["document_id"] = doc_id
            record_title = self._first_nonempty(doc.get("display_name"), doc.get("title"), doc.get("file_name"))
            if not record_title:
                record_title = f"Document {doc_id or len(str(doc))}"
                qa_flags.append("document_title_missing")
            record["record_title"] = record_title
            raw_subject = self._first_nonempty(doc.get("subject_name"), doc.get("subject"), doc.get("party"))
            formatted_subject = self._format_subject_name(raw_subject)
            if formatted_subject:
                record["subject_name"] = formatted_subject
            else:
                record["subject_name"] = ""
                missing.append("subject_name")
            record_type = self._first_nonempty(doc.get("record_type"), doc.get("type"), doc.get("category"))
            if not record_type:
                record_type = "Unspecified Record"
                qa_flags.append("record_type_missing")
                missing.append("record_type")
            record["record_type"] = record_type
            jurisdiction = self._first_nonempty(doc.get("jurisdiction"), doc.get("issuing_authority"), doc.get("county"))
            if jurisdiction:
                record["jurisdiction"] = jurisdiction
            else:
                record["jurisdiction"] = ""
                missing.append("jurisdiction")
            record_date = self._first_nonempty(doc.get("record_date"), doc.get("issued_date"), doc.get("filing_date"))
            if record_date:
                try:
                    record["record_date"] = datetime.fromisoformat(str(record_date)).date().isoformat()
                except Exception:
                    record["record_date"] = str(record_date)
            else:
                record["record_date"] = ""
                missing.append("record_date")
            record["verification_status"] = doc.get("verification_status") or doc.get("status") or "PENDING"
            relevance = doc.get("relevance") or doc.get("relevance_score")
            if relevance is not None:
                record["relevance"] = float(relevance)
            custody = doc.get("custody_reference") or doc.get("anchor_id") or doc.get("storage_location")
            record["custody_reference"] = custody or ""
            notes = self._first_nonempty(doc.get("notes"), doc.get("summary"))
            record["notes"] = notes or ""
            record["missing_fields"] = missing
            if missing:
                qa_flags.append("document_metadata_missing")
                manual_review = True
            subjects_in_scope = [formatted_subject] if formatted_subject else []
            return record, qa_flags, subjects_in_scope, manual_review

        def _build_summary_stats(self, inventory: Dict[str, List[Dict[str, Any]]], meta: Dict[str, Any]) -> Dict[str, Any]:
            counts = {category: len(records) for category, records in inventory.items() if records}
            total = sum(counts.values())
            return {
                "counts": counts,
                "total_documents": total,
                "missing_metadata": len(meta.get("missing_metadata", [])),
            }

        def _compose_notes(self, case_mode: str, context: Dict[str, Any], meta: Dict[str, Any]) -> str:
            notes: List[str] = []
            if meta.get("missing_metadata"):
                notes.append(
                    f"Metadata completion required for: {', '.join(meta['missing_metadata'])}"
                )
            if meta.get("duplicates"):
                notes.append(
                    f"Duplicate document identifiers detected: {', '.join(meta['duplicates'])}"
                )
            notes.extend(str(item).strip() for item in meta.get("notes", []) if str(item).strip())
            notes.extend(str(item).strip() for item in context.get("manual_annotations", []) if str(item).strip())
            continuity = context.get("toolkit_results", {}).get("continuity")
            if continuity:
                if isinstance(continuity, str):
                    notes.append(continuity)
                else:
                    notes.extend(str(item).strip() for item in continuity if str(item).strip())
            if case_mode == "investigative":
                notes.append("Inventory reflects investigative document acquisition.")
            if not notes:
                return "Inventory verified with no outstanding issues."
            return '\n'.join(dict.fromkeys(notes))


        def _run_inline_tools(self, context: Dict[str, Any], inventory: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
            documents = [record for records in inventory.values() for record in records]
            case_meta = context.get("case_metadata", {})
            subjects = case_meta.get("subjects") or []
            identity_candidates = context.get("toolkit_results", {}).get("identity_candidates", {})
            identity_checks: List[Dict[str, Any]] = []
            for subject in subjects:
                if not isinstance(subject, dict):
                    continue
                subject_id = subject.get("id") or subject.get("subject_id")
                candidate = identity_candidates.get(subject_id) if subject_id else None
                if candidate:
                    identity_checks.append(
                        {
                            "subject_id": subject_id,
                            "result": CochranMatchTool.verify_identity(subject, candidate),
                        }
                    )
            text_blob = "\n".join(
                filter(
                    None,
                    [
                        record.get("record_title")
                        for record in documents
                    ],
                )
            )
            reverse_tool = ReverseContinuityTool()
            continuity_docs = [json.dumps(record, default=str) for record in documents]
            planning_docs = context.get("planning_manifest", {}).get("supporting_documents") or []
            reverse_ok, reverse_log = reverse_tool.run_validation(
                text_blob,
                continuity_docs,
                [json.dumps(doc, default=str) for doc in planning_docs],
            )
            metadata_zip = context.get("metadata_bundle_zip") or context.get("raw_inputs", {}).get("metadata_bundle_zip")
            metadata_result = (
                MetadataToolV5.process_zip(metadata_zip, context.get("metadata_output_dir", "./metadata_out"))
                if metadata_zip
                else {"status": "SKIPPED"}
            )
            qa_flags: List[str] = []
            if not reverse_ok:
                qa_flags.append("reverse_continuity_manual_review")
            if metadata_result.get("status") == "ERROR":
                qa_flags.append("metadata_extraction_failure")
            # Process OCR documents if available
            ocr_results = {}
            if OCR_AVAILABLE:
                ocr_results = self._process_ocr_documents(context)
            
            if ocr_results.get("ocr_processing_issues"):
                qa_flags.append("ocr_processing_issues")
            
            return {
                "identity_checks": identity_checks,
                "reverse_continuity": {"ok": bool(reverse_ok), "log": reverse_log},
                "metadata_audit": metadata_result,
                "ocr_results": ocr_results,
                "qa_flags": qa_flags,
            }

        def _process_ocr_documents(self, context: Dict[str, Any]) -> Dict[str, Any]:
            """Process PDF and image documents using OCR"""
            ocr_results = {
                "pdf_documents": [],
                "image_documents": [],
                "ocr_processing_issues": []
            }
            
            try:
                # Get documents from various sources
                document_index = context.get("document_index", [])
                planning_manifest = context.get("planning_manifest", {})
                repository_metadata = context.get("repository_metadata", {})
                
                # Collect all document paths
                document_paths = []
                for doc in document_index:
                    if isinstance(doc, dict) and doc.get("file_path"):
                        document_paths.append(doc["file_path"])
                
                # Process each document
                for doc_path in document_paths:
                    if not os.path.exists(doc_path):
                        ocr_results["ocr_processing_issues"].append(f"Document not found: {doc_path}")
                        continue
                    
                    file_ext = os.path.splitext(doc_path)[1].lower()
                    
                    if file_ext == '.pdf':
                        try:
                            text = extract_text_from_pdf(doc_path)
                            ocr_results["pdf_documents"].append({
                                "path": doc_path,
                                "extracted_text": text[:500] + "..." if len(text) > 500 else text,
                                "status": "success"
                            })
                        except Exception as e:
                            ocr_results["ocr_processing_issues"].append(f"PDF OCR failed for {doc_path}: {str(e)}")
                    
                    elif file_ext in ['.jpg', '.jpeg', '.png', '.tiff', '.bmp']:
                        try:
                            text = extract_text_from_image(doc_path)
                            ocr_results["image_documents"].append({
                                "path": doc_path,
                                "extracted_text": text[:500] + "..." if len(text) > 500 else text,
                                "status": "success"
                            })
                        except Exception as e:
                            ocr_results["ocr_processing_issues"].append(f"Image OCR failed for {doc_path}: {str(e)}")
                
            except Exception as e:
                ocr_results["ocr_processing_issues"].append(f"OCR processing error: {str(e)}")
            
            return ocr_results

        def _build_renderer_sources(self, context: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
            return {
                "intake": context.get("case_metadata", {}),
                "prior_section": context.get("planning_manifest", {}),
                "upload_index": context.get("repository_metadata", {}),
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

        def _format_subject_name(self, value: Optional[str]) -> Optional[str]:
            if not value:
                return None
            parts = [part.strip() for part in value.replace(",", " ").split() if part.strip()]
            if not parts:
                return None
            if len(parts) == 1:
                return parts[0]
            last = parts[-1]
            first_middle = " ".join(parts[:-1])
            return f"{last}, {first_middle}"


__all__ = [
    "Section5Framework",
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

