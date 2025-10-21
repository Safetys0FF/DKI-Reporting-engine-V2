r"""
System Protocol Registry - Central Command Auto-Registration System
Date: October 10, 2025
Location: F:\The Central Command\Command Center\Data Bus\diagnostic_manager

UNIFIED EXECUTABLE MODULE:
- Protocol definitions (radio codes, signal translations, schemas)
- Auto-registration writer (updates protocol + registry + module code)
- Address validation and parent-child relationship enforcement
- CLI interface for manual registration

USAGE:
    # Import and use programmatically
    from system_protocol_registry import SystemProtocolRegistry, SIGNAL_TRANSLATIONS
    
    registry = SystemProtocolRegistry()
    result = registry.register_system(...)
    
    # Or use CLI
    python system_protocol_registry.py --register --name "System" --address "1.9" ...
"""

import json
import re
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from enum import Enum


# =============================================================================
# PROTOCOL DEFINITIONS
# =============================================================================

class RadioCode(Enum):
    """Standard radio codes for system communication"""
    TEN_FOUR = "10-4"
    TEN_SIX = "10-6"
    TEN_EIGHT = "10-8"
    TEN_NINE = "10-9"
    TEN_TEN = "10-10"
    SOS = "SOS"
    MAYDAY = "MAYDAY"
    STATUS = "STATUS"
    ROLLCALL = "ROLLCALL"
    RADIO_CHECK = "RADIO_CHECK"


RADIO_CODE_DEFINITIONS: Dict[str, Dict[str, str]] = {
    "10-4": {"meaning": "ACKNOWLEDGED", "usage": "Message received/Section approved/Ready", "gateway_action": "Unlock next section", "uds_monitoring": "System operational"},
    "10-6": {"meaning": "EVIDENCE_RECEIVED", "usage": "Evidence processing/Toolkit initialized", "gateway_action": "Broadcast toolkit context", "uds_monitoring": "Processing started"},
    "10-8": {"meaning": "EVIDENCE_COMPLETE", "usage": "Processing complete/Section finished/Output ready", "gateway_action": "Collect output payload", "uds_monitoring": "Processing complete"},
    "10-9": {"meaning": "REPEAT", "usage": "Repeat message/Manual review/Communication retry", "gateway_action": "Trigger manual review", "uds_monitoring": "Communication issue"},
    "10-10": {"meaning": "STANDBY", "usage": "Processing/System waiting/Emergency halt", "gateway_action": "Freeze gateway, notify lead", "uds_monitoring": "System waiting"},
    "SOS": {"meaning": "EMERGENCY", "usage": "System failure/Critical error", "gateway_action": "Escalate to diagnostics", "uds_monitoring": "Fault detected"},
    "MAYDAY": {"meaning": "CRITICAL_FAILURE", "usage": "System down/Complete failure", "gateway_action": "Emergency shutdown protocol", "uds_monitoring": "System down"},
    "STATUS": {"meaning": "STATUS_REQUEST", "usage": "Request status/Health check", "gateway_action": "Return status payload", "uds_monitoring": "Health monitoring"},
    "ROLLCALL": {"meaning": "ROLLCALL", "usage": "All systems respond/System discovery", "gateway_action": "Registry update", "uds_monitoring": "System registration"},
    "RADIO_CHECK": {"meaning": "COMMUNICATION_TEST", "usage": "Communication test/Connectivity validation", "gateway_action": "Acknowledge receipt", "uds_monitoring": "Connectivity test"}
}


SIGNAL_TRANSLATIONS: Dict[str, Dict[str, Any]] = {
    "locker": {
        "address": "1",
        "wildcard_signal": "locker.child.broadcast",
        "handler_method": "_handle_child_broadcast",
        "translations": {
            "ingest_evidence": [
                {"signal": "evidence.new", "radio_code": "10-6", "description": "Evidence file received and processing"},
                {"signal": "evidence.classified", "radio_code": "10-4", "description": "Evidence classified and ready"}
            ],
            "start_new_case": [{"signal": "case.created", "radio_code": None, "description": "New case initialized"}],
            "clear_evidence_pool": [{"signal": "locker.cleared", "radio_code": None, "description": "Evidence pool cleared"}]
        }
    },
    "warden": {
        "address": "2",
        "wildcard_signal": "warden.child.broadcast",
        "handler_method": "_handle_child_broadcast",
        "translations": {
            "gateway_ready": [{"signal": "gateway.ready", "radio_code": "10-4", "description": "Gateway initialization complete"}],
            "ecosystem_ready": [{"signal": "ecosystem.ready", "radio_code": None, "description": "ECC initialization complete"}],
            "section_routed": [{"signal": "section.routed", "radio_code": "10-4", "description": "Section routing approved"}],
            "handoff_complete": [{"signal": "handoff.completed", "radio_code": None, "description": "Module handoff successful"}]
        }
    },
    "marshall": {
        "address": "3",
        "wildcard_signal": "marshall.child.broadcast",
        "handler_method": "_handle_child_broadcast",
        "translations": {
            "evidence_processed": [{"signal": "evidence.processed", "radio_code": "10-6", "description": "Evidence processing active"}],
            "evidence_distributed": [{"signal": "evidence.distributed", "radio_code": None, "description": "Evidence distributed to section"}],
            "evidence_ready_for_debrief": [{"signal": "evidence.ready_for_debrief", "radio_code": "10-8", "description": "Evidence processing complete"}]
        }
    },
    "mission": {
        "address": "5",
        "wildcard_signal": "mission.child.broadcast",
        "handler_method": "_handle_child_broadcast",
        "translations": {
            "report_assembled": [{"signal": "mission.report.assembled", "radio_code": "10-8", "description": "Report assembly complete"}],
            "narrative_assembled": [{"signal": "narrative.assembled", "radio_code": None, "description": "Narrative assembly complete"}],
            "artifacts_generated": [{"signal": "artifacts.generated", "radio_code": None, "description": "Artifacts generated"}],
            "final_report_ready": [{"signal": "report.ready", "radio_code": None, "description": "Final report ready"}]
        }
    },
    "gui": {
        "address": "GUI-1",
        "wildcard_signal": "gui.child.broadcast",
        "handler_method": "_handle_child_broadcast",
        "translations": {
            "user_action": [{"signal": "gui.user.action", "radio_code": None, "description": "User initiated action"}],
            "view_changed": [{"signal": "gui.view.changed", "radio_code": None, "description": "GUI view/tab changed"}],
            "error_displayed": [{"signal": "gui.error.displayed", "radio_code": None, "description": "Error shown to user"}],
            "progress_updated": [{"signal": "gui.progress.updated", "radio_code": None, "description": "Progress indicator updated"}]
        }
    }
    # AUTO-REGISTRATION: New entries added below
}


ADDRESS_SCHEMA: Dict[str, Any] = {
    "bus_system": {"pattern": r"^Bus-\d+(\.\d+)?$", "examples": ["Bus-1", "Bus-1.1"]},
    "evidence_locker": {"parent": "1", "child_pattern": r"^1\.\d+$", "examples": ["1", "1.1", "1.9"]},
    "warden": {"parent": "2", "child_pattern": r"^2-[2-9](\.\d+)?$", "examples": ["2", "2-2", "2-2.1"]},
    "marshall": {"parent": "3", "child_pattern": r"^3-\d+$", "examples": ["3", "3-1", "3-2"]},
    "analyst_deck": {"parent_pattern": r"^4-\d+$", "examples": ["4-1", "4-2"], "fault_relay_parent": "2-3"},
    "mission_debrief": {"parent": "5", "child_pattern": r"^5-\d+(\.\d+)?$", "examples": ["5", "5-1", "5-1.1"]},
    "war_room": {"parent_pattern": r"^6-\d+$", "examples": ["6-1", "6-2"]},
    "gui": {"parent": "GUI-1", "child_pattern": r"^GUI-1\.\d+$", "examples": ["GUI-1", "GUI-1.1"]}
}


PARENT_CHILD_RELATIONSHIPS: Dict[str, Dict[str, Any]] = {
    "Bus-1": {"parent_name": "Central Command Bus", "parent_address": "Bus-1", "children": ["Bus-1.1", "Bus-1.2", "Bus-1.3", "Bus-1.4", "Bus-1.5"]},
    "DIAG-1": {"parent_name": "Unified Diagnostic System", "parent_address": "DIAG-1", "children": []},
    "1": {"parent_name": "Evidence Locker Main", "parent_address": "1", "children": ["1.1", "1.2", "1.3", "1.4", "1.5", "1.6", "1.7", "1.8"]},
    "2": {"parent_name": "Warden Module", "parent_address": "2", "children": ["2-2", "2-2.1", "2-2.2", "2-2.3", "2-2.4", "2-3", "2-3.1", "2-3.2", "2-3.3", "2-3.4"]},
    "3": {"parent_name": "Marshall Module", "parent_address": "3", "children": ["3-1", "3-2", "3-3"]},
    "5": {"parent_name": "Mission Debrief Module", "parent_address": "5", "children": ["5-1", "5-1.1", "5-1.2", "5.1", "5.2", "5.3", "5.4", "5-2", "5-2.1", "5-2.2", "5-2.3", "5-2.4"]},
    "GUI-1": {"parent_name": "Enhanced Functional GUI", "parent_address": "GUI-1", "children": ["GUI-1.1", "GUI-1.2", "GUI-1.3", "GUI-1.4", "GUI-1.5", "GUI-1.6", "GUI-1.7", "GUI-1.8", "GUI-1.9"]}
}


# =============================================================================
# AUTO-REGISTRATION SYSTEM
# =============================================================================

class SystemProtocolRegistry:
    """
    Unified system protocol registry and auto-registration engine.
    
    Handles:
    - Protocol definitions (radio codes, signal translations, address schemas)
    - System registration (validates, updates protocol + registry + code)
    - Address validation and parent-child relationship enforcement
    """
    
    def __init__(self, base_path: Optional[Path] = None):
        """Initialize registry"""
        if base_path is None:
            base_path = Path(__file__).parent
        
        self.base_path = Path(base_path)
        self.protocol_file = Path(__file__)  # This file
        self.registry_file = self.base_path / "read_me" / "system_registry.json"
        
        self.logger = logging.getLogger("SystemProtocolRegistry")
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('[%(levelname)s] %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    # -------------------------------------------------------------------------
    # PROTOCOL LOOKUP METHODS
    # -------------------------------------------------------------------------
    
    def get_radio_code_info(self, code: str) -> Optional[Dict[str, str]]:
        """Get radio code information"""
        return RADIO_CODE_DEFINITIONS.get(code)
    
    def get_signal_translations(self, module_name: str) -> Optional[Dict[str, Any]]:
        """Get signal translation table for module"""
        return SIGNAL_TRANSLATIONS.get(module_name)
    
    def get_parent_children(self, parent_address: str) -> Optional[List[str]]:
        """Get child addresses for parent"""
        rel = PARENT_CHILD_RELATIONSHIPS.get(parent_address)
        return rel["children"] if rel else None
    
    def validate_address_format(self, address: str) -> bool:
        """Validate address format"""
        patterns = [
            r"^Bus-\d+(\.\d+)?$",
            r"^\d+$",
            r"^\d+\.\d+$",
            r"^\d+-\d+(\.\d+)?$",
            r"^GUI-\d+(\.\d+)?$"
        ]
        return any(re.match(p, address) for p in patterns)
    
    # -------------------------------------------------------------------------
    # REGISTRATION METHODS
    # -------------------------------------------------------------------------
    
    def register_system(
        self,
        system_name: str,
        system_address: str,
        parent_address: Optional[str],
        handler_path: str,
        signal_translations: Optional[Dict[str, List[Dict[str, Any]]]] = None,
        is_parent_module: bool = False,
        wildcard_signal: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Register new system to Central Command.
        
        Args:
            system_name: Human-readable system name
            system_address: System address (e.g., "1.9", "GUI-1.10")
            parent_address: Parent system address (None for top-level)
            handler_path: Path to handler module
            signal_translations: Signal translation table (for parents only)
            is_parent_module: True if system will have children
            wildcard_signal: Wildcard signal name (e.g., "locker.child.broadcast")
        
        Returns:
            Registration result dict with status and details
        """
        result = {
            "success": False,
            "system_name": system_name,
            "system_address": system_address,
            "timestamp": datetime.now().isoformat(),
            "updates": {"protocol": False, "registry": False, "module_code": False},
            "errors": []
        }
        
        try:
            # Validate
            self.logger.info(f"Validating: {system_name} ({system_address})")
            if not self._validate_registration(system_address, parent_address, handler_path):
                result["errors"].append("Validation failed")
                return result
            
            # Update registry
            self.logger.info("Updating system_registry.json...")
            if self._update_registry(system_name, system_address, parent_address, handler_path):
                result["updates"]["registry"] = True
            else:
                result["errors"].append("Registry update failed")
            
            # Update protocol + code (for parents only)
            if is_parent_module and signal_translations:
                self.logger.info("Updating protocol definitions...")
                if self._update_protocol(system_address, signal_translations, wildcard_signal):
                    result["updates"]["protocol"] = True
                
                self.logger.info("Updating module code...")
                if self._update_module_code(handler_path, signal_translations, wildcard_signal):
                    result["updates"]["module_code"] = True
            
            result["success"] = result["updates"]["registry"] and (
                not is_parent_module or (result["updates"]["protocol"] and result["updates"]["module_code"])
            )
            
            if result["success"]:
                self.logger.info(f"[OK] Registration complete: {system_address}")
            
        except Exception as e:
            result["errors"].append(f"Exception: {e}")
            self.logger.error(f"Registration failed: {e}")
        
        return result
    
    def _validate_registration(self, address: str, parent: Optional[str], handler: str) -> bool:
        """Validate registration metadata"""
        if not self.validate_address_format(address):
            self.logger.error(f"Invalid address format: {address}")
            return False
        
        if parent and not self._validate_parent_child(parent, address):
            self.logger.error(f"Invalid parent-child: {parent} -> {address}")
            return False
        
        if not Path(handler).exists():
            self.logger.error(f"Handler not found: {handler}")
            return False
        
        return True
    
    def _validate_parent_child(self, parent: str, child: str) -> bool:
        """Validate parent-child relationship"""
        return child.startswith(parent) or child.split('-')[0] == parent.split('-')[0] or child.split('.')[0] == parent.split('.')[0]
    
    def _update_registry(self, name: str, address: str, parent: Optional[str], handler: str) -> bool:
        """Update system_registry.json"""
        try:
            if not self.registry_file.exists():
                return False
            
            with open(self.registry_file, 'r', encoding='utf-8') as f:
                registry = json.load(f)
            
            new_system = {
                "name": name,
                "address": address,
                "handler": handler,
                "location": handler,
                "parent": parent or "none",
                "status": "REGISTERED",
                "last_check": datetime.now().strftime("%Y-%m-%d"),
                "auto_registered": True,
                "registration_timestamp": datetime.now().isoformat()
            }
            
            registry["system_registry"]["connected_systems"].append(new_system)
            
            with open(self.registry_file, 'w', encoding='utf-8') as f:
                json.dump(registry, f, indent=2)
            
            self.logger.info(f"[OK] Registry updated: {address}")
            return True
            
        except Exception as e:
            self.logger.error(f"Registry update error: {e}")
            return False
    
    def _update_protocol(self, address: str, translations: Dict, wildcard: Optional[str]) -> bool:
        """Update SIGNAL_TRANSLATIONS in this file"""
        try:
            with open(self.protocol_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            module_key = address.replace('-', '_').replace('.', '_')
            
            new_entry = f'''
    "{module_key}": {{
        "address": "{address}",
        "wildcard_signal": "{wildcard or f'{module_key}.child.broadcast'}",
        "handler_method": "_handle_child_broadcast",
        "translations": {json.dumps(translations, indent=12)[:-1]}    }}
    }}
    # AUTO-REGISTRATION: New entries added below'''
            
            marker = "# AUTO-REGISTRATION: New entries added below"
            if marker in content:
                content = content.replace(marker, new_entry)
                
                with open(self.protocol_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                self.logger.info(f"[OK] Protocol updated: {address}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Protocol update error: {e}")
            return False
    
    def _update_module_code(self, handler_path: str, translations: Dict, wildcard: Optional[str]) -> bool:
        """Inject _handle_child_broadcast into module"""
        try:
            handler_file = Path(handler_path)
            if not handler_file.exists():
                return False
            
            with open(handler_file, 'r', encoding='utf-8') as f:
                code = f.read()
            
            if "_handle_child_broadcast" in code:
                self.logger.info("Handler already exists, skipping injection")
                return True
            
            handler_code = self._generate_handler(translations, wildcard)
            
            with open(handler_file, 'a', encoding='utf-8') as f:
                f.write(f'\n\n# AUTO-REGISTERED HANDLER\n{handler_code}')
            
            self.logger.info(f"[OK] Code injected: {handler_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Code injection error: {e}")
            return False
    
    def _generate_handler(self, translations: Dict, wildcard: Optional[str]) -> str:
        """Generate _handle_child_broadcast method code"""
        cases = []
        for msg_type, signals in translations.items():
            case = [f'        if message_type == "{msg_type}":']
            for sig in signals:
                radio = f'RadioCode.{sig["radio_code"].replace("-", "_").upper()}' if sig.get("radio_code") else 'None'
                case.append(f'            self.communicator.send_signal(target_address="Bus-1", signal_name="{sig["signal"]}", radio_code={radio}, payload=payload)')
            cases.append('\n'.join(case))
        
        all_cases = '\n        el'.join(cases)
        
        return f'''    def _handle_child_broadcast(self, payload: Dict[str, Any]) -> None:
        """AUTO-GENERATED signal translation handler - Wildcard: {wildcard or "N/A"}"""
        message_type = payload.get('message_type')
        if not message_type:
            self.log("[WARN] Child broadcast missing message_type")
            return
        {all_cases}
        else:
            self.log(f"[WARN] Unknown child message type: {{message_type}}")
'''


# =============================================================================
# CLI INTERFACE
# =============================================================================

def cli_register():
    """Command-line registration interface"""
    import argparse
    parser = argparse.ArgumentParser(description="Register system to Central Command")
    parser.add_argument("--name", required=True, help="System name")
    parser.add_argument("--address", required=True, help="System address")
    parser.add_argument("--parent", help="Parent address")
    parser.add_argument("--handler", required=True, help="Handler module path")
    parser.add_argument("--is-parent", action="store_true", help="Parent module flag")
    parser.add_argument("--wildcard", help="Wildcard signal name")
    
    args = parser.parse_args()
    
    registry = SystemProtocolRegistry()
    result = registry.register_system(
        system_name=args.name,
        system_address=args.address,
        parent_address=args.parent,
        handler_path=args.handler,
        signal_translations={},
        is_parent_module=args.is_parent,
        wildcard_signal=args.wildcard
    )
    
    print(f"\n{'='*70}")
    print(f"Registration: {'SUCCESS' if result['success'] else 'FAILED'}")
    print(f"{'='*70}")
    print(f"System: {result['system_name']} ({result['system_address']})")
    print(f"Timestamp: {result['timestamp']}")
    print(f"\nUpdates:")
    for target, status in result['updates'].items():
        print(f"  {'[OK]' if status else '[FAIL]'} {target}")
    if result['errors']:
        print(f"\nErrors: {result['errors']}")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    cli_register()

