# ==== signal_types.py ====

from enum import Enum

class SignalType(Enum):
    EXECUTE = "EXECUTE"
    CLASSIFY = "CLASSIFY"
    FINALIZE = "FINALIZE"
    NARRATE = "NARRATE"
    VALIDATE = "VALIDATE"
    STATUS = "STATUS"


# ==== signal.py ====

from datetime import datetime

class Signal:
    def __init__(self, type, target, source, payload, case_id):
        self.type = type
        self.target = target
        self.source = source
        self.payload = payload
        self.case_id = case_id
        self.timestamp = datetime.utcnow().isoformat()

    def to_dict(self):
        return {
            "type": self.type,
            "target": self.target,
            "source": self.source,
            "payload": self.payload,
            "case_id": self.case_id,
            "timestamp": self.timestamp
        }


# ==== section_base.py ====

class SectionBase:
    def on_signal(self, signal: dict) -> dict:
        raise NotImplementedError("Each section must implement on_signal")


# ==== section_5_module.py ====

from section_base import SectionBase

class Section5Module(SectionBase):
    def on_signal(self, signal: dict) -> dict:
        if not signal.get("payload"):
            return {
                "status": "NO_ACTION",
                "narrative": "No financial documents were available or required.",
                "origin": "section_5",
                "timestamp": signal.get("timestamp")
            }

        # Logic to process payload goes here
        return {
            "status": "COMPLETED",
            "narrative": "Financial documents reviewed and added to summary.",
            "origin": "section_5",
            "timestamp": signal.get("timestamp")
        }


# ==== registry.py ====

from section_5_module import Section5Module

SECTION_REGISTRY = {
    "section_5": Section5Module()
}


# ==== gateway.py ====

from registry import SECTION_REGISTRY

class GatewayController:
    def __init__(self, ecc):
        self.ecc = ecc

    def dispatch(self, signal: dict) -> dict:
        if not self.ecc.can_run(signal["target"]):
            return {
                "status": "BLOCKED",
                "origin": signal["target"],
                "timestamp": signal["timestamp"]
            }

        handler = SECTION_REGISTRY.get(signal["target"])
        if not handler:
            return {
                "status": "FAILED",
                "origin": signal["target"],
                "error": "No handler",
                "timestamp": signal["timestamp"]
            }

        return handler.on_signal(signal)


# ==== intake_agent.py ====

from gateway import GatewayController
from ecosystem_controller import EcosystemController  # Assuming ECC already exists
from signal_types import SignalType
from signal import Signal

class IntakeAgent:
    def __init__(self):
        self.ecc = EcosystemController()
        self.gateway = GatewayController(ecc=self.ecc)

    def run_case(self, evidence_payload):
        signal = Signal(
            type=SignalType.EXECUTE.value,
            target="section_5",
            source="intake_pipeline",
            payload=evidence_payload,
            case_id="CASE_001"
        )
        result = self.gateway.dispatch(signal.to_dict())
        print("[GATEWAY RESPONSE]", result)


# Example run
if __name__ == "__main__":
    agent = IntakeAgent()
    dummy_payload = {"file": "contract.pdf"}
    agent.run_case(dummy_pa