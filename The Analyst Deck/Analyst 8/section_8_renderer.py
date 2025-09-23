#!/usr/bin/env python3
"""
Section 8 Renderer - Photo / Evidence Index

Chronologically organizes and displays photo and video surveillance evidence.
Rules per spec:
- Group by day with heading: "DATE OF SURVEILLANCE: Day, Month DD, YYYY"
- List Photos first, then Videos per day; each numbered starting at 1
- Omit internal filenames/paths/camera tags
- Keep only media items provably aligned with Section 3/4 + metadata
- GPS: "Observed near, [nearest mailing address]" when available (fallback to field notes)
- Render 2x2 grid (handled by exporters) and include textual fallback
"""

from __future__ import annotations

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import logging
import os

logger = logging.getLogger(__name__)

DATE_FMT_HEADING = "%A, %B %d, %Y"  # Day, Month DD, YYYY
MIN_WIDTH, MIN_HEIGHT = 640, 480


class Section8Renderer:
    SECTION_KEY = "section_8"
    TITLE = "8. Photo / Evidence Index"

    STYLE_RULES = {
        "font": "Times New Roman",
        "section_title": {"size_pt": 16, "bold": True, "all_caps": True, "align": "center", "shaded_background": True},
        "header": {"size_pt": 14, "bold": True, "underline": True, "all_caps": True, "align": "left"},
        "paragraph": {"size_pt": 12, "bold": False, "italic": False, "align": "left"},
        "emphasis": {"size_pt": 12, "italic": True, "align": "left"},
        "line_spacing": 1.15,
    }

    def render_model(self, section_payload: Dict[str, Any], case_sources: Dict[str, Any]) -> Dict[str, Any]:
        try:
            images: Dict[str, Dict[str, Any]] = section_payload.get('images', {}) or {}
            videos: Dict[str, Dict[str, Any]] = section_payload.get('videos', {}) or {}
            previous_sections: Dict[str, Any] = section_payload.get('previous_sections', {}) or {}
            manual_notes: Dict[str, str] = section_payload.get('manual_notes', {}) or {}
            api_keys: Dict[str, str] = section_payload.get('api_keys', {}) or {}
            policies: Dict[str, Any] = section_payload.get('data_policies', {}) or {}
            field_notes: Dict[str, Any] = case_sources.get('notes', {}) if isinstance(case_sources, dict) else {}
            # Prepare geocoder from API keys if available
            self._geocoder_key = None
            self._api_keys = api_keys
            try:
                from geocoding_util import extract_google_maps_key
                self._geocoder_key = extract_google_maps_key(api_keys)
            except Exception:
                self._geocoder_key = None

            # Collect and normalize media items
            items: List[Dict[str, Any]] = []
            items.extend(self._collect_media(images, kind='image'))
            items.extend(self._collect_media(videos, kind='video'))
            audio_clips: Dict[str, Any] = section_payload.get('audio', {}) or {}
            items.extend(self._collect_media(audio_clips, kind='audio'))

            # Filter: low-quality and duplicates
            items = self._filter_low_quality(items)
            items = self._dedupe_items(items)

            # Enforce relevance via continuity (Sec 3 / Sec 4) + metadata alignment
            sec3 = previous_sections.get('section_3', {})
            sec4 = previous_sections.get('section_4', {})
            items = [it for it in items if self._is_relevant(it, sec3, sec4)]

            # Group by date string
            grouped: Dict[str, List[Dict[str, Any]]] = {}
            for it in items:
                dt = it.get('captured_at') or it.get('processing_timestamp')
                date_key = self._date_key(dt)
                grouped.setdefault(date_key, []).append(it)

            # Build render tree
            render_tree: List[Dict[str, Any]] = []
            render_tree.append({
                "type": "title",
                "text": self.TITLE,
                "style": self.STYLE_RULES["section_title"],
            })

            manifest: Dict[str, Any] = {
                "section_key": self.SECTION_KEY,
                "dates": list(grouped.keys()),
                "counts": {},
            }

            # Sort dates chronologically
            for date_key in sorted(grouped.keys(), key=lambda d: self._date_parse(d)):
                day_items = grouped[date_key]
                # Split photos then videos, each sorted chronologically
                photos = sorted([i for i in day_items if i['kind'] == 'image'], key=lambda x: x.get('captured_at') or x.get('processing_timestamp') or '')
                videos_k = sorted([i for i in day_items if i['kind'] == 'video'], key=lambda x: x.get('captured_at') or x.get('processing_timestamp') or '')
                audios = sorted([i for i in day_items if i['kind'] == 'audio'], key=lambda x: x.get('captured_at') or x.get('processing_timestamp') or '')

                manifest["counts"][date_key] = {"photos": len(photos), "videos": len(videos_k), "audio": len(audios)}

                # Date header
                render_tree.append({
                    "type": "header",
                    "text": f"DATE OF SURVEILLANCE: {date_key}",
                    "style": self.STYLE_RULES["header"],
                })

                # Numbering per day
                pnum, vnum = 1, 1

                # Photos first
                for it in photos:
                    caption = f"Photo {pnum}"
                    render_tree.extend(self._image_block(it, caption, manual_notes, field_notes))
                    pnum += 1

                # Videos after (with mid-point thumbnail if available)
                for it in videos_k:
                    caption = f"Video {vnum}"
                    render_tree.extend(self._image_block(it, caption, manual_notes, field_notes, is_video=True))
                    vnum += 1

                # Audio memos
                anum = 1
                for it in audios:
                    caption = f"Audio Memo {anum}"
                    render_tree.extend(self._audio_block(it, caption))
                    anum += 1

            return {
                "render_tree": render_tree,
                "manifest": manifest,
                "handoff": "gateway",
            }

        except Exception as e:
            logger.error(f"Section 8 render failed: {e}")
            return {
                "render_tree": [
                    {"type": "title", "text": self.TITLE, "style": self.STYLE_RULES["section_title"]},
                    {"type": "paragraph", "text": f"Error generating Section 8: {e}", "style": self.STYLE_RULES["emphasis"]},
                ],
                "manifest": {"section_key": self.SECTION_KEY, "error": str(e)},
                "handoff": "gateway",
            }

    # -------------------- Helpers -------------------- #
    def _collect_media(self, media_map: Dict[str, Dict[str, Any]], kind: str) -> List[Dict[str, Any]]:
        items = []
        for mid, data in media_map.items():
            try:
                fi = (data or {}).get('file_info', {})
                dims = data.get('dimensions') or data.get('resolution')
                w, h = (dims if isinstance(dims, (tuple, list)) and len(dims) == 2 else (None, None))
                exif = data.get('exif', {}) if isinstance(data.get('exif'), dict) else {}
                metadata = data.get('metadata', {})
                ts = self._select_timestamp(data, exif, fi)
                item = {
                    'id': mid,
                    'kind': kind,
                    'path': fi.get('path'),
                    'file_hash': data.get('file_hash'),
                    'dimensions': (w, h) if w and h else None,
                    'captured_at': ts,
                    'processing_timestamp': data.get('processing_timestamp'),
                    'exif': exif,
                    'metadata': metadata,
                }

                if kind == 'audio':
                    transcription_payload = data.get('transcription') if isinstance(data.get('transcription'), dict) else {}
                    item['transcript'] = data.get('summary') or data.get('transcript') or transcription_payload.get('summary') or transcription_payload.get('text')
                    item['language'] = data.get('transcript_language') or transcription_payload.get('language')
                    item['duration'] = data.get('duration')
                    item['segments'] = data.get('transcription_segments') or transcription_payload.get('segments')
                    item['metadata'] = metadata or {}
                    generated = data.get('transcription_generated_at') or transcription_payload.get('generated_at')
                    if generated and not item.get('captured_at'):
                        item['captured_at'] = generated
                # Compute video thumbnail lazily in exporters; we keep placeholder
                items.append(item)
            except Exception:
                continue
        return items

    def _filter_low_quality(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        ok = []
        for it in items:
            dims = it.get('dimensions')
            if it['kind'] == 'image' and dims:
                w, h = dims
                if w < MIN_WIDTH or h < MIN_HEIGHT:
                    continue
            ok.append(it)
        return ok

    def _dedupe_items(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        seen_hash = set()
        kept: List[Dict[str, Any]] = []
        for it in sorted(items, key=lambda x: (x.get('captured_at') or x.get('processing_timestamp') or '')):
            fh = it.get('file_hash')
            dims = it.get('dimensions')
            ts = self._to_dt(it.get('captured_at') or it.get('processing_timestamp'))
            if fh and fh in seen_hash:
                continue
            near_dup = False
            for prev in kept:
                if dims and prev.get('dimensions') == dims:
                    pts = self._to_dt(prev.get('captured_at') or prev.get('processing_timestamp'))
                    if ts and pts and abs((ts - pts).total_seconds()) <= 2:
                        near_dup = True
                        break
            if near_dup:
                continue
            if fh:
                seen_hash.add(fh)
            kept.append(it)
        return kept

    def _is_relevant(self, item: Dict[str, Any], sec3: Dict[str, Any], sec4: Dict[str, Any]) -> bool:
        # Heuristic continuity: if capture time falls within any session/log window extracted from text
        # Parse render_tree content text blocks for time anchors
        try:
            ts = self._to_dt(item.get('captured_at') or item.get('processing_timestamp'))
            if not ts:
                return False
            windows = []
            for sec in (sec3, sec4):
                content = ''
                if isinstance(sec, dict):
                    content = (sec.get('content') or '')
                windows.extend(self._extract_time_windows(content))
            for start, end in windows:
                if start <= ts <= end:
                    return True
            return False
        except Exception:
            return False

    def _image_block(self, it: Dict[str, Any], caption: str, manual_notes: Dict[str, str], field_notes: Dict[str, Any], is_video: bool = False) -> List[Dict[str, Any]]:
        blocks: List[Dict[str, Any]] = []
        # Compose per-item text
        ts_str = self._fmt_ts(it.get('captured_at') or it.get('processing_timestamp'))
        # Resolve address lazily; exporter may attempt API geocode; here we provide placeholder text
        address_line = self._resolve_address_text(it, field_notes)
        user_note = manual_notes.get(it.get('id') or '', '')
        if user_note:
            user_note = user_note.strip()[:150]

        # Emit an image block for exporters, plus a text fallback paragraph
        img_path = it.get('path')
        if is_video and img_path:
            thumb = self._ensure_video_thumbnail(img_path)
            if thumb:
                img_path = thumb
        blocks.append({
            "type": "image",
            "path": img_path,
            "is_video": is_video,
            "label": caption,
            "timestamp": ts_str,
            "address": address_line,
            "note": f"* {user_note}" if user_note else None,
        })

        # Fallback text in content rendering
        lines = [f"{caption}"]
        if ts_str:
            lines.append(f"  Time: {ts_str}")
        if address_line:
            lines.append(f"  {address_line}")
        if user_note:
            lines.append(f"  * {user_note}")
        blocks.append({
            "type": "paragraph",
            "text": "\n".join(lines),
            "style": self.STYLE_RULES["paragraph"],
        })
        return blocks

    # -------------------- Utilities -------------------- #    def _audio_block(self, it: Dict[str, Any], caption: str) -> List[Dict[str, Any]]:
        blocks: List[Dict[str, Any]] = []
        transcript = it.get('transcript') or it.get('summary')
        if transcript:
            blocks.append({
                "type": "paragraph",
                "text": f"{caption}: {transcript}",
                "style": self.STYLE_RULES["paragraph"]
            })
        else:
            blocks.append({
                "type": "paragraph",
                "text": f"{caption}: *No transcript available*",
                "style": self.STYLE_RULES["emphasis"]
            })

        meta_parts = []
        if it.get('language'):
            meta_parts.append(f"Language: {it['language']}")
        if it.get('duration'):
            meta_parts.append(f"Duration: {it['duration']}")
        if meta_parts:
            blocks.append({
                "type": "paragraph",
                "text": ' | '.join(meta_parts),
                "style": self.STYLE_RULES["emphasis"]
            })

        return blocks


    def _select_timestamp(self, data: Dict[str, Any], exif: Dict[str, Any], file_info: Dict[str, Any]) -> Optional[str]:
        # EXIF DateTimeOriginal -> OCR overlay timestamp (from OCR text heuristics) -> file modified time
        for key in ("DateTimeOriginal", "DateTime"):
            if key in exif and exif[key]:
                try:
                    # Common EXIF format: 'YYYY:MM:DD HH:MM:SS'
                    t = exif[key].replace(':', '-', 2)
                    dt = datetime.fromisoformat(t)
                    return dt.isoformat()
                except Exception:
                    pass
        # OCR overlay timestamp heuristic (best-effort)
        ocr_text = (data.get('text') or '').strip()
        if ocr_text:
            ts = self._find_timestamp_in_text(ocr_text)
            if ts:
                return ts
        # File modified time from file_info if available
        try:
            p = file_info.get('path')
            if p and os.path.exists(p):
                mtime = datetime.fromtimestamp(os.path.getmtime(p))
                return mtime.isoformat()
        except Exception:
            pass
        # Fallback to processing timestamp
        return data.get('processing_timestamp')

    def _find_timestamp_in_text(self, text: str) -> Optional[str]:
        import re
        patterns = [
            r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})",
            r"(\d{2}/\d{2}/\d{4} \d{1,2}:\d{2}(:\d{2})?)",
        ]
        for pat in patterns:
            m = re.search(pat, text)
            if m:
                s = m.group(1)
                # Normalize to ISO
                try:
                    if '/' in s:
                        # MM/DD/YYYY HH:MM[:SS]
                        parts = s.split(' ')
                        md, y = parts[0], parts[1:]
                        m1, d1, y1 = md.split('/')
                        rest = ' '.join(y)
                        dt = datetime.fromisoformat(f"{y1}-{int(m1):02d}-{int(d1):02d} {rest}")
                    else:
                        dt = datetime.fromisoformat(s)
                    return dt.isoformat()
                except Exception:
                    return s
        return None

    def _date_key(self, ts: Optional[str]) -> str:
        dt = self._to_dt(ts) or datetime.now()
        return dt.strftime(DATE_FMT_HEADING)

    def _fmt_ts(self, ts: Optional[str]) -> Optional[str]:
        if not ts:
            return None
        try:
            dt = self._to_dt(ts)
            return dt.strftime("%Y-%m-%d %H:%M:%S") if dt else None
        except Exception:
            return ts

    def _to_dt(self, ts: Optional[str]) -> Optional[datetime]:
        if not ts:
            return None
        try:
            # Support 'YYYY-MM-DD HH:MM:SS' or ISO
            s = ts.replace('T', ' ')
            return datetime.fromisoformat(s)
        except Exception:
            return None

    def _date_parse(self, date_key: str) -> datetime:
        try:
            return datetime.strptime(date_key, DATE_FMT_HEADING)
        except Exception:
            return datetime.min

    def _extract_time_windows(self, content: str) -> List[Tuple[datetime, datetime]]:
        """Heuristically extract time windows (start/end) from section content text."""
        import re
        windows: List[Tuple[datetime, datetime]] = []
        # Match ranges like 2025-09-13 08:00 - 10:30
        pat = re.compile(r"(\d{4}-\d{2}-\d{2})\s+(\d{1,2}:\d{2})(?:\s*[-to]{1,3}\s*)(\d{1,2}:\d{2})")
        for m in pat.finditer(content or ""):
            day, s1, s2 = m.group(1), m.group(2), m.group(3)
            try:
                start = datetime.fromisoformat(f"{day} {s1}:00")
                end = datetime.fromisoformat(f"{day} {s2}:00")
                if end > start:
                    windows.append((start, end))
            except Exception:
                continue
        return windows

    def _resolve_address_text(self, item: Dict[str, Any], field_notes: Dict[str, Any]) -> Optional[str]:
        # Placeholder: exporters may attempt actual geocoding via profile API keys
        # If API keys provided, attempt reverse geocoding via Google Maps
        try:
            exif = item.get('exif') or {}
            latlon = self._extract_latlon(exif)
            if latlon:
                # Orchestrated lookup: ChatGPT -> Copilot -> Google Maps
                try:
                    from smart_lookup import SmartLookupResolver
                    sl = SmartLookupResolver(api_keys=(self._api_keys if hasattr(self, '_api_keys') else {}),
                                             policies=section_payload.get('data_policies', {}),
                                             cache=section_payload.get('lookup_cache'))
                    addr = sl.reverse_geocode(latlon[0], latlon[1])
                    if addr:
                        return f"Observed near, {addr}"
                except Exception:
                    pass
                # Fallback Google-only if policy keys were collected separately
                if getattr(self, '_geocoder_key', None):
                    try:
                        from geocoding_util import ReverseGeocoder
                        rg = ReverseGeocoder(self._geocoder_key)
                        addr = rg.reverse(latlon[0], latlon[1])
                        if addr:
                            return f"Observed near, {addr}"
                    except Exception:
                        pass
                # No API or failed; generic placeholder
                return "Observed near, [nearest mailing address]"
            # Fallback to field notes
            loc = field_notes.get('location') if isinstance(field_notes, dict) else None
            if loc:
                return f"Observed near, {loc}"
        except Exception:
            pass
        return None

    def _extract_latlon(self, exif: Dict[str, Any]) -> Optional[Tuple[float, float]]:
        try:
            # Handle flattened EXIF fields
            if 'GPSLatitude' in exif and 'GPSLongitude' in exif:
                lat = self._convert_gps(exif.get('GPSLatitude'), exif.get('GPSLatitudeRef', 'N'))
                lon = self._convert_gps(exif.get('GPSLongitude'), exif.get('GPSLongitudeRef', 'E'))
                return (lat, lon)
            # Handle nested GPSInfo dict
            gps = exif.get('GPSInfo')
            if isinstance(gps, dict):
                # Standard GPS tags
                lat = gps.get(2)  # GPSLatitude
                lat_ref = gps.get(1, 'N')
                lon = gps.get(4)  # GPSLongitude
                lon_ref = gps.get(3, 'E')
                if lat and lon:
                    return (self._convert_gps(lat, lat_ref), self._convert_gps(lon, lon_ref))
        except Exception:
            pass
        return None

    def _convert_gps(self, value, ref) -> float:
        # Convert EXIF GPS rationals to decimal degrees
        try:
            def to_float(x):
                try:
                    return float(x[0]) / float(x[1]) if isinstance(x, tuple) else float(x)
                except Exception:
                    return float(x)
            if isinstance(value, (list, tuple)) and len(value) >= 3:
                d = to_float(value[0])
                m = to_float(value[1])
                s = to_float(value[2])
                dec = d + m/60.0 + s/3600.0
            else:
                dec = float(value)
            if isinstance(ref, bytes):
                ref = ref.decode(errors='ignore')
            ref = str(ref)
            if ref in ('S', 'W'):
                dec = -dec
            return dec
        except Exception:
            return 0.0

    def _ensure_video_thumbnail(self, video_path: str) -> Optional[str]:
        """Create a mid-point thumbnail for a video if possible. Returns path or None."""
        try:
            import cv2
            import tempfile
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS) or 0
            total = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0
            if total <= 0 or fps <= 0:
                cap.release()
                return None
            mid_frame = int(total // 2)
            cap.set(cv2.CAP_PROP_POS_FRAMES, mid_frame)
            ok, frame = cap.read()
            cap.release()
            if not ok:
                return None
            # Write thumbnail to temp file
            thumb_dir = os.path.join(tempfile.gettempdir(), 'dki_thumbs')
            os.makedirs(thumb_dir, exist_ok=True)
            base = os.path.splitext(os.path.basename(video_path))[0]
            out_path = os.path.join(thumb_dir, f"{base}_mid.jpg")
            cv2.imwrite(out_path, frame)
            return out_path if os.path.exists(out_path) else None
        except Exception:
            return None
