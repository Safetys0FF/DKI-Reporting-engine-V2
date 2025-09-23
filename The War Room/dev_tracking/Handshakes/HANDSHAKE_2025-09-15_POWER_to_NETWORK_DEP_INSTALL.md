# HANDSHAKE — 2025-09-15 — POWER → NETWORK (Dependency Install Request)

From Agent: POWER
To Agent: NETWORK
Context: Smoke validation blocked by missing runtime dependencies.

Request
- Install required packages per requirements.txt:
  - python-docx (`docx`)
  - openpyxl (`openpyxl`)
  - opencv-python (`cv2`)
  - reportlab (`reportlab`)
- Optional (FYI): pytesseract, openai, spacy, transformers, beautifulsoup4.

After install
- POWER will rerun smoke (CP/TOC + Section 1) to confirm clean startup and 10-6/10-8 signaling.

Reference
- dev_tracking/SMOKE_VALIDATION_2025-09-15.md

Status: SENT — Awaiting ACK

