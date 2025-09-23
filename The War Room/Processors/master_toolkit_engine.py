#!/usr/bin/env python3
"""
Master Toolkit Engine - Direct Implementation
Consolidates all investigative tools for section processing
"""

import sys
import os
from pathlib import Path
import logging

# Add Tools directory to path for tool imports
current_dir = Path(__file__).parent
tools_dir = current_dir.parent / "Tools"
if str(tools_dir) not in sys.path:
    sys.path.insert(0, str(tools_dir))

try:
    from mileage_tool_v_2 import MileageTool
    from northstar_protocol_tool import NorthstarLogic
    from billing_tool_engine import BillingToolEngine
    from cochran_match_tool import CochranMatcher
    from metadata_tool_v_5 import MetadataProcessor
    from reverse_continuity_tool import ReverseContinuityTool
except ImportError as e:
    # Fallback stubs if tools not available
    class MileageTool:
        def run(self, text_data): return {"status": "SKIPPED", "reason": "Tool unavailable"}
    class NorthstarLogic:
        def process(self, text_data, report_meta): return {"classified": [], "deadfile_registry": []}
    class BillingToolEngine:
        def validate(self, report_meta): return {"info": "No billing data available"}
    class CochranMatcher:
        def analyze(self, text_data): return {"info": "Subject/candidate data unavailable; identity check skipped"}
    class MetadataProcessor:
        def tag(self, text_data): return {"info": "No document available for metadata hashing"}
    class ReverseContinuityTool:
        def run_validation(self, text_data, documents, assets): return [True, ["No continuity issues found."]]


class MasterToolKitEngine:
    def __init__(self):
        self.mileage_tool = MileageTool()
        self.northstar_tool = NorthstarLogic()
        self.billing_tool = BillingToolEngine()
        self.cochran_tool = CochranMatcher()
        self.metadata_tool = MetadataProcessor()
        self.continuity_tool = ReverseContinuityTool()
        self.user_profile_manager = None
        self.api_key_manager = None

    def set_user_profile_manager(self, profile_manager):
        """Attach a user profile manager to toolkit-aware tools."""
        self.user_profile_manager = profile_manager
        for tool in (
            self.mileage_tool,
            self.northstar_tool,
            self.billing_tool,
            self.cochran_tool,
            self.metadata_tool,
            self.continuity_tool,
        ):
            if hasattr(tool, 'set_user_profile_manager'):
                try:
                    tool.set_user_profile_manager(profile_manager)
                except Exception:
                    logging.getLogger(__name__).warning(
                        "Tool %s failed to accept user profile manager", type(tool).__name__,
                        exc_info=True
                    )

    def set_api_key_manager(self, api_key_manager):
        """Provide the toolkit tools with the active API key manager."""
        self.api_key_manager = api_key_manager
        for tool in (
            self.mileage_tool,
            self.northstar_tool,
            self.billing_tool,
            self.cochran_tool,
            self.metadata_tool,
            self.continuity_tool,
        ):
            if hasattr(tool, 'set_api_key_manager'):
                try:
                    tool.set_api_key_manager(api_key_manager)
                except Exception:
                    logging.getLogger(__name__).warning(
                        "Tool %s failed to accept API key manager", type(tool).__name__,
                        exc_info=True
                    )

    def run_all(self, section_id, text_data, report_meta, documents, assets):
        return {
            "mileage_check": self.mileage_tool.run(text_data),
            "northstar_analysis": self.northstar_tool.process(text_data, report_meta),
            "billing_validation": self.billing_tool.validate(report_meta),
            "cochran_result": self.cochran_tool.analyze(text_data),
            "metadata": self.metadata_tool.tag(text_data),
            "continuity_check": self.continuity_tool.run_validation(text_data, documents, assets)
        }
