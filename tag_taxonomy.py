"""Evidence tag taxonomy shared across Central Command components.

Provides helper utilities so the GUI, Evidence Locker, SectionBusAdapter,
and Gateway can agree on normalized tags and their section affinities.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple


@dataclass(frozen=True)
class TagProfile:
    """Describes the canonical mapping between a tag category and sections."""

    slug: str
    label: str
    tags: Tuple[str, ...]
    aliases: Tuple[str, ...]
    primary_section: Optional[str]
    related_sections: Tuple[str, ...]

    def all_keywords(self) -> Set[str]:
        values: Set[str] = {self.slug}
        values.update(self.tags)
        values.update(self.aliases)
        return {normalize_tag(value) for value in values if value}


TAG_TAXONOMY: Dict[str, TagProfile] = {
    "intake": TagProfile(
        slug="intake",
        label="Client Intake",
        tags=("intake", "intake_form", "client_data"),
        aliases=("#intake", "#intakeform", "intakeform", "client-intake", "subject-intake"),
        primary_section="section_1",
        related_sections=("section_5", "section_7"),
    ),
    "background": TagProfile(
        slug="background",
        label="Background Brief",
        tags=("background", "profile", "osint"),
        aliases=("#background", "#profile", "due_diligence", "open_source"),
        primary_section="section_1",
        related_sections=("section_2", "section_4", "section_5", "section_7"),
    ),
    "contract": TagProfile(
        slug="contract",
        label="Contracts & Agreements",
        tags=("contract", "agreement", "retainer"),
        aliases=("#contract", "#agreement", "#retainer", "sow", "engagement"),
        primary_section="section_5",
        related_sections=("section_1", "section_6"),
    ),
    "billing": TagProfile(
        slug="billing",
        label="Billing & Expenses",
        tags=("billing", "expense", "mileage"),
        aliases=("#billing", "#expense", "#mileage", "accounts_receivable"),
        primary_section="section_6",
        related_sections=("section_5", "section_7"),
    ),
    "field_notes": TagProfile(
        slug="field_notes",
        label="Field Notes",
        tags=("field_notes", "surveillance", "observation"),
        aliases=("#fieldnotes", "#surveillance", "shift_log", "daily_log"),
        primary_section="section_3",
        related_sections=("section_4", "section_6"),
    ),
    "data_report": TagProfile(
        slug="data_report",
        label="Data / Analytics",
        tags=("data_report", "analysis", "open_records"),
        aliases=("#analytics", "#data", "openrecords", "dataset"),
        primary_section="section_4",
        related_sections=("section_3", "section_7"),
    ),
    "communication": TagProfile(
        slug="communication",
        label="Communications",
        tags=("communication", "correspondence"),
        aliases=("#communication", "#email", "#text", "sms", "imessage"),
        primary_section="section_5",
        related_sections=("section_3", "section_6"),
    ),
    "media_photo": TagProfile(
        slug="media_photo",
        label="Photo Evidence",
        tags=("media", "photo", "image"),
        aliases=("#photo", "#image", "photograph"),
        primary_section="section_8",
        related_sections=("section_2", "section_6", "section_7"),
    ),
    "media_video": TagProfile(
        slug="media_video",
        label="Video Evidence",
        tags=("media", "video", "surveillance"),
        aliases=("#video", "#surveillance", "footage"),
        primary_section="section_8",
        related_sections=("section_2", "section_3", "section_6", "section_7"),
    ),
    "media_audio": TagProfile(
        slug="media_audio",
        label="Audio Evidence",
        tags=("media", "audio", "recording"),
        aliases=("#audio", "#recording", "voice_note"),
        primary_section="section_3",
        related_sections=("section_6",),
    ),
    "geo": TagProfile(
        slug="geo",
        label="Geospatial",
        tags=("geo", "map", "location"),
        aliases=("#geo", "#map", "#location", "kml", "gps"),
        primary_section="section_2",
        related_sections=("section_3", "section_8", "section_6"),
    ),
    "disclosure": TagProfile(
        slug="disclosure",
        label="Disclosure / Compliance",
        tags=("disclosure", "compliance"),
        aliases=("#disclosure", "#compliance"),
        primary_section="section_dp",
        related_sections=("section_5",),
    ),
    "uncategorized": TagProfile(
        slug="uncategorized",
        label="Uncategorized",
        tags=("uncategorized",),
        aliases=("#uncategorized", "other"),
        primary_section="section_cp",
        related_sections=("section_5",),
    ),
}


EXTENSION_DEFAULT_CATEGORIES: Dict[str, str] = {
    ".csv": "billing",
    ".tsv": "billing",
    ".xls": "billing",
    ".xlsx": "billing",
    ".pdf": "contract",
    ".doc": "contract",
    ".docx": "contract",
    ".rtf": "contract",
    ".txt": "field_notes",
    ".rtfd": "field_notes",
    ".json": "data_report",
    ".xml": "data_report",
    ".jpg": "media_photo",
    ".jpeg": "media_photo",
    ".png": "media_photo",
    ".gif": "media_photo",
    ".bmp": "media_photo",
    ".tif": "media_photo",
    ".tiff": "media_photo",
    ".heic": "media_photo",
    ".webp": "media_photo",
    ".mp4": "media_video",
    ".mov": "media_video",
    ".avi": "media_video",
    ".wmv": "media_video",
    ".mkv": "media_video",
    ".m4v": "media_video",
    ".mp3": "media_audio",
    ".wav": "media_audio",
    ".m4a": "media_audio",
    ".aac": "media_audio",
    ".kml": "geo",
    ".kmz": "geo",
    ".gpx": "geo",
    ".shp": "geo",
}


def normalize_tag(value: Optional[str]) -> str:
    if not value:
        return ""
    normalized = value.strip().lower()
    if normalized.startswith("#"):
        normalized = normalized[1:]
    normalized = normalized.replace(" ", "_").replace("-", "_")
    while "__" in normalized:
        normalized = normalized.replace("__", "_")
    return normalized.strip("_")


def _lookup_category(candidate: Optional[str], tags: Iterable[str]) -> Optional[TagProfile]:
    normalized_candidate = normalize_tag(candidate)
    if normalized_candidate and normalized_candidate in TAG_TAXONOMY:
        return TAG_TAXONOMY[normalized_candidate]
    for profile in TAG_TAXONOMY.values():
        if normalized_candidate and normalized_candidate in profile.all_keywords():
            return profile
    normalized_tags = {normalize_tag(tag) for tag in tags if tag}
    for profile in TAG_TAXONOMY.values():
        if normalized_tags.intersection(profile.all_keywords()):
            return profile
    return None


def resolve_tags(
    *,
    category: Optional[str] = None,
    tags: Optional[Iterable[str]] = None,
    file_path: Optional[str] = None,
) -> Dict[str, Optional[object]]:
    """Return normalized tags and section hints derived from inputs."""

    tags = list(tags or [])
    profile = _lookup_category(category, tags)

    if not profile and file_path:
        ext = Path(file_path).suffix.lower()
        auto_category = EXTENSION_DEFAULT_CATEGORIES.get(ext)
        if auto_category:
            profile = TAG_TAXONOMY.get(auto_category)

    normalized_tags: List[str] = []
    for tag in tags:
        norm = normalize_tag(tag)
        if norm:
            normalized_tags.append(norm)

    if profile:
        for tag in profile.tags:
            norm = normalize_tag(tag)
            if norm:
                normalized_tags.append(norm)

    # Preserve order while removing duplicates.
    seen: Set[str] = set()
    ordered: List[str] = []
    for entry in normalized_tags:
        if entry and entry not in seen:
            seen.add(entry)
            ordered.append(entry)

    return {
        "category": profile.slug if profile else normalize_tag(category) or None,
        "tags": ordered,
        "primary_section": profile.primary_section if profile else None,
        "related_sections": list(profile.related_sections) if profile else [],
    }


def candidate_categories_from_tags(tags: Iterable[str]) -> List[str]:
    normalized = {normalize_tag(tag) for tag in tags if tag}
    matches: List[str] = []
    for slug, profile in TAG_TAXONOMY.items():
        if normalized.intersection(profile.all_keywords()):
            matches.append(slug)
    return matches or (["uncategorized"] if normalized else [])


__all__ = [
    "TAG_TAXONOMY",
    "EXTENSION_DEFAULT_CATEGORIES",
    "TagProfile",
    "resolve_tags",
    "normalize_tag",
    "candidate_categories_from_tags",
]
