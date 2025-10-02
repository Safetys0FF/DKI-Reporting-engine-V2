# Analyst Deck System Summary

## Overview
The Analyst Deck provides investigation analytics, test plans, and validation tooling for the Central Command ecosystem. With the latest bus-enabled updates, the deck consumes live manifest data, section enrichment signals, and mission status broadcasts to drive automated validation and insight generation.

## Core Responsibilities
- Run integration and smoke tests across Evidence Locker, Gateway, Mission Debrief, and UI workflows.
- Analyse manifest coverage, section completion timelines, and enrichment depth using bus snapshots.
- Host scenario scripts that replay `section.needs`, `evidence.request`, and enrichment events for QA.
- Surface dashboards and reports that help operators gauge readiness before final assembly.

## Architectural Highlights
- **Bus-Aware Test Harness:** Uses the shared `DKIReportBus` interfaces to poll manifests, status payloads, and case snapshots.
- **Scenario Runner:** Automates evidence ingestion and section broker flows, verifying enrichment confirms before completion signals fire.
- **Telemetry Capture:** Ingests `mission.status`, `mission_debrief.section.*`, and Gateway status outputs for historical analytics.
- **Report Artifacts:** Generates summaries for QA cycles, feeding Mission Debrief and UI teams with actionable metrics.

## Recent Enhancements
- Updated scripts to consume `get_bus_snapshots()` so manifest and status data feed directly into Analyst Deck dashboards.
- Added validations ensuring Gateway now emits `section.data.updated` prior to completion, and locker manifest entries reflect enrichment history.
- Mission Debrief test plans now assert receipt of section completion events and monitor section update counts.
- Enhanced evidence flow simulations align with the new UI `section.needs` hints and locker request prioritisation.

## Operational Status
- **Completed:** Bus snapshot integration, enrichment validation scenarios, mission status ingestion.
- **In Progress:** Automated anomaly detection across case snapshots and manifest gaps.
- **Next:** Predictive analytics for section duration, AI-assisted QA recommendations, cross-case trend reporting.

*Last updated: 2025-09-30*
