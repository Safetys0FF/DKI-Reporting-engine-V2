import importlib.util
import inspect
import sys
from pathlib import Path

root = Path(r"F:\The Central Command")
sys.path.insert(0, str(root / "The Marshall" / "Gateway"))
sys.path.insert(0, str(root / "The War Room" / "Processors"))

spec = importlib.util.spec_from_file_location('gateway', str(root / "The Marshall" / "Gateway" / "gateway_controller.py"))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
cls = module.GatewayController
source, start = inspect.getsourcelines(cls.__init__)
for line in source:
    print(line.rstrip())
