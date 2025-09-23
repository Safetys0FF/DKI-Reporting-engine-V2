#!/usr/bin/env python3
"""
Full-stack PDF pipeline utility built on the DKI Engine processing stack.
Stages: load files -> document processor (pdfplumber + Camelot + pdf2image/OCR) ->
optional AI analysis -> report synthesis. Designed as an operational version of the
prior theoretical pipeline example.
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

try:
    from CoreSystem.Processors.document_processor import DocumentProcessor
    from CoreSystem.Gateway.file_processing_orchestrator import FileProcessingOrchestrator
except ImportError as import_err:
    raise SystemExit(f"Unable to import core processing modules: {import_err}")

try:
    from CoreSystem.Tools.ai_integration import AIAnalysisEngine
except ImportError:
    AIAnalysisEngine = None  # Optional dependency

logger = logging.getLogger(__name__)

class BasicAIToolkit:
    """Lightweight fallback AI toolkit when the full integration is unavailable."""

    def analyze_text(self, text: str) -> Dict[str, Any]:
        trimmed = (text or "").strip()
        if not trimmed:
            return {'summary': '', 'entities': [], 'key_points': [], 'confidence': 0.0}
        summary = trimmed[:500] + ("..." if len(trimmed) > 500 else "")
        return {
            'summary': summary,
            'entities': [],
            'key_points': [],
            'confidence': 0.3
        }

def detect_file_type(processor: DocumentProcessor, file_path: Path) -> str:
    """Map a file extension to the processor's supported category."""
    ext = file_path.suffix.lower()
    for category, extensions in processor.supported_formats.items():
        if ext in extensions:
            if category in {"image", "video", "audio", "contract", "form"}:
                return category
            return "document"
    return "document"

def collect_files(input_path: Path) -> List[Path]:
    if input_path.is_file():
        return [input_path]
    if input_path.is_dir():
        return sorted([p for p in input_path.rglob('*') if p.is_file()])
    raise FileNotFoundError(f"Input path not found: {input_path}")

def build_file_list(processor: DocumentProcessor, paths: List[Path]) -> List[Dict[str, Any]]:
    files: List[Dict[str, Any]] = []
    for path in paths:
        try:
            file_type = detect_file_type(processor, path)
            files.append({
                'name': path.name,
                'path': str(path),
                'type': file_type
            })
        except Exception as err:
            logger.warning("Skipping %s: %s", path, err)
    return files

def create_orchestrator(use_ai: bool) -> FileProcessingOrchestrator:
    processor = DocumentProcessor()
    ai_toolkit = None
    if use_ai:
        if AIAnalysisEngine is not None:
            try:
                ai_toolkit = AIAnalysisEngine()
            except Exception as err:
                logger.warning("AIAnalysisEngine unavailable (%s); using fallback toolkit", err)
                ai_toolkit = BasicAIToolkit()
        else:
            ai_toolkit = BasicAIToolkit()
    return FileProcessingOrchestrator(document_processor=processor, ai_toolkit=ai_toolkit)

def run_pipeline(orchestrator: FileProcessingOrchestrator,
                 files: List[Dict[str, Any]],
                 sections: List[str]) -> Dict[str, Any]:
    if not files:
        raise ValueError("No input files supplied to the pipeline")
    logger.info("Running pipeline for %d files", len(files))
    return orchestrator.process_file_batch(files, sections)

def summarise_results(results: Dict[str, Any]) -> Dict[str, Any]:
    processed = results.get('processed_files', {})
    files = processed.get('files', {})
    tables = []
    object_detections = []
    for file_id, file_data in files.items():
        for table in file_data.get('tables', []):
            tables.append({
                'file_id': file_id,
                'table_id': table.get('table_id'),
                'rows': table.get('rows'),
                'cols': table.get('cols'),
                'page': table.get('page'),
                'source': table.get('source'),
                'accuracy': table.get('accuracy')
            })
        detections = file_data.get('objects', [])
        for entry in detections:
            if isinstance(entry, dict) and 'detections' in entry:
                enriched = {'file_id': file_id, **entry}
                object_detections.append(enriched)
            else:
                object_detections.append({'file_id': file_id, 'detections': entry})
    return {
        'run_timestamp': datetime.now().isoformat(),
        'files_processed': len(files),
        'tables_extracted': tables,
        'object_detections': object_detections,
        'processing_stats': results.get('processing_stats', {}),
        'section_summary_keys': list(results.get('section_data', {}).keys())
    }

def write_summary(summary: Dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(summary, indent=2), encoding='utf-8')
    logger.info("Summary written to %s", output_path)

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the DKI Engine full-stack PDF pipeline over a folder or set of files."
    )
    parser.add_argument('input', type=Path, help='Path to a file or directory of evidence documents')
    parser.add_argument('--sections', nargs='+', default=['section_1', 'section_cp', 'section_dp', 'section_fr', 'section_summary'],
                        help='Section identifiers to populate (defaults to key report sections)')
    parser.add_argument('--output', type=Path, default=Path('fullstack_pipeline_summary.json'),
                        help='Path to write a JSON summary of the run')
    parser.add_argument('--no-ai', action='store_true', help='Disable AI analysis stage')
    parser.add_argument('--log-level', default='INFO', help='Logging level (default: INFO)')
    return parser.parse_args()

def main() -> None:
    args = parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO),
                        format='[%(levelname)s] %(message)s')

    input_paths = collect_files(args.input)
    orchestrator = create_orchestrator(use_ai=not args.no_ai)
    files = build_file_list(orchestrator.document_processor, input_paths)

    results = run_pipeline(orchestrator, files, args.sections)
    summary = summarise_results(results)

    write_summary(summary, args.output)

    tables = summary['tables_extracted']
    detections = summary.get('object_detections', [])
    print()
    print("=== Pipeline Summary ===")
    print(f"Files processed: {summary['files_processed']}")
    print(f"Tables extracted: {len(tables)}")
    if tables:
        preview = tables[:5]
        for table in preview:
            print(f" - {table['file_id']} :: {table['table_id']} (rows={table['rows']}, cols={table['cols']}, source={table['source']})")
        if len(tables) > len(preview):
            print(f"   ... {len(tables) - len(preview)} more tables")
    print(f"Detection entries: {len(detections)}")
    if detections:
        preview_det = detections[:3]
        for entry in preview_det:
            det_list = entry.get('detections', [])
            count = len(det_list) if isinstance(det_list, list) else 1
            sample = None
            if isinstance(det_list, list) and det_list:
                sample = det_list[0].get('label') if isinstance(det_list[0], dict) else det_list[0]
            elif isinstance(entry.get('detections'), dict):
                sample = entry['detections'].get('label')
            page = entry.get('page', 'n/a')
            print(f" - {entry.get('file_id')} :: page {page} -> {count} detections (sample label: {sample})")
        if len(detections) > len(preview_det):
            print(f"   ... {len(detections) - len(preview_det)} more entries")
    print(f"Processing stats: {json.dumps(summary['processing_stats'], indent=2)}")

if __name__ == '__main__':
    main()
