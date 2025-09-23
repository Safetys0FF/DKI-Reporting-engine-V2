"""Base framework templates for DKI Engine section pipelines."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, Optional, Sequence, Tuple


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
    """Abstract template for section orchestration.

    Subclasses should override the class attributes to describe their pipeline
    and implement the hook methods to apply section-specific logic.
    """

    SECTION_ID: str = ""
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
        queue_client: Optional[Any] = None,
        storage: Optional[Any] = None,
        fact_graph: Optional[Any] = None,
    ) -> None:
        self.gateway = gateway
        self.queue_client = queue_client
        self.storage = storage
        self.fact_graph = fact_graph
        self.revision_depth: int = 0
        self.signed_payload_id: Optional[str] = None

    # ------------------------------------------------------------------
    # Lifecycle hooks
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
            raise RuntimeError(
                f"{self.SECTION_ID} exceeded max reruns ({self.MAX_RERUNS})"
            )
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
        # Implementation placeholder for async infrastructure.

    def load_inputs(self) -> Dict[str, Any]:
        """Pull required inputs from the gateway based on COMMUNICATION contract."""
        raise NotImplementedError


__all__ = [
    "StageDefinition",
    "CommunicationContract",
    "PersistenceContract",
    "FactGraphContract",
    "OrderContract",
    "SectionFramework",
]
