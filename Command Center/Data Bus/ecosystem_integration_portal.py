# ecosystem_integration_portal.py
# Unified plug-in and UI portal layer for the ecosystem bus system

from plugin_manager import PluginManager
from plugin_lifecycle_manager import PluginLifecycleManager
from api_manager import APIManager
from pdf_manager import PDFManager
from case_library_manager import CaseLibraryManager

class EcosystemIntegrationPortal:
    def __init__(self, bus):
        self.bus = bus

        # Plug-in system
        self.plugin_manager = PluginManager(self.bus)
        self.lifecycle = PluginLifecycleManager()

        # API and tools
        self.api = APIManager()
        self.pdf = PDFManager()
        self.library = CaseLibraryManager()

        # Startup loading
        self.plugin_manager.auto_register_plugins()
        self.active_ui = None

    def register_ui(self, ui_controller):
        self.active_ui = ui_controller
        print("[Portal] UI registered.")

    def launch_ui(self):
        if self.active_ui:
            self.active_ui.launch()
        else:
            raise Exception("No UI controller registered.")

    def refresh_plugins(self):
        self.plugin_manager.auto_register_plugins()

    def install_plugin(self, plugin_id, url):
        return self.lifecycle.install_plugin_from_url(plugin_id, url)

    def uninstall_plugin(self, plugin_id):
        return self.lifecycle.uninstall_plugin(plugin_id)

    def toggle_plugin(self, plugin_id, enable):
        if enable:
            self.lifecycle.enable_plugin(plugin_id)
        else:
            self.lifecycle.disable_plugin(plugin_id)

    def list_plugins(self):
        return self.lifecycle.list_plugins()

    def toggle_api(self, name, enabled):
        self.api.toggle_api(name, enabled)

    def test_api(self, name):
        return self.api.test_api(name)

    def export_case_pdf(self, case_id, report_data):
        return self.pdf.export_report(case_id, report_data)

    def load_case_library(self):
        return self.library.list_cases()

    def get_case_info(self, case_id):
        return self.library.get_case_metadata(case_id)

    def get_pdf_path(self, case_id):
        return self.library.get_final_pdf_path(case_id)
