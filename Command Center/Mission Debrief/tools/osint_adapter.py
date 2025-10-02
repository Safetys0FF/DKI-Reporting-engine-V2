#!/usr/bin/env python3
"""OSINT adapter shim."""

from __future__ import annotations

from .api_manager_adapter import OsintAdapter as OsintAdapter  # re-export

__all__ = ["OsintAdapter"]
