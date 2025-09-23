"""Section parsing dispatcher.

Builds structured payload context for each section based on the parsing maps.
This allows the gateway to understand which data is needed, which OpenAI
validation steps should fire, and what the UI needs to confirm before approval.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Callable, Optional


def _merge_dicts(*sources: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Merge dictionaries, ignoring None values."""
    merged: Dict[str, Any] = {}
    for src in sources:
        if isinstance(src, dict):
            for key, value in src.items():
                if value not in (None, "", [], {}):
                    merged[key] = value
    return merged


def _safe_get(mapping: Dict[str, Any], key: str, default: Any) -> Any:
    value = mapping.get(key)
    return value if value is not None else default


def _compute_case_number(client_name: str, contract_date: str) -> str:
    try:
        last = (client_name or "").strip().split()[-1]
        last = last.upper() if last else "CLIENT"
        mm = "00"
        yy = "00"
        if contract_date:
            parts = str(contract_date).split("-")
            if len(parts) >= 2:
                mm = f"{int(parts[1]):02d}"
            if len(parts) >= 1:
                yy = f"{int(parts[0]) % 100:02d}"
        return f"{last}-{mm}-{yy}"
    except Exception:
        return "CLIENT-00-00"


def _default_plan(section_id: str) -> Dict[str, Any]:
    return {
        "inputs": {},
        "openai_triggers": [],
        "ui_checklist": [],
        "dependencies": {},
        "mapping_document": None,
        "notes": f"No parsing plan registered for {section_id}."
    }


def _build_cp(context: Dict[str, Any]) -> Dict[str, Any]:
    processed = context["processed_data"]
    case_data = context["case_data"]
    toolkit = context["toolkit_results"]

    client_info = _merge_dicts(case_data.get("client_info"), processed.get("metadata", {}).get("client_info"))
    client_profile = _merge_dicts(
        case_data.get("client_profile"),
        processed.get("metadata", {}).get("client_profile"),
        toolkit.get("metadata", {}).get("client_profile") if isinstance(toolkit.get("metadata"), dict) else None,
    )
    agency_profile = _merge_dicts(toolkit.get("metadata", {}).get("agency")) if isinstance(toolkit.get("metadata"), dict) else {}
    contract = next(iter(processed.get("contracts", {}).values()), {}) if processed.get("contracts") else {}

    client_name = client_info.get("client_name") or client_profile.get("client_name") or "Client"
    contract_date = contract.get("contract_date") or case_data.get("contract_date")
    case_number = _compute_case_number(client_name, contract_date)

    branding_assets = {
        "logo": client_profile.get("cover_logo_path") or agency_profile.get("logo_path") or processed.get("metadata", {}).get("logo_path"),
        "signature": client_profile.get("signature_path"),
        "profile_photo": client_profile.get("profile_photo_path"),
    }

    inputs = {
        "client_info": client_info,
        "client_profile": client_profile,
        "agency_profile": agency_profile,
        "contract_snapshot": contract,
        "branding_assets": branding_assets,
        "case_number": case_number,
        "source_documents": list(processed.get("contracts", {}).keys()),
    }

    return {
        "inputs": inputs,
        "openai_triggers": [
            {
                "id": "contract_verification",
                "when": "post_ocr",
                "description": "Compare contract OCR fields against intake data before rendering the cover page."
            },
            {
                "id": "name_normalization",
                "when": "pre_render",
                "description": "Normalize client and investigator names for professional presentation."
            }
        ],
        "ui_checklist": [
            "Confirm client and investigator names are spelled correctly.",
            "Verify licensing and contact data match the latest profile.",
            "Approve branding assets (logo, signature, photo)."
        ],
        "dependencies": {
            "feeds_sections": ["section_dp", "section_9"],
            "shares_fields": ["cover_profile", "case_number"]
        },
        "mapping_document": "SECTION_CP_PARSING_MAP.md"
    }


def _build_toc(context: Dict[str, Any]) -> Dict[str, Any]:
    report_type = context["report_type"]
    section_sequence = context["section_sequence"]
    section_states = context["section_states"]
    title_overrides = {
        sid: context["section_outputs"].get(sid, {}).get("manifest", {}).get("title_override")
        for sid, _ in section_sequence
    }

    inputs = {
        "report_type": report_type,
        "section_sequence": section_sequence,
        "title_overrides": {k: v for k, v in title_overrides.items() if v},
        "section_states": section_states,
    }

    return {
        "inputs": inputs,
        "openai_triggers": [
            {
                "id": "title_quality",
                "when": "post_compose",
                "description": "Review custom section titles for tone and professionalism."
            },
            {
                "id": "coverage_gap",
                "when": "post_compose",
                "description": "Ensure the TOC covers mandatory sections for the report type."
            }
        ],
        "ui_checklist": [
            "Confirm section order and optional sections.",
            "Verify custom titles and ensure attachments appear where expected."
        ],
        "dependencies": {
            "feeds_sections": ["section_fr"],
            "shares_fields": ["section_titles"]
        },
        "mapping_document": "SECTION_TOC_PARSING_MAP.md"
    }


def _build_section_1(context: Dict[str, Any]) -> Dict[str, Any]:
    processed = context["processed_data"]
    case_data = context["case_data"]
    toolkit = context["toolkit_results"]

    objectives = case_data.get("objectives") or case_data.get("investigation_goals")
    subjects = case_data.get("subjects") or processed.get("metadata", {}).get("subjects")
    jurisdiction = case_data.get("jurisdiction") or processed.get("metadata", {}).get("jurisdiction")
    compliance = processed.get("metadata", {}).get("compliance_flags") or {}

    inputs = {
        "client_info": case_data.get("client_info", {}),
        "objectives": objectives or [],
        "subjects": subjects or [],
        "jurisdiction": jurisdiction or "Unknown",
        "compliance_flags": compliance,
        "osint_summary": toolkit.get("osint_verification"),
    }

    return {
        "inputs": inputs,
        "openai_triggers": [
            {
                "id": "goal_clarification",
                "when": "post_intake",
                "description": "Translate free-form objectives into standardized investigative goals."
            },
            {
                "id": "compliance_scan",
                "when": "pre_render",
                "description": "Validate jurisdiction against investigator licensing requirements."
            }
        ],
        "ui_checklist": [
            "Confirm objectives and subjects.",
            "Review compliance alerts before approval."
        ],
        "dependencies": {
            "feeds_sections": ["section_3", "section_7", "section_9"],
            "shares_fields": ["subjects", "jurisdiction"]
        },
        "mapping_document": "SECTION_1_PARSING_MAP.md"
    }


def _build_section_2(context: Dict[str, Any]) -> Dict[str, Any]:
    processed = context["processed_data"]
    case_data = context["case_data"]

    prep_plan = case_data.get("preparation_plan") or processed.get("manual_notes", {}).get("prep_plan")
    resources = case_data.get("assignments") or processed.get("manual_notes", {}).get("resource_assignments")
    legal_notices = processed.get("forms", {}).get("legal") if isinstance(processed.get("forms"), dict) else {}

    inputs = {
        "preparation_plan": prep_plan or [],
        "resource_assignments": resources or [],
        "legal_notices": legal_notices or {},
        "equipment": processed.get("metadata", {}).get("equipment_ready"),
        "risk_register": case_data.get("risk_matrix") or processed.get("manual_notes", {}).get("risk")
    }

    return {
        "inputs": inputs,
        "openai_triggers": [
            {
                "id": "plan_consistency",
                "when": "pre_render",
                "description": "Check resource coverage and logistics against objectives."
            },
            {
                "id": "legal_compliance",
                "when": "pre_render",
                "description": "Ensure jurisdictional notices and permissions are attached."
            }
        ],
        "ui_checklist": [
            "Mark each preparation item as ready.",
            "Confirm legal notices and subcontractor credentials."
        ],
        "dependencies": {
            "feeds_sections": ["section_3", "section_6", "section_9"],
            "shares_fields": ["resource_assignments", "legal_notices"]
        },
        "mapping_document": "SECTION_2_PARSING_MAP.md"
    }


def _build_section_3(context: Dict[str, Any]) -> Dict[str, Any]:
    processed = context["processed_data"]
    toolkit = context["toolkit_results"]

    timeline = processed.get("timeline") or processed.get("scan_results", {})
    if isinstance(timeline, dict):
        timeline_events = timeline
    else:
        timeline_events = timeline or []

    inputs = {
        "timeline": timeline_events,
        "log_entries": processed.get("manual_notes", {}).get("logs"),
        "media_assets": {
            "images": processed.get("images", {}),
            "videos": processed.get("videos", {}),
            "audio": processed.get("audio", {})
        },
        "gps_tracks": processed.get("metadata", {}).get("location_tracks"),
        "continuity": toolkit.get("continuity_check")
    }

    return {
        "inputs": inputs,
        "openai_triggers": [
            {
                "id": "narrative_alignment",
                "when": "post_compile",
                "description": "Ensure each log entry references supporting evidence."
            },
            {
                "id": "gap_detection",
                "when": "post_compile",
                "description": "Detect significant gaps in the timeline and prompt for explanations."
            }
        ],
        "ui_checklist": [
            "Confirm every narrative element ties to evidence.",
            "Review flagged timeline gaps."
        ],
        "dependencies": {
            "feeds_sections": ["section_4", "section_6", "section_7", "section_8"],
            "shares_fields": ["timeline", "evidence_links"]
        },
        "mapping_document": "SECTION_3_PARSING_MAP.md"
    }


def _build_section_4(context: Dict[str, Any]) -> Dict[str, Any]:
    toolkit = context["toolkit_results"]
    processed = context["processed_data"]

    sessions = toolkit.get("continuity_check", {}).get("sessions") if isinstance(toolkit.get("continuity_check"), dict) else None
    inputs = {
        "sessions": sessions or [],
        "environmental": processed.get("metadata", {}).get("environmental"),
        "tactics": processed.get("manual_notes", {}).get("tactics"),
        "issues": processed.get("manual_notes", {}).get("issues")
    }

    return {
        "inputs": inputs,
        "openai_triggers": [
            {
                "id": "session_summary",
                "when": "post_compile",
                "description": "Summarize each surveillance session with evidence references."
            },
            {
                "id": "condition_validation",
                "when": "post_compile",
                "description": "Check environmental notes against external data feeds."
            }
        ],
        "ui_checklist": [
            "Adjust session boundaries if necessary.",
            "Confirm issues/lessons learned."
        ],
        "dependencies": {
            "feeds_sections": ["section_7"],
            "shares_fields": ["session_metrics"]
        },
        "mapping_document": "SECTION_4_PARSING_MAP.md"
    }


def _build_section_5(context: Dict[str, Any]) -> Dict[str, Any]:
    processed = context["processed_data"]

    documents = processed.get("contracts", {}).copy()
    documents.update(processed.get("forms", {}))
    metadata_reports = processed.get("metadata", {}).get("reports")

    inputs = {
        "documents": documents,
        "metadata_reports": metadata_reports,
        "custody": processed.get("manual_notes", {}).get("custody"),
        "appendix_candidates": context["case_data"].get("appendices") or []
    }

    return {
        "inputs": inputs,
        "openai_triggers": [
            {
                "id": "doc_classification",
                "when": "post_ocr",
                "description": "Classify supporting documents and summarize key findings."
            },
            {
                "id": "risk_highlight",
                "when": "post_ocr",
                "description": "Flag clauses that introduce liabilities or compliance concerns."
            }
        ],
        "ui_checklist": [
            "Confirm custody trail for critical documents.",
            "Approve document summaries and appendix selections."
        ],
        "dependencies": {
            "feeds_sections": ["section_7", "section_9", "section_dp"],
            "shares_fields": ["document_summaries", "appendices"]
        },
        "mapping_document": "SECTION_5_PARSING_MAP.md"
    }


def _build_section_6(context: Dict[str, Any]) -> Dict[str, Any]:
    processed = context["processed_data"]
    toolkit = context["toolkit_results"]
    case_data = context["case_data"]

    inputs = {
        "time_entries": processed.get("summary", {}).get("time_entries"),
        "expense_receipts": processed.get("manual_notes", {}).get("expenses"),
        "contract_terms": case_data.get("contract") or next(iter(processed.get("contracts", {}).values()), {}),
        "subcontractor_invoices": processed.get("manual_notes", {}).get("subcontractor_invoices"),
        "billing_validation": toolkit.get("billing_validation")
    }

    return {
        "inputs": inputs,
        "openai_triggers": [
            {
                "id": "narrative_reconciliation",
                "when": "pre_render",
                "description": "Check that billed hours align with Section 3 timeline."
            },
            {
                "id": "receipt_verification",
                "when": "pre_render",
                "description": "Summarize receipts and detect duplicates or inconsistencies."
            }
        ],
        "ui_checklist": [
            "Link each line item to supporting evidence.",
            "Confirm totals match contract and retainer."
        ],
        "dependencies": {
            "feeds_sections": ["section_7", "section_fr"],
            "shares_fields": ["billing_totals", "variance_notes"]
        },
        "mapping_document": "SECTION_6_PARSING_MAP.md"
    }


def _build_section_7(context: Dict[str, Any]) -> Dict[str, Any]:
    processed = context["processed_data"]
    case_data = context["case_data"]
    toolkit = context["toolkit_results"]

    inputs = {
        "objective_status": case_data.get("objective_status") or processed.get("manual_notes", {}).get("objective_status"),
        "key_findings": processed.get("manual_notes", {}).get("findings"),
        "recommendations": case_data.get("recommendations") or processed.get("manual_notes", {}).get("recommendations"),
        "risk_limitations": processed.get("metadata", {}).get("compliance_flags"),
        "osint_summary": toolkit.get("osint_verification")
    }

    return {
        "inputs": inputs,
        "openai_triggers": [
            {
                "id": "evidence_support_audit",
                "when": "pre_render",
                "description": "Ensure each finding cites evidence IDs from Section 3/8."
            },
            {
                "id": "tone_compliance",
                "when": "pre_render",
                "description": "Validate the professional tone and required disclaimers."
            }
        ],
        "ui_checklist": [
            "Approve findings and associated evidence references.",
            "Confirm recommendations are actionable."
        ],
        "dependencies": {
            "feeds_sections": ["section_9", "section_fr"],
            "shares_fields": ["findings", "recommendations"]
        },
        "mapping_document": "SECTION_7_PARSING_MAP.md"
    }


def _build_section_8(context: Dict[str, Any]) -> Dict[str, Any]:
    processed = context["processed_data"]

    inputs = {
        "evidence_manifest": {
            "images": processed.get("images", {}),
            "videos": processed.get("videos", {}),
            "audio": processed.get("audio", {}),
            "documents": processed.get("files", {}),
        },
        "media_analysis": processed.get("media_analysis"),
        "chain_of_custody": processed.get("manual_notes", {}).get("custody"),
        "validation_status": processed.get("manual_notes", {}).get("validation"),
        "section_routing": processed.get("manual_notes", {}).get("routing")
    }

    return {
        "inputs": inputs,
        "openai_triggers": [
            {
                "id": "content_verification",
                "when": "post_ocr",
                "description": "Extract key facts and detect tampering cues for each evidence item."
            },
            {
                "id": "chain_integrity",
                "when": "pre_render",
                "description": "Summarize custody sequence and flag breaks."
            }
        ],
        "ui_checklist": [
            "Ensure each evidence item has title, description, custody, and validation status.",
            "Initiate re-validation as needed."
        ],
        "dependencies": {
            "feeds_sections": ["section_3", "section_7", "section_9", "section_dp"],
            "shares_fields": ["evidence_links", "validation_summary"]
        },
        "mapping_document": "SECTION_8_PARSING_MAP.md"
    }


def _build_section_9(context: Dict[str, Any]) -> Dict[str, Any]:
    case_data = context["case_data"]
    section_outputs = context["section_outputs"]

    cover_manifest = section_outputs.get("section_cp", {}).get("manifest", {})
    evidence_summary = section_outputs.get("section_8", {}).get("manifest", {}).get("validation_summary")

    inputs = {
        "cover_profile": cover_manifest.get("cover_profile", {}),
        "compliance_flags": case_data.get("compliance_flags") or {},
        "disclaimer_templates": case_data.get("legal", {}).get("disclaimers") if isinstance(case_data.get("legal"), dict) else None,
        "evidence_validation": evidence_summary,
        "limitations": section_outputs.get("section_7", {}).get("manifest", {}).get("limitations")
    }

    return {
        "inputs": inputs,
        "openai_triggers": [
            {
                "id": "template_integrity",
                "when": "pre_render",
                "description": "Verify all required statutory clauses appear for the jurisdiction."
            },
            {
                "id": "consistency_check",
                "when": "pre_render",
                "description": "Ensure limitation statements align with Section 7 conclusions."
            }
        ],
        "ui_checklist": [
            "Confirm investigator certification wording.",
            "Verify required disclaimers and signature blocks."
        ],
        "dependencies": {
            "feeds_sections": ["section_dp", "section_fr"],
            "shares_fields": ["disclaimers", "certification"]
        },
        "mapping_document": "SECTION_9_PARSING_MAP.md"
    }


def _build_section_dp(context: Dict[str, Any]) -> Dict[str, Any]:
    section_outputs = context["section_outputs"]
    case_data = context["case_data"]

    cover_manifest = section_outputs.get("section_cp", {}).get("manifest", {})
    inputs = {
        "cover_profile": cover_manifest.get("cover_profile", {}),
        "disclosures": case_data.get("legal", {}).get("disclosures") if isinstance(case_data.get("legal"), dict) else None,
        "distribution_list": case_data.get("distribution_list") or [],
        "delivery_instructions": case_data.get("delivery_instructions"),
        "acknowledgment": case_data.get("acknowledgment")
    }

    return {
        "inputs": inputs,
        "openai_triggers": [
            {
                "id": "clause_verification",
                "when": "pre_render",
                "description": "Confirm disclosure text covers confidentiality and client responsibilities."
            }
        ],
        "ui_checklist": [
            "Approve disclosure clauses and distribution list.",
            "Ensure acknowledgment instructions are complete."
        ],
        "dependencies": {
            "feeds_sections": ["section_fr"],
            "shares_fields": ["disclosures", "distribution"]
        },
        "mapping_document": "SECTION_DP_PARSING_MAP.md"
    }


def _build_section_fr(context: Dict[str, Any]) -> Dict[str, Any]:
    section_outputs = context["section_outputs"]
    section_states = context["section_states"]
    processed = context["processed_data"]

    inputs = {
        "approved_sections": {
            sid: data.get("manifest", {})
            for sid, data in section_outputs.items()
            if section_states.get(sid) == "approved"
        },
        "pending_sections": [sid for sid, state in section_states.items() if state != "approved"],
        "attachments": processed.get("manual_notes", {}).get("attachments"),
        "export_settings": context["case_data"].get("export_settings")
    }

    return {
        "inputs": inputs,
        "openai_triggers": [
            {
                "id": "narrative_consistency_sweep",
                "when": "pre_export",
                "description": "Compare executive summary with section conclusions."
            },
            {
                "id": "redaction_check",
                "when": "pre_export",
                "description": "Scan appendices for unredacted PII prior to packaging."
            }
        ],
        "ui_checklist": [
            "Verify all required sections are approved.",
            "Confirm export formats and attachment order."
        ],
        "dependencies": {
            "feeds_sections": [],
            "shares_fields": ["attachments", "export_manifest"]
        },
        "mapping_document": "SECTION_FR_PARSING_MAP.md"
    }


SECTION_BUILDERS: Dict[str, Callable[[Dict[str, Any]], Dict[str, Any]]] = {
    "section_cp": _build_cp,
    "section_toc": _build_toc,
    "section_1": _build_section_1,
    "section_2": _build_section_2,
    "section_3": _build_section_3,
    "section_4": _build_section_4,
    "section_5": _build_section_5,
    "section_6": _build_section_6,
    "section_7": _build_section_7,
    "section_8": _build_section_8,
    "section_9": _build_section_9,
    "section_dp": _build_section_dp,
    "section_fr": _build_section_fr,
}


def build_section_context(
    *,
    section_id: str,
    processed_data: Dict[str, Any],
    case_data: Dict[str, Any],
    toolkit_results: Dict[str, Any],
    report_type: Optional[str],
    section_sequence: List[Any],
    section_outputs: Dict[str, Any],
    section_states: Dict[str, str],
) -> Dict[str, Any]:
    """Build a structured context block for a section based on the parsing maps."""

    builder = SECTION_BUILDERS.get(section_id)
    context = {
        "processed_data": processed_data or {},
        "case_data": case_data or {},
        "toolkit_results": toolkit_results or {},
        "report_type": report_type,
        "section_sequence": section_sequence,
        "section_outputs": section_outputs or {},
        "section_states": section_states or {},
    }

    if not builder:
        plan = _default_plan(section_id)
    else:
        plan = builder(context)

    plan.setdefault("mapping_document", None)
    plan.setdefault("inputs", {})
    plan.setdefault("openai_triggers", [])
    plan.setdefault("ui_checklist", [])
    plan.setdefault("dependencies", {})

    # Provide timestamp for diagnostics
    plan["generated_at"] = datetime.now().isoformat()
    plan.setdefault("notes", None)

    return plan