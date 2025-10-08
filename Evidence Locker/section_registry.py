#!/usr/bin/env python3
"""
Shared section registry and reporting standards for Evidence Locker modules.
Centralizes section metadata to keep ingestion, classification, and export
pipelines aligned with the GatewayController configuration.
"""

from __future__ import annotations

from typing import Dict, List, Any

# Canonical section metadata keyed by gateway section identifier.
SECTION_REGISTRY: Dict[str, Dict[str, Any]] = {
    "section_cp": {
        "title": "Cover Page",
        "category": "front_matter",
        "tags": ["cover-page", "front-matter", "case-profile"],
        "description": "Front matter cover sheet with agency and case metadata.",
        "default_order": 0,
    },
    "section_toc": {
        "title": "Table of Contents",
        "category": "front_matter",
        "tags": ["table-of-contents", "navigation", "index"],
        "description": "Navigational table of contents for generated sections.",
        "default_order": 1,
    },
    "section_1": {
        "title": "Case Objectives & Intake",
        "category": "core",
        "tags": ["intake-form", "client-data", "subject-profile", "background-report", "contract", "subcontractor-agreement", "supporting-documents"],
        "description": "Foundational case briefing, objectives, and subject details.",
        "default_order": 2,
    },
    "section_2": {
        "title": "Requirements & Pre-Surveillance Planning",
        "category": "core",
        "tags": ["background-report", "intake-form", "map", "route-plan", "target-location", "vehicle-id", "subcontractor-agreement", "planning-notes", "supporting-documents"],
        "description": "Planning materials, constraints, and operational requirements.",
        "default_order": 3,
    },
    "section_3": {
        "title": "Daily Surveillance Logs",
        "category": "core",
        "tags": ["surveillance-log", "daily-log", "timeline-entry", "field-notes", "background-report", "media-photo", "media-video", "action-report"],
        "description": "Chronological field activity logs and investigator notes.",
        "default_order": 4,
    },
    "section_4": {
        "title": "Surveillance Session Review",
        "category": "core",
        "tags": ["daily-review", "action-report", "session-review", "chronology", "analysis", "continuity", "surveillance-log", "media-photo", "media-video"],
        "description": "Session level rollups, timing analysis, and continuity checks.",
        "default_order": 5,
    },
    "section_5": {
        "title": "Supporting Documents Review",
        "category": "evidence",
        "tags": ["intake-form", "background-report", "contract", "subcontractor-agreement", "court-filing", "petition", "summons", "affidavit", "receipt", "invoice", "billing-record", "email", "correspondence", "official-record", "supporting-documents"],
        "description": "Corroborating records such as contracts, background reports, and filings.",
        "default_order": 6,
    },
    "section_6": {
        "title": "Billing Summary",
        "category": "financial",
        "tags": ["billing-record", "hours-log", "shift-report", "expense-record", "mileage-log", "invoice", "receipt", "subcontractor-agreement", "subcontractor-invoice", "contract", "supporting-documents", "background-report", "court-filing", "email", "correspondence", "equipment-use", "service-return"],
        "description": "Time and expense summary aligned with investigative activity.",
        "default_order": 7,
    },
    "section_7": {
        "title": "Conclusion & Case Decision",
        "category": "core",
        "tags": ["conclusion", "findings", "decision", "recommendation", "final-summary", "daily-review", "action-report", "background-report"],
        "description": "Investigator findings and case disposition guidance.",
        "default_order": 8,
    },
    "section_8": {
        "title": "Photo & Video Evidence Index",
        "category": "evidence",
        "tags": ["media-photo", "media-video", "screenshot", "surveillance-photo", "surveillance-video", "surveillance-log"],
        "description": "Chronological index of photo, video, and audio surveillance assets.",
        "default_order": 9,
    },
    "section_9": {
        "title": "Certifications & Disclaimers",
        "category": "compliance",
        "tags": ["certification", "disclosure", "authenticity", "signature", "legal", "disclaimer", "supporting-documents", "contract", "subcontractor-agreement"],
        "description": "Jurisdictional disclosures, licensing, and compliance statements.",
        "default_order": 10,
    },
    "section_dp": {
        "title": "Disclosure & Authenticity Page",
        "category": "compliance",
        "tags": ["disclosure", "authenticity", "signature", "compliance"],
        "description": "Investigator certification, authenticity attestations, and quality flags.",
        "default_order": 11,
    },
    "section_fr": {
        "title": "Final Report Assembly",
        "category": "output",
        "tags": ["final-report", "assembly", "export", "packaging"],
        "description": "Final packaging checkpoint prior to export or delivery.",
        "default_order": 12,
    },
}

# Report type ordering mirrors the GatewayController configuration so
# Evidence Locker validation and exports stay synchronized.
REPORTING_STANDARDS: Dict[str, Dict[str, Any]] = {
    "Investigative": {
        "description": "Default investigation report flow used by the gateway controller.",
        "sections": [
            {"id": "section_cp", "title": "Cover Page"},
            {"id": "section_toc", "title": "Table of Contents"},
            {"id": "section_1", "title": "Investigation Objectives"},
            {"id": "section_2", "title": "Investigation Requirements"},
            {"id": "section_3", "title": "Investigation Details"},
            {"id": "section_4", "title": "Review of Details"},
            {"id": "section_5", "title": "Review of Supporting Documents"},
            {"id": "section_6", "title": "Billing Summary"},
            {"id": "section_7", "title": "Conclusion"},
            {"id": "section_8", "title": "Investigation Evidence Review"},
            {"id": "section_9", "title": "Certification & Disclaimers"},
            {"id": "section_dp", "title": "Disclosure Page"},
            {"id": "section_fr", "title": "Final Report Assembly"},
        ],
    },
    "Surveillance": {
        "description": "Surveillance-focused workflow emphasising field activity logs and media evidence.",
        "sections": [
            {"id": "section_cp", "title": "Cover Page"},
            {"id": "section_toc", "title": "Table of Contents"},
            {"id": "section_1", "title": "Surveillance Objectives"},
            {"id": "section_2", "title": "Pre-Surveillance Planning"},
            {"id": "section_3", "title": "Daily Logs"},
            {"id": "section_4", "title": "Review of Surveillance Sessions"},
            {"id": "section_5", "title": "Review of Supporting Documents"},
            {"id": "section_6", "title": "Billing Summary"},
            {"id": "section_7", "title": "Conclusion"},
            {"id": "section_8", "title": "Investigation Evidence Review"},
            {"id": "section_9", "title": "Certification & Disclaimers"},
            {"id": "section_dp", "title": "Disclosure Page"},
            {"id": "section_fr", "title": "Final Report Assembly"},
        ],
    },
    "Hybrid": {
        "description": "Hybrid workflow combining investigative and surveillance reporting elements.",
        "sections": [
            {"id": "section_cp", "title": "Cover Page"},
            {"id": "section_toc", "title": "Table of Contents"},
            {"id": "section_1", "title": "Investigation Objectives"},
            {"id": "section_2", "title": "Preliminary Case Review"},
            {"id": "section_3", "title": "Investigative Details"},
            {"id": "section_4", "title": "Review of Surveillance Sessions"},
            {"id": "section_5", "title": "Review of Supporting Documents"},
            {"id": "section_6", "title": "Billing Summary"},
            {"id": "section_7", "title": "Conclusion"},
            {"id": "section_8", "title": "Investigation Evidence Review"},
            {"id": "section_9", "title": "Certification & Disclaimers"},
            {"id": "section_dp", "title": "Disclosure Page"},
            {"id": "section_fr", "title": "Final Report Assembly"},
        ],
    },
}


__all__ = ["SECTION_REGISTRY", "REPORTING_STANDARDS"]