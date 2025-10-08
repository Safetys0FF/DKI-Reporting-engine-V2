"""Framework template for Section 4 (Review of Surveillance Sessions)."""

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

class Section4Renderer:
    """
    Handles Section 4: Review of Surveillance Sessions
    - Courtroom-ready evidentiary summary
    - Requires visual confirmation, time anchors, and narrative sourcing
    - Supports Investigative, Surveillance, and Hybrid switch states
    - Implements 3x fallback pass across 4 data zones
    - Always hands off to Gateway after completion
    """

    SECTION_KEY = "section_4"
    TITLE = "SECTION 4 â€“ REVIEW OF SURVEILLANCE SESSIONS"

    WHITELIST_FIELDS = [
        "surveillance_date", "time_blocks", "locations", "subject_confirmed",
        "observed_behavior", "subject_interactions", "visual_evidence",
        "deviations_noted", "closure_status",
        "voice_memos"
    ]

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
        Performs 3x cyclical validation over:
        - Intake, Notes, Evidence, Prior Section Output
        Returns first found or None after exhaustion
        """
        for _ in range(3):
            for zone in ["intake", "notes", "evidence", "prior_section"]:
                val = zones.get(zone, {}).get(key)
                if val:
                    return val
        return None

    def _to_dt(self, ts):
        if not ts:
            return None
        try:
            return datetime.fromisoformat(str(ts).replace('T', ' '))
        except Exception:
            return None

    def _extract_time_windows(self, text):
        windows = []
        if not text:
            return windows
        pat = re.compile(r"(\d{4}-\d{2}-\d{2})\s+(\d{1,2}:\d{2})(?:\s*[-to]{1,3}\s*)(\d{1,2}:\d{2})")
        for m in pat.finditer(str(text)):
            day, s1, s2 = m.group(1), m.group(2), m.group(3)
            try:
                start = datetime.fromisoformat(f"{day} {s1}:00")
                end = datetime.fromisoformat(f"{day} {s2}:00")
                if end > start:
                    windows.append((start, end))
            except Exception:
                continue
        return windows

    def _media_timestamp(self, data):
        ts = (data or {}).get('processing_timestamp')
        if ts:
            return ts
        exif = (data or {}).get('exif') or {}
        for k in ('DateTimeOriginal', 'DateTime'):
            if exif.get(k):
                try:
                    t = exif[k].replace(':', '-', 2)
                    datetime.fromisoformat(t)
                    return t
                except Exception:
                    continue
        return None

    def _build_internal_sidebar(self, payload):
        windows = []
        # Prefer explicit time_blocks field if present
        if payload.get('time_blocks'):
            windows.extend(self._extract_time_windows(payload.get('time_blocks')))
        for key in ('observed_behavior', 'visual_evidence'):
            if payload.get(key):
                windows.extend(self._extract_time_windows(payload.get(key)))
        images = (payload.get('images') or {}).items()
        videos = (payload.get('videos') or {}).items()
        refs = []
        for start, end in windows:
            matched = []
            for mid, md in list(images) + list(videos):
                ts = self._media_timestamp(md)
                dt = self._to_dt(ts)
                if dt and start <= dt <= end:
                    matched.append({
                        'id': mid,
                        'kind': 'video' if (mid in (payload.get('videos') or {})) else 'image',
                        'captured_at': dt.isoformat(),
                    })
            refs.append({
                'window_start': start.isoformat(),
                'window_end': end.isoformat(),
                'matched_media': matched,
            })
        return {
            'windows': refs,
            'counts': {
                'windows': len(windows),
                'images': len(images),
                'videos': len(videos),
                'matches': sum(len(r['matched_media']) for r in refs),
            },
            'policies': payload.get('data_policies', {}),
        }

    def _format_voice_memos(self, memos):
        if not memos:
            placeholder = self.PLACEHOLDERS["unknown"]
            return placeholder, True

        entries = []
        if isinstance(memos, dict):
            memos = memos.values()
        for idx, memo in enumerate(memos, 1):
            if not isinstance(memo, dict):
                continue
            name = memo.get('name') or f'Voice Memo {idx}'
            summary = memo.get('summary') or memo.get('text') or memo.get('transcript')
            if not summary:
                continue
            language = memo.get('language')
            duration = memo.get('duration')
            entry = f"{idx}. {name}: {summary.strip()}"
            if language:
                entry += f" (Language: {language})"
            if duration:
                entry += f" [Duration: {duration}]"
            entries.append(entry)

        if not entries:
            placeholder = self.PLACEHOLDERS["unknown"]
            return placeholder, True

        formatted = '\n'.join(entries)
        return formatted, False

    def render_model(self, section_payload, case_sources):
        rendered_blocks = []
        drift_bounced = {}
        placeholders_used = {}

        # Use contract-based title
        title = section_payload.get("section_heading", self.TITLE)
        rendered_blocks.append({
            "type": "title",
            "text": title,
            "style": self.STYLE_RULES["section_title"]
        })

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
                                  if f not in ["visual_evidence", "subject_confirmed", "deviations_noted"]]
            elif report_type == "Hybrid":
                fields_to_render = self.WHITELIST_FIELDS  # All fields for hybrid
            else:  # Surveillance
                fields_to_render = self.WHITELIST_FIELDS

        # Apply hide effects from contract config
        if contract_config.get("effects", {}).get("hide"):
            hidden_fields = contract_config["effects"]["hide"]
            fields_to_render = [f for f in fields_to_render if f not in hidden_fields]

        for key in fields_to_render:
            if key == 'voice_memos':
                value, is_ph = self._format_voice_memos(section_payload.get('voice_memos'))
            else:
                val = section_payload.get(key)
                if not val:
                    val = self._fallback_check(key, case_sources)

                value, is_ph = self._placeholder_for(key, self._normalize(val))

            if is_ph:
                placeholders_used[key] = value

            rendered_blocks.append({
                "type": "field",
                "label": key.replace("_", " " ).title(),
                "value": value,
                "style": self.STYLE_RULES["placeholder_value"] if is_ph else self.STYLE_RULES["field_value"]
            })

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
            'voice_memos': section_payload.get('voice_memos', []),
            "contract_config": contract_config,
            "report_type": report_type,
            # Internal-only media cross-reference sidebar (not client-facing)
            "internal_sidebar": self._build_internal_sidebar(section_payload)
        }

        return {
            "render_tree": rendered_blocks,
            "manifest": manifest,
            "handoff": "gateway"
        }


INVESTIGATIVE_HEADING = "SECTION 4 - INVESTIGATION FINDINGS"
FIELD_HEADING = "SECTION 4 - REVIEW OF SURVEILLANCE SESSIONS"
HYBRID_HEADING = "SECTION 4 - INVESTIGATION FINDINGS & FIELD REVIEW"
HYBRID_FIELD_SEGMENT_LABEL = "FIELD VERIFICATION (PHASE 2)"
INVESTIGATIVE_NOTE = "Investigative findings summarized for court-ready presentation."
NO_FIELD_MESSAGE = "Due to the nature of this case no surveillance field operations were performed."
NO_CONFIRM_MESSAGE = "Subject was not visually confirmed during the reviewed window."
NO_DEVIATION_MESSAGE = "No deviations from planned operations were observed."
DEFAULT_CLOSURE_MESSAGE = "Session concluded within authorized parameters."
BILLING_CATEGORIES = (
    "drive_to",
    "field_operation_time",
    "surveillance_engagement",
    "mobile_drive",
    "drive_from",
)


# === Enhanced Contract-Based Report Logic ===
def get_report_config(contract_history):
    """Enhanced contract analysis with Section 4-specific configurations"""
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
    
    # Section 4-specific report configurations
    report_configs = {
        "Investigative": {
            "label": "SECTION 4 - INVESTIGATION FINDINGS",
            "billing": "Flat",
            "clause": "investigation_only",
            "modules": {
                "active": ["investigation_findings", "document_analysis"],
                "inactive": ["surveillance_sessions", "visual_evidence", "field_verification"]
            },
            "effects": {
                "hide": ["visual_evidence", "subject_confirmed", "deviations_noted"],
                "tag": "Investigation Analysis"
            }
        },
        "Surveillance": {
            "label": "SECTION 4 - REVIEW OF SURVEILLANCE SESSIONS", 
            "billing": "Hourly",
            "clause": "field_verification",
            "modules": {
                "active": ["surveillance_sessions", "visual_evidence", "subject_verification"],
                "inactive": ["investigation_findings", "document_analysis"]
            },
            "effects": {
                "render_all": True,
                "tag": "Field Review Ready"
            }
        },
        "Hybrid": {
            "label": "SECTION 4 - INVESTIGATION FINDINGS & FIELD REVIEW",
            "billing": "Hybrid", 
            "clause": "mixed_analysis",
            "modules": {
                "active": ["investigation_findings", "surveillance_sessions", "visual_evidence", "subject_verification"],
                "inactive": []
            },
            "effects": {
                "forced_render_order": ["investigation_segment", "field_verification"],
                "contract_order_required": True,
                "tag": "Full Analysis Stack"
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

class Section4Framework(SectionFramework):
    SECTION_ID = "section_4_review"
    BUS_SECTION_ID = "section_4"
    MAX_RERUNS = 2
    STAGES = (
        StageDefinition(
            name="intake",
            description="Pull gateway bundle, confirm upstream hashes, and load toolkit continuity outputs.",
            checkpoint="s4_intake_logged",
            guardrails=("order_lock", "async_queue", "persistence_snapshot"),
            inputs=("case_metadata", "planning_manifest", "surveillance_manifest"),
            outputs=("intake_context",),
        ),
        StageDefinition(
            name="analyze",
            description="Map surveillance entries to objectives, generate narratives, and link evidence.",
            checkpoint="s4_analysis_complete",
            guardrails=("schema_validation", "fact_alignment", "north_star"),
            inputs=("surveillance_manifest", "planning_manifest", "media_index"),
            outputs=("analysis_manifest",),
        ),
        StageDefinition(
            name="validate",
            description="Apply continuity checks, speculation filters, and QA policy enforcement.",
            checkpoint="s4_validated",
            guardrails=("manual_queue_routes", "risk_threshold", "immutability_precheck"),
            inputs=("analysis_manifest",),
            outputs=("validated_manifest",),
        ),
        StageDefinition(
            name="publish",
            description="Publish narrative payload, emit session review signal, and persist provenance.",
            checkpoint="section_4_completed",
            guardrails=("durable_persistence", "signal_emission", "immutability"),
            inputs=("validated_manifest",),
            outputs=("gateway_handoff",),
        ),
        StageDefinition(
            name="monitor",
            description="Handle revision requests while enforcing rerun guardrails.",
            checkpoint="s4_revision_processed",
            guardrails=("max_reruns", "revision_depth_cap", "fact_graph_consistency"),
        ),
    )
    COMMUNICATION = CommunicationContract(
        prepare_signal="section_3_logs.completed",
        input_channels=(
            "case_metadata",
            "planning_manifest",
            "surveillance_manifest",
            "media_index",
            "toolkit_results",
            "voice_transcripts",
            "analysis_notes",
            "manual_annotations",
        ),
        output_signal="section_4_review.completed",
        revision_signal="session_review_revision",
    )
    ORDER = OrderContract(
        execution_after=("section_3_logs", "section_2_planning", "section_1_profile", "section_cp"),
        export_after=("section_7", "section_fr"),
        export_priority=40,
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
        return section_id or "section_4"

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


    def __init__(self, gateway: Any, ecc: Optional[Any] = None) -> None:
        super().__init__(gateway=gateway, ecc=ecc)
        self._last_context: Dict[str, Any] = {}

    def load_inputs(self) -> Dict[str, Any]:
        try:
            self._guard_execution("input loading")
            bundle = self.gateway.get_section_inputs("section_4") if self.gateway else {}
            context = {
                "raw_inputs": bundle,
                "case_metadata": bundle.get("case_metadata", {}),
                "planning_manifest": bundle.get("planning_manifest", {}),
                "surveillance_manifest": bundle.get("surveillance_manifest", {}),
                "media_index": bundle.get("media_index", {}),
                "toolkit_results": bundle.get("toolkit_results", {}),
                "voice_transcripts": bundle.get("voice_transcripts", []),
                "analysis_notes": bundle.get("analysis_notes", []),
                "manual_annotations": bundle.get("manual_annotations", []),
                "media_bundle_zip": bundle.get("media_bundle_zip"),
            }
            sessions = context.get("surveillance_manifest", {}).get("sessions") or []
            if isinstance(sessions, dict):
                session_count = len(sessions)
            else:
                session_count = len(sessions)
            media_stats = MediaCorrelationHelper.collect_media_stats(context.get("media_index", {}))
            context["basic_stats"] = {
                "session_count": session_count,
                "media_counts": media_stats,
            }
            context = self._augment_with_bus_context(context)
            self.logger.debug("Section 4 inputs loaded: %s", context["basic_stats"])
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
                    active_components = ["investigation_findings", "document_analysis"]
                elif report_type == "Hybrid":
                    active_components = ["investigation_findings", "surveillance_sessions", "visual_evidence", "subject_verification"]
                else:  # Surveillance
                    active_components = ["surveillance_sessions", "visual_evidence", "subject_verification"]
            
            # Apply hide effects from contract config
            if config.get("effects", {}).get("hide"):
                hidden_components = config["effects"]["hide"]
                active_components = [c for c in active_components if c not in hidden_components]
            
            case_mode = self._determine_case_mode(context)
            requires_surveillance = case_mode in {"field", "hybrid"}
            media_context = self._collect_media_context(context)
            session_fields, session_meta = self._build_session_fields(context, case_mode, media_context["summary"])
            voice_summary = VoiceTranscriptionHelper.summarize(context.get("voice_transcripts"))
            billing = self._build_billing(context, case_mode, session_meta, requires_surveillance)
            notes = self._compose_notes(case_mode, context, session_meta, requires_surveillance)
            tool_results = self._run_inline_tools(context, requires_surveillance, media_context, session_fields)
            qa_flags = set(session_meta.get("qa_flags", []))
            qa_flags.update(tool_results.get("qa_flags", []))
            subjects_in_scope = {
                str(item).strip()
                for item in session_meta.get("subjects_in_scope", [])
                if item is not None and str(item).strip()
            }
            
            # Use contract-based section heading
            section_heading = config.get("label", self._case_heading(case_mode))
            
            payload: Dict[str, Any] = {
                "section_heading": section_heading,
                "report_type": report_type,
                "whitelist_applied": whitelist,
                "contract_config": config,
                **session_fields,
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
                "hybrid_segment_label": session_meta.get("hybrid_field_label"),
                "active_components": active_components,
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
            renderer = Section4Renderer()
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
                "source": "section_4_framework",
            }
            if self.gateway:
                self.gateway.publish_section_result(section_bus_id, result)
                emit_payload = dict(result)
                emit_payload.setdefault("published_at", timestamp)
                if self.COMMUNICATION and self.COMMUNICATION.output_signal:
                    self.gateway.emit(self.COMMUNICATION.output_signal, emit_payload)
                self.gateway.emit("session_review_ready", model["manifest"])
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
        contracts = case_meta.get("contracts") or planning.get("contracts") or []
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

    def _collect_session_sources(self, context: Dict[str, Any]) -> Dict[str, Any]:
        manifest = context.get("surveillance_manifest") or {}
        sessions = manifest.get("sessions") or manifest.get("logs") or []
        if isinstance(sessions, dict):
            sessions = list(sessions.values())
        planning = context.get("planning_manifest", {})
        toolkit = context.get("toolkit_results", {})
        investigative_findings = (
            planning.get("investigative_findings")
            or toolkit.get("investigative_findings")
            or []
        )
        continuity_notes = (
            toolkit.get("continuity")
            or manifest.get("continuity_notes")
            or []
        )
        return {
            "sessions": sessions,
            "session_summary": manifest.get("summary") or manifest.get("narrative"),
            "investigative_findings": investigative_findings,
            "continuity_notes": continuity_notes,
            "analysis_notes": context.get("analysis_notes") or manifest.get("analysis_notes") or [],
            "manual_annotations": context.get("manual_annotations") or [],
        }

        def _build_session_fields(
            self,
            context: Dict[str, Any],
            case_mode: str,
            media_summary: Dict[str, Any],
        ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
            sources = self._collect_session_sources(context)
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
            time_blocks: List[str] = []
            locations: List[str] = []
            behaviors: List[str] = []
            interactions: List[str] = []
            deviations: List[str] = []
            qa_flags: List[str] = []
            subjects_in_scope: List[str] = []
            closure = None
            for idx, finding in enumerate(findings, 1):
                if isinstance(finding, dict):
                    day = self._first_nonempty(finding.get("date"), finding.get("observed_date"))
                    if day:
                        date_lines.append(f"Event Entry {idx}: {day}")
                    window = self._first_nonempty(finding.get("time_window"), finding.get("time"))
                    if window and day:
                        time_blocks.append(f"{day} - {window}")
                    elif window:
                        time_blocks.append(window)
                    location = self._first_nonempty(finding.get("location"), finding.get("address"))
                    if location:
                        locations.append(location)
                    summary = self._first_nonempty(finding.get("summary"), finding.get("finding"))
                    if summary:
                        behaviors.append(summary)
                    interaction = finding.get("interaction")
                    if interaction:
                        interactions.append(str(interaction))
                    deviation = finding.get("deviation")
                    if deviation:
                        deviations.append(str(deviation))
                    subject = finding.get("subject") or finding.get("person")
                    if subject:
                        subjects_in_scope.append(str(subject))
                    closure = closure or finding.get("closure")
                else:
                    text = str(finding)
                    date_lines.append(f"Event Entry {idx}: Investigative detail documented")
                    behaviors.append(text)
            if not behaviors:
                qa_flags.append("investigative_findings_missing")
            fields = {
                "surveillance_date": self._safe_join(date_lines, default="Investigative findings under review."),
                "time_blocks": self._safe_join(time_blocks, default="Investigative timeline validation pending."),
                "locations": self._safe_join(locations, default="Locations documented in investigative record."),
                "subject_confirmed": self._safe_join(subjects_in_scope, default="Investigative leads pending confirmation."),
                "observed_behavior": self._safe_join(behaviors, default="Investigative findings to be finalized."),
                "subject_interactions": self._safe_join(interactions, default="No direct interactions recorded."),
                "visual_evidence": "Investigative mode active; field evidence suppressed.",
                "deviations_noted": self._safe_join(deviations, default="No deviations recorded in investigative phase."),
                "closure_status": closure or "Investigative review ongoing.",
                "voice_memos": [],
            }
            meta = {
                "qa_flags": qa_flags,
                "subjects_in_scope": subjects_in_scope,
                "notes": [INVESTIGATIVE_NOTE],
            }
            return fields, meta

        def _build_field_fields(
            self,
            context: Dict[str, Any],
            sources: Dict[str, Any],
            media_summary: Dict[str, Any],
            hybrid: bool,
        ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
            sessions = sources.get("sessions") or []
            date_lines: List[str] = []
            time_lines: List[str] = []
            location_lines: List[str] = []
            behavior_lines: List[str] = []
            interaction_lines: List[str] = []
            deviation_lines: List[str] = []
            qa_flags: List[str] = []
            subjects_in_scope: List[str] = []
            closure = None
            subject_confirmed_entries: List[str] = []
            duration_map = {key: 0.0 for key in BILLING_CATEGORIES}
            for idx, session in enumerate(sessions, 1):
                if not isinstance(session, dict):
                    continue
                date_val = self._first_nonempty(session.get("date"), session.get("session_date"))
                if date_val:
                    prefix = HYBRID_FIELD_SEGMENT_LABEL + ": " if hybrid else "Session: "
                    date_lines.append(f"{prefix}{date_val}")
                time_window = self._first_nonempty(
                    session.get("time_window"),
                    session.get("time_block"),
                    session.get("start_time"),
                )
                if time_window:
                    time_lines.append(f"{date_val or 'Session'} - {time_window}")
                location = self._first_nonempty(
                    session.get("location"),
                    session.get("address"),
                    session.get("area"),
                )
                if location:
                    location_lines.append(location)
                subject_flag = session.get("subject_confirmed")
                subject_name = self._first_nonempty(" ".join(session.get("subject_names", [])), session.get("subject"))
                if subject_flag or subject_name:
                    entry = subject_name or ("Subject visually confirmed" if subject_flag else NO_CONFIRM_MESSAGE)
                    subject_confirmed_entries.append(entry)
                    if subject_name:
                        subjects_in_scope.append(subject_name)
                observations = session.get("observations") or session.get("activities") or []
                if isinstance(observations, dict):
                    observations = list(observations.values())
                for obs in observations:
                    if isinstance(obs, dict):
                        timestamp = self._first_nonempty(obs.get("time"), obs.get("timestamp"))
                        description = self._first_nonempty(
                            obs.get("description"),
                            obs.get("activity"),
                            obs.get("summary"),
                        )
                        if description and timestamp:
                            behavior_lines.append(f"{timestamp} - {description}")
                        elif description:
                            behavior_lines.append(description)
                        interaction = obs.get("interaction")
                        if interaction:
                            interaction_lines.append(str(interaction))
                        deviation = obs.get("deviation") or obs.get("variance")
                        if deviation:
                            deviation_lines.append(str(deviation))
                        subject = obs.get("subject") or obs.get("person")
                        if subject:
                            subjects_in_scope.append(str(subject))
                        duration = obs.get("duration_minutes") or obs.get("minutes")
                        category = (obs.get("category") or "").lower()
                        if isinstance(duration, (int, float)):
                            for key in BILLING_CATEGORIES:
                                normalized_key = key.replace("_", " ")
                                if normalized_key in category or key in category:
                                    duration_map[key] += float(duration)
                                    break
                    else:
                        behavior_lines.append(str(obs))
                closure = closure or session.get("closure") or session.get("status")
            if not behavior_lines:
                qa_flags.append("field_sessions_missing")
            if not subject_confirmed_entries and not hybrid:
                subject_confirmed_entries.append(NO_CONFIRM_MESSAGE)
            visual_evidence = f"Images: {media_summary.get('images', 0)} | Videos: {media_summary.get('videos', 0)}"
            fields = {
                "surveillance_date": self._safe_join(date_lines, default="Field operations pending."),
                "time_blocks": self._safe_join(time_lines, default="Timeline will finalize after QA."),
                "locations": self._safe_join(location_lines, default="Location details pending confirmation."),
                "subject_confirmed": self._safe_join(subject_confirmed_entries, default=NO_CONFIRM_MESSAGE),
                "observed_behavior": self._safe_join(behavior_lines, default="No behaviors recorded during this window."),
                "subject_interactions": self._safe_join(interaction_lines, default="No direct interactions observed."),
                "visual_evidence": visual_evidence,
                "deviations_noted": self._safe_join(deviation_lines, default=NO_DEVIATION_MESSAGE),
                "closure_status": closure or DEFAULT_CLOSURE_MESSAGE,
                "voice_memos": [],
            }
            meta = {
                "qa_flags": qa_flags,
                "subjects_in_scope": subjects_in_scope,
                "duration_map": duration_map,
                "notes": sources.get("analysis_notes") or [],
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
            combined_fields["surveillance_date"] = self._safe_join(
                [investigative_fields["surveillance_date"], field_fields["surveillance_date"]],
                default=field_fields["surveillance_date"],
                separator="\n\n",
            )
            combined_fields["time_blocks"] = self._safe_join(
                [investigative_fields["time_blocks"], field_fields["time_blocks"]],
                default=field_fields["time_blocks"],
                separator="\n\n",
            )
            combined_fields["observed_behavior"] = self._safe_join(
                [investigative_fields["observed_behavior"], field_fields["observed_behavior"]],
                default=field_fields["observed_behavior"],
                separator="\n\n",
            )
            combined_fields["subject_interactions"] = self._safe_join(
                [investigative_fields["subject_interactions"], field_fields["subject_interactions"]],
                default=field_fields["subject_interactions"],
                separator="\n",
            )
            combined_fields["deviations_noted"] = self._safe_join(
                [investigative_fields["deviations_noted"], field_fields["deviations_noted"]],
                default=field_fields["deviations_noted"],
                separator="\n",
            )
            combined_meta = {
                "qa_flags": [],
                "subjects_in_scope": [],
                "duration_map": field_meta.get("duration_map", {}),
                "notes": [HYBRID_FIELD_SEGMENT_LABEL],
                "hybrid_field_label": HYBRID_FIELD_SEGMENT_LABEL,
            }
            combined_meta["qa_flags"].extend(investigative_meta.get("qa_flags", []))
            combined_meta["qa_flags"].extend(field_meta.get("qa_flags", []))
            combined_meta["subjects_in_scope"].extend(investigative_meta.get("subjects_in_scope", []))
            combined_meta["subjects_in_scope"].extend(field_meta.get("subjects_in_scope", []))
            combined_meta["notes"].extend(investigative_meta.get("notes", []))
            combined_meta["notes"].extend(field_meta.get("notes", []))
            return combined_fields, combined_meta

        def _build_billing(
            self,
            context: Dict[str, Any],
            case_mode: str,
            session_meta: Dict[str, Any],
            requires_surveillance: bool,
        ) -> Dict[str, Any]:
            toolkit_billing = context.get("toolkit_results", {}).get("billing", {})
            categories = {key: float(toolkit_billing.get(key, 0)) for key in BILLING_CATEGORIES}
            notes = list(toolkit_billing.get("notes", []))
            if requires_surveillance and not any(categories.values()):
                duration_map = session_meta.get("duration_map", {})
                for key in BILLING_CATEGORIES:
                    if key in duration_map:
                        categories[key] = float(duration_map[key])
            if not requires_surveillance:
                notes.append("Investigative mode: field billing suppressed.")
            model = toolkit_billing.get("model") or ("hybrid" if case_mode == "hybrid" else ("field" if requires_surveillance else "investigative"))
            return {
                "model": model,
                "categories": categories,
                "notes": notes,
            }

        def _compose_notes(
            self,
            case_mode: str,
            context: Dict[str, Any],
            session_meta: Dict[str, Any],
            requires_surveillance: bool,
        ) -> str:
            notes: List[str] = []
            notes.extend(session_meta.get("notes", []))
            continuity_notes = context.get("toolkit_results", {}).get("continuity") or []
            if isinstance(continuity_notes, str):
                continuity_notes = [continuity_notes]
            notes.extend(str(n).strip() for n in continuity_notes if str(n).strip())
            manual_entries = context.get("manual_annotations", [])
            notes.extend(str(item).strip() for item in manual_entries if str(item).strip())
            if case_mode == "hybrid":
                notes.insert(0, "Hybrid case: Investigative findings triggered field verification.")
            if not requires_surveillance:
                notes.append(NO_FIELD_MESSAGE)
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
            surveillance = context.get("surveillance_manifest", {})
            
            # PDF documents
            pdf_docs = (planning.get("pdf_documents", []) or 
                       case_meta.get("pdf_documents", []) or 
                       surveillance.get("pdf_documents", []))
            for pdf_path in pdf_docs:
                if os.path.exists(pdf_path):
                    try:
                        text = extract_text_from_pdf(pdf_path)
                        ocr_results[f"pdf_{os.path.basename(pdf_path)}"] = text
                    except Exception as e:
                        ocr_results[f"pdf_{os.path.basename(pdf_path)}"] = f"PDF extraction failed: {str(e)}"
            
            # Image documents
            img_docs = (planning.get("image_documents", []) or 
                       case_meta.get("image_documents", []) or 
                       surveillance.get("image_documents", []))
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
            session_fields: Dict[str, Any],
        ) -> Dict[str, Any]:
            subject_manifest = context.get("planning_manifest", {}).get("subjects") or context.get("case_metadata", {}).get("subjects") or []
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
                        session_fields.get("surveillance_date"),
                        session_fields.get("time_blocks"),
                        session_fields.get("observed_behavior"),
                        session_fields.get("deviations_noted"),
                    ],
                )
            )
            sessions = self._collect_session_sources(context).get("sessions") or []
            session_docs: List[str] = []
            for entry in sessions:
                try:
                    session_docs.append(json.dumps(entry, default=str))
                except TypeError:
                    session_docs.append(str(entry))
            reverse_ok, reverse_log = reverse_tool.run_validation(
                text_blob,
                session_docs,
                [json.dumps(meta, default=str) for meta in image_assets.values()],
            )
            metadata_zip = context.get("surveillance_manifest", {}).get("metadata_zip") or context.get("media_bundle_zip")
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
            surveillance = context.get("surveillance_manifest", {})
            field_logs = surveillance.get("sessions") or surveillance.get("logs") or []
            if isinstance(field_logs, dict):
                field_logs = list(field_logs.values())
            fallback_notes = {
                "observed_behavior": "\n".join(
                    filter(None, (str(entry.get("summary")) for entry in field_logs if isinstance(entry, dict)))
                )
            }
            return {
                "intake": context.get("case_metadata", {}),
                "notes": planning.get("investigator_notes", fallback_notes),
                "evidence": context.get("media_index", {}),
                "prior_section": surveillance,
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
    "Section4Framework",
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

