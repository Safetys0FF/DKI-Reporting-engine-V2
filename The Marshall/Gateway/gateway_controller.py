#!/usr/bin/env python3
"""
Gateway Controller - Main orchestrator for the DKI Engine reporting system
Manages section-by-section processing, signal handling, and report flow control
Integrated with media processing engine for comprehensive evidence handling
"""

import logging
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
import threading
import time

# Add Tools directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'Tools'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'Processors'))

# Import section renderers
from section_1_gateway import Section1Renderer
from section_2_renderer import Section2Renderer  
from section_3_renderer import Section3Renderer
from section_4_renderer import Section4Renderer
from section_5_renderer import Section5Renderer
from section_6_renderer import Section6BillingRenderer
from section_7_renderer import Section7Renderer
from section_8_renderer import Section8Renderer
from section_9_renderer import Section9Renderer
from section_toc_renderer import SectionTOCRenderer
from section_cp_renderer import SectionCPRenderer
from master_toolkit_engine import MasterToolKitEngine
from final_assembly import FinalAssemblyManager

# Import media processing engine
from media_processing_engine import MediaProcessingEngine, MediaAnalysisTool

logger = logging.getLogger(__name__)

class SignalType(Enum):
    """Gateway signal types for section communication"""
    APPROVED = "10-4"           # Section approved
    REVISION_REQUIRED = "10-9"  # Needs revision  
    HALT = "10-10"             # Emergency halt
    TOOLKIT_READY = "10-6"     # Toolkit dispatched
    SECTION_COMPLETE = "10-8"  # Section reporting complete
    FINAL_APPROVED = "10-99"   # Final report approved
    
    # Media processing signals
    MEDIA_PROCESSING_START = "MEDIA_START"
    MEDIA_PROCESSING_COMPLETE = "MEDIA_COMPLETE"
    MEDIA_ANALYSIS_READY = "MEDIA_ANALYSIS_READY"

class SectionState(Enum):
    """Section processing states"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    APPROVED = "approved"
    REVISION_REQUIRED = "revision_required"
    FAILED = "failed"

class GatewayController:
    """Main gateway controller for orchestrating the investigation reporting process"""
    
    def __init__(self):
        self.report_types = {
            "Investigative": {
                "sections": [
                    ("section_cp", "Cover Page"),
                    ("section_toc", "Table of Contents"),
                    ("section_1", "Investigation Objectives"),
                    ("section_2", "Investigation Requirements"),
                    ("section_3", "Investigation Details"),
                    ("section_4", "Review of Details"),
                    ("section_5", "Review of Supporting Documents"),
                    ("section_6", "Billing Summary"),
                    ("section_7", "Conclusion"),
                    ("section_8", "Investigation Evidence Review"),
                    ("section_9", "Certification & Disclaimers"),
                    ("section_dp", "Disclosure Page"),
                    ("section_fr", "Final Report Assembly")
                ]
            },
            "Surveillance": {
                "sections": [
                    ("section_cp", "Cover Page"),
                    ("section_toc", "Table of Contents"),
                    ("section_1", "Surveillance Objectives"),
                    ("section_2", "Pre-Surveillance Planning"),
                    ("section_3", "Daily Logs"),
                    ("section_4", "Review of Surveillance Sessions"),
                    ("section_5", "Review of Supporting Documents"),
                    ("section_6", "Billing Summary"),
                    ("section_7", "Conclusion"),
                    ("section_8", "Investigation Evidence Review"),
                    ("section_9", "Certification & Disclaimers"),
                    ("section_dp", "Disclosure Page"),
                    ("section_fr", "Final Report Assembly")
                ]
            },
            "Hybrid": {
                "sections": [
                    ("section_cp", "Cover Page"),
                    ("section_toc", "Table of Contents"),
                    ("section_1", "Investigation Objectives"),
                    ("section_2", "Preliminary Case Review"),
                    ("section_3", "Investigative Details"),
                    ("section_4", "Review of Surveillance Sessions"),
                    ("section_5", "Review of Supporting Documents"),
                    ("section_6", "Billing Summary"),
                    ("section_7", "Conclusion"),
                    ("section_8", "Investigation Evidence Review"),
                    ("section_9", "Certification & Disclaimers"),
                    ("section_dp", "Disclosure Page"),
                    ("section_fr", "Final Report Assembly")
                ]
            }
        }
        
        # Initialize section renderers
        self.section_renderers = {
            "section_cp": SectionCPRenderer(),
            "section_toc": SectionTOCRenderer(),
            "section_1": Section1Renderer(),
            "section_2": Section2Renderer(),
            "section_3": Section3Renderer(),
            "section_4": Section4Renderer(),
            "section_5": Section5Renderer(),
            "section_6": Section6BillingRenderer(),
            "section_7": Section7Renderer(),
            "section_8": Section8Renderer(),
            "section_9": Section9Renderer(),
        }
        
        # Initialize toolkit engine
        self.toolkit_engine = MasterToolKitEngine()
        
        # Initialize media processing engine
        self.media_engine = MediaProcessingEngine()
        self.media_analysis_tool = MediaAnalysisTool(self.media_engine)
        
        # Initialize final assembly manager (receives approved sections)
        self.final_assembly = FinalAssemblyManager()
        
        # Gateway state
        self.current_report_type = None
        self.current_case_data = {}
        self.section_states = {}
        self.section_outputs = {}
        self.processing_log = []
        self.signal_queue = []
        self.is_frozen = False
        
        # Per-case lookup/result cache to avoid redundant external calls across sections
        self.lookup_cache: Dict[str, Any] = {}
        self.last_processed_data: Dict[str, Any] = {}
        
        # Media processing state
        self.media_processing_queue: List[str] = []
        self.media_results_cache: Dict[str, Dict[str, Any]] = {}
        self.media_processing_active = False
        
        # Threading
        self.signal_lock = threading.Lock()
        self.media_lock = threading.Lock()
        
        logger.info("Gateway Controller initialized with media processing capabilities")
    
    def initialize_case(self, report_type: Optional[str], case_data: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize a new case with specified (or inferred) report type and data.
        If report_type is None or 'auto', infer from case_data and fallback logic.
        Accepts alias mapping where 'Field' is treated as 'Surveillance'.
        """

        normalized = self._normalize_report_type(report_type)
        if normalized is None:
            inferred = self._infer_report_type(case_data)
            normalized = inferred
            self.processing_log.append({
                'timestamp': datetime.now().isoformat(),
                'action': 'report_type_inferred',
                'report_type': normalized
            })

        if normalized not in self.report_types:
            raise ValueError(f"Unsupported report type: {report_type}")

        self.current_report_type = normalized
        self.current_case_data = case_data.copy()
        
        # Initialize section states
        sections = self.report_types[normalized]["sections"]
        self.section_states = {
            section_id: SectionState.PENDING 
            for section_id, _ in sections
        }
        self.section_outputs = {}
        self.lookup_cache = {}
        
        # Clear media processing state
        with self.media_lock:
            self.media_processing_queue.clear()
            self.media_results_cache.clear()
            self.media_processing_active = False
        
        # Generate case ID if not provided
        if 'case_id' not in self.current_case_data:
            self.current_case_data['case_id'] = self._generate_case_id()
        
        # Inject client_profile from signed-in user's profile (agency + investigator defaults)
        try:
            upm = getattr(self.toolkit_engine, 'user_profile_manager', None)
            if upm and upm.is_authenticated():
                merged = self._build_client_profile_from_user(upm, self.current_case_data.get('client_profile', {}))
                self.current_case_data['client_profile'] = merged
                # Enforce investigator license presence
                inv_lic = (merged.get('investigator_license') or '').strip()
                if not inv_lic:
                    raise ValueError("Investigator license is required to initialize a case. Please update User Profile.")
        except Exception as e:
            logger.warning(f"Client profile injection skipped: {e}")

        self.processing_log.append({
            'timestamp': datetime.now().isoformat(),
            'action': 'case_initialized',
            'report_type': normalized,
            'case_id': self.current_case_data.get('case_id')
        })
        
        logger.info(f"Case initialized: {normalized} - {self.current_case_data.get('case_id')}")
        
        return {
            'case_id': self.current_case_data.get('case_id'),
            'report_type': normalized,
            'sections': sections,
            'status': 'initialized'
        }

    def _normalize_report_type(self, report_type: Optional[str]) -> Optional[str]:
        """Normalize input report_type; map aliases and accept None/auto."""
        if not report_type:
            return None
        rt = str(report_type).strip()
        if not rt:
            return None
        if rt.lower() in { 'auto', 'autodetect', 'detect' }:
            return None
        # Alias mapping: Field => Surveillance
        if rt.lower() in { 'field' }:
            return 'Surveillance'
        # Title-case keys in self.report_types
        for k in self.report_types.keys():
            if rt.lower() == k.lower():
                return k
        return rt

    def _infer_report_type(self, case_data: Dict[str, Any]) -> str:
        """Infer report type from case_data using fallback logic cues.
        Defaults to Field≡Surveillance when ambiguous; Hybrid when both clauses present.
        """
        text_blobs = []
        for key in ('contract_type', 'contract_name', 'investigation_goals', 'goals', 'notes'):
            val = case_data.get(key)
            if isinstance(val, str):
                text_blobs.append(val.lower())
        joined = "\n".join(text_blobs)

        field_flags = set()
        inv_flags = set()

        # Clause flags
        if 'field' in joined or 'surveillance' in joined or 'in-field' in joined or case_data.get('field_work') or case_data.get('field_ops'):
            field_flags.add('field')
        if 'investigative' in joined or 'investigation' in joined or 'desk' in joined or 'background' in joined:
            inv_flags.add('investigative')

        # Explicit contract_type mapping
        ct = str(case_data.get('contract_type', '')).lower()
        if ct in {'investigative', 'investigation'}:
            inv_flags.add('explicit')
        if ct in {'field', 'surveillance'}:
            field_flags.add('explicit')
        if ct in {'hybrid'}:
            return 'Hybrid'

        # Multiple contracts
        contracts = case_data.get('contracts')
        if isinstance(contracts, list) and len(contracts) > 1:
            # Prefer Hybrid if mixed cues
            if field_flags or inv_flags:
                return 'Hybrid'

        # Decision
        if field_flags and inv_flags:
            return 'Hybrid'
        if field_flags:
            return 'Surveillance'
        if inv_flags:
            return 'Investigative'
        # Fallback default to Field≡Surveillance per fallback docs
        return 'Surveillance'

    def _build_client_profile_from_user(self, upm, current_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Merge agency-level and investigator-level settings from the signed-in user profile.
        Uses structured accessors (get_personal_info, get_business_info) for complete profile data.
        Prefers existing case client_profile values, then user settings, then config defaults (handled in renderer).
        """
        profile = dict(current_profile or {})
        try:
            # Use structured accessors instead of individual get_setting calls
            personal_info = upm.get_personal_info()
            business_info = upm.get_business_info()
            
            # Merge with preference: existing profile > user settings > defaults
            for key, value in {**personal_info, **business_info}.items():
                if not profile.get(key) and value:
                    profile[key] = value
                    
            logger.debug(f"Profile merged: {len(profile)} fields from user settings")
        except Exception as e:
            logger.warning(f"Profile merge failed: {e}")
            pass
        return profile
    
    def generate_section(self, section_name: str, processed_data: Dict[str, Any], report_type: str) -> Dict[str, Any]:
        """Generate a specific section of the report"""
        
        if self.is_frozen:
            raise RuntimeError("Gateway is frozen - cannot process sections")
        
        # Extract section ID from section name
        section_id = self._extract_section_id(section_name)
        
        if section_id not in self.section_states:
            raise ValueError(f"Unknown section: {section_name}")
        
        logger.info(f"Starting generation of {section_name} ({section_id})")
        
        # Update section state
        self.section_states[section_id] = SectionState.IN_PROGRESS

        try:
            # Track last processed data for potential auto-advance
            self.last_processed_data = processed_data or {}
            
            # Special handling for Section 8 (media evidence)
            if section_id == 'section_8':
                processed_data = self._process_media_for_section_8(processed_data)
            
            # Run toolkit analysis first
            toolkit_results = self._run_section_toolkit(section_id, processed_data)

            # Prepare section payload once (reuse for internal audits)
            section_payload = self._prepare_section_payload(section_id, processed_data, toolkit_results)
            
            # Generate section content
            section_result = self._generate_section_content(
                section_id, section_name, processed_data, toolkit_results
            )

            # Post-process: admin-only internal audits (no client-facing content changes)
            try:
                self._post_process_internal_audits(section_id, section_result, section_payload)
            except Exception:
                pass
            
            # Update section state and store output
            self.section_states[section_id] = SectionState.COMPLETED
            self.section_outputs[section_id] = section_result
            
            # Emit completion signal
            self._emit_signal(SignalType.SECTION_COMPLETE, {
                'section_id': section_id,
                'section_name': section_name,
                'status': 'completed'
            })
            
            self.processing_log.append({
                'timestamp': datetime.now().isoformat(),
                'action': 'section_generated',
                'section_id': section_id,
                'section_name': section_name
            })
            
            logger.info(f"Section {section_name} generated successfully")
            
            return section_result
            
        except Exception as e:
            # Handle section generation failure
            self.section_states[section_id] = SectionState.FAILED
            
            self.processing_log.append({
                'timestamp': datetime.now().isoformat(),
                'action': 'section_failed',
                'section_id': section_id,
                'error': str(e)
            })
            
            logger.error(f"Section generation failed for {section_name}: {str(e)}")
            
            # Emit halt signal for critical failures
            self._emit_signal(SignalType.HALT, {
                'section_id': section_id,
                'error': str(e)
            })
            
            raise
    
    def _process_media_for_section_8(self, processed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process media files specifically for Section 8 evidence review"""
        
        logger.info("Processing media files for Section 8")
        
        # Extract media files from processed data
        media_files = []
        
        # Check for images
        images = processed_data.get('images', {})
        for image_id, image_data in images.items():
            file_info = image_data.get('file_info', {})
            if file_info.get('path'):
                media_files.append(file_info['path'])
        
        # Check for videos
        videos = processed_data.get('videos', {})
        for video_id, video_data in videos.items():
            file_info = video_data.get('file_info', {})
            if file_info.get('path'):
                media_files.append(file_info['path'])
        
        # Check for audio files
        audio_entries = processed_data.get('audio', {})
        for audio_id, audio_data in audio_entries.items():
            if not isinstance(audio_data, dict):
                continue
            file_info = audio_data.get('file_info', {}) if isinstance(audio_data, dict) else {}
            audio_path = file_info.get('path') if isinstance(file_info, dict) else None
            if audio_path:
                media_files.append(audio_path)

        if not media_files:
            logger.info("No media files found for Section 8 processing")
            return processed_data
        
        try:
            # Process media files with comprehensive analysis
            media_results = self.media_engine.process_media_batch(media_files, {
                'extract_text': True,
                'detect_faces': True,
                'extract_frames': True,
                'frame_count': 5,
                'analyze_audio': True,
                'detect_motion': True
            })

            self._merge_audio_media_results(processed_data, media_results)
            
            # Perform additional analysis
            timeline_data = self.media_analysis_tool.analyze_media_timeline(media_files)
            duplicate_data = self.media_analysis_tool.detect_duplicate_media(media_files)
            geolocation_data = self.media_analysis_tool.extract_geolocation_data(media_files)
            
            # Update processed data with media analysis results
            processed_data['media_analysis'] = {
                'processing_results': media_results,
                'timeline_analysis': timeline_data,
                'duplicate_detection': duplicate_data,
                'geolocation_data': geolocation_data,
                'processed_count': len(media_results)
            }
            
            # Cache results
            with self.media_lock:
                self.media_results_cache['section_8'] = processed_data['media_analysis']
            
            # Emit media processing complete signal
            self._emit_signal(SignalType.MEDIA_PROCESSING_COMPLETE, {
                'section_id': 'section_8',
                'media_count': len(media_files),
                'analysis_complete': True
            })
            
            logger.info(f"Media processing completed for Section 8: {len(media_files)} files processed")
            
        except Exception as e:
            logger.error(f"Media processing failed for Section 8: {e}")
            # Don't fail the section generation, just log the error
            processed_data['media_analysis'] = {
                'error': str(e),
                'processed_count': 0
            }
        
        return processed_data
    
    def _merge_audio_media_results(self, processed_data: Dict[str, Any], media_results: Dict[str, Any]):
        """Merge media-engine audio results into processed data."""
        if not media_results:
            return

        audio_bucket = processed_data.setdefault('audio', {})
        files_bucket = processed_data.get('files', {})

        path_to_id: Dict[str, str] = {}
        for file_id, record in files_bucket.items():
            info = (record or {}).get('file_info', {})
            media_path = info.get('path') if isinstance(info, dict) else None
            if media_path:
                path_to_id[media_path] = file_id

        for file_id, record in audio_bucket.items():
            info = (record or {}).get('file_info', {})
            media_path = info.get('path') if isinstance(info, dict) else None
            if media_path and media_path not in path_to_id:
                path_to_id[media_path] = file_id

        for media_path, result in media_results.items():
            if not isinstance(result, dict) or result.get('file_type') != 'audio':
                continue

            entry: Dict[str, Any] = {
                'file_info': result.get('file_info'),
                'duration': result.get('duration'),
                'sample_rate': result.get('sample_rate'),
                'channels': result.get('channels'),
                'transcript': result.get('transcript'),
                'transcription': result.get('transcription'),
                'transcription_segments': result.get('transcription_segments'),
                'transcription_model': result.get('transcription_model'),
                'transcription_generated_at': result.get('transcription_generated_at'),
            }

            transcription_payload = result.get('transcription')
            if isinstance(transcription_payload, dict):
                summary = transcription_payload.get('summary') or transcription_payload.get('text')
                if summary:
                    entry['summary'] = summary

            file_id = path_to_id.get(media_path) or result.get('file_hash')
            if not file_id:
                file_info = result.get('file_info') or {}
                name = file_info.get('name') or os.path.basename(media_path)
                file_id = f"audio_{name}"
                path_to_id[media_path] = file_id

            audio_bucket[file_id] = entry

    def _build_voice_memo_entries(self, audio_entries: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create structured voice memo entries for section payloads."""
        voice_memos: List[Dict[str, Any]] = []
        for clip_id, payload in audio_entries.items():
            if not isinstance(payload, dict):
                continue
            file_info = payload.get('file_info') or {}
            name = file_info.get('name') or clip_id
            transcript = payload.get('summary') or payload.get('transcript')
            transcription_payload = payload.get('transcription') if isinstance(payload.get('transcription'), dict) else {}
            if not transcript and isinstance(transcription_payload, dict):
                transcript = transcription_payload.get('summary') or transcription_payload.get('text')
            if not transcript:
                continue

            voice_memos.append({
                'id': clip_id,
                'name': name,
                'summary': transcript.strip(),
                'language': payload.get('transcript_language') or transcription_payload.get('language'),
                'generated_at': payload.get('transcription_generated_at') or transcription_payload.get('generated_at'),
                'duration': payload.get('duration'),
                'path': file_info.get('path'),
            })

        voice_memos.sort(key=lambda entry: (entry.get('generated_at') or '', entry.get('name') or ''))
        return voice_memos


    def _run_section_toolkit(self, section_id: str, processed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run the master toolkit for a specific section"""
        
        logger.debug(f"Running toolkit analysis for {section_id}")
        
        # Prepare toolkit inputs
        text_data = self._extract_text_for_section(section_id, processed_data)
        report_meta = self._prepare_report_metadata()
        documents = processed_data.get('files', {})
        assets = processed_data.get('images', {})
        
        audio_entries = processed_data.get('audio', {})
        if audio_entries:
            voice_memos = self._build_voice_memo_entries(audio_entries)
            if voice_memos:
                payload['voice_memos'] = voice_memos

        # Include media analysis results for Section 8 without flattening into assets
        if section_id == 'section_8' and 'media_analysis' in processed_data:
            assets = dict(assets)
            assets['media_analysis'] = processed_data['media_analysis']
        
        # Run toolkit analysis
        toolkit_results = self.toolkit_engine.run_all(
            section_id=section_id,
            text_data=text_data,
            report_meta=report_meta,
            documents=documents,
            assets=assets
        )
        
        # Emit toolkit ready signal
        self._emit_signal(SignalType.TOOLKIT_READY, {
            'section_id': section_id,
            'toolkit_results': toolkit_results
        })
        
        logger.debug(f"Toolkit analysis complete for {section_id}")
        
        return toolkit_results
    
    def _generate_section_content(self, section_id: str, section_name: str, 
                                processed_data: Dict[str, Any], toolkit_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate the actual section content using the appropriate renderer"""
        
        # Prepare section payload
        section_payload = self._prepare_section_payload(section_id, processed_data, toolkit_results)
        
        # Use appropriate renderer
        if section_id in self.section_renderers:
            renderer = self.section_renderers[section_id]
            
            # Generate section using renderer
            if hasattr(renderer, 'render_model'):
                render_result = renderer.render_model(section_payload, self.current_case_data)
            else:
                # Fallback for custom renderers
                render_result = renderer.generate_section(section_payload)
            
            # Prepare final result
            result = {
                'section_id': section_id,
                'section_name': section_name,
                'content': self._format_section_content(render_result),
                'render_data': render_result,
                'toolkit_results': toolkit_results,
                'metadata': {
                    'generated_timestamp': datetime.now().isoformat(),
                    'report_type': self.current_report_type,
                    'case_id': self.current_case_data.get('case_id')
                }
            }
        else:
            # Generic section generation for sections without specific renderers
            result = self._generate_generic_section(section_id, section_name, section_payload, toolkit_results)
        
        return result
    
    def _format_section_content(self, render_result: Dict[str, Any]) -> str:
        """Format rendered section data into readable text content"""
        
        if isinstance(render_result, dict) and 'render_tree' in render_result:
            # Format structured render tree
            content_parts = []
            
            for block in render_result['render_tree']:
                if block['type'] == 'title':
                    content_parts.append(f"\n{block['text']}\n{'=' * len(block['text'])}\n")
                elif block['type'] == 'header':
                    content_parts.append(f"\n{block['text']}\n{'-' * len(block['text'])}\n")
                elif block['type'] == 'field':
                    content_parts.append(f"{block['label']}: {block['value']}")
                elif block['type'] == 'paragraph':
                    content_parts.append(f"\n{block['text']}\n")
            
            return '\n'.join(content_parts)
        
        elif isinstance(render_result, dict) and 'content' in render_result:
            return render_result['content']
        
        else:
            # Fallback formatting
            return str(render_result)
    
    def _generate_generic_section(self, section_id: str, section_name: str, 
                                section_payload: Dict[str, Any], toolkit_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a generic section for sections without specific renderers"""
        
        logger.info(f"Using generic section generation for {section_id}")
        
        # Basic section template
        content = f"{section_name.upper()}\n{'=' * len(section_name)}\n\n"
        
        # Add relevant data based on section type
        if 'extracted_text' in section_payload:
            content += "EXTRACTED INFORMATION:\n"
            for source, text in section_payload['extracted_text'].items():
                if text.strip():
                    content += f"\nFrom {source}:\n{text[:500]}...\n"
        
        # Add toolkit insights
        if toolkit_results:
            content += "\nANALYSIS RESULTS:\n"
            for tool, result in toolkit_results.items():
                if isinstance(result, dict) and result.get('status') == 'success':
                    content += f"- {tool}: {result.get('summary', 'Analysis completed')}\n"
        
        # Add case-specific information
        if self.current_case_data:
            content += "\nCASE INFORMATION:\n"
            for key, value in self.current_case_data.items():
                if key in ['client_name', 'case_id', 'investigation_goals']:
                    content += f"- {key.replace('_', ' ').title()}: {value}\n"
        
        return {
            'section_id': section_id,
            'section_name': section_name,
            'content': content,
            'toolkit_results': toolkit_results,
            'metadata': {
                'generated_timestamp': datetime.now().isoformat(),
                'generator': 'generic',
                'report_type': self.current_report_type
            }
        }
    
    def _prepare_section_payload(self, section_id: str, processed_data: Dict[str, Any], 
                               toolkit_results: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare the payload for section generation"""
        
        # Baseline, shared across all sections
        payload = {
            'section_id': section_id,
            'report_type': self.current_report_type,
            'case_data': self.current_case_data,
            'extracted_text': processed_data.get('extracted_text', {}),
            'metadata': processed_data.get('metadata', {}),
            'toolkit_results': toolkit_results,
            'previous_sections': {
                sid: output for sid, output in self.section_outputs.items()
                if self.section_states[sid] in [SectionState.COMPLETED, SectionState.APPROVED]
            },
            # Make all case uploads and media available to every section
            'files': processed_data.get('files', {}),
            'images': processed_data.get('images', {}),
            'videos': processed_data.get('videos', {}),
            'audio': processed_data.get('audio', {}),
            'contracts': processed_data.get('contracts', {}),
            'forms': processed_data.get('forms', {}),
            'processing_log': processed_data.get('processing_log', []),
            'summary': processed_data.get('summary', {}),
            # Shared in-memory cache for lookups (e.g., reverse geocode) across sections
            'lookup_cache': self.lookup_cache,
            # Data usage policies (guidance for renderers on how to use the data)
            'data_policies': {
                'hide_file_names': True,
                'hide_camera_tags': True,
                'min_image_resolution': {'width': 640, 'height': 480},
                'geocoding_via_profile': True,
                'narrative_required_for_media_link': True,
                'timezone': 'local_system',
                'max_snippet_chars': 200,
                # Lookup orchestration policy (short-circuit on first success)
                'lookup_order': ['chatgpt', 'copilot', 'google_maps'],
                'short_circuit': True,
                'prompt_user_on_fail': True,
            },
        }
        
        # Include media analysis results for Section 8
        if section_id == 'section_8' and 'media_analysis' in processed_data:
            payload['media_analysis'] = processed_data['media_analysis']
        
        # Inject API keys if available via user profile manager
        try:
            if hasattr(self.toolkit_engine, 'user_profile_manager') and self.toolkit_engine.user_profile_manager and self.toolkit_engine.user_profile_manager.is_authenticated():
                payload['api_keys'] = self.toolkit_engine.user_profile_manager.get_api_keys()
        except Exception:
            pass
        
        # Add section-specific data
        if section_id == 'section_1':
            # Investigation objectives need client and case info
            payload.update({
                'client_name': self.current_case_data.get('client_name'),
                'client_address': self.current_case_data.get('client_address'),
                'client_phone': self.current_case_data.get('client_phone'),
                'contract_date': self.current_case_data.get('contract_date'),
                'investigation_goals': self.current_case_data.get('investigation_goals'),
                'subject_primary': self.current_case_data.get('subject_primary'),
                'subject_secondary': self.current_case_data.get('subject_secondary'),
                'assigned_investigator': self.current_case_data.get('assigned_investigator', 'David Krashin'),
                'investigator_license': self.current_case_data.get('investigator_license', '0163814-C000480'),
                'agency_name': self.current_case_data.get('agency_name', 'DKI Services LLC'),
                'agency_license': self.current_case_data.get('agency_license', '0200812-IA000307')
            })
        
        elif section_id == 'section_6':
            # Billing section needs financial data
            payload.update({
                'contract_total': self.current_case_data.get('contract_total'),
                'billing_data': toolkit_results.get('billing_validation', {})
            })
        elif section_id == 'section_8':
            # Evidence section may include user notes keyed by media id
            payload.update({
                'manual_notes': processed_data.get('manual_notes', {}),
            })
        elif section_id == 'section_toc':
            # Provide section order for TOC rendering
            try:
                sections = self.report_types[self.current_report_type]['sections']
            except Exception:
                sections = []
            payload.update({
                'report_sections': sections,
            })
        elif section_id == 'section_cp':
            # Provide optional cover logo path from user profile settings
            try:
                upm = getattr(self.toolkit_engine, 'user_profile_manager', None)
                if upm and upm.is_authenticated():
                    cover_logo_path = upm.get_setting('cover_logo_path')
                else:
                    cover_logo_path = None
            except Exception:
                cover_logo_path = None
            payload.update({
                'cover_logo_path': cover_logo_path,
                'client_profile': self.current_case_data.get('client_profile', {}),
            })

        return payload

    def _derive_route_pairs_from_section8(self, previous_sections: Dict[str, Any], max_pairs: int = 10) -> List[Dict[str, str]]:
        """Derive route origin/destination pairs from Section 8 content by scanning
        address lines in chronological order and building successive pairs.
        """
        try:
            sec8 = previous_sections.get('section_8', {}) or {}
            content = sec8.get('content') or ''
            if not isinstance(content, str) or not content:
                return []
            addresses: List[str] = []
            for raw in content.split('\n'):
                line = raw.strip()
                if not line:
                    continue
                if line.lower().startswith('observed near, '):
                    addr = line[len('Observed near, '):].strip()
                    # Skip placeholders
                    if addr.startswith('[') and addr.endswith(']'):
                        continue
                    if not addresses or addresses[-1] != addr:
                        addresses.append(addr)
            pairs: List[Dict[str, str]] = []
            for i in range(len(addresses) - 1):
                if len(pairs) >= max_pairs:
                    break
                pairs.append({'origin': addresses[i], 'destination': addresses[i + 1]})
            return pairs
        except Exception:
            return []
    
    def _extract_text_for_section(self, section_id: str, processed_data: Dict[str, Any]) -> str:
        """Extract relevant text data for a specific section"""
        
        extracted_text = processed_data.get('extracted_text', {})
        
        # Combine all extracted text
        all_text = []
        for source, text in extracted_text.items():
            if text.strip():
                all_text.append(f"--- {source} ---\n{text}")
        
        return '\n\n'.join(all_text)
    
    def _prepare_report_metadata(self) -> Dict[str, Any]:
        """Prepare metadata for toolkit analysis"""
        
        return {
            'case_id': self.current_case_data.get('case_id'),
            'report_type': self.current_report_type,
            'client_name': self.current_case_data.get('client_name'),
            'contract_date': self.current_case_data.get('contract_date'),
            'investigator': self.current_case_data.get('assigned_investigator'),
            'timestamp': datetime.now().isoformat()
        }
    
    def _extract_section_id(self, section_name: str) -> str:
        """Extract section ID from section name"""
        
        # Map section names to IDs
        name_to_id = {}
        if self.current_report_type:
            sections = self.report_types[self.current_report_type]["sections"]
            for section_id, name in sections:
                name_to_id[name] = section_id
        
        # Try direct lookup first
        if section_name in name_to_id:
            return name_to_id[section_name]
        
        # Try partial matching
        for name, section_id in name_to_id.items():
            if section_name.lower() in name.lower() or name.lower() in section_name.lower():
                return section_id
        
        # Default extraction from section name
        if 'section' in section_name.lower():
            parts = section_name.lower().split()
            for part in parts:
                if part.startswith('section'):
                    return part.replace(' ', '_')
                elif part.isdigit():
                    return f"section_{part}"
        
        # Fallback
        return section_name.lower().replace(' ', '_').replace('-', '_')

    def _post_process_internal_audits(self, section_id: str, section_result: Dict[str, Any], section_payload: Dict[str, Any]):
        """Attach admin-facing audit results to section_result without altering client-facing content."""
        try:
            from smart_lookup import SmartLookupResolver
        except Exception:
            SmartLookupResolver = None

        api_keys = section_payload.get('api_keys', {}) or {}
        policies = section_payload.get('data_policies', {}) or {}
        cache = section_payload.get('lookup_cache')

        # Identity verification for Sections 1 and 5 (admin-only)
        if section_id in ('section_1', 'section_5') and SmartLookupResolver:
            try:
                subject = {
                    'name': self.current_case_data.get('subject_primary') or self.current_case_data.get('client_name'),
                    'address': self.current_case_data.get('subject_address') or self.current_case_data.get('client_address'),
                    'phone': self.current_case_data.get('subject_phone') or self.current_case_data.get('client_phone'),
                }
                resolver = SmartLookupResolver(api_keys=api_keys, policies=policies, cache=cache)
                res = resolver.identity_verify(subject)
                if isinstance(section_result.get('render_data'), dict):
                    manifest = section_result['render_data'].setdefault('manifest', {})
                    manifest['internal_identity_verification'] = res or {'status': 'unavailable'}
            except Exception:
                pass

        # Mileage auditing for Section 6 (admin-only)
        if section_id == 'section_6' and SmartLookupResolver:
            try:
                route_pairs = (section_payload.get('metadata', {}) or {}).get('route_pairs', [])
                if not route_pairs:
                    # Try to derive from Section 8 evidence addresses
                    route_pairs = self._derive_route_pairs_from_section8(section_payload.get('previous_sections', {}))
                if route_pairs:
                    resolver = SmartLookupResolver(api_keys=api_keys, policies=policies, cache=cache)
                    audits = []
                    for rp in route_pairs:
                        origin = rp.get('origin')
                        destination = rp.get('destination')
                        if not origin or not destination:
                            continue
                        res = resolver.route_distance(origin, destination)
                        audits.append({'origin': origin, 'destination': destination, **(res or {'error': 'unresolved'})})
                    section_result['internal_mileage_audit'] = {
                        'status': 'ok',
                        'audits': audits,
                        'policy_order': policies.get('lookup_order')
                    }
            except Exception:
                pass

    def _friendly_name_for(self, section_id: str) -> str:
        """Return the UI-friendly name for a given section id"""
        if self.current_report_type:
            for sid, name in self.report_types[self.current_report_type]["sections"]:
                if sid == section_id:
                    return name
        return section_id

    def _next_section_id(self, current_sid: str) -> Optional[str]:
        """Get next section id in current report ordering"""
        if not self.current_report_type:
            return None
        seq = [sid for sid, _ in self.report_types[self.current_report_type]["sections"]]
        try:
            idx = seq.index(current_sid)
        except ValueError:
            return None
        return seq[idx + 1] if idx < len(seq) - 1 else None

    def _all_content_sections_approved(self) -> bool:
        """Check if all primary content sections are approved (excludes CP/TOC/DP/FR)"""
        if not self.current_report_type:
            return False
        excluded = {"section_cp", "section_toc", "section_dp", "section_fr"}
        for sid, _ in self.report_types[self.current_report_type]["sections"]:
            if sid in excluded:
                continue
            if self.section_states.get(sid) != SectionState.APPROVED:
                return False
        return True
    
    def _generate_case_id(self) -> str:
        """Generate a unique case ID"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        client_name = self.current_case_data.get('client_name', 'UNKNOWN')
        
        # Clean client name
        clean_name = ''.join(c for c in client_name.upper() if c.isalnum())[:8]
        
        return f"{clean_name}_{timestamp}"
    
    def _emit_signal(self, signal_type: SignalType, payload: Dict[str, Any] = None):
        """Emit a signal for gateway communication"""
        
        with self.signal_lock:
            signal = {
                'type': signal_type.value,
                'timestamp': datetime.now().isoformat(),
                'payload': payload or {}
            }
            
            self.signal_queue.append(signal)
            
            logger.debug(f"Signal emitted: {signal_type.value}")
            
            # Handle immediate signal processing
            self._process_signal(signal)
    
    def _process_signal(self, signal: Dict[str, Any]):
        """Process an emitted signal"""
        
        signal_type = signal['type']
        payload = signal['payload']
        
        if signal_type == SignalType.HALT.value:
            self.is_frozen = True
            logger.warning("Gateway frozen due to HALT signal")
        
        elif signal_type == SignalType.REVISION_REQUIRED.value:
            section_id = payload.get('section_id')
            if section_id and section_id in self.section_states:
                self.section_states[section_id] = SectionState.REVISION_REQUIRED
                logger.info(f"Section {section_id} marked for revision")
        
        elif signal_type == SignalType.APPROVED.value:
            section_id = payload.get('section_id')
            if section_id and section_id in self.section_states:
                self.section_states[section_id] = SectionState.APPROVED
                logger.info(f"Section {section_id} approved")
        
        elif signal_type == SignalType.MEDIA_PROCESSING_COMPLETE.value:
            section_id = payload.get('section_id')
            logger.info(f"Media processing completed for {section_id}")
    
    def approve_section(self, section_name: str) -> bool:
        """Approve a completed section"""
        
        section_id = self._extract_section_id(section_name)
        
        if section_id not in self.section_states:
            return False
        
        if self.section_states[section_id] != SectionState.COMPLETED:
            return False
        
        self._emit_signal(SignalType.APPROVED, {'section_id': section_id})
        
        self.processing_log.append({
            'timestamp': datetime.now().isoformat(),
            'action': 'section_approved',
            'section_id': section_id
        })
        
        # Send to assembly cache on approval
        try:
            if section_id in self.section_outputs:
                self.final_assembly.add_section_output(section_id, self.section_outputs[section_id])
                self.final_assembly.mark_section_state(section_id, SectionState.APPROVED.value)
        except Exception as e:
            logger.error(f"Assembly cache update failed: {e}")

        # Attempt auto-advance to next section (generation only; review will still be user-driven)
        try:
            next_sid = self._next_section_id(section_id)
            if next_sid and next_sid in self.section_states and not self.is_frozen:
                if self.section_states[next_sid] == SectionState.PENDING:
                    processed_data = self.last_processed_data
                    logger.info(f"Auto-advance to generate next section: {next_sid}")
                    self.generate_section(self._friendly_name_for(next_sid), processed_data, self.current_report_type)
        except Exception as e:
            logger.warning(f"Auto-advance skipped: {e}")

        # If all content sections are approved, assemble final report
        try:
            if self._all_content_sections_approved():
                assembled = self.final_assembly.assemble_final_report(self.current_report_type, self.current_case_data)
                self.processing_log.append({
                    'timestamp': datetime.now().isoformat(),
                    'action': 'final_report_assembled',
                    'sections': len(assembled.get('sections', []))
                })
                self._emit_signal(SignalType.FINAL_APPROVED, {'status': 'final_assembled'})
        except Exception as e:
            logger.error(f"Final assembly failed: {e}")

        return True
    
    def request_revision(self, section_name: str, feedback: str = None) -> bool:
        """Request revision for a section"""
        
        section_id = self._extract_section_id(section_name)
        
        if section_id not in self.section_states:
            return False
        
        self._emit_signal(SignalType.REVISION_REQUIRED, {
            'section_id': section_id,
            'feedback': feedback
        })
        
        self.processing_log.append({
            'timestamp': datetime.now().isoformat(),
            'action': 'revision_requested',
            'section_id': section_id,
            'feedback': feedback
        })
        
        return True
    
    def get_section_status(self, section_name: str = None) -> Dict[str, Any]:
        """Get status of a specific section or all sections"""
        
        if section_name:
            section_id = self._extract_section_id(section_name)
            if section_id in self.section_states:
                return {
                    'section_id': section_id,
                    'section_name': section_name,
                    'state': self.section_states[section_id].value,
                    'has_output': section_id in self.section_outputs
                }
            return None
        else:
            # Return all section statuses
            status = {}
            if self.current_report_type:
                sections = self.report_types[self.current_report_type]["sections"]
                for section_id, name in sections:
                    status[section_id] = {
                        'section_name': name,
                        'state': self.section_states.get(section_id, SectionState.PENDING).value,
                        'has_output': section_id in self.section_outputs
                    }
            return status
    
    def get_processing_log(self) -> List[Dict[str, Any]]:
        """Get the processing log"""
        return self.processing_log.copy()
    
    def get_signal_queue(self) -> List[Dict[str, Any]]:
        """Get the current signal queue"""
        with self.signal_lock:
            return self.signal_queue.copy()
    
    def clear_signal_queue(self):
        """Clear the signal queue"""
        with self.signal_lock:
            self.signal_queue.clear()
    
    def reset_gateway(self):
        """Reset the gateway state"""
        self.is_frozen = False
        self.section_states.clear()
        self.section_outputs.clear()
        self.processing_log.clear()
        self.clear_signal_queue()
        self.current_case_data.clear()
        self.current_report_type = None
        
        # Reset media processing state
        with self.media_lock:
            self.media_processing_queue.clear()
            self.media_results_cache.clear()
            self.media_processing_active = False
        
        logger.info("Gateway reset completed")
    
    def export_case_data(self) -> Dict[str, Any]:
        """Export complete case data for saving"""
        
        return {
            'case_id': self.current_case_data.get('case_id'),
            'report_type': self.current_report_type,
            'case_data': self.current_case_data,
            'section_states': {k: v.value for k, v in self.section_states.items()},
            'section_outputs': self.section_outputs,
            'processing_log': self.processing_log,
            'media_results_cache': self.media_results_cache,
            'export_timestamp': datetime.now().isoformat()
        }
    
    def get_media_processing_status(self) -> Dict[str, Any]:
        """Get current media processing status"""
        
        with self.media_lock:
            return {
                'media_processing_active': self.media_processing_active,
                'media_queue_length': len(self.media_processing_queue),
                'media_results_count': len(self.media_results_cache),
                'cached_results': list(self.media_results_cache.keys())
            }






