import inspect
import sys
from pathlib import Path
sys.path.insert(0, r"F:\The Central Command\Command Center\UI")
import central_plugin
print(inspect.getsource(central_plugin.CentralPluginAdapter.start_case))
