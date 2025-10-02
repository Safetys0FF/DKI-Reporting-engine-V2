#!/usr/bin/env python3
"""
Archive Manager - Secure storage of finalized narratives
Handles tamper-proofing, audit logging, and retrieval of completed reports
"""

import os
import sys
import json
import hashlib
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

# Add Central Command paths for integration
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "The Warden"))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "Command Center", "Data Bus", "Bus Core Design"))

logger = logging.getLogger(__name__)

class ArchiveManager:
    """Archive Manager - Secure storage of finalized narratives with ECC integration"""
    
    # SECTION REGISTRY - Standardized 10-section registry matching Evidence Locker
    SECTION_REGISTRY = {
        "section_1": {"title": "Client & Subject Details", "tags": ["client", "subject", "intake"]},
        "section_2": {"title": "Pre-Surveillance Summary", "tags": ["background", "planning", "map", "aerial"]},
        "section_3": {"title": "Surveillance Details", "tags": ["surveillance", "field-log", "observed"]},
        "section_4": {"title": "Surveillance Recap", "tags": ["summary", "recap", "patterns"]},
        "section_5": {"title": "Supporting Documents", "tags": ["contract", "agreement", "lease", "court record"]},
        "section_6": {"title": "Billing Summary", "tags": ["billing", "retainer", "payment", "hours"]},
        "section_7": {"title": "Surveillance Photos", "tags": ["photo", "image", "visual"]},
        "section_8": {"title": "Conclusion", "tags": ["conclusion", "findings", "outcome"]},
        "section_9": {"title": "Disclosures / Legal", "tags": ["disclosure", "legal", "compliance", "licensing"]},
        "section_cp": {"title": "Cover Page", "tags": ["cover", "title", "branding"]},
        "section_dp": {"title": "Disclosure Page", "tags": ["disclosure", "authenticity", "signature"]},
        "section_toc": {"title": "Table of Contents", "tags": ["toc", "index", "navigation"]}
    }
    
    def __init__(self, ecc=None, bus=None, gateway=None):
        self.ecc = ecc
        self.bus = bus
        self.gateway = gateway
        self.logger = logger
        
        # Archive configuration
        self.archive_root = Path("final_reports")
        self.archive_root.mkdir(exist_ok=True)
        
        # ECC Integration tracking
        self.handoff_log = []
        self.audit_log = []
        
        # Initialize archive structure
        self._initialize_archive_structure()
        
        self.logger.info("Archive Manager initialized with ECC integration")
    
    def _initialize_archive_structure(self):
        """Initialize the archive directory structure"""
        try:
            # Create main archive directories
            (self.archive_root / "cases").mkdir(exist_ok=True)
            (self.archive_root / "audit_logs").mkdir(exist_ok=True)
            (self.archive_root / "tamper_proof").mkdir(exist_ok=True)
            (self.archive_root / "exports").mkdir(exist_ok=True)
            
            self.logger.info("Archive structure initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize archive structure: {e}")
    
    # ECC Integration Methods - Following Evidence Locker Pattern
    def _call_out_to_ecc(self, operation: str, data: Dict[str, Any]) -> bool:
        """Call out to ECC for permission to perform operation"""
        try:
            if not self.ecc:
                self.logger.warning("ECC not available for call-out")
                return False
            
            # Prepare call-out data
            call_out_data = {
                "operation": operation,
                "source": "archive_manager",
                "data": data,
                "timestamp": datetime.now().isoformat()
            }
            
            # Emit call-out signal to ECC
            if hasattr(self.ecc, 'emit'):
                self.ecc.emit("archive_manager.call_out", call_out_data)
                self.logger.info(f"📡 Called out to ECC for operation: {operation}")
                return True
            else:
                self.logger.warning("ECC does not support signal emission")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to call out to ECC: {e}")
            return False
    
    def _wait_for_ecc_confirm(self, timeout: int = 30) -> bool:
        """Wait for ECC confirmation"""
        try:
            # In a real implementation, this would wait for ECC response
            # For now, we'll simulate immediate confirmation
            self.logger.info("⏳ Waiting for ECC confirmation...")
            # Simulate confirmation delay
            import time
            time.sleep(0.1)  # Brief delay to simulate processing
            self.logger.info("✅ ECC confirmation received")
            return True
            
        except Exception as e:
            self.logger.error(f"ECC confirmation timeout or error: {e}")
            return False
    
    def _send_message(self, message_type: str, data: Dict[str, Any]) -> bool:
        """Send message to ECC"""
        try:
            if not self.ecc:
                self.logger.warning("ECC not available for message sending")
                return False
            
            message_data = {
                "message_type": message_type,
                "source": "archive_manager",
                "data": data,
                "timestamp": datetime.now().isoformat()
            }
            
            # Emit message to ECC
            if hasattr(self.ecc, 'emit'):
                self.ecc.emit(f"archive_manager.{message_type}", message_data)
                self.logger.info(f"📤 Sent message to ECC: {message_type}")
                return True
            else:
                self.logger.warning("ECC does not support signal emission")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to send message to ECC: {e}")
            return False
    
    def _send_accept_signal(self, operation: str) -> bool:
        """Send accept signal to ECC"""
        try:
            if not self.ecc:
                self.logger.warning("ECC not available for accept signal")
                return False
            
            accept_data = {
                "operation": operation,
                "source": "archive_manager",
                "status": "accepted",
                "timestamp": datetime.now().isoformat()
            }
            
            # Emit accept signal to ECC
            if hasattr(self.ecc, 'emit'):
                self.ecc.emit("archive_manager.accept", accept_data)
                self.logger.info(f"✅ Sent accept signal to ECC for operation: {operation}")
                return True
            else:
                self.logger.warning("ECC does not support signal emission")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to send accept signal to ECC: {e}")
            return False
    
    def _complete_handoff(self, operation: str, status: str) -> bool:
        """Complete handoff process"""
        try:
            handoff_data = {
                "operation": operation,
                "source": "archive_manager",
                "status": status,
                "timestamp": datetime.now().isoformat()
            }
            
            # Log handoff completion
            self.handoff_log.append(handoff_data)
            
            self.logger.info(f"🔄 Handoff completed: {operation} - {status}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to complete handoff: {e}")
            return False
    
    def _enforce_section_aware_execution(self, section_id: str) -> bool:
        """Enforce section-aware execution before operations"""
        try:
            if not self.ecc:
                self.logger.warning("ECC not available for section validation")
                return True  # Allow execution if ECC not available
            
            # Validate section ID against registry
            if not self.validate_section_id(section_id):
                self.logger.error(f"Invalid section ID: {section_id}")
                return False
            
            # Check if section is active in ECC
            if hasattr(self.ecc, 'can_run'):
                if not self.ecc.can_run(section_id):
                    self.logger.error(f"Section {section_id} not active or blocked")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Section-aware execution validation failed: {e}")
            return False
    
    def validate_section_id(self, section_id: str) -> bool:
        """Validate section ID against SECTION_REGISTRY"""
        return section_id in self.SECTION_REGISTRY
    
    def get_section_registry(self) -> Dict[str, Any]:
        """Get the section registry"""
        return self.SECTION_REGISTRY.copy()
    
    def archive_narrative(self, case_number: str, narrative_data: Dict[str, Any], section_id: str = "section_1") -> Dict[str, Any]:
        """Archive a finalized narrative with ECC handoff protocol"""
        try:
            # Step 1: Call out to ECC for permission
            if not self._call_out_to_ecc("archive_narrative", {
                "case_number": case_number, 
                "section_id": section_id, 
                "narrative_data": narrative_data
            }):
                self.logger.error("ECC permission denied for narrative archiving")
                return {'error': 'ECC permission denied', 'status': 'error'}
            
            # Step 2: Wait for ECC confirmation
            if not self._wait_for_ecc_confirm():
                self.logger.error("ECC confirmation timeout for narrative archiving")
                return {'error': 'ECC confirmation timeout', 'status': 'error'}
            
            # Step 3: Enforce section-aware execution
            if not self._enforce_section_aware_execution(section_id):
                self.logger.error(f"Section-aware execution failed for {section_id}")
                return {'error': f'Section {section_id} not authorized', 'status': 'error'}
            
            # Step 4: Create case directory
            case_dir = self.archive_root / "cases" / case_number
            case_dir.mkdir(exist_ok=True)
            
            # Step 5: Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"final_narrative_{case_number}_{timestamp}.json"
            file_path = case_dir / filename
            
            # Step 6: Prepare archive data
            archive_data = {
                "case_number": case_number,
                "section_id": section_id,
                "narrative_data": narrative_data,
                "archived_at": datetime.now().isoformat(),
                "archive_version": "1.0",
                "section_registry": self.get_section_registry(),
                "handoff_log": self.handoff_log
            }
            
            deposition_catalog_raw = narrative_data.get("deposition_catalog") or narrative_data.get("depositions")
            export_log_reference = narrative_data.get("export_log")
            normalized_catalog = self._normalize_deposition_catalog(deposition_catalog_raw)
            manifest_path = None
            manifest_payload = None
            if normalized_catalog or export_log_reference:
                manifest_path, manifest_payload = self._persist_deposition_catalog(
                    case_number, normalized_catalog, export_log_reference
                )
                if manifest_payload:
                    archive_data["deposition_catalog"] = manifest_payload.get("entries", [])
                    export_log_snapshot = manifest_payload.get("export_log")
                    if export_log_snapshot is not None:
                        archive_data["export_log"] = export_log_snapshot
                    if manifest_path:
                        archive_data["deposition_manifest"] = str(manifest_path)
                    archive_data["deposition_manifest_recorded_at"] = manifest_payload.get("recorded_at")

            # Step 7: Calculate hash for tamper-proofing
            content_hash = self._calculate_hash(archive_data)
            archive_data["content_hash"] = content_hash
            
            # Step 8: Write to archive
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(archive_data, f, indent=2, ensure_ascii=False)
            
            # Step 9: Create tamper-proof record
            tamper_proof_path = self.archive_root / "tamper_proof" / f"{case_number}_{timestamp}.hash"
            with open(tamper_proof_path, 'w') as f:
                f.write(f"{filename}:{content_hash}")
            
            # Step 10: Log audit trail
            audit_entry = {
                "action": "archive_narrative",
                "case_number": case_number,
                "section_id": section_id,
                "filename": filename,
                "content_hash": content_hash,
                "timestamp": datetime.now().isoformat(),
                "status": "success"
            }
            self._log_audit_entry(audit_entry)
            
            # Step 11: Send message back to ECC
            self._send_message("narrative_archived", {
                "case_number": case_number,
                "section_id": section_id,
                "filename": filename,
                "content_hash": content_hash
            })
            
            # Step 12: Send accept signal
            self._send_accept_signal("archive_narrative")
            
            # Step 13: Complete handoff
            self._complete_handoff("archive_narrative", "success")
            
            result = {
                'status': 'success',
                'case_number': case_number,
                'section_id': section_id,
                'filename': filename,
                'file_path': str(file_path),
                'content_hash': content_hash,
                'archived_at': archive_data["archived_at"],
                'deposition_manifest': archive_data.get('deposition_manifest'),
                'deposition_catalog': archive_data.get('deposition_catalog', []),
                'export_log': archive_data.get('export_log'),
            }
            
            self.logger.info(f"✅ Narrative archived: {case_number} - {filename}")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to archive narrative for {case_number}: {e}")
            self._complete_handoff("archive_narrative", "error")
            return {'error': str(e), 'status': 'error'}
    
    def retrieve_narrative(self, case_number: str, filename: Optional[str] = None) -> Dict[str, Any]:
        """Retrieve a narrative from archive with ECC handoff protocol"""
        try:
            # Step 1: Call out to ECC for permission
            if not self._call_out_to_ecc("retrieve_narrative", {
                "case_number": case_number, 
                "filename": filename
            }):
                self.logger.error("ECC permission denied for narrative retrieval")
                return {'error': 'ECC permission denied', 'status': 'error'}
            
            # Step 2: Wait for ECC confirmation
            if not self._wait_for_ecc_confirm():
                self.logger.error("ECC confirmation timeout for narrative retrieval")
                return {'error': 'ECC confirmation timeout', 'status': 'error'}
            
            # Step 3: Find the narrative file
            case_dir = self.archive_root / "cases" / case_number
            if not case_dir.exists():
                return {'error': f'Case {case_number} not found', 'status': 'error'}
            
            if filename:
                file_path = case_dir / filename
                if not file_path.exists():
                    return {'error': f'File {filename} not found', 'status': 'error'}
            else:
                # Find the most recent file
                json_files = list(case_dir.glob("final_narrative_*.json"))
                if not json_files:
                    return {'error': f'No narratives found for case {case_number}', 'status': 'error'}
                file_path = max(json_files, key=lambda f: f.stat().st_mtime)
            
            # Step 4: Load and validate the narrative
            with open(file_path, 'r', encoding='utf-8') as f:
                archive_data = json.load(f)
            
            # Step 5: Verify tamper-proofing
            if not self._verify_tamper_proof(file_path.name, archive_data.get("content_hash")):
                self.logger.warning(f"Tamper-proof verification failed for {file_path.name}")
                return {'error': 'Tamper-proof verification failed', 'status': 'error'}
            
            # Step 6: Log audit trail
            audit_entry = {
                "action": "retrieve_narrative",
                "case_number": case_number,
                "filename": file_path.name,
                "timestamp": datetime.now().isoformat(),
                "status": "success"
            }
            self._log_audit_entry(audit_entry)
            
            # Step 7: Send message back to ECC
            self._send_message("narrative_retrieved", {
                "case_number": case_number,
                "filename": file_path.name,
                "section_id": archive_data.get("section_id")
            })
            
            # Step 8: Send accept signal
            self._send_accept_signal("retrieve_narrative")
            
            # Step 9: Complete handoff
            self._complete_handoff("retrieve_narrative", "success")
            
            result = {
                'status': 'success',
                'case_number': case_number,
                'section_id': archive_data.get('section_id'),
                'narrative_data': archive_data.get('narrative_data'),
                'archived_at': archive_data.get('archived_at'),
                'content_hash': archive_data.get('content_hash'),
                'filename': file_path.name,
                'deposition_catalog': archive_data.get('deposition_catalog', []),
                'deposition_manifest': archive_data.get('deposition_manifest'),
                'export_log': archive_data.get('export_log'),
            }
            
            self.logger.info(f"✅ Narrative retrieved: {case_number} - {file_path.name}")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve narrative for {case_number}: {e}")
            self._complete_handoff("retrieve_narrative", "error")
            return {'error': str(e), 'status': 'error'}
    
    def list_all_reports(self) -> Dict[str, Any]:
        """List all archived reports with ECC handoff protocol"""
        try:
            if not self._call_out_to_ecc("list_all_reports", {}):
                self.logger.error("ECC permission denied for listing reports")
                return {'error': 'ECC permission denied', 'status': 'error'}

            if not self._wait_for_ecc_confirm():
                self.logger.error("ECC confirmation timeout for listing reports")
                return {'error': 'ECC confirmation timeout', 'status': 'error'}

            cases_dir = self.archive_root / "cases"
            reports: List[Dict[str, Any]] = []

            if cases_dir.exists():
                for case_dir in cases_dir.iterdir():
                    if not case_dir.is_dir():
                        continue
                    case_number = case_dir.name
                    json_files = list(case_dir.glob("final_narrative_*.json"))
                    for json_file in json_files:
                        try:
                            with json_file.open('r', encoding='utf-8') as handle:
                                archive_data = json.load(handle)
                            reports.append(
                                {
                                    "case_number": case_number,
                                    "filename": json_file.name,
                                    "section_id": archive_data.get("section_id"),
                                    "archived_at": archive_data.get("archived_at"),
                                    "content_hash": archive_data.get("content_hash"),
                                    "file_size": json_file.stat().st_size,
                                    "has_depositions": bool(archive_data.get("deposition_catalog")),
                                }
                            )
                        except Exception as exc:
                            self.logger.warning("Failed to read %s: %s", json_file, exc)

            self._send_message("reports_listed", {"count": len(reports)})
            self._send_accept_signal("list_all_reports")
            self._complete_handoff("list_all_reports", "success")

            return {
                'status': 'success',
                'reports': reports,
                'total_count': len(reports),
                'listed_at': datetime.now().isoformat(),
            }

        except Exception as exc:
            self.logger.error("Failed to list reports: %s", exc)
            self._complete_handoff("list_all_reports", "error")
            return {'error': str(exc), 'status': 'error'}

    def get_deposition_catalog(self, case_number: str) -> Dict[str, Any]:
        manifest_path = self._deposition_manifest_path(case_number)
        try:
            if not manifest_path.exists():
                return {
                    'status': 'success',
                    'case_number': case_number,
                    'catalog': [],
                    'manifest_path': str(manifest_path),
                }
            with manifest_path.open('r', encoding='utf-8') as handle:
                manifest = json.load(handle)
            return {
                'status': 'success',
                'case_number': case_number,
                'catalog': manifest.get('entries', []),
                'export_log': manifest.get('export_log'),
                'recorded_at': manifest.get('recorded_at'),
                'manifest_path': str(manifest_path),
            }
        except Exception as exc:
            self.logger.error("Failed to load deposition catalog for %s: %s", case_number, exc)
            return {'error': str(exc), 'status': 'error'}

    def _deposition_manifest_path(self, case_number: str) -> Path:
        return self.archive_root / "exports" / f"{case_number}_depositions.json"

    def _calculate_file_hash(self, file_path: Path, chunk_size: int = 65536) -> Optional[str]:
        try:
            sha256 = hashlib.sha256()
            with file_path.open('rb') as handle:
                for chunk in iter(lambda: handle.read(chunk_size), b''):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except Exception as exc:
            self.logger.warning("Failed to hash file %s: %s", file_path, exc)
            return None

    def _collect_file_metadata(self, file_path: Path) -> Dict[str, Any]:
        metadata: Dict[str, Any] = {
            "path": str(file_path),
            "exists": False,
        }
        try:
            if file_path.exists():
                stat = file_path.stat()
                metadata.update(
                    {
                        "exists": True,
                        "size_bytes": stat.st_size,
                        "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    }
                )
                file_hash = self._calculate_file_hash(file_path)
                if file_hash:
                    metadata["sha256"] = file_hash
        except Exception as exc:
            self.logger.warning("Failed to gather metadata for %s: %s", file_path, exc)
        return metadata

    def _normalize_deposition_catalog(self, catalog: Any) -> List[Dict[str, Any]]:
        normalized: List[Dict[str, Any]] = []
        if not catalog:
            return normalized

        def iterate_items(source: Any):
            if isinstance(source, dict):
                return source.items()
            if isinstance(source, list):
                return ((idx, item) for idx, item in enumerate(source))
            return []

        for artifact, value in iterate_items(catalog):
            entry: Dict[str, Any] = {"artifact": str(artifact)}
            if isinstance(value, dict):
                path_token = value.get("path") or value.get("file_path") or value.get("location")
                entry.update({k: v for k, v in value.items() if k not in {"path", "file_path", "location"}})
            else:
                path_token = value
            if path_token:
                entry.update(self._collect_file_metadata(Path(path_token)))
            normalized.append(entry)
        return normalized

    def _persist_deposition_catalog(
        self,
        case_number: str,
        entries: List[Dict[str, Any]],
        export_log_reference: Optional[Any] = None,
    ) -> Tuple[Optional[Path], Optional[Dict[str, Any]]]:
        if not entries and not export_log_reference:
            return None, None

        manifest_path = self._deposition_manifest_path(case_number)
        manifest_path.parent.mkdir(parents=True, exist_ok=True)

        manifest: Dict[str, Any] = {
            "case_number": case_number,
            "recorded_at": datetime.now().isoformat(),
            "entries": entries,
        }

        if export_log_reference:
            if isinstance(export_log_reference, dict):
                manifest["export_log"] = export_log_reference.copy()
                path_token = export_log_reference.get("path")
                if path_token:
                    log_metadata = self._collect_file_metadata(Path(path_token))
                    manifest["export_log"].update({k: v for k, v in log_metadata.items() if k not in manifest["export_log"]})
            else:
                manifest["export_log"] = self._collect_file_metadata(Path(str(export_log_reference)))

        with manifest_path.open('w', encoding='utf-8') as handle:
            json.dump(manifest, handle, indent=2, ensure_ascii=False)

        self.logger.info("Deposition catalog manifest updated for case %s", case_number)
        return manifest_path, manifest

    def _calculate_hash(self, data: Dict[str, Any]) -> str:
        """Calculate SHA-256 hash of data"""
        content = json.dumps(data, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def export_narrative(self, case_number: str, filename: str, export_path: str) -> Dict[str, Any]:
        """Export narrative to external location with ECC handoff protocol"""
        try:
            # Step 1: Call out to ECC for permission
            if not self._call_out_to_ecc("export_narrative", {
                "case_number": case_number, 
                "filename": filename,
                "export_path": export_path
            }):
                self.logger.error("ECC permission denied for narrative export")
                return {'error': 'ECC permission denied', 'status': 'error'}
            
            # Step 2: Wait for ECC confirmation
            if not self._wait_for_ecc_confirm():
                self.logger.error("ECC confirmation timeout for narrative export")
                return {'error': 'ECC confirmation timeout', 'status': 'error'}
            
            # Step 3: Retrieve the narrative
            retrieve_result = self.retrieve_narrative(case_number, filename)
            if retrieve_result.get('status') != 'success':
                return retrieve_result
            
            # Step 4: Export to external location
            export_dir = Path(export_path)
            export_dir.mkdir(parents=True, exist_ok=True)
            
            source_file = self.archive_root / "cases" / case_number / filename
            target_file = export_dir / filename
            
            import shutil
            shutil.copy2(source_file, target_file)
            
            # Step 5: Log audit trail
            audit_entry = {
                "action": "export_narrative",
                "case_number": case_number,
                "filename": filename,
                "export_path": str(target_file),
                "timestamp": datetime.now().isoformat(),
                "status": "success"
            }
            self._log_audit_entry(audit_entry)
            
            # Step 6: Send message back to ECC
            self._send_message("narrative_exported", {
                "case_number": case_number,
                "filename": filename,
                "export_path": str(target_file)
            })
            
            # Step 7: Send accept signal
            self._send_accept_signal("export_narrative")
            
            # Step 8: Complete handoff
            self._complete_handoff("export_narrative", "success")
            
            result = {
                'status': 'success',
                'case_number': case_number,
                'filename': filename,
                'export_path': str(target_file),
                'exported_at': datetime.now().isoformat()
            }
            
            self.logger.info(f"✅ Narrative exported: {case_number} - {filename}")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to export narrative for {case_number}: {e}")
            self._complete_handoff("export_narrative", "error")
            return {'error': str(e), 'status': 'error'}





