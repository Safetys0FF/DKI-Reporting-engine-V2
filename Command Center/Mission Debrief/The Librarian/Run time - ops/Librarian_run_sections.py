# run_sections.py

from section_cp_framework import SectionCPFramework
from section_dp_framework import SectionDPFramework

class MockECC:
    def can_run(self, section_id): return True
    def mark_complete(self, section_id, source): print(f"[ECC] Marked {section_id} complete via {source}")

class MockGateway:
    def get_input(self, channel): return f"Mocked data from {channel}"

# Implement missing stage methods for demo purposes
class ActiveCP(SectionCPFramework):
    def _define_communication_contract(self): return self.COMMUNICATION
    def _define_fact_graph_contract(self): return None
    def _define_persistence_contract(self): return None

    def _stage_intake(self): print("Stage: intake → OK"); return True
    def _stage_validate(self): print("Stage: validate → OK"); return True
    def _stage_render(self): print("Stage: render → OK"); return True
    def _stage_qa(self): print("Stage: QA → OK"); return True
    def _stage_publish(self): print("Stage: publish → OK"); return True
    def _stage_monitor(self): print("Stage: monitor → OK"); return True

class ActiveDP(SectionDPFramework):
    def _define_communication_contract(self): return self.COMMUNICATION
    def _define_fact_graph_contract(self): return self.FACT_GRAPH
    def _define_persistence_contract(self): return self.PERSISTENCE

    def _stage_intake(self): print("Stage: intake → OK"); return True
    def _stage_compile(self): print("Stage: compile → OK"); return True
    def _stage_validate(self): print("Stage: validate → OK"); return True
    def _stage_publish(self): print("Stage: publish → OK"); return True
    def _stage_monitor(self): print("Stage: monitor → OK"); return True

def run_all_sections():
    ecc = MockECC()
    gateway = MockGateway()

    print("\n▶ Running Cover Page (section_cp)")
    cp = ActiveCP(ecc=ecc, gateway=gateway)
    cp.run_pipeline()

    print("\n▶ Running Disclosure Page (section_dp)")
    dp = ActiveDP(ecc=ecc, gateway=gateway)
    dp.run_pipeline()

if __name__ == "__main__":
    run_all_sections()
