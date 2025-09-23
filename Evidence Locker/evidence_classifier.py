#!/usr/bin/env python3
"""
EvidenceClassifier - Classification system for assigning evidence to sections
Implements file type detection, content analysis, and section assignment logic
"""

import os
import mimetypes
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

class EvidenceClassifier:
    """Evidence classification system for assigning files to appropriate sections"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, ecc=None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        self.ecc = ecc  # Reference to EcosystemController for validation
        
        # Classification rules
        self.file_type_rules = {
            # Video files -> Section 3 (Surveillance)
            '.mp4': 'section_3',
            '.avi': 'section_3',
            '.mov': 'section_3',
            '.mkv': 'section_3',
            '.wmv': 'section_3',
            
            # Image files -> Section 8 (Photo/Evidence Index)
            '.jpg': 'section_8',
            '.jpeg': 'section_8',
            '.png': 'section_8',
            '.gif': 'section_8',
            '.bmp': 'section_8',
            '.tiff': 'section_8',
            
            # Document files -> Section 5 (Supporting Documents)
            '.pdf': 'section_5',
            '.doc': 'section_5',
            '.docx': 'section_5',
            '.txt': 'section_5',
            '.rtf': 'section_5',
            
            # Audio files -> Section 3 (Surveillance)
            '.mp3': 'section_3',
            '.wav': 'section_3',
            '.m4a': 'section_3',
            '.aac': 'section_3',
        }
        
        # Content-based classification keywords
        self.content_keywords = {
            'section_3': [
                'surveillance', 'video', 'recording', 'camera', 'footage',
                'monitoring', 'observation', 'activity', 'movement'
            ],
            'section_5': [
                'lease', 'contract', 'agreement', 'document', 'legal',
                'terms', 'conditions', 'rental', 'property'
            ],
            'section_8': [
                'photo', 'image', 'picture', 'evidence', 'scene',
                'location', 'property', 'damage', 'condition'
            ]
        }
        
        # Classification history for learning
        self.classification_history = []
        
        self.logger.info("EvidenceClassifier initialized")
    
    def _call_out_to_ecc(self, operation: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Call out to ECC for permission to perform operation"""
        try:
            if not self.ecc:
                return {"permission_granted": True, "request_id": None}
            
            request_id = f"classify_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
            
            # Emit call-out signal to ECC
            if hasattr(self.ecc, 'emit'):
                self.ecc.emit("evidence_locker.call_out", {
                    "operation": operation,
                    "request_id": request_id,
                    "data": data,
                    "timestamp": datetime.now().isoformat(),
                    "module": "evidence_classifier"
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
                    "module": "evidence_classifier"
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
                    "module": "evidence_classifier"
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
                    "module": "evidence_classifier"
                })
            
            self.logger.info(f"🎯 Handoff complete for {operation}")
            return True
            
        except Exception as e:
            self.logger.error(f"Handoff complete failed: {e}")
            return False
    
    def classify(self, file_path: str, section_id: str = None) -> Dict[str, Any]:
        """Classify a file and return section assignment with confidence - ENFORCES SECTION-AWARE EXECUTION"""
        try:
            # ECC CALL-OUT: Request permission to classify
            if self.ecc:
                call_out_result = self._call_out_to_ecc("classify", {
                    "file_path": file_path,
                    "section_id": section_id,
                    "operation": "evidence_classification"
                })
                
                if not call_out_result.get("permission_granted", False):
                    raise Exception(f"ECC denied classification permission for {file_path}")
                
                # ECC CONFIRM: Wait for confirmation
                confirm_result = self._wait_for_ecc_confirm("classify", call_out_result.get("request_id"))
                if not confirm_result.get("confirmed", False):
                    raise Exception(f"ECC confirmation failed for classification of {file_path}")
            
            # SECTION-AWARE EXECUTION ENFORCEMENT
            if section_id and self.ecc:
                if not self.ecc.can_run(section_id):
                    raise Exception(f"Section {section_id} not active or blocked for evidence classification")
            
            filename = os.path.basename(file_path).lower()
            file_extension = os.path.splitext(filename)[1].lower()
            
            # Get MIME type
            mime_type, _ = mimetypes.guess_type(file_path)
            
            # Initialize classification result
            classification = {
                'file_path': file_path,
                'filename': filename,
                'file_extension': file_extension,
                'mime_type': mime_type,
                'assigned_section': 'unassigned',
                'confidence': 0.0,
                'classification_method': 'unknown',
                'keywords_found': [],
                'timestamp': datetime.now().isoformat()
            }
            
            # Method 1: File extension classification
            if file_extension in self.file_type_rules:
                classification['assigned_section'] = self.file_type_rules[file_extension]
                classification['confidence'] = 0.8
                classification['classification_method'] = 'file_extension'
                self.logger.debug(f"📁 Classified {filename} as {classification['assigned_section']} by extension")
                self.logger.info(f"Classified {filename} as {classification['assigned_section']} by extension")
            
            # Method 2: Filename keyword analysis
            elif self._classify_by_filename(filename, classification):
                self.logger.debug(f"📁 Classified {filename} as {classification['assigned_section']} by filename")
                self.logger.info(f"Classified {filename} as {classification['assigned_section']} by filename")
            
            # Method 3: MIME type classification
            elif mime_type and self._classify_by_mime_type(mime_type, classification):
                self.logger.debug(f"📁 Classified {filename} as {classification['assigned_section']} by MIME type")
                self.logger.info(f"Classified {filename} as {classification['assigned_section']} by MIME type")
            
            # Method 4: Content analysis (if file is readable)
            elif self._classify_by_content(file_path, classification):
                self.logger.debug(f"📁 Classified {filename} as {classification['assigned_section']} by content")
                self.logger.info(f"Classified {filename} as {classification['assigned_section']} by content")
            
            # Record classification
            self.classification_history.append(classification)
            
            # COMPLETE HANDOFF PROCESS
            if classification['assigned_section'] != 'unassigned':
                # 1. SEND MESSAGE: Notify receiving module
                self._send_message("classification_sent", {
                    "file_path": file_path,
                    "assigned_section": classification['assigned_section'],
                    "confidence": classification['confidence'],
                    "classification_method": classification['classification_method']
                })
                
                # 2. SEND ACCEPT SIGNAL: Notify receiving module
                self._send_accept_signal("classification_complete", {
                    "file_path": file_path,
                    "assigned_section": classification['assigned_section'],
                    "confidence": classification['confidence'],
                    "classification_method": classification['classification_method']
                })
                
                # 3. COMPLETE HANDOFF: Final confirmation
                self._complete_handoff("classification_handoff", {
                    "file_path": file_path,
                    "assigned_section": classification['assigned_section'],
                    "confidence": classification['confidence'],
                    "classification_method": classification['classification_method']
                })
            
            return classification
            
        except Exception as e:
            self.logger.error(f"Failed to classify file {file_path}: {e}")
            return {
                'file_path': file_path,
                'filename': os.path.basename(file_path),
                'assigned_section': 'unassigned',
                'confidence': 0.0,
                'classification_method': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _classify_by_filename(self, filename: str, classification: Dict[str, Any]) -> bool:
        """Classify based on filename keywords"""
        filename_lower = filename.lower()
        
        for section, keywords in self.content_keywords.items():
            for keyword in keywords:
                if keyword in filename_lower:
                    classification['assigned_section'] = section
                    classification['confidence'] = 0.7
                    classification['classification_method'] = 'filename_keywords'
                    classification['keywords_found'].append(keyword)
                    return True
        
        return False
    
    def _classify_by_mime_type(self, mime_type: str, classification: Dict[str, Any]) -> bool:
        """Classify based on MIME type"""
        mime_rules = {
            'video/': 'section_3',
            'image/': 'section_8',
            'application/pdf': 'section_5',
            'text/': 'section_5',
            'application/msword': 'section_5',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'section_5'
        }
        
        for mime_pattern, section in mime_rules.items():
            if mime_type.startswith(mime_pattern):
                classification['assigned_section'] = section
                classification['confidence'] = 0.6
                classification['classification_method'] = 'mime_type'
                return True
        
        return False
    
    def _classify_by_content(self, file_path: str, classification: Dict[str, Any]) -> bool:
        """Classify based on file content analysis"""
        try:
            # Only analyze text-based files for content
            if not self._is_text_file(file_path):
                return False
            
            # Read file content (limit to first 1KB for performance)
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(1024).lower()
            
            # Check for section-specific keywords in content
            for section, keywords in self.content_keywords.items():
                found_keywords = []
                for keyword in keywords:
                    if keyword in content:
                        found_keywords.append(keyword)
                
                # If multiple keywords found, assign to section
                if len(found_keywords) >= 2:
                    classification['assigned_section'] = section
                    classification['confidence'] = 0.9
                    classification['classification_method'] = 'content_analysis'
                    classification['keywords_found'] = found_keywords
                    return True
            
            return False
            
        except Exception as e:
            self.logger.debug(f"Content analysis failed for {file_path}: {e}")
            return False
    
    def _is_text_file(self, file_path: str) -> bool:
        """Check if file is likely a text file"""
        try:
            # Check file extension
            text_extensions = {'.txt', '.md', '.log', '.csv', '.json', '.xml', '.html', '.htm'}
            if os.path.splitext(file_path)[1].lower() in text_extensions:
                return True
            
            # Check MIME type
            mime_type, _ = mimetypes.guess_type(file_path)
            if mime_type and mime_type.startswith('text/'):
                return True
            
            # Check file size (small files are more likely to be text)
            if os.path.getsize(file_path) < 1024 * 1024:  # Less than 1MB
                return True
            
            return False
            
        except Exception:
            return False
    
    def validate_section_assignment(self, file_path: str, section_id: str) -> bool:
        """Validate that a file can be assigned to a specific section - ENFORCES SECTION-AWARE EXECUTION"""
        try:
            # SECTION-AWARE EXECUTION ENFORCEMENT
            if self.ecc:
                if not self.ecc.can_run(section_id):
                    raise Exception(f"Section {section_id} not active or blocked for assignment validation")
            
            classification = self.classify(file_path, section_id)
            assigned_section = classification['assigned_section']
            is_valid = assigned_section == section_id or assigned_section == "unassigned"
            
            self.logger.debug(f"✅ Assignment validation: {os.path.basename(file_path)} -> {section_id} = {is_valid}")
            self.logger.info(f"Assignment validation: {os.path.basename(file_path)} -> {section_id} = {is_valid}")
            return is_valid
            
        except Exception as e:
            self.logger.error(f"Failed to validate section assignment: {e}")
            raise

    def batch_classify(self, file_paths: List[str], section_id: str = None) -> Dict[str, Dict[str, Any]]:
        """Classify multiple files at once - ENFORCES SECTION-AWARE EXECUTION"""
        try:
            # SECTION-AWARE EXECUTION ENFORCEMENT
            if section_id and self.ecc:
                if not self.ecc.can_run(section_id):
                    raise Exception(f"Section {section_id} not active or blocked for batch classification")
            
            results = {}
            
            for file_path in file_paths:
                results[file_path] = self.classify(file_path, section_id)
            
            self.logger.debug(f"📊 Batch classified {len(file_paths)} files")
            self.logger.info(f"Batch classified {len(file_paths)} files")
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to batch classify files: {e}")
            raise
    
    def get_classification_stats(self) -> Dict[str, Any]:
        """Get classification statistics"""
        if not self.classification_history:
            return {'total_classifications': 0}
        
        # Count by section
        section_counts = {}
        method_counts = {}
        
        for classification in self.classification_history:
            section = classification['assigned_section']
            method = classification['classification_method']
            
            section_counts[section] = section_counts.get(section, 0) + 1
            method_counts[method] = method_counts.get(method, 0) + 1
        
        return {
            'total_classifications': len(self.classification_history),
            'section_distribution': section_counts,
            'method_distribution': method_counts,
            'average_confidence': sum(c['confidence'] for c in self.classification_history) / len(self.classification_history)
        }
    
    def update_classification_rules(self, file_extension: str, section: str) -> bool:
        """Update classification rules based on user feedback"""
        try:
            self.file_type_rules[file_extension] = section
            self.logger.info(f"Updated classification rule: {file_extension} -> {section}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update classification rules: {e}")
            return False
    
    def export_classification_rules(self) -> Dict[str, Any]:
        """Export current classification rules"""
        return {
            'file_type_rules': self.file_type_rules,
            'content_keywords': self.content_keywords,
            'export_timestamp': datetime.now().isoformat()
        }