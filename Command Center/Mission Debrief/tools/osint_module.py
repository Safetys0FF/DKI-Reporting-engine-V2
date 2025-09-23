#!/usr/bin/env python3
"""
OSINT Module - Open Source Intelligence Integration
Handles internet lookups, verification, and data gathering for investigations
"""

import os
import json
import logging
import time
from typing import Dict, List, Any, Optional
import requests
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class OSINTEngine:
    """Main OSINT engine for internet-based investigation tools"""
    
    def __init__(self, api_keys_file="api_keys.json", user_profile_manager=None):
        self.api_keys = {}
        self.cache = {}
        self.cache_expiry = {}
        self.user_profile_manager = user_profile_manager
        self.rate_limits = {
            'google_search': {'calls': 0, 'reset_time': datetime.now()},
            'google_maps': {'calls': 0, 'reset_time': datetime.now()},
            'bing_search': {'calls': 0, 'reset_time': datetime.now()}
        }
        
        # Load API keys (from user profile if available, otherwise from file)
        if user_profile_manager and user_profile_manager.is_authenticated():
            self.api_keys = user_profile_manager.get_api_keys_for_osint()
            logger.info("Loaded API keys from user profile")
        else:
            self.load_api_keys(api_keys_file)
        
        # Rate limiting settings (calls per hour)
        self.rate_limits_config = {
            'google_search': 100,  # Free tier limit
            'google_maps': 1000,   # Free tier limit
            'bing_search': 1000    # Free tier limit
        }
        
        logger.info("OSINT Engine initialized")
    
    def load_api_keys(self, api_keys_file):
        """Load API keys from file"""
        try:
            if os.path.exists(api_keys_file):
                with open(api_keys_file, 'r') as f:
                    self.api_keys = json.load(f)
                logger.info(f"Loaded API keys from {api_keys_file}")
            else:
                # Create template API keys file
                template_keys = {
                    "google_search_api_key": "your_google_custom_search_api_key_here",
                    "google_search_engine_id": "your_custom_search_engine_id_here",
                    "google_maps_api_key": "your_google_maps_api_key_here",
                    "bing_search_api_key": "your_bing_search_api_key_here",
                    "public_records_api_key": "your_public_records_api_key_here",
                    "whitepages_api_key": "your_whitepages_api_key_here"
                }
                
                with open(api_keys_file, 'w') as f:
                    json.dump(template_keys, f, indent=2)
                
                logger.warning(f"Created template API keys file: {api_keys_file}")
                logger.warning("Please add your actual API keys to this file")
                
        except Exception as e:
            logger.error(f"Failed to load API keys: {str(e)}")
            self.api_keys = {}
    
    def check_rate_limit(self, service):
        """Check if we're within rate limits for a service"""
        now = datetime.now()
        limit_info = self.rate_limits[service]
        
        # Reset counter if an hour has passed
        if now - limit_info['reset_time'] > timedelta(hours=1):
            limit_info['calls'] = 0
            limit_info['reset_time'] = now
        
        # Check if we're under the limit
        if limit_info['calls'] >= self.rate_limits_config[service]:
            logger.warning(f"Rate limit reached for {service}")
            return False
        
        limit_info['calls'] += 1
        return True
    
    def get_cached_result(self, cache_key):
        """Get cached result if it exists and hasn't expired"""
        if cache_key in self.cache:
            expiry_time = self.cache_expiry.get(cache_key, datetime.now())
            if datetime.now() < expiry_time:
                logger.debug(f"Using cached result for: {cache_key}")
                return self.cache[cache_key]
            else:
                # Remove expired cache
                del self.cache[cache_key]
                del self.cache_expiry[cache_key]
        
        return None
    
    def cache_result(self, cache_key, result, hours=24):
        """Cache a result with expiry time"""
        self.cache[cache_key] = result
        self.cache_expiry[cache_key] = datetime.now() + timedelta(hours=hours)
        logger.debug(f"Cached result for: {cache_key}")
    
    def google_search(self, query, num_results=5):
        """Perform Google search using Custom Search API"""
        cache_key = f"google_search:{query}:{num_results}"
        cached = self.get_cached_result(cache_key)
        if cached:
            return cached
        
        if not self.check_rate_limit('google_search'):
            return {"error": "Rate limit exceeded for Google Search"}
        
        api_key = self.api_keys.get('google_search_api_key')
        search_engine_id = self.api_keys.get('google_search_engine_id')
        
        if not api_key or not search_engine_id or api_key.startswith('your_'):
            return {"error": "Google Search API key not configured"}
        
        try:
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                'key': api_key,
                'cx': search_engine_id,
                'q': query,
                'num': min(num_results, 10)  # Google allows max 10 per request
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            for item in data.get('items', []):
                results.append({
                    'title': item.get('title', ''),
                    'link': item.get('link', ''),
                    'snippet': item.get('snippet', ''),
                    'display_link': item.get('displayLink', '')
                })
            
            result = {
                'query': query,
                'results': results,
                'total_results': data.get('searchInformation', {}).get('totalResults', '0'),
                'search_time': data.get('searchInformation', {}).get('searchTime', '0')
            }
            
            self.cache_result(cache_key, result)
            logger.info(f"Google search completed for: {query}")
            return result
            
        except Exception as e:
            error_result = {"error": f"Google search failed: {str(e)}"}
            logger.error(f"Google search error: {str(e)}")
            return error_result
    
    def verify_address(self, address):
        """Verify address using Google Maps Geocoding API"""
        cache_key = f"address_verify:{address}"
        cached = self.get_cached_result(cache_key)
        if cached:
            return cached
        
        if not self.check_rate_limit('google_maps'):
            return {"error": "Rate limit exceeded for Google Maps"}
        
        api_key = self.api_keys.get('google_maps_api_key')
        if not api_key or api_key.startswith('your_'):
            return {"error": "Google Maps API key not configured"}
        
        try:
            url = "https://maps.googleapis.com/maps/api/geocode/json"
            params = {
                'address': address,
                'key': api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data['status'] == 'OK' and data['results']:
                result_data = data['results'][0]
                
                result = {
                    'address': address,
                    'verified': True,
                    'formatted_address': result_data.get('formatted_address', ''),
                    'location': {
                        'lat': result_data['geometry']['location']['lat'],
                        'lng': result_data['geometry']['location']['lng']
                    },
                    'place_id': result_data.get('place_id', ''),
                    'types': result_data.get('types', [])
                }
            else:
                result = {
                    'address': address,
                    'verified': False,
                    'error': f"Address verification failed: {data.get('status', 'Unknown error')}"
                }
            
            self.cache_result(cache_key, result)
            logger.info(f"Address verification completed for: {address}")
            return result
            
        except Exception as e:
            error_result = {
                'address': address,
                'verified': False,
                'error': f"Address verification error: {str(e)}"
            }
            logger.error(f"Address verification error: {str(e)}")
            return error_result
    
    def reverse_phone_lookup(self, phone_number):
        """Enhanced reverse phone lookup with basic validation and pattern analysis"""
        cache_key = f"phone_lookup:{phone_number}"
        cached = self.get_cached_result(cache_key)
        if cached:
            return cached
        
        import re
        
        # Clean and validate phone number
        clean_number = re.sub(r'[^0-9+]', '', phone_number)
        
        # Basic phone number validation and analysis
        result = {
            'phone_number': phone_number,
            'clean_number': clean_number,
            'verified': False,
            'info': 'Basic phone analysis completed',
            'carrier': 'Unknown',
            'location': 'Unknown',
            'type': 'Unknown',
            'analysis': {}
        }
        
        # Analyze phone number patterns
        if len(clean_number) == 10:  # US domestic
            area_code = clean_number[:3]
            exchange = clean_number[3:6]
            result['type'] = 'Domestic US'
            result['analysis']['area_code'] = area_code
            result['analysis']['exchange'] = exchange
            
            # Basic area code analysis (sample data)
            area_code_info = {
                '212': 'New York, NY',
                '310': 'Los Angeles, CA',
                '312': 'Chicago, IL',
                '415': 'San Francisco, CA',
                '713': 'Houston, TX'
            }
            
            if area_code in area_code_info:
                result['location'] = area_code_info[area_code]
                result['analysis']['region'] = area_code_info[area_code]
            
        elif len(clean_number) == 11 and clean_number.startswith('1'):
            result['type'] = 'US with country code'
            result['analysis']['country_code'] = '1'
            result['analysis']['domestic_number'] = clean_number[1:]
            
        elif clean_number.startswith('+'):
            result['type'] = 'International'
            result['analysis']['international_format'] = True
            
        # Pattern analysis for validity
        if re.match(r'^\+?1?[2-9]\d{2}[2-9]\d{2}\d{4}$', clean_number):
            result['analysis']['format_valid'] = True
        else:
            result['analysis']['format_valid'] = False
            
        # Check for common patterns that might indicate issues
        if re.match(r'^(\d)\1{9}$', clean_number):  # All same digit
            result['analysis']['suspicious'] = 'Repeated digits'
        elif clean_number in ['1234567890', '0987654321']:
            result['analysis']['suspicious'] = 'Sequential digits'
            
        self.cache_result(cache_key, result, hours=168)  # Cache for a week
        logger.info(f"Phone analysis completed for: {phone_number}")
        return result
    
    def business_lookup(self, business_name, location=None):
        """Look up business information"""
        query = business_name
        if location:
            query += f" {location}"
        
        # Use Google search for business information
        search_results = self.google_search(f'"{business_name}" business information')
        
        if 'error' in search_results:
            return search_results
        
        # Also verify location if provided
        location_info = None
        if location:
            location_info = self.verify_address(location)
        
        result = {
            'business_name': business_name,
            'location': location,
            'search_results': search_results['results'][:3],  # Top 3 results
            'location_verified': location_info,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"Business lookup completed for: {business_name}")
        return result
    
    def person_lookup(self, name, location=None, additional_info=None):
        """Look up person information (within legal limits)"""
        query_parts = [f'"{name}"']
        
        if location:
            query_parts.append(location)
        
        if additional_info:
            query_parts.append(additional_info)
        
        query = ' '.join(query_parts)
        
        # Perform search
        search_results = self.google_search(query)
        
        if 'error' in search_results:
            return search_results
        
        result = {
            'name': name,
            'location': location,
            'additional_info': additional_info,
            'search_results': search_results['results'][:5],  # Top 5 results
            'verification_status': 'searched',
            'timestamp': datetime.now().isoformat(),
            'disclaimer': 'Results are from public sources only'
        }
        
        logger.info(f"Person lookup completed for: {name}")
        return result
    
    def comprehensive_verification(self, subject_data):
        """Perform comprehensive verification of subject information"""
        results = {
            'subject_data': subject_data,
            'verification_results': {},
            'timestamp': datetime.now().isoformat(),
            'summary': {'verified_count': 0, 'total_checks': 0}
        }
        
        # Verify name if provided
        if subject_data.get('name'):
            name_result = self.person_lookup(
                subject_data['name'], 
                subject_data.get('address'),
                subject_data.get('employer')
            )
            results['verification_results']['name_verification'] = name_result
            results['summary']['total_checks'] += 1
            if not name_result.get('error'):
                results['summary']['verified_count'] += 1
        
        # Verify address if provided
        if subject_data.get('address'):
            address_result = self.verify_address(subject_data['address'])
            results['verification_results']['address_verification'] = address_result
            results['summary']['total_checks'] += 1
            if address_result.get('verified'):
                results['summary']['verified_count'] += 1
        
        # Verify phone if provided
        if subject_data.get('phone'):
            phone_result = self.reverse_phone_lookup(subject_data['phone'])
            results['verification_results']['phone_verification'] = phone_result
            results['summary']['total_checks'] += 1
        
        # Verify employer if provided
        if subject_data.get('employer'):
            business_result = self.business_lookup(
                subject_data['employer'],
                subject_data.get('employer_address')
            )
            results['verification_results']['employer_verification'] = business_result
            results['summary']['total_checks'] += 1
            if not business_result.get('error'):
                results['summary']['verified_count'] += 1
        
        # Calculate verification score
        if results['summary']['total_checks'] > 0:
            verification_score = (results['summary']['verified_count'] / results['summary']['total_checks']) * 100
            results['summary']['verification_score'] = round(verification_score, 1)
        else:
            results['summary']['verification_score'] = 0
        
        logger.info(f"Comprehensive verification completed. Score: {results['summary']['verification_score']}%")
        return results
    
    def get_system_status(self):
        """Get OSINT system status and API key configuration"""
        status = {
            'osint_engine': 'operational',
            'api_keys_configured': {},
            'rate_limits': self.rate_limits,
            'cache_size': len(self.cache),
            'services_available': []
        }
        
        # Check which API keys are configured
        for key, value in self.api_keys.items():
            if key.startswith('_'):  # Skip instruction/metadata keys
                continue
                
            if value and isinstance(value, str) and not value.startswith('your_'):
                status['api_keys_configured'][key] = 'configured'
                if 'google_search' in key:
                    status['services_available'].append('Google Search')
                elif 'google_maps' in key:
                    status['services_available'].append('Google Maps')
                elif 'bing_search' in key:
                    status['services_available'].append('Bing Search')
            else:
                status['api_keys_configured'][key] = 'not_configured'
        
        return status


# Integration function for the master toolkit
def create_osint_tool():
    """Create OSINT tool instance for integration with master toolkit"""
    return OSINTEngine()


# Example usage and testing
if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Create OSINT engine
    osint = OSINTEngine()
    
    # Test system status
    status = osint.get_system_status()
    print("OSINT System Status:")
    print(json.dumps(status, indent=2))
    
    # Example verification (will only work with configured API keys)
    test_subject = {
        'name': 'John Smith',
        'address': '123 Main St, Anytown, OK 74000',
        'phone': '555-123-4567',
        'employer': 'ABC Company'
    }
    
    print("\nExample comprehensive verification:")
    verification_result = osint.comprehensive_verification(test_subject)
    print(json.dumps(verification_result, indent=2))
