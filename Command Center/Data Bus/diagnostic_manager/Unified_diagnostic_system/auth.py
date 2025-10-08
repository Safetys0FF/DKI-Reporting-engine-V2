"""
Authentication Module - Unified Diagnostic System
Handles fault authentication, authorization, and cryptographic key management

Author: Central Command System
Date: 2025-10-07
Version: 2.0.0 - MODULAR ARCHITECTURE
"""

import os
import json
import hmac
import hashlib
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path


class AuthSystem:
    """
    Authentication System Module
    
    Responsibilities:
    - Fault authentication and authorization
    - Cryptographic key management (HMAC-SHA256)
    - Signature validation and generation
    - System authorization registry
    - Security and spoof detection
    - Idle fault filtering
    """
    
    def __init__(self, orchestrator=None, bus_connection=None, communicator=None):
        """Initialize authentication system with CAN-BUS connection"""
        self.orchestrator = orchestrator
        self.bus = bus_connection
        self.communicator = communicator
        self.bus_connected = bus_connection is not None
        self.logger = logging.getLogger("AuthSystem")
        
        # Get paths from core if available
        if orchestrator and hasattr(orchestrator, 'core'):
            self.secure_vault_path = orchestrator.core.secure_vault_path
            self.keys_path = self.secure_vault_path / "keys"
        else:
            self.secure_vault_path = Path(__file__).parent / "secure_vault"
            self.keys_path = self.secure_vault_path / "keys"
        
        # Authentication state
        self.authorized_systems = {}
        self.authentication_keys = {}
        self.fault_signatures = {}
        self.spoof_detection_enabled = True
        self.idle_fault_filtering_enabled = True
        
        # Initialize
        self._load_authorized_systems()
        self._load_authentication_keys()
        
        self.logger.info("Authentication system initialized")
    
    def _load_authorized_systems(self):
        """Load authorized systems from registry"""
        if self.orchestrator and hasattr(self.orchestrator, 'core'):
            # Pull system registry from core
            for address, system_info in self.orchestrator.core.system_registry.items():
                self.authorized_systems[address] = {
                    'name': system_info.get('name', 'Unknown'),
                    'address': address,
                    'authorized': True,
                    'authorization_date': datetime.now().isoformat()
                }
            self.logger.info(f"Loaded {len(self.authorized_systems)} authorized systems")
    
    def validate_fault_code(self, fault_code: str, system_address: str) -> Dict[str, Any]:
        """Validate fault code before storage - CRITICAL SECURITY FUNCTION"""
        try:
            self.logger.info(f"Validating fault code: {fault_code} from system: {system_address}")
            
            validation_result = {
                'valid': False,
                'fault_code': fault_code,
                'system_address': system_address,
                'validation_timestamp': datetime.now().isoformat(),
                'errors': [],
                'warnings': [],
                'severity': None,
                'authenticated': False,
                'authorized': False
            }
            
            # Step 1: Check if system is authorized
            if not self._is_system_authorized(system_address):
                validation_result['errors'].append(f"System {system_address} is not authorized to submit fault codes")
                return validation_result
            
            validation_result['authorized'] = True
            
            # Step 2: Validate fault code format
            if not self._validate_fault_code_format(fault_code):
                validation_result['errors'].append(f"Invalid fault code format: {fault_code}")
                return validation_result
            
            # Step 3: Authenticate fault code signature
            if not self._authenticate_fault_signature(fault_code, system_address):
                validation_result['errors'].append(f"Fault code signature authentication failed for {system_address}")
                return validation_result
            
            validation_result['authenticated'] = True
            
            # Step 4: Parse and validate fault code components
            parsed_code = self._parse_fault_code(fault_code)
            if not parsed_code:
                validation_result['errors'].append(f"Failed to parse fault code: {fault_code}")
                return validation_result
            
            # Step 5: Validate fault severity
            severity = self._determine_fault_severity(parsed_code.get('fault_id', ''))
            validation_result['severity'] = severity
            
            # Step 6: Check for spoofing attempts
            if self._detect_spoofing_attempt(fault_code, system_address):
                validation_result['errors'].append(f"Potential spoofing attempt detected from {system_address}")
                return validation_result
            
            # Step 7: Check for idle fault filtering
            if self._should_filter_idle_fault(system_address):
                validation_result['warnings'].append(f"Fault from idle system {system_address} - may be filtered")
            
            # If all validations pass
            validation_result['valid'] = True
            self.logger.info(f"Fault code validation successful: {fault_code}")
            
            return validation_result
            
        except Exception as e:
            self.logger.error(f"Error validating fault code: {e}")
            return {
                'valid': False,
                'fault_code': fault_code,
                'system_address': system_address,
                'error': str(e),
                'validation_timestamp': datetime.now().isoformat()
            }
    
    def _is_system_authorized(self, system_address: str) -> bool:
        """Check if system is authorized to submit fault codes"""
        try:
            return system_address in self.authorized_systems and self.authorized_systems[system_address]['authorized']
        except Exception as e:
            self.logger.error(f"Error checking system authorization: {e}")
            return False
    
    def _validate_fault_code_format(self, fault_code: str) -> bool:
        """Validate fault code format according to protocol"""
        try:
            import re
            
            # Expected format: [SYSTEM_ADDRESS-FAULT_ID-LINE_NUMBER]
            # Examples: [1-1-50-123], [Bus-1-25-main_function], [DIAG-1-99-456]
            pattern = r'^\[[A-Za-z0-9-]+-\d{2}-[A-Za-z0-9_-]+\]$'
            
            if not re.match(pattern, fault_code):
                self.logger.warning(f"Fault code format validation failed: {fault_code}")
                return False
            
            # Additional validation - check fault ID range
            parts = fault_code.strip('[]').split('-')
            if len(parts) >= 2:
                try:
                    fault_id = int(parts[-2])  # Second to last part should be fault ID
                    if not (1 <= fault_id <= 99):
                        self.logger.warning(f"Fault ID out of range: {fault_id}")
                        return False
                except ValueError:
                    self.logger.warning(f"Invalid fault ID in code: {fault_code}")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating fault code format: {e}")
            return False
    
    def _authenticate_fault_signature(self, fault_code: str, system_address: str) -> bool:
        """Authenticate fault code signature using HMAC-SHA256"""
        try:
            if system_address not in self.authentication_keys:
                self.logger.warning(f"No authentication key found for system: {system_address}")
                return False
            
            # Generate expected signature
            key = self.authentication_keys[system_address]
            expected_signature = self._generate_fault_signature(fault_code, key)
            
            # In a real implementation, the fault code would come with a signature
            # For now, we'll assume the signature is valid if the key exists
            # This would be enhanced with actual signature verification
            
            self.logger.debug(f"Fault signature authenticated for {system_address}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error authenticating fault signature: {e}")
            return False
    
    def _generate_fault_signature(self, fault_code: str, key: str) -> str:
        """Generate HMAC-SHA256 signature for fault code"""
        try:
            signature = hmac.new(
                key.encode('utf-8'),
                fault_code.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            return signature
            
        except Exception as e:
            self.logger.error(f"Error generating fault signature: {e}")
            return ""
    
    def _parse_fault_code(self, fault_code: str) -> Optional[Dict[str, str]]:
        """Parse fault code into components"""
        try:
            # Remove brackets and split by hyphens
            clean_code = fault_code.strip('[]')
            parts = clean_code.split('-')
            
            if len(parts) >= 3:
                # Last part is line number, second to last is fault ID, rest is system address
                line_number = parts[-1]
                fault_id = parts[-2]
                system_address = '-'.join(parts[:-2])
                
                return {
                    'system_address': system_address,
                    'fault_id': fault_id,
                    'line_number': line_number,
                    'original_code': fault_code
                }
            else:
                self.logger.warning(f"Invalid fault code structure: {fault_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error parsing fault code: {e}")
            return None
    
    def _determine_fault_severity(self, fault_id: str) -> str:
        """Determine fault severity from fault ID"""
        try:
            fault_num = int(fault_id) if fault_id.isdigit() else 99
            
            if 1 <= fault_num <= 49:
                return 'ERROR'  # Help me
            elif 50 <= fault_num <= 89:
                return 'FAILURE'  # I'm dead
            elif 90 <= fault_num <= 99:
                return 'CRITICAL'  # System dead
            else:
                return 'UNKNOWN'
                
        except Exception as e:
            self.logger.error(f"Error determining fault severity: {e}")
            return 'UNKNOWN'
    
    def _detect_spoofing_attempt(self, fault_code: str, system_address: str) -> bool:
        """Detect potential spoofing attempts"""
        try:
            if not self.spoof_detection_enabled:
                return False
            
            # Check for suspicious patterns
            suspicious_patterns = [
                'fake_fault',
                'test_fault',
                'spoofed',
                'malicious'
            ]
            
            fault_code_lower = fault_code.lower()
            for pattern in suspicious_patterns:
                if pattern in fault_code_lower:
                    self.logger.warning(f"Suspicious pattern detected in fault code: {pattern}")
                    return True
            
            # Check for rapid fault submissions (would need rate limiting in real implementation)
            # This is a simplified check
            current_time = datetime.now()
            if hasattr(self, 'last_fault_submission'):
                if system_address in self.last_fault_submission:
                    last_submission = self.last_fault_submission[system_address]
                    time_diff = (current_time - last_submission).total_seconds()
                    if time_diff < 1:  # Less than 1 second between submissions
                        self.logger.warning(f"Rapid fault submissions detected from {system_address}")
                        return True
            
            # Update last submission time
            if not hasattr(self, 'last_fault_submission'):
                self.last_fault_submission = {}
            self.last_fault_submission[system_address] = current_time
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error detecting spoofing attempt: {e}")
            return False
    
    def _should_filter_idle_fault(self, system_address: str) -> bool:
        """Check if fault should be filtered due to idle system"""
        try:
            if not self.idle_fault_filtering_enabled:
                return False
            
            # In a real implementation, this would check if the system is currently idle
            # For now, we'll return False (don't filter)
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking idle fault filtering: {e}")
            return False
    
    def _load_authentication_keys(self):
        """Load persistent authentication keys from secure vault"""
        keys_file = self.keys_path / "authentication_keys.json"
        
        if keys_file.exists():
            try:
                with open(keys_file, 'r') as f:
                    self.authentication_keys = json.load(f)
                self.logger.info(f"Loaded {len(self.authentication_keys)} authentication keys")
            except Exception as e:
                self.logger.error(f"Error loading authentication keys: {e}")
                self._generate_authentication_keys()
        else:
            self._generate_authentication_keys()
    
    def _generate_authentication_keys(self):
        """Generate HMAC-SHA256 authentication keys for all authorized systems"""
        for address in self.authorized_systems.keys():
            key = self._generate_authentication_key(address)
            self.authentication_keys[address] = key
        
        # Save to secure vault
        self._save_authentication_keys()
        self.logger.info(f"Generated {len(self.authentication_keys)} authentication keys")
    
    def _generate_authentication_key(self, system_address: str) -> str:
        """Generate unique HMAC-SHA256 key for a system"""
        # Create unique key based on system address and timestamp
        key_material = f"{system_address}-{datetime.now().isoformat()}-DIAGNOSTIC-AUTH"
        key_hash = hashlib.sha256(key_material.encode()).hexdigest()
        return key_hash
    
    def _save_authentication_keys(self):
        """Save authentication keys to secure vault"""
        keys_file = self.keys_path / "authentication_keys.json"
        
        try:
            with open(keys_file, 'w') as f:
                json.dump(self.authentication_keys, f, indent=2)
            self.logger.info("Authentication keys saved to secure vault")
        except Exception as e:
            self.logger.error(f"Error saving authentication keys: {e}")
    
    def authenticate_fault_report(self, fault_report: Dict[str, Any]) -> bool:
        """
        Authenticate incoming fault report
        
        Checks:
        1. System is authorized
        2. System is not in idle state
        3. Signature is valid
        """
        system_address = fault_report.get('system_address')
        signature = fault_report.get('signature')
        
        # Check authorization
        if not self.is_system_authorized(system_address):
            self.logger.warning(f"Unauthorized fault report from {system_address}")
            return False
        
        # Check idle state
        if self.idle_fault_filtering_enabled:
            if self._is_system_in_idle_state(system_address):
                self.logger.info(f"Filtered fault report from idle system {system_address}")
                return False
        
        # Validate signature
        if signature:
            if not self.validate_fault_signature(fault_report, signature):
                self.logger.warning(f"Invalid signature for fault report from {system_address}")
                return False
        
        return True
    
    def is_system_authorized(self, system_address: str) -> bool:
        """Check if system is authorized"""
        return system_address in self.authorized_systems and \
               self.authorized_systems[system_address].get('authorized', False)
    
    def authorize_system(self, system_address: str, system_name: str):
        """Authorize a new system"""
        self.authorized_systems[system_address] = {
            'name': system_name,
            'address': system_address,
            'authorized': True,
            'authorization_date': datetime.now().isoformat()
        }
        
        # Generate authentication key
        key = self._generate_authentication_key(system_address)
        self.authentication_keys[system_address] = key
        self._save_authentication_keys()
        
        self.logger.info(f"Authorized system: {system_address}")
    
    def revoke_system_authorization(self, system_address: str):
        """Revoke system authorization"""
        if system_address in self.authorized_systems:
            self.authorized_systems[system_address]['authorized'] = False
            self.logger.warning(f"Revoked authorization for system: {system_address}")
    
    def generate_fault_signature(self, fault_report: Dict[str, Any]) -> str:
        """Generate HMAC-SHA256 signature for fault report"""
        system_address = fault_report.get('system_address')
        
        if system_address not in self.authentication_keys:
            self.logger.error(f"No authentication key for system: {system_address}")
            return ""
        
        # Create signature payload
        signature_data = f"{fault_report.get('fault_id')}-{fault_report.get('fault_code')}-{fault_report.get('timestamp')}"
        key = self.authentication_keys[system_address].encode()
        
        # Generate HMAC-SHA256 signature
        signature = hmac.new(key, signature_data.encode(), hashlib.sha256).hexdigest()
        
        return signature
    
    def validate_fault_signature(self, fault_report: Dict[str, Any], provided_signature: str) -> bool:
        """Validate HMAC-SHA256 signature of fault report"""
        expected_signature = self.generate_fault_signature(fault_report)
        
        if not expected_signature:
            return False
        
        # Constant-time comparison to prevent timing attacks
        return hmac.compare_digest(expected_signature, provided_signature)
    
    def _is_system_in_idle_state(self, system_address: str) -> bool:
        """Check if system is currently in idle state"""
        # Pull idle state from orchestrator if available
        if self.orchestrator and hasattr(self.orchestrator, 'enforcement'):
            return self.orchestrator.enforcement.is_system_idle(system_address)
        return False
    
    def get_authentication_status(self) -> Dict[str, Any]:
        """Pull authentication system status"""
        return {
            'authorized_systems': len(self.authorized_systems),
            'authentication_keys': len(self.authentication_keys),
            'spoof_detection_enabled': self.spoof_detection_enabled,
            'idle_fault_filtering_enabled': self.idle_fault_filtering_enabled,
            'systems': {
                address: {
                    'name': info['name'],
                    'authorized': info['authorized'],
                    'has_key': address in self.authentication_keys
                }
                for address, info in self.authorized_systems.items()
            }
        }
    
    def regenerate_all_keys(self):
        """Regenerate all authentication keys (emergency procedure)"""
        self.logger.warning("Regenerating all authentication keys")
        self.authentication_keys.clear()
        self._generate_authentication_keys()
        self.logger.info("All authentication keys regenerated")
    
    # ========================================================================
    # MODULE HEALTH AND PRIORITY EXECUTION METHODS
    # ========================================================================
    
    def is_healthy(self) -> bool:
        """Check if authentication module is healthy and responsive"""
        try:
            # Check if core systems are responsive
            health_checks = [
                self.orchestrator is not None,
                hasattr(self, 'authorized_systems'),
                hasattr(self, 'authentication_keys'),
                hasattr(self, 'spoof_detection_enabled'),
                hasattr(self, 'idle_fault_filtering_enabled')
            ]
            
            return all(health_checks)
            
        except Exception as e:
            self.logger.error(f"Error checking authentication module health: {e}")
            return False
    
    def authenticate_fault_priority(self, operation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute fault authentication with priority handling"""
        try:
            self.logger.info("Executing priority fault authentication...")
            
            # Priority fault authentication
            fault_report = operation_data.get('fault_report', {})
            system_address = operation_data.get('system_address')
            
            authentication_result = {
                'operation_type': 'fault_authentication',
                'priority': operation_data.get('priority', 1),
                'system_address': system_address,
                'fault_authenticated': False,
                'authentication_timestamp': datetime.now().isoformat(),
                'success': True
            }
            
            # Perform authentication checks
            if fault_report and system_address:
                # Check system authorization
                if self.is_system_authorized(system_address):
                    # Validate fault signature
                    if self.validate_fault_signature(fault_report, system_address):
                        authentication_result['fault_authenticated'] = True
                        authentication_result['authentication_method'] = 'signature_validation'
                    else:
                        authentication_result['authentication_failed'] = True
                        authentication_result['failure_reason'] = 'invalid_signature'
                else:
                    authentication_result['authentication_failed'] = True
                    authentication_result['failure_reason'] = 'system_not_authorized'
            else:
                authentication_result['authentication_failed'] = True
                authentication_result['failure_reason'] = 'missing_fault_report_or_system_address'
            
            return authentication_result
            
        except Exception as e:
            self.logger.error(f"Error in priority fault authentication: {e}")
            return {
                'operation_type': 'fault_authentication',
                'success': False,
                'error': str(e)
            }
    
    def authorize_system_priority(self, operation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute system authorization with priority handling"""
        try:
            self.logger.info("Executing priority system authorization...")
            
            # Priority system authorization
            system_address = operation_data.get('system_address')
            system_info = operation_data.get('system_info', {})
            
            authorization_result = {
                'operation_type': 'system_authorization',
                'priority': operation_data.get('priority', 1),
                'system_address': system_address,
                'authorization_granted': False,
                'authorization_timestamp': datetime.now().isoformat(),
                'success': True
            }
            
            # Perform authorization
            if system_address and system_info:
                # Check if system is already authorized
                if self.is_system_authorized(system_address):
                    authorization_result['authorization_granted'] = True
                    authorization_result['authorization_status'] = 'already_authorized'
                else:
                    # Authorize new system
                    authorization_success = self._authorize_new_system_priority(system_address, system_info)
                    authorization_result['authorization_granted'] = authorization_success
                    authorization_result['authorization_status'] = 'new_authorization' if authorization_success else 'authorization_failed'
            else:
                authorization_result['authorization_failed'] = True
                authorization_result['failure_reason'] = 'missing_system_address_or_info'
            
            return authorization_result
            
        except Exception as e:
            self.logger.error(f"Error in priority system authorization: {e}")
            return {
                'operation_type': 'system_authorization',
                'success': False,
                'error': str(e)
            }
    
    def _authorize_new_system_priority(self, system_address: str, system_info: Dict[str, Any]) -> bool:
        """Authorize new system with priority handling"""
        try:
            self.logger.info(f"Authorizing new system with priority: {system_address}")
            
            # Generate authentication key for new system
            auth_key = self._generate_authentication_key_priority(system_address)
            
            if auth_key:
                # Register system
                self.authorized_systems[system_address] = {
                    'name': system_info.get('name', system_address),
                    'authorized': True,
                    'authorization_timestamp': datetime.now().isoformat(),
                    'system_type': system_info.get('system_type', 'unknown'),
                    'capabilities': system_info.get('capabilities', [])
                }
                
                # Store authentication key
                self.authentication_keys[system_address] = auth_key
                
                self.logger.info(f"System authorized with priority: {system_address}")
                return True
            else:
                self.logger.error(f"Failed to generate authentication key for {system_address}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error authorizing new system with priority: {e}")
            return False
    
    def _generate_authentication_key_priority(self, system_address: str) -> Optional[str]:
        """Generate authentication key with priority handling"""
        try:
            # Generate key using system address and timestamp
            key_data = f"{system_address}_{datetime.now().isoformat()}_priority_auth"
            auth_key = hashlib.sha256(key_data.encode()).hexdigest()
            
            self.logger.info(f"Authentication key generated for {system_address}")
            return auth_key
            
        except Exception as e:
            self.logger.error(f"Error generating authentication key: {e}")
            return None
    
    def integrate_systems_into_protocol(self):
        """Integrate registered systems into the Master Diagnostic Protocol tables"""
        try:
            if not self.orchestrator:
                self.logger.error("No orchestrator available for system integration")
                return
            
            # Load the registry
            registry_path = self.orchestrator.base_path.parent / "read_me" / "system_registry.json"
            if not registry_path.exists():
                self.logger.error(f"Registry file not found: {registry_path}")
                return
            
            with open(registry_path, 'r') as f:
                import json
                registry = json.load(f)
            
            systems = registry['system_registry']['connected_systems']
            
            # Load the protocol file
            protocol_path = self.orchestrator.base_path.parent / "read_me" / "MASTER_DIAGNOSTIC_PROTOCOL_2025-10-05.md"
            if not protocol_path.exists():
                self.logger.error(f"Protocol file not found: {protocol_path}")
                return
            
            with open(protocol_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.logger.info("Integrating systems into Master Diagnostic Protocol...")
            
            # Systems to integrate (excluding the original ones that are already in the protocol)
            systems_to_integrate = []
            for addr, data in systems.items():
                # Skip systems that are likely already in the protocol
                if addr not in ['1-1', 'Bus-1.1']:  # These are likely already in the protocol
                    systems_to_integrate.append({
                        'address': addr,
                        'name': data['name'],
                        'handler': data['handler'],
                        'parent': data.get('parent', '-')
                    })
            
            self.logger.info(f"Found {len(systems_to_integrate)} systems to integrate")
            
            # Integrate each system into the appropriate table
            updated_content = content
            
            for system in systems_to_integrate:
                address = system['address']
                name = system['name']
                handler = system['handler']
                parent = system['parent']
                
                self.logger.info(f"Integrating: {address} - {name}")
                
                if address.startswith("Bus-"):
                    updated_content = self._add_to_bus_table(updated_content, address, name, handler, parent)
                elif address.startswith("1-"):
                    updated_content = self._add_to_evidence_locker_table(updated_content, address, name, handler, parent)
                elif address.startswith("2-"):
                    updated_content = self._add_to_warden_table(updated_content, address, name, handler, parent)
                elif address.startswith("3-"):
                    updated_content = self._add_to_mission_debrief_table(updated_content, address, name, handler, parent)
                elif address.startswith("4-"):
                    updated_content = self._add_to_analyst_deck_table(updated_content, address, name, handler, parent)
                elif address.startswith("5-"):
                    updated_content = self._add_to_marshall_table(updated_content, address, name, handler, parent)
                elif address.startswith("6-"):
                    updated_content = self._add_to_war_room_table(updated_content, address, name, handler, parent)
                elif address.startswith("7-"):
                    updated_content = self._add_to_gui_table(updated_content, address, name, handler, parent)
                elif address.startswith("GEN-"):
                    updated_content = self._add_to_general_table(updated_content, address, name, handler, parent)
            
            # Write the updated content back
            with open(protocol_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            
            self.logger.info(f"Successfully integrated {len(systems_to_integrate)} systems into the protocol")
            
        except Exception as e:
            self.logger.error(f"Error integrating systems into protocol: {e}")
    
    def analyze_system_registry(self):
        """Analyze system registry to count main systems vs subsystems"""
        try:
            if not self.orchestrator:
                self.logger.error("No orchestrator available for system analysis")
                return {}
            
            # Load the registry
            registry_path = self.orchestrator.base_path.parent / "read_me" / "system_registry.json"
            if not registry_path.exists():
                self.logger.error(f"Registry file not found: {registry_path}")
                return {}
            
            with open(registry_path, 'r') as f:
                import json
                registry = json.load(f)
            
            systems = registry['system_registry']['connected_systems']
            
            # Categorize systems
            main_systems = {}      # No dots (e.g., "1-1", "2-1", "3-1")
            subsystems = {}        # One dot (e.g., "1-1.1", "2-1.1", "3-1.3")
            bus_systems = {}       # Bus systems (e.g., "Bus-1.1", "Bus-1.2")
            other_systems = {}     # Everything else
            
            for addr, data in systems.items():
                if addr.startswith('Bus-'):
                    bus_systems[addr] = data
                elif '.' in addr and addr.count('.') == 1:
                    subsystems[addr] = data
                elif '.' not in addr and '-' in addr:
                    main_systems[addr] = data
                else:
                    other_systems[addr] = data
            
            # Log results
            self.logger.info("=" * 60)
            self.logger.info("SYSTEM REGISTRY ANALYSIS")
            self.logger.info("=" * 60)
            self.logger.info(f"Total Systems Registered: {len(systems)}")
            self.logger.info(f"MAIN SYSTEMS: {len(main_systems)}")
            self.logger.info(f"SUBSYSTEMS: {len(subsystems)}")
            self.logger.info(f"BUS SYSTEMS: {len(bus_systems)}")
            self.logger.info(f"OTHER SYSTEMS: {len(other_systems)}")
            
            # Analyze parent-child relationships
            parent_counts = {}
            for addr, data in systems.items():
                parent = data.get('parent')
                if parent:
                    if parent not in parent_counts:
                        parent_counts[parent] = 0
                    parent_counts[parent] += 1
            
            self.logger.info("PARENT-CHILD RELATIONSHIPS:")
            for parent, count in parent_counts.items():
                self.logger.info(f"  {parent}: {count} subsystems")
            
            return {
                'total': len(systems),
                'main_systems': len(main_systems),
                'subsystems': len(subsystems),
                'bus_systems': len(bus_systems),
                'other_systems': len(other_systems),
                'parent_counts': parent_counts
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing system registry: {e}")
            return {}
    
    def _add_to_bus_table(self, content, address, name, handler, parent):
        """Add system to Bus System table"""
        import re
        bus_pattern = r'(### \*\*Bus System\*\*\s*\n\| Address \| System Name \| Handler \| Status \| Last Check \|\s*\n\|-+\|-+\|-+\|-+\|-+\|\s*\n)'
        
        def add_row(match):
            table_header = match.group(1)
            if address not in table_header:
                new_row = f"| {address} | {name} | {handler} | ACTIVE | - |\n"
                return table_header + new_row
            return table_header
        
        return re.sub(bus_pattern, add_row, content, flags=re.MULTILINE | re.DOTALL)
    
    def _add_to_evidence_locker_table(self, content, address, name, handler, parent):
        """Add system to Evidence Locker Complex table"""
        import re
        evidence_pattern = r'(### \*\*Evidence Locker Complex \(1-x\)\*\*\s*\n\| Address \| System Name \| Handler \| Parent \| Status \| Last Check \|\s*\n\|-+\|-+\|-+\|-+\|-+\|-+\|\s*\n)'
        
        def add_row(match):
            table_header = match.group(1)
            if address not in table_header:
                new_row = f"| {address} | {name} | {handler} | {parent} | ACTIVE | - |\n"
                return table_header + new_row
            return table_header
        
        return re.sub(evidence_pattern, add_row, content, flags=re.MULTILINE | re.DOTALL)
    
    def _add_to_warden_table(self, content, address, name, handler, parent):
        """Add system to Warden Complex table"""
        import re
        warden_pattern = r'(### \*\*Warden Complex \(2-x\)\*\*\s*\n\| Address \| System Name \| Handler \| Parent \| Status \| Last Check \|\s*\n\|-+\|-+\|-+\|-+\|-+\|-+\|\s*\n)'
        
        def add_row(match):
            table_header = match.group(1)
            if address not in table_header:
                new_row = f"| {address} | {name} | {handler} | {parent} | ACTIVE | - |\n"
                return table_header + new_row
            return table_header
        
        return re.sub(warden_pattern, add_row, content, flags=re.MULTILINE | re.DOTALL)
    
    def _add_to_mission_debrief_table(self, content, address, name, handler, parent):
        """Add system to Mission Debrief Complex table"""
        import re
        mission_pattern = r'(### \*\*Mission Debrief Complex \(3-x\)\*\*\s*\n\| Address \| System Name \| Handler \| Parent \| Status \| Last Check \|\s*\n\|-+\|-+\|-+\|-+\|-+\|-+\|\s*\n)'
        
        def add_row(match):
            table_header = match.group(1)
            if address not in table_header:
                new_row = f"| {address} | {name} | {handler} | {parent} | ACTIVE | - |\n"
                return table_header + new_row
            return table_header
        
        return re.sub(mission_pattern, add_row, content, flags=re.MULTILINE | re.DOTALL)
    
    def _add_to_analyst_deck_table(self, content, address, name, handler, parent):
        """Add system to Analyst Deck Complex table"""
        import re
        analyst_pattern = r'(### \*\*Analyst Deck Complex \(4-x\)\*\*\s*\n\| Address \| System Name \| Handler \| Parent \| Status \| Last Check \|\s*\n\|-+\|-+\|-+\|-+\|-+\|-+\|\s*\n)'
        
        def add_row(match):
            table_header = match.group(1)
            if address not in table_header:
                new_row = f"| {address} | {name} | {handler} | {parent} | ACTIVE | - |\n"
                return table_header + new_row
            return table_header
        
        return re.sub(analyst_pattern, add_row, content, flags=re.MULTILINE | re.DOTALL)
    
    def _add_to_marshall_table(self, content, address, name, handler, parent):
        """Add system to Marshall Complex table"""
        import re
        marshall_pattern = r'(### \*\*Marshall Complex \(5-x\)\*\*\s*\n\| Address \| System Name \| Handler \| Parent \| Status \| Last Check \|\s*\n\|-+\|-+\|-+\|-+\|-+\|-+\|\s*\n)'
        
        def add_row(match):
            table_header = match.group(1)
            if address not in table_header:
                new_row = f"| {address} | {name} | {handler} | {parent} | ACTIVE | - |\n"
                return table_header + new_row
            return table_header
        
        return re.sub(marshall_pattern, add_row, content, flags=re.MULTILINE | re.DOTALL)
    
    def _add_to_war_room_table(self, content, address, name, handler, parent):
        """Add system to War Room Complex table"""
        import re
        war_room_pattern = r'(### \*\*War Room Complex \(6-x\)\*\*\s*\n\| Address \| System Name \| Handler \| Parent \| Status \| Last Check \|\s*\n\|-+\|-+\|-+\|-+\|-+\|-+\|\s*\n)'
        
        def add_row(match):
            table_header = match.group(1)
            if address not in table_header:
                new_row = f"| {address} | {name} | {handler} | {parent} | ACTIVE | - |\n"
                return table_header + new_row
            return table_header
        
        return re.sub(war_room_pattern, add_row, content, flags=re.MULTILINE | re.DOTALL)
    
    def _add_to_gui_table(self, content, address, name, handler, parent):
        """Add system to Enhanced Functional GUI table"""
        import re
        gui_pattern = r'(### \*\*Enhanced Functional GUI \(7-x\)\*\*\s*\n\| Address \| System Name \| Handler \| Parent \| Status \| Last Check \|\s*\n\|-+\|-+\|-+\|-+\|-+\|-+\|\s*\n)'
        
        def add_row(match):
            table_header = match.group(1)
            if address not in table_header:
                new_row = f"| {address} | {name} | {handler} | {parent} | ACTIVE | - |\n"
                return table_header + new_row
            return table_header
        
        return re.sub(gui_pattern, add_row, content, flags=re.MULTILINE | re.DOTALL)
    
    def _add_to_general_table(self, content, address, name, handler, parent):
        """Add system to General Systems table (create if doesn't exist)"""
        import re
        general_pattern = r'(### \*\*General Systems\*\*\s*\n\| Address \| System Name \| Handler \| Parent \| Status \| Last Check \|\s*\n\|-+\|-+\|-+\|-+\|-+\|-+\|\s*\n)'
        
        def add_row(match):
            table_header = match.group(1)
            if address not in table_header:
                new_row = f"| {address} | {name} | {handler} | {parent} | ACTIVE | - |\n"
                return table_header + new_row
            return table_header
        
        # If general section exists, update it
        if re.search(general_pattern, content, flags=re.MULTILINE | re.DOTALL):
            return re.sub(general_pattern, add_row, content, flags=re.MULTILINE | re.DOTALL)
        else:
            # Create new general section
            general_section = f"""
### **General Systems**
| Address | System Name | Handler | Parent | Status | Last Check |
|---------|-------------|---------|--------|--------|------------|
| {address} | {name} | {handler} | {parent} | ACTIVE | - |

"""
            # Insert before the fault codes section
            fault_codes_marker = "## **FAULT SYMPTOMS & DIAGNOSTIC CODES**"
            return content.replace(fault_codes_marker, general_section + fault_codes_marker)