#!/usr/bin/env python3
"""
OCR Flow Engine - Implementation of OCR Flow SOP
Strongest-first execution with structured outputs and fallback hierarchy
"""

import os
import logging
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class OCRFlowEngine:
    """Main OCR Flow Engine implementing OCR Flow SOP"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # OCR Flow SOP Configuration
        self.ocr_config = {
            'confidence_threshold': 0.7,
            'fallback_enabled': True,
            'strongest_first': True,
            'enable_unstructured': True,
            'enable_tesseract': True,
            'fallback_engines': ['easyocr', 'paddleocr', 'azure']
        }
        
        # Structured Output Schema
        self.structured_schema = {
            'text_blocks': [],
            'tables': [],
            'entities': [],
            'media': [],
            'metadata': {},
            'ai_notes': [],
            'confidence': 0.0,
            'engine_used': '',
            'fallback_attempts': [],
            'processing_time': 0.0,
            'timestamp': datetime.now().isoformat()
        }
        
        # Engine availability flags
        self.engines_available = {
            'unstructured': False,
            'tesseract': False,
            'easyocr': False,
            'paddleocr': False,
            'azure': False
        }
        
        # Initialize engines
        self._initialize_engines()
        
    def _initialize_engines(self):
        """Initialize available OCR engines"""
        self.logger.info("Initializing OCR engines...")
        
        # Check Unstructured parser
        try:
            import unstructured
            self.engines_available['unstructured'] = True
            self.logger.info("Unstructured parser: Available")
        except ImportError:
            self.logger.warning("Unstructured parser: Not available")
        
        # Check Tesseract
        try:
            import pytesseract
            from PIL import Image
            self.engines_available['tesseract'] = True
            self.logger.info("Tesseract OCR: Available")
        except ImportError:
            self.logger.warning("Tesseract OCR: Not available")
        
        # Check EasyOCR
        try:
            import easyocr
            self.engines_available['easyocr'] = True
            self.logger.info("EasyOCR: Available")
        except ImportError:
            self.logger.warning("EasyOCR: Not available")
        
        # Check PaddleOCR
        try:
            import paddleocr
            self.engines_available['paddleocr'] = True
            self.logger.info("PaddleOCR: Available")
        except ImportError:
            self.logger.warning("PaddleOCR: Not available")
        
        # Check Azure OCR
        try:
            from azure.cognitiveservices.vision.computervision import ComputerVisionClient
            self.engines_available['azure'] = True
            self.logger.info("Azure OCR: Available")
        except ImportError:
            self.logger.warning("Azure OCR: Not available")
    
    def process_file(self, file_path: str, file_type: str) -> Dict[str, Any]:
        """Main processing method implementing OCR Flow SOP"""
        start_time = datetime.now()
        
        self.logger.info(f"Starting OCR Flow processing for {file_path}")
        
        # Initialize result with structured schema
        result = self.structured_schema.copy()
        result['file_path'] = file_path
        result['file_type'] = file_type
        
        # Stage 1: Primary Extraction (Strongest-first)
        primary_result = self._perform_primary_extraction(file_path, file_type)
        
        if primary_result['confidence'] >= self.ocr_config['confidence_threshold']:
            result.update(primary_result)
            result['processing_time'] = (datetime.now() - start_time).total_seconds()
            self.logger.info(f"Primary extraction successful: {primary_result['engine_used']}")
            return result
        
        # Stage 2: Fallback Extraction
        if self.ocr_config['fallback_enabled']:
            fallback_result = self._perform_fallback_extraction(file_path, file_type, primary_result)
            result.update(fallback_result)
            result['processing_time'] = (datetime.now() - start_time).total_seconds()
            
            if fallback_result['confidence'] >= self.ocr_config['confidence_threshold']:
                self.logger.info(f"Fallback extraction successful: {fallback_result['engine_used']}")
                return result
        
        # All extraction failed
        result['confidence'] = 0.0
        result['engine_used'] = 'all_failed'
        result['processing_time'] = (datetime.now() - start_time).total_seconds()
        self.logger.error(f"All OCR engines failed for {file_path}")
        return result
    
    def _perform_primary_extraction(self, file_path: str, file_type: str) -> Dict[str, Any]:
        """Primary extraction using strongest-first approach"""
        result = self.structured_schema.copy()
        
        # Stage 1: Unstructured parser for native PDFs/DOCX
        if (file_type in ['pdf', 'docx'] and 
            self.engines_available['unstructured'] and 
            self.ocr_config['enable_unstructured']):
            
            unstructured_result = self._extract_with_unstructured(file_path)
            if unstructured_result['confidence'] >= self.ocr_config['confidence_threshold']:
                result.update(unstructured_result)
                result['engine_used'] = 'unstructured'
                return result
        
        # Stage 2: Tesseract OCR for images/scans
        if (file_type in ['image', 'pdf'] and 
            self.engines_available['tesseract'] and 
            self.ocr_config['enable_tesseract']):
            
            tesseract_result = self._extract_with_tesseract(file_path)
            if tesseract_result['confidence'] >= self.ocr_config['confidence_threshold']:
                result.update(tesseract_result)
                result['engine_used'] = 'tesseract'
                return result
        
        # Primary extraction failed
        result['confidence'] = 0.0
        result['engine_used'] = 'primary_failed'
        return result
    
    def _perform_fallback_extraction(self, file_path: str, file_type: str, primary_result: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback extraction cascade"""
        result = primary_result.copy()
        fallback_attempts = []
        
        # Fallback engines in order
        fallback_engines = [
            ('easyocr', self._extract_with_easyocr),
            ('paddleocr', self._extract_with_paddleocr),
            ('azure', self._extract_with_azure)
        ]
        
        for engine_name, engine_func in fallback_engines:
            if (engine_name in self.ocr_config['fallback_engines'] and 
                self.engines_available[engine_name] and 
                file_type in ['image', 'pdf']):
                
                self.logger.info(f"Attempting {engine_name} fallback for {file_path}")
                engine_result = engine_func(file_path)
                
                if engine_result['confidence'] >= self.ocr_config['confidence_threshold']:
                    result.update(engine_result)
                    result['engine_used'] = engine_name
                    result['fallback_attempts'] = fallback_attempts + [engine_name]
                    return result
                else:
                    fallback_attempts.append(f"{engine_name}_low_confidence")
        
        # All fallbacks failed
        result['fallback_attempts'] = fallback_attempts
        result['engine_used'] = 'all_failed'
        result['confidence'] = 0.0
        return result
    
    def _extract_with_unstructured(self, file_path: str) -> Dict[str, Any]:
        """Extract text using Unstructured parser"""
        try:
            from unstructured.partition.pdf import partition_pdf
            from unstructured.partition.docx import partition_docx
            
            result = self.structured_schema.copy()
            
            if file_path.lower().endswith('.pdf'):
                elements = partition_pdf(file_path)
            elif file_path.lower().endswith('.docx'):
                elements = partition_docx(file_path)
            else:
                return result
            
            text_blocks = []
            tables = []
            
            for element in elements:
                if hasattr(element, 'text') and element.text.strip():
                    text_blocks.append({
                        'text': element.text,
                        'type': element.category,
                        'confidence': getattr(element, 'confidence', 1.0),
                        'bbox': getattr(element, 'bbox', None)
                    })
                
                if element.category == 'Table':
                    tables.append({
                        'text': element.text,
                        'confidence': getattr(element, 'confidence', 1.0),
                        'bbox': getattr(element, 'bbox', None)
                    })
            
            result['text_blocks'] = text_blocks
            result['tables'] = tables
            result['confidence'] = 0.9  # High confidence for native document parsing
            result['engine_used'] = 'unstructured'
            
            return result
            
        except Exception as e:
            self.logger.error(f"Unstructured extraction failed: {e}")
            return self.structured_schema.copy()
    
    def _extract_with_tesseract(self, file_path: str) -> Dict[str, Any]:
        """Extract text using Tesseract OCR"""
        try:
            import pytesseract
            from PIL import Image
            
            result = self.structured_schema.copy()
            
            # Load and preprocess image
            image = Image.open(file_path)
            image = self._preprocess_image_for_ocr(image)
            
            # Configure Tesseract
            config = '--oem 3 --psm 6'
            
            # Perform OCR
            text = pytesseract.image_to_string(image, lang='eng', config=config)
            
            # Get detailed data for structured output
            data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
            
            # Extract text blocks with confidence and bounding boxes
            text_blocks = []
            confidences = []
            
            for i in range(len(data['text'])):
                if int(data['conf'][i]) > 0 and data['text'][i].strip():
                    text_blocks.append({
                        'text': data['text'][i],
                        'confidence': int(data['conf'][i]) / 100.0,
                        'bbox': [data['left'][i], data['top'][i], data['width'][i], data['height'][i]]
                    })
                    confidences.append(int(data['conf'][i]))
            
            result['text'] = text.strip()
            result['text_blocks'] = text_blocks
            result['confidence'] = sum(confidences) / len(confidences) / 100.0 if confidences else 0.0
            result['engine_used'] = 'tesseract'
            result['metadata'] = {
                'config_used': config,
                'language': 'eng',
                'blocks_count': len(text_blocks)
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"Tesseract extraction failed: {e}")
            return self.structured_schema.copy()
    
    def _extract_with_easyocr(self, file_path: str) -> Dict[str, Any]:
        """Extract text using EasyOCR"""
        try:
            import easyocr
            from PIL import Image
            import numpy as np
            
            result = self.structured_schema.copy()
            
            # Initialize EasyOCR reader
            reader = easyocr.Reader(['en'], gpu=False)
            
            # Load image
            image = Image.open(file_path)
            img_array = np.array(image)
            
            # Perform OCR
            ocr_results = reader.readtext(img_array)
            
            # Extract structured data
            text_blocks = []
            confidences = []
            text_parts = []
            
            for (bbox, text, confidence) in ocr_results:
                if confidence > 0.5:  # Filter low confidence results
                    text_blocks.append({
                        'text': text,
                        'confidence': confidence,
                        'bbox': bbox
                    })
                    text_parts.append(text)
                    confidences.append(confidence)
            
            result['text'] = ' '.join(text_parts)
            result['text_blocks'] = text_blocks
            result['confidence'] = sum(confidences) / len(confidences) if confidences else 0.0
            result['engine_used'] = 'easyocr'
            result['metadata'] = {
                'results_count': len(ocr_results),
                'filtered_count': len(text_blocks)
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"EasyOCR extraction failed: {e}")
            return self.structured_schema.copy()
    
    def _extract_with_paddleocr(self, file_path: str) -> Dict[str, Any]:
        """Extract text using PaddleOCR"""
        try:
            import paddleocr
            from PIL import Image
            import numpy as np
            
            result = self.structured_schema.copy()
            
            # Initialize PaddleOCR
            paddle_ocr = paddleocr.PaddleOCR(use_angle_cls=True, lang='en', use_gpu=False)
            
            # Load image
            image = Image.open(file_path)
            img_array = np.array(image)
            
            # Perform OCR
            ocr_results = paddle_ocr.ocr(img_array, cls=True)
            
            # Extract structured data
            text_blocks = []
            confidences = []
            text_parts = []
            
            if ocr_results and ocr_results[0]:
                for line in ocr_results[0]:
                    if line and len(line) >= 2:
                        text = line[1][0] if line[1] else ''
                        confidence = line[1][1] if line[1] and len(line[1]) > 1 else 0
                        
                        if confidence > 0.5 and text.strip():
                            text_blocks.append({
                                'text': text,
                                'confidence': confidence,
                                'bbox': line[0] if line[0] else None
                            })
                            text_parts.append(text)
                            confidences.append(confidence)
            
            result['text'] = ' '.join(text_parts)
            result['text_blocks'] = text_blocks
            result['confidence'] = sum(confidences) / len(confidences) if confidences else 0.0
            result['engine_used'] = 'paddleocr'
            result['metadata'] = {
                'lines_processed': len(ocr_results[0]) if ocr_results and ocr_results[0] else 0,
                'filtered_count': len(text_blocks)
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"PaddleOCR extraction failed: {e}")
            return self.structured_schema.copy()
    
    def _extract_with_azure(self, file_path: str) -> Dict[str, Any]:
        """Extract text using Azure Computer Vision"""
        try:
            from azure.cognitiveservices.vision.computervision import ComputerVisionClient
            from msrest.authentication import CognitiveServicesCredentials
            
            result = self.structured_schema.copy()
            
            # This would require Azure credentials configuration
            # For now, return empty result
            self.logger.info("Azure OCR available but not configured")
            result['engine_used'] = 'azure_not_configured'
            result['confidence'] = 0.0
            
            return result
            
        except Exception as e:
            self.logger.error(f"Azure OCR extraction failed: {e}")
            return self.structured_schema.copy()
    
    def _preprocess_image_for_ocr(self, image):
        """Preprocess image to improve OCR accuracy"""
        try:
            from PIL import ImageEnhance, ImageFilter
            
            # Convert to grayscale
            if image.mode != 'L':
                image = image.convert('L')
            
            # Enhance contrast
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(2.0)
            
            # Apply sharpening filter
            image = image.filter(ImageFilter.SHARPEN)
            
            return image
            
        except Exception as e:
            self.logger.warning(f"Image preprocessing failed: {e}")
            return image
    
    def get_engine_status(self) -> Dict[str, Any]:
        """Get status of all OCR engines"""
        return {
            'engines_available': self.engines_available,
            'config': self.ocr_config,
            'total_engines': len([e for e in self.engines_available.values() if e])
        }



