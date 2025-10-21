#!/usr/bin/env python3
"""
Script to update all Analyst sections with initialization protocol.
Updates sections 2-8 with bus stabilization and registration.
"""

import os
from pathlib import Path

# Base paths
ANALYST_DECK = Path(r"F:\The Central Command\The Analyst Deck")

# Section addresses
SECTIONS = {
    2: "4-2",
    3: "4-3", 
    4: "4-4",
    5: "4-5",
    6: "4-6",
    7: "4-7",
    8: "4-8"
}

# Section capabilities
CAPABILITIES = {
    2: "['report_structure', 'document_assembly', 'formatting']",
    3: "['media_analysis', 'video_processing', 'audio_transcription']",
    4: "['document_validation', 'compliance_checks', 'data_sources']",
    5: "['witness_statements', 'testimony_analysis', 'deposition_review']",
    6: "['billing_analysis', 'cost_tracking', 'expense_validation']",
    7: "['timeline_analysis', 'chronological_ordering', 'event_tracking']",
    8: "['multimedia_processing', 'media_orchestration', 'caption_generation']"
}

def update_section(num, address, caps):
    """Update a single analyst section file."""
    section_file = ANALYST_DECK / f"Analyst {num}" / f"section_{num}_framework.py"
    
    if not section_file.exists():
        print(f"[ERROR] Section {num} file not found: {section_file}")
        return False
    
    print(f"[UPDATE] Updating Section {num} ({address})...")
    
    # Read file
    with open(section_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if already updated
    if 'MODULE INITIALIZATION PROTOCOL' in content:
        print(f"  [OK] Already updated")
        return True
    
    # Find and replace bus initialization
    old_pattern = """        if self.bus:
            self._initialize_canbus(self.bus, communicator=self.communicator)
        else:
            self.logger.warning("[%s] CANBUS initialization skipped - no bus provided", self.MODULE_ADDRESS)
            self.bus_connected = False"""
    
    new_pattern = f"""        if self.bus:
            # MODULE INITIALIZATION PROTOCOL - Wait for bus ready and module turn
            self.logger.info("[%s] Waiting for bus stabilization...", self.MODULE_ADDRESS)
            if not self.bus.wait_for_ready(timeout=15.0):
                self.logger.error("[%s] Bus stabilization timeout - initialization may be unstable", self.MODULE_ADDRESS)
                self.bus_connected = False
            else:
                self.logger.info("[%s] Bus ready - waiting for module turn in sequence...", self.MODULE_ADDRESS)
                if not self.bus.wait_for_module_turn('{address}', timeout=30.0):
                    self.logger.error("[%s] Module turn timeout - cannot initialize", self.MODULE_ADDRESS)
                    self.bus_connected = False
                else:
                    self._initialize_canbus(self.bus, communicator=self.communicator)
        else:
            self.logger.warning("[%s] CANBUS initialization skipped - no bus provided", self.MODULE_ADDRESS)
            self.bus_connected = False"""
    
    if old_pattern in content:
        content = content.replace(old_pattern, new_pattern)
        print(f"  [OK] Added bus stabilization checks")
    else:
        print(f"  [WARN] Bus initialization pattern not found")
    
    # Find and replace registration
    old_reg_pattern = """            self._register_signal_handlers()
            self.bus_connected = True
            self.logger.info("[%s] CANBUS CONNECTION ESTABLISHED", self.MODULE_ADDRESS)"""
    
    new_reg_pattern = f"""            self._register_signal_handlers()
            self.bus_connected = True
            self.logger.info("[%s] CANBUS CONNECTION ESTABLISHED", self.MODULE_ADDRESS)
            
            # MODULE INITIALIZATION PROTOCOL - Register with bus
            if self.bus.register_module_init('{address}', {{
                'version': '1.0',
                'type': 'analyst_section',
                'capabilities': {caps}
            }}):
                self.logger.info("[%s] [OK] Module registered with bus (Address {address})", self.MODULE_ADDRESS)
            else:
                self.logger.warning("[%s] Module registration failed - continuing anyway", self.MODULE_ADDRESS)"""
    
    if old_reg_pattern in content:
        content = content.replace(old_reg_pattern, new_reg_pattern)
        print(f"  [OK] Added bus registration")
    else:
        print(f"  [WARN] Registration pattern not found")
    
    # Write updated content
    with open(section_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"  [OK] Section {num} updated successfully")
    return True

def main():
    """Update all analyst sections."""
    print("=" * 60)
    print("ANALYST SECTION PROTOCOL UPDATE")
    print("=" * 60)
    print()
    
    updated = 0
    for num, address in SECTIONS.items():
        caps = CAPABILITIES[num]
        if update_section(num, address, caps):
            updated += 1
        print()
    
    print("=" * 60)
    print(f"COMPLETE: {updated}/{len(SECTIONS)} sections updated")
    print("=" * 60)

if __name__ == "__main__":
    main()

