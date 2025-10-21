# plugin_lifecycle_manager.py
# Manages plug-in installation, startup activation, downloading, and uninstallation

import os
import json
import shutil
import requests

class PluginLifecycleManager:
    def __init__(self, plugin_dir="./plugins/sections", registry_path="./plugins/plugin_registry.json"):
        self.plugin_dir = plugin_dir
        self.registry_path = registry_path
        self.registry = self.load_registry()

    def load_registry(self):
        if os.path.exists(self.registry_path):
            with open(self.registry_path, 'r') as f:
                return json.load(f)
        return {}

    def save_registry(self):
        with open(self.registry_path, 'w') as f:
            json.dump(self.registry, f, indent=4)

    def install_plugin_from_url(self, plugin_id, url):
        response = requests.get(url)
        if response.status_code == 200:
            file_path = os.path.join(self.plugin_dir, f"{plugin_id}_manager.py")
            with open(file_path, 'wb') as f:
                f.write(response.content)
            self.registry[plugin_id] = {"enabled": True, "source_url": url}
            self.save_registry()
            return True
        return False

    def uninstall_plugin(self, plugin_id):
        file_path = os.path.join(self.plugin_dir, f"{plugin_id}_manager.py")
        if os.path.exists(file_path):
            os.remove(file_path)
            self.registry.pop(plugin_id, None)
            self.save_registry()
            return True
        return False

    def enable_plugin(self, plugin_id):
        if plugin_id in self.registry:
            self.registry[plugin_id]["enabled"] = True
            self.save_registry()

    def disable_plugin(self, plugin_id):
        if plugin_id in self.registry:
            self.registry[plugin_id]["enabled"] = False
            self.save_registry()

    def is_plugin_enabled(self, plugin_id):
        return self.registry.get(plugin_id, {}).get("enabled", False)

    def list_plugins(self):
        return self.registry