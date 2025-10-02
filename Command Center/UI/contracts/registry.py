#!/usr/bin/env python3
"""Contract registry for the Enhanced Central Command GUI."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class Contract:
    """Represents a contract entry available to the analyst."""

    contract_id: str
    title: str
    workflow: str
    template: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class ContractRegistry:
    """Loads and returns contract definitions."""

    def __init__(self, profile_registry: Any) -> None:
        self.profile_registry = profile_registry
        self.logger = logging.getLogger(__name__)
        self._config_root = Path(getattr(profile_registry, "_config_root", Path(__file__).resolve().parent))
        self._contracts: Dict[str, Contract] = {}
        self._default_contract_id: Optional[str] = None
        self._load_catalog()

    # ------------------------------------------------------------------
    def _load_catalog(self) -> None:
        profile = self.profile_registry.load_profile()
        contracts_payload = profile.payload.get("contracts", {})
        catalog_data: Iterable[Dict[str, Any]] = contracts_payload.get("catalog", [])
        default_id = contracts_payload.get("default")

        # Try loading supplemental catalog from config if present
        config_catalog = self._config_root / "contracts" / "catalog.json"
        if config_catalog.exists():
            try:
                extra_data = json.loads(config_catalog.read_text(encoding="utf-8"))
                if isinstance(extra_data, list):
                    catalog_data = list(catalog_data) + extra_data
            except Exception as exc:  # pragma: no cover
                self.logger.warning("Failed to load catalog.json: %s", exc)

        for entry in catalog_data:
            contract_id = entry.get("contract_id")
            title = entry.get("title") or contract_id or "Contract"
            workflow = entry.get("workflow") or "surveillance"
            template = entry.get("template")
            metadata = dict(entry)
            if not contract_id:
                continue
            self._contracts[contract_id] = Contract(
                contract_id=contract_id,
                title=title,
                workflow=workflow,
                template=template,
                metadata=metadata,
            )

        if default_id and default_id in self._contracts:
            self._default_contract_id = default_id
        elif self._contracts:
            self._default_contract_id = next(iter(self._contracts))
        else:
            # Ensure at least one contract entry exists
            fallback = Contract(
                contract_id="investigation_surveillance",
                title="Surveillance Investigation Agreement",
                workflow="surveillance",
                template=None,
                metadata={"keywords": ["surveillance"]},
            )
            self._contracts[fallback.contract_id] = fallback
            self._default_contract_id = fallback.contract_id

    # ------------------------------------------------------------------
    def list_contracts(self) -> List[Contract]:
        return list(self._contracts.values())

    @property
    def default_contract_id(self) -> str:
        return self._default_contract_id or next(iter(self._contracts))

    def load_contract(self, profile: Any, contract_id: str) -> Contract:
        if contract_id in self._contracts:
            return self._contracts[contract_id]
        self.logger.warning("Unknown contract '%s' requested; returning default", contract_id)
        return self._contracts[self.default_contract_id]
