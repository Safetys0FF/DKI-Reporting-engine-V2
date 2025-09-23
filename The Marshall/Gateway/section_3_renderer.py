# Section 3 Surveillance Logs Renderer Logic

from datetime import datetime
import re

class Section3Renderer:
    """
    Handles Section 3: Daily Surveillance Logs
    - Field logs with full time-stamp format
    - Placeholder compliance
    - 3x cyclical fallback logic across 4 data zones
    - Outputs section artifact + manifest, returns to Gateway
    """

    SECTION_KEY = "section_3"
    TITLE = "SECTION 3 – SURVEILLANCE REPORTS / DAILY LOGS"

    WHITELIST_FIELDS = [
        "date_block", "time_logs", "field_agent", "location_context", "activities_observed",
        "photos_captured", "vehicles_logged", "weather_conditions", "narrative_notes",
        "voice_memos"
    ]

    PLACEHOLDERS = {
        "unknown": "*Unknown*",
        "unconfirmed": "*Unconfirmed at this time*",
        "suppressed": "*Due to the nature of this case this portion was not performed or was not necessary*"
    }

    BANNED_TOKENS = {"", " ", "N/A", "NA", "TBD", "[REDACTED]", "REDACTED"}

    STYLE_RULES = {
        "font": "Times New Roman",
        "section_title": {"size_pt": 16, "bold": True, "all_caps": True, "align": "center", "shaded_background": True},
        "header": {"size_pt": 14, "bold": True, "underline": True, "all_caps": True, "align": "left"},
        "field_label": {"size_pt": 12, "bold": True, "align": "left"},
        "field_value": {"size_pt": 12, "bold": False, "italic": False, "align": "left"},
        "placeholder_value": {"size_pt": 12, "italic": True, "align": "left"},
        "line_spacing": 1.15
    }

    def _normalize(self, val):
        return str(val).strip() if val else None

    def _placeholder_for(self, key, value):
        if not value or value.upper() in self.BANNED_TOKENS:
            return self.PLACEHOLDERS["unknown"], True
        return value, False

    def _fallback_check(self, key, zones):
        """
        Performs 3x cyclical validation over all fallback zones:
        - intake, notes, evidence, prior_section
        Returns first valid value or None after full cycle
        """
        for _ in range(3):
            for zone in ["intake", "notes", "evidence", "prior_section"]:
                val = zones.get(zone, {}).get(key)
                if val:
                    return val
        return None

    def _to_dt(self, ts):
        if not ts:
            return None
        try:
            return datetime.fromisoformat(str(ts).replace('T', ' '))
        except Exception:
            return None

    def _extract_time_windows(self, text):
        """Heuristically extract time windows from free text like '2025-09-13 08:00 - 10:30'"""
        windows = []
        if not text:
            return windows
        pat = re.compile(r"(\d{4}-\d{2}-\d{2})\s+(\d{1,2}:\d{2})(?:\s*[-to]{1,3}\s*)(\d{1,2}:\d{2})")
        for m in pat.finditer(str(text)):
            day, s1, s2 = m.group(1), m.group(2), m.group(3)
            try:
                start = datetime.fromisoformat(f"{day} {s1}:00")
                end = datetime.fromisoformat(f"{day} {s2}:00")
                if end > start:
                    windows.append((start, end))
            except Exception:
                continue
        return windows

    def _media_timestamp(self, data):
        # Prefer processing_timestamp, then EXIF DateTimeOriginal/DateTime, else None
        ts = (data or {}).get('processing_timestamp')
        if ts:
            return ts
        exif = (data or {}).get('exif') or {}
        for k in ('DateTimeOriginal', 'DateTime'):
            if exif.get(k):
                try:
                    t = exif[k].replace(':', '-', 2)
                    datetime.fromisoformat(t)  # validate
                    return t
                except Exception:
                    continue
        return None

    def _build_internal_sidebar(self, payload):
        # Build internal-only cross references of media matched to time windows
        windows = []
        for key in ('time_logs', 'date_block'):
            if payload.get(key):
                windows.extend(self._extract_time_windows(payload.get(key)))
        images = (payload.get('images') or {}).items()
        videos = (payload.get('videos') or {}).items()
        refs = []
        for start, end in windows:
            matched = []
            for mid, md in list(images) + list(videos):
                ts = self._media_timestamp(md)
                dt = self._to_dt(ts)
                if dt and start <= dt <= end:
                    matched.append({
                        'id': mid,
                        'kind': 'video' if (mid in (payload.get('videos') or {})) else 'image',
                        'captured_at': dt.isoformat(),
                    })
            refs.append({
                'window_start': start.isoformat(),
                'window_end': end.isoformat(),
                'matched_media': matched,
            })
        return {
            'windows': refs,
            'counts': {
                'windows': len(windows),
                'images': len(images),
                'videos': len(videos),
                'matches': sum(len(r['matched_media']) for r in refs),
            },
            'policies': payload.get('data_policies', {}),
        }

    def _format_voice_memos(self, memos):
        if not memos:
            placeholder = self.PLACEHOLDERS["unknown"]
            return placeholder, True

        entries = []
        if isinstance(memos, dict):
            memos = memos.values()
        for idx, memo in enumerate(memos, 1):
            if not isinstance(memo, dict):
                continue
            name = memo.get('name') or f'Voice Memo {idx}'
            summary = memo.get('summary') or memo.get('text') or memo.get('transcript')
            if not summary:
                continue
            language = memo.get('language')
            duration = memo.get('duration')
            entry = f"{idx}. {name}: {summary.strip()}"
            if language:
                entry += f" (Language: {language})"
            if duration:
                entry += f" [Duration: {duration}]"
            entries.append(entry)

        if not entries:
            placeholder = self.PLACEHOLDERS["unknown"]
            return placeholder, True

        formatted = '\n'.join(entries)
        return formatted, False

    def render_model(self, section_payload, case_sources):
        rendered_blocks = []
        drift_bounced = {}
        placeholders_used = {}

        rendered_blocks.append({
            "type": "title",
            "text": self.TITLE,
            "style": self.STYLE_RULES["section_title"]
        })

        for key in self.WHITELIST_FIELDS:
            if key == 'voice_memos':
                value, is_ph = self._format_voice_memos(section_payload.get('voice_memos'))
            else:
                val = section_payload.get(key)
                if not val:
                    val = self._fallback_check(key, case_sources)

                value, is_ph = self._placeholder_for(key, self._normalize(val))

            if is_ph:
                placeholders_used[key] = value

            rendered_blocks.append({
                "type": "field",
                "label": key.replace("_", " " ).title(),
                "value": value,
                "style": self.STYLE_RULES["placeholder_value"] if is_ph else self.STYLE_RULES["field_value"]
            })
        manifest = {
            "section_key": self.SECTION_KEY,
            "fields_rendered": self.WHITELIST_FIELDS,
            "placeholders_used": placeholders_used,
            "drift_bounced": drift_bounced,
            'voice_memos': section_payload.get('voice_memos', []),
            # Internal-only sidebar for audit/cross-reference (not client-facing)
            "internal_sidebar": self._build_internal_sidebar(section_payload)
        }

        return {
            "render_tree": rendered_blocks,
            "manifest": manifest,
            "handoff": "gateway"
        }
