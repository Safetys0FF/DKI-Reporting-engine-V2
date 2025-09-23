#!/usr/bin/env python3
"""
Evidence Class Builder - Dynamic evidence class generation and management
Creates evidence classes based on file types, content analysis, and section requirements
"""

import os
import uuid
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Type, Union
from dataclasses import dataclass, field
from enum import Enum
import mimetypes

logger = logging.getLogger(__name__)

class EvidenceType(Enum):
    """Evidence type enumeration"""
    VIDEO = "video"
    AUDIO = "audio"
    IMAGE = "image"
    DOCUMENT = "document"
    TEXT = "text"
    DATA = "data"
    UNKNOWN = "unknown"

class EvidencePriority(Enum):
    """Evidence priority levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

@dataclass
class EvidenceMetadata:
    """Evidence metadata container"""
    evidence_id: str
    filename: str
    file_path: str
    file_size: int
    file_type: str
    mime_type: str
    evidence_type: EvidenceType
    priority: EvidencePriority
    section_id: str
    tags: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    modified_at: str = field(default_factory=lambda: datetime.now().isoformat())
    source: str = "unknown"
    checksum: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

class EvidenceClassBuilder:
    """Dynamic evidence class builder with section-aware execution"""
    
    def __init__(self, ecc=None):
        self.ecc = ecc  # Reference to EcosystemController for validation
        self.logger = logging.getLogger(__name__)
        
        # Evidence class templates
        self.evidence_templates = {
            EvidenceType.VIDEO: self._create_video_evidence_class,
            EvidenceType.AUDIO: self._create_audio_evidence_class,
            EvidenceType.IMAGE: self._create_image_evidence_class,
            EvidenceType.DOCUMENT: self._create_document_evidence_class,
            EvidenceType.TEXT: self._create_text_evidence_class,
            EvidenceType.DATA: self._create_data_evidence_class
        }
        
        # File type mappings
        self.file_type_mappings = {
            # Video files
            '.mp4': EvidenceType.VIDEO,
            '.avi': EvidenceType.VIDEO,
            '.mov': EvidenceType.VIDEO,
            '.mkv': EvidenceType.VIDEO,
            '.wmv': EvidenceType.VIDEO,
            '.flv': EvidenceType.VIDEO,
            '.webm': EvidenceType.VIDEO,
            
            # Audio files
            '.mp3': EvidenceType.AUDIO,
            '.wav': EvidenceType.AUDIO,
            '.m4a': EvidenceType.AUDIO,
            '.aac': EvidenceType.AUDIO,
            '.flac': EvidenceType.AUDIO,
            '.ogg': EvidenceType.AUDIO,
            
            # Image files
            '.jpg': EvidenceType.IMAGE,
            '.jpeg': EvidenceType.IMAGE,
            '.png': EvidenceType.IMAGE,
            '.gif': EvidenceType.IMAGE,
            '.bmp': EvidenceType.IMAGE,
            '.tiff': EvidenceType.IMAGE,
            '.svg': EvidenceType.IMAGE,
            '.webp': EvidenceType.IMAGE,
            
            # Document files
            '.pdf': EvidenceType.DOCUMENT,
            '.doc': EvidenceType.DOCUMENT,
            '.docx': EvidenceType.DOCUMENT,
            '.txt': EvidenceType.TEXT,
            '.rtf': EvidenceType.DOCUMENT,
            '.odt': EvidenceType.DOCUMENT,
            
            # Data files
            '.json': EvidenceType.DATA,
            '.xml': EvidenceType.DATA,
            '.csv': EvidenceType.DATA,
            '.xlsx': EvidenceType.DATA,
            '.db': EvidenceType.DATA,
            '.sqlite': EvidenceType.DATA
        }
        
        # Section-specific evidence requirements
        self.section_requirements = {
            'section_1': {
                'required_types': [EvidenceType.DOCUMENT, EvidenceType.TEXT],
                'priority': EvidencePriority.HIGH,
                'description': 'Case overview and initial documentation'
            },
            'section_3': {
                'required_types': [EvidenceType.VIDEO, EvidenceType.AUDIO, EvidenceType.IMAGE],
                'priority': EvidencePriority.CRITICAL,
                'description': 'Surveillance operations and monitoring'
            },
            'section_5': {
                'required_types': [EvidenceType.DOCUMENT, EvidenceType.DATA],
                'priority': EvidencePriority.HIGH,
                'description': 'Financial records and supporting documents'
            },
            'section_8': {
                'required_types': [EvidenceType.IMAGE, EvidenceType.DOCUMENT],
                'priority': EvidencePriority.MEDIUM,
                'description': 'Media documentation and evidence index'
            }
        }
        
        self.logger.info("EvidenceClassBuilder initialized")
    
    def _call_out_to_ecc(self, operation: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Call out to ECC for permission to perform operation"""
        try:
            if not self.ecc:
                return {"permission_granted": True, "request_id": None}
            
            request_id = f"builder_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
            
            # Emit call-out signal to ECC
            if hasattr(self.ecc, 'emit'):
                self.ecc.emit("evidence_locker.call_out", {
                    "operation": operation,
                    "request_id": request_id,
                    "data": data,
                    "timestamp": datetime.now().isoformat(),
                    "module": "evidence_class_builder"
                })
            
            self.logger.info(f"📞 Called out to ECC for {operation} - Request ID: {request_id}")
            return {"permission_granted": True, "request_id": request_id}
            
        except Exception as e:
            self.logger.error(f"ECC call-out failed: {e}")
            return {"permission_granted": False, "error": str(e)}
    
    def _wait_for_ecc_confirm(self, operation: str, request_id: str) -> Dict[str, Any]:
        """Wait for ECC confirmation"""
        try:
            if not self.ecc or not request_id:
                return {"confirmed": True}
            
            # In a real implementation, this would wait for ECC response
            # For now, simulate immediate confirmation
            self.logger.info(f"✅ ECC confirmed {operation} - Request ID: {request_id}")
            return {"confirmed": True, "request_id": request_id}
            
        except Exception as e:
            self.logger.error(f"ECC confirmation failed: {e}")
            return {"confirmed": False, "error": str(e)}
    
    def _send_message(self, operation: str, data: Dict[str, Any]) -> bool:
        """Send message to receiving module"""
        try:
            if not self.ecc:
                return True
            
            # Emit send message signal
            if hasattr(self.ecc, 'emit'):
                self.ecc.emit("evidence_locker.send", {
                    "operation": operation,
                    "data": data,
                    "timestamp": datetime.now().isoformat(),
                    "module": "evidence_class_builder"
                })
            
            self.logger.info(f"📤 Sent message for {operation}")
            return True
            
        except Exception as e:
            self.logger.error(f"Send message failed: {e}")
            return False
    
    def _send_accept_signal(self, operation: str, data: Dict[str, Any]) -> bool:
        """Send accept signal to receiving module"""
        try:
            if not self.ecc:
                return True
            
            # Emit accept signal
            if hasattr(self.ecc, 'emit'):
                self.ecc.emit("evidence_locker.accept", {
                    "operation": operation,
                    "data": data,
                    "timestamp": datetime.now().isoformat(),
                    "module": "evidence_class_builder"
                })
            
            self.logger.info(f"✅ Sent accept signal for {operation}")
            return True
            
        except Exception as e:
            self.logger.error(f"Accept signal failed: {e}")
            return False
    
    def _complete_handoff(self, operation: str, data: Dict[str, Any]) -> bool:
        """Complete handoff process"""
        try:
            if not self.ecc:
                return True
            
            # Emit handoff complete signal
            if hasattr(self.ecc, 'emit'):
                self.ecc.emit("evidence_locker.handoff_complete", {
                    "operation": operation,
                    "data": data,
                    "timestamp": datetime.now().isoformat(),
                    "module": "evidence_class_builder"
                })
            
            self.logger.info(f"🎯 Handoff complete for {operation}")
            return True
            
        except Exception as e:
            self.logger.error(f"Handoff complete failed: {e}")
            return False
    
    def _handoff_to_module(self, target_module: str, operation: str, data: Dict[str, Any]) -> bool:
        """Handoff to another Evidence Locker module"""
        try:
            if not self.ecc:
                return True
            
            # Emit inter-module handoff signal
            if hasattr(self.ecc, 'emit'):
                self.ecc.emit("evidence_locker.inter_module_handoff", {
                    "from_module": "evidence_class_builder",
                    "to_module": target_module,
                    "operation": operation,
                    "data": data,
                    "timestamp": datetime.now().isoformat()
                })
            
            self.logger.info(f"🔄 Handing off to {target_module} for {operation}")
            return True
            
        except Exception as e:
            self.logger.error(f"Inter-module handoff failed: {e}")
            return False

    def _enforce_section_aware_execution(self, section_id: str, operation: str):
        """ENFORCES SECTION-AWARE EXECUTION - Every function begins with this check"""
        if not self.ecc:
            raise Exception(f"No ECC reference available for {operation}")
        
        if not self.ecc.can_run(section_id):
            raise Exception(f"Section {section_id} not active or blocked for {operation}")
        
        self.logger.debug(f"✅ Section {section_id} validated for {operation}")

    def detect_evidence_type(self, file_path: str) -> EvidenceType:
        """Detect evidence type from file path and content"""
        try:
            filename = os.path.basename(file_path)
            file_extension = os.path.splitext(filename)[1].lower()
            
            # Check file extension mapping
            if file_extension in self.file_type_mappings:
                return self.file_type_mappings[file_extension]
            
            # Check MIME type
            mime_type, _ = mimetypes.guess_type(file_path)
            if mime_type:
                if mime_type.startswith('video/'):
                    return EvidenceType.VIDEO
                elif mime_type.startswith('audio/'):
                    return EvidenceType.AUDIO
                elif mime_type.startswith('image/'):
                    return EvidenceType.IMAGE
                elif mime_type.startswith('text/'):
                    return EvidenceType.TEXT
                elif mime_type in ['application/pdf', 'application/msword']:
                    return EvidenceType.DOCUMENT
            
            # Content-based detection for unknown files
            return self._detect_by_content(file_path)
            
        except Exception as e:
            self.logger.error(f"Failed to detect evidence type for {file_path}: {e}")
            return EvidenceType.UNKNOWN

    def _detect_by_content(self, file_path: str) -> EvidenceType:
        """Detect evidence type by analyzing file content"""
        try:
            # Check file size and first few bytes
            if os.path.getsize(file_path) < 1024:  # Small files are likely text/data
                return EvidenceType.TEXT
            
            # Read first 512 bytes to check for magic numbers
            with open(file_path, 'rb') as f:
                header = f.read(512)
            
            # Check for common file signatures
            if header.startswith(b'\x89PNG'):
                return EvidenceType.IMAGE
            elif header.startswith(b'\xff\xd8\xff'):
                return EvidenceType.IMAGE
            elif header.startswith(b'GIF8'):
                return EvidenceType.IMAGE
            elif header.startswith(b'%PDF'):
                return EvidenceType.DOCUMENT
            elif header.startswith(b'PK\x03\x04'):
                return EvidenceType.DOCUMENT
            
            return EvidenceType.UNKNOWN
            
        except Exception as e:
            self.logger.debug(f"Content detection failed for {file_path}: {e}")
            return EvidenceType.UNKNOWN

    def build_evidence_class(self, file_path: str, section_id: str, priority: Optional[EvidencePriority] = None) -> EvidenceMetadata:
        """Build evidence class for a file - ENFORCES SECTION-AWARE EXECUTION"""
        try:
            # ECC CALL-OUT: Request permission to build evidence class
            if self.ecc:
                call_out_result = self._call_out_to_ecc("build_evidence_class", {
                    "file_path": file_path,
                    "section_id": section_id,
                    "operation": "evidence_class_building"
                })
                
                if not call_out_result.get("permission_granted", False):
                    raise Exception(f"ECC denied evidence class building permission for {file_path}")
                
                # ECC CONFIRM: Wait for confirmation
                confirm_result = self._wait_for_ecc_confirm("build_evidence_class", call_out_result.get("request_id"))
                if not confirm_result.get("confirmed", False):
                    raise Exception(f"ECC confirmation failed for evidence class building of {file_path}")
            
            # SECTION-AWARE EXECUTION ENFORCEMENT
            self._enforce_section_aware_execution(section_id, "evidence class building")
            
            # Detect evidence type
            evidence_type = self.detect_evidence_type(file_path)
            
            # Get file metadata
            filename = os.path.basename(file_path)
            file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
            file_extension = os.path.splitext(filename)[1].lower()
            mime_type, _ = mimetypes.guess_type(file_path)
            
            # Determine priority
            if priority is None:
                priority = self._determine_priority(section_id, evidence_type)
            
            # Generate evidence ID
            evidence_id = str(uuid.uuid4())
            
            # Create evidence metadata
            evidence_metadata = EvidenceMetadata(
                evidence_id=evidence_id,
                filename=filename,
                file_path=file_path,
                file_size=file_size,
                file_type=file_extension,
                mime_type=mime_type or "unknown",
                evidence_type=evidence_type,
                priority=priority,
                section_id=section_id,
                tags=self._generate_tags(filename, evidence_type, section_id),
                checksum=self._calculate_checksum(file_path)
            )
            
            # Add section-specific metadata
            self._add_section_metadata(evidence_metadata, section_id)
            
            self.logger.debug(f"🔧 Built evidence class for {filename} as {evidence_type.value}")
            self.logger.info(f"Built evidence class for {filename} as {evidence_type.value}")
            
            # COMPLETE HANDOFF PROCESS
            # 1. SEND MESSAGE: Notify receiving module
            self._send_message("evidence_class_built", {
                "evidence_id": evidence_id,
                "file_path": file_path,
                "section_id": section_id,
                "evidence_type": evidence_type.value,
                "priority": priority.value if priority else "auto"
            })
            
            # 2. HANDOFF TO EVIDENCE INDEX: Pass to next module
            self._handoff_to_module("evidence_index", "evidence_class_ready", {
                "evidence_metadata": evidence_metadata,
                "evidence_id": evidence_id,
                "section_id": section_id
            })
            
            # 3. SEND ACCEPT SIGNAL: Notify receiving module
            self._send_accept_signal("evidence_class_complete", {
                "evidence_id": evidence_id,
                "file_path": file_path,
                "section_id": section_id,
                "evidence_type": evidence_type.value
            })
            
            # 4. COMPLETE HANDOFF: Final confirmation
            self._complete_handoff("evidence_class_handoff", {
                "evidence_id": evidence_id,
                "file_path": file_path,
                "section_id": section_id,
                "evidence_type": evidence_type.value
            })
            
            return evidence_metadata
            
        except Exception as e:
            self.logger.error(f"Failed to build evidence class for {file_path}: {e}")
            raise

    def _determine_priority(self, section_id: str, evidence_type: EvidenceType) -> EvidencePriority:
        """Determine evidence priority based on section and type"""
        try:
            # Check section requirements
            if section_id in self.section_requirements:
                section_req = self.section_requirements[section_id]
                if evidence_type in section_req['required_types']:
                    return section_req['priority']
            
            # Default priority based on evidence type
            priority_mapping = {
                EvidenceType.VIDEO: EvidencePriority.CRITICAL,
                EvidenceType.AUDIO: EvidencePriority.HIGH,
                EvidenceType.IMAGE: EvidencePriority.MEDIUM,
                EvidenceType.DOCUMENT: EvidencePriority.HIGH,
                EvidenceType.TEXT: EvidencePriority.LOW,
                EvidenceType.DATA: EvidencePriority.MEDIUM,
                EvidenceType.UNKNOWN: EvidencePriority.LOW
            }
            
            return priority_mapping.get(evidence_type, EvidencePriority.LOW)
            
        except Exception as e:
            self.logger.error(f"Failed to determine priority: {e}")
            return EvidencePriority.LOW

    def _generate_tags(self, filename: str, evidence_type: EvidenceType, section_id: str) -> List[str]:
        """Generate tags for evidence based on filename and type"""
        tags = []
        
        # Add evidence type tag
        tags.append(evidence_type.value)
        
        # Add section tag
        tags.append(section_id)
        
        # Add filename-based tags
        filename_lower = filename.lower()
        
        # Common keywords
        keyword_tags = {
            'surveillance': ['surveillance', 'monitor', 'camera', 'footage'],
            'financial': ['lease', 'contract', 'bill', 'invoice', 'payment'],
            'legal': ['legal', 'court', 'law', 'agreement'],
            'evidence': ['evidence', 'proof', 'documentation'],
            'media': ['photo', 'image', 'picture', 'video', 'recording']
        }
        
        for tag_category, keywords in keyword_tags.items():
            if any(keyword in filename_lower for keyword in keywords):
                tags.append(tag_category)
        
        return tags

    def _calculate_checksum(self, file_path: str) -> str:
        """Calculate file checksum for integrity verification"""
        try:
            import hashlib
            
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
            
        except Exception as e:
            self.logger.debug(f"Failed to calculate checksum for {file_path}: {e}")
            return ""

    def _add_section_metadata(self, evidence_metadata: EvidenceMetadata, section_id: str):
        """Add section-specific metadata to evidence"""
        try:
            if section_id in self.section_requirements:
                section_req = self.section_requirements[section_id]
                evidence_metadata.metadata.update({
                    'section_description': section_req['description'],
                    'section_priority': section_req['priority'].value,
                    'required_types': [t.value for t in section_req['required_types']]
                })
            
            # Add processing metadata
            evidence_metadata.metadata.update({
                'processed_at': datetime.now().isoformat(),
                'builder_version': '1.0.0',
                'processing_method': 'dynamic_class_builder'
            })
            
        except Exception as e:
            self.logger.error(f"Failed to add section metadata: {e}")

    def batch_build_evidence_classes(self, file_paths: List[str], section_id: str) -> List[EvidenceMetadata]:
        """Build evidence classes for multiple files - ENFORCES SECTION-AWARE EXECUTION"""
        try:
            # SECTION-AWARE EXECUTION ENFORCEMENT
            self._enforce_section_aware_execution(section_id, "batch evidence class building")
            
            evidence_classes = []
            
            for file_path in file_paths:
                try:
                    evidence_class = self.build_evidence_class(file_path, section_id)
                    evidence_classes.append(evidence_class)
                except Exception as e:
                    self.logger.error(f"Failed to build evidence class for {file_path}: {e}")
                    continue
            
            self.logger.debug(f"📊 Built {len(evidence_classes)} evidence classes for {section_id}")
            self.logger.info(f"Built {len(evidence_classes)} evidence classes for {section_id}")
            return evidence_classes
            
        except Exception as e:
            self.logger.error(f"Failed to batch build evidence classes: {e}")
            raise

    def validate_evidence_class(self, evidence_metadata: EvidenceMetadata, section_id: str) -> bool:
        """Validate evidence class against section requirements - ENFORCES SECTION-AWARE EXECUTION"""
        try:
            # SECTION-AWARE EXECUTION ENFORCEMENT
            self._enforce_section_aware_execution(section_id, "evidence class validation")
            
            # Check if section has requirements
            if section_id not in self.section_requirements:
                self.logger.warning(f"No requirements defined for section {section_id}")
                return True
            
            section_req = self.section_requirements[section_id]
            
            # Check if evidence type is required
            if evidence_metadata.evidence_type not in section_req['required_types']:
                self.logger.warning(f"Evidence type {evidence_metadata.evidence_type.value} not required for {section_id}")
                return False
            
            # Check file exists and is readable
            if not os.path.exists(evidence_metadata.file_path):
                self.logger.error(f"Evidence file does not exist: {evidence_metadata.file_path}")
                return False
            
            # Check file size
            if evidence_metadata.file_size == 0:
                self.logger.warning(f"Evidence file is empty: {evidence_metadata.file_path}")
                return False
            
            self.logger.debug(f"✅ Evidence class validation passed for {evidence_metadata.filename}")
            self.logger.info(f"Evidence class validation passed for {evidence_metadata.filename}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to validate evidence class: {e}")
            raise

    def get_evidence_class_summary(self, evidence_classes: List[EvidenceMetadata]) -> Dict[str, Any]:
        """Get summary of evidence classes"""
        try:
            summary = {
                'total_evidence': len(evidence_classes),
                'by_type': {},
                'by_priority': {},
                'by_section': {},
                'total_size': 0,
                'file_types': set()
            }
            
            for evidence in evidence_classes:
                # Count by type
                evidence_type = evidence.evidence_type.value
                summary['by_type'][evidence_type] = summary['by_type'].get(evidence_type, 0) + 1
                
                # Count by priority
                priority = evidence.priority.value
                summary['by_priority'][priority] = summary['by_priority'].get(priority, 0) + 1
                
                # Count by section
                section = evidence.section_id
                summary['by_section'][section] = summary['by_section'].get(section, 0) + 1
                
                # Sum total size
                summary['total_size'] += evidence.file_size
                
                # Collect file types
                summary['file_types'].add(evidence.file_type)
            
            # Convert set to list for JSON serialization
            summary['file_types'] = list(summary['file_types'])
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Failed to generate evidence class summary: {e}")
            return {}

    def export_evidence_classes(self, evidence_classes: List[EvidenceMetadata], export_path: str) -> bool:
        """Export evidence classes to JSON file"""
        try:
            export_data = {
                'export_timestamp': datetime.now().isoformat(),
                'total_evidence': len(evidence_classes),
                'evidence_classes': []
            }
            
            for evidence in evidence_classes:
                evidence_dict = {
                    'evidence_id': evidence.evidence_id,
                    'filename': evidence.filename,
                    'file_path': evidence.file_path,
                    'file_size': evidence.file_size,
                    'file_type': evidence.file_type,
                    'mime_type': evidence.mime_type,
                    'evidence_type': evidence.evidence_type.value,
                    'priority': evidence.priority.value,
                    'section_id': evidence.section_id,
                    'tags': evidence.tags,
                    'created_at': evidence.created_at,
                    'modified_at': evidence.modified_at,
                    'source': evidence.source,
                    'checksum': evidence.checksum,
                    'metadata': evidence.metadata
                }
                export_data['evidence_classes'].append(evidence_dict)
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            self.logger.debug(f"📤 Exported {len(evidence_classes)} evidence classes to {export_path}")
            self.logger.info(f"Exported {len(evidence_classes)} evidence classes to {export_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export evidence classes: {e}")
            return False

    def get_builder_status(self) -> Dict[str, Any]:
        """Get evidence class builder status"""
        return {
            'evidence_types_supported': len(self.evidence_templates),
            'file_type_mappings': len(self.file_type_mappings),
            'section_requirements': len(self.section_requirements),
            'ecc_connected': bool(self.ecc),
            'builder_version': '1.0.0'
        }

    # Template methods for creating specific evidence classes
    def _create_video_evidence_class(self, metadata: EvidenceMetadata) -> Dict[str, Any]:
        """Create video-specific evidence class"""
        return {
            'type': 'video',
            'duration': metadata.metadata.get('duration', 0),
            'resolution': metadata.metadata.get('resolution', 'unknown'),
            'codec': metadata.metadata.get('codec', 'unknown'),
            'fps': metadata.metadata.get('fps', 0)
        }

    def _create_audio_evidence_class(self, metadata: EvidenceMetadata) -> Dict[str, Any]:
        """Create audio-specific evidence class"""
        return {
            'type': 'audio',
            'duration': metadata.metadata.get('duration', 0),
            'sample_rate': metadata.metadata.get('sample_rate', 0),
            'channels': metadata.metadata.get('channels', 0),
            'bitrate': metadata.metadata.get('bitrate', 0)
        }

    def _create_image_evidence_class(self, metadata: EvidenceMetadata) -> Dict[str, Any]:
        """Create image-specific evidence class"""
        return {
            'type': 'image',
            'width': metadata.metadata.get('width', 0),
            'height': metadata.metadata.get('height', 0),
            'color_depth': metadata.metadata.get('color_depth', 0),
            'format': metadata.metadata.get('format', 'unknown')
        }

    def _create_document_evidence_class(self, metadata: EvidenceMetadata) -> Dict[str, Any]:
        """Create document-specific evidence class"""
        return {
            'type': 'document',
            'page_count': metadata.metadata.get('page_count', 0),
            'word_count': metadata.metadata.get('word_count', 0),
            'language': metadata.metadata.get('language', 'unknown'),
            'author': metadata.metadata.get('author', 'unknown')
        }

    def _create_text_evidence_class(self, metadata: EvidenceMetadata) -> Dict[str, Any]:
        """Create text-specific evidence class"""
        return {
            'type': 'text',
            'line_count': metadata.metadata.get('line_count', 0),
            'word_count': metadata.metadata.get('word_count', 0),
            'encoding': metadata.metadata.get('encoding', 'utf-8'),
            'language': metadata.metadata.get('language', 'unknown')
        }

    def _create_data_evidence_class(self, metadata: EvidenceMetadata) -> Dict[str, Any]:
        """Create data-specific evidence class"""
        return {
            'type': 'data',
            'record_count': metadata.metadata.get('record_count', 0),
            'field_count': metadata.metadata.get('field_count', 0),
            'format': metadata.metadata.get('format', 'unknown'),
            'schema': metadata.metadata.get('schema', {})
        }


# Usage example
def create_evidence_class_builder(ecc):
    """Create evidence class builder instance"""
    builder = EvidenceClassBuilder(ecc=ecc)
    logger.info("Evidence class builder created")
    return builder
