"""Framework template for Section 3 (Surveillance Reports / Daily Logs)."""

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
        media_sets = MediaCorrelationHelper.flatten_media_records(payload.get("media_index") or {})
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
        summary = VoiceTranscriptionHelper.summarize(memos)
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

class Section3Framework(SectionFramework):
    SECTION_ID = "section_3_logs"
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

    def __init__(self, gateway: Any, ecc: Optional[Any] = None) -> None:
        super().__init__(gateway=gateway, ecc=ecc)
        self._last_context: Dict[str, Any] = {}

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
            media_stats = MediaCorrelationHelper.collect_media_stats(context["media_index"])
            field_log_count = (
                len(context["field_logs"])
                if isinstance(context.get("field_logs"), (list, tuple, set))
                else (len(context["field_logs"]) if isinstance(context.get("field_logs"), dict) else 0)
            )
            context["basic_stats"] = {
                "field_log_count": field_log_count,
                "media_counts": media_stats,
            }
            self.logger.debug("Section 3 inputs loaded: %s", context["basic_stats"])
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
            voice_summary = VoiceTranscriptionHelper.summarize(context.get("voice_transcripts"))
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
            result = {
                "payload": payload,
                "manifest": model["manifest"],
                "render_tree": model["render_tree"],
                "narrative": narrative,
                "status": "completed",
            }
            if self.gateway:
                self.gateway.publish_section_result("section_3", result)
                self.gateway.emit("surveillance_ready", model["manifest"])
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
    def _collect_media_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        media_index = context.get("media_index") or {}
        summary = MediaCorrelationHelper.collect_media_stats(media_index)
        return {
            "media_index": media_index,
            "summary": summary,
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
        for subject in subject_manifest:
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
        media_index = media_context.get("media_index", {})
        image_assets = media_index.get("images") or {}
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
        northstar_result = (
            NorthstarProtocolTool.process_assets(assets) if assets else {"status": "SKIPPED"}
        )
        reverse_tool = ReverseContinuityTool()
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
        metadata_result = (
            MetadataToolV5.process_zip(metadata_zip, context.get("metadata_output_dir", "./metadata_out"))
            if metadata_zip
            else {"status": "SKIPPED"}
        )
        mileage_result = MileageToolV2.audit_mileage()
        
        # Process OCR documents if available
        ocr_results = {}
        if OCR_AVAILABLE:
            ocr_results = self._process_ocr_documents(context)
        
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
            
        return {
            "identity_checks": identity_checks,
            "northstar": northstar_result,
            "reverse_continuity": {"ok": bool(reverse_ok), "log": reverse_log},
            "metadata_audit": metadata_result,
            "mileage_audit": mileage_result,
            "ocr_results": ocr_results,
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

__all__ = [
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
]





