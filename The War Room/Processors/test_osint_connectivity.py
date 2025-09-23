#!/usr/bin/env python3
"""
OSINT Engine Connectivity Test
Tests OSINT engine external service connections and functionality
"""

import json
import logging
import sys
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_api_keys() -> Dict[str, str]:
    """Load API keys from api_keys.json"""
    try:
        with open('api_keys.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error("api_keys.json not found")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in api_keys.json: {e}")
        return {}

def test_osint_engine_initialization():
    """Test OSINT engine initialization"""
    try:
        from osint_module import OSINTEngine
        
        # Initialize OSINT engine
        engine = OSINTEngine()
        logger.info("✅ OSINT Engine initialized successfully")
        
        # Check available services
        if hasattr(engine, 'google_maps_client'):
            logger.info("✅ Google Maps client available")
        
        if hasattr(engine, 'google_search_client'):
            logger.info("✅ Google Search client available")
        
        if hasattr(engine, 'bing_search_client'):
            logger.info("✅ Bing Search client available")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ OSINT engine initialization failed: {e}")
        return False

def test_osint_google_maps_integration():
    """Test OSINT Google Maps integration"""
    try:
        from osint_module import OSINTEngine
        
        engine = OSINTEngine()
        
        # Test reverse geocoding
        result = engine.reverse_geocode(40.7128, -74.0060)  # NYC coordinates
        if result:
            logger.info(f"✅ OSINT reverse geocoding: {result}")
            return True
        else:
            logger.warning("⚠️  OSINT reverse geocoding returned no result")
            return False
        
    except Exception as e:
        logger.error(f"❌ OSINT Google Maps integration test failed: {e}")
        return False

def test_osint_google_search_integration():
    """Test OSINT Google Search integration"""
    try:
        from osint_module import OSINTEngine
        
        engine = OSINTEngine()
        
        # Test search functionality
        result = engine.search_web("test search query", max_results=3)
        if result:
            logger.info(f"✅ OSINT web search returned {len(result)} results")
            return True
        else:
            logger.warning("⚠️  OSINT web search returned no results")
            return False
        
    except Exception as e:
        logger.error(f"❌ OSINT Google Search integration test failed: {e}")
        return False

def test_osint_bing_search_integration():
    """Test OSINT Bing Search integration"""
    try:
        from osint_module import OSINTEngine
        
        engine = OSINTEngine()
        
        # Test Bing search functionality
        result = engine.search_bing("test search query", max_results=3)
        if result:
            logger.info(f"✅ OSINT Bing search returned {len(result)} results")
            return True
        else:
            logger.warning("⚠️  OSINT Bing search returned no results")
            return False
        
    except Exception as e:
        logger.error(f"❌ OSINT Bing Search integration test failed: {e}")
        return False

def test_osint_public_records_integration():
    """Test OSINT public records integration"""
    try:
        from osint_module import OSINTEngine
        
        engine = OSINTEngine()
        
        # Test public records lookup
        result = engine.lookup_public_records("John Smith", "123 Main St")
        if result:
            logger.info(f"✅ OSINT public records lookup returned data")
            return True
        else:
            logger.warning("⚠️  OSINT public records lookup returned no data")
            return False
        
    except Exception as e:
        logger.error(f"❌ OSINT public records integration test failed: {e}")
        return False

def test_osint_whitepages_integration():
    """Test OSINT WhitePages integration"""
    try:
        from osint_module import OSINTEngine
        
        engine = OSINTEngine()
        
        # Test WhitePages lookup
        result = engine.lookup_whitepages("555-1234")
        if result:
            logger.info(f"✅ OSINT WhitePages lookup returned data")
            return True
        else:
            logger.warning("⚠️  OSINT WhitePages lookup returned no data")
            return False
        
    except Exception as e:
        logger.error(f"❌ OSINT WhitePages integration test failed: {e}")
        return False

def test_osint_comprehensive_search():
    """Test OSINT comprehensive search functionality"""
    try:
        from osint_module import OSINTEngine
        
        engine = OSINTEngine()
        
        # Test comprehensive search
        result = engine.comprehensive_search("John Smith", "123 Main St", "555-1234")
        if result:
            logger.info(f"✅ OSINT comprehensive search returned data")
            logger.info(f"   Search result keys: {list(result.keys())}")
            return True
        else:
            logger.warning("⚠️  OSINT comprehensive search returned no data")
            return False
        
    except Exception as e:
        logger.error(f"❌ OSINT comprehensive search test failed: {e}")
        return False

def main():
    """Run all OSINT connectivity tests"""
    logger.info("🚀 Starting OSINT Engine Connectivity Tests")
    logger.info("=" * 50)
    
    # Test results
    tests = {
        'OSINT Engine Initialization': test_osint_engine_initialization(),
        'Google Maps Integration': test_osint_google_maps_integration(),
        'Google Search Integration': test_osint_google_search_integration(),
        'Bing Search Integration': test_osint_bing_search_integration(),
        'Public Records Integration': test_osint_public_records_integration(),
        'WhitePages Integration': test_osint_whitepages_integration(),
        'Comprehensive Search': test_osint_comprehensive_search()
    }
    
    # Summary
    logger.info("=" * 50)
    logger.info("📊 TEST SUMMARY")
    logger.info("=" * 50)
    
    passed = 0
    total = len(tests)
    
    for test_name, result in tests.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{test_name}: {status}")
        if result:
            passed += 1
    
    logger.info("=" * 50)
    logger.info(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All OSINT connectivity tests passed!")
        return 0
    else:
        logger.warning(f"⚠️  {total - passed} tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())







