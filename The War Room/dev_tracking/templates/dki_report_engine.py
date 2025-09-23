#!/usr/bin/env python3
"""
DKI Report Engine - OCR Tools Integration
Comprehensive integration of OCR Flow SOP, Evidence Classification, and Gateway Orchestration
"""

import os
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

from ocr_flow_engine import OCRFlowEngine
from evidence_classifier import EvidenceClassifier
from scalable_gateway import ScalableGateway
from narrative_assembler import NarrativeAssembler

logger = logging.getLogger(__name__)

class DKIReportEngine:
    """Main DKI Report Engine integrating all OCR tools and processing components"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Initialize core components
        self.ocr_engine = OCRFlowEngine(config)
        self.evidence_classifier = EvidenceClassifier(config)
        self.gateway = ScalableGateway(config)
        self.narrative_assembler = NarrativeAssembler(config)
        
        # Processing statistics
        self.processing_stats = {
            'total_files_processed': 0,
            'successful_extractions': 0,
            'failed_extractions': 0,
            'sections_completed': 0,
            'narratives_generated': 0,
            'cross_links_created': 0
        }
        
        self.logger.info("DKI Report Engine initialized with OCR tools")
    
    def process_case_files(self, file_paths: List[str]) -> Dict[str, Any]:
        """Process multiple case files through the complete pipeline"""
        self.logger.info(f"Starting case processing for {len(file_paths)} files")
        
        results = {
            'case_id': f"case_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'total_files': len(file_paths),
            'processing_results': {},
            'section_assignments': {},
            'extraction_results': {},
            'narrative_results': {},
            'gateway_status': {},
            'processing_summary': {}
        }
        
        try:
            # Stage 1: Register and classify all files
            self.logger.info("Stage 1: File registration and classification")
            for file_path in file_paths:
                if os.path.exists(file_path):
                    registration_result = self.gateway.register_file(file_path)
                    if registration_result['success']:
                        results['processing_results'][file_path] = registration_result
                        section = registration_result['section']
                        if section not in results['section_assignments']:
                            results['section_assignments'][section] = []
                        results['section_assignments'][section].append(file_path)
                    else:
                        self.logger.error(f"Failed to register file: {file_path}")
                else:
                    self.logger.warning(f"File not found: {file_path}")
            
            # Stage 2: OCR extraction for each file
            self.logger.info("Stage 2: OCR extraction")
            for file_path in file_paths:
                if file_path in results['processing_results']:
                    file_type = self._determine_file_type(file_path)
                    extraction_result = self.ocr_engine.process_file(file_path, file_type)
                    results['extraction_results'][file_path] = extraction_result
                    
                    if extraction_result['confidence'] > 0.7:
                        self.processing_stats['successful_extractions'] += 1
                    else:
                        self.processing_stats['failed_extractions'] += 1
            
            # Stage 3: Generate narratives for each section
            self.logger.info("Stage 3: Narrative generation")
            for section, files in results['section_assignments'].items():
                if section != 'unassigned':
                    section_data = self._compile_section_data(section, files, results['extraction_results'])
                    narrative_result = self.narrative_assembler.assemble(section, section_data)
                    results['narrative_results'][section] = narrative_result
                    
                    if narrative_result['success']:
                        self.processing_stats['narratives_generated'] += 1
                        
                        # Transfer to gateway
                        self.gateway.transfer_section_data(section, {
                            'narrative': narrative_result['narrative'],
                            'raw_data': section_data,
                            'extraction_results': [results['extraction_results'].get(f) for f in files if f in results['extraction_results']]
                        })
            
            # Stage 4: Create cross-links
            self.logger.info("Stage 4: Cross-link creation")
            self._create_cross_links(results)
            
            # Stage 5: Get final gateway status
            results['gateway_status'] = self.gateway.get_gateway_status()
            
            # Update processing summary
            results['processing_summary'] = {
                'success_rate': self.processing_stats['successful_extractions'] / len(file_paths) if file_paths else 0,
                'sections_with_data': len([s for s in results['section_assignments'].keys() if s != 'unassigned']),
                'total_narratives': self.processing_stats['narratives_generated'],
                'processing_time': datetime.now().isoformat()
            }
            
            self.processing_stats['total_files_processed'] += len(file_paths)
            
            self.logger.info("Case processing completed successfully")
            return results
            
        except Exception as e:
            self.logger.error(f"Case processing failed: {e}")
            results['error'] = str(e)
            return results
    
    def _determine_file_type(self, file_path: str) -> str:
        """Determine file type for OCR processing"""
        file_ext = Path(file_path).suffix.lower()
        
        if file_ext in ['.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp', '.heic']:
            return 'image'
        elif file_ext in ['.pdf']:
            return 'pdf'
        elif file_ext in ['.docx', '.doc']:
            return 'docx'
        elif file_ext in ['.mp4', '.mov', '.avi', '.mkv']:
            return 'video'
        elif file_ext in ['.mp3', '.wav', '.m4a', '.aac']:
            return 'audio'
        else:
            return 'unknown'
    
    def _compile_section_data(self, section: str, files: List[str], extraction_results: Dict[str, Any]) -> Dict[str, Any]:
        """Compile data for a specific section"""
        section_data = {
            'section_id': section,
            'files': files,
            'timestamp': datetime.now().isoformat(),
            'content': [],
            'metadata': {}
        }
        
        # Compile content from extraction results
        for file_path in files:
            if file_path in extraction_results:
                extraction = extraction_results[file_path]
                if extraction['confidence'] > 0.5:  # Only include high-confidence extractions
                    section_data['content'].append({
                        'file': file_path,
                        'text': extraction.get('text', ''),
                        'confidence': extraction['confidence'],
                        'engine_used': extraction['engine_used'],
                        'text_blocks': extraction.get('text_blocks', [])
                    })
        
        # Add section-specific metadata
        if section == 'section_3':
            section_data['subject'] = 'Unknown Subject'  # Would be extracted from data
            section_data['location'] = 'Unknown Location'  # Would be extracted from data
            section_data['activity'] = 'Surveillance activities'
        elif section == 'section_6':
            section_data['case_id'] = 'CASE-001'  # Would be from case data
            section_data['hours'] = 0  # Would be calculated
            section_data['mileage'] = 0  # Would be calculated
            section_data['total'] = 0  # Would be calculated
        
        return section_data
    
    def _create_cross_links(self, results: Dict[str, Any]):
        """Create cross-links between related evidence"""
        try:
            # Create cross-links based on common subjects, locations, or keywords
            all_text = ""
            for file_path, extraction in results['extraction_results'].items():
                if extraction.get('text'):
                    all_text += extraction['text'] + " "
            
            # Simple keyword-based cross-linking
            keywords = ['subject', 'location', 'date', 'time', 'activity']
            for keyword in keywords:
                if keyword in all_text.lower():
                    # Find files containing this keyword
                    related_files = []
                    for file_path, extraction in results['extraction_results'].items():
                        if extraction.get('text') and keyword in extraction['text'].lower():
                            related_files.append(file_path)
                    
                    # Create cross-links between related files
                    if len(related_files) > 1:
                        for i, file1 in enumerate(related_files):
                            for file2 in related_files[i+1:]:
                                # Get evidence IDs from gateway
                                for evidence_id, evidence in self.gateway.master_evidence_index.items():
                                    if evidence['file_path'] == file1:
                                        self.gateway.add_cross_link(evidence_id, keyword)
                                        self.processing_stats['cross_links_created'] += 1
                                        break
            
        except Exception as e:
            self.logger.error(f"Cross-link creation failed: {e}")
    
    def get_engine_status(self) -> Dict[str, Any]:
        """Get comprehensive status of all engines"""
        return {
            'ocr_engine': self.ocr_engine.get_engine_status(),
            'evidence_classifier': self.evidence_classifier.get_classification_stats(),
            'gateway': self.gateway.get_gateway_status(),
            'narrative_assembler': self.narrative_assembler.get_available_templates(),
            'processing_stats': self.processing_stats
        }
    
    def sign_off_section(self, section_id: str, user: str) -> bool:
        """Sign off a completed section"""
        return self.gateway.sign_off_section(section_id, user)
    
    def get_completed_sections(self) -> List[str]:
        """Get list of completed sections"""
        return list(self.gateway.completed_sections)
    
    def generate_final_report(self) -> Dict[str, Any]:
        """Generate final report from all completed sections"""
        try:
            report = {
                'report_id': f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'generated_at': datetime.now().isoformat(),
                'sections': {},
                'summary': {}
            }
            
            # Assemble each completed section
            for section_id in self.gateway.completed_sections:
                section_report = self.gateway.assemble_for_report(section_id)
                if section_report:
                    report['sections'][section_id] = section_report
            
            # Generate summary
            report['summary'] = {
                'total_sections': len(report['sections']),
                'total_evidence_items': len(self.gateway.master_evidence_index),
                'processing_stats': self.processing_stats,
                'gateway_status': self.gateway.get_gateway_status()
            }
            
            return report
            
        except Exception as e:
            self.logger.error(f"Final report generation failed: {e}")
            return {'error': str(e)}
    
    def save_case_state(self, file_path: str) -> bool:
        """Save complete case state to file"""
        return self.gateway.persist_gateway_state(file_path)
    
    def load_case_state(self, file_path: str) -> bool:
        """Load case state from file"""
        return self.gateway.load_gateway_state(file_path)

# Example usage and testing
if __name__ == "__main__":
    # Initialize the engine
    engine = DKIReportEngine()
    
    # Example file processing
    test_files = [
        "test_document.pdf",
        "surveillance_video.mp4",
        "evidence_photo.jpg"
    ]
    
    # Process files
    results = engine.process_case_files(test_files)
    
    # Print results
    print("Processing Results:")
    print(f"Total files: {results['total_files']}")
    print(f"Sections assigned: {list(results['section_assignments'].keys())}")
    print(f"Successful extractions: {engine.processing_stats['successful_extractions']}")
    
    # Get engine status
    status = engine.get_engine_status()
    print(f"\nEngine Status:")
    print(f"OCR engines available: {status['ocr_engine']['total_engines']}")
    print(f"Gateway evidence items: {status['gateway']['total_evidence_items']}")



