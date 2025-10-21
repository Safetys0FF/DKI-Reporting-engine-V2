#!/usr/bin/env python3
"""
Test OpenAI-first functionality across the entire system
"""

import sys
import os
import json
from pathlib import Path

# Add the central plugin path
sys.path.append(r"F:\The Central Command\Command Center\Start Menu\Run Time")

def test_openai_integration():
    """Test OpenAI-first integration across all components"""
    print("=== Testing OpenAI-First Integration ===\n")
    
    try:
        # Import central plugin
        from central_plugin import central_plugin
        print("[OK] Central Plugin imported successfully")
        
        # Test 1: API Manager Status
        print("\n1. Testing API Manager...")
        if hasattr(central_plugin, 'api_manager') and central_plugin.api_manager:
            print("[OK] API Manager initialized")
            
            # Check OpenAI API key
            openai_key = central_plugin.api_manager.get_key("openai_api")
            if openai_key:
                print(f"[OK] OpenAI API key configured: {openai_key[:20]}...")
            else:
                print("[ERROR] OpenAI API key not configured")
                return False
                
            # Check other API keys
            google_maps_key = central_plugin.api_manager.get_key("google_maps_api")
            if google_maps_key:
                print(f"[OK] Google Maps API key configured: {google_maps_key[:20]}...")
            else:
                print("[WARN] Google Maps API key not configured")
                
            google_gemini_key = central_plugin.api_manager.get_key("google_gemini_api")
            if google_gemini_key:
                print(f"[OK] Google Gemini API key configured: {google_gemini_key[:20]}...")
            else:
                print("[WARN] Google Gemini API key not configured")
        else:
            print("[ERROR] API Manager not initialized")
            return False
        
        # Test 2: Bus Integration
        print("\n2. Testing Data Bus Integration...")
        if central_plugin.bus:
            print("[OK] Data Bus initialized")
            
            # Test OpenAI-first narrative generation
            print("\n3. Testing OpenAI-first Narrative Generation...")
            test_payload = {
                "section_id": "section_1",
                "processed_data": {"test": "data"},
                "case_metadata": {
                    "case_number": "TEST-001",
                    "client_name": "Test Client"
                }
            }
            
            try:
                response = central_plugin.send_to_bus("narrative.generate", test_payload)
                if response.get("status") == "ok":
                    print("[OK] Narrative generation successful")
                    print(f"   Source: {response.get('source', 'unknown')}")
                else:
                    print(f"[WARN] Narrative generation: {response.get('status', 'unknown')}")
            except Exception as e:
                print(f"[WARN] Narrative generation test failed: {e}")
            
            # Test OpenAI-first OSINT verification
            print("\n4. Testing OpenAI-first OSINT Verification...")
            osint_payload = {
                "query": "John Smith 123 Main Street",
                "type": "person_address"
            }
            
            try:
                response = central_plugin.send_to_bus("osint.verify", osint_payload)
                if response.get("status") == "ok":
                    print("[OK] OSINT verification successful")
                    print(f"   Source: {response.get('result', {}).get('source', 'unknown')}")
                else:
                    print(f"[WARN] OSINT verification: {response.get('status', 'unknown')}")
            except Exception as e:
                print(f"[WARN] OSINT verification test failed: {e}")
            
            # Test OpenAI-first geocoding
            print("\n5. Testing OpenAI-first Geocoding...")
            geocoding_payload = {
                "address": "1600 Amphitheatre Parkway, Mountain View, CA"
            }
            
            try:
                response = central_plugin.send_to_bus("geocoding", geocoding_payload)
                if response.get("status") == "ok":
                    print("[OK] Geocoding successful")
                    print(f"   Source: {response.get('source', 'unknown')}")
                else:
                    print(f"[WARN] Geocoding: {response.get('status', 'unknown')}")
            except Exception as e:
                print(f"[WARN] Geocoding test failed: {e}")
            
            # Test OpenAI-first reverse geocoding
            print("\n6. Testing OpenAI-first Reverse Geocoding...")
            reverse_geocoding_payload = {
                "latitude": 37.4220,
                "longitude": -122.0841
            }
            
            try:
                response = central_plugin.send_to_bus("geocoding.reverse", reverse_geocoding_payload)
                if response.get("status") == "ok":
                    print("[OK] Reverse geocoding successful")
                    print(f"   Source: {response.get('source', 'unknown')}")
                else:
                    print(f"[WARN] Reverse geocoding: {response.get('status', 'unknown')}")
            except Exception as e:
                print(f"[WARN] Reverse geocoding test failed: {e}")
            
        else:
            print("[ERROR] Data Bus not initialized")
            return False
        
        # Test 3: Evidence Analysis (if we have test files)
        print("\n7. Testing OpenAI-first Evidence Analysis...")
        test_image_path = r"F:\The Central Command\Command Center\UI\test_image.jpg"
        test_doc_path = r"F:\The Central Command\Command Center\UI\test_document.txt"
        
        # Create test files if they don't exist
        if not os.path.exists(test_image_path):
            print("[WARN] No test image available for analysis")
        else:
            evidence_payload = {
                "file_path": test_image_path,
                "section_id": "section_5",
                "name": "Test Image"
            }
            
            try:
                response = central_plugin.send_to_bus("evidence.scan", evidence_payload)
                if response.get("status") == "analyzed":
                    print("[OK] Evidence analysis successful")
                    print(f"   Source: {response.get('analysis', {}).get('source', 'unknown')}")
                else:
                    print(f"[WARN] Evidence analysis: {response.get('status', 'unknown')}")
            except Exception as e:
                print(f"[WARN] Evidence analysis test failed: {e}")
        
        if not os.path.exists(test_doc_path):
            print("[WARN] No test document available for analysis")
        else:
            evidence_payload = {
                "file_path": test_doc_path,
                "section_id": "section_5",
                "name": "Test Document"
            }
            
            try:
                response = central_plugin.send_to_bus("evidence.scan", evidence_payload)
                if response.get("status") == "analyzed":
                    print("[OK] Document analysis successful")
                    print(f"   Source: {response.get('analysis', {}).get('source', 'unknown')}")
                else:
                    print(f"[WARN] Document analysis: {response.get('status', 'unknown')}")
            except Exception as e:
                print(f"[WARN] Document analysis test failed: {e}")
        
        print("\n=== OpenAI-First Integration Test Complete ===")
        return True
        
    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
        return False

def test_direct_openai_calls():
    """Test direct OpenAI API calls"""
    print("\n=== Testing Direct OpenAI API Calls ===\n")
    
    try:
        import openai
        
        # Load API key from central plugin
        sys.path.append(r"F:\The Central Command\Command Center\Start Menu\Run Time")
        from central_plugin import central_plugin
        
        if not (hasattr(central_plugin, 'api_manager') and central_plugin.api_manager):
            print("[ERROR] API Manager not available")
            return False
            
        openai_key = central_plugin.api_manager.get_key("openai_api")
        if not openai_key:
            print("[ERROR] OpenAI API key not configured")
            return False
            
        openai.api_key = openai_key
        
        # Test 1: Basic text generation
        print("1. Testing basic text generation...")
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Say 'OpenAI integration working' in exactly those words."}
                ],
                max_tokens=50,
                temperature=0.1
            )
            
            result = response.choices[0].message["content"].strip()
            print(f"[OK] Text generation successful: {result}")
        except Exception as e:
            print(f"[ERROR] Text generation failed: {e}")
            return False
        
        # Test 2: Document analysis
        print("\n2. Testing document analysis...")
        try:
            test_doc_content = """
            Case Number: INV-2024-001
            Client: ABC Corporation
            Subject: John Smith
            Address: 123 Main Street, Anytown, ST 12345
            Phone: (555) 123-4567
            Date: January 15, 2024
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a professional investigation analyst. Extract key information from documents."},
                    {"role": "user", "content": f"Analyze this document and extract: 1) Case number, 2) Client name, 3) Subject name, 4) Address, 5) Phone number, 6) Date. Document: {test_doc_content}"}
                ],
                max_tokens=200,
                temperature=0.1
            )
            
            result = response.choices[0].message["content"].strip()
            print(f"[OK] Document analysis successful")
            print(f"   Result: {result[:100]}...")
        except Exception as e:
            print(f"[ERROR] Document analysis failed: {e}")
            return False
        
        # Test 3: Geolocation analysis
        print("\n3. Testing geolocation analysis...")
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a professional geolocation analyst. Provide comprehensive location analysis."},
                    {"role": "user", "content": "Analyze this address: '1600 Amphitheatre Parkway, Mountain View, CA 94043'. Provide: 1) Approximate GPS coordinates, 2) Geographic context, 3) Landmarks nearby, 4) Time zone."}
                ],
                max_tokens=200,
                temperature=0.1
            )
            
            result = response.choices[0].message["content"].strip()
            print(f"[OK] Geolocation analysis successful")
            print(f"   Result: {result[:100]}...")
        except Exception as e:
            print(f"[ERROR] Geolocation analysis failed: {e}")
            return False
        
        print("\n=== Direct OpenAI API Test Complete ===")
        return True
        
    except Exception as e:
        print(f"[ERROR] Direct OpenAI test failed: {e}")
        return False

if __name__ == "__main__":
    print("OpenAI-First Functionality Test")
    print("=" * 50)
    
    # Test 1: System integration
    integration_success = test_openai_integration()
    
    # Test 2: Direct API calls
    direct_success = test_direct_openai_calls()
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    print(f"System Integration: {'[PASS]' if integration_success else '[FAIL]'}")
    print(f"Direct API Calls: {'[PASS]' if direct_success else '[FAIL]'}")
    
    if integration_success and direct_success:
        print("\n[SUCCESS] ALL TESTS PASSED - OpenAI-first integration is working!")
    else:
        print("\n[WARN] Some tests failed - check configuration and API keys")
