"""
central_plugin.py

DKI Engine - Central Plugin Interface
Provides a base class and registration mechanism for Central Command plugins.
"""

import os
import sys
from typing import Any, Dict, List, Optional, Callable

# Add Central Command paths
sys.path.append(r"F:\The Central Command\The Warden")
sys.path.append(r"F:\The Central Command\Evidence Locker")
sys.path.append(r"F:\The Central Command\The Marshall")
sys.path.append(r"F:\The Central Command\Command Center\Mission Debrief")
sys.path.append(r"F:\The Central Command\Command Center\Data Bus\Bus Core Design")

from warden_main import Warden
from evidence_locker_main import EvidenceLocker
from evidence_manager import EvidenceManager
from narrative_assembler import NarrativeAssembler
from mission_debrief_manager import MissionDebriefManager
from bus_core import DKIReportBus

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
        self.warden = Warden()
        self.warden.start_warden()

        self.evidence_locker = EvidenceLocker(
            ecc=self.warden.ecc, gateway=self.warden.gateway, bus=self.bus
        )
        self.evidence_manager = EvidenceManager(
            ecc=self.warden.ecc, gateway=self.warden.gateway
        )
        self.assembler = NarrativeAssembler(
            ecc=self.warden.ecc, bus=self.bus
        )
        self.debrief = MissionDebriefManager(
            ecc=self.warden.ecc, bus=self.bus, gateway=self.warden.gateway
        )

    def store_file(self, file_info):
        return self.evidence_locker.store(file_info)

    def get_case_summary(self, case_id):
        return self.debrief.get_summary(case_id)

    def generate_narrative(self, processed_data, section_id: str = 'section_1'):
        return self.assembler.assemble(section_id, processed_data)

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