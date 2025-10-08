#!/usr/bin/env python3
"""
Test the protocol update functionality
"""

import re
from pathlib import Path

def test_protocol_update():
    """Test the protocol update functionality"""
    
    # Load the protocol file
    protocol_path = Path(__file__).parent.parent / "read_me" / "MASTER_DIAGNOSTIC_PROTOCOL_2025-10-05.md"
    with open(protocol_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("Testing protocol update functionality...")
    print(f"File size: {len(content)} characters")
    
    # Test the fault codes pattern
    fault_codes_pattern = r'(## \*\*FAULT SYMPTOMS & DIAGNOSTIC CODES\*\*)'
    match = re.search(fault_codes_pattern, content)
    
    if match:
        print("[FOUND] FAULT SYMPTOMS section")
        print(f"Position: {match.start()}")
        
        # Test inserting a new section before it
        test_section = """
### **General Systems**
| Address | System Name | Handler | Parent | Status | Last Check |
|---------|-------------|---------|--------|--------|------------|
| GEN-2.798 | Case Management Panel | case_management_panel.CaseManagementPanel | GEN-2 | ACTIVE | - |

"""
        
        # Test the replacement
        new_content = re.sub(fault_codes_pattern, test_section + r'\1', content)
        
        if len(new_content) > len(content):
            print("[SUCCESS] Successfully inserted new section")
            print(f"New file size: {len(new_content)} characters")
            
            # Find the inserted content
            if "GEN-2.798" in new_content:
                print("[SUCCESS] New system found in updated content")
            else:
                print("[ERROR] New system not found in updated content")
        else:
            print("[ERROR] Failed to insert new section")
    else:
        print("[ERROR] FAULT SYMPTOMS section not found")
    
    # Test the Bus section pattern
    bus_section_pattern = r'(### \*\*Bus System\*\*\s*\n\| Address \| System Name \| Handler \| Status \| Last Check \|\s*\n\|-+\|-+\|-+\|-+\|-+\|\s*\n)'
    bus_match = re.search(bus_section_pattern, content)
    
    if bus_match:
        print("[FOUND] Bus System section")
        print(f"Position: {bus_match.start()}")
        
        # Test adding to bus table
        def add_to_bus_table(match):
            table_header = match.group(1)
            new_row = "| Bus-1.6 | Test System | test_system.TestSystem | ACTIVE | - |\n"
            return table_header + new_row
        
        bus_content = re.sub(bus_section_pattern, add_to_bus_table, content)
        
        if "Bus-1.6" in bus_content:
            print("[SUCCESS] Successfully added to Bus table")
        else:
            print("[ERROR] Failed to add to Bus table")
    else:
        print("[ERROR] Bus System section not found")

if __name__ == "__main__":
    test_protocol_update()
