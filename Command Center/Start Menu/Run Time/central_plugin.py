from pathlib import Path
import sys
from importlib.util import spec_from_file_location, module_from_spec

ROOT_DIR = Path(r"F:\The Central Command")
UI_DIR = ROOT_DIR / "Command Center" / "UI"
if str(UI_DIR) not in sys.path:
    sys.path.insert(0, str(UI_DIR))

# Ensure shared component paths match the UI plugin expectations
runtime_paths = [
    ROOT_DIR / "The Warden",
    ROOT_DIR / "Evidence Locker",
    ROOT_DIR / "The Marshall",
    ROOT_DIR / "Command Center" / "Mission Debrief",
    ROOT_DIR / "Command Center" / "Mission Debrief" / "The Librarian",
    ROOT_DIR / "Command Center" / "Mission Debrief" / "Debrief" / "README",
    ROOT_DIR / "Command Center" / "Data Bus" / "Bus Core Design",
]
for candidate in runtime_paths:
    candidate_str = str(candidate)
    if candidate.exists() and candidate_str not in sys.path:
        sys.path.append(candidate_str)

UI_PLUGIN_PATH = UI_DIR / "central_plugin.py"
_spec = spec_from_file_location("central_command_ui.central_plugin", UI_PLUGIN_PATH)
if _spec is None or _spec.loader is None:
    raise ImportError(f"Unable to load Central Command UI plugin from {UI_PLUGIN_PATH}")
_ui_module = module_from_spec(_spec)
_spec.loader.exec_module(_ui_module)

CentralPlugin = getattr(_ui_module, "CentralPlugin", None)
CentralPluginAdapter = getattr(_ui_module, "CentralPluginAdapter")

__all__ = [name for name in ("CentralPlugin", "CentralPluginAdapter") if name in globals() and globals()[name] is not None]
