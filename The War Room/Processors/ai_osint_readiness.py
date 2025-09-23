#!/usr/bin/env python3
"""
AI/OSINT Readiness Smoke
- Reports installed modules
- Detects keys from User Profile (if available) or api_keys.json
- Does not make paid network calls
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

DEV_TRACKING_DIR = Path(__file__).resolve().parents[1]
if str(DEV_TRACKING_DIR) not in sys.path:
    sys.path.insert(0, str(DEV_TRACKING_DIR))

from path_bootstrap import bootstrap_paths

bootstrap_paths(__file__)

from config import get_config

status = {
    'modules': {},
    'keys': {},
}

# Modules
try:
    import openai  # noqa
    status['modules']['openai'] = True
except Exception:
    status['modules']['openai'] = False

try:
    from bs4 import BeautifulSoup  # noqa
    status['modules']['beautifulsoup4'] = True
except Exception:
    status['modules']['beautifulsoup4'] = False

try:
    import spacy  # noqa
    status['modules']['spacy'] = True
except Exception:
    status['modules']['spacy'] = False

try:
    from transformers import pipeline  # noqa
    status['modules']['transformers'] = True
except Exception:
    status['modules']['transformers'] = False

# Keys: from config and api_keys.json
cfg = get_config()
status['keys']['enable_osint'] = bool(cfg.get('ai','enable_osint'))
status['keys']['openai_api_key'] = bool(cfg.get('ai','openai_api_key'))

api_keys_path = Path('api_keys.json')
if api_keys_path.exists():
    try:
        data = json.loads(api_keys_path.read_text(encoding='utf-8'))
        for k in ['openai_api_key','google_maps_api_key','google_search_api_key','google_search_engine_id','bing_search_api_key']:
            status['keys'][k] = bool(data.get(k) and not str(data.get(k)).startswith('your_'))
    except Exception:
        pass

print(json.dumps(status, indent=2))
