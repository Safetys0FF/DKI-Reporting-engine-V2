"""Central manifest describing each section's structured rebuild metadata.

This module provides a single source of truth for:
- Documentation references (READMEs, parsing maps, logic scripts, SOPs)
- Renderer modules/classes
- Toolkit dependencies and data contracts
- Execution / export ordering (kept in sync with framework classes)
- Guardrail enforcement (style lint, persistence, fact graph, immutability, rerun caps)
- Suggested test coverage for the rebuild work

It is intentionally read-only; orchestration code imports this manifest to configure
section frameworks without touching production wiring.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Tuple


@dataclass(frozen=True)
class DocumentationRefs:
    readme: str
    parsing_map: str
    sop: str
    logic_notes: Tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class RendererRef:
    module: str
    class_name: str


@dataclass(frozen=True)
class ToolkitRefs:
    modules: Tuple[str, ...]
    notes: Tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class GuardrailRefs:
    style_lint: bool = False
    persistence: bool = False
    fact_graph: bool = False
    immutability: bool = False
    rerun_caps: bool = False


@dataclass(frozen=True)
class TestCoverage:
    unit: Tuple[str, ...]
    integration: Tuple[str, ...]


@dataclass(frozen=True)
class SectionMeta:
    section_id: str
    documentation: DocumentationRefs
    renderer: RendererRef
    toolkit: ToolkitRefs
    guardrails: GuardrailRefs
    tests: TestCoverage
    notes: Tuple[str, ...] = field(default_factory=tuple)


REPORT_ENGINE_ROOT = Path(__file__).resolve().parents[2]


def _resolve(relative_path: str) -> Path:
    """Resolve a manifest path relative to the Report Engine root."""
    path = (REPORT_ENGINE_ROOT / relative_path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"Resource '{relative_path}' could not be found at {path}.")
    return path


def _read(relative_path: str) -> str:
    """Read text content for a manifest resource with utf-8 fallback."""
    resource_path = _resolve(relative_path)
    return resource_path.read_text(encoding='utf-8', errors='ignore')


def ingest_section_documentation(section_id: str) -> Dict[str, object]:
    """Load the registered documentation artifacts for a section."""
    if section_id not in SECTION_MANIFEST:
        raise KeyError(f"Unknown section_id '{section_id}'")
    meta = SECTION_MANIFEST[section_id]
    documentation = {
        'readme': _read(meta.documentation.readme),
        'parsing_map': _read(meta.documentation.parsing_map),
        'sop': _read(meta.documentation.sop),
        'logic_notes': {path: _read(path) for path in meta.documentation.logic_notes},
    }
    return documentation


def resolve_resource_path(relative_path: str) -> Path:
    """Expose path resolution for callers that need filesystem access."""
    return _resolve(relative_path)

gateway_meta = SectionMeta(
    section_id='gateway',
    documentation=DocumentationRefs(
        readme='Sections/section_readme/Section_1_README.md',
        parsing_map='Gateway/parsing maps/SECTION_1_PARSING_MAP.md',
        sop='dev_tracking/templates/playbook rules/Section_1_Rebuild_Playbook.md',
        logic_notes=(
            'Sections/section_engines/3. Section 1=gateway controller.txt',
            'dev_tracking/templates/Scaffolding plans/Section_1_Gateway_Scaffolding.md',
        ),
    ),
    renderer=RendererRef(
        module='Sections.section_renderers.section_1_gateway',
        class_name='Section1Renderer',
    ),
    toolkit=ToolkitRefs(
        modules=(
            'MasterToolKitEngine',
            'metadata_tool_v_5.py',
            'cochran_match_tool.py',
            'northstar_protocol_tool.py',
        ),
        notes=(),
    ),
    guardrails=GuardrailRefs(
        style_lint=True,
        persistence=True,
        fact_graph=True,
        immutability=True,
        rerun_caps=True,
    ),
    tests=TestCoverage(
        unit=(
            'tests/test_gateway_ingest.py',
            'tests/test_gateway_factgraph.py',
        ),
        integration=(
            'tests/test_full_pipeline.py',
        ),
    ),
    notes=(
            'Async queue routing handled via SectionFramework.ORDER + CommunicationContract',
            "Evidence index persisted at 'storage/sections/section_1.json'",
        ),
)
section_cp_meta = SectionMeta(
    section_id='section_cp',
    documentation=DocumentationRefs(
        readme='Sections/section_readme/Section_CP_README.md',
        parsing_map='Gateway/parsing maps/SECTION_CP_PARSING_MAP.md',
        sop='dev_tracking/templates/playbook rules/Section_CP_Rebuild_Playbook.md',
        logic_notes=(
            'Sections/section_engines/1. Section CP.txt',
            'dev_tracking/templates/Scaffolding plans/Section_CP_Scaffolding.md',
        ),
    ),
    renderer=RendererRef(
        module='Sections.section_renderers.section_cp_renderer',
        class_name='SectionCPRenderer',
    ),
    toolkit=ToolkitRefs(
        modules=(
            'UserProfileManager',
            'metadata_tool_v_5.py',
        ),
        notes=(),
    ),
    guardrails=GuardrailRefs(
        style_lint=True,
        persistence=True,
        fact_graph=True,
        immutability=True,
        rerun_caps=True,
    ),
    tests=TestCoverage(
        unit=(
            'tests/sections/test_section_cp_renderer.py',
        ),
        integration=(
            'tests/sections/test_section_cp_workflow.py',
        ),
    ),
    notes=(
            'Cover profile manifest reused by Sections DP/9',
        ),
)
section_toc_meta = SectionMeta(
    section_id='section_toc',
    documentation=DocumentationRefs(
        readme='Sections/section_readme/Section_TOC_README.md',
        parsing_map='Gateway/parsing maps/SECTION_TOC_PARSING_MAP.md',
        sop='app/CP, TOC, Sec 1.txt',
        logic_notes=(
            'Sections/section_engines/2. Section TOC.txt',
            'dev_tracking/templates/Scaffolding plans/Section_1_Scaffolding.md',
        ),
    ),
    renderer=RendererRef(
        module='Sections.section_renderers.section_cp_renderer',
        class_name='SectionCPRenderer',
    ),
    toolkit=ToolkitRefs(
        modules=(),
        notes=(
            'TOC generation uses report generator manifest snapshots',
        ),
    ),
    guardrails=GuardrailRefs(
        style_lint=True,
        persistence=True,
        fact_graph=False,
        immutability=True,
        rerun_caps=True,
    ),
    tests=TestCoverage(
        unit=(
            'tests/sections/test_section_toc.py',
        ),
        integration=(
            'tests/test_final_assembly_toc.py',
        ),
    ),
    notes=(
            'Renderer placeholder until dedicated Section TOC renderer is restored.',
        ),
)
section_2_meta = SectionMeta(
    section_id='section_2',
    documentation=DocumentationRefs(
        readme='Sections/section_readme/Section_2_README.md',
        parsing_map='Gateway/parsing maps/SECTION_2_PARSING_MAP.md',
        sop='dev_tracking/templates/playbook rules/Section_2_Rebuild_Playbook.md',
        logic_notes=(
            'Sections/section_engines/4. Section 2.txt',
            'dev_tracking/templates/Scaffolding plans/Section_2_Scaffolding.md',
            'Logic files/canvas logic for report/Section 2 - Presurveillance Logic.txt',
        ),
    ),
    renderer=RendererRef(
        module='Sections.section_renderers.section_2_renderer',
        class_name='Section2Renderer',
    ),
    toolkit=ToolkitRefs(
        modules=(),
        notes=(),
    ),
    guardrails=GuardrailRefs(
        style_lint=True,
        persistence=True,
        fact_graph=True,
        immutability=True,
        rerun_caps=True,
    ),
    tests=TestCoverage(
        unit=(),
        integration=(),
    ),
    notes=(
            'Pre-surveillance planning consumes gateway approvals and toolkit cache.',
        ),
)
section_3_meta = SectionMeta(
    section_id='section_3',
    documentation=DocumentationRefs(
        readme='Sections/section_readme/Section_3_README.md',
        parsing_map='Gateway/parsing maps/SECTION_3_PARSING_MAP.md',
        sop='dev_tracking/templates/playbook rules/Section_3_Rebuild_Playbook.md',
        logic_notes=(
            'Sections/section_engines/5. Section 3.txt',
            'dev_tracking/templates/Scaffolding plans/Section_3_Scaffolding.md',
            'Logic files/canvas logic for report/Section 3 - Surveillance Reports - Dialy Logs.txt',
        ),
    ),
    renderer=RendererRef(
        module='Sections.section_renderers.section_3_renderer',
        class_name='Section3Renderer',
    ),
    toolkit=ToolkitRefs(
        modules=(),
        notes=(),
    ),
    guardrails=GuardrailRefs(
        style_lint=True,
        persistence=True,
        fact_graph=True,
        immutability=True,
        rerun_caps=True,
    ),
    tests=TestCoverage(
        unit=(),
        integration=(),
    ),
    notes=(
            'Surveillance narratives rely on gateway media orchestration.',
        ),
)
section_4_meta = SectionMeta(
    section_id='section_4',
    documentation=DocumentationRefs(
        readme='Sections/section_readme/Section_4_README.md',
        parsing_map='Gateway/parsing maps/SECTION_4_PARSING_MAP.md',
        sop='dev_tracking/templates/playbook rules/Section_4_Rebuild_Playbook.md',
        logic_notes=(
            'Sections/section_engines/6. Section 4.txt',
            'dev_tracking/templates/Scaffolding plans/Section_4_Scaffolding.md',
            'Logic files/canvas logic for report/Section 4 - Review of Surveillance Sessions.txt',
        ),
    ),
    renderer=RendererRef(
        module='Sections.section_renderers.section_4_renderer',
        class_name='Section4Renderer',
    ),
    toolkit=ToolkitRefs(
        modules=(),
        notes=(),
    ),
    guardrails=GuardrailRefs(
        style_lint=True,
        persistence=True,
        fact_graph=True,
        immutability=True,
        rerun_caps=True,
    ),
    tests=TestCoverage(
        unit=(),
        integration=(),
    ),
    notes=(
            'Session review feeds downstream billing and conclusions.',
        ),
)
section_5_meta = SectionMeta(
    section_id='section_5',
    documentation=DocumentationRefs(
        readme='Sections/section_readme/Section_5_README.md',
        parsing_map='Gateway/parsing maps/SECTION_5_PARSING_MAP.md',
        sop='dev_tracking/templates/playbook rules/Section_5_Rebuild_Playbook.md',
        logic_notes=(
            'Sections/section_engines/7. Section 5.txt',
            'dev_tracking/templates/Scaffolding plans/Section_5_Scaffolding.md',
            'Logic files/canvas logic for report/Section 5 - review of documents Logic Overview.txt',
        ),
    ),
    renderer=RendererRef(
        module='Sections.section_renderers.section_5_renderer',
        class_name='Section5Renderer',
    ),
    toolkit=ToolkitRefs(
        modules=(),
        notes=(),
    ),
    guardrails=GuardrailRefs(
        style_lint=True,
        persistence=True,
        fact_graph=True,
        immutability=True,
        rerun_caps=True,
    ),
    tests=TestCoverage(
        unit=(),
        integration=(),
    ),
    notes=(
            'Document inventory feeds conclusions and billing cross-checks.',
        ),
)
section_6_meta = SectionMeta(
    section_id='section_6',
    documentation=DocumentationRefs(
        readme='Sections/section_readme/Section_6_README.md',
        parsing_map='Gateway/parsing maps/SECTION_6_PARSING_MAP.md',
        sop='dev_tracking/templates/playbook rules/Section_6_Rebuild_Playbook.md',
        logic_notes=(
            'Sections/section_engines/8. Section 6 - Billing Summary.txt',
            'dev_tracking/templates/Scaffolding plans/Section_6_Scaffolding.md',
            'Logic files/canvas logic for report/section 6 - BILLING SUMMARY.txt',
        ),
    ),
    renderer=RendererRef(
        module='Sections.section_renderers.section_6_renderer',
        class_name='Section6BillingRenderer',
    ),
    toolkit=ToolkitRefs(
        modules=(),
        notes=(),
    ),
    guardrails=GuardrailRefs(
        style_lint=True,
        persistence=True,
        fact_graph=True,
        immutability=True,
        rerun_caps=True,
    ),
    tests=TestCoverage(
        unit=(),
        integration=(),
    ),
    notes=(
            'Billing pulls mileage, expenses, and contract enforcement inputs.',
        ),
)
section_7_meta = SectionMeta(
    section_id='section_7',
    documentation=DocumentationRefs(
        readme='Sections/section_readme/Section_7_README.md',
        parsing_map='Gateway/parsing maps/SECTION_7_PARSING_MAP.md',
        sop='dev_tracking/templates/playbook rules/Section_7_Rebuild_Playbook.md',
        logic_notes=(
            'Sections/section_engines/9. Section 7.txt',
            'dev_tracking/templates/Scaffolding plans/Section_7_Scaffolding.md',
            'Legal/Sections 7, 8, and 9 Final Report.txt',
        ),
    ),
    renderer=RendererRef(
        module='Sections.section_renderers.section_7_renderer',
        class_name='Section7Renderer',
    ),
    toolkit=ToolkitRefs(
        modules=(),
        notes=(),
    ),
    guardrails=GuardrailRefs(
        style_lint=True,
        persistence=True,
        fact_graph=True,
        immutability=True,
        rerun_caps=True,
    ),
    tests=TestCoverage(
        unit=(),
        integration=(),
    ),
    notes=(
            'Conclusion synthesis aligns findings across sections 3-6.',
        ),
)
section_8_meta = SectionMeta(
    section_id='section_8',
    documentation=DocumentationRefs(
        readme='Sections/section_readme/Section_8_README.md',
        parsing_map='Gateway/parsing maps/SECTION_8_PARSING_MAP.md',
        sop='dev_tracking/templates/playbook rules/Section_8_Rebuild_Playbook.md',
        logic_notes=(
            'Sections/section_engines/10. Section 8.txt',
            'dev_tracking/templates/Scaffolding plans/Section_8_Scaffolding.md',
            'Legal/Sections 7, 8, and 9 Final Report.txt',
        ),
    ),
    renderer=RendererRef(
        module='Sections.section_renderers.section_8_renderer',
        class_name='Section8Renderer',
    ),
    toolkit=ToolkitRefs(
        modules=(),
        notes=(),
    ),
    guardrails=GuardrailRefs(
        style_lint=True,
        persistence=True,
        fact_graph=True,
        immutability=True,
        rerun_caps=True,
    ),
    tests=TestCoverage(
        unit=(),
        integration=(),
    ),
    notes=(
            'Photo/evidence index aligns media against the surveillance timeline.',
        ),
)
section_9_meta = SectionMeta(
    section_id='section_9',
    documentation=DocumentationRefs(
        readme='Sections/section_readme/Section_9_README.md',
        parsing_map='Gateway/parsing maps/SECTION_9_PARSING_MAP.md',
        sop='dev_tracking/templates/playbook rules/Section_9_Rebuild_Playbook.md',
        logic_notes=(
            'dev_tracking/templates/Scaffolding plans/Section_9_Scaffolding.md',
            'Sections/section_renderers/section_9_renderer.py',
            'Legal/Sections 7, 8, and 9 Final Report.txt',
        ),
    ),
    renderer=RendererRef(
        module='Sections.section_renderers.section_9_renderer',
        class_name='Section9Renderer',
    ),
    toolkit=ToolkitRefs(
        modules=(),
        notes=(),
    ),
    guardrails=GuardrailRefs(
        style_lint=True,
        persistence=True,
        fact_graph=True,
        immutability=True,
        rerun_caps=True,
    ),
    tests=TestCoverage(
        unit=(),
        integration=(),
    ),
    notes=(
            'Certification draws on cover, conclusion, and billing approvals.',
        ),
)
section_dp_meta = SectionMeta(
    section_id='section_dp',
    documentation=DocumentationRefs(
        readme='Sections/section_readme/Section_DP_README.md',
        parsing_map='Gateway/parsing maps/SECTION_DP_PARSING_MAP.md',
        sop='dev_tracking/templates/playbook rules/Section_DP_Rebuild_Playbook.md',
        logic_notes=(
            'Sections/section_engines/11. Section DP.txt',
            'dev_tracking/templates/Scaffolding plans/Section_DP_Scaffolding.md',
        ),
    ),
    renderer=RendererRef(
        module='Sections.section_renderers.section_dp_renderer',
        class_name='SectionDPRenderer',
    ),
    toolkit=ToolkitRefs(
        modules=(),
        notes=(),
    ),
    guardrails=GuardrailRefs(
        style_lint=True,
        persistence=True,
        fact_graph=True,
        immutability=True,
        rerun_caps=True,
    ),
    tests=TestCoverage(
        unit=(),
        integration=(),
    ),
    notes=(
            'Disclosure page locks signatures and compliance statements.',
        ),
)
section_fr_meta = SectionMeta(
    section_id='section_fr',
    documentation=DocumentationRefs(
        readme='Sections/section_readme/Section_FR_README.md',
        parsing_map='Gateway/parsing maps/SECTION_FR_PARSING_MAP.md',
        sop='dev_tracking/templates/playbook rules/Section_FR_Rebuild_Playbook.md',
        logic_notes=(
            'Sections/section_engines/12. Final Assembly.txt',
            'dev_tracking/templates/Scaffolding plans/Section_FR_Scaffolding.md',
        ),
    ),
    renderer=RendererRef(
        module='Sections.section_renderers.section_fr_renderer',
        class_name='SectionFRRenderer',
    ),
    toolkit=ToolkitRefs(
        modules=(),
        notes=(),
    ),
    guardrails=GuardrailRefs(
        style_lint=True,
        persistence=True,
        fact_graph=True,
        immutability=True,
        rerun_caps=True,
    ),
    tests=TestCoverage(
        unit=(),
        integration=(),
    ),
    notes=(
            'Final assembly consumes all section payloads and export config.',
        ),
)
SECTION_MANIFEST: Dict[str, SectionMeta] = {
    'gateway': gateway_meta,
    'section_cp': section_cp_meta,
    'section_toc': section_toc_meta,
    'section_2': section_2_meta,
    'section_3': section_3_meta,
    'section_4': section_4_meta,
    'section_5': section_5_meta,
    'section_6': section_6_meta,
    'section_7': section_7_meta,
    'section_8': section_8_meta,
    'section_9': section_9_meta,
    'section_dp': section_dp_meta,
    'section_fr': section_fr_meta,
    'section_1': gateway_meta,
}


__all__ = [
    'SECTION_MANIFEST',
    'SectionMeta',
    'ingest_section_documentation',
    'resolve_resource_path',
]
