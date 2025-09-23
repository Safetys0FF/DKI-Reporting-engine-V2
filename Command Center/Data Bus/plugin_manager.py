# plugin_manager.py
# Handles plug-in discovery, validation, handshake, licensing, and registration

import os
import importlib.util
import json

class PluginManager:
    def __init__(self, bus, plugin_dir="./plugins/sections"):
        self.bus = bus
        self.plugin_dir = plugin_dir
        self.license_dir = "./plugins/licenses"
        self.plugins = {}

    def auto_register_plugins(self):
        for filename in os.listdir(self.plugin_dir):
            if filename.endswith("_manager.py"):
                path = os.path.join(self.plugin_dir, filename)
                section_id = filename.split("_")[0]  # assumes format section_X_manager.py

                module_name = filename[:-3]
                spec = importlib.util.spec_from_file_location(module_name, path)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)

                for attr in dir(mod):
                    obj = getattr(mod, attr)
                    if callable(obj) and hasattr(obj, "run"):
                        contract = getattr(obj, "plugin_contract", {})
                        if contract.get("requires_license"):
                            if not self.verify_license(contract.get("license_id")):
                                print(f"[PluginManager] License check failed for {section_id}. Skipped.")
                                continue
                        self.bus.register_plugin(section_id, obj)
                        self.plugins[section_id] = obj
                        print(f"[PluginManager] Registered {section_id} from {filename}")

    def verify_license(self, license_id):
        license_path = os.path.join(self.license_dir, f"{license_id}.license")
        if not os.path.exists(license_path):
            return False
        try:
            with open(license_path) as f:
                data = json.load(f)
                return data.get("active", False)
        except:
            return False