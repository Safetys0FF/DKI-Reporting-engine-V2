#!/usr/bin/env python3
"""
Section 6 Renderer - Billing Summary
Generates a structured billing summary compatible with GatewayController.
"""

import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class Section6BillingRenderer:
    """Renders Section 6 - Billing Summary with contract-based logic"""

    def __init__(self):
        self.section_id = "section_6"
        # ASCII-only to avoid encoding issues across logs/exports
        self.section_title = "SECTION 6 - BILLING SUMMARY"
        self.hourly_rate = 100.00
        self.planning_budget = 500.00
        self.documentation_fee = 100.00
        logger.info("Section 6 Billing Renderer initialized")

    def render_data_model(self, processed_data: Dict[str, Any], report_type: str) -> Dict[str, Any]:
        """Generate billing data model based on processed data and report type"""

        logger.info(f"Generating billing data model for {report_type}")

        # Extract contract and billing information
        contract_total = float(processed_data.get('contract_total', 3000.00))
        prep_cost = float(processed_data.get('prep_cost', 500.00))
        subcontractor_cost = float(processed_data.get('subcontractor_cost', 1275.00))

        # Calculate remaining operations budget
        remaining_ops = contract_total - prep_cost - subcontractor_cost

        # Generate billing sections based on report type
        billing_sections = self._generate_billing_sections(
            report_type, contract_total, prep_cost, subcontractor_cost, remaining_ops
        )

        # Calculate totals and margins
        total_costs = prep_cost + subcontractor_cost
        internal_margin = remaining_ops - total_costs if remaining_ops > total_costs else 0.0

        billing_data = {
            'contract_total': contract_total,
            'prep_cost': prep_cost,
            'subcontractor_cost': subcontractor_cost,
            'remaining_ops_budget': remaining_ops,
            'total_costs': total_costs,
            'internal_margin': internal_margin,
            'billing_sections': billing_sections,
            'report_type': report_type,
            'generated_at': datetime.now().isoformat(),
            'notes': self._generate_billing_notes(report_type, remaining_ops, total_costs),
        }

        logger.info(
            f"Billing data model generated: contract=${contract_total:,.2f} margin=${internal_margin:,.2f}"
        )
        return billing_data

    def _generate_billing_sections(
        self,
        report_type: str,
        contract_total: float,
        prep_cost: float,
        subcontractor_cost: float,
        remaining_ops: float,
    ) -> List[Dict[str, Any]]:
        """Generate billing breakdown sections based on report type"""

        if report_type == "Investigative":
            return [
                {
                    'category': 'Investigation Planning',
                    'description': 'Case analysis, strategy development, resource allocation',
                    'amount': prep_cost,
                    'type': 'fixed',
                },
                {
                    'category': 'Field Investigation',
                    'description': 'On-site investigation, surveillance, interviews',
                    'amount': subcontractor_cost * 0.7,
                    'type': 'variable',
                },
                {
                    'category': 'Research & Analysis',
                    'description': 'Background checks, public records, data analysis',
                    'amount': subcontractor_cost * 0.3,
                    'type': 'variable',
                },
                {
                    'category': 'Documentation & Reporting',
                    'description': 'Report compilation, evidence organization, final documentation',
                    'amount': self.documentation_fee,
                    'type': 'fixed',
                },
            ]

        if report_type in {"Field", "Surveillance"}:
            return [
                {
                    'category': 'Field Operations',
                    'description': 'On-site surveillance, evidence collection, photography',
                    'amount': subcontractor_cost * 0.8,
                    'type': 'variable',
                },
                {
                    'category': 'Travel & Logistics',
                    'description': 'Transportation, equipment, operational support',
                    'amount': subcontractor_cost * 0.2,
                    'type': 'variable',
                },
                {
                    'category': 'Planning & Coordination',
                    'description': 'Operation planning, team coordination, briefings',
                    'amount': prep_cost,
                    'type': 'fixed',
                },
            ]

        # Hybrid by default
        return [
            {
                'category': 'Investigation Planning',
                'description': 'Combined planning across investigative and field operations',
                'amount': prep_cost * 0.6,
                'type': 'fixed',
            },
            {
                'category': 'Field Operations',
                'description': 'Surveillance, interviews, evidence collection',
                'amount': subcontractor_cost * 0.6,
                'type': 'variable',
            },
            {
                'category': 'Research & Analysis',
                'description': 'Background investigation, data analysis, verification',
                'amount': subcontractor_cost * 0.4,
                'type': 'variable',
            },
            {
                'category': 'Administrative',
                'description': 'Documentation, reporting, client coordination',
                'amount': prep_cost * 0.4,
                'type': 'fixed',
            },
        ]

    def _generate_billing_notes(self, report_type: str, remaining_ops: float, total_costs: float) -> List[str]:
        """Generate billing notes and observations"""

        notes: List[str] = []

        if remaining_ops > total_costs:
            notes.append("No overage. Standard $500 applied clean.")
        elif remaining_ops == total_costs:
            notes.append("Budget utilized at 100% efficiency.")
        else:
            overage = total_costs - remaining_ops
            notes.append(f"Overage of ${overage:.2f} requires client approval.")

        if report_type == "Investigative":
            notes.append("Investigation-focused billing structure applied.")
        elif report_type in {"Field", "Surveillance"}:
            notes.append("Field operations billing structure applied.")
        else:
            notes.append("Hybrid investigation/field billing structure applied.")

        return notes

    # Gateway-compatible rendering API
    def render_model(self, section_payload: Dict[str, Any], case_sources: Dict[str, Any] = None) -> Dict[str, Any]:
        """Return a structured render model for Gateway/ReportGenerator."""

        payload = section_payload or {}
        report_meta = payload.get('report_meta', {})
        report_type = (
            report_meta.get('report_type')
            or (case_sources or {}).get('report_type')
            or 'Investigative'
        )

        billing_hint = payload.get('billing_data') or {}
        processed = {
            'contract_total': payload.get('contract_total') or billing_hint.get('contract_total') or 3000.00,
            'prep_cost': payload.get('prep_cost') or billing_hint.get('prep_cost') or 500.00,
            'subcontractor_cost': payload.get('subcontractor_cost') or billing_hint.get('subcontractor_cost') or 1275.00,
        }

        model = self.render_data_model(processed, report_type)

        blocks: List[Dict[str, Any]] = []
        blocks.append({
            'type': 'title',
            'text': self.section_title,
            'style': {"font": "Times New Roman", "size_pt": 16, "bold": True,
                      "all_caps": True, "align": "center", "spacing": 1.15},
        })

        # Contract overview
        blocks.append({'type': 'header', 'text': 'CONTRACT OVERVIEW'})
        blocks.append({'type': 'field', 'label': 'Total Contract Value', 'value': f"${model['contract_total']:,.2f}"})
        blocks.append({'type': 'field', 'label': 'Report Type', 'value': model['report_type']})

        # Billing breakdown
        blocks.append({'type': 'header', 'text': 'BILLING BREAKDOWN'})
        for sec in model.get('billing_sections', []) or []:
            blocks.append({'type': 'field', 'label': sec.get('category', 'Item'), 'value': f"${sec.get('amount', 0):,.2f}"})
            if sec.get('description'):
                blocks.append({'type': 'paragraph', 'text': sec['description']})

        # Financial summary
        blocks.append({'type': 'header', 'text': 'FINANCIAL SUMMARY'})
        blocks.append({'type': 'field', 'label': 'Preparation Costs', 'value': f"${model['prep_cost']:,.2f}"})
        blocks.append({'type': 'field', 'label': 'Subcontractor Costs', 'value': f"${model['subcontractor_cost']:,.2f}"})
        blocks.append({'type': 'field', 'label': 'Total Direct Costs', 'value': f"${model['total_costs']:,.2f}"})
        blocks.append({'type': 'field', 'label': 'Remaining Operations Budget', 'value': f"${model['remaining_ops_budget']:,.2f}"})
        blocks.append({'type': 'field', 'label': 'Internal Margin', 'value': f"${model['internal_margin']:,.2f}"})

        # Notes
        notes = model.get('notes') or []
        if notes:
            blocks.append({'type': 'header', 'text': 'BILLING NOTES'})
            for n in notes:
                blocks.append({'type': 'paragraph', 'text': f"- {n}"})

        manifest = {
            'section_key': self.section_id,
            'title': self.section_title,
            'fields_rendered': [
                'contract_total', 'prep_cost', 'subcontractor_cost',
                'remaining_ops_budget', 'internal_margin'
            ],
            'generated_at': model.get('generated_at'),
        }

        return {
            'render_tree': blocks,
            'manifest': manifest,
            'billing_model': model,
            'handoff': 'gateway',
        }

    def render_docx_section(self, billing_data: Dict[str, Any]) -> str:
        """Render Section 6 as formatted text for DOCX insertion (text-only)."""

        logger.info("Rendering Section 6 billing summary for DOCX")

        content: List[str] = []
        content.append(self.section_title)
        content.append("=" * len(self.section_title))
        content.append("")

        # Contract Overview
        content.append("CONTRACT OVERVIEW")
        content.append("-" * 17)
        content.append(f"Total Contract Value: ${billing_data['contract_total']:,.2f}")
        content.append(f"Report Type: {billing_data['report_type']}")
        content.append("")

        # Billing Breakdown
        content.append("BILLING BREAKDOWN")
        content.append("-" * 16)

        for section in billing_data.get('billing_sections', []) or []:
            content.append(f"{section['category']}: ${section['amount']:,.2f}")
            if section.get('description'):
                content.append(f"  {section['description']}")
            content.append("")

        # Financial Summary
        content.append("FINANCIAL SUMMARY")
        content.append("-" * 16)
        content.append(f"Preparation Costs: ${billing_data['prep_cost']:,.2f}")
        content.append(f"Subcontractor Costs: ${billing_data['subcontractor_cost']:,.2f}")
        content.append(f"Total Direct Costs: ${billing_data['total_costs']:,.2f}")
        content.append(f"Remaining Operations Budget: ${billing_data['remaining_ops_budget']:,.2f}")
        content.append(f"Internal Margin: ${billing_data['internal_margin']:,.2f}")
        content.append("")

        # Notes
        if billing_data.get('notes'):
            content.append("BILLING NOTES")
            content.append("-" * 12)
            for note in billing_data['notes']:
                content.append(f"- {note}")
            content.append("")

        # Footer
        content.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        return "\n".join(content)


# Test the renderer
if __name__ == "__main__":
    test_data = {
        'contract_total': 3000.00,
        'prep_cost': 500.00,
        'subcontractor_cost': 1275.00,
    }
    renderer = Section6BillingRenderer()
    for report_type in ["Investigative", "Field", "Surveillance", "Hybrid"]:
        print(f"\n=== Testing {report_type} Report ===")
        billing_data = renderer.render_data_model(test_data, report_type)
        print(f"Contract Total: ${billing_data['contract_total']:.2f}")
        print(f"Prep Cost: ${billing_data['prep_cost']:.2f}")
        print(f"Subcontractor Cost: ${billing_data['subcontractor_cost']:.2f}")
        print(f"Remaining Ops Budget: ${billing_data['remaining_ops_budget']:.2f}")
        print(f"Internal Margin: ${billing_data['internal_margin']:.2f}")
        print(f"Notes: {billing_data['notes']}")






