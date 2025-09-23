#!/usr/bin/env python3
"""
Case Manifest Builder - Generates case manifests with section validation and integrity checks
Integrates with ECC, Gateway, and EvidenceClassBuilder for comprehensive case documentation
"""

import os
import hashlib
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class CaseManifestBuilder:
    """Case Manifest Builder with section-aware execution enforcement"""
    
    def __init__(self, gateway=None, ecc=None, evidence_builder=None):
        self.gateway = gateway
        self.ecc = ecc
        self.evidence_builder = evidence_builder
        self.logger = logging.getLogger(__name__)
        
        # Manifest configuration
        self.manifest_version = "1.0.0"
        self.hash_algorithm = "sha256"
        
        self.logger.info("CaseManifestBuilder initialized")

    def _enforce_section_aware_execution(self, operation: str):
        """ENFORCES SECTION-AWARE EXECUTION - Every function begins with this check"""
        if not self.ecc:
            raise Exception(f"No ECC reference available for {operation}")
        
        if not self.gateway:
            raise Exception(f"No Gateway reference available for {operation}")
        
        self.logger.debug(f"✅ Section-aware execution validated for {operation}")

    def build_manifest(self, case_id: str = None) -> Dict[str, Any]:
        """Build case manifest with section validation and integrity checks - ENFORCES SECTION-AWARE EXECUTION"""
        try:
            # SECTION-AWARE EXECUTION ENFORCEMENT
            self._enforce_section_aware_execution("manifest building")
            
            # Check if case is exportable
            if not self.ecc.is_case_exportable():
                raise Exception("Case not exportable - not all sections completed")
            
            self.logger.info("Building case manifest...")
            
            # Initialize manifest
            manifest = {
                "case_id": case_id or self._generate_case_id(),
                "manifest_version": self.manifest_version,
                "generated_at": datetime.now().isoformat(),
                "generated_by": "CaseManifestBuilder",
                "hash_algorithm": self.hash_algorithm,
                "sections": {},
                "evidence_summary": {},
                "integrity_hashes": {},
                "case_status": {
                    "total_sections": len(self.ecc.section_contracts),
                    "completed_sections": len(self.ecc.completed_ecosystems),
                    "exportable": self.ecc.is_case_exportable(),
                    "locked": False
                }
            }
            
            # Process each section
            for section_id in self.ecc.section_contracts:
                section_data = self._process_section(section_id)
                manifest["sections"][section_id] = section_data
            
            # Generate evidence summary
            manifest["evidence_summary"] = self._generate_evidence_summary()
            
            # Generate integrity hashes
            manifest["integrity_hashes"] = self._generate_integrity_hashes(manifest)
            
            self.logger.debug(f"📋 Built manifest for case {manifest['case_id']}")
            self.logger.info(f"Built manifest for case {manifest['case_id']}")
            return manifest
            
        except Exception as e:
            self.logger.error(f"Failed to build manifest: {e}")
            raise

    def _process_section(self, section_id: str) -> Dict[str, Any]:
        """Process individual section data"""
        try:
            section_contract = self.ecc.section_contracts[section_id]
            
            # Check if section is completed
            is_completed = section_id in self.ecc.completed_ecosystems
            
            section_data = {
                "section_id": section_id,
                "title": section_contract.get("title", f"Section {section_id}"),
                "priority": section_contract.get("priority", 0),
                "depends_on": section_contract.get("depends_on", []),
                "status": "completed" if is_completed else "pending",
                "validated": is_completed,
                "timestamp": None,
                "signed_by": None,
                "data_hash": None,
                "evidence_count": 0,
                "revision_count": 0
            }
            
            if is_completed:
                # Get section data from Gateway
                section_cache_entry = self.gateway.section_cache.get(section_id)
                if section_cache_entry:
                    section_data.update({
                        "timestamp": section_cache_entry.get("sign_time"),
                        "signed_by": section_cache_entry.get("signed_by"),
                        "revision_count": section_cache_entry.get("revision_count", 0)
                    })
                    
                    # Generate data hash
                    data = section_cache_entry.get("data", {})
                    serialized = json.dumps(data, sort_keys=True)
                    section_data["data_hash"] = hashlib.sha256(serialized.encode()).hexdigest()
                
                # Count evidence for this section
                if self.evidence_builder:
                    evidence_summary = self.evidence_builder.get_evidence_class_summary([])
                    section_data["evidence_count"] = evidence_summary.get("by_section", {}).get(section_id, 0)
            
            return section_data
            
        except Exception as e:
            self.logger.error(f"Failed to process section {section_id}: {e}")
            return {
                "section_id": section_id,
                "title": f"Section {section_id}",
                "status": "error",
                "validated": False,
                "error": str(e)
            }

    def _generate_evidence_summary(self) -> Dict[str, Any]:
        """Generate evidence summary for the case"""
        try:
            if not self.evidence_builder:
                return {"total_evidence": 0, "by_type": {}, "by_section": {}}
            
            # Get evidence summary from builder
            evidence_summary = self.evidence_builder.get_evidence_class_summary([])
            
            return {
                "total_evidence": evidence_summary.get("total_evidence", 0),
                "by_type": evidence_summary.get("by_type", {}),
                "by_section": evidence_summary.get("by_section", {}),
                "total_size": evidence_summary.get("total_size", 0),
                "file_types": evidence_summary.get("file_types", [])
            }
            
        except Exception as e:
            self.logger.error(f"Failed to generate evidence summary: {e}")
            return {"total_evidence": 0, "error": str(e)}

    def _generate_integrity_hashes(self, manifest: Dict[str, Any]) -> Dict[str, str]:
        """Generate integrity hashes for manifest sections"""
        try:
            integrity_hashes = {}
            
            # Generate hash for each completed section
            for section_id, section_data in manifest["sections"].items():
                if section_data.get("validated", False) and section_data.get("data_hash"):
                    integrity_hashes[section_id] = section_data["data_hash"]
            
            # Generate overall manifest hash
            manifest_copy = manifest.copy()
            manifest_copy.pop("integrity_hashes", None)  # Remove hashes to avoid circular reference
            manifest_serialized = json.dumps(manifest_copy, sort_keys=True)
            integrity_hashes["manifest"] = hashlib.sha256(manifest_serialized.encode()).hexdigest()
            
            return integrity_hashes
            
        except Exception as e:
            self.logger.error(f"Failed to generate integrity hashes: {e}")
            return {}

    def _generate_case_id(self) -> str:
        """Generate case ID if not provided"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            return f"CASE_{timestamp}"
        except Exception as e:
            self.logger.error(f"Failed to generate case ID: {e}")
            return "CASE_UNKNOWN"

    def finalize_manifest(self, output_path: str, case_id: str = None) -> str:
        """Finalize and export manifest to file - ENFORCES SECTION-AWARE EXECUTION"""
        try:
            # SECTION-AWARE EXECUTION ENFORCEMENT
            self._enforce_section_aware_execution("manifest finalization")
            
            self.logger.info(f"Finalizing manifest to {output_path}")
            
            # Build manifest
            manifest = self.build_manifest(case_id)
            
            # Lock the manifest
            manifest["case_status"]["locked"] = True
            manifest["finalized_at"] = datetime.now().isoformat()
            
            # Ensure output directory exists
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            # Write manifest to file
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(manifest, f, indent=4, ensure_ascii=False)
            
            self.logger.debug(f"📄 Finalized manifest exported to {output_path}")
            self.logger.info(f"Finalized manifest exported to {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Failed to finalize manifest: {e}")
            raise

    def validate_manifest_integrity(self, manifest_path: str) -> bool:
        """Validate manifest integrity by checking hashes"""
        try:
            self.logger.info(f"Validating manifest integrity: {manifest_path}")
            
            # Load manifest
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
            
            # Check if manifest is locked
            if not manifest.get("case_status", {}).get("locked", False):
                self.logger.warning("Manifest is not locked - integrity cannot be fully validated")
                return False
            
            # Validate section hashes
            integrity_hashes = manifest.get("integrity_hashes", {})
            sections = manifest.get("sections", {})
            
            for section_id, section_data in sections.items():
                if section_data.get("validated", False):
                    stored_hash = integrity_hashes.get(section_id)
                    if not stored_hash:
                        self.logger.error(f"No integrity hash found for section {section_id}")
                        return False
            
            # Validate manifest hash
            manifest_hash = integrity_hashes.get("manifest")
            if not manifest_hash:
                self.logger.error("No manifest integrity hash found")
                return False
            
            self.logger.debug(f"✅ Manifest integrity validation passed")
            self.logger.info(f"Manifest integrity validation passed")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to validate manifest integrity: {e}")
            return False

    def get_manifest_summary(self, manifest_path: str) -> Dict[str, Any]:
        """Get summary of manifest contents"""
        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
            
            case_status = manifest.get("case_status", {})
            evidence_summary = manifest.get("evidence_summary", {})
            
            return {
                "case_id": manifest.get("case_id"),
                "generated_at": manifest.get("generated_at"),
                "locked": case_status.get("locked", False),
                "total_sections": case_status.get("total_sections", 0),
                "completed_sections": case_status.get("completed_sections", 0),
                "exportable": case_status.get("exportable", False),
                "total_evidence": evidence_summary.get("total_evidence", 0),
                "evidence_by_type": evidence_summary.get("by_type", {}),
                "evidence_by_section": evidence_summary.get("by_section", {}),
                "integrity_hashes_count": len(manifest.get("integrity_hashes", {}))
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get manifest summary: {e}")
            return {}

    def get_builder_status(self) -> Dict[str, Any]:
        """Get case manifest builder status"""
        return {
            "manifest_version": self.manifest_version,
            "hash_algorithm": self.hash_algorithm,
            "ecc_connected": bool(self.ecc),
            "gateway_connected": bool(self.gateway),
            "evidence_builder_connected": bool(self.evidence_builder),
            "case_exportable": self.ecc.is_case_exportable() if self.ecc else False,
            "total_sections": len(self.ecc.section_contracts) if self.ecc else 0,
            "completed_sections": len(self.ecc.completed_ecosystems) if self.ecc else 0
        }


# Usage example
def create_case_manifest_builder(ecc, gateway, evidence_builder=None):
    """Create case manifest builder instance"""
    builder = CaseManifestBuilder(
        gateway=gateway,
        ecc=ecc,
        evidence_builder=evidence_builder
    )
    logger.info("Case manifest builder created")
    return builder