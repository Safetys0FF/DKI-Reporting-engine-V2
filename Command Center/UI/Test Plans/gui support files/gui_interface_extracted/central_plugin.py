"""
central_plugin.py

DKI Engine - Central Plugin Interface
Provides a base class and registration mechanism for Central Command plugins.
"""

import os
import sys
from typing import Any, Dict, List, Optional, Callable
from pathlib import Path

# Add Central Command paths
sys.path.append(r"F:\The Central Command\The Warden")
sys.path.append(r"F:\The Central Command\Evidence Locker")
sys.path.append(r"F:\The Central Command\The Marshall")
sys.path.append(r"F:\The Central Command\Command Center\Mission Debrief")
sys.path.append(r"F:\The Central Command\Command Center\Data Bus\Bus Core Design")

from warden_main import Warden
from evidence_locker_main import EvidenceLocker
from evidence_manager import EvidenceManager
from importlib.util import spec_from_file_location, module_from_spec
from bus_core import DKIReportBus

LIBRARIAN_DIR = Path(r"F:/The Central Command/Command Center/Mission Debrief/The Librarian")
DEBRIEF_DIR = Path(r"F:/The Central Command/Command Center/Mission Debrief/Debrief/README")


def _load_class(module_name: str, module_path: Path, attr_name: str):
    spec = spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load spec for {module_name} from {module_path}")
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    try:
        return getattr(module, attr_name)
    except AttributeError as exc:
        raise ImportError(f"{attr_name} not found in {module_path}") from exc


NarrativeAssembler = _load_class("narrative_assembler", LIBRARIAN_DIR / "narrative_assembler.py", "NarrativeAssembler")
MissionDebriefManager = _load_class("mission_debrief_manager", DEBRIEF_DIR / "mission_debrief_manager.py", "MissionDebriefManager")

class CentralPlugin:
    """
    Base class for all Central Command plugins.
    Plugins should inherit from this class and implement the required methods.
    """
    name: str = "UnnamedPlugin"
    version: str = "0.1"
    author: str = "Unknown"
    description: str = "No description provided."

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

    def initialize(self) -> None:
        """
        Called when the plugin is loaded.
        Override this method to perform setup tasks.
        """
        pass

    def shutdown(self) -> None:
        """
        Called when the plugin is unloaded or the system is shutting down.
        Override this method to perform cleanup tasks.
        """
        pass

    def handle_event(self, event_type: str, data: Any) -> None:
        """
        Handle an event broadcast by the Central Command system.
        Override to respond to system events.
        """
        pass

# Plugin registry for dynamic loading and management
class CentralPluginRegistry:
    _plugins: Dict[str, CentralPlugin] = {}

    @classmethod
    def register(cls, plugin: CentralPlugin) -> None:
        cls._plugins[plugin.name] = plugin

    @classmethod
    def unregister(cls, plugin_name: str) -> None:
        if plugin_name in cls._plugins:
            del cls._plugins[plugin_name]

    @classmethod
    def get_plugin(cls, plugin_name: str) -> Optional[CentralPlugin]:
        return cls._plugins.get(plugin_name)

    @classmethod
    def list_plugins(cls) -> List[str]:
        return list(cls._plugins.keys())

    @classmethod
    def broadcast_event(cls, event_type: str, data: Any) -> None:
        for plugin in cls._plugins.values():
            plugin.handle_event(event_type, data)

# central_plugin.py

class CentralPluginAdapter:
    def __init__(self):
        self.bus = DKIReportBus()
        
        # Initialize Warden first
        self.warden = Warden()
        self.warden.start_warden()

        # Initialize components with proper error handling
        try:
            self.evidence_locker = EvidenceLocker(
                ecc=self.warden.ecc, gateway=self.warden.gateway, bus=self.bus
            )
        except Exception as e:
            print(f"Error initializing EvidenceLocker: {e}")
            self.evidence_locker = None
            
        try:
            self.evidence_manager = EvidenceManager(
                ecc=self.warden.ecc, gateway=self.warden.gateway
            )
        except Exception as e:
            print(f"Error initializing EvidenceManager: {e}")
            self.evidence_manager = None
            
        try:
            self.assembler = NarrativeAssembler(
                ecc=self.warden.ecc, bus=self.bus
            )
        except Exception as e:
            print(f"Error initializing NarrativeAssembler: {e}")
            self.assembler = None
            
        try:
            self.debrief = MissionDebriefManager(
                ecc=self.warden.ecc, bus=self.bus, gateway=self.warden.gateway
            )
        except Exception as e:
            print(f"Error initializing MissionDebriefManager: {e}")
            self.debrief = None

    def store_file(self, file_info):
        if self.evidence_locker:
            return self.evidence_locker.store(file_info)
        return {"error": "EvidenceLocker not initialized"}

    def get_case_summary(self, case_id):
        if self.debrief:
            return self.debrief.get_summary(case_id)
        return {"error": "MissionDebriefManager not initialized"}

    def generate_narrative(self, processed_data, section_id: str = "section_1"):
        if not self.assembler:
            return {"status": "error", "error": "NarrativeAssembler not initialized"}
        try:
            narrative_text = self.assembler.assemble(section_id, processed_data)
            summary = narrative_text if len(narrative_text) <= 400 else narrative_text[:400] + "..."
            return {
                "status": "ok",
                "section_id": section_id,
                "summary": summary,
                "full_narrative": narrative_text
            }
        except Exception as exc:
            return {"status": "error", "error": str(exc)}

    def log_event(self, msg):
        self.bus.log_event("GUI", msg)

    def send_to_bus(self, topic: str, payload: dict) -> dict:
        """Send a payload through the DKI bus system"""
        try:
            self.log_event(f"Sending to bus: {topic}")
            result = self.bus.send(topic=topic, data=payload)
            if isinstance(result, dict) and 'responses' in result and result['responses']:
                last_response = result['responses'][-1]
                if isinstance(last_response, dict):
                    return last_response
            return result
        except Exception as e:
            self.log_event(f"Bus send error: {e}")
            return {"error": str(e)}

# Exportable object
central_plugin = CentralPluginAdapter()