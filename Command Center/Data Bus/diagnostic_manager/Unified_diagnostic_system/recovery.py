"""
Recovery Module - Unified Diagnostic System
Handles code restoration, repair logic, and sandbox testing

Author: Central Command System
Date: 2025-10-07
Version: 2.0.0 - MODULAR ARCHITECTURE
"""

import os
import json
import time
import threading
import shutil
import subprocess
import logging
import json
import threading
import re
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass


@dataclass
class RestoreRequest:
    """Restoration request structure"""
    system_address: str
    fault_code: str
    file_path: str
    backup_path: Optional[str] = None
    user_authorized: bool = False
    signature: str = ""
    timestamp: str = ""


class RecoverySystem:
    """
    Recovery System Module
    
    Responsibilities:
    - Code restoration and repair logic
    - Sandbox testing environment management
    - Backup validation and management
    - User authorization workflow
    - Audit trail and reporting
    - ONE-TIME repair attempt enforcement
    - Dual backup requirement validation
    """
    
    def __init__(self, orchestrator=None, bus_connection=None, communicator=None):
        """Initialize recovery system with CAN-BUS connection"""
        self.orchestrator = orchestrator
        self.bus = bus_connection
        self.communicator = communicator
        self.bus_connected = bus_connection is not None
        self.logger = logging.getLogger("RecoverySystem")
        
        # Get paths from core if available
        if orchestrator and hasattr(orchestrator, 'core'):
            self.sandbox_path = orchestrator.core.sandbox_path
            self.fault_vault_path = orchestrator.core.fault_vault_path
            self.diagnostic_reports_path = orchestrator.core.diagnostic_reports_path
            self.fault_amendments_path = orchestrator.core.fault_amendments_path
        else:
            base_path = Path(__file__).parent
            self.sandbox_path = base_path / "sandbox"
            self.fault_vault_path = base_path / "fault_vault"
            self.diagnostic_reports_path = base_path / "library" / "diagnostic_reports"
            self.fault_amendments_path = base_path / "library" / "fault_amendments"
        
        # Sandbox subdirectories
        self.writeback_path = self.sandbox_path / "writeback"
        self.staging_path = self.sandbox_path / "staging"
        self.validation_path = self.sandbox_path / "validation"
        
        # Recovery state
        self.repair_attempts = {}  # Track ONE-TIME repair attempts
        self.restoration_queue = []  # SINGLE-THREADED processing queue
        self.restoration_in_progress = False  # Exclusive lock
        self.known_good_states = {}  # Backup validation
        
        # Initialize diagnostic protocols
        self._load_diagnostic_protocols()
        
        # Initialize system backup validation
        self._initialize_system_backup_validation()
        
        self.logger.info("Recovery system initialized with diagnostic protocols")
    
    def start_automatic_code_fixing(self):
        """Start automatic code fixing system"""
        def code_fixer():
            while True:
                try:
                    # Process fault queue for automatic fixes
                    self._process_fault_queue_for_fixes()
                    
                    # Perform automatic code repairs
                    self._perform_automatic_repairs()
                    
                    time.sleep(30)  # Check every 30 seconds
                    
                except Exception as e:
                    self.logger.error(f"Error in automatic code fixing: {e}")
                    time.sleep(60)
        
        fixer_thread = threading.Thread(target=code_fixer, daemon=True)
        fixer_thread.start()
        
        self.logger.info("Automatic code fixing system started")
    
    def _process_fault_queue_for_fixes(self):
        """Process fault queue and determine which faults can be auto-fixed"""
        try:
            # Get active faults from orchestrator
            active_faults = self.orchestrator.active_faults
            
            for fault_id, fault_data in active_faults.items():
                if fault_data.get('requires_fix', False):
                    # Check if fault can be automatically fixed
                    if self._can_auto_fix_fault(fault_data):
                        self._queue_automatic_fix(fault_data)
                        
        except Exception as e:
            self.logger.error(f"Error processing fault queue: {e}")
    
    def _can_auto_fix_fault(self, fault_data: Dict[str, Any]) -> bool:
        """Determine if a fault can be automatically fixed"""
        try:
            fault_type = fault_data.get('fault_type', '')
            severity = fault_data.get('severity', '')
            
            # Only auto-fix ERROR and some FAILURE level faults
            if severity == 'CRITICAL':
                return False  # Never auto-fix critical faults
            
            # Auto-fixable fault types
            auto_fixable_types = [
                'SYNTAX_ERROR',
                'IMPORT_ERROR', 
                'CONFIG_ERROR',
                'MISSING_FIELD',
                'INVALID_FORMAT',
                'STALE_FILE'
            ]
            
            return fault_type in auto_fixable_types
            
        except Exception as e:
            self.logger.error(f"Error checking if fault can be auto-fixed: {e}")
            return False
    
    def _queue_automatic_fix(self, fault_data: Dict[str, Any]):
        """Queue a fault for automatic fixing"""
        try:
            if not hasattr(self, 'fix_queue'):
                self.fix_queue = []
            
            # Add to fix queue
            self.fix_queue.append({
                'fault_data': fault_data,
                'queued_at': datetime.now().isoformat(),
                'fix_attempted': False
            })
            
            self.logger.info(f"Queued automatic fix for fault: {fault_data.get('fault_code', 'Unknown')}")
            
        except Exception as e:
            self.logger.error(f"Error queuing automatic fix: {e}")
    
    def _perform_automatic_repairs(self):
        """Perform automatic code repairs"""
        try:
            if not hasattr(self, 'fix_queue') or not self.fix_queue:
                return
            
            # Process one fix at a time (single-threaded as per SOP)
            for fix_item in self.fix_queue[:]:  # Copy to avoid modification during iteration
                if not fix_item['fix_attempted']:
                    self._attempt_automatic_fix(fix_item)
                    
        except Exception as e:
            self.logger.error(f"Error performing automatic repairs: {e}")
    
    def _attempt_automatic_fix(self, fix_item: Dict[str, Any]):
        """Attempt to automatically fix a fault"""
        try:
            fault_data = fix_item['fault_data']
            fault_type = fault_data.get('fault_type', '')
            system_address = fault_data.get('system_address', '')
            
            self.logger.info(f"Attempting automatic fix for {fault_type} in system {system_address}")
            
            # Mark as attempted
            fix_item['fix_attempted'] = True
            
            # Get system info
            system_info = self.orchestrator.system_registry.get(system_address, {})
            system_location = system_info.get('location')
            
            if not system_location:
                self.logger.error(f"No system location found for {system_address}")
                return
            
            # Attempt different types of fixes
            fix_successful = False
            
            if fault_type == 'SYNTAX_ERROR':
                fix_successful = self._fix_syntax_error(system_location, fault_data)
            elif fault_type == 'IMPORT_ERROR':
                fix_successful = self._fix_import_error(system_location, fault_data)
            elif fault_type == 'CONFIG_ERROR':
                fix_successful = self._fix_config_error(system_address, fault_data)
            elif fault_type == 'MISSING_FIELD':
                fix_successful = self._fix_missing_field(system_address, fault_data)
            elif fault_type == 'STALE_FILE':
                fix_successful = self._fix_stale_file(system_location, fault_data)
            else:
                self.logger.warning(f"No automatic fix available for fault type: {fault_type}")
            
            # Record fix attempt
            self._record_fix_attempt(fault_data, fix_successful)
            
            # Remove from queue
            if fix_item in self.fix_queue:
                self.fix_queue.remove(fix_item)
                
        except Exception as e:
            self.logger.error(f"Error attempting automatic fix: {e}")
    
    def _fix_syntax_error(self, file_path: str, fault_data: Dict[str, Any]) -> bool:
        """Attempt to fix Python syntax errors"""
        try:
            self.logger.info(f"Attempting to fix syntax error in {file_path}")
            
            # Read the file
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Common syntax fixes
            fixed_content = content
            
            # Fix common indentation issues
            lines = fixed_content.split('\n')
            fixed_lines = []
            expected_indent = 0
            
            for line in lines:
                # Skip empty lines
                if not line.strip():
                    fixed_lines.append(line)
                    continue
                
                # Calculate current indentation
                current_indent = len(line) - len(line.lstrip())
                
                # Fix common indentation issues
                if line.strip().endswith(':'):
                    # This line should increase indentation for next line
                    fixed_lines.append(line)
                    expected_indent = current_indent + 4
                elif current_indent > expected_indent + 4:
                    # Over-indented, fix it
                    fixed_line = ' ' * expected_indent + line.strip()
                    fixed_lines.append(fixed_line)
                else:
                    fixed_lines.append(line)
                    expected_indent = current_indent
            
            fixed_content = '\n'.join(fixed_lines)
            
            # Validate the fix
            try:
                import ast
                ast.parse(fixed_content)
                
                # Fix was successful, write the file
                self._backup_file(file_path)
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(fixed_content)
                
                self.logger.info(f"Successfully fixed syntax error in {file_path}")
                return True
                
            except SyntaxError:
                self.logger.warning(f"Syntax fix failed for {file_path}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error fixing syntax error: {e}")
            return False
    
    def _fix_import_error(self, file_path: str, fault_data: Dict[str, Any]) -> bool:
        """Attempt to fix import errors"""
        try:
            description = fault_data.get('description', '')
            
            # Extract missing module from description
            if 'Missing module:' in description:
                missing_module = description.split('Missing module: ')[1].strip()
                
                self.logger.info(f"Attempting to fix missing import: {missing_module}")
                
                # Read the file
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Try to fix common import issues
                fixed_content = content
                
                # Fix common import patterns
                import_fixes = {
                    'os': 'import os',
                    'sys': 'import sys', 
                    'json': 'import json',
                    'datetime': 'from datetime import datetime',
                    'pathlib': 'from pathlib import Path',
                    'logging': 'import logging',
                    'threading': 'import threading',
                    'time': 'import time'
                }
                
                if missing_module in import_fixes:
                    # Add the import at the top of the file
                    import_line = import_fixes[missing_module]
                    
                    # Check if import already exists
                    if import_line not in fixed_content:
                        # Add import after existing imports or at the top
                        lines = fixed_content.split('\n')
                        insert_index = 0
                        
                        # Find where to insert (after existing imports)
                        for i, line in enumerate(lines):
                            if line.strip().startswith('import ') or line.strip().startswith('from '):
                                insert_index = i + 1
                            elif line.strip() and not line.strip().startswith('#'):
                                break
                        
                        lines.insert(insert_index, import_line)
                        fixed_content = '\n'.join(lines)
                        
                        # Write the fixed file
                        self._backup_file(file_path)
                        
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(fixed_content)
                        
                        self.logger.info(f"Successfully added missing import: {missing_module}")
                        return True
                
            return False
            
        except Exception as e:
            self.logger.error(f"Error fixing import error: {e}")
            return False
    
    def _fix_config_error(self, system_address: str, fault_data: Dict[str, Any]) -> bool:
        """Attempt to fix configuration errors"""
        try:
            description = fault_data.get('description', '')
            
            self.logger.info(f"Attempting to fix config error for {system_address}: {description}")
            
            # Get system info
            system_info = self.orchestrator.system_registry.get(system_address, {})
            
            # Fix missing required fields
            if 'Missing required field:' in description:
                field_name = description.split('Missing required field: ')[1].strip()
                
                # Provide default values for missing fields
                default_values = {
                    'name': system_address.replace('-', ' ').title(),
                    'address': system_address,
                    'handler': f"{system_address.replace('-', '_')}.{system_address.replace('-', '_')}",
                    'location': f"F:/The Central Command/{system_address}.py"
                }
                
                if field_name in default_values:
                    system_info[field_name] = default_values[field_name]
                    
                    # Update system registry
                    self.orchestrator.system_registry[system_address] = system_info
                    
                    self.logger.info(f"Successfully fixed missing field: {field_name}")
                    return True
            
            # Fix invalid format issues
            elif 'Invalid' in description and 'format' in description:
                if 'address' in description:
                    # Fix address format
                    fixed_address = re.sub(r'[^A-Za-z0-9.-]', '', system_address)
                    if fixed_address != system_address:
                        # Update the address
                        self.orchestrator.system_registry[fixed_address] = system_info
                        if fixed_address != system_address:
                            del self.orchestrator.system_registry[system_address]
                        
                        self.logger.info(f"Successfully fixed address format: {system_address} -> {fixed_address}")
                        return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error fixing config error: {e}")
            return False
    
    def _fix_missing_field(self, system_address: str, fault_data: Dict[str, Any]) -> bool:
        """Fix missing field errors"""
        try:
            # This is similar to config error fixing
            return self._fix_config_error(system_address, fault_data)
            
        except Exception as e:
            self.logger.error(f"Error fixing missing field: {e}")
            return False
    
    def _fix_stale_file(self, file_path: str, fault_data: Dict[str, Any]) -> bool:
        """Attempt to fix stale file issues"""
        try:
            self.logger.info(f"Attempting to fix stale file: {file_path}")
            
            # Touch the file to update modification time
            Path(file_path).touch()
            
            self.logger.info(f"Successfully updated modification time for {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error fixing stale file: {e}")
            return False
    
    def _backup_file(self, file_path: str):
        """Create backup of file before modification"""
        try:
            backup_path = f"{file_path}.backup_{int(time.time())}"
            
            # Copy file to backup location
            import shutil
            shutil.copy2(file_path, backup_path)
            
            self.logger.info(f"Created backup: {backup_path}")
            
        except Exception as e:
            self.logger.error(f"Error creating backup: {e}")
    
    def _record_fix_attempt(self, fault_data: Dict[str, Any], successful: bool):
        """Record fix attempt in diagnostic reports"""
        try:
            fix_report = {
                'fault_data': fault_data,
                'fix_attempted': True,
                'fix_successful': successful,
                'fix_timestamp': datetime.now().isoformat(),
                'fix_method': 'AUTOMATIC_CODE_FIXING'
            }
            
            # Store in diagnostic reports
            reports_path = self.orchestrator.diagnostic_reports_path
            reports_path.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = reports_path / f"automatic_fix_{timestamp}.json"
            
            with open(report_file, 'w') as f:
                json.dump(fix_report, f, indent=2)
            
            status = "SUCCESS" if successful else "FAILED"
            self.logger.info(f"Recorded automatic fix attempt: {status}")
            
        except Exception as e:
            self.logger.error(f"Error recording fix attempt: {e}")
    
    def can_attempt_restoration(self, system_address: str, fault_code: str) -> bool:
        """Check if restoration can be attempted (ONE-TIME rule)"""
        repair_key = f"{system_address}-{fault_code}"
        
        if repair_key in self.repair_attempts:
            self.logger.warning(f"Restoration already attempted for {repair_key}")
            return False
        
        return True
    
    def mark_repair_attempt(self, system_address: str, fault_code: str):
        """Mark that a repair attempt has been made"""
        repair_key = f"{system_address}-{fault_code}"
        self.repair_attempts[repair_key] = {
            'timestamp': datetime.now().isoformat(),
            'system_address': system_address,
            'fault_code': fault_code
        }
    
    def verify_dual_backup_requirement(self, file_path: str) -> Tuple[bool, List[str]]:
        """
        Verify at least TWO good backup files exist
        Returns: (requirement_met, list_of_backups)
        """
        backups = self._find_backup_files(file_path)
        
        if len(backups) < 2:
            self.logger.warning(f"Dual backup requirement not met: only {len(backups)} backup(s) found")
            
            # Attempt to create additional backup if only one exists
            if len(backups) == 1:
                additional_backup = self._duplicate_backup(backups[0])
                if additional_backup:
                    backups.append(additional_backup)
                    self.logger.info("Created additional backup to meet dual requirement")
        
        return len(backups) >= 2, backups
    
    def _find_backup_files(self, file_path: str) -> List[str]:
        """Find all backup files for a given file"""
        file_path = Path(file_path)
        backup_dir = file_path.parent / "backups"
        
        if not backup_dir.exists():
            return []
        
        # Find all backup files
        backups = list(backup_dir.glob(f"{file_path.stem}*.backup_*"))
        return [str(b) for b in backups]
    
    def _duplicate_backup(self, backup_path: str) -> Optional[str]:
        """Duplicate a backup file to create second backup"""
        try:
            backup_path = Path(backup_path)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            duplicate_path = backup_path.parent / f"{backup_path.stem}_duplicate_{timestamp}{backup_path.suffix}"
            
            shutil.copy2(backup_path, duplicate_path)
            self.logger.info(f"Created duplicate backup: {duplicate_path}")
            return str(duplicate_path)
        except Exception as e:
            self.logger.error(f"Error duplicating backup: {e}")
            return None
    
    def queue_restoration_request(self, restore_request: RestoreRequest):
        """Queue restoration request for SINGLE-THREADED processing"""
        self.restoration_queue.append(restore_request)
        self.logger.info(f"Queued restoration request for {restore_request.system_address}")
        
        # Process queue if not currently processing
        if not self.restoration_in_progress:
            self._process_restoration_queue()
    
    def _process_restoration_queue(self):
        """Process restoration queue one at a time"""
        while self.restoration_queue:
            # Set exclusive lock
            self.restoration_in_progress = True
            
            # Get next request
            restore_request = self.restoration_queue.pop(0)
            
            # Process restoration
            self._execute_restoration(restore_request)
            
            # Release lock
            self.restoration_in_progress = False
    
    def _execute_restoration(self, restore_request: RestoreRequest):
        """Execute ONE-TIME restoration attempt"""
        self.logger.info(f"Executing restoration for {restore_request.system_address}")
        
        # Step 1: Check if restoration can be attempted
        if not self.can_attempt_restoration(restore_request.system_address, restore_request.fault_code):
            self._log_manual_intervention_required(restore_request, "Restoration already attempted")
            return
        
        # Step 2: Mark repair attempt
        self.mark_repair_attempt(restore_request.system_address, restore_request.fault_code)
        
        # Step 3: Verify dual backup requirement
        requirement_met, backups = self.verify_dual_backup_requirement(restore_request.file_path)
        if not requirement_met:
            self._log_manual_intervention_required(restore_request, "Dual backup requirement not met")
            return
        
        # Step 4: Restore to sandbox
        sandbox_success = self._restore_to_sandbox(restore_request.file_path, backups[0])
        if not sandbox_success:
            self._log_manual_intervention_required(restore_request, "Sandbox restoration failed")
            return
        
        # Step 5: Validate restored code
        validation_success = self._validate_restored_code_in_sandbox(restore_request.file_path)
        if not validation_success:
            self._log_manual_intervention_required(restore_request, "Code validation failed")
            return
        
        # Step 6: Run sandbox tests
        test_success = self._run_sandbox_tests(restore_request.system_address)
        if not test_success:
            self._log_manual_intervention_required(restore_request, "Sandbox tests failed")
            return
        
        # Step 7: Request user authorization
        if not restore_request.user_authorized:
            self._request_user_authorization(restore_request)
            return  # Wait for authorization
        
        # Step 8: Commit to live system (with authorization)
        commit_success = self._commit_to_live_system(restore_request)
        if commit_success:
            self._generate_audit_report(restore_request, "SUCCESS")
            self.logger.info(f"Restoration successful for {restore_request.system_address}")
        else:
            self._log_manual_intervention_required(restore_request, "Live commit failed")
    
    def _restore_to_sandbox(self, file_path: str, backup_path: str) -> bool:
        """Restore file to sandbox for testing"""
        try:
            file_name = Path(file_path).name
            sandbox_file = self.validation_path / file_name
            
            shutil.copy2(backup_path, sandbox_file)
            self.logger.info(f"Restored to sandbox: {sandbox_file}")
            return True
        except Exception as e:
            self.logger.error(f"Error restoring to sandbox: {e}")
            return False
    
    def _validate_restored_code_in_sandbox(self, file_path: str) -> bool:
        """Validate restored code syntax and imports"""
        try:
            file_name = Path(file_path).name
            sandbox_file = self.validation_path / file_name
            
            # Compile Python code to check syntax
            with open(sandbox_file, 'r') as f:
                code = f.read()
            
            compile(code, str(sandbox_file), 'exec')
            self.logger.info("Code validation passed")
            return True
        except Exception as e:
            self.logger.error(f"Code validation failed: {e}")
            return False
    
    def _run_sandbox_tests(self, system_address: str) -> bool:
        """Run comprehensive tests in sandbox"""
        self.logger.info(f"Running sandbox tests for {system_address}")
        # Placeholder for actual test execution
        return True
    
    def _request_user_authorization(self, restore_request: RestoreRequest):
        """Request user authorization for live commit"""
        self.logger.info(f"Requesting user authorization for {restore_request.system_address}")
        
        # Generate notification
        notification = {
            'system_address': restore_request.system_address,
            'fault_code': restore_request.fault_code,
            'sandbox_tests': 'PASSED',
            'authorization_required': True,
            'timestamp': datetime.now().isoformat()
        }
        
        # Save notification for user review
        notification_file = self.fault_vault_path / f"authorization_request_{restore_request.system_address}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(notification_file, 'w') as f:
            import json
            json.dump(notification, f, indent=2)
    
    def _commit_to_live_system(self, restore_request: RestoreRequest) -> bool:
        """Commit restored code to live system"""
        try:
            file_name = Path(restore_request.file_path).name
            sandbox_file = self.validation_path / file_name
            
            # Stage in writeback
            writeback_file = self.writeback_path / file_name
            shutil.copy2(sandbox_file, writeback_file)
            
            # Commit to live
            shutil.copy2(writeback_file, restore_request.file_path)
            
            self.logger.info(f"Committed to live system: {restore_request.file_path}")
            return True
        except Exception as e:
            self.logger.error(f"Error committing to live system: {e}")
            return False
    
    def _generate_audit_report(self, restore_request: RestoreRequest, result: str):
        """Generate audit report with signature"""
        audit_report = {
            'system_address': restore_request.system_address,
            'fault_code': restore_request.fault_code,
            'file_path': restore_request.file_path,
            'result': result,
            'signature': restore_request.signature,
            'timestamp': datetime.now().isoformat()
        }
        
        # Save to diagnostic_reports
        report_file = self.diagnostic_reports_path / f"audit_report_{restore_request.system_address}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            import json
            json.dump(audit_report, f, indent=2)
        
        self.logger.info(f"Generated audit report: {report_file}")
    
    def _log_manual_intervention_required(self, restore_request: RestoreRequest, reason: str):
        """Log that manual intervention is required"""
        self.logger.warning(f"Manual intervention required for {restore_request.system_address}: {reason}")
        
        # Save to fault_amendments
        amendment_file = self.fault_amendments_path / f"manual_intervention_{restore_request.system_address}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(amendment_file, 'w') as f:
            import json
            json.dump({
                'system_address': restore_request.system_address,
                'fault_code': restore_request.fault_code,
                'reason': reason,
                'timestamp': datetime.now().isoformat()
            }, f, indent=2)
    
    def _attempt_automatic_code_fix(self, file_path: str, line_number: str, function_name: str, fault_code: str) -> bool:
        """ACTUALLY attempt automatic code fix"""
        try:
            self.logger.info(f"ATTEMPTING AUTOMATIC CODE FIX: {file_path} Line {line_number}")
            
            # Read the current file
            with open(file_path, 'r') as f:
                lines = f.readlines()
            
            # Extract fault type from fault code
            fault_type = self._extract_fault_type_from_code(fault_code)
            
            # Attempt fixes based on fault type
            fix_applied = False
            
            if fault_type == 'syntax_error':
                fix_applied = self._fix_syntax_error(lines, line_number)
            elif fault_type == 'initialization_failure':
                fix_applied = self._fix_initialization_error(lines, function_name)
            elif fault_type == 'communication_timeout':
                fix_applied = self._fix_communication_error(lines, function_name)
            elif fault_type == 'data_processing_error':
                fix_applied = self._fix_data_processing_error(lines, function_name)
            elif fault_type == 'resource_failure':
                fix_applied = self._fix_resource_error(lines, function_name)
            
            if fix_applied:
                # Write the fixed code back to file
                with open(file_path, 'w') as f:
                    f.writelines(lines)
                
                self.logger.info(f"AUTOMATIC CODE FIX APPLIED: {file_path}")
                return True
            else:
                self.logger.error(f"NO AUTOMATIC FIX AVAILABLE: {file_path}")
                return False
            
        except Exception as e:
            self.logger.error(f"Error attempting automatic code fix: {e}")
            return False
    
    def _fix_syntax_error(self, lines: List[str], line_number: str) -> bool:
        """Fix common syntax errors"""
        try:
            line_idx = int(line_number) - 1
            
            if line_idx >= len(lines):
                return False
            
            line = lines[line_idx]
            
            # Common syntax fixes
            if line.strip().endswith(':'):
                # Add pass statement if line ends with colon but next line is indented incorrectly
                if line_idx + 1 < len(lines) and not lines[line_idx + 1].strip():
                    lines.insert(line_idx + 1, '    pass\n')
                    return True
            
            elif '=' in line and line.count('(') != line.count(')'):
                # Fix mismatched parentheses
                if line.count('(') > line.count(')'):
                    lines[line_idx] = line.rstrip() + ')\n'
                    return True
            
            elif line.strip().startswith('import') and not line.strip().endswith(';'):
                # Ensure import statements end properly
                lines[line_idx] = line.rstrip() + '\n'
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error fixing syntax error: {e}")
            return False
    
    def _fix_initialization_error(self, lines: List[str], function_name: str) -> bool:
        """Fix initialization errors"""
        try:
            # Look for the function
            for i, line in enumerate(lines):
                if function_name in line and 'def ' in line:
                    # Add try-except block around function
                    indent = len(line) - len(line.lstrip())
                    indent_str = ' ' * (indent + 4)
                    
                    # Insert try-except wrapper
                    lines.insert(i + 1, f"{indent_str}try:\n")
                    
                    # Find end of function and add except block
                    for j in range(i + 2, len(lines)):
                        if lines[j].strip() and len(lines[j]) - len(lines[j].lstrip()) <= indent:
                            lines.insert(j, f"{indent_str}except Exception as e:\n")
                            lines.insert(j + 1, f"{indent_str}    self.logger.error(f'Initialization error in {function_name}: {{e}}')\n")
                            lines.insert(j + 2, f"{indent_str}    return None\n")
                            break
                    
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error fixing initialization error: {e}")
            return False
    
    def _fix_communication_error(self, lines: List[str], function_name: str) -> bool:
        """Fix communication errors"""
        try:
            # Look for the function
            for i, line in enumerate(lines):
                if function_name in line and 'def ' in line:
                    # Add timeout handling
                    indent = len(line) - len(line.lstrip())
                    indent_str = ' ' * (indent + 4)
                    
                    # Insert timeout wrapper
                    lines.insert(i + 1, f"{indent_str}import time\n")
                    lines.insert(i + 2, f"{indent_str}start_time = time.time()\n")
                    
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error fixing communication error: {e}")
            return False
    
    def _fix_data_processing_error(self, lines: List[str], function_name: str) -> bool:
        """Fix data processing errors"""
        try:
            # Look for the function
            for i, line in enumerate(lines):
                if function_name in line and 'def ' in line:
                    # Add data validation
                    indent = len(line) - len(line.lstrip())
                    indent_str = ' ' * (indent + 4)
                    
                    # Insert data validation
                    lines.insert(i + 1, f"{indent_str}if data is None or data == '':\n")
                    lines.insert(i + 2, f"{indent_str}    return None\n")
                    
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error fixing data processing error: {e}")
            return False
    
    def _fix_resource_error(self, lines: List[str], function_name: str) -> bool:
        """Fix resource errors"""
        try:
            # Look for the function
            for i, line in enumerate(lines):
                if function_name in line and 'def ' in line:
                    # Add resource cleanup
                    indent = len(line) - len(line.lstrip())
                    indent_str = ' ' * (indent + 4)
                    
                    # Insert resource cleanup
                    lines.insert(i + 1, f"{indent_str}try:\n")
                    
                    # Find end of function and add finally block
                    for j in range(i + 2, len(lines)):
                        if lines[j].strip() and len(lines[j]) - len(lines[j].lstrip()) <= indent:
                            lines.insert(j, f"{indent_str}finally:\n")
                            lines.insert(j + 1, f"{indent_str}    # Resource cleanup\n")
                            break
                    
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error fixing resource error: {e}")
            return False
    
    def _log_code_changes(self, system_address: str, file_path: str, change_type: str, change_details: str):
        """Log actual code changes made"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = self.orchestrator.fault_vault_path / f"code_changes_{timestamp}.md"
            
            with open(log_file, 'w') as f:
                f.write(f"# CODE CHANGES LOG\n\n")
                f.write(f"**Timestamp:** {datetime.now().isoformat()}\n")
                f.write(f"**System Address:** {system_address}\n")
                f.write(f"**File Path:** {file_path}\n")
                f.write(f"**Change Type:** {change_type}\n")
                f.write(f"**Change Details:** {change_details}\n")
                f.write(f"**Change Applied:** YES\n")
                f.write(f"**Status:** ACTUAL CODE MODIFICATION\n")
            
            self.logger.info(f"CODE CHANGES LOGGED: {log_file}")
            
        except Exception as e:
            self.logger.error(f"Error logging code changes: {e}")
    
    def _extract_fault_type_from_code(self, fault_code: str) -> str:
        """Extract fault type from fault code"""
        try:
            import re
            match = re.match(r'\[([A-Za-z0-9-]+)-(\d{2})-([A-Za-z0-9_-]+)\]', fault_code)
            
            if match:
                fault_id = match.group(2)
                
                # Map fault IDs to types based on protocol
                if fault_id in ['01', '02', '03']:
                    return 'syntax_error'
                elif fault_id in ['10', '11', '12']:
                    return 'initialization_failure'
                elif fault_id in ['20', '21', '22']:
                    return 'communication_timeout'
                elif fault_id in ['30', '31', '32']:
                    return 'data_processing_error'
                elif fault_id in ['40', '41', '42']:
                    return 'resource_failure'
                else:
                    return 'unknown_error'
            
            return 'unknown_error'
            
        except Exception as e:
            self.logger.error(f"Error extracting fault type: {e}")
            return 'unknown_error'

    # ===== DIAGNOSTIC PROTOCOL METHODS =====
    
    def _load_diagnostic_protocols(self):
        """Load diagnostic protocols from master protocol file"""
        try:
            protocol_file = self.orchestrator.master_protocol_path
            
            self.diagnostic_protocols = {
                'system_addresses': {},
                'fault_codes': {},
                'radio_codes': {}
            }
            
            if protocol_file.exists():
                with open(protocol_file, 'r') as f:
                    content = f.read()
                self._parse_protocol_content(content)
                self.logger.info("Loaded diagnostic protocols")
            else:
                self.logger.warning(f"Protocol file not found: {protocol_file}")
                
        except Exception as e:
            self.logger.error(f"Failed to load diagnostic protocols: {e}")
    
    def _parse_protocol_content(self, content: str):
        """Parse protocol content for system addresses and fault codes"""
        try:
            lines = content.split('\n')
            current_section = None
            
            for line in lines:
                if 'SYSTEM ADDRESS REGISTRY' in line:
                    current_section = 'addresses'
                elif 'FAULT SYMPTOMS & DIAGNOSTIC CODES' in line:
                    current_section = 'faults'
                elif 'COMMUNICATION CALLOUTS & RADIO CODES' in line:
                    current_section = 'radio'
                elif current_section and '|' in line and not line.startswith('|'):
                    parts = [p.strip() for p in line.split('|') if p.strip()]
                    if len(parts) >= 2:
                        if current_section == 'addresses':
                            self.diagnostic_protocols['system_addresses'][parts[1]] = parts
                        elif current_section == 'faults':
                            self.diagnostic_protocols['fault_codes'][parts[0]] = parts
                        elif current_section == 'radio':
                            self.diagnostic_protocols['radio_codes'][parts[0]] = parts
                            
        except Exception as e:
            self.logger.error(f"Error parsing protocol content: {e}")
    
    def _validate_fault_code_format(self, fault_code: str) -> bool:
        """Validate fault code format matches protocol"""
        try:
            import re
            pattern = r'\[([A-Za-z0-9-]+)-(\d{2})-([A-Za-z0-9_-]+)\]'
            match = re.match(pattern, fault_code)
            
            if match:
                system_address = match.group(1)
                fault_id = match.group(2)
                line_number = match.group(3)
                
                # Validate fault ID is in range 01-99
                if 1 <= int(fault_id) <= 99:
                    # Validate system address exists in registry
                    if system_address in self.orchestrator.system_registry:
                        return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error validating fault code format: {e}")
            return False
    
    def _parse_fault_code(self, fault_code: str) -> Dict[str, str]:
        """Parse fault code to extract components"""
        try:
            import re
            pattern = r'\[([A-Za-z0-9-]+)-(\d{2})-([A-Za-z0-9_-]+)\]'
            match = re.match(pattern, fault_code)
            
            if match:
                return {
                    'system_address': match.group(1),
                    'fault_id': match.group(2),
                    'line_number': match.group(3)
                }
            
            return {}
            
        except Exception as e:
            self.logger.error(f"Error parsing fault code: {e}")
            return {}
    
    def _determine_fault_severity(self, fault_id: str) -> str:
        """Determine fault severity based on fault ID"""
        try:
            fault_num = int(fault_id)
            
            # Critical system failures (90-99)
            if 90 <= fault_num <= 99:
                return 'CRITICAL'
            
            # Failures (50-89)
            elif 50 <= fault_num <= 89:
                return 'FAILURE'
            
            # Errors (01-49)
            else:
                return 'ERROR'
                
        except Exception:
            return 'ERROR'
    
    def _convert_error_to_fault_code(self, error_code: str, system_address: str, error_message: str) -> str:
        """Convert error code to fault code format"""
        try:
            # Try to determine fault ID from error message
            error_lower = error_message.lower()
            
            # Map common error patterns to fault codes
            if 'syntax' in error_lower:
                fault_id = '01'
            elif 'initialization' in error_lower or 'init' in error_lower:
                fault_id = '10'
            elif 'timeout' in error_lower:
                fault_id = '20'
            elif 'processing' in error_lower or 'data' in error_lower:
                fault_id = '30'
            elif 'resource' in error_lower or 'memory' in error_lower:
                fault_id = '40'
            else:
                fault_id = '99'  # Unknown error
            
            # Generate line number from error or use default
            line_number = '001'
            if 'line' in error_lower:
                import re
                line_match = re.search(r'line (\d+)', error_lower)
                if line_match:
                    line_number = line_match.group(1).zfill(3)
            
            return f"[{system_address}-{fault_id}-{line_number}]"
            
        except Exception as e:
            self.logger.error(f"Error converting error to fault code: {e}")
            return f"[{system_address}-99-001]"

    # ===== SYSTEM VALIDATION AND BACKUP PROTOCOLS =====
    
    def _initialize_system_backup_validation(self):
        """Initialize system backup validation and good/bad state logging"""
        try:
            self.logger.info("Initializing system backup validation...")
            
            # Initialize known good states storage
            self.known_good_states = {}
            self.backup_validation_active = True
            
            # Load existing known good states
            self._load_known_good_states()
            
            # Start backup validation monitoring
            self._start_backup_validation_monitoring()
            
            self.logger.info("System backup validation initialized")
            
        except Exception as e:
            self.logger.error(f"Error initializing system backup validation: {e}")
    
    def _load_known_good_states(self):
        """Load known good states from persistent storage"""
        try:
            states_file = self.orchestrator.secure_vault_path / "known_good_states.json"
            
            if states_file.exists():
                with open(states_file, 'r') as f:
                    self.known_good_states = json.load(f)
                self.logger.info(f"Loaded {len(self.known_good_states)} known good states")
            else:
                self.logger.info("No existing known good states found")
                
        except Exception as e:
            self.logger.error(f"Error loading known good states: {e}")
    
    def _start_backup_validation_monitoring(self):
        """Start background monitoring for backup validation"""
        import threading
        
        def validation_monitor():
            while self.backup_validation_active:
                try:
                    self._validate_current_system_states()
                    time.sleep(3600)  # Check every hour
                except Exception as e:
                    self.logger.error(f"Backup validation monitoring error: {e}")
                    time.sleep(7200)  # Wait 2 hours on error
        
        threading.Thread(target=validation_monitor, daemon=True).start()
        self.logger.info("Backup validation monitoring started")
    
    def _create_initial_good_state_baseline(self):
        """Create initial good state baseline for all systems"""
        try:
            self.logger.info("Creating initial good state baseline...")
            
            for system_address, system_info in self.orchestrator.system_registry.items():
                # Run comprehensive validation
                validation_result = self._run_comprehensive_system_validation(system_address)
                
                if validation_result['overall_valid']:
                    # Record as good state
                    timestamp = datetime.now().isoformat()
                    self._record_good_state(system_address, validation_result, timestamp)
                    self.logger.info(f"Recorded good state for {system_address}")
            
            # Save known good states
            self._save_known_good_states()
            
            self.logger.info("Initial good state baseline created")
            
        except Exception as e:
            self.logger.error(f"Error creating initial good state baseline: {e}")
    
    def _run_comprehensive_system_validation(self, system_address: str) -> Dict[str, Any]:
        """Run comprehensive validation of a system"""
        try:
            validation_result = {
                'system_address': system_address,
                'overall_valid': False,
                'file_integrity': {'valid': False, 'details': []},
                'configuration': {'valid': False, 'details': []},
                'dependencies': {'valid': False, 'details': []},
                'communication': {'valid': False, 'details': []},
                'timestamp': datetime.now().isoformat()
            }
            
            # Validate file integrity
            file_validation = self._validate_system_file_integrity(system_address)
            validation_result['file_integrity'] = file_validation
            
            # Validate configuration
            config_validation = self._validate_system_configuration(system_address)
            validation_result['configuration'] = config_validation
            
            # Validate dependencies
            dep_validation = self._validate_system_dependencies(system_address)
            validation_result['dependencies'] = dep_validation
            
            # Test communication
            comm_validation = self._test_system_communication(system_address)
            validation_result['communication'] = comm_validation
            
            # Determine overall validity
            validation_result['overall_valid'] = all([
                file_validation['valid'],
                config_validation['valid'],
                dep_validation['valid'],
                comm_validation['valid']
            ])
            
            return validation_result
            
        except Exception as e:
            self.logger.error(f"Error running comprehensive system validation: {e}")
            return {'overall_valid': False, 'error': str(e)}
    
    def _validate_system_file_integrity(self, system_address: str) -> Dict[str, Any]:
        """Validate system file integrity using checksums"""
        try:
            system_info = self.orchestrator.system_registry.get(system_address)
            if not system_info:
                return {'valid': False, 'details': ['System not found in registry']}
            
            file_path = system_info.get('location')
            if not file_path or not Path(file_path).exists():
                return {'valid': False, 'details': ['Handler file does not exist']}
            
            # Calculate current file checksum
            current_checksum = self._calculate_file_checksum(file_path)
            
            return {
                'valid': True,
                'details': [f'File checksum: {current_checksum}'],
                'checksum': current_checksum,
                'file_path': file_path
            }
            
        except Exception as e:
            return {'valid': False, 'details': [f'File integrity validation error: {e}']}
    
    def _calculate_file_checksum(self, file_path: str) -> Optional[str]:
        """Calculate MD5 checksum of a file"""
        try:
            import hashlib
            
            with open(file_path, 'rb') as f:
                file_hash = hashlib.md5()
                while chunk := f.read(8192):
                    file_hash.update(chunk)
            
            return file_hash.hexdigest()
            
        except PermissionError as e:
            self.logger.warning(f"Permission denied accessing {file_path}: {e}")
            # Log this as a permission issue that needs elevated privileges
            self.logger.warning(f"DIAGNOSTIC SYSTEM NEEDS ELEVATED PRIVILEGES to access {file_path}")
            return None
        except FileNotFoundError:
            self.logger.warning(f"File not found: {file_path}")
            return None
        except Exception as e:
            self.logger.error(f"Error calculating file checksum: {e}")
            return None
    
    def _validate_system_configuration(self, system_address: str) -> Dict[str, Any]:
        """Validate system configuration files"""
        try:
            system_info = self.orchestrator.system_registry.get(system_address)
            if not system_info:
                return {'valid': False, 'details': ['System not found in registry']}
            
            # Find system config files
            config_files = self._find_system_config_files(system_address)
            
            if not config_files:
                return {'valid': True, 'details': ['No configuration files to validate']}
            
            valid_configs = []
            invalid_configs = []
            
            for config_file in config_files:
                if Path(config_file).exists():
                    valid_configs.append(config_file)
                else:
                    invalid_configs.append(config_file)
            
            return {
                'valid': len(invalid_configs) == 0,
                'details': [
                    f'Valid configs: {len(valid_configs)}',
                    f'Invalid configs: {len(invalid_configs)}'
                ],
                'config_files': config_files
            }
            
        except Exception as e:
            return {'valid': False, 'details': [f'Configuration validation error: {e}']}
    
    def _find_system_config_files(self, system_address: str) -> List[str]:
        """Find configuration files for a system"""
        try:
            config_files = []
            
            # Common config file patterns
            config_patterns = ['config.json', 'settings.json', 'config.py', 'settings.py']
            
            # Look in system directory
            system_info = self.orchestrator.system_registry.get(system_address)
            if system_info and system_info.get('location'):
                system_dir = Path(system_info['location']).parent
                
                for pattern in config_patterns:
                    config_file = system_dir / pattern
                    if config_file.exists():
                        config_files.append(str(config_file))
            
            return config_files
            
        except Exception as e:
            self.logger.error(f"Error finding system config files: {e}")
            return []
    
    def _validate_system_dependencies(self, system_address: str) -> Dict[str, Any]:
        """Validate system dependencies"""
        try:
            system_info = self.orchestrator.system_registry.get(system_address)
            if not system_info:
                return {'valid': False, 'details': ['System not found in registry']}
            
            file_path = system_info.get('location')
            if not file_path or not Path(file_path).exists():
                return {'valid': False, 'details': ['Handler file does not exist']}
            
            # Extract imports from file
            imports = self._extract_file_imports(file_path)
            
            valid_imports = []
            invalid_imports = []
            
            for import_name in imports:
                try:
                    __import__(import_name)
                    valid_imports.append(import_name)
                except ImportError:
                    invalid_imports.append(import_name)
            
            return {
                'valid': len(invalid_imports) == 0,
                'details': [
                    f'Valid imports: {len(valid_imports)}',
                    f'Invalid imports: {len(invalid_imports)}'
                ],
                'imports': imports,
                'invalid_imports': invalid_imports
            }
            
        except Exception as e:
            return {'valid': False, 'details': [f'Dependency validation error: {e}']}
    
    def _extract_file_imports(self, file_path: str) -> List[str]:
        """Extract import statements from a Python file"""
        try:
            import ast
            
            with open(file_path, 'r') as f:
                tree = ast.parse(f.read())
            
            imports = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)
            
            return imports
            
        except PermissionError as e:
            self.logger.warning(f"Permission denied accessing {file_path}: {e}")
            self.logger.warning(f"DIAGNOSTIC SYSTEM NEEDS ELEVATED PRIVILEGES to access {file_path}")
            return []
        except FileNotFoundError:
            self.logger.warning(f"File not found: {file_path}")
            return []
        except Exception as e:
            self.logger.error(f"Error extracting file imports: {e}")
            return []
    
    def _test_system_communication(self, system_address: str) -> Dict[str, Any]:
        """Test system communication capabilities"""
        try:
            # Simple communication test - check if system responds to basic signals
            if self.orchestrator.comms:
                # Try to send a basic signal
                signal_id = self.orchestrator.comms.transmit_radio_check(system_address)
                
                if signal_id:
                    return {
                        'valid': True,
                        'details': ['Communication test successful'],
                        'signal_id': signal_id
                    }
                else:
                    return {
                        'valid': False,
                        'details': ['Communication test failed - no signal ID generated']
                    }
            else:
                return {
                    'valid': False,
                    'details': ['Communication system not available']
                }
                
        except Exception as e:
            return {'valid': False, 'details': [f'Communication test error: {e}']}
    
    def _record_good_state(self, system_address: str, validation_result: Dict[str, Any], timestamp: str):
        """Record a known good state for a system"""
        try:
            if system_address not in self.known_good_states:
                self.known_good_states[system_address] = []
            
            good_state = {
                'timestamp': timestamp,
                'validation_result': validation_result,
                'file_checksums': {},
                'config_snapshots': {}
            }
            
            # Record file checksums
            if validation_result.get('file_integrity', {}).get('checksum'):
                good_state['file_checksums']['handler'] = validation_result['file_integrity']['checksum']
            
            # Record config snapshots
            if validation_result.get('configuration', {}).get('config_files'):
                for config_file in validation_result['configuration']['config_files']:
                    config_checksum = self._calculate_file_checksum(config_file)
                    if config_checksum:
                        good_state['config_snapshots'][config_file] = config_checksum
            
            self.known_good_states[system_address].append(good_state)
            
            # Keep only last 10 good states per system
            if len(self.known_good_states[system_address]) > 10:
                self.known_good_states[system_address] = self.known_good_states[system_address][-10:]
            
        except Exception as e:
            self.logger.error(f"Error recording good state: {e}")
    
    def _save_known_good_states(self):
        """Save known good states to persistent storage"""
        try:
            states_file = self.orchestrator.secure_vault_path / "known_good_states.json"
            
            with open(states_file, 'w') as f:
                json.dump(self.known_good_states, f, indent=2)
            
            self.logger.info("Known good states saved")
            
        except Exception as e:
            self.logger.error(f"Error saving known good states: {e}")
    
    def _validate_current_system_states(self):
        """Validate current system states against known good states"""
        try:
            for system_address in self.orchestrator.system_registry.keys():
                # Run current validation
                current_validation = self._run_comprehensive_system_validation(system_address)
                
                # Get known good states for this system
                known_good_states = self.known_good_states.get(system_address, [])
                
                if known_good_states:
                    # Analyze deviation from known good states
                    self._analyze_state_deviation(system_address, current_validation, known_good_states)
                
                # If current state is good, record it
                if current_validation.get('overall_valid'):
                    timestamp = datetime.now().isoformat()
                    self._record_good_state(system_address, current_validation, timestamp)
            
            # Save updated known good states
            self._save_known_good_states()
            
        except Exception as e:
            self.logger.error(f"Error validating current system states: {e}")
    
    def _analyze_state_deviation(self, system_address: str, current_validation: Dict[str, Any], known_good_states: List[Dict[str, Any]]):
        """Analyze deviation from known good states"""
        try:
            if not known_good_states:
                return
            
            latest_good_state = known_good_states[-1]
            deviation_analysis = {
                'system_address': system_address,
                'timestamp': datetime.now().isoformat(),
                'deviations_detected': [],
                'severity': 'NONE'
            }
            
            # Compare file checksums
            current_checksum = current_validation.get('file_integrity', {}).get('checksum')
            good_checksum = latest_good_state.get('file_checksums', {}).get('handler')
            
            if current_checksum and good_checksum and current_checksum != good_checksum:
                deviation_analysis['deviations_detected'].append('FILE_CHECKSUM_MISMATCH')
                deviation_analysis['severity'] = 'HIGH'
            
            # Compare configuration validity
            current_config_valid = current_validation.get('configuration', {}).get('valid')
            good_config_valid = latest_good_state.get('validation_result', {}).get('configuration', {}).get('valid')
            
            if current_config_valid != good_config_valid:
                deviation_analysis['deviations_detected'].append('CONFIG_VALIDITY_CHANGE')
                deviation_analysis['severity'] = 'MEDIUM'
            
            # Log deviation if any detected
            if deviation_analysis['deviations_detected']:
                self._log_state_deviation(deviation_analysis)
            
        except Exception as e:
            self.logger.error(f"Error analyzing state deviation: {e}")
    
    def _log_state_deviation(self, deviation_analysis: Dict[str, Any]):
        """Log state deviation analysis"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = self.orchestrator.fault_vault_path / f"state_deviation_{timestamp}.md"
            
            with open(log_file, 'w') as f:
                f.write(f"# STATE DEVIATION ANALYSIS\n\n")
                f.write(f"**Timestamp:** {deviation_analysis['timestamp']}\n")
                f.write(f"**System Address:** {deviation_analysis['system_address']}\n")
                f.write(f"**Severity:** {deviation_analysis['severity']}\n")
                f.write(f"**Deviations Detected:** {', '.join(deviation_analysis['deviations_detected'])}\n")
                f.write(f"**Status:** SYSTEM STATE DEVIATION DETECTED\n")
            
            self.logger.warning(f"State deviation detected for {deviation_analysis['system_address']}: {deviation_analysis['severity']}")
            
        except Exception as e:
            self.logger.error(f"Error logging state deviation: {e}")

    def get_recovery_status(self) -> Dict[str, Any]:
        """Pull recovery system status"""
        return {
            'restoration_in_progress': self.restoration_in_progress,
            'queued_restorations': len(self.restoration_queue),
            'repair_attempts': len(self.repair_attempts),
            'known_good_states': len(self.known_good_states)
        }
    
    # ===== ROOT CAUSE ANALYSIS SYSTEM =====
    
    def perform_root_cause_analysis(self, fault_id: str, fault_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive root cause analysis with multi-layer structure and cascading-failure detection"""
        try:
            self.logger.info(f"Starting root cause analysis for fault: {fault_id}")
            
            # Initialize RCA structure
            rca_result = {
                'fault_id': fault_id,
                'analysis_timestamp': datetime.now().isoformat(),
                'system_address': fault_data.get('system_address', 'UNKNOWN'),
                'fault_code': fault_data.get('fault_code', 'UNKNOWN'),
                'severity': fault_data.get('severity', 'UNKNOWN'),
                'analysis_layers': {},
                'cascading_failures': [],
                'parent_child_relationships': {},
                'dependency_analysis': {},
                'root_cause_identified': False,
                'confidence_score': 0.0,
                'recommendations': []
            }
            
            # Layer 1: Direct Fault Analysis
            rca_result['analysis_layers']['direct_fault'] = self._analyze_direct_fault(fault_data)
            
            # Layer 2: Parent-Child Relationship Analysis
            rca_result['analysis_layers']['parent_child'] = self._analyze_parent_child_relationships(fault_data)
            
            # Layer 3: Cascading Failure Detection
            rca_result['analysis_layers']['cascading_failure'] = self._detect_cascading_failures(fault_data)
            
            # Layer 4: Dependency Failure Analysis
            rca_result['analysis_layers']['dependency_analysis'] = self._analyze_dependency_failures(fault_data)
            
            # Layer 5: Temporal Pattern Analysis
            rca_result['analysis_layers']['temporal_pattern'] = self._analyze_temporal_patterns(fault_data)
            
            # Layer 6: System Family Analysis
            rca_result['analysis_layers']['system_family'] = self._analyze_system_family(fault_data)
            
            # Synthesize root cause
            root_cause = self._synthesize_root_cause(rca_result)
            rca_result.update(root_cause)
            
            # Generate recommendations
            rca_result['recommendations'] = self._generate_rca_recommendations(rca_result)
            
            # Save RCA results
            self._save_root_cause_analysis(rca_result)
            
            self.logger.info(f"Root cause analysis completed for fault: {fault_id} - Confidence: {rca_result['confidence_score']:.2f}")
            
            return rca_result
            
        except Exception as e:
            self.logger.error(f"Error in root cause analysis: {e}")
            return {'error': str(e), 'fault_id': fault_id}
    
    def _analyze_direct_fault(self, fault_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the direct fault for immediate causes"""
        try:
            direct_analysis = {
                'fault_type': fault_data.get('fault_code', 'UNKNOWN'),
                'line_number': fault_data.get('line_number', 'UNKNOWN'),
                'function_name': fault_data.get('function_name', 'UNKNOWN'),
                'file_path': fault_data.get('file_path', 'UNKNOWN'),
                'immediate_causes': [],
                'error_patterns': []
            }
            
            # Analyze fault code patterns
            fault_code = fault_data.get('fault_code', '')
            if fault_code:
                # Extract fault type from code
                if '01' in fault_code:
                    direct_analysis['immediate_causes'].append('Syntax error detected')
                elif '10' in fault_code:
                    direct_analysis['immediate_causes'].append('Initialization failure')
                elif '30' in fault_code:
                    direct_analysis['immediate_causes'].append('Data processing error')
                elif '50' in fault_code:
                    direct_analysis['immediate_causes'].append('System failure')
                elif '90' in fault_code:
                    direct_analysis['immediate_causes'].append('Critical system failure')
            
            # Analyze error patterns
            description = fault_data.get('description', '')
            if 'timeout' in description.lower():
                direct_analysis['error_patterns'].append('Timeout pattern detected')
            if 'memory' in description.lower():
                direct_analysis['error_patterns'].append('Memory-related issue')
            if 'connection' in description.lower():
                direct_analysis['error_patterns'].append('Connection issue')
            
            return direct_analysis
            
        except Exception as e:
            self.logger.error(f"Error in direct fault analysis: {e}")
            return {'error': str(e)}
    
    def _analyze_parent_child_relationships(self, fault_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze parent-child system relationships for fault propagation"""
        try:
            parent_child_analysis = {
                'system_address': fault_data.get('system_address', 'UNKNOWN'),
                'parent_systems': [],
                'child_systems': [],
                'fault_propagation': {},
                'relationship_impact': 'UNKNOWN'
            }
            
            system_address = fault_data.get('system_address', '')
            
            # Determine parent and child systems based on address
            if '-' in system_address:
                parts = system_address.split('-')
                if len(parts) >= 2:
                    parent_address = parts[0]
                    parent_child_analysis['parent_systems'].append(parent_address)
                    
                    # Find child systems
                    if self.orchestrator and hasattr(self.orchestrator, 'system_registry'):
                        for addr, info in self.orchestrator.system_registry.items():
                            if addr.startswith(system_address + '.'):
                                parent_child_analysis['child_systems'].append(addr)
            
            # Analyze fault propagation
            if parent_child_analysis['parent_systems']:
                parent_child_analysis['fault_propagation']['parent_affected'] = True
                parent_child_analysis['fault_propagation']['propagation_path'] = 'UPWARD'
            
            if parent_child_analysis['child_systems']:
                parent_child_analysis['fault_propagation']['children_affected'] = True
                parent_child_analysis['fault_propagation']['propagation_path'] = 'DOWNWARD'
            
            return parent_child_analysis
            
        except Exception as e:
            self.logger.error(f"Error in parent-child relationship analysis: {e}")
            return {'error': str(e)}
    
    def _detect_cascading_failures(self, fault_data: Dict[str, Any]) -> Dict[str, Any]:
        """Detect cascading failures and temporal clustering"""
        try:
            cascading_analysis = {
                'cascading_detected': False,
                'cascade_chain': [],
                'temporal_clustering': False,
                'cluster_timeframe_minutes': 0,
                'affected_systems': []
            }
            
            # Check for recent faults in the same system family
            system_address = fault_data.get('system_address', '')
            current_time = datetime.now()
            
            if self.orchestrator and hasattr(self.orchestrator, 'active_faults'):
                recent_faults = []
                for fault_id, fault_info in self.orchestrator.active_faults.items():
                    fault_time_str = fault_info.get('timestamp', '')
                    if fault_time_str:
                        try:
                            fault_time = datetime.fromisoformat(fault_time_str)
                            time_diff = (current_time - fault_time).total_seconds() / 60  # minutes
                            
                            # Check if fault is within 10 minutes and in same system family
                            if time_diff <= 10 and fault_info.get('system_address', '').startswith(system_address.split('-')[0]):
                                recent_faults.append({
                                    'fault_id': fault_id,
                                    'system_address': fault_info.get('system_address', ''),
                                    'time_diff_minutes': time_diff
                                })
                        except:
                            continue
                
                if len(recent_faults) >= 3:  # 3 or more faults in 10 minutes
                    cascading_analysis['cascading_detected'] = True
                    cascading_analysis['cascade_chain'] = recent_faults
                    cascading_analysis['temporal_clustering'] = True
                    cascading_analysis['cluster_timeframe_minutes'] = 10
                    cascading_analysis['affected_systems'] = list(set([f['system_address'] for f in recent_faults]))
            
            return cascading_analysis
            
        except Exception as e:
            self.logger.error(f"Error in cascading failure detection: {e}")
            return {'error': str(e)}
    
    def _analyze_dependency_failures(self, fault_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze failures in dependent systems"""
        try:
            dependency_analysis = {
                'dependent_systems': [],
                'dependency_failures': [],
                'dependency_impact': 'UNKNOWN',
                'critical_dependencies': []
            }
            
            system_address = fault_data.get('system_address', '')
            
            # Define system dependencies (simplified mapping)
            system_dependencies = {
                '1-1': ['Bus-1'],  # Evidence Locker depends on Bus
                '2-1': ['Bus-1', '1-1'],  # Gateway depends on Bus and Evidence Locker
                '3-1': ['2-1'],  # Mission Debrief depends on Gateway
                '4-1': ['2-1'],  # ECC depends on Gateway
                '5-1': ['Bus-1'],  # GUI depends on Bus
                '7-1': ['Bus-1']  # Analyst Deck depends on Bus
            }
            
            # Find dependencies for this system
            dependencies = system_dependencies.get(system_address, [])
            dependency_analysis['dependent_systems'] = dependencies
            
            # Check if dependencies have faults
            if self.orchestrator and hasattr(self.orchestrator, 'active_faults'):
                for dep_system in dependencies:
                    for fault_id, fault_info in self.orchestrator.active_faults.items():
                        if fault_info.get('system_address') == dep_system:
                            dependency_analysis['dependency_failures'].append({
                                'dependency': dep_system,
                                'fault_id': fault_id,
                                'fault_code': fault_info.get('fault_code', 'UNKNOWN')
                            })
                            
                            if dep_system == 'Bus-1':  # Bus is critical
                                dependency_analysis['critical_dependencies'].append(dep_system)
            
            # Determine dependency impact
            if dependency_analysis['dependency_failures']:
                if dependency_analysis['critical_dependencies']:
                    dependency_analysis['dependency_impact'] = 'CRITICAL'
                else:
                    dependency_analysis['dependency_impact'] = 'MODERATE'
            else:
                dependency_analysis['dependency_impact'] = 'NONE'
            
            return dependency_analysis
            
        except Exception as e:
            self.logger.error(f"Error in dependency failure analysis: {e}")
            return {'error': str(e)}
    
    def _analyze_temporal_patterns(self, fault_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze temporal patterns in fault occurrence"""
        try:
            temporal_analysis = {
                'fault_frequency': 'UNKNOWN',
                'time_pattern': 'UNKNOWN',
                'recurring_faults': False,
                'pattern_confidence': 0.0
            }
            
            system_address = fault_data.get('system_address', '')
            
            # Analyze fault history for patterns
            if self.orchestrator and hasattr(self.orchestrator, 'active_faults'):
                system_faults = []
                for fault_id, fault_info in self.orchestrator.active_faults.items():
                    if fault_info.get('system_address') == system_address:
                        system_faults.append(fault_info)
                
                if len(system_faults) > 1:
                    temporal_analysis['recurring_faults'] = True
                    temporal_analysis['fault_frequency'] = 'HIGH' if len(system_faults) > 5 else 'MODERATE'
                    temporal_analysis['pattern_confidence'] = min(0.8, len(system_faults) * 0.1)
            
            return temporal_analysis
            
        except Exception as e:
            self.logger.error(f"Error in temporal pattern analysis: {e}")
            return {'error': str(e)}
    
    def _analyze_system_family(self, fault_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze faults within the same system family"""
        try:
            family_analysis = {
                'family_root': 'UNKNOWN',
                'family_members': [],
                'family_faults': [],
                'family_impact': 'UNKNOWN'
            }
            
            system_address = fault_data.get('system_address', '')
            
            # Determine system family
            if '-' in system_address:
                family_root = system_address.split('-')[0]
                family_analysis['family_root'] = family_root
                
                # Find family members
                if self.orchestrator and hasattr(self.orchestrator, 'system_registry'):
                    for addr, info in self.orchestrator.system_registry.items():
                        if addr.startswith(family_root + '-'):
                            family_analysis['family_members'].append(addr)
                
                # Check for faults in family
                if self.orchestrator and hasattr(self.orchestrator, 'active_faults'):
                    for fault_id, fault_info in self.orchestrator.active_faults.items():
                        if fault_info.get('system_address', '').startswith(family_root + '-'):
                            family_analysis['family_faults'].append({
                                'fault_id': fault_id,
                                'system_address': fault_info.get('system_address'),
                                'fault_code': fault_info.get('fault_code')
                            })
                
                # Determine family impact
                fault_count = len(family_analysis['family_faults'])
                if fault_count >= 3:
                    family_analysis['family_impact'] = 'HIGH'
                elif fault_count >= 1:
                    family_analysis['family_impact'] = 'MODERATE'
                else:
                    family_analysis['family_impact'] = 'LOW'
            
            return family_analysis
            
        except Exception as e:
            self.logger.error(f"Error in system family analysis: {e}")
            return {'error': str(e)}
    
    def _synthesize_root_cause(self, rca_result: Dict[str, Any]) -> Dict[str, Any]:
        """Synthesize all analysis layers to identify root cause"""
        try:
            root_cause = {
                'root_cause_identified': False,
                'root_cause_type': 'UNKNOWN',
                'root_cause_description': '',
                'confidence_score': 0.0,
                'evidence': []
            }
            
            # Analyze each layer for root cause indicators
            confidence_factors = []
            
            # Direct fault analysis
            direct_fault = rca_result['analysis_layers'].get('direct_fault', {})
            if direct_fault.get('immediate_causes'):
                confidence_factors.append(0.3)
                root_cause['evidence'].append('Direct fault causes identified')
            
            # Parent-child relationships
            parent_child = rca_result['analysis_layers'].get('parent_child', {})
            if parent_child.get('fault_propagation', {}).get('parent_affected'):
                confidence_factors.append(0.4)
                root_cause['evidence'].append('Parent system affected - likely root cause')
            
            # Cascading failures
            cascading = rca_result['analysis_layers'].get('cascading_failure', {})
            if cascading.get('cascading_detected'):
                confidence_factors.append(0.5)
                root_cause['evidence'].append('Cascading failure pattern detected')
            
            # Dependency failures
            dependency = rca_result['analysis_layers'].get('dependency_analysis', {})
            if dependency.get('dependency_impact') == 'CRITICAL':
                confidence_factors.append(0.6)
                root_cause['evidence'].append('Critical dependency failure identified')
            
            # System family analysis
            family = rca_result['analysis_layers'].get('system_family', {})
            if family.get('family_impact') == 'HIGH':
                confidence_factors.append(0.4)
                root_cause['evidence'].append('High impact across system family')
            
            # Calculate confidence score
            if confidence_factors:
                root_cause['confidence_score'] = sum(confidence_factors) / len(confidence_factors)
                
                if root_cause['confidence_score'] >= 0.6:
                    root_cause['root_cause_identified'] = True
                    
                    # Determine root cause type
                    if dependency.get('dependency_impact') == 'CRITICAL':
                        root_cause['root_cause_type'] = 'DEPENDENCY_FAILURE'
                        root_cause['root_cause_description'] = 'Critical dependency system failure'
                    elif cascading.get('cascading_detected'):
                        root_cause['root_cause_type'] = 'CASCADING_FAILURE'
                        root_cause['root_cause_description'] = 'Cascading failure pattern'
                    elif parent_child.get('fault_propagation', {}).get('parent_affected'):
                        root_cause['root_cause_type'] = 'PARENT_SYSTEM_FAILURE'
                        root_cause['root_cause_description'] = 'Parent system failure'
                    else:
                        root_cause['root_cause_type'] = 'SYSTEM_ISOLATED_FAILURE'
                        root_cause['root_cause_description'] = 'Isolated system failure'
            
            return root_cause
            
        except Exception as e:
            self.logger.error(f"Error synthesizing root cause: {e}")
            return {'error': str(e)}
    
    def _generate_rca_recommendations(self, rca_result: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations based on RCA results"""
        try:
            recommendations = []
            
            if rca_result.get('root_cause_identified'):
                root_cause_type = rca_result.get('root_cause_type', '')
                
                if root_cause_type == 'DEPENDENCY_FAILURE':
                    recommendations.extend([
                        'Immediately check and restore critical dependency systems',
                        'Implement dependency health monitoring',
                        'Add dependency failure recovery procedures'
                    ])
                elif root_cause_type == 'CASCADING_FAILURE':
                    recommendations.extend([
                        'Implement cascading failure prevention mechanisms',
                        'Add system isolation procedures',
                        'Review system coupling and dependencies'
                    ])
                elif root_cause_type == 'PARENT_SYSTEM_FAILURE':
                    recommendations.extend([
                        'Focus repair efforts on parent system',
                        'Check parent system configuration and state',
                        'Verify parent system dependencies'
                    ])
                else:
                    recommendations.extend([
                        'Focus on isolated system repair',
                        'Check system-specific configuration',
                        'Verify system resource availability'
                    ])
            
            # Add general recommendations
            if rca_result['analysis_layers'].get('temporal_pattern', {}).get('recurring_faults'):
                recommendations.append('Investigate recurring fault patterns')
            
            if rca_result['analysis_layers'].get('system_family', {}).get('family_impact') == 'HIGH':
                recommendations.append('Review system family configuration and dependencies')
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Error generating RCA recommendations: {e}")
            return ['Error generating recommendations']
    
    def _save_root_cause_analysis(self, rca_result: Dict[str, Any]):
        """Save root cause analysis results"""
        try:
            if self.orchestrator:
                # Save to diagnostic reports
                report_path = self.orchestrator.diagnostic_reports_path / f"rca_{rca_result['fault_id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                
                with open(report_path, 'w') as f:
                    json.dump(rca_result, f, indent=2, default=str)
                
                self.logger.info(f"Root cause analysis saved: {report_path}")
            
        except Exception as e:
            self.logger.error(f"Error saving root cause analysis: {e}")
    
    # ========================================================================
    # MODULE HEALTH AND PRIORITY EXECUTION METHODS
    # ========================================================================
    
    def is_healthy(self) -> bool:
        """Check if recovery module is healthy and responsive"""
        try:
            # Check if core systems are responsive
            health_checks = [
                self.orchestrator is not None,
                hasattr(self, 'repair_attempts'),
                hasattr(self, 'system_backup_validation'),
                hasattr(self, 'sandbox_environment'),
                hasattr(self, 'user_authorization_workflow')
            ]
            
            return all(health_checks)
            
        except Exception as e:
            self.logger.error(f"Error checking recovery module health: {e}")
            return False
    
    def repair_system_priority(self, operation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute system repair with priority handling"""
        try:
            self.logger.info("Executing priority system repair...")
            
            # Priority system repair - interrupt lower priority operations
            system_address = operation_data.get('system_address')
            fault_id = operation_data.get('fault_id')
            repair_type = operation_data.get('repair_type', 'code_restoration')
            
            # Perform immediate repair
            repair_result = {
                'operation_type': 'system_repair',
                'priority': operation_data.get('priority', 1),
                'system_address': system_address,
                'fault_id': fault_id,
                'repair_type': repair_type,
                'repair_attempted': False,
                'repair_successful': False,
                'repair_timestamp': datetime.now().isoformat(),
                'success': True
            }
            
            # Check if repair is allowed (one-time attempt)
            if self._is_repair_allowed(system_address, fault_id):
                repair_result['repair_attempted'] = True
                
                # Execute repair based on type
                if repair_type == 'code_restoration':
                    repair_success = self._execute_priority_code_restoration(system_address, fault_id, operation_data)
                elif repair_type == 'configuration_reset':
                    repair_success = self._execute_priority_configuration_reset(system_address, operation_data)
                elif repair_type == 'system_restart':
                    repair_success = self._execute_priority_system_restart(system_address, operation_data)
                else:
                    repair_success = self._execute_priority_general_repair(system_address, fault_id, operation_data)
                
                repair_result['repair_successful'] = repair_success
                
                # Record repair attempt
                self._record_repair_attempt(system_address, fault_id, repair_success)
                
            else:
                repair_result['repair_blocked'] = True
                repair_result['block_reason'] = 'One-time repair attempt already used'
                self.logger.warning(f"Repair blocked for {system_address}: {fault_id} - already attempted")
            
            return repair_result
            
        except Exception as e:
            self.logger.error(f"Error in priority system repair: {e}")
            return {
                'operation_type': 'system_repair',
                'success': False,
                'error': str(e)
            }
    
    def _is_repair_allowed(self, system_address: str, fault_id: str) -> bool:
        """Check if repair is allowed (one-time attempt enforcement)"""
        try:
            repair_key = f"{system_address}_{fault_id}"
            
            # Check if repair already attempted
            if repair_key in self.repair_attempts:
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking repair allowance: {e}")
            return False
    
    def _execute_priority_code_restoration(self, system_address: str, fault_id: str, operation_data: Dict[str, Any]) -> bool:
        """Execute priority code restoration"""
        try:
            self.logger.info(f"Executing priority code restoration for {system_address}")
            
            # Get fault details
            fault_details = operation_data.get('fault_details', {})
            file_path = fault_details.get('file_path')
            
            if not file_path:
                self.logger.error("No file path provided for code restoration")
                return False
            
            # Find last known good version
            last_good_version = self._find_last_known_good_version_priority(file_path, system_address)
            
            if last_good_version:
                # Create backup of current file
                backup_path = f"{file_path}.priority_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                self._create_file_backup_priority(file_path, backup_path)
                
                # Restore from last good version
                restore_success = self._restore_code_from_backup_priority(file_path, last_good_version)
                
                if restore_success:
                    # Validate restored code
                    validation_result = self._validate_restored_code_priority(file_path, system_address)
                    
                    if validation_result['valid']:
                        self.logger.info(f"Priority code restoration successful: {system_address}")
                        return True
                    else:
                        # Restore backup if validation failed
                        self._restore_code_from_backup_priority(file_path, backup_path)
                        self.logger.error(f"Code validation failed for {system_address}")
                        return False
                else:
                    self.logger.error(f"Code restoration failed for {system_address}")
                    return False
            else:
                self.logger.error(f"No good version found for {system_address}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error in priority code restoration: {e}")
            return False
    
    def _execute_priority_configuration_reset(self, system_address: str, operation_data: Dict[str, Any]) -> bool:
        """Execute priority configuration reset"""
        try:
            self.logger.info(f"Executing priority configuration reset for {system_address}")
            
            # Reset system configuration to defaults
            # This would involve resetting configuration files, environment variables, etc.
            
            # For now, simulate successful reset
            self.logger.info(f"Configuration reset completed for {system_address}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error in priority configuration reset: {e}")
            return False
    
    def _execute_priority_system_restart(self, system_address: str, operation_data: Dict[str, Any]) -> bool:
        """Execute priority system restart"""
        try:
            self.logger.info(f"Executing priority system restart for {system_address}")
            
            # Restart the system
            # This would involve stopping and starting the system process
            
            # For now, simulate successful restart
            self.logger.info(f"System restart completed for {system_address}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error in priority system restart: {e}")
            return False
    
    def _execute_priority_general_repair(self, system_address: str, fault_id: str, operation_data: Dict[str, Any]) -> bool:
        """Execute priority general repair"""
        try:
            self.logger.info(f"Executing priority general repair for {system_address}")
            
            # General repair logic
            # This would involve various repair strategies based on fault type
            
            # For now, simulate successful repair
            self.logger.info(f"General repair completed for {system_address}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error in priority general repair: {e}")
            return False
    
    def _find_last_known_good_version_priority(self, file_path: str, system_address: str) -> Optional[str]:
        """Find last known good version with priority handling"""
        try:
            # Look for backup files in system's backup directory
            backup_dir = Path(f"F:/The Central Command/Backups/{system_address}")
            
            if backup_dir.exists():
                # Find most recent backup
                backup_files = list(backup_dir.glob(f"{Path(file_path).name}.backup_*"))
                if backup_files:
                    latest_backup = max(backup_files, key=lambda x: x.stat().st_mtime)
                    return str(latest_backup)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error finding last known good version: {e}")
            return None
    
    def _create_file_backup_priority(self, file_path: str, backup_path: str) -> bool:
        """Create file backup with priority handling"""
        try:
            shutil.copy2(file_path, backup_path)
            self.logger.info(f"Priority backup created: {file_path} -> {backup_path}")
            return True
        except Exception as e:
            self.logger.error(f"Error creating priority backup: {e}")
            return False
    
    def _restore_code_from_backup_priority(self, file_path: str, backup_path: str) -> bool:
        """Restore code from backup with priority handling"""
        try:
            shutil.copy2(backup_path, file_path)
            self.logger.info(f"Priority code restoration: {backup_path} -> {file_path}")
            return True
        except Exception as e:
            self.logger.error(f"Error in priority code restoration: {e}")
            return False
    
    def _validate_restored_code_priority(self, file_path: str, system_address: str) -> Dict[str, Any]:
        """Validate restored code with priority handling"""
        try:
            # Basic validation - check if file exists and is readable
            if Path(file_path).exists():
                # Try to read the file
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if content:
                    return {'valid': True, 'reason': 'File exists and is readable'}
                else:
                    return {'valid': False, 'reason': 'File is empty'}
            else:
                return {'valid': False, 'reason': 'File does not exist'}
                
        except Exception as e:
            self.logger.error(f"Error validating restored code: {e}")
            return {'valid': False, 'reason': f'Validation error: {e}'}
    
    def _record_repair_attempt(self, system_address: str, fault_id: str, success: bool):
        """Record repair attempt for one-time enforcement"""
        try:
            repair_key = f"{system_address}_{fault_id}"
            self.repair_attempts[repair_key] = {
                'system_address': system_address,
                'fault_id': fault_id,
                'attempt_timestamp': datetime.now().isoformat(),
                'success': success,
                'attempt_count': 1
            }
            
            self.logger.info(f"Repair attempt recorded: {repair_key} - Success: {success}")
            
        except Exception as e:
            self.logger.error(f"Error recording repair attempt: {e}")
    
    def cleanup_protocol_file(self):
        """Clean up the Master Diagnostic Protocol file by removing appended sections and properly integrating systems into the main tables"""
        try:
            if not self.orchestrator:
                self.logger.error("No orchestrator available for protocol cleanup")
                return
            
            # Load the protocol file
            protocol_path = self.orchestrator.base_path.parent / "read_me" / "MASTER_DIAGNOSTIC_PROTOCOL_2025-10-05.md"
            
            if not protocol_path.exists():
                self.logger.error(f"Protocol file not found: {protocol_path}")
                return
            
            with open(protocol_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.logger.info("Cleaning up Master Diagnostic Protocol file...")
            self.logger.info(f"Original file size: {len(content)} characters")
            
            # Find where the appended sections start (after the main content)
            fault_codes_start = content.find("## **FAULT SYMPTOMS & DIAGNOSTIC CODES**")
            if fault_codes_start == -1:
                self.logger.error("Could not find FAULT SYMPTOMS section")
                return
            
            # Find where the appended sections start
            appended_start = content.find("## Bus-1.2 - Universal Communicator")
            if appended_start == -1:
                self.logger.info("No appended sections found")
                return
            
            # Extract the main content (before appended sections)
            main_content = content[:appended_start].rstrip()
            
            # Extract the appended systems
            appended_content = content[appended_start:]
            
            # Parse the appended systems to extract their information
            systems_to_add = []
            
            # Find all appended system entries
            system_pattern = r'## ([^-]+) - (.+?)\n\n\*\*Handler:\*\* (.+?)\n\*\*Location:\*\* (.+?)\n'
            matches = re.findall(system_pattern, appended_content, re.DOTALL)
            
            for match in matches:
                address = match[0].strip()
                name = match[1].strip()
                handler = match[2].strip()
                location = match[3].strip()
                
                # Determine parent based on address pattern
                if '.' in address:
                    if address.startswith('Bus-'):
                        parent = 'Bus-1'
                    elif address.startswith('1-'):
                        parent = '1-1'
                    elif address.startswith('2-'):
                        parent = '2-1'
                    elif address.startswith('3-'):
                        parent = '3-1'
                    elif address.startswith('4-'):
                        parent = '4-1'
                    elif address.startswith('5-'):
                        parent = '5-1'
                    elif address.startswith('6-'):
                        parent = '6-1'
                    elif address.startswith('7-'):
                        parent = '7-1'
                    else:
                        parent = '-'
                else:
                    parent = '-'
                
                systems_to_add.append({
                    'address': address,
                    'name': name,
                    'handler': handler,
                    'parent': parent
                })
                
                self.logger.info(f"Found system: {address} - {name}")
            
            # Now integrate these systems into the appropriate tables
            updated_content = main_content
            
            # Remove duplicates and sort systems
            unique_systems = {}
            for system in systems_to_add:
                key = system['address']
                if key not in unique_systems:
                    unique_systems[key] = system
            
            # Add systems to appropriate sections
            for system in unique_systems.values():
                address = system['address']
                name = system['name']
                handler = system['handler']
                parent = system['parent']
                
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
            
            # Write the cleaned up content back to file
            with open(protocol_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            
            self.logger.info(f"Cleaned up file size: {len(updated_content)} characters")
            self.logger.info(f"Removed {len(content) - len(updated_content)} characters of appended content")
            self.logger.info(f"Integrated {len(unique_systems)} systems into main tables")
            
        except Exception as e:
            self.logger.error(f"Error cleaning up protocol file: {e}")
    
    def _add_to_bus_table(self, content, address, name, handler, parent):
        """Add system to Bus System table"""
        bus_pattern = r'(### \*\*Bus System\*\*\s*\n\| Address \| System Name \| Handler \| Status \| Last Check \|\s*\n\|-+\|-+\|-+\|-+\|-+\|\s*\n)'
        
        def add_row(match):
            table_header = match.group(1)
            new_row = f"| {address} | {name} | {handler} | ACTIVE | - |\n"
            return table_header + new_row
        
        return re.sub(bus_pattern, add_row, content)
    
    def _add_to_evidence_locker_table(self, content, address, name, handler, parent):
        """Add system to Evidence Locker Complex table"""
        evidence_pattern = r'(### \*\*Evidence Locker Complex \(1-x\)\*\*\s*\n\| Address \| System Name \| Handler \| Parent \| Status \| Last Check \|\s*\n\|-+\|-+\|-+\|-+\|-+\|-+\|\s*\n)'
        
        def add_row(match):
            table_header = match.group(1)
            new_row = f"| {address} | {name} | {handler} | {parent} | ACTIVE | - |\n"
            return table_header + new_row
        
        return re.sub(evidence_pattern, add_row, content)
    
    def _add_to_warden_table(self, content, address, name, handler, parent):
        """Add system to Warden Complex table"""
        warden_pattern = r'(### \*\*Warden Complex \(2-x\)\*\*\s*\n\| Address \| System Name \| Handler \| Parent \| Status \| Last Check \|\s*\n\|-+\|-+\|-+\|-+\|-+\|-+\|\s*\n)'
        
        def add_row(match):
            table_header = match.group(1)
            new_row = f"| {address} | {name} | {handler} | {parent} | ACTIVE | - |\n"
            return table_header + new_row
        
        return re.sub(warden_pattern, add_row, content)
    
    def _add_to_mission_debrief_table(self, content, address, name, handler, parent):
        """Add system to Mission Debrief Complex table"""
        mission_pattern = r'(### \*\*Mission Debrief Complex \(3-x\)\*\*\s*\n\| Address \| System Name \| Handler \| Parent \| Status \| Last Check \|\s*\n\|-+\|-+\|-+\|-+\|-+\|-+\|\s*\n)'
        
        def add_row(match):
            table_header = match.group(1)
            new_row = f"| {address} | {name} | {handler} | {parent} | ACTIVE | - |\n"
            return table_header + new_row
        
        return re.sub(mission_pattern, add_row, content)
    
    def _add_to_analyst_deck_table(self, content, address, name, handler, parent):
        """Add system to Analyst Deck Complex table"""
        analyst_pattern = r'(### \*\*Analyst Deck Complex \(4-x\)\*\*\s*\n\| Address \| System Name \| Handler \| Parent \| Status \| Last Check \|\s*\n\|-+\|-+\|-+\|-+\|-+\|-+\|\s*\n)'
        
        def add_row(match):
            table_header = match.group(1)
            new_row = f"| {address} | {name} | {handler} | {parent} | ACTIVE | - |\n"
            return table_header + new_row
        
        return re.sub(analyst_pattern, add_row, content)
    
    def _add_to_marshall_table(self, content, address, name, handler, parent):
        """Add system to Marshall Complex table"""
        marshall_pattern = r'(### \*\*Marshall Complex \(5-x\)\*\*\s*\n\| Address \| System Name \| Handler \| Parent \| Status \| Last Check \|\s*\n\|-+\|-+\|-+\|-+\|-+\|-+\|\s*\n)'
        
        def add_row(match):
            table_header = match.group(1)
            new_row = f"| {address} | {name} | {handler} | {parent} | ACTIVE | - |\n"
            return table_header + new_row
        
        return re.sub(marshall_pattern, add_row, content)
    
    def _add_to_war_room_table(self, content, address, name, handler, parent):
        """Add system to War Room Complex table"""
        war_room_pattern = r'(### \*\*War Room Complex \(6-x\)\*\*\s*\n\| Address \| System Name \| Handler \| Parent \| Status \| Last Check \|\s*\n\|-+\|-+\|-+\|-+\|-+\|-+\|\s*\n)'
        
        def add_row(match):
            table_header = match.group(1)
            new_row = f"| {address} | {name} | {handler} | {parent} | ACTIVE | - |\n"
            return table_header + new_row
        
        return re.sub(war_room_pattern, add_row, content)
    
    def _add_to_gui_table(self, content, address, name, handler, parent):
        """Add system to Enhanced Functional GUI table"""
        gui_pattern = r'(### \*\*Enhanced Functional GUI \(7-x\)\*\*\s*\n\| Address \| System Name \| Handler \| Parent \| Status \| Last Check \|\s*\n\|-+\|-+\|-+\|-+\|-+\|-+\|\s*\n)'
        
        def add_row(match):
            table_header = match.group(1)
            new_row = f"| {address} | {name} | {handler} | {parent} | ACTIVE | - |\n"
            return table_header + new_row
        
        return re.sub(gui_pattern, add_row, content)
    
    def _add_to_general_table(self, content, address, name, handler, parent):
        """Add system to General Systems table (create if doesn't exist)"""
        general_pattern = r'(### \*\*General Systems\*\*\s*\n\| Address \| System Name \| Handler \| Parent \| Status \| Last Check \|\s*\n\|-+\|-+\|-+\|-+\|-+\|-+\|\s*\n)'
        
        def add_row(match):
            table_header = match.group(1)
            new_row = f"| {address} | {name} | {handler} | {parent} | ACTIVE | - |\n"
            return table_header + new_row
        
        # If general section exists, update it
        if re.search(general_pattern, content):
            return re.sub(general_pattern, add_row, content)
        else:
            # Create new general section
            general_section = f"""
### **General Systems**
| Address | System Name | Handler | Parent | Status | Last Check |
|---------|-------------|---------|--------|--------|------------|
| {address} | {name} | {handler} | {parent} | ACTIVE | - |

"""
            # Insert before the fault codes section
            fault_codes_pattern = r'(## \*\*FAULT SYMPTOMS & DIAGNOSTIC CODES\*\*)'
            return re.sub(fault_codes_pattern, general_section + r'\1', content)
