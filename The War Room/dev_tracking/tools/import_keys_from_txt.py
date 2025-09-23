#!/usr/bin/env python3
import json, re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
src = REPO_ROOT / "api_keys.txt"
json_path = Path('api_keys.json')
if not src.exists():
    raise SystemExit('Keys file not found')
text = src.read_text(encoding='utf-8', errors='ignore')
# naive parse: look for lines following a label
labels = {
  'chatgpt': 'openai_api_key',
  'openai': 'openai_api_key',
  'google gemini': 'google_gemini_api_key',
  'gemini': 'google_gemini_api_key',
  'google maps': 'google_maps_api_key',
  'maps': 'google_maps_api_key',
}
lines = [ln.strip() for ln in text.splitlines()]
found = {}
i = 0
while i < len(lines):
    line = lines[i].lower()
    for k, dest in labels.items():
        if k in line:
            # next non-empty line is the key
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines):
                found[dest] = lines[j].strip()
                i = j
            break
    i += 1

# load existing json
try:
    data = json.loads(json_path.read_text(encoding='utf-8'))
except Exception:
    data = {}
changed = False
for k, v in found.items():
    if v and (not data.get(k) or data.get(k, '').startswith('your_')):
        data[k] = v
        changed = True
if changed:
    json_path.write_text(json.dumps(data, indent=2), encoding='utf-8')
print(json.dumps({'updated': changed, 'keys': list(found.keys())}, indent=2))
