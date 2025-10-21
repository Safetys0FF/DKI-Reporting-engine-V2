import sys
from pathlib import Path
import unittest
base_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(base_dir / 'Data Bus'))
sys.path.insert(0, str(base_dir / 'Data Bus' / 'Bus Core Design'))

sys.path.insert(0, str(Path(__file__).resolve().parent))

from central_plugin import central_plugin


class TestGatewayWiring(unittest.TestCase):
    def test_gateway_signals_registered(self):
        registry = getattr(central_plugin.bus, "signal_registry", {})
        self.assertIn("gateway.handoff", registry)
        self.assertIn("gateway.signal.dispatch", registry)
        self.assertIn("gateway.status.request", registry)

    def test_ping_bus_structure(self):
        response = central_plugin.ping_bus()
        self.assertIsInstance(response, dict)
        self.assertEqual(response.get("status"), "ok")
        self.assertIsInstance(response.get("registered_signals"), list)

    def test_route_evidence_handoff_returns_status(self):
        result = central_plugin.route_evidence_handoff({})
        self.assertIn(result.get("status"), {"ok", "error"})


if __name__ == "__main__":
    unittest.main()
