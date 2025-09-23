#!/usr/bin/env python3
"""
File Processing Orchestrator - Multi-stage pipeline for comprehensive document analysis
Stages: Load → Scan → AI Analysis → Context Building → Section Distribution
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import time

# Ensure critical modules resolve relative to the Report Engine root

REPO_ROOT = Path(__file__).resolve().parents[1]
ADDITIONAL_PATHS = [
    REPO_ROOT,
    REPO_ROOT / 'CoreSystem' / 'Processors',
    REPO_ROOT / 'CoreSystem' / 'Gateway',
    REPO_ROOT / 'CoreSystem' / 'Tools',
    REPO_ROOT / 'Processors',
    REPO_ROOT / 'Gateway',
    REPO_ROOT / 'Tools',
]
for candidate in ADDITIONAL_PATHS:
    candidate_str = str(candidate)
    if candidate.exists() and candidate_str not in sys.path:
        sys.path.insert(0, candidate_str)

logger = logging.getLogger(__name__)

class FileProcessingOrchestrator:
    """
    Orchestrates the complete file processing pipeline:
    1. File Loading & Validation
    2. Document Scanning (OCR + pdfplumber)
    3. AI Context Analysis 
    4. Cross-referencing & Context Building
    5. Section-specific Data Distribution
    """
    
    def __init__(self, document_processor=None, ai_toolkit=None):
        self.document_processor = document_processor
        self.ai_toolkit = ai_toolkit
        self.processing_stats = {
            'files_loaded': 0,
            'files_scanned': 0,
            'ai_analyses': 0,
            'sections_populated': 0,
            'start_time': None,
            'stage_times': {}
        }
        
    def process_file_batch(self, file_list: List[Dict[str, Any]], report_sections: List[str]) -> Dict[str, Any]:
        """
        Main orchestration method - processes files through all stages
        
        Args:
            file_list: List of file info dicts with 'name', 'path', 'type'
            report_sections: List of section IDs that need data
            
        Returns:
            Comprehensive processing result with section-specific data
        """
        
        self.processing_stats['start_time'] = time.time()
        logger.info(f"🚀 Starting file processing orchestration for {len(file_list)} files")
        
        # Stage 1: File Loading & Validation
        stage_start = time.time()
        loaded_files = self._stage_1_load_files(file_list)
        self.processing_stats['stage_times']['loading'] = time.time() - stage_start
        
        # Stage 2: Document Scanning (OCR + pdfplumber)
        stage_start = time.time()
        scanned_data = self._stage_2_scan_documents(loaded_files)
        self.processing_stats['stage_times']['scanning'] = time.time() - stage_start
        
        # Stage 3: AI Context Analysis
        stage_start = time.time()
        ai_analysis = self._stage_3_ai_analysis(scanned_data)
        self.processing_stats['stage_times']['ai_analysis'] = time.time() - stage_start
        
        # Stage 4: Cross-referencing & Context Building
        stage_start = time.time()
        unified_context = self._stage_4_build_context(scanned_data, ai_analysis)
        self.processing_stats['stage_times']['context_building'] = time.time() - stage_start
        
        # Stage 5: Section-specific Distribution
        stage_start = time.time()
        section_data = self._stage_5_distribute_to_sections(unified_context, report_sections)
        self.processing_stats['stage_times']['section_distribution'] = time.time() - stage_start
        
        total_time = time.time() - self.processing_stats['start_time']
        
        return {
            'processed_files': scanned_data,
            'ai_analysis': ai_analysis,
            'unified_context': unified_context,
            'section_data': section_data,
            'processing_stats': self.processing_stats,
            'total_processing_time': total_time,
            'success': True
        }
    
    def _stage_1_load_files(self, file_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Stage 1: Load and validate files"""
        logger.info(f"📁 Stage 1: Loading {len(file_list)} files...")
        
        loaded_files = []
        for file_info in file_list:
            try:
                file_path = file_info.get('path', '')
                if os.path.exists(file_path):
                    file_size = os.path.getsize(file_path)
                    file_info.update({
                        'size': file_size,
                        'loaded': True,
                        'load_time': datetime.now().isoformat()
                    })
                    loaded_files.append(file_info)
                    self.processing_stats['files_loaded'] += 1
                else:
                    logger.warning(f"File not found: {file_path}")
                    
            except Exception as e:
                logger.error(f"Failed to load {file_info.get('name', 'unknown')}: {e}")
        
        logger.info(f"✅ Stage 1 Complete: {len(loaded_files)}/{len(file_list)} files loaded")
        return loaded_files
    
    def _stage_2_scan_documents(self, loaded_files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Stage 2: Scan documents using OCR + pdfplumber"""
        logger.info(f"🔍 Stage 2: Scanning {len(loaded_files)} files...")
        
        if not self.document_processor:
            logger.warning("No document processor available - skipping scanning")
            return {'files': {}, 'extracted_text': {}, 'tables': {}, 'metadata': {}}
        
        # Use the enhanced document processor with pdfplumber
        scan_results = self.document_processor.process_files(loaded_files)
        self.processing_stats['files_scanned'] = len(loaded_files)
        
        logger.info(f"✅ Stage 2 Complete: {len(scan_results.get('files', {}))} files scanned")
        return scan_results
    
    def _stage_3_ai_analysis(self, scanned_data: Dict[str, Any]) -> Dict[str, Any]:
        """Stage 3: AI analysis of extracted content"""
        logger.info("🤖 Stage 3: AI analysis of extracted content...")
        
        if not self.ai_toolkit:
            logger.warning("No AI toolkit available - skipping AI analysis")
            return {'analyses': {}, 'summaries': {}, 'entities': {}}
        
        ai_results = {
            'analyses': {},
            'summaries': {},
            'entities': {},
            'classifications': {}
        }
        
        # Analyze each file's extracted text
        extracted_texts = scanned_data.get('extracted_text', {})
        
        for file_id, text in extracted_texts.items():
            if text and len(text.strip()) > 50:  # Only analyze substantial content
                try:
                    # AI analysis using your existing toolkit
                    analysis = self._analyze_text_with_ai(text, file_id)
                    ai_results['analyses'][file_id] = analysis
                    self.processing_stats['ai_analyses'] += 1
                    
                except Exception as e:
                    logger.error(f"AI analysis failed for {file_id}: {e}")
        
        logger.info(f"✅ Stage 3 Complete: {self.processing_stats['ai_analyses']} AI analyses")
        return ai_results
    
    def _stage_4_build_context(self, scanned_data: Dict[str, Any], ai_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Stage 4: Build unified context from all sources"""
        logger.info("🧠 Stage 4: Building unified context...")
        
        unified_context = {
            'all_text': '',
            'key_entities': [],
            'important_dates': [],
            'locations': [],
            'people': [],
            'organizations': [],
            'financial_data': [],
            'tables_summary': [],
            'document_types': [],
            'cross_references': {}
        }
        
        # Combine all extracted text
        all_texts = []
        for text in scanned_data.get('extracted_text', {}).values():
            if text:
                all_texts.append(text)
        unified_context['all_text'] = '\n\n'.join(all_texts)
        
        # Extract key information from AI analyses
        for file_id, analysis in ai_analysis.get('analyses', {}).items():
            if analysis:
                unified_context['key_entities'].extend(analysis.get('entities', []))
                unified_context['important_dates'].extend(analysis.get('dates', []))
                unified_context['locations'].extend(analysis.get('locations', []))
        
        # Process tables from pdfplumber
        for file_id, file_data in scanned_data.get('files', {}).items():
            tables = file_data.get('tables', [])
            for table in tables:
                unified_context['tables_summary'].append({
                    'file_id': file_id,
                    'table_id': table.get('table_id'),
                    'rows': table.get('rows', 0),
                    'cols': table.get('cols', 0),
                    'page': table.get('page', 0),
                    'source': table.get('source'),
                    'accuracy': table.get('accuracy')
                })
        
        logger.info("✅ Stage 4 Complete: Unified context built")
        return unified_context
    
    def _stage_5_distribute_to_sections(self, unified_context: Dict[str, Any], report_sections: List[str]) -> Dict[str, Any]:
        """Stage 5: Distribute relevant data to each report section"""
        logger.info(f"📋 Stage 5: Distributing data to {len(report_sections)} sections...")
        
        section_data = {}
        
        for section_id in report_sections:
            section_data[section_id] = self._extract_section_relevant_data(
                section_id, unified_context
            )
            self.processing_stats['sections_populated'] += 1
        
        logger.info(f"✅ Stage 5 Complete: {len(section_data)} sections populated")
        return section_data
    
    def _analyze_text_with_ai(self, text: str, file_id: str) -> Dict[str, Any]:
        """Analyze text using AI toolkit"""
        try:
            # Use your existing AI toolkit for analysis
            if hasattr(self.ai_toolkit, 'analyze_text'):
                return self.ai_toolkit.analyze_text(text)
            else:
                # Fallback: basic analysis
                return {
                    'entities': [],
                    'summary': text[:500] + "..." if len(text) > 500 else text,
                    'key_points': [],
                    'confidence': 0.8
                }
        except Exception as e:
            logger.error(f"AI analysis error for {file_id}: {e}")
            return {}
    
    def _extract_section_relevant_data(self, section_id: str, unified_context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract data relevant to a specific report section"""
        
        # Section-specific data extraction rules
        section_rules = {
            'section_1': ['people', 'organizations', 'locations'],  # Client info
            'section_cp': ['people', 'locations', 'important_dates'],  # Case participants  
            'section_dp': ['all_text', 'tables_summary', 'financial_data'],  # Data processing
            'section_fr': ['financial_data', 'tables_summary', 'organizations'],  # Financial records
            'section_summary': ['key_entities', 'important_dates', 'cross_references']
        }
        
        relevant_keys = section_rules.get(section_id, ['all_text'])
        section_specific_data = {}
        
        for key in relevant_keys:
            if key in unified_context:
                section_specific_data[key] = unified_context[key]
        
        # Add the full context for reference
        section_specific_data['full_context_available'] = True
        section_specific_data['context_keys'] = list(unified_context.keys())
        
        return section_specific_data
    
    def get_processing_summary(self) -> str:
        """Get a human-readable processing summary"""
        stats = self.processing_stats
        
        summary = f"""
🎯 File Processing Orchestration Complete!

📊 Processing Statistics:
   • Files Loaded: {stats['files_loaded']}
   • Files Scanned: {stats['files_scanned']} 
   • AI Analyses: {stats['ai_analyses']}
   • Sections Populated: {stats['sections_populated']}

⏱️ Stage Timing:
"""
        
        for stage, duration in stats.get('stage_times', {}).items():
            summary += f"   • {stage.title()}: {duration:.2f}s\n"
        
        return summary

# Integration function for main application
def create_processing_orchestrator(document_processor=None, ai_toolkit=None):
    """Factory function to create orchestrator with dependencies"""
    return FileProcessingOrchestrator(document_processor, ai_toolkit)



