# api_manager.py
# Handles API registration, toggle states, validation, and status polling
# Enhanced for Data Bus integration

import os
import json
import requests
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class APIManager:
    def __init__(self, config_path="./configs/api_keys.json"):
        self.config_path = config_path
        self.api_registry = {}
        self.rate_limits = {}
        self.cache = {}
        self.cache_expiry = {}
        self.load_keys()
        self.load_config()

    def load_keys(self):
        """Load API keys from configuration file"""
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                self.api_registry = json.load(f)
        else:
            self.api_registry = {}
            logger.warning(f"API keys file not found: {self.config_path}")

    def load_config(self):
        """Load API configuration settings"""
        config_path = os.path.join(os.path.dirname(self.config_path), "api_config.json")
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                self.config = json.load(f)
        else:
            self.config = {
                "api_settings": {
                    "rate_limits": {},
                    "timeouts": {"default": 30},
                    "retry_settings": {"max_retries": 3, "backoff_factor": 2},
                    "cache_settings": {"enabled": True, "ttl_seconds": 3600}
                }
            }

    def save_keys(self):
        """Save API keys to configuration file"""
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(self.api_registry, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save API keys: {e}")

    def register_api(self, name: str, key: str, endpoint: str, description: str = ""):
        """Register a new API with the system"""
        self.api_registry[name] = {
            "key": key,
            "endpoint": endpoint,
            "enabled": True,
            "description": description,
            "registered_at": datetime.now().isoformat()
        }
        self.save_keys()
        logger.info(f"Registered API: {name}")

    def toggle_api(self, name: str, enabled: bool):
        """Enable or disable an API"""
        if name in self.api_registry:
            self.api_registry[name]["enabled"] = enabled
            self.save_keys()
            logger.info(f"API {name} {'enabled' if enabled else 'disabled'}")

    def is_enabled(self, name: str) -> bool:
        """Check if an API is enabled"""
        return self.api_registry.get(name, {}).get("enabled", False)

    def get_key(self, name: str) -> Optional[str]:
        """Get API key for a service"""
        return self.api_registry.get(name, {}).get("key")

    def get_endpoint(self, name: str) -> Optional[str]:
        """Get API endpoint for a service"""
        return self.api_registry.get(name, {}).get("endpoint")

    def test_api(self, name: str) -> Dict[str, Any]:
        """Test API connectivity and return status"""
        if not self.is_enabled(name):
            return {"status": "disabled", "message": f"API {name} is disabled"}

        api_config = self.api_registry.get(name, {})
        if not api_config.get("key"):
            return {"status": "no_key", "message": f"No API key configured for {name}"}

        try:
            # Test different APIs based on type
            if "openai" in name.lower():
                return self._test_openai_api(api_config)
            elif "google" in name.lower():
                return self._test_google_api(api_config)
            elif "bing" in name.lower():
                return self._test_bing_api(api_config)
            else:
                return self._test_generic_api(api_config)
        except Exception as e:
            logger.error(f"API test failed for {name}: {e}")
            return {"status": "error", "message": str(e)}

    def _test_openai_api(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Test OpenAI API connectivity"""
        try:
            import openai
            openai.api_key = config["key"]
            
            # Simple test request
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Test"}],
                max_tokens=5
            )
            
            return {
                "status": "success",
                "message": "OpenAI API is working",
                "response_time": 0  # Could add timing
            }
        except Exception as e:
            return {"status": "error", "message": f"OpenAI API test failed: {str(e)}"}

    def _test_google_api(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Test Google API connectivity"""
        try:
            # Test with a simple geocoding request
            endpoint = config["endpoint"]
            key = config["key"]
            
            test_url = f"{endpoint}/geocode/json?address=New+York&key={key}"
            response = requests.get(test_url, timeout=10)
            
            if response.status_code == 200:
                return {
                    "status": "success",
                    "message": "Google API is working",
                    "response_time": response.elapsed.total_seconds()
                }
            else:
                return {
                    "status": "error",
                    "message": f"Google API returned status {response.status_code}"
                }
        except Exception as e:
            return {"status": "error", "message": f"Google API test failed: {str(e)}"}

    def _test_bing_api(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Test Bing API connectivity"""
        try:
            endpoint = config["endpoint"]
            key = config["key"]
            
            headers = {"Ocp-Apim-Subscription-Key": key}
            test_url = f"{endpoint}/search?q=test&count=1"
            
            response = requests.get(test_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                return {
                    "status": "success",
                    "message": "Bing API is working",
                    "response_time": response.elapsed.total_seconds()
                }
            else:
                return {
                    "status": "error",
                    "message": f"Bing API returned status {response.status_code}"
                }
        except Exception as e:
            return {"status": "error", "message": f"Bing API test failed: {str(e)}"}

    def _test_generic_api(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Test generic API connectivity"""
        try:
            endpoint = config["endpoint"]
            response = requests.get(endpoint, timeout=10)
            
            if response.status_code in [200, 401, 403]:  # 401/403 means API is reachable
                return {
                    "status": "success",
                    "message": "API endpoint is reachable",
                    "response_time": response.elapsed.total_seconds()
                }
            else:
                return {
                    "status": "error",
                    "message": f"API returned status {response.status_code}"
                }
        except Exception as e:
            return {"status": "error", "message": f"API test failed: {str(e)}"}

    def get_api_status(self) -> Dict[str, Any]:
        """Get comprehensive API status for all registered APIs"""
        status = {
            "total_apis": len(self.api_registry),
            "enabled_apis": 0,
            "disabled_apis": 0,
            "apis_with_keys": 0,
            "apis_without_keys": 0,
            "api_details": {}
        }
        
        for name, config in self.api_registry.items():
            enabled = config.get("enabled", False)
            has_key = bool(config.get("key"))
            
            if enabled:
                status["enabled_apis"] += 1
            else:
                status["disabled_apis"] += 1
                
            if has_key:
                status["apis_with_keys"] += 1
            else:
                status["apis_without_keys"] += 1
            
            status["api_details"][name] = {
                "enabled": enabled,
                "has_key": has_key,
                "endpoint": config.get("endpoint", ""),
                "description": config.get("description", "")
            }
        
        return status

    def get_available_apis(self) -> List[str]:
        """Get list of available (enabled with keys) APIs"""
        available = []
        for name, config in self.api_registry.items():
            if config.get("enabled", False) and config.get("key"):
                available.append(name)
        return available

    def check_rate_limit(self, api_name: str) -> bool:
        """Check if API is within rate limits"""
        if api_name not in self.rate_limits:
            self.rate_limits[api_name] = {
                "calls": 0,
                "reset_time": datetime.now()
            }
        
        rate_info = self.rate_limits[api_name]
        
        # Reset counter if hour has passed
        if datetime.now() - rate_info["reset_time"] > timedelta(hours=1):
            rate_info["calls"] = 0
            rate_info["reset_time"] = datetime.now()
        
        # Get rate limit from config
        api_settings = self.config.get("api_settings", {})
        rate_limits = api_settings.get("rate_limits", {})
        max_calls = rate_limits.get(api_name, {}).get("calls_per_hour", 1000)
        
        return rate_info["calls"] < max_calls

    def increment_rate_limit(self, api_name: str):
        """Increment API call counter"""
        if api_name not in self.rate_limits:
            self.rate_limits[api_name] = {
                "calls": 0,
                "reset_time": datetime.now()
            }
        
        self.rate_limits[api_name]["calls"] += 1

    def get_cache_key(self, api_name: str, request_data: Dict[str, Any]) -> str:
        """Generate cache key for API request"""
        import hashlib
        cache_data = f"{api_name}:{json.dumps(request_data, sort_keys=True)}"
        return hashlib.md5(cache_data.encode()).hexdigest()

    def get_cached_response(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached API response"""
        if cache_key in self.cache:
            if cache_key in self.cache_expiry:
                if datetime.now() < self.cache_expiry[cache_key]:
                    return self.cache[cache_key]
                else:
                    # Cache expired
                    del self.cache[cache_key]
                    del self.cache_expiry[cache_key]
        return None

    def cache_response(self, cache_key: str, response: Dict[str, Any], ttl_seconds: int = 3600):
        """Cache API response"""
        self.cache[cache_key] = response
        self.cache_expiry[cache_key] = datetime.now() + timedelta(seconds=ttl_seconds)

        url = self.get_endpoint(name)
        headers = {"Authorization": f"Bearer {self.get_key(name)}"}
        try:
            res = requests.get(url, headers=headers, timeout=5)
            return {"status": res.status_code, "response": res.text[:200]}
        except Exception as e:
            return {"status": "error", "error": str(e)}