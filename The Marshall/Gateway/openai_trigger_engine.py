"""OpenAI trigger dispatcher for section parsing plans."""
from __future__ import annotations

import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable

logger = logging.getLogger(__name__)

# Ensure root project on sys.path so we can reuse ai_integration
REPO_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT_STR = str(REPO_ROOT)
if REPO_ROOT_STR not in sys.path:
    sys.path.append(REPO_ROOT_STR)
TOOLS_DIR = REPO_ROOT / 'Tools'
TOOLS_DIR_STR = str(TOOLS_DIR)
if TOOLS_DIR.exists() and TOOLS_DIR_STR not in sys.path:
    sys.path.append(TOOLS_DIR_STR)

try:
    from ai_integration import AIAnalysisEngine  # type: ignore
    HAVE_AI_ENGINE = True
except Exception as e:
    logger.warning(f"AI integration not available: {e}")
    AIAnalysisEngine = None  # type: ignore
    HAVE_AI_ENGINE = False

class OpenAITriggerDispatcher:
    """Runs OpenAI (and other AI) validations described in parsing plans."""

    def __init__(self, base_config: Optional[Dict[str, Any]] = None):
        self.base_config = base_config or {}
        self.api_keys: Dict[str, Any] = {}
        self.ai_engine: Optional[AIAnalysisEngine] = None  # type: ignore

    def configure(self, *, api_keys: Optional[Dict[str, Any]] = None, case_data: Optional[Dict[str, Any]] = None):
        """Refresh API keys / config before running triggers."""
        if api_keys:
            self.api_keys.update(api_keys)
        if case_data:
            # stash case metadata if needed later
            self.base_config.setdefault('case_meta', case_data)
        if self.ai_engine is not None:
            return
        if HAVE_AI_ENGINE:
            cfg = {}
            if 'openai_api_key' in self.api_keys:
                cfg['openai_api_key'] = self.api_keys.get('openai_api_key')
            elif 'openai_api_key' in self.base_config:
                cfg['openai_api_key'] = self.base_config['openai_api_key']
            try:
                self.ai_engine = AIAnalysisEngine(cfg)
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning(f"AIAnalysisEngine init failed: {exc}")
                self.ai_engine = None

    # ------------------------------------------------------------------
    def run_triggers(
        self,
        section_id: str,
        plan: Dict[str, Any],
        payload: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Execute triggers defined in the parsing plan."""

        results: List[Dict[str, Any]] = []
        triggers = plan.get('openai_triggers') or []
        for trigger in triggers:
            trigger_id = trigger.get('id') or 'unknown_trigger'
            handler = TRIGGER_HANDLERS.get(trigger_id, _default_handler)
            try:
                result = handler(self, section_id, trigger, payload)
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning(f"Trigger {trigger_id} failed: {exc}")
                result = {
                    'id': trigger_id,
                    'status': 'error',
                    'notes': str(exc),
                    'timestamp': datetime.now().isoformat(),
                }
            results.append(result)
        return results

    # ------------------------------------------------------------------
    def analyze_text(self, text: str, analysis_type: str) -> Dict[str, Any]:
        if not text or not text.strip():
            return {'error': 'no_text'}
        if not HAVE_AI_ENGINE:
            return {'error': 'ai_engine_unavailable'}
        if self.ai_engine is None:
            self.configure()
        if self.ai_engine is None:
            return {'error': 'ai_engine_unavailable'}
        try:
            return self.ai_engine.analyze_document_content(text, analysis_type=analysis_type)
        except Exception as exc:
            logger.warning(f"AI analysis failed: {exc}")
            return {'error': str(exc)}


# ----------------------------------------------------------------------
# Helper functions for trigger handlers
# ----------------------------------------------------------------------

def _join_text_from_documents(docs: Optional[Dict[str, Any]]) -> str:
    if not isinstance(docs, dict):
        return ''
    parts: List[str] = []
    for item in docs.values():
        if isinstance(item, dict):
            for key in ('text', 'extracted_text', 'aggregated_text'):
                value = item.get(key)
                if isinstance(value, str) and value.strip():
                    parts.append(value.strip())
            blocks = item.get('text_blocks')
            if isinstance(blocks, list):
                parts.extend([str(b).strip() for b in blocks if str(b).strip()])
    return '\n\n'.join(parts)


def _timeline_text(payload: Dict[str, Any]) -> str:
    timeline = payload.get('summary', {}).get('timeline') or payload.get('timeline')
    if isinstance(timeline, str):
        return timeline
    if isinstance(timeline, dict):
        parts = []
        for key, value in timeline.items():
            parts.append(f"{key}: {value}")
        return '\n'.join(parts)
    if isinstance(timeline, list):
        return '\n'.join([str(item) for item in timeline])
    return ''


def _make_result(trigger_id: str, status: str, notes: str = '', extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    result = {
        'id': trigger_id,
        'status': status,
        'notes': notes,
        'timestamp': datetime.now().isoformat(),
    }
    if extra:
        result.update(extra)
    return result


def _analysis_handler(dispatcher: OpenAITriggerDispatcher, trigger_id: str, payload: Dict[str, Any], text: str, analysis_type: str, success_note: str) -> Dict[str, Any]:
    if not text.strip():
        return _make_result(trigger_id, 'skipped', 'No relevant text available')
    analysis = dispatcher.analyze_text(text, analysis_type)
    if 'error' in analysis:
        return _make_result(trigger_id, 'error', analysis['error'])
    summary = analysis.get('summary') or success_note
    return _make_result(trigger_id, 'completed', summary, {'analysis': analysis})


# ----------------------------------------------------------------------
# Trigger handlers
# ----------------------------------------------------------------------

def handle_contract_verification(dispatcher, section_id, trigger, payload):
    text = _join_text_from_documents(payload.get('contracts'))
    if not text:
        text = _join_text_from_documents(payload.get('files'))
    return _analysis_handler(dispatcher, trigger['id'], payload, text, 'investigation', 'Contract analysis completed')


def handle_name_normalization(dispatcher, section_id, trigger, payload):
    text = payload.get('client_info', {}).get('client_name') or ''
    text += '\n' + payload.get('client_profile', {}).get('investigator_name', '')
    if not text.strip():
        return _make_result(trigger['id'], 'skipped', 'No names to normalize')
    analysis = dispatcher.analyze_text(text, 'summary')
    if 'error' in analysis:
        return _make_result(trigger['id'], 'error', analysis['error'])
    normalized = ', '.join(set(analysis.get('entities', {}).get('persons', []))) if isinstance(analysis.get('entities'), dict) else text
    return _make_result(trigger['id'], 'completed', f"Normalized names: {normalized}", {'analysis': analysis})


def handle_title_quality(dispatcher, section_id, trigger, payload):
    titles = payload.get('section_sequence') or []
    if not titles:
        return _make_result(trigger['id'], 'skipped', 'No section sequence available')
    title_text = '\n'.join([name for _, name in titles]) if isinstance(titles[0], (list, tuple)) else '\n'.join(titles)
    return _analysis_handler(dispatcher, trigger['id'], payload, title_text, 'summary', 'Titles reviewed')


def handle_coverage_gap(dispatcher, section_id, trigger, payload):
    titles = payload.get('section_sequence') or []
    missing = []
    required = {'section_cp', 'section_3', 'section_8'}
    available_ids = {sid for sid, _ in titles} if titles and isinstance(titles[0], (list, tuple)) else set()
    for req in required:
        if req not in available_ids:
            missing.append(req)
    if missing:
        return _make_result(trigger['id'], 'warning', f"Missing required sections: {', '.join(missing)}")
    return _make_result(trigger['id'], 'completed', 'All mandatory sections present')


def handle_goal_clarification(dispatcher, section_id, trigger, payload):
    goals = payload.get('objectives') or payload.get('investigation_goals') or []
    text = '\n'.join(goals) if isinstance(goals, list) else str(goals)
    return _analysis_handler(dispatcher, trigger['id'], payload, text, 'investigation', 'Goals clarified')


def handle_compliance_scan(dispatcher, section_id, trigger, payload):
    jurisdiction = payload.get('jurisdiction') or ''
    license_info = payload.get('client_profile', {}).get('investigator_license') if isinstance(payload.get('client_profile'), dict) else ''
    text = f"Jurisdiction: {jurisdiction}\nLicense: {license_info}"
    return _analysis_handler(dispatcher, trigger['id'], payload, text, 'summary', 'Compliance check complete')


def handle_plan_consistency(dispatcher, section_id, trigger, payload):
    plan_items = payload.get('preparation_plan') or []
    text = '\n'.join([str(item) for item in plan_items])
    return _analysis_handler(dispatcher, trigger['id'], payload, text, 'surveillance', 'Preparation plan reviewed')


def handle_legal_compliance(dispatcher, section_id, trigger, payload):
    notices = payload.get('legal_notices') or {}
    text = '\n'.join([str(v) for v in notices.values()]) if isinstance(notices, dict) else str(notices)
    return _analysis_handler(dispatcher, trigger['id'], payload, text, 'summary', 'Legal notices checked')


def handle_narrative_alignment(dispatcher, section_id, trigger, payload):
    text = _timeline_text(payload)
    return _analysis_handler(dispatcher, trigger['id'], payload, text, 'surveillance', 'Timeline alignment reviewed')


def handle_gap_detection(dispatcher, section_id, trigger, payload):
    timeline_text = _timeline_text(payload)
    if not timeline_text.strip():
        return _make_result(trigger['id'], 'skipped', 'No timeline data')
    analysis = dispatcher.analyze_text(timeline_text, 'summary')
    if 'error' in analysis:
        return _make_result(trigger['id'], 'error', analysis['error'])
    return _make_result(trigger['id'], 'completed', 'Gap analysis complete', {'analysis': analysis})


def handle_session_summary(dispatcher, section_id, trigger, payload):
    sessions = payload.get('sessions') or []
    text = '\n'.join([str(session) for session in sessions])
    return _analysis_handler(dispatcher, trigger['id'], payload, text, 'surveillance', 'Session summaries generated')


def handle_condition_validation(dispatcher, section_id, trigger, payload):
    environmental = payload.get('environmental')
    text = str(environmental)
    return _analysis_handler(dispatcher, trigger['id'], payload, text, 'summary', 'Environmental conditions reviewed')


def handle_doc_classification(dispatcher, section_id, trigger, payload):
    text = _join_text_from_documents(payload.get('documents'))
    return _analysis_handler(dispatcher, trigger['id'], payload, text, 'investigation', 'Documents classified')


def handle_risk_highlight(dispatcher, section_id, trigger, payload):
    text = _join_text_from_documents(payload.get('documents'))
    return _analysis_handler(dispatcher, trigger['id'], payload, text, 'summary', 'Risk clauses highlighted')


def handle_narrative_reconciliation(dispatcher, section_id, trigger, payload):
    text = _timeline_text(payload)
    return _analysis_handler(dispatcher, trigger['id'], payload, text, 'summary', 'Billing narrative reconciled')


def handle_receipt_verification(dispatcher, section_id, trigger, payload):
    receipts = payload.get('expense_receipts') or {}
    text = '\n'.join([str(v) for v in receipts.values()]) if isinstance(receipts, dict) else str(receipts)
    return _analysis_handler(dispatcher, trigger['id'], payload, text, 'summary', 'Receipts reviewed')


def handle_evidence_support(dispatcher, section_id, trigger, payload):
    text = _timeline_text(payload)
    return _analysis_handler(dispatcher, trigger['id'], payload, text, 'investigation', 'Evidence support audit complete')


def handle_tone_compliance(dispatcher, section_id, trigger, payload):
    findings = payload.get('key_findings') or []
    text = '\n'.join([str(f) for f in findings])
    return _analysis_handler(dispatcher, trigger['id'], payload, text, 'summary', 'Tone validated')


def handle_content_verification(dispatcher, section_id, trigger, payload):
    manifest = payload.get('evidence_manifest') or {}
    text = '\n'.join([str(v) for v in manifest.values()])
    return _analysis_handler(dispatcher, trigger['id'], payload, text, 'investigation', 'Evidence content verified')


def handle_chain_integrity(dispatcher, section_id, trigger, payload):
    custody = payload.get('chain_of_custody') or {}
    text = '\n'.join([str(v) for v in custody.values()]) if isinstance(custody, dict) else str(custody)
    return _analysis_handler(dispatcher, trigger['id'], payload, text, 'summary', 'Custody chain reviewed')


def handle_template_integrity(dispatcher, section_id, trigger, payload):
    text = '\n'.join([str(v) for v in (payload.get('disclaimer_templates') or {}).values()])
    return _analysis_handler(dispatcher, trigger['id'], payload, text, 'summary', 'Template integrity checked')


def handle_consistency_check(dispatcher, section_id, trigger, payload):
    limitations = payload.get('limitations')
    text = str(limitations)
    return _analysis_handler(dispatcher, trigger['id'], payload, text, 'summary', 'Consistency checked')


def handle_clause_verification(dispatcher, section_id, trigger, payload):
    disclosures = payload.get('disclosures')
    text = str(disclosures)
    return _analysis_handler(dispatcher, trigger['id'], payload, text, 'summary', 'Disclosure clauses verified')


def handle_narrative_consistency(dispatcher, section_id, trigger, payload):
    approved_sections = payload.get('approved_sections') or {}
    text = '\n'.join([str(v) for v in approved_sections.values()])
    return _analysis_handler(dispatcher, trigger['id'], payload, text, 'summary', 'Narrative consistency sweep complete')


def handle_redaction_check(dispatcher, section_id, trigger, payload):
    attachments = payload.get('attachments') or []
    text = '\n'.join([str(a) for a in attachments])
    return _analysis_handler(dispatcher, trigger['id'], payload, text, 'summary', 'Redaction check complete')


def _default_handler(dispatcher, section_id, trigger, payload):
    return _make_result(trigger.get('id', 'unknown_trigger'), 'skipped', 'No handler implemented')


TRIGGER_HANDLERS: Dict[str, Callable[[OpenAITriggerDispatcher, str, Dict[str, Any], Dict[str, Any]], Dict[str, Any]]] = {
    'contract_verification': handle_contract_verification,
    'name_normalization': handle_name_normalization,
    'title_quality': handle_title_quality,
    'coverage_gap': handle_coverage_gap,
    'goal_clarification': handle_goal_clarification,
    'compliance_scan': handle_compliance_scan,
    'plan_consistency': handle_plan_consistency,
    'legal_compliance': handle_legal_compliance,
    'narrative_alignment': handle_narrative_alignment,
    'gap_detection': handle_gap_detection,
    'session_summary': handle_session_summary,
    'condition_validation': handle_condition_validation,
    'doc_classification': handle_doc_classification,
    'risk_highlight': handle_risk_highlight,
    'narrative_reconciliation': handle_narrative_reconciliation,
    'receipt_verification': handle_receipt_verification,
    'evidence_support_audit': handle_evidence_support,
    'tone_compliance': handle_tone_compliance,
    'content_verification': handle_content_verification,
    'chain_integrity': handle_chain_integrity,
    'template_integrity': handle_template_integrity,
    'consistency_check': handle_consistency_check,
    'clause_verification': handle_clause_verification,
    'narrative_consistency_sweep': handle_narrative_consistency,
    'redaction_check': handle_redaction_check,
}