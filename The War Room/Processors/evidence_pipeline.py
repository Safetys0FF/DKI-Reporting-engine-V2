#!/usr/bin/env python3
"""Evidence pipeline and routing utilities for the DKI Engine."""

from __future__ import annotations

import hashlib
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from document_processor import DocumentProcessor

logger = logging.getLogger(__name__)


class EvidencePipeline:
    """Bridge between the evidence cache/UI intake and the document processor."""

    DEFAULT_SECTION_MAP: Dict[str, str] = {
        'image': 'section_8',      # Photo / Evidence Index
        'video': 'section_8',      # Video evidence consolidated with photo index
        'audio': 'section_6',      # Billing / call recordings summarized alongside audio analysis
        'pdf': 'section_3',        # Document reviews default to Section 3 narrative
        'document': 'section_3',
        'spreadsheet': 'section_5',# Financial / detailed listings
        'contract': 'section_4',   # Contracts & legal paperwork
        'form': 'section_4',
    }

    DEFAULT_ENGINE_PRIORITY: Dict[str, List[str]] = {
        'image': ['easyocr', 'paddleocr', 'tesseract'],
        'video': ['frame_ocr', 'easyocr', 'tesseract'],
        'pdf': ['pdfplumber', 'tesseract', 'easyocr'],
        'document': ['direct_text'],
        'spreadsheet': ['direct_text'],
        'audio': ['transcription'],
    }

    def __init__(
        self,
        document_processor: DocumentProcessor,
        *,
        manifest_path: Optional[Path] = None,
        router_config: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.document_processor = document_processor
        self.router_config = router_config or {}
        configured_path = manifest_path or self.router_config.get('manifest_path')
        self.manifest_path = Path(configured_path) if configured_path else Path('intake/manifest.json')
        self.manifest_path.parent.mkdir(parents=True, exist_ok=True)

    # ---------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------
    def process_batch(self, files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate manifest, route files, and invoke the document processor."""

        errors: List[str] = []
        manifest = self._build_manifest(files, errors)
        routing_plan = self._build_routing_plan(manifest)
        normalized_files = self._normalize_files(files, manifest, errors)

        processed_data: Dict[str, Any]
        if normalized_files:
            try:
                processed_data = self.document_processor.process_files(normalized_files)
            except Exception as exc:  # pragma: no cover - safety catch during integration
                logger.exception("Document processing failed")
                errors.append(f'document_processing_error: {exc}')
                processed_data = {'success': False, 'error': str(exc), 'files': {}}
        else:
            processed_data = {
                'success': False,
                'error': 'no_valid_files',
                'files': {},
                'extracted_text': {},
                'processing_log': [],
            }

        processed_data.setdefault('routing_plan', routing_plan)
        result = {
            'manifest': manifest,
            'routing': routing_plan,
            'processed_data': processed_data,
            'errors': errors,
        }

        self._persist_manifest(manifest)
        return result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _build_manifest(self, files: List[Dict[str, Any]], errors: List[str]) -> List[Dict[str, Any]]:
        manifest: List[Dict[str, Any]] = []
        for entry in files:
            raw_path = entry.get('path') if isinstance(entry, dict) else entry
            if not raw_path:
                errors.append('missing_path_entry')
                continue

            path_obj = Path(raw_path).expanduser().resolve()
            manifest_entry: Dict[str, Any] = {
                'path': str(path_obj),
                'name': entry.get('name') or path_obj.name,
                'type': entry.get('type'),
                'uploaded': entry.get('uploaded_date') or datetime.utcnow().isoformat(),
            }

            if not path_obj.exists():
                manifest_entry['error'] = 'not_found'
                errors.append(f'file_not_found:{path_obj}')
                manifest.append(manifest_entry)
                continue

            if 'size' in entry:
                manifest_entry['size'] = entry['size']
            else:
                try:
                    manifest_entry['size'] = path_obj.stat().st_size
                except OSError as exc:
                    manifest_entry['size_error'] = str(exc)

            manifest_entry['hashes'] = self._calculate_hashes(path_obj)
            manifest_entry['type'] = manifest_entry['type'] or entry.get('category')
            if not manifest_entry['type']:
                try:
                    manifest_entry['type'] = self.document_processor._infer_file_type(str(path_obj))
                except Exception:
                    manifest_entry['type'] = 'unknown'
            manifest.append(manifest_entry)

        return manifest

    def _build_routing_plan(self, manifest: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        section_map = {**self.DEFAULT_SECTION_MAP, **self.router_config.get('section_map', {})}
        engine_pref = {**self.DEFAULT_ENGINE_PRIORITY, **self.router_config.get('engine_priority', {})}

        routing_plan: List[Dict[str, Any]] = []
        for item in manifest:
            file_type = item.get('type') or 'unknown'
            target_section = section_map.get(file_type, 'section_8')
            preferred_engines = engine_pref.get(file_type, [])
            routing_plan.append({
                'path': item.get('path'),
                'name': item.get('name'),
                'type': file_type,
                'target_section': target_section,
                'engine_priority': preferred_engines,
            })
        return routing_plan

    def _normalize_files(
        self,
        files: List[Dict[str, Any]],
        manifest: List[Dict[str, Any]],
        errors: List[str],
    ) -> List[Dict[str, Any]]:
        manifest_index = {entry['path']: entry for entry in manifest if 'path' in entry}
        normalized: List[Dict[str, Any]] = []

        for original in files:
            info = dict(original)
            path_value = info.get('path')
            if not path_value:
                errors.append('normalize_missing_path')
                continue

            abs_path = str(Path(path_value).expanduser().resolve())
            manifest_entry = manifest_index.get(abs_path)
            if not manifest_entry or manifest_entry.get('error'):
                errors.append(f'manifest_error:{abs_path}')
                continue

            info['path'] = abs_path
            info.setdefault('name', manifest_entry.get('name'))
            info.setdefault('type', manifest_entry.get('type'))
            if not info.get('type'):
                try:
                    info['type'] = self.document_processor._infer_file_type(abs_path)
                except Exception:
                    info['type'] = 'unknown'
            info.setdefault('size', manifest_entry.get('size'))
            info.setdefault('uploaded_date', manifest_entry.get('uploaded'))
            normalized.append(info)

        return normalized

    def _persist_manifest(self, manifest: List[Dict[str, Any]]) -> None:
        try:
            payload = {
                'generated_at': datetime.utcnow().isoformat(),
                'items': manifest,
            }
            with self.manifest_path.open('w', encoding='utf-8') as handle:
                json.dump(payload, handle, indent=2)
        except Exception as exc:  # pragma: no cover - safety net for IO errors
            logger.warning("Failed to persist manifest at %s: %s", self.manifest_path, exc)

    @staticmethod
    def _calculate_hashes(file_path: Path) -> Dict[str, str]:
        hashes = {'md5': '', 'sha256': ''}
        try:
            md5 = hashlib.md5()
            sha256 = hashlib.sha256()
            with file_path.open('rb') as handle:
                for chunk in iter(lambda: handle.read(8192), b''):
                    md5.update(chunk)
                    sha256.update(chunk)
            hashes['md5'] = md5.hexdigest()
            hashes['sha256'] = sha256.hexdigest()
        except Exception as exc:  # pragma: no cover - IO/permission issues
            hashes['error'] = str(exc)
        return hashes
