#!/usr/bin/env python3
"""
Mission Debrief Manager - Central Command integration for professional report tools
Integrates Digital Signature, Printing, Template, Watermark, and OSINT systems
"""

import os
import sys
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add Central Command paths for integration
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "The Warden"))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "Command Center", "Data Bus", "Bus Core Design"))

# Import professional tools (optional)
try:
    from tools.digital_signature_system import DigitalSignatureSystem
except ImportError:
    DigitalSignatureSystem = None

try:
    from tools.printing_system import PrintingSystem
except ImportError:
    PrintingSystem = None

try:
    from tools.template_system import TemplateSystem
except ImportError:
    TemplateSystem = None

try:
    from tools.watermark_system import WatermarkSystem
except ImportError:
    WatermarkSystem = None

try:
    from tools.osint_module import OSINTEngine
except ImportError:
    OSINTEngine = None

logger = logging.getLogger(__name__)

class MissionDebriefManager:
    """Mission Debrief Manager - Bootstrap Component for professional report tools"""
    
    def __init__(self, ecc=None, bus=None, gateway=None):
        self.ecc = ecc
        self.bus = bus
        self.gateway = gateway
        self.logger = logger

        # Bootstrap status
        self.is_bootstrap_component = True
        self.bootstrap_time = datetime.now().isoformat()
        self.registered_signals = []
        
        # Initialize professional tools (with graceful degradation)
        self.digital_signature_system = DigitalSignatureSystem() if DigitalSignatureSystem else None
        self.printing_system = PrintingSystem() if PrintingSystem else None
        self.template_system = TemplateSystem() if TemplateSystem else None
        self.watermark_system = WatermarkSystem() if WatermarkSystem else None
        self.osint_engine = OSINTEngine() if OSINTEngine else None
        
        # Tool status tracking
        self.tool_status = {
            'digital_signature': getattr(self.digital_signature_system, 'HAVE_CRYPTOGRAPHY', False) if self.digital_signature_system else False,
            'printing': getattr(self.printing_system, 'HAVE_WIN32_PRINT', False) if self.printing_system else False,
            'template': True if self.template_system else False,  # Template system doesn't require external dependencies
            'watermark': getattr(self.watermark_system, 'HAVE_REPORTLAB', False) if self.watermark_system else False,
            'osint': True if self.osint_engine else False  # OSINT engine handles its own dependencies
        }
        
        # Report processing queue
        self.report_queue = []
        self.processed_reports = {}
        self.case_summaries = {}

        # Register with Central Command Bus if available
        if self.bus:
            self._register_with_bus()
        
        logger.info("Mission Debrief Manager initialized as Bootstrap Component")
    
    def _register_with_bus(self):
        """Register Mission Debrief Manager with Central Command Bus"""
        try:
            if not self.bus:
                return False
            
            # Register signal handlers for professional tools
            self.bus.register_signal("mission_debrief.digital_sign", self._handle_digital_sign_signal)
            self.bus.register_signal("mission_debrief.print_report", self._handle_print_report_signal)
            self.bus.register_signal("mission_debrief.apply_template", self._handle_apply_template_signal)
            self.bus.register_signal("mission_debrief.add_watermark", self._handle_add_watermark_signal)
            self.bus.register_signal("mission_debrief.osint_lookup", self._handle_osint_lookup_signal)
            self.bus.register_signal("mission_debrief.process_report", self._handle_process_report_signal)
            
            self.registered_signals = [
                "mission_debrief.digital_sign",
                "mission_debrief.print_report", 
                "mission_debrief.apply_template",
                "mission_debrief.add_watermark",
                "mission_debrief.osint_lookup",
                "mission_debrief.process_report"
            ]
            
            logger.info("📡 Mission Debrief Manager registered with Central Command Bus")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register with bus: {e}")
            return False
    
    def _handle_digital_sign_signal(self, signal_data: Dict[str, Any]):
        """Handle digital signature signals from the bus"""
        try:
            file_path = signal_data.get('file_path')
            certificate_path = signal_data.get('certificate_path')
            password = signal_data.get('password')

            if not file_path:
                self.logger.error("Missing file_path in digital sign signal")
                return

            if not self.digital_signature_system:
                self.logger.warning("Digital signature system not available - skipping request")
                return

            # Apply digital signature
            result = self.digital_signature_system.sign_document(
                file_path, certificate_path, password
            )

            # Emit completion signal
            if self.bus:
                self.bus.emit("mission_debrief.digital_signed", {
                    'file_path': file_path,
                    'result': result,
                    'signed_at': datetime.now().isoformat()
                })

            self.logger.info(f"🔐 Digital signature applied to {file_path}")

        except Exception as e:
            self.logger.error(f"Failed to handle digital sign signal: {e}")
    def _handle_print_report_signal(self, signal_data: Dict[str, Any]):
        """Handle print report signals from the bus"""
        try:
            file_path = signal_data.get('file_path')
            printer_name = signal_data.get('printer_name')
            print_settings = signal_data.get('print_settings', {})

            if not file_path:
                self.logger.error("Missing file_path in print report signal")
                return

            if not self.printing_system:
                self.logger.warning("Printing system not available - skipping request")
                return

            # Print the report
            result = self.printing_system.print_document(
                file_path, printer_name, print_settings
            )

            # Emit completion signal
            if self.bus:
                self.bus.emit("mission_debrief.report_printed", {
                    'file_path': file_path,
                    'result': result,
                    'printed_at': datetime.now().isoformat()
                })

            self.logger.info(f"🖨️ Report printed: {file_path}")

        except Exception as e:
            self.logger.error(f"Failed to handle print report signal: {e}")
    def _handle_apply_template_signal(self, signal_data: Dict[str, Any]):
        """Handle apply template signals from the bus"""
        try:
            template_name = signal_data.get('template_name')
            data = signal_data.get('data', {})
            output_path = signal_data.get('output_path')

            if not template_name:
                self.logger.error("Missing template_name in apply template signal")
                return

            if not self.template_system:
                self.logger.warning("Template system not available - skipping request")
                return

            # Apply template
            result = self.template_system.apply_template(
                template_name, data, output_path
            )

            # Emit completion signal
            if self.bus:
                self.bus.emit("mission_debrief.template_applied", {
                    'template_name': template_name,
                    'result': result,
                    'applied_at': datetime.now().isoformat()
                })

            self.logger.info(f"📄 Template applied: {template_name}")

        except Exception as e:
            self.logger.error(f"Failed to handle apply template signal: {e}")
    def _handle_add_watermark_signal(self, signal_data: Dict[str, Any]):
        """Handle add watermark signals from the bus"""
        try:
            file_path = signal_data.get('file_path')
            watermark_text = signal_data.get('watermark_text', 'DRAFT')
            watermark_type = signal_data.get('watermark_type', 'draft')

            if not file_path:
                self.logger.error("Missing file_path in add watermark signal")
                return

            if not self.watermark_system:
                self.logger.warning("Watermark system not available - skipping request")
                return

            # Add watermark
            result = self.watermark_system.add_watermark(
                file_path, watermark_text, watermark_type
            )

            # Emit completion signal
            if self.bus:
                self.bus.emit("mission_debrief.watermark_added", {
                    'file_path': file_path,
                    'result': result,
                    'watermarked_at': datetime.now().isoformat()
                })

            self.logger.info(f"💧 Watermark added to {file_path}")

        except Exception as e:
            self.logger.error(f"Failed to handle add watermark signal: {e}")
    def _handle_osint_lookup_signal(self, signal_data: Dict[str, Any]):
        """Handle OSINT lookup signals from the bus"""
        try:
            query = signal_data.get('query')
            lookup_type = signal_data.get('lookup_type', 'general')

            if not query:
                self.logger.error("Missing query in OSINT lookup signal")
                return

            if not self.osint_engine:
                self.logger.warning("OSINT engine not available - skipping request")
                return

            # Perform OSINT lookup
            result = self.osint_engine.search(query, lookup_type)

            # Emit completion signal
            if self.bus:
                self.bus.emit("mission_debrief.osint_completed", {
                    'query': query,
                    'lookup_type': lookup_type,
                    'result': result,
                    'searched_at': datetime.now().isoformat()
                })

            self.logger.info(f"🔍 OSINT lookup completed: {query}")

        except Exception as e:
            self.logger.error(f"Failed to handle OSINT lookup signal: {e}")
    def _handle_process_report_signal(self, signal_data: Dict[str, Any]):
        """Handle complete report processing signals from the bus"""
        try:
            report_data = signal_data.get('report_data', {})
            processing_options = signal_data.get('processing_options', {})

            # Process complete report pipeline
            result = self.process_complete_report(report_data, processing_options)

            # Emit completion signal
            if self.bus:
                self.bus.emit("mission_debrief.report_processed", {
                    'result': result,
                    'processed_at': datetime.now().isoformat()
                })

            case_id = report_data.get('case_id')
            if case_id:
                summary_payload = {
                    'case_id': case_id,
                    'report_id': result.get('report_id') if isinstance(result, dict) else None,
                    'processed_at': result.get('processed_at') if isinstance(result, dict) else None,
                    'steps_completed': result.get('steps_completed', []) if isinstance(result, dict) else [],
                    'tools_used': result.get('tools_used', []) if isinstance(result, dict) else [],
                    'status': result.get('status', 'processed') if isinstance(result, dict) else 'error',
                    'last_result': result
                }
                self.case_summaries[case_id] = summary_payload

            self.logger.info(f"📋 Complete report processed")

        except Exception as e:
            self.logger.error(f"Failed to handle process report signal: {e}")
    def process_complete_report(self, report_data: Dict[str, Any], options: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process a complete report through all professional tools"""
        try:
            options = options or {}
            processing_result = {
                'report_id': report_data.get('report_id', f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"),
                'processed_at': datetime.now().isoformat(),
                'steps_completed': [],
                'tools_used': [],
                'output_files': [],
                'status': 'ok'
            }

            output_files = processing_result['output_files']

            # Step 1: Apply template if requested
            if options.get('apply_template'):
                if not self.template_system:
                    self.logger.warning("Template system not available - skipping template step")
                else:
                    template_name = options.get('template_name', 'default')
                    template_result = self.template_system.apply_template(template_name, report_data)
                    processing_result['steps_completed'].append('template_applied')
                    processing_result['tools_used'].append('template_system')
                    if isinstance(template_result, dict) and template_result.get('output_path'):
                        output_files.append(template_result['output_path'])

            # Step 2: Add watermark if requested
            if options.get('add_watermark'):
                if not self.watermark_system:
                    self.logger.warning("Watermark system not available - skipping watermark step")
                else:
                    watermark_text = options.get('watermark_text', 'DRAFT')
                    watermark_type = options.get('watermark_type', 'draft')
                    targets = list(output_files) or report_data.get('output_files', [])
                    if not targets and report_data.get('file_path'):
                        targets = [report_data['file_path']]
                    for file_path in targets:
                        watermark_result = self.watermark_system.add_watermark(file_path, watermark_text, watermark_type)
                        processing_result['steps_completed'].append('watermark_added')
                        processing_result['tools_used'].append('watermark_system')
                        if isinstance(watermark_result, dict) and watermark_result.get('output_path'):
                            output_files.append(watermark_result['output_path'])

            # Step 3: Apply digital signature if requested
            if options.get('digital_sign'):
                if not self.digital_signature_system:
                    self.logger.warning("Digital signature system not available - skipping signature step")
                else:
                    certificate_path = options.get('certificate_path')
                    password = options.get('password')
                    targets = list(output_files) or report_data.get('output_files', [])
                    if not targets and report_data.get('file_path'):
                        targets = [report_data['file_path']]
                    for file_path in targets:
                        sign_result = self.digital_signature_system.sign_document(file_path, certificate_path, password)
                        processing_result['steps_completed'].append('digital_signed')
                        processing_result['tools_used'].append('digital_signature_system')
                        if isinstance(sign_result, dict) and sign_result.get('output_path'):
                            output_files.append(sign_result['output_path'])

            # Step 4: Print if requested
            if options.get('print_report'):
                if not self.printing_system:
                    self.logger.warning("Printing system not available - skipping print step")
                else:
                    printer_name = options.get('printer_name')
                    print_settings = options.get('print_settings', {})
                    targets = list(output_files) or report_data.get('output_files', [])
                    if not targets and report_data.get('file_path'):
                        targets = [report_data['file_path']]
                    for file_path in targets:
                        _ = self.printing_system.print_document(file_path, printer_name, print_settings)
                        processing_result['steps_completed'].append('printed')
                        processing_result['tools_used'].append('printing_system')

            self.logger.info(f"✅ Complete report processed: {processing_result['report_id']}")

            self.logger.info(f"📋 Complete report processed")
            return processing_result

        except Exception as e:
            self.logger.error(f"Failed to process complete report: {e}")
            return {'error': str(e), 'status': 'error'}
    def get_summary(self, case_id: str) -> Dict[str, Any]:
        """Get summary information for a case"""
        case_key = case_id or 'unknown_case'
        summary = self.case_summaries.get(case_key)
        if summary:
            return summary
        return {
            'case_id': case_key,
            'status': 'pending',
            'reports_processed': len(self.processed_reports),
            'tools_available': {k: v for k, v in self.tool_status.items()}
        }

    def get_bootstrap_status(self) -> Dict[str, Any]:
        """Get Mission Debrief Manager bootstrap status"""
        return {
            'is_bootstrap_component': self.is_bootstrap_component,
            'bootstrap_time': self.bootstrap_time,
            'registered_signals': self.registered_signals,
            'tool_status': self.tool_status,
            'report_queue_length': len(self.report_queue),
            'processed_reports_count': len(self.processed_reports),
            'available_tools': list(self.tool_status.keys()),
            'bus_connected': bool(self.bus),
            'ecc_connected': bool(self.ecc),
            'gateway_connected': bool(self.gateway)
        }
    
    def get_tool_capabilities(self) -> Dict[str, Any]:
        """Get capabilities of all professional tools"""
        return {
            'digital_signature': {
                'available': self.tool_status['digital_signature'],
                'capabilities': ['pdf_signing', 'certificate_management', 'document_authentication']
            },
            'printing': {
                'available': self.tool_status['printing'],
                'capabilities': ['direct_printing', 'print_preview', 'printer_selection']
            },
            'template': {
                'available': self.tool_status['template'],
                'capabilities': ['custom_templates', 'branding', 'color_schemes', 'layouts']
            },
            'watermark': {
                'available': self.tool_status['watermark'],
                'capabilities': ['draft_watermarks', 'confidential_stamps', 'security_overlays']
            },
            'osint': {
                'available': self.tool_status['osint'],
                'capabilities': ['internet_lookups', 'verification', 'data_gathering']
            }
        }

