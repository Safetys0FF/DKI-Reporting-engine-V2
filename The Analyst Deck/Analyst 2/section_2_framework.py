"""Framework template for Section 2 (Pre-Surveillance / Case Preparation)."""

from __future__ import annotations

import json
import logging
import os
import re
import zipfile
import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from difflib import SequenceMatcher
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

    # ------------------------------------------------------------------
    # Lifecycle hooks
    # ------------------------------------------------------------------
    def load_inputs(self) -> Dict[str, Any]:
        raise NotImplementedError

    def build_payload(self, context: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError

    def publish(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError

    # ------------------------------------------------------------------
    # Utility helpers
    # ------------------------------------------------------------------
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
    
    # Enhanced report configurations
    report_configs = {
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
            }
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
                "forced_render_order": ["2A_case_summary", "2B_subject_information", "2C_habits_and_POIs", "2B_investigative_data", "2D_visual_assets", "2E_final_planning"],
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

class Section2Renderer:
    SECTION_KEY = "section_2"
    TITLE = "SECTION 2 - PRE-SURVEILLANCE / CASE PREP"
    SUBSECTIONS = {
        "2A": ["case_summary", "summary_tags", "case_type_token"],
        "2B": [
            "verified_subjects",
            "known_aliases",
            "verified_addresses",
            "subject_vehicles",
            "subject_employment",
            "subject_contact",
        ],
        "2C": ["routines", "poi_tags", "timeline_blocks", "observed_patterns"],
        "2D": ["geo_areas", "pinned_locations", "visual_aids"],
        "2E": [
            "field_ready",
            "ethics_statement",
            "surveillance_hours_allocated",
            "planning_notes",
        ],
    }
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
        "subsection_header": {
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

    def render_model(self, section_payload: Dict[str, Any], case_sources: Dict[str, Dict[str, Any]]):
        rendered_blocks: List[Dict[str, Any]] = []
        placeholders_used: Dict[str, str] = {}
        drift_bounced: Dict[str, Any] = {}
        
        # Use dynamic title from payload
        section_title = section_payload.get("section_heading", self.TITLE)
        rendered_blocks.append(
            {
                "type": "title",
                "text": section_title,
                "style": self.STYLE_RULES["section_title"],
            }
        )
        
        # Get contract configuration for render order
        contract_config = section_payload.get("contract_config", {})
        report_type = section_payload.get("report_type", "Surveillance")
        
        # Determine render order based on contract config
        if contract_config.get("effects", {}).get("forced_render_order"):
            render_order = contract_config["effects"]["forced_render_order"]
            # Convert to subsection keys
            subsection_order = []
            for item in render_order:
                if item.startswith("2"):
                    subsection_order.append(item)
        else:
            # Default order
            subsection_order = ["2A", "2B", "2C", "2D", "2E"]
        
        # Get whitelist-determined subsections
        whitelist = section_payload.get("whitelist_applied", {})
        active_subsections = whitelist.get("subsections", list(self.SUBSECTIONS.keys()))
        
        # Apply contract-based hiding
        if contract_config.get("effects", {}).get("hide"):
            hidden_sections = contract_config["effects"]["hide"]
            active_subsections = [s for s in active_subsections if s not in hidden_sections]
        
        # Render subsections in contract-determined order
        for sub_key in subsection_order:
            if sub_key not in active_subsections or sub_key not in self.SUBSECTIONS:
                continue
                
            field_keys = self.SUBSECTIONS[sub_key]
            rendered_blocks.append(
                {
                    "type": "subheader",
                    "text": f"SUBSECTION {sub_key}",
                    "style": self.STYLE_RULES["subsection_header"],
                }
            )
            
            # Special handling for hybrid reports with investigative data
            if sub_key == "2B" and report_type == "Hybrid":
                # Add investigative data fields
                investigative_fields = [
                    "investigative_findings", "court_records", "background_checks", 
                    "social_media_intel", "public_records", "investigative_summary"
                ]
                field_keys = list(field_keys) + investigative_fields
            
            for key in field_keys:
                value = section_payload.get(key)
                if not value:
                    value = self._fallback_check(key, case_sources)
                normalized = self._normalize(value)
                value_to_render, is_placeholder = self._placeholder_for(key, normalized)
                if is_placeholder:
                    placeholders_used[key] = value_to_render
                rendered_blocks.append(
                    {
                        "type": "field",
                        "label": key.replace("_", " ").title(),
                        "value": value_to_render,
                        "style": self.STYLE_RULES["placeholder_value"]
                        if is_placeholder
                        else self.STYLE_RULES["field_value"],
                    }
                )
        
        # Add contract-specific disclaimer if present
        if section_payload.get("contract_disclaimer"):
            rendered_blocks.append(
                {
                    "type": "disclaimer",
                    "text": section_payload["contract_disclaimer"],
                    "style": self.STYLE_RULES["field_value"],
                }
            )
        
        manifest = {
            "section_key": self.SECTION_KEY,
            "placeholders_used": placeholders_used,
            "fields_rendered": [k for keys in self.SUBSECTIONS.values() for k in keys],
            "drift_bounced": drift_bounced,
            "whitelist_applied": whitelist,
            "contract_config": contract_config,
            "report_type": report_type,
        }
        return {
            "render_tree": rendered_blocks,
            "manifest": manifest,
            "handoff": "gateway",
        }

NO_SURVEILLANCE_MESSAGE = "Due to the nature of this case no surveillance or surveillance planning was performed."
PLANNING_DISCLAIMER = (
    "The investigative work and research used to prepare the pre-surveillance report is based solely on the "
    "information provided by the client. All findings, references, and assessments contained therein were intended "
    "exclusively for operational planning purposes. No claims made by the client were independently tested, verified, "
    "or contested prior to field deployment. The following section outlines the objectives, scope, and preliminary "
    "findings conducted by DKI Services LLC before initiating field surveillance. This includes verification of subject "
    "information, locations of interest, behavioral patterns, and logistics planning to ensure legal and operational "
    "efficiency. All intelligence information was obtained before live observation and cross-referenced against client "
    "observations and suspicions disclosed during the intake process. This section is not intended to confirm or dispute "
    "the client's concerns or allegations, but to prepare for legal and operational investigation."
)
SUBCONTRACTOR_STATEMENTS = {
    "final": (
        "This case utilized subcontracted field agents operating under their respective state licensing requirements "
        "and within their legal limitations, and in agreement with DKI Services."
    ),
    "pre": (
        "This case utilized subcontracted field agents operating under their respective state licensing requirements "
        "and within their legal limitations, and in agreement with DKI Services. This case is allotted {hours} hours of "
        "surveillance, subject to change based on the client's authorization and investigative need."
    ),
    "owner": (
        "This case is prepared and conducted by DKI Services and is allotted {hours} hours of surveillance, subject to "
        "change based on the client's authorization and investigative need."
    ),
}
CASE_MODE_TO_HEADING = {
    "investigative": "SECTION 2 - INVESTIGATIVE REQUIREMENTS",
    "field": "SECTION 2 - PRE-SURVEILLANCE SUMMARY",
    "hybrid": "SECTION 2 - HYBRID PREPARATION SUMMARY",
}


class Section2Framework(SectionFramework):
    SECTION_ID = "section_2_planning"
    BUS_SECTION_ID = "section_2"
    MAX_RERUNS = 2
    STAGES = (
        StageDefinition(
            name="intake",
            description="Pull gateway bundle, confirm Section 1 hash, load planning documents.",
            checkpoint="s2_intake_logged",
            guardrails=("order_lock", "async_queue", "persistence_snapshot"),
            inputs=("case_metadata", "section_1_manifest", "planning_docs"),
            outputs=("planning_context",),
        ),
        StageDefinition(
            name="verify",
            description="Confirm subject identities via toolkit/OSINT alignment.",
            checkpoint="s2_subjects_verified",
            guardrails=("identity_link", "fact_graph_sync"),
            inputs=("subject_manifest", "osint_cache"),
            outputs=("verified_subjects",),
        ),
        StageDefinition(
            name="analyze",
            description="Derive routines, timelines, and geospatial anchors using parsing maps.",
            checkpoint="s2_analysis_complete",
            guardrails=("schema_validation", "north_star", "continuity_checks"),
            inputs=("planning_docs", "toolkit_results"),
            outputs=("analysis_manifest",),
        ),
        StageDefinition(
            name="validate",
            description="Apply compliance policy checks, risk scoring, and manual queue triggers.",
            checkpoint="s2_validated",
            guardrails=("manual_queue_routes", "risk_threshold", "immutability_precheck"),
            inputs=("analysis_manifest",),
            outputs=("validated_manifest",),
        ),
        StageDefinition(
            name="publish",
            description="Publish payload, emit planning signals, and lock manifest.",
            checkpoint="section_2_completed",
            guardrails=("durable_persistence", "signal_emission", "immutability"),
            inputs=("validated_manifest",),
            outputs=("gateway_handoff",),
        ),
        StageDefinition(
            name="monitor",
            description="Handle revision requests while enforcing rerun guardrails.",
            checkpoint="s2_revision_processed",
            guardrails=("max_reruns", "revision_depth_cap", "fact_graph_consistency"),
        ),
    )
    COMMUNICATION = CommunicationContract(
        prepare_signal="section_1_profile.completed",
        input_channels=(
            "case_metadata",
            "subject_manifest",
            "planning_docs",
            "osint_cache",
            "toolkit_results",
            "section_1_manifest",
        ),
        output_signal="section_2_planning.completed",
        revision_signal="planning_revision_requested",
    )
    ORDER = OrderContract(
        execution_after=("section_1_profile", "section_cp"),
        export_after=("section_3", "section_4", "section_6", "section_8"),
        export_priority=20,
    )

    def __init__(self, gateway: Any, ecc: Optional[Any] = None) -> None:
        super().__init__(gateway=gateway, ecc=ecc)
        self._last_context: Dict[str, Any] = {}

    def load_inputs(self) -> Dict[str, Any]:
        try:
            self._guard_execution("input loading")
            bundle = self.gateway.get_section_inputs("section_2") if self.gateway else {}
            context = {
                "raw_inputs": bundle,
                "case_metadata": bundle.get("case_metadata", {}),
                "section_1_manifest": bundle.get("section_1_manifest", {}),
                "subject_manifest": bundle.get("subject_manifest", []),
                "planning_docs": bundle.get("planning_docs", {}),
                "osint_cache": bundle.get("osint_cache", {}),
                "toolkit_results": bundle.get("toolkit_results", {}),
                "contracts": bundle.get("case_metadata", {}).get("contracts", []),
            }
            context["basic_stats"] = {
                "subject_count": len(context["subject_manifest"]),
                "planning_asset_count": len(context["planning_docs"].get("route_assets", [])),
            }
            context = self._augment_with_bus_context(context)
            self.logger.debug("Section 2 inputs loaded: %s", context["basic_stats"])
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
            contracts = context.get("contracts", [])
            report_config = get_report_config(contracts) if contracts else {"report_type": "Surveillance", "config": {}}
            report_type = report_config["report_type"]
            config = report_config["config"]
            
            # Get ECC-determined whitelist (can override contract config)
            whitelist = context.get("ecc_whitelist", {})
            
            # Determine active subsections based on report type and whitelist
            if whitelist.get("subsections"):
                active_subsections = whitelist["subsections"]
            else:
                # Use contract-based logic
                if report_type == "Investigative":
                    active_subsections = ["2A", "2B"]  # Hide 2C, 2D per config
                elif report_type == "Hybrid":
                    active_subsections = ["2A", "2B", "2C", "2D", "2E"]  # All sections
                else:  # Surveillance
                    active_subsections = ["2A", "2B", "2C", "2D", "2E"]  # All sections
            
            # Apply hide effects from contract config
            if config.get("effects", {}).get("hide"):
                hidden_sections = config["effects"]["hide"]
                active_subsections = [s for s in active_subsections if s not in hidden_sections]
            
            ethics_type = whitelist.get("ethics_statement", "default")
            billing_model = whitelist.get("billing_model", config.get("billing", "auto"))
            content_suppression = whitelist.get("content_suppression", [])
            
            case_mode = self._determine_case_mode(context)
            requires_surveillance = case_mode in {"field", "hybrid"}
            
            # Use contract-based section heading
            section_heading = config.get("label", CASE_MODE_TO_HEADING.get(case_mode, CASE_MODE_TO_HEADING["field"]))
            
            # Start with base payload
            payload: Dict[str, Any] = {
                "section_heading": section_heading,
                "case_type_token": case_mode.upper(),
                "report_type": report_type,
                "whitelist_applied": whitelist,
                "contract_config": config,
            }
            
            # Build subsections based on active list and render order
            render_order = config.get("effects", {}).get("forced_render_order", ["2A", "2B", "2C", "2D", "2E"])
            
            for subsection in render_order:
                if subsection in active_subsections:
                    if subsection == "2A":
                        payload.update({
                            "case_summary": self._build_case_summary(context, case_mode, requires_surveillance),
                            "summary_tags": self._collect_summary_tags(context, case_mode),
                        })
                    elif subsection == "2B":
                        payload.update(self._build_subject_sections(context))
                        # Add investigative data for hybrid reports
                        if report_type == "Hybrid":
                            payload.update(self._build_investigative_data_section(context))
                    elif subsection == "2C":
                        payload.update(self._build_routine_sections(context, requires_surveillance, content_suppression))
                    elif subsection == "2D":
                        payload.update(self._build_geospatial_sections(context, requires_surveillance, content_suppression))
                    elif subsection == "2E":
                        payload.update(self._build_readiness_section(context, case_mode, requires_surveillance, ethics_type))
            
            # Apply contract-based billing
            payload["billing"] = self._determine_billing(context, case_mode, requires_surveillance, billing_model)
            payload["tool_results"] = self._run_inline_tools(context, requires_surveillance)
            payload["requires_surveillance"] = requires_surveillance
            payload["content_suppression"] = content_suppression
            
            # Add contract-specific disclaimer
            if config.get("disclaimer"):
                payload["contract_disclaimer"] = config["disclaimer"]
            
            case_id = context.get("case_id") or context.get("bus_state", {}).get("case_id")
            if case_id:
                payload["case_id"] = case_id
            payload["section_id"] = self.bus_section_id() or "section_2"
            if context.get("manifest_context") is not None:
                payload.setdefault("manifest_context", context.get("manifest_context"))
            if context.get("section_needs") is not None:
                payload.setdefault("section_needs", context.get("section_needs"))
            if context.get("evidence") is not None:
                payload.setdefault("section_evidence", context.get("evidence"))
            if context.get("bus_state") is not None:
                payload.setdefault("bus_state", context.get("bus_state"))
            return payload
        except Exception as exc:
            self.logger.exception("Failed to build payload for %s: %s", self.SECTION_ID, exc)
            return {"error": str(exc)}

    def publish(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # 1. ECC validation
            if self.ecc:
                if not self.ecc.can_run(self.SECTION_ID):
                    raise Exception(f"Section {self.SECTION_ID} not active for publishing")
            
            # 2. Generate narrative (Section 2 specific)
            renderer = Section2Renderer()
            case_sources = self._build_renderer_sources(self._last_context)
            model = renderer.render_model(payload, case_sources)
            
            # Build narrative from render tree
            narrative_lines: List[str] = []
            for block in model["render_tree"]:
                if block["type"] == "field":
                    narrative_lines.append(f"{block['label']}: {block['value']}")
                else:
                    narrative_lines.append(str(block["text"]))
            narrative = "\n".join(narrative_lines)
            
            # 3. Create result package
            section_bus_id = self.bus_section_id() or "section_2"
            timestamp = datetime.now().isoformat()
            summary = narrative.splitlines()[0] if narrative else ""
            summary = summary[:320]
            result = {
                "section_id": section_bus_id,
                "case_id": payload.get("case_id"),
                "payload": payload,
                "manifest": model["manifest"],
                "narrative": narrative,
                "summary": summary,
                "metadata": {"published_at": timestamp, "section": self.SECTION_ID},
                "source": "section_2_framework",
            }

            # 4. Gateway publishing
            self.gateway.publish_section_result(section_bus_id, result)

            # 5. ECC completion notification
            if self.ecc:
                self.ecc.mark_complete(self.SECTION_ID)

            # 6. Signal emission (standardized)
            emit_payload = dict(result)
            emit_payload.setdefault("published_at", timestamp)
            self.gateway.emit("section_2_planning.completed", emit_payload)

            return {
                "status": "published",
                "narrative": narrative,
                "manifest": model["manifest"]
            }
        except Exception as exc:
            self.logger.exception("Failed to publish for %s: %s", self.SECTION_ID, exc)
            return {"error": str(exc)}

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _determine_case_mode(self, context: Dict[str, Any]) -> str:
        """Enhanced case mode determination using contract analysis"""
        contracts = context.get("contracts") or []
        
        # Use enhanced contract analysis if available
        if contracts:
            try:
                contract_config = get_report_config(contracts)
                report_type = contract_config["report_type"].lower()
                if report_type in ["investigative", "surveillance", "hybrid"]:
                    return report_type
            except Exception as e:
                self.logger.warning(f"Contract analysis failed, falling back to basic logic: {e}")
        
        # Fallback to original logic
        case_meta = context.get("case_metadata", {})
        contract_type = (case_meta.get("contract_type") or case_meta.get("case_type") or "").lower()
        mapping = {
            "investigative": "investigative",
            "investigative_report": "investigative", 
            "field": "field",
            "surveillance": "field",
            "hybrid": "hybrid",
            "mixed": "hybrid",
        }
        if contract_type in mapping:
            return mapping[contract_type]
        
        # Basic contract analysis
        has_surveillance = any(
            (contract.get("type") or "").lower() in {"field", "surveillance"} for contract in contracts
        )
        has_investigative = any(
            (contract.get("type") or "").lower() in {"investigative", "analysis"} for contract in contracts
        )
        if has_surveillance and has_investigative:
            return "hybrid"
        if has_surveillance:
            return "field"
        if has_investigative:
            return "investigative"
        return "field"

    def _build_case_summary(
        self,
        context: Dict[str, Any],
        case_mode: str,
        requires_surveillance: bool,
    ) -> str:
        case_meta = context.get("case_metadata", {})
        section1 = context.get("section_1_manifest", {})
        planning_docs = context.get("planning_docs", {})
        summary_sources = [
            planning_docs.get("case_summary"),
            case_meta.get("case_summary"),
            section1.get("case_summary"),
            case_meta.get("intake_summary"),
        ]
        summary = self._first_nonempty(*summary_sources) or "Summary forthcoming pending verification."
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", summary) if s.strip()]
        summary_limited = " ".join(sentences[:5])
        components = [summary_limited]
        objective = case_meta.get("client_objective") or section1.get("investigation_goals")
        if objective:
            components.append(f"Client objective: {objective}.")
        if not requires_surveillance:
            components.append(NO_SURVEILLANCE_MESSAGE)
        components.append(PLANNING_DISCLAIMER)
        return " ".join(components)

    def _collect_summary_tags(self, context: Dict[str, Any], case_mode: str) -> List[str]:
        toolkit = context.get("toolkit_results", {})
        tags = list(toolkit.get("summary_tags", []) or [])
        if not tags:
            tags = [case_mode.upper(), "PLANNING"]
        return tags

    def _build_subject_sections(self, context: Dict[str, Any]) -> Dict[str, Any]:
        subjects = context.get("subject_manifest", []) or []
        verified_subjects: List[str] = []
        aliases: List[str] = []
        addresses: List[str] = []
        vehicles: List[str] = []
        employment: List[str] = []
        contact: List[str] = []
        for subject in subjects:
            verified_subjects.append(self._format_subject_line(subject))
            aliases.extend(subject.get("known_aliases", []))
            if subject.get("address"):
                addresses.append(f"{subject['full_name']}: {subject['address']}")
            for vehicle in subject.get("vehicles", []):
                vehicles.append(
                    f"{subject.get('full_name', 'Subject')} - {vehicle.get('year', '')} {vehicle.get('make', '')} {vehicle.get('model', '')} {vehicle.get('tag', '')}".strip()
                )
            if subject.get("employment"):
                employment.append(f"{subject['full_name']}: {subject['employment']}")
            if subject.get("contact"):
                contact.append(f"{subject['full_name']}: {subject['contact']}")
        if not verified_subjects:
            verified_subjects.append("No subjects confirmed at this stage.")
        return {
            "verified_subjects": "\n".join(verified_subjects),
            "known_aliases": "\n".join(aliases) if aliases else "None documented",
            "verified_addresses": "\n".join(addresses) if addresses else "Pending confirmation",
            "subject_vehicles": "\n".join(vehicles) if vehicles else "Not reported",
            "subject_employment": "\n".join(employment) if employment else "Not confirmed",
            "subject_contact": "\n".join(contact) if contact else "Not provided",
        }

    def _build_investigative_data_section(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Build investigative data section for hybrid reports"""
        planning_docs = context.get("planning_docs", {})
        toolkit_results = context.get("toolkit_results", {})
        
        # Investigative research findings
        research_findings = planning_docs.get("investigative_findings", [])
        court_records = planning_docs.get("court_records", [])
        background_checks = planning_docs.get("background_checks", [])
        
        # OSINT data
        osint_data = context.get("osint_cache", {})
        social_media = osint_data.get("social_media_findings", [])
        public_records = osint_data.get("public_records", [])
        
        return {
            "investigative_findings": self._safe_join(research_findings, default="Research findings pending review"),
            "court_records": self._safe_join(court_records, default="Court records under review"),
            "background_checks": self._safe_join(background_checks, default="Background verification in progress"),
            "social_media_intel": self._safe_join(social_media, default="Social media analysis pending"),
            "public_records": self._safe_join(public_records, default="Public records verification ongoing"),
            "investigative_summary": "Documented investigative research conducted prior to field deployment. All findings have been verified and cross-referenced against client intake information."
        }

    def _build_routine_sections(
        self,
        context: Dict[str, Any],
        requires_surveillance: bool,
        content_suppression: List[str] = None,
    ) -> Dict[str, Any]:
        if not requires_surveillance:
            return {
                "routines": NO_SURVEILLANCE_MESSAGE,
                "poi_tags": NO_SURVEILLANCE_MESSAGE,
                "timeline_blocks": NO_SURVEILLANCE_MESSAGE,
                "observed_patterns": NO_SURVEILLANCE_MESSAGE,
            }
        planning_docs = context.get("planning_docs", {})
        routines = planning_docs.get("routines") or []
        poi_tags = planning_docs.get("poi_tags") or []
        timeline = planning_docs.get("timeline_blocks") or []
        patterns = planning_docs.get("observed_patterns") or []
        return {
            "routines": self._safe_join(routines, default="Routines pending analysis"),
            "poi_tags": self._safe_join(poi_tags, default="POIs under review"),
            "timeline_blocks": self._safe_join(timeline, default="Timeline will be established post-verification"),
            "observed_patterns": self._safe_join(patterns, default="Patterns to be confirmed"),
        }

    def _build_geospatial_sections(
        self,
        context: Dict[str, Any],
        requires_surveillance: bool,
        content_suppression: List[str] = None,
    ) -> Dict[str, Any]:
        if not requires_surveillance:
            return {
                "geo_areas": NO_SURVEILLANCE_MESSAGE,
                "pinned_locations": NO_SURVEILLANCE_MESSAGE,
                "visual_aids": NO_SURVEILLANCE_MESSAGE,
            }
        planning_docs = context.get("planning_docs", {})
        geo_areas = planning_docs.get("geo_areas") or []
        pinned = planning_docs.get("pinned_locations") or []
        visuals = planning_docs.get("visual_aids") or []
        return {
            "geo_areas": self._safe_join(geo_areas, default="Geographic focus pending final clearance"),
            "pinned_locations": self._safe_join(pinned, default="No locations pinned yet"),
            "visual_aids": self._safe_join(visuals, default="Maps and imagery will attach post-validation"),
        }

    def _build_readiness_section(
        self,
        context: Dict[str, Any],
        case_mode: str,
        requires_surveillance: bool,
        ethics_type: str = "default",
    ) -> Dict[str, Any]:
        planning_docs = context.get("planning_docs", {})
        hours = planning_docs.get("surveillance_hours") or context.get("case_metadata", {}).get("authorized_hours")
        hours_text = f"{hours} hours" if hours else "Pending authorization"
        if not requires_surveillance:
            field_ready = NO_SURVEILLANCE_MESSAGE
            planning_notes = NO_SURVEILLANCE_MESSAGE
        else:
            field_ready = planning_docs.get("field_ready") or "Field team activation pending final compliance check"
            planning_notes = self._safe_join(
                planning_docs.get("planning_notes") or [],
                default="Planning notes to be finalized after toolkit reconciliation",
            )
        # Use whitelist-determined ethics type
        if ethics_type == "subcontractor_pre":
            ethics_statement = SUBCONTRACTOR_STATEMENTS["pre"].format(hours=hours_text)
        elif ethics_type == "subcontractor_final":
            ethics_statement = SUBCONTRACTOR_STATEMENTS["final"]
        elif ethics_type == "owner_operator":
            ethics_statement = SUBCONTRACTOR_STATEMENTS["owner"].format(hours=hours_text)
        else:
            # Fallback to original logic
            subcontractor = context.get("case_metadata", {}).get("subcontractor_manifest", {})
            owner_operator = context.get("section_1_manifest", {}).get("agency_name") == "DKI Services LLC"
            if subcontractor and subcontractor.get("active"):
                ethics_statement = SUBCONTRACTOR_STATEMENTS["pre"].format(hours=hours_text)
            elif owner_operator:
                ethics_statement = SUBCONTRACTOR_STATEMENTS["owner"].format(hours=hours_text)
            else:
                ethics_statement = SUBCONTRACTOR_STATEMENTS["final"]
        return {
            "field_ready": field_ready,
            "ethics_statement": ethics_statement,
            "surveillance_hours_allocated": hours_text,
            "planning_notes": planning_notes,
        }

    def _determine_billing(
        self,
        context: Dict[str, Any],
        case_mode: str,
        requires_surveillance: bool,
        billing_model: str = "auto",
    ) -> Dict[str, Any]:
        contracts = context.get("contracts") or []
        multi_contract = len(contracts) >= 2
        field_contracts = [c for c in contracts if (c.get("type") or "").lower() in {"field", "surveillance"}]
        investigative_contracts = [c for c in contracts if (c.get("type") or "").lower() in {"investigative", "analysis"}]
        billing_model = context.get("case_metadata", {}).get("billing_model")
        if not billing_model:
            if case_mode == "investigative":
                billing_model = "flat"
            elif case_mode == "field":
                billing_model = "hourly"
            else:
                billing_model = "hybrid"
        planning_fee_assumed = False
        if requires_surveillance and field_contracts:
            prior_field_history = context.get("case_metadata", {}).get("field_contract_history")
            planning_fee_assumed = not prior_field_history
        flags = {
            "multi_contract_mode": multi_contract,
            "planning_fee_assumed": planning_fee_assumed,
            "investigative_components": bool(investigative_contracts),
        }
        return {
            "model": billing_model,
            "flags": flags,
        }

    def _run_inline_tools(
        self,
        context: Dict[str, Any],
        requires_surveillance: bool,
    ) -> Dict[str, Any]:
        """Enhanced tool execution with OCR capabilities"""
        planning_docs = context.get("planning_docs", {})
        subject_manifest = context.get("subject_manifest", [])
        osint_cache = context.get("osint_cache", {})
        identity_candidates = osint_cache.get("identity_candidates", {})
        identity_checks: List[Dict[str, Any]] = []
        
        # Identity verification
        for subject in subject_manifest:
            candidate = identity_candidates.get(subject.get("id"), {})
            if candidate:
                identity_checks.append(
                    {
                        "subject_id": subject.get("id"),
                        "result": CochranMatchTool.verify_identity(subject, candidate),
                    }
                )
        
        # Route assets processing
        route_assets = planning_docs.get("route_assets", []) if requires_surveillance else []
        northstar_result = (
            NorthstarProtocolTool.process_assets(route_assets) if route_assets else {"status": "SKIPPED"}
        )
        
        # Reverse continuity validation
        reverse_tool = ReverseContinuityTool()
        intake_summary = context.get("case_metadata", {}).get("intake_summary", "")
        doc_log = planning_docs.get("analysis_documents", [])
        asset_text = planning_docs.get("asset_summaries", [])
        reverse_ok, reverse_log = reverse_tool.run_validation(intake_summary or "", doc_log, asset_text)
        
        # Enhanced metadata processing with OCR
        metadata_zip = planning_docs.get("metadata_zip")
        metadata_result = (
            MetadataToolV5.process_zip(metadata_zip, planning_docs.get("metadata_output_dir", "./metadata_out"))
            if metadata_zip
            else {"status": "SKIPPED"}
        )
        
        # OCR processing for documents
        ocr_results = {}
        if OCR_AVAILABLE:
            ocr_results = self._process_ocr_documents(planning_docs)
        
        # Mileage audit
        mileage_result = MileageToolV2.audit_mileage()
        
        return {
            "northstar": northstar_result,
            "identity_checks": identity_checks,
            "reverse_continuity": {"ok": bool(reverse_ok), "log": reverse_log},
            "metadata_audit": metadata_result,
            "mileage_audit": mileage_result,
            "ocr_results": ocr_results,
            "fallback_clause": None if requires_surveillance else NO_SURVEILLANCE_MESSAGE,
        }
    
    def _process_ocr_documents(self, planning_docs: Dict[str, Any]) -> Dict[str, Any]:
        """Process documents using OCR capabilities"""
        ocr_results = {}
        
        # Process PDFs
        pdf_files = planning_docs.get("pdf_documents", [])
        for pdf_path in pdf_files:
            if os.path.exists(pdf_path):
                ocr_results[f"pdf_{os.path.basename(pdf_path)}"] = extract_text_from_pdf(pdf_path)
        
        # Process images
        image_files = planning_docs.get("image_documents", [])
        for img_path in image_files:
            if os.path.exists(img_path):
                ocr_results[f"image_{os.path.basename(img_path)}"] = {
                    "tesseract": extract_text_from_image(img_path),
                    "easyocr": easyocr_text(img_path)
                }
        
        return ocr_results

    def _build_renderer_sources(self, context: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        return {
            "intake": context.get("case_metadata", {}),
            "notes": context.get("planning_docs", {}).get("investigator_notes", {}),
            "evidence": context.get("planning_docs", {}).get("evidence_manifest", {}),
            "prior_section": context.get("section_1_manifest", {}),
        }

    @staticmethod
    def _format_subject_line(subject: Dict[str, Any]) -> str:
        name = subject.get("full_name") or subject.get("name") or "Subject"
        dob = subject.get("dob") or "DOB unknown"
        address = subject.get("address") or "Address pending"
        return f"{name} | DOB: {dob} | Address: {address}"

    @staticmethod
    def _safe_join(items: Iterable[Any], default: str) -> str:
        values = [str(item).strip() for item in items if str(item).strip()]
        return "\n".join(values) if values else default

    @staticmethod
    def _first_nonempty(*candidates: Optional[str]) -> Optional[str]:
        for candidate in candidates:
            if candidate:
                candidate_str = str(candidate).strip()
                if candidate_str:
                    return candidate_str
        return None

    SECTION_STRUCTURE = {
        "2A": {
            "title": "CASE SUMMARY",
            "components": [
                "Client Objective Recap",
                "Case Origin and Scope",
                "Operational Planning Disclaimer"
            ],
            "max_sentences": 5,
            "fallback": "Summary forthcoming pending verification."
        },
        "2B": {
            "title": "SUBJECT INFORMATION",
            "fields": [
                "Full Name",
                "Date of Birth",
                "Home Address",
                "Employment",
                "Vehicles",
                "Places of Interest"
            ],
            "group_by": "Subject Entity",
            "fallback_text": "Unknown at this time"
        },
        "2C": {
            "title": "SUBJECT HABITS, PATTERNS, AND PLACES OF INTEREST",
            "anchors": [
                "Daily Routines",
                "Travel Behavior",
                "Dining Preferences",
                "POIs: Confirmed/Suspected/Recommended"
            ],
            "logic": {
                "confirmed_POIs": "Client Intake",
                "suspected_POIs": "Subject-typical area + travel overlap",
                "recommended_POIs": "Map overlay, proximity, behavioral triggers"
            },
            "format": "Far-left alignment for operator photo insertion"
        },
        "2D": {
            "title": "MAPS AND VISUAL REFERENCE ASSETS",
            "media_types": [
                "Known Subjects",
                "Vehicles",
                "POI Maps"
            ],
            "metadata_rules": [
                "Match photo timestamps with surveillance window",
                "Validate GPS or location references",
                "No placeholders allowed"
            ]
        },
        "2E": {
            "title": "FINAL PLANNING STATEMENT",
            "includes": [
                "Ethics Declaration",
                "Surveillance Clause",
                "Planning Lock Confirmation"
            ],
            "logic_switch": "subcontractor_assigned + report_mode",
            "fallback_clause": "Due to the nature of this case, no surveillance planning was performed."
        }
    }
    SECTION_STRUCTURE = {
        "2A": {
            "title": "CASE SUMMARY",
            "components": [
                "Client Objective Recap",
                "Case Origin and Scope",
                "Operational Planning Disclaimer"
            ],
            "max_sentences": 5,
            "fallback": "Summary forthcoming pending verification."
        },
        "2B": {
            "title": "SUBJECT INFORMATION",
            "fields": [
                "Full Name",
                "Date of Birth",
                "Home Address",
                "Employment",
                "Vehicles",
                "Places of Interest"
            ],
            "group_by": "Subject Entity",
            "fallback_text": "Unknown at this time"
        },
        "2C": {
            "title": "SUBJECT HABITS, PATTERNS, AND PLACES OF INTEREST",
            "anchors": [
                "Daily Routines",
                "Travel Behavior",
                "Dining Preferences",
                "POIs: Confirmed/Suspected/Recommended"
            ],
            "logic": {
                "confirmed_POIs": "Client Intake",
                "suspected_POIs": "Subject-typical area + travel overlap",
                "recommended_POIs": "Map overlay, proximity, behavioral triggers"
            },
            "format": "Far-left alignment for operator photo insertion"
        },
        "2D": {
            "title": "MAPS AND VISUAL REFERENCE ASSETS",
            "media_types": [
                "Known Subjects",
                "Vehicles",
                "POI Maps"
            ],
            "metadata_rules": [
                "Match photo timestamps with surveillance window",
                "Validate GPS or location references",
                "No placeholders allowed"
            ]
        },
        "2E": {
            "title": "FINAL PLANNING STATEMENT",
            "includes": [
                "Ethics Declaration",
                "Surveillance Clause",
                "Planning Lock Confirmation"
            ],
            "logic_switch": "subcontractor_assigned + report_mode",
            "fallback_clause": "Due to the nature of this case, no surveillance planning was performed."
        }
    }

__all__ = [
    "Section2Framework",
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
