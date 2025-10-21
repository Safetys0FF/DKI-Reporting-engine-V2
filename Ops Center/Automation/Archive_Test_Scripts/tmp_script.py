from pathlib import Path
path = Path(r'Command Center\\UI\\central_plugin.py')
lines = path.read_text().splitlines(True)
lines[1232] = '        return "\\\\r\\\\n".join(lines).strip()\n'
print(repr(lines[1232]))
