"""AI Orchestrator - coordinates OpenAI-powered enrichment for evidence objects."""

from __future__ import annotations

import base64
import hashlib
import json
import logging
import mimetypes
import os
from pathlib import Path
from typing import Any, Dict, Optional

import requests

logger = logging.getLogger(__name__)

try:  # Prefer the modern OpenAI SDK
    from openai import OpenAI  # type: ignore
    HAVE_OPENAI_SDK = True
except Exception:  # pragma: no cover - fall back to legacy layout
    HAVE_OPENAI_SDK = False
    try:
        import openai  # type: ignore
        HAVE_OPENAI_LEGACY = True
    except Exception:  # pragma: no cover - only HTTP fallback available
        openai = None  # type: ignore
        HAVE_OPENAI_LEGACY = False


def _default_cache_dir() -> Path:
    env_override = os.getenv("DKI_AI_CACHE")
    if env_override:
        return Path(env_override)
    return Path.home() / ".dki_ai_cache"


class AIOrchestrator:
    """Centralised helper that enriches evidence files using OpenAI models.

    The orchestrator keeps a lightweight cache to avoid duplicate API calls and
    exposes a single ``enrich_evidence`` entry point that returns a structured
    payload containing document/image insights plus case-context suggestions.
    """

    document_model: str = "gpt-4o-mini"
    image_model: str = "gpt-4o-mini"

    def __init__(self, api_manager: Optional[Any] = None, cache_dir: Optional[Path] = None) -> None:
        self.api_manager = api_manager
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.cache_dir = Path(cache_dir) if cache_dir else _default_cache_dir()
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        except Exception:  # pragma: no cover - cache dir best-effort only
            logger.debug("AI cache directory %s could not be created", self.cache_dir)
        self.logger = logger.getChild("orchestrator")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def enrich_evidence(self, evidence_record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Analyse the supplied evidence record and return AI insights.

        The caller must provide ``file_path`` inside ``evidence_record``. On
        success a dictionary with ``analysis`` metadata and optional
        ``case_updates`` is returned. When enrichment is skipped (missing key,
        unsupported type, etc.) ``None`` is returned.
        """

        file_path = evidence_record.get("file_path")
        if not file_path:
            self.logger.debug("Evidence record missing file_path; skipping AI analysis")
            return None

        path = Path(file_path)
        if not path.exists():
            self.logger.warning("Evidence file %s no longer exists; skipping AI analysis", file_path)
            return None

        cache_key = self._build_cache_key(path)
        cached = self._read_cache(cache_key)
        if cached:
            self.logger.debug("Using cached AI analysis for %s", path.name)
            return cached

        extension = path.suffix.lower()
        try:
            if extension in {".txt", ".md", ".rtf", ".json", ".csv", ".log", ".pdf", ".doc", ".docx"}:
                analysis = self._analyse_document(path, evidence_record)
            elif extension in {".png", ".jpg", ".jpeg", ".bmp", ".gif"}:
                analysis = self._analyse_image(path, evidence_record)
            else:
                self.logger.debug("Unsupported file extension %s for AI enrichment", extension)
                analysis = {
                    "status": "skipped",
                    "reason": f"Unsupported evidence type {extension}"
                }
        except Exception as exc:  # pragma: no cover - defensive guard
            self.logger.exception("AI enrichment failed for %s: %s", path.name, exc)
            analysis = {
                "status": "error",
                "error": str(exc)
            }

        if not analysis:
            return None

        self._write_cache(cache_key, analysis)
        return analysis

    # ------------------------------------------------------------------
    # Document handling
    # ------------------------------------------------------------------
    def _analyse_document(self, file_path: Path, evidence_record: Dict[str, Any]) -> Dict[str, Any]:
        text = self._read_text(file_path)
        if not text:
            return {
                "status": "skipped",
                "reason": "Document text could not be extracted"
            }

        text = text[:12000]  # keep prompts bounded
        subject_hint = evidence_record.get("metadata", {}).get("subject")

        prompt = (
            "You are an investigative analyst. Analyse the supplied evidence text and "
            "respond as a compact JSON object with keys: document_type (string), "
            "summary (string), parties (list of names), locations (list of strings), "
            "dates (list of ISO strings), key_facts (list of bullet strings), risks (list), "
            "and subject_observations (list of objects with name, descriptors, confidence)."
        )
        if subject_hint:
            prompt += f" Primary subject of record: {subject_hint}. Flag mismatches clearly."
        prompt += "\nText:\n" + text

        response = self._call_openai_chat(prompt, model=self.document_model, max_tokens=900)
        if not response:
            return {"status": "skipped", "reason": "OpenAI unavailable"}

        case_updates = self._case_updates_from_document(response)
        return {
            "status": "ok",
            "provider": "openai_api",
            "document": response,
            "case_updates": case_updates
        }

    # ------------------------------------------------------------------
    # Image handling
    # ------------------------------------------------------------------
    def _analyse_image(self, file_path: Path, evidence_record: Dict[str, Any]) -> Dict[str, Any]:
        api_key = self._get_openai_key()
        if not api_key:
            return {"status": "skipped", "reason": "No OpenAI API key available"}

        mime = mimetypes.guess_type(str(file_path))[0] or "image/png"
        image_bytes = file_path.read_bytes()
        if len(image_bytes) > 4 * 1024 * 1024:
            return {"status": "skipped", "reason": "Image exceeds 4MB vision limit"}

        image_b64 = base64.b64encode(image_bytes).decode("utf-8")
        subject_hint = evidence_record.get("metadata", {}).get("subject")
        detail_prompt = (
            "You are analysing an investigative evidence photo. Describe subjects, hair colour, attire, "
            "visible items, text, locations, and any identifying markers. Flag if the primary subject "
            "does not match the provided subject description. Return JSON with keys: summary, subjects "
            "(list of {label, hair_color, notes, confidence}), items (list), locations (list), risks (list), "
            "and alerts (list)."
        )
        if subject_hint:
            detail_prompt += f" Primary subject of record: {subject_hint}."

        payload = {
            "model": self.image_model,
            "messages": [
                {
                    "role": "system",
                    "content": [
                        {"type": "text", "text": "You are an investigative analyst. Always respond in JSON."}
                    ]
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": detail_prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:{mime};base64,{image_b64}"}
                        }
                    ]
                }
            ],
            "max_tokens": 700,
            "temperature": 0.2,
            "response_format": {"type": "json_object"}
        }

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        try:
            resp = requests.post(
                "https://api.openai.com/v1/chat/completions",
                json=payload,
                headers=headers,
                timeout=45
            )
            if resp.status_code != 200:
                self.logger.warning("OpenAI image analysis failed (%s): %s", resp.status_code, resp.text)
                return {"status": "error", "error": f"HTTP {resp.status_code}"}
            body = resp.json()
            content = body.get("choices", [{}])[0].get("message", {}).get("content", "")
            parsed = self._safe_json(content)
        except Exception as exc:  # pragma: no cover - network/runtime errors
            self.logger.warning("OpenAI vision call failed: %s", exc)
            return {"status": "error", "error": str(exc)}

        if not isinstance(parsed, dict):
            return {"status": "error", "error": "Unexpected OpenAI vision response"}

        case_updates = self._case_updates_from_image(parsed)
        return {
            "status": "ok",
            "provider": "openai_api",
            "image": parsed,
            "case_updates": case_updates
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _case_updates_from_document(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        updates: Dict[str, Any] = {}
        if not isinstance(payload, dict):
            return updates

        summary = payload.get("summary")
        if summary:
            updates.setdefault("case", {}).setdefault("narrative", {})["summary"] = summary

        parties = payload.get("parties")
        if parties:
            updates.setdefault("case", {}).setdefault("parties", {})["mentioned"] = parties

        locations = payload.get("locations")
        if locations:
            updates.setdefault("case", {}).setdefault("locations", {})["mentioned"] = locations

        dates = payload.get("dates")
        if dates:
            updates.setdefault("case", {}).setdefault("dates", {})["mentioned"] = dates

        risks = payload.get("risks")
        if risks:
            updates.setdefault("case", {}).setdefault("alerts", {})["document_risks"] = risks

        subjects = payload.get("subject_observations")
        if subjects:
            updates.setdefault("case", {}).setdefault("subjects", {})["observations"] = subjects
        return updates

    def _case_updates_from_image(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        updates: Dict[str, Any] = {}
        if not isinstance(payload, dict):
            return updates

        summary = payload.get("summary")
        if summary:
            updates.setdefault("case", {}).setdefault("narrative", {})["image_summary"] = summary

        subjects = payload.get("subjects")
        if subjects:
            updates.setdefault("case", {}).setdefault("subjects", {})["image_observations"] = subjects

        alerts = payload.get("alerts")
        if alerts:
            updates.setdefault("case", {}).setdefault("alerts", {})["image_alerts"] = alerts
        return updates

    def _read_text(self, file_path: Path) -> Optional[str]:
        try:
            if file_path.suffix.lower() == ".pdf":
                try:
                    import PyPDF2  # type: ignore
                except Exception:  # pragma: no cover - optional dependency
                    self.logger.debug("PyPDF2 not available; cannot extract text from %s", file_path)
                    return None
                text = []
                with file_path.open("rb") as handle:
                    reader = PyPDF2.PdfReader(handle)
                    for page in reader.pages:
                        try:
                            text.append(page.extract_text() or "")
                        except Exception:  # pragma: no cover - individual page errors
                            continue
                return "\n".join(text)

            with file_path.open("r", encoding="utf-8", errors="ignore") as handle:
                return handle.read()
        except Exception as exc:  # pragma: no cover - IO errors
            self.logger.debug("Failed to read text from %s: %s", file_path, exc)
            return None

    def _build_cache_key(self, file_path: Path) -> str:
        stat = file_path.stat()
        digest = hashlib.sha256()
        digest.update(str(file_path.resolve()).encode("utf-8"))
        digest.update(str(stat.st_mtime_ns).encode("utf-8"))
        digest.update(str(stat.st_size).encode("utf-8"))
        return digest.hexdigest()

    def _read_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        if cache_key in self.cache:
            return self.cache[cache_key]
        cache_file = self.cache_dir / f"{cache_key}.json"
        if not cache_file.exists():
            return None
        try:
            data = json.loads(cache_file.read_text(encoding="utf-8"))
            self.cache[cache_key] = data
            return data
        except Exception:  # pragma: no cover - corrupted cache
            return None

    def _write_cache(self, cache_key: str, payload: Dict[str, Any]) -> None:
        self.cache[cache_key] = payload
        cache_file = self.cache_dir / f"{cache_key}.json"
        try:
            cache_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        except Exception:  # pragma: no cover - best effort
            pass

    def _call_openai_chat(self, prompt: str, *, model: str, max_tokens: int = 600) -> Optional[Dict[str, Any]]:
        api_key = self._get_openai_key()
        if not api_key:
            return None

        try:
            if HAVE_OPENAI_SDK:
                client = OpenAI(api_key=api_key)
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": "You are an investigative analyst. Respond in JSON."},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.2,
                    max_tokens=max_tokens,
                    response_format={"type": "json_object"},
                )
                content = response.choices[0].message.content  # type: ignore[attr-defined]
            elif HAVE_OPENAI_LEGACY:
                openai.api_key = api_key  # type: ignore[attr-defined]
                response = openai.ChatCompletion.create(  # type: ignore[attr-defined]
                    model=model,
                    messages=[
                        {"role": "system", "content": "You are an investigative analyst. Respond in JSON."},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.2,
                    max_tokens=max_tokens,
                )
                content = response["choices"][0]["message"]["content"]  # type: ignore[index]
            else:
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": model,
                    "messages": [
                        {"role": "system", "content": "You are an investigative analyst. Respond in JSON."},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.2,
                    "max_tokens": max_tokens,
                }
                resp = requests.post("https://api.openai.com/v1/chat/completions", json=payload, headers=headers, timeout=45)
                if resp.status_code != 200:
                    self.logger.warning("OpenAI chat completion failed (%s): %s", resp.status_code, resp.text)
                    return None
                content = resp.json().get("choices", [{}])[0].get("message", {}).get("content", "")
        except Exception as exc:  # pragma: no cover - network/runtime errors
            self.logger.warning("OpenAI chat call failed: %s", exc)
            return None

        return self._safe_json(content)

    def _safe_json(self, content: Any) -> Optional[Dict[str, Any]]:
        if isinstance(content, dict):
            return content
        if isinstance(content, str):
            content = content.strip()
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                self.logger.debug("OpenAI response was not valid JSON: %s", content[:200])
                return None
        return None

    def _get_openai_key(self) -> Optional[str]:
        key = None
        if self.api_manager and hasattr(self.api_manager, "get_key"):
            try:
                key = self.api_manager.get_key("openai_api")
            except Exception as exc:  # pragma: no cover - defensive guard
                self.logger.debug("API manager failed to supply OpenAI key: %s", exc)
        if not key:
            key = os.getenv("OPENAI_API_KEY")
        return key
