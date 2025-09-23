POWER Agent Role (Updated)
- Own the tunnel blueprint end to end and keep intake->routing->OCR->enrichment->validation->report flow aligned with section READMEs.
- Wire the evidence cache, document intake points, and UI pipeline to the new routing queue.
- Implement core DocumentProcessor updates, guardrails, error handling, and fallback procedures (media routing, merge safeguards, section hand-offs).
- Build and maintain the regression harness that drives mixed-media batches, flagging anomalies or rollback needs.
- Manage change logs and implementation plan; hand off coordination tasks to supporting agents when needed.

Networking Agent Role (Revised)
- Establish and monitor external service integrations (OpenAI/ChatGPT, Google, internal APIs) with credential and rate-limit management.
- Surface enrichment/API status and lineage back into the UI, keeping stakeholders informed.

DEESCALATION Agent Role (Revised)
- Validate routing paths and section outputs provided by POWER; confirm OCR engines and enrichment calls execute as configured.
- Review guardrail results and sign off on section validations (totals, TOC links) before report synthesis proceeds.
- Provide operational oversight, raising issues when regression harnesses or runtime checks surface inconsistencies.

