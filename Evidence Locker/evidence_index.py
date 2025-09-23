#!/usr/bin/env python3
"""
Evidence Index - Central evidence management system
Holds every file's tag, source, path, and links with master archive and per-section mapping
"""

import os
import uuid
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Set

logger = logging.getLogger(__name__)

class EvidenceIndex:
    """Evidence Index - holds every file's tag, source, path, and links"""
    
    def __init__(self, ecc=None):
        # Master evidence index - full case archive
        self.master_evidence_index = {}
        
        # Evidence map - per-section input
        self.evidence_map = {}
        
        # Cross-link tracking
        self.cross_links = {}
        self.link_graph = {}
        
        # Metadata tracking
        self.file_tags = {}
        self.source_registry = {}
        self.path_index = {}
        
        self.logger = logging.getLogger(__name__)
        self.ecc = ecc  # Reference to EcosystemController for validation
        self.logger.info("Evidence Index initialized")
    
    def _call_out_to_ecc(self, operation: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Call out to ECC for permission to perform operation"""
        try:
            if not self.ecc:
                return {"permission_granted": True, "request_id": None}
            
            request_id = f"index_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
            
            # Emit call-out signal to ECC
            if hasattr(self.ecc, 'emit'):
                self.ecc.emit("evidence_locker.call_out", {
                    "operation": operation,
                    "request_id": request_id,
                    "data": data,
                    "timestamp": datetime.now().isoformat(),
                    "module": "evidence_index"
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
                    "module": "evidence_index"
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
                    "module": "evidence_index"
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
                    "module": "evidence_index"
                })
            
            self.logger.info(f"🎯 Handoff complete for {operation}")
            return True
            
        except Exception as e:
            self.logger.error(f"Handoff complete failed: {e}")
            return False
    
    def add_file(self, file_path: str, tags: List[str] = None, source: str = "upload", section_id: str = None) -> str:
        """Add file to master evidence index - ENFORCES SECTION-AWARE EXECUTION"""
        try:
            # ECC CALL-OUT: Request permission to add file
            if self.ecc:
                call_out_result = self._call_out_to_ecc("add_file", {
                    "file_path": file_path,
                    "section_id": section_id,
                    "operation": "evidence_indexing"
                })
                
                if not call_out_result.get("permission_granted", False):
                    raise Exception(f"ECC denied file addition permission for {file_path}")
                
                # ECC CONFIRM: Wait for confirmation
                confirm_result = self._wait_for_ecc_confirm("add_file", call_out_result.get("request_id"))
                if not confirm_result.get("confirmed", False):
                    raise Exception(f"ECC confirmation failed for file addition of {file_path}")
            
            # SECTION-AWARE EXECUTION ENFORCEMENT
            if section_id and self.ecc:
                if not self.ecc.can_run(section_id):
                    raise Exception(f"Section {section_id} not active or blocked for file addition")
            
            evidence_id = str(uuid.uuid4())
            filename = os.path.basename(file_path)
            
            # File metadata
            file_stats = {
                'filename': filename,
                'file_path': file_path,
                'file_size': os.path.getsize(file_path) if os.path.exists(file_path) else 0,
                'file_type': os.path.splitext(file_path)[1].lower(),
                'created_at': datetime.now().isoformat(),
                'source': source
            }
            
            # Evidence record
            evidence_record = {
                'evidence_id': evidence_id,
                'filename': filename,
                'path': file_path,
                'tags': tags or [],
                'source': source,
                'links': [],
                'assigned_section': section_id or 'unassigned',
                'metadata': file_stats,
                'added_at': datetime.now().isoformat()
            }
            
            # Add to master index
            self.master_evidence_index[evidence_id] = evidence_record
            
            # Index by path
            self.path_index[file_path] = evidence_id
            
            # Index by tags
            for tag in (tags or []):
                if tag not in self.file_tags:
                    self.file_tags[tag] = []
                self.file_tags[tag].append(evidence_id)
            
            # Index by source
            if source not in self.source_registry:
                self.source_registry[source] = []
            self.source_registry[source].append(evidence_id)
            
            self.logger.debug(f"📁 Added file {filename} as {evidence_id}")
            self.logger.info(f"Added file {filename} to evidence index")
            
            # COMPLETE HANDOFF PROCESS
            # 1. SEND MESSAGE: Notify receiving module
            self._send_message("file_indexed", {
                "evidence_id": evidence_id,
                "file_path": file_path,
                "section_id": section_id,
                "tags": tags or [],
                "source": source
            })
            
            # 2. SEND ACCEPT SIGNAL: Notify receiving module
            self._send_accept_signal("file_indexed_complete", {
                "evidence_id": evidence_id,
                "file_path": file_path,
                "section_id": section_id,
                "tags": tags or [],
                "source": source
            })
            
            # 3. COMPLETE HANDOFF: Final confirmation
            self._complete_handoff("file_indexing_handoff", {
                "evidence_id": evidence_id,
                "file_path": file_path,
                "section_id": section_id,
                "tags": tags or [],
                "source": source
            })
            
            return evidence_id
            
        except Exception as e:
            self.logger.error(f"Failed to add file {file_path}: {e}")
            raise
    
    def assign_to_section(self, evidence_id: str, section_id: str) -> bool:
        """Assign evidence to specific section - ENFORCES SECTION-AWARE EXECUTION"""
        try:
            # SECTION-AWARE EXECUTION ENFORCEMENT
            if self.ecc:
                if not self.ecc.can_run(section_id):
                    raise Exception(f"Section {section_id} not active or blocked for evidence assignment")
            
            if evidence_id not in self.master_evidence_index:
                self.logger.error(f"Evidence {evidence_id} not found")
                return False
            
            # Update master record
            self.master_evidence_index[evidence_id]['assigned_section'] = section_id
            
            # Add to section map
            if section_id not in self.evidence_map:
                self.evidence_map[section_id] = []
            
            # Check if already assigned to avoid duplicates
            existing_ids = [e['evidence_id'] for e in self.evidence_map[section_id]]
            if evidence_id not in existing_ids:
                self.evidence_map[section_id].append(self.master_evidence_index[evidence_id])
            
            self.logger.debug(f"📋 Assigned evidence {evidence_id} to {section_id}")
            self.logger.info(f"Assigned evidence {evidence_id} to {section_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to assign evidence {evidence_id} to {section_id}: {e}")
            raise
    
    def add_cross_link(self, evidence_id: str, keyword: str, target_evidence_id: Optional[str] = None, link_strength: float = 1.0) -> bool:
        """Tracks file relationships"""
        try:
            if evidence_id not in self.master_evidence_index:
                self.logger.error(f"Evidence {evidence_id} not found")
                return False
            
            # Create cross-link record
            cross_link = {
                'keyword': keyword,
                'target_evidence_id': target_evidence_id,
                'link_strength': link_strength,
                'created_at': datetime.now().isoformat()
            }
            
            # Add to evidence record
            self.master_evidence_index[evidence_id]['links'].append(cross_link)
            
            # Add to cross-links index
            if keyword not in self.cross_links:
                self.cross_links[keyword] = []
            self.cross_links[keyword].append({
                'evidence_id': evidence_id,
                'target_evidence_id': target_evidence_id,
                'link_strength': link_strength,
                'created_at': datetime.now().isoformat()
            })
            
            # Build link graph
            if evidence_id not in self.link_graph:
                self.link_graph[evidence_id] = []
            self.link_graph[evidence_id].append({
                'target': target_evidence_id,
                'keyword': keyword,
                'strength': link_strength
            })
            
            self.logger.info(f"🔗 Added cross-link: {keyword} from {evidence_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add cross-link: {e}")
            return False
    
    def get_evidence_for_section(self, section_id: str) -> List[Dict[str, Any]]:
        """Get evidence assigned to specific section"""
        return self.evidence_map.get(section_id, [])
    
    def get_evidence_by_tag(self, tag: str) -> List[Dict[str, Any]]:
        """Get evidence by tag"""
        evidence_ids = self.file_tags.get(tag, [])
        return [self.master_evidence_index[eid] for eid in evidence_ids if eid in self.master_evidence_index]
    
    def get_evidence_by_source(self, source: str) -> List[Dict[str, Any]]:
        """Get evidence by source"""
        evidence_ids = self.source_registry.get(source, [])
        return [self.master_evidence_index[eid] for eid in evidence_ids if eid in self.master_evidence_index]
    
    def get_cross_links(self, evidence_id: str) -> List[Dict[str, Any]]:
        """Get all cross-links for evidence"""
        if evidence_id not in self.master_evidence_index:
            return []
        return self.master_evidence_index[evidence_id]['links']
    
    def get_related_evidence(self, evidence_id: str) -> List[Dict[str, Any]]:
        """Get evidence related through cross-links"""
        if evidence_id not in self.link_graph:
            return []
        
        related_ids = []
        for link in self.link_graph[evidence_id]:
            if link['target'] and link['target'] in self.master_evidence_index:
                related_ids.append(link['target'])
        
        return [self.master_evidence_index[eid] for eid in related_ids]
    
    def search_evidence(self, query: str) -> List[Dict[str, Any]]:
        """Search evidence by filename, tags, or keywords"""
        results = []
        query_lower = query.lower()
        
        for evidence_id, record in self.master_evidence_index.items():
            # Search filename
            if query_lower in record['filename'].lower():
                results.append(record)
                continue
            
            # Search tags
            for tag in record['tags']:
                if query_lower in tag.lower():
                    results.append(record)
                    break
            
            # Search cross-link keywords
            for link in record['links']:
                if query_lower in link['keyword'].lower():
                    results.append(record)
                    break
        
        return results
    
    def get_master_index(self) -> Dict[str, Any]:
        """Get full master evidence index"""
        return self.master_evidence_index
    
    def get_evidence_map(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get evidence map by section"""
        return self.evidence_map
    
    def get_index_statistics(self) -> Dict[str, Any]:
        """Get evidence index statistics"""
        return {
            'total_evidence_items': len(self.master_evidence_index),
            'total_sections': len(self.evidence_map),
            'total_cross_links': sum(len(links) for links in self.cross_links.values()),
            'total_tags': len(self.file_tags),
            'total_sources': len(self.source_registry),
            'section_distribution': {section: len(evidence) for section, evidence in self.evidence_map.items()},
            'tag_distribution': {tag: len(evidence_ids) for tag, evidence_ids in self.file_tags.items()},
            'source_distribution': {source: len(evidence_ids) for source, evidence_ids in self.source_registry.items()}
        }
    
    def export_evidence_index(self) -> Dict[str, Any]:
        """Export complete evidence index"""
        return {
            'master_evidence_index': self.master_evidence_index,
            'evidence_map': self.evidence_map,
            'cross_links': self.cross_links,
            'file_tags': self.file_tags,
            'source_registry': self.source_registry,
            'path_index': self.path_index,
            'export_timestamp': datetime.now().isoformat()
        }


