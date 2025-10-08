#!/usr/bin/env python3
"""Analyst Deck bus bridge for Central Command signal consumption."""

from __future__ import annotations

import json
import logging
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger("AnalystDeckBus")

_STATE_LOCK = threading.Lock()
_SECTION_STATE: Dict[str, Dict[str, Any]] = {}
_CASE_STATE: Dict[str, Dict[str, Any]] = {}
_STATE_PATH = Path(__file__).resolve().with_name("deck_state.json")


def _persist_state() -> None:
    """Persist deck state to disk for offline analysis."""
    payload = {
        "updated_at": datetime.now().isoformat(),
        "sections": _SECTION_STATE,
        "cases": _CASE_STATE,
    }
    tmp_path = _STATE_PATH.with_suffix(".tmp")
    tmp_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp_path.replace(_STATE_PATH)


class DeckBusListener:
    """Subscribe to bus signals and retain Analyst Deck state."""

    def __init__(self, bus: Any) -> None:
        self.bus = bus
        if not bus or not hasattr(bus, "register_signal"):
            logger.warning("Analyst Deck listener initialized without an active bus")
            return
        bus.register_signal("section.data.updated", self._handle_section_data_updated)
        bus.register_signal("narrative.assembled", self._handle_narrative_assembled)
        bus.register_signal("case.snapshot", self._handle_case_snapshot)
        bus.register_signal("mission.status", self._handle_mission_status)
        logger.info("Analyst Deck bus bridge registered listeners")

    def _handle_section_data_updated(self, payload: Dict[str, Any]) -> None:
        if not isinstance(payload, dict):
            return
        section_id = payload.get("section_id")
        if not section_id:
            return
        case_id = payload.get("case_id")
        record = {
            "section_id": section_id,
            "case_id": case_id,
            "received_at": datetime.now().isoformat(),
            "payload": payload,
        }
        with _STATE_LOCK:
            _SECTION_STATE.setdefault(section_id, {}).update(record)
            if case_id:
                _CASE_STATE.setdefault(case_id, {}).setdefault("sections", {})[section_id] = record
            _persist_state()

    def _handle_narrative_assembled(self, payload: Dict[str, Any]) -> None:
        if not isinstance(payload, dict):
            return
        section_id = payload.get("section_id")
        if not section_id:
            return
        case_id = payload.get("case_id")
        record = {
            "section_id": section_id,
            "case_id": case_id,
            "assembled_at": payload.get("assembled_at") or datetime.now().isoformat(),
            "narrative": payload.get("narrative"),
            "summary": payload.get("summary"),
            "structured_data": payload.get("structured_data"),
            "narrative_id": payload.get("narrative_id"),
            "source": payload.get("source"),
        }
        with _STATE_LOCK:
            section_entry = _SECTION_STATE.setdefault(section_id, {})
            section_entry.setdefault("narratives", [])
            section_entry["narratives"].append(record)
            section_entry["last_narrative"] = record
            if case_id:
                case_entry = _CASE_STATE.setdefault(case_id, {})
                case_entry.setdefault("narratives", {})[section_id] = record
            _persist_state()

    def _handle_case_snapshot(self, payload: Dict[str, Any]) -> None:
        if not isinstance(payload, dict):
            return
        case_id = payload.get("case_id") or payload.get("id")
        if not case_id:
            return
        with _STATE_LOCK:
            entry = _CASE_STATE.setdefault(case_id, {})
            snapshots = entry.setdefault("snapshots", [])
            snapshot = dict(payload)
            snapshot.setdefault("received_at", datetime.now().isoformat())
            snapshots.append(snapshot)
            entry["last_snapshot"] = snapshot
            _persist_state()

    def _handle_mission_status(self, payload: Dict[str, Any]) -> None:
        if not isinstance(payload, dict):
            return
        with _STATE_LOCK:
            _SECTION_STATE.setdefault("mission_status", {})["latest"] = {
                "payload": payload,
                "received_at": datetime.now().isoformat(),
            }
            _persist_state()


def initialize(bus: Any) -> DeckBusListener:
    """Entry point used by the Central Command bootstrap."""
    return DeckBusListener(bus)


def get_section_state(section_id: str) -> Dict[str, Any]:
    with _STATE_LOCK:
        return dict(_SECTION_STATE.get(section_id, {}))


def get_all_section_state() -> Dict[str, Dict[str, Any]]:
    with _STATE_LOCK:
        return {sid: dict(data) for sid, data in _SECTION_STATE.items()}


def get_case_state(case_id: str) -> Dict[str, Any]:
    with _STATE_LOCK:
        return dict(_CASE_STATE.get(case_id, {}))


__all__ = [
    "DeckBusListener",
    "initialize",
    "get_section_state",
    "get_all_section_state",
    "get_case_state",
]
