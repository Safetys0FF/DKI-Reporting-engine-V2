#!/usr/bin/env python3
"""
Shared Interfaces - Standardized communication contracts between Central Command components
Provides consistent data formats and method signatures for NarrativeAssembler, MissionDebriefManager, and ReportGenerator
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum


class SectionStatus(Enum):
    """Standard section status values"""
    PENDING = "pending"
    DRAFT = "draft"
    READY = "ready"
    APPROVED = "approved"
    COMPLETE = "complete"
    ERROR = "error"


class ExportFormat(Enum):
    """Standard export format values"""
    TXT = "txt"
    PDF = "pdf"
    DOCX = "docx"


@dataclass
class StandardSectionData:
    """Standardized section data format used across all components"""
    section_id: str
    title: str
    content: str
    status: SectionStatus
    case_id: str
    evidence_ids: List[str]
    metadata: Dict[str, Any]
    generated_at: str
    source: str
    tags: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for JSON serialization"""
        return {
            "section_id": self.section_id,
            "title": self.title,
            "content": self.content,
            "status": self.status.value,
            "case_id": self.case_id,
            "evidence_ids": self.evidence_ids,
            "metadata": self.metadata,
            "generated_at": self.generated_at,
            "source": self.source,
            "tags": self.tags
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StandardSectionData":
        """Create from dictionary format"""
        return cls(
            section_id=data["section_id"],
            title=data["title"],
            content=data["content"],
            status=SectionStatus(data.get("status", "pending")),
            case_id=data["case_id"],
            evidence_ids=data.get("evidence_ids", []),
            metadata=data.get("metadata", {}),
            generated_at=data.get("generated_at", datetime.now().isoformat()),
            source=data.get("source", "unknown"),
            tags=data.get("tags", [])
        )


@dataclass
class StandardEvidenceData:
    """Standardized evidence data format"""
    evidence_id: str
    filename: str
    file_path: str
    file_type: str
    file_size: int
    classification: str
    section_hints: List[str]
    tags: List[str]
    metadata: Dict[str, Any]
    processed_at: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format"""
        return {
            "evidence_id": self.evidence_id,
            "filename": self.filename,
            "file_path": self.file_path,
            "file_type": self.file_type,
            "file_size": self.file_size,
            "classification": self.classification,
            "section_hints": self.section_hints,
            "tags": self.tags,
            "metadata": self.metadata,
            "processed_at": self.processed_at
        }


@dataclass
class StandardReportPayload:
    """Standardized report payload format"""
    case_id: str
    report_id: str
    sections: Dict[str, StandardSectionData]
    evidence: Dict[str, StandardEvidenceData]
    metadata: Dict[str, Any]
    generated_at: str
    status: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format"""
        return {
            "case_id": self.case_id,
            "report_id": self.report_id,
            "sections": {k: v.to_dict() for k, v in self.sections.items()},
            "evidence": {k: v.to_dict() for k, v in self.evidence.items()},
            "metadata": self.metadata,
            "generated_at": self.generated_at,
            "status": self.status
        }


class StandardInterface:
    """Base interface class for standardized component communication"""
    
    @staticmethod
    def validate_section_data(data: Dict[str, Any]) -> bool:
        """Validate section data format"""
        required_fields = ["section_id", "title", "content", "status", "case_id"]
        return all(field in data for field in required_fields)
    
    @staticmethod
    def validate_evidence_data(data: Dict[str, Any]) -> bool:
        """Validate evidence data format"""
        required_fields = ["evidence_id", "filename", "file_path", "file_type"]
        return all(field in data for field in required_fields)
    
    @staticmethod
    def validate_report_payload(data: Dict[str, Any]) -> bool:
        """Validate report payload format"""
        required_fields = ["case_id", "report_id", "sections", "evidence"]
        return all(field in data for field in required_fields)
    
    @staticmethod
    def normalize_section_content(content: Union[str, Dict[str, Any]]) -> str:
        """Normalize section content to plain text"""
        if isinstance(content, str):
            return content.strip()
        elif isinstance(content, dict):
            # Extract text from structured content
            if "content" in content:
                return str(content["content"]).strip()
            elif "narrative" in content:
                return str(content["narrative"]).strip()
            elif "text" in content:
                return str(content["text"]).strip()
            else:
                return str(content).strip()
        else:
            return str(content).strip()
    
    @staticmethod
    def create_section_dict(sections: Dict[str, StandardSectionData]) -> Dict[str, str]:
        """Convert StandardSectionData dict to simple section_id -> content mapping"""
        return {
            section_id: data.content 
            for section_id, data in sections.items()
        }
    
    @staticmethod
    def create_evidence_dict(evidence: Dict[str, StandardEvidenceData]) -> Dict[str, Dict[str, Any]]:
        """Convert StandardEvidenceData dict to simple evidence_id -> metadata mapping"""
        return {
            evidence_id: {
                "filename": data.filename,
                "file_path": data.file_path,
                "classification": data.classification,
                "tags": data.tags
            }
            for evidence_id, data in evidence.items()
        }


# Standard signal payload formats
SIGNAL_PAYLOADS = {
    "narrative.assembled": {
        "required": ["section_id", "case_id", "narrative", "status"],
        "optional": ["summary", "auto_narrative", "evidence_ids", "metadata"]
    },
    "section.data.updated": {
        "required": ["section_id", "case_id", "content", "status"],
        "optional": ["title", "evidence_ids", "metadata", "source"]
    },
    "evidence.updated": {
        "required": ["evidence_id", "filename", "classification"],
        "optional": ["file_path", "section_hints", "tags", "metadata"]
    },
    "report.generated": {
        "required": ["case_id", "report_id", "status"],
        "optional": ["report_path", "sections", "evidence", "metadata"]
    }
}


def validate_signal_payload(signal_type: str, payload: Dict[str, Any]) -> bool:
    """Validate signal payload against standard format"""
    if signal_type not in SIGNAL_PAYLOADS:
        return True  # Unknown signals pass validation
    
    schema = SIGNAL_PAYLOADS[signal_type]
    required_fields = schema["required"]
    
    return all(field in payload for field in required_fields)


def create_standard_narrative_signal(
    section_id: str,
    case_id: str,
    narrative: str,
    status: str = "complete",
    **kwargs
) -> Dict[str, Any]:
    """Create standardized narrative.assembled signal payload"""
    return {
        "section_id": section_id,
        "case_id": case_id,
        "narrative": narrative,
        "status": status,
        "timestamp": datetime.now().isoformat(),
        "source": "narrative_assembler",
        **kwargs
    }


def create_standard_section_signal(
    section_id: str,
    case_id: str,
    content: str,
    status: str = "updated",
    **kwargs
) -> Dict[str, Any]:
    """Create standardized section.data.updated signal payload"""
    return {
        "section_id": section_id,
        "case_id": case_id,
        "content": content,
        "status": status,
        "timestamp": datetime.now().isoformat(),
        "source": "mission_debrief_manager",
        **kwargs
    }


def create_standard_report_signal(
    case_id: str,
    report_id: str,
    status: str = "complete",
    **kwargs
) -> Dict[str, Any]:
    """Create standardized report.generated signal payload"""
    return {
        "case_id": case_id,
        "report_id": report_id,
        "status": status,
        "timestamp": datetime.now().isoformat(),
        "source": "report_generator",
        **kwargs
    }

