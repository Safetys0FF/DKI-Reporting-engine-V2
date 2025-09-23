# api_manager.py
# Handles API registration, toggle states, validation, and status polling

import os
import json
import requests

class APIManager:
    def __init__(self, config_path="./configs/api_keys.json"):
        self.config_path = config_path
        self.api_registry = {}
        self.load_keys()

    def load_keys(self):
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                self.api_registry = json.load(f)
        else:
            self.api_registry = {}

    def save_keys(self):
        with open(self.config_path, 'w') as f:
            json.dump(self.api_registry, f, indent=4)

    def register_api(self, name, key, endpoint):
        self.api_registry[name] = {
            "key": key,
            "endpoint": endpoint,
            "enabled": True
        }
        self.save_keys()

    def toggle_api(self, name, enabled):
        if name in self.api_registry:
            self.api_registry[name]["enabled"] = enabled
            self.save_keys()

    def is_enabled(self, name):
        return self.api_registry.get(name, {}).get("enabled", False)

    def get_key(self, name):
        return self.api_registry.get(name, {}).get("key")

    def get_endpoint(self, name):
        return self.api_registry.get(name, {}).get("endpoint")

    def test_api(self, name):
        if not self.is_enabled(name):
            return {"status": "disabled"}

        url = self.get_endpoint(name)
        headers = {"Authorization": f"Bearer {self.get_key(name)}"}
        try:
            res = requests.get(url, headers=headers, timeout=5)
            return {"status": res.status_code, "response": res.text[:200]}
        except Exception as e:
            return {"status": "error", "error": str(e)}