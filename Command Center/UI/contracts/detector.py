#!/usr/bin/env python3
"""Contract detector heuristics for Enhanced Central Command."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
import logging

from .registry import ContractRegistry, Contract

logger = logging.getLogger(__name__)


@dataclass
class ContractDetection:
    contract: Contract
    confident: bool
    score: float


class ContractDetector:
    """Heuristic contract detector based on artifact filenames."""

    def __init__(self, registry: ContractRegistry, profile) -> None:
        self.registry = registry
        self.profile = profile
        self.logger = logging.getLogger(__name__)

        # Cache catalog for quick scoring
        self._catalog = {contract.contract_id: contract for contract in registry.list_contracts()}

    def detect_from_artifacts(self, artifact_paths: Iterable[Path | str]) -> ContractDetection:
        paths = [Path(p) for p in artifact_paths]
        if not paths:
            contract = self.registry.load_contract(self.profile, self.registry.default_contract_id)
            return ContractDetection(contract=contract, confident=False, score=0.0)

        best_contract: Contract | None = None
        best_hits = 0

        for contract in self._catalog.values():
            keywords = contract.metadata.get("keywords") or [contract.contract_id]
            hits = 0
            for path in paths:
                stem = path.stem.lower()
                if any(keyword.lower() in stem for keyword in keywords):
                    hits += 1
            if hits > best_hits:
                best_hits = hits
                best_contract = contract

        if not best_contract:
            best_contract = self.registry.load_contract(self.profile, self.registry.default_contract_id)
            return ContractDetection(contract=best_contract, confident=False, score=0.0)

        score = min(1.0, best_hits / max(1, len(paths)))
        confident = score >= 0.25
        return ContractDetection(contract=best_contract, confident=confident, score=score)
