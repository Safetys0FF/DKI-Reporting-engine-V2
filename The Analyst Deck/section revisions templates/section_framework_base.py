"""Base framework templates for DKI Engine section pipelines."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
import logging
from threading import Lock
from time import monotonic
from typing import Any, Callable, Dict, Iterable, Optional, Sequence, Tuple

try:
    from ..deck_bus_listener import get_section_state
except ImportError:  # pragma: no cover

    def get_section_state(section_id: str) -> Dict[str, Any]:
        return {}


class LifecycleState(Enum):
    """Lifecycle states for section engines."""

    CREATED = auto()
    INITIALIZING = auto()
    ACTIVE = auto()
    RESTING = auto()
    SHUTTING_DOWN = auto()
    SHUTDOWN = auto()
    FAULTED = auto()


@dataclass(frozen=True)
class StageDefinition:
    """Describes a single stage the section executes."""

    name: str
    description: str
    checkpoint: str
    guardrails: Tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class CommunicationContract:
    """Signals and channels used to coordinate with the gateway."""

    prepare_signal: str
    input_channels: Tuple[str, ...]
    output_signal: str
    revision_signal: str


@dataclass(frozen=True)
class PersistenceContract:
    """Durable storage expectations for section state."""

    persistence_key: str
    durable_paths: Tuple[str, ...]


@dataclass(frozen=True)
class FactGraphContract:
    """Shared fact graph interactions (publish/subscribe)."""

    publishes: Tuple[str, ...]
    subscribes: Tuple[str, ...]


@dataclass(frozen=True)
class OrderContract:
    """Declares execution and export ordering constraints for a section."""

    execution_after: Tuple[str, ...] = field(default_factory=tuple)
    export_after: Tuple[str, ...] = field(default_factory=tuple)
    export_priority: int = 0  # Lower numbers appear earlier in exports.


class SectionFramework:
    """Abstract template for section orchestration."""

    SECTION_ID: str = ""
    MODULE_ADDRESS: Optional[str] = None
    BUS_SECTION_ID: Optional[str] = None
    MAX_RERUNS: int = 3
    STAGES: Tuple[StageDefinition, ...] = ()
    COMMUNICATION: Optional[CommunicationContract] = None
    PERSISTENCE: Optional[PersistenceContract] = None
    FACT_GRAPH: Optional[FactGraphContract] = None
    ORDER: Optional[OrderContract] = None
    IMMUTABILITY_FLAG: str = "signed_off"

    def __init__(
        self,
        gateway: Any,
        *,
        module_address: Optional[str] = None,
        communicator_initializer: Optional[Callable[..., Any]] = None,
        marshal_client: Optional[Any] = None,
        marshal_address: Optional[str] = None,
        warden_client: Optional[Any] = None,
        dependency_initializers: Optional[Dict[str, Callable[..., Any]]] = None,
        mayday_channel: Optional[str] = None,
        fault_channel: Optional[str] = None,
        queue_client: Optional[Any] = None,
        storage: Optional[Any] = None,
        fact_graph: Optional[Any] = None,
    ) -> None:
        self.gateway = gateway
        self.ecc = getattr(gateway, "ecc", None)
        self.queue_client = queue_client
        self.storage = storage
        self.fact_graph = fact_graph
        self.marshal_client = marshal_client
        self.marshal_address = marshal_address
        self.warden_client = warden_client
        self._communicator_initializer = communicator_initializer
        self._dependency_initializers = dependency_initializers or {}
        self.dependencies: Dict[str, Any] = {}
        self.revision_depth: int = 0
        self.signed_payload_id: Optional[str] = None
        self.logger = logging.getLogger(self.__class__.__name__)
        self._lifecycle_state: LifecycleState = LifecycleState.CREATED
        self._state_lock = Lock()

        resolved_address = module_address or self.MODULE_ADDRESS
        if not resolved_address:
            resolved_address = self.bus_section_id() or self.SECTION_ID or "UNKNOWN"
        self.module_address = resolved_address
        self.fault_channel = fault_channel or f"section.fault.{self.module_address}"
        self.mayday_channel = mayday_channel or f"section.mayday.{self.module_address}"

        self.communicator: Optional[Any] = None
        self.bus: Optional[Any] = None
        if communicator_initializer:
            try:
                self.communicator = communicator_initializer(resolved_address)
                self.bus = getattr(self.communicator, "bus_connection", None)
            except Exception as exc:  # pragma: no cover - fatal at runtime
                self.logger.exception("Failed to initialize communicator for %s: %s", resolved_address, exc)
                self._transition_state(LifecycleState.FAULTED)

        self._rest_requested = False
        self._rest_reason: Optional[str] = None
        self._last_activity = monotonic()

    # ------------------------------------------------------------------
    # Lifecycle state management
    # ------------------------------------------------------------------
    def lifecycle_state(self) -> LifecycleState:
        with self._state_lock:
            return self._lifecycle_state

    def _transition_state(self, new_state: LifecycleState) -> None:
        with self._state_lock:
            if self._lifecycle_state == new_state:
                return
            self.logger.debug(
                "Section %s state transition: %s -> %s",
                self.SECTION_ID or self.module_address,
                self._lifecycle_state,
                new_state,
            )
            self._lifecycle_state = new_state
            self._last_activity = monotonic()

    # ------------------------------------------------------------------
    # Dependency handling
    # ------------------------------------------------------------------
    def _initialize_dependencies(self) -> Dict[str, Any]:
        initialized: Dict[str, Any] = {}
        for name, initializer in self._dependency_initializers.items():
            if not callable(initializer):
                self.logger.warning("Dependency initializer for %s is not callable", name)
                continue
            try:
                dependency = initializer(
                    module_address=self.module_address,
                    communicator=self.communicator,
                    bus=self.bus,
                    gateway=self.gateway,
                )
                self.dependencies[name] = dependency
                initialized[name] = {
                    "status": "initialized",
                    "details": getattr(dependency, "status", "ok"),
                }
            except Exception as exc:
                self.logger.exception("Failed to initialize dependency %s: %s", name, exc)
                initialized[name] = {
                    "status": "error",
                    "details": str(exc),
                }
        return initialized

    def get_dependency(self, name: str) -> Any:
        return self.dependencies.get(name)

    @classmethod
    def bus_section_id(cls) -> Optional[str]:
        if cls.BUS_SECTION_ID:
            return cls.BUS_SECTION_ID
        section_id = getattr(cls, "SECTION_ID", "")
        if section_id.startswith("section_"):
            parts = section_id.split("_")
            if len(parts) >= 2:
                return f"section_{parts[1]}"
        return section_id or None

    @classmethod
    def get_bus_state(cls) -> Dict[str, Any]:
        bus_id = cls.bus_section_id()
        if not bus_id:
            return {}
        try:
            return get_section_state(bus_id)
        except Exception as exc:  # pragma: no cover
            logging.getLogger(cls.__name__).warning("Failed to fetch bus state for %s: %s", bus_id, exc)
            return {}

    def get_latest_bus_state(self) -> Dict[str, Any]:
        return self.get_bus_state()

    def _augment_with_bus_context(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        bus_state = self.get_latest_bus_state()
        if not bus_state:
            return inputs
        enriched = dict(inputs)
        enriched.setdefault("bus_state", bus_state)
        payload = bus_state.get("payload") or {}
        if isinstance(payload, dict):
            enriched.setdefault("section_payload", payload.get("structured_data") or payload)
            for key, value in payload.items():
                enriched.setdefault(key, value)
        return enriched

    # ------------------------------------------------------------------
    # Lifecycle hooks to be implemented by sections
    # ------------------------------------------------------------------
    def prepare(self, context: Dict[str, Any]) -> None:
        """Confirm prerequisites before executing stages."""

    def execute_stage(self, stage: StageDefinition, context: Dict[str, Any]) -> None:
        """Run an individual stage. Override to apply section logic."""

    def build_payload(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Return the structured payload to publish to the gateway."""
        raise NotImplementedError

    def publish(self, payload: Dict[str, Any]) -> None:
        """Persist, emit signals, and mark completion."""
        raise NotImplementedError

    def handle_revision(self, reason: str, context: Dict[str, Any]) -> None:
        """Respond to downstream revision requests while enforcing guardrails."""
        if self.revision_depth >= self.MAX_RERUNS:
            raise RuntimeError(f"{self.SECTION_ID} exceeded max reruns ({self.MAX_RERUNS})")
        self.revision_depth += 1

    def lock_payload(self, payload_id: str) -> None:
        """Record immutable sign-off for the given payload identifier."""
        self.signed_payload_id = payload_id

    def persist_state(self, snapshot: Dict[str, Any]) -> None:
        """Write state to durable storage. Override to integrate real persistence."""

    def update_fact_graph(self, facts: Iterable[Dict[str, Any]]) -> None:
        """Publish updates to the shared fact graph."""

    # ------------------------------------------------------------------
    # Ordering helpers
    # ------------------------------------------------------------------
    @classmethod
    def execution_dependencies(cls) -> Tuple[str, ...]:
        return cls.ORDER.execution_after if cls.ORDER else tuple()

    @classmethod
    def export_dependencies(cls) -> Tuple[str, ...]:
        return cls.ORDER.export_after if cls.ORDER else tuple()

    @classmethod
    def export_priority(cls) -> int:
        return cls.ORDER.export_priority if cls.ORDER else 0

    # ------------------------------------------------------------------
    # Utility helpers
    # ------------------------------------------------------------------
    def ensure_order_lock(self, prerequisites: Sequence[str]) -> None:
        """Validate that prerequisite sections have completed before execution."""
        # Implementation left to concrete subclass / real system integration.

    def queue_signal(self, signal: str, payload: Dict[str, Any]) -> None:
        """Dispatch an asynchronous signal via the queue client."""
        if self.queue_client and hasattr(self.queue_client, "queue"):
            try:
                self.queue_client.queue(signal, payload)
            except Exception:  # pragma: no cover
                self.logger.exception("Queue dispatch failed for signal %s", signal)

    def load_inputs(self) -> Dict[str, Any]:
        """Pull required inputs from the gateway based on COMMUNICATION contract."""
        raise NotImplementedError

    # ------------------------------------------------------------------
    # Lifecycle orchestration helpers
    # ------------------------------------------------------------------
    def run_baseline_initialization(self) -> Dict[str, Any]:
        """Run self-initialization and report status to Marshall."""
        if self.lifecycle_state() in {LifecycleState.ACTIVE, LifecycleState.RESTING}:
            return {"status": "already_initialized"}

        self._transition_state(LifecycleState.INITIALIZING)
        results = {
            "section_id": self.SECTION_ID,
            "module_address": self.module_address,
            "dependencies": {},
            "communicator": "connected" if self.communicator else "not_connected",
            "bus_registered": bool(self.bus),
        }

        dependency_results = self._initialize_dependencies()
        results["dependencies"] = dependency_results
        results["status"] = "passed"

        for outcome in dependency_results.values():
            if outcome.get("status") != "initialized":
                results["status"] = "failed"
                break

        if results["status"] == "passed":
            self._transition_state(LifecycleState.ACTIVE)
        else:
            self._transition_state(LifecycleState.FAULTED)

        self._notify_marshal("section.init.result", results)
        return results

    def soft_shutdown(self, reason: str = "system_shutdown") -> Dict[str, Any]:
        """Gracefully shut down the section engine."""
        if self.lifecycle_state() in {LifecycleState.SHUTDOWN, LifecycleState.SHUTTING_DOWN}:
            return {"status": "already_shutdown", "reason": reason}

        self._transition_state(LifecycleState.SHUTTING_DOWN)
        shutdown_report = {
            "section_id": self.SECTION_ID,
            "module_address": self.module_address,
            "reason": reason,
            "dependencies": {},
        }

        for name, dependency in list(self.dependencies.items()):
            status = "released"
            try:
                if hasattr(dependency, "shutdown"):
                    dependency.shutdown()
                elif hasattr(dependency, "close"):
                    dependency.close()
            except Exception as exc:  # pragma: no cover
                status = f"error: {exc}"
                self.logger.exception("Failed to shutdown dependency %s: %s", name, exc)
            shutdown_report["dependencies"][name] = status

        self._transition_state(LifecycleState.SHUTDOWN)
        shutdown_report["status"] = "completed"
        self._notify_marshal("section.shutdown", shutdown_report)
        return shutdown_report

    def enter_rest_state(self, reason: str = "") -> None:
        """Place the section into a rest/sleep state while other sections execute."""
        if self.lifecycle_state() == LifecycleState.RESTING:
            return
        self._rest_requested = True
        self._rest_reason = reason
        self._transition_state(LifecycleState.RESTING)
        self._notify_marshal(
            "section.resting",
            {
                "section_id": self.SECTION_ID,
                "module_address": self.module_address,
                "reason": reason,
            },
        )

    def resume_from_rest(self) -> None:
        """Resume section work after a rest/sleep window."""
        if self.lifecycle_state() != LifecycleState.RESTING:
            return
        self._rest_requested = False
        self._rest_reason = None
        self._transition_state(LifecycleState.ACTIVE)
        self._notify_marshal(
            "section.resume",
            {
                "section_id": self.SECTION_ID,
                "module_address": self.module_address,
            },
        )

    # ------------------------------------------------------------------
    # Fault handling helpers
    # ------------------------------------------------------------------
    def emit_fault(
        self,
        fault_code: str,
        *,
        severity: str = "ERROR",
        detail: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Relay a section fault through Marshall with a mayday fallback."""
        payload = {
            "section_id": self.SECTION_ID,
            "module_address": self.module_address,
            "fault_code": fault_code,
            "severity": severity,
            "detail": detail,
            "context": context or {},
        }
        self._notify_marshal(self.fault_channel, payload)

    def emit_mayday(
        self,
        message: str,
        *,
        fault_code: Optional[str] = None,
        severity: str = "CRITICAL",
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Send a direct mayday signal when fault routing fails."""
        payload = {
            "section_id": self.SECTION_ID,
            "module_address": self.module_address,
            "message": message,
            "fault_code": fault_code,
            "severity": severity,
            "context": context or {},
        }
        if self.marshal_client and hasattr(self.marshal_client, "receive_mayday"):
            try:
                self.marshal_client.receive_mayday(payload)
                return
            except Exception:  # pragma: no cover
                self.logger.exception("Marshal receive_mayday failed; falling back to communicator")

        if self.communicator and hasattr(self.communicator, "send_sos_fault"):
            try:
                code = fault_code or f"{self.module_address}-SOS"
                self.communicator.send_sos_fault(code, message)
            except Exception as exc:  # pragma: no cover
                self.logger.exception("Failed to emit mayday for %s: %s", self.module_address, exc)

    # ------------------------------------------------------------------
    # Internal signal helpers
    # ------------------------------------------------------------------
    def _notify_marshal(self, topic: str, payload: Dict[str, Any]) -> None:
        """Dispatch payload to Marshall (preferred) or fallback to communicator."""
        payload.setdefault("timestamp", monotonic())
        if self.marshal_client:
            handler_names = (
                "relay_section_signal",
                "queue_section_signal",
                "handle_section_signal",
            )
            for handler_name in handler_names:
                handler = getattr(self.marshal_client, handler_name, None)
                if callable(handler):
                    try:
                        handler(topic, payload)
                        return
                    except Exception:  # pragma: no cover
                        self.logger.exception("Marshal handler %s failed for topic %s", handler_name, topic)

        if self.communicator and hasattr(self.communicator, "send_signal"):
            target = self.marshal_address or "2-3"
            try:
                message = f"{topic}:{payload}"
                self.communicator.send_signal(target, "STATUS", message=message)
            except Exception as exc:  # pragma: no cover
                self.logger.exception("Failed to notify marshal via communicator for %s: %s", topic, exc)

    # ------------------------------------------------------------------
    # Activity helpers
    # ------------------------------------------------------------------
    def seconds_since_activity(self) -> float:
        return monotonic() - self._last_activity


__all__ = [
    "StageDefinition",
    "CommunicationContract",
    "PersistenceContract",
    "FactGraphContract",
    "OrderContract",
    "SectionFramework",
    "LifecycleState",
]
