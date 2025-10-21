"""
Component Auto-Loader - Central Command UI
Date: October 10, 2025

Automatically discovers and loads available UI components based on:
- Component availability (optional dependencies installed)
- User role and permissions
- System configuration

Provides progressive disclosure - basic users see simple interface,
advanced users/admins see additional capabilities.
"""

import sys
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ComponentInfo:
    """Metadata for a loadable component"""
    name: str
    module_name: str
    class_name: str
    display_name: str
    description: str
    required_role: str  # "basic", "analyst", "supervisor", "admin"
    required_deps: List[str]  # External dependencies
    category: str  # "monitoring", "management", "setup", "advanced"
    available: bool = False
    load_error: Optional[str] = None


class ComponentLoader:
    """
    Auto-discovers and conditionally loads UI components based on
    availability, dependencies, and user permissions.
    """
    
    # Component registry with metadata
    COMPONENT_REGISTRY: Dict[str, ComponentInfo] = {
        "system_health": ComponentInfo(
            name="system_health",
            module_name="components.system_health_dashboard",
            class_name="SystemHealthDashboard",
            display_name="System Health Monitor",
            description="Real-time CPU, memory, and disk monitoring",
            required_role="analyst",
            required_deps=["psutil"],
            category="monitoring"
        ),
        "api_status": ComponentInfo(
            name="api_status",
            module_name="components.api_status_panel",
            class_name="APIStatusPanel",
            display_name="API Status Monitor",
            description="Monitor external API connectivity",
            required_role="supervisor",
            required_deps=["requests"],
            category="monitoring"
        ),
        "case_management": ComponentInfo(
            name="case_management",
            module_name="components.case_management_panel",
            class_name="CaseManagementPanel",
            display_name="Case Management",
            description="Create and manage investigation cases",
            required_role="basic",
            required_deps=[],
            category="management"
        ),
        "evidence_panel": ComponentInfo(
            name="evidence_panel",
            module_name="components.evidence_panel",
            class_name="EvidencePanel",
            display_name="Evidence Intake",
            description="Evidence upload and processing",
            required_role="basic",
            required_deps=[],
            category="management"
        ),
        "file_drop": ComponentInfo(
            name="file_drop",
            module_name="components.file_drop_zone",
            class_name="FileDropZone",
            display_name="File Drop Zone",
            description="Drag-and-drop file upload",
            required_role="basic",
            required_deps=["tkinterdnd2"],
            category="management"
        ),
        "section_control": ComponentInfo(
            name="section_control",
            module_name="components.section_control_panel",
            class_name="SectionControlPanel",
            display_name="Section Control",
            description="Control report sections",
            required_role="analyst",
            required_deps=[],
            category="advanced"
        ),
        "report_control": ComponentInfo(
            name="report_control",
            module_name="components.report_control_panel",
            class_name="ReportControlPanel",
            display_name="Report Controls",
            description="Generate and export reports",
            required_role="analyst",
            required_deps=[],
            category="advanced"
        ),
        "setup_wizard": ComponentInfo(
            name="setup_wizard",
            module_name="components.setup_wizard",
            class_name="SetupWizard",
            display_name="Setup Wizard",
            description="First-time setup and configuration",
            required_role="basic",
            required_deps=[],
            category="setup"
        ),
        "user_profile": ComponentInfo(
            name="user_profile",
            module_name="components.user_profile_dialog",
            class_name="UserProfileDialog",
            display_name="User Profile",
            description="User profile settings",
            required_role="basic",
            required_deps=[],
            category="setup"
        )
    }
    
    # Role hierarchy (higher includes lower)
    ROLE_HIERARCHY = {
        "basic": 0,
        "analyst": 1,
        "supervisor": 2,
        "admin": 3
    }
    
    def __init__(self, user_role: str = "basic"):
        """
        Initialize component loader.
        
        Args:
            user_role: User's role level (basic, analyst, supervisor, admin)
        """
        self.user_role = user_role.lower()
        self.user_level = self.ROLE_HIERARCHY.get(self.user_role, 0)
        self.available_components: Dict[str, ComponentInfo] = {}
        self.loaded_classes: Dict[str, Any] = {}
        
        self._discover_components()
    
    def _discover_components(self) -> None:
        """Discover which components are available based on dependencies and role"""
        logger.info(f"Discovering components for role: {self.user_role}")
        
        for comp_id, comp_info in self.COMPONENT_REGISTRY.items():
            # Check role permission
            required_level = self.ROLE_HIERARCHY.get(comp_info.required_role, 0)
            if self.user_level < required_level:
                logger.debug(f"Component {comp_id} requires role {comp_info.required_role}, skipping")
                continue
            
            # Check dependencies
            missing_deps = []
            for dep in comp_info.required_deps:
                try:
                    __import__(dep)
                except ImportError:
                    missing_deps.append(dep)
            
            if missing_deps:
                comp_info.load_error = f"Missing dependencies: {', '.join(missing_deps)}"
                logger.warning(f"Component {comp_id} unavailable: {comp_info.load_error}")
                continue
            
            # Component is available
            comp_info.available = True
            self.available_components[comp_id] = comp_info
            logger.info(f"[OK] Component available: {comp_info.display_name}")
    
    def get_component_class(self, component_id: str) -> Optional[Any]:
        """
        Load and return component class if available.
        
        Args:
            component_id: Component identifier
        
        Returns:
            Component class or None if unavailable
        """
        # Check if already loaded
        if component_id in self.loaded_classes:
            return self.loaded_classes[component_id]
        
        # Check if available
        comp_info = self.available_components.get(component_id)
        if not comp_info or not comp_info.available:
            logger.warning(f"Component {component_id} not available")
            return None
        
        # Load component class
        try:
            module = __import__(comp_info.module_name, fromlist=[comp_info.class_name])
            component_class = getattr(module, comp_info.class_name)
            self.loaded_classes[component_id] = component_class
            logger.info(f"[OK] Loaded component: {comp_info.display_name}")
            return component_class
        except Exception as e:
            logger.error(f"Failed to load component {component_id}: {e}")
            comp_info.load_error = str(e)
            return None
    
    def get_components_by_category(self, category: str) -> List[ComponentInfo]:
        """Get all available components in a category"""
        return [
            comp for comp in self.available_components.values()
            if comp.category == category
        ]
    
    def is_component_available(self, component_id: str) -> bool:
        """Check if component is available for current user"""
        comp = self.available_components.get(component_id)
        return comp is not None and comp.available
    
    def get_available_component_ids(self) -> List[str]:
        """Get list of all available component IDs"""
        return list(self.available_components.keys())
    
    def get_component_info(self, component_id: str) -> Optional[ComponentInfo]:
        """Get metadata for a component"""
        return self.available_components.get(component_id)
    
    def create_component(
        self,
        component_id: str,
        parent,
        **kwargs
    ) -> Optional[Any]:
        """
        Create component instance if available.
        
        Args:
            component_id: Component identifier
            parent: Parent tkinter widget
            **kwargs: Additional arguments for component constructor
        
        Returns:
            Component instance or None if unavailable
        """
        component_class = self.get_component_class(component_id)
        if not component_class:
            return None
        
        try:
            instance = component_class(parent, **kwargs)
            logger.info(f"[OK] Created component instance: {component_id}")
            return instance
        except Exception as e:
            logger.error(f"Failed to create component {component_id}: {e}")
            return None
    
    def get_role_appropriate_tabs(self) -> List[Dict[str, str]]:
        """
        Get tab definitions appropriate for user's role.
        
        Returns list of tab configs: [{"id": "home", "title": "Home", "category": "core"}, ...]
        """
        tabs = [
            # Core tabs (always visible)
            {"id": "home", "title": "Home", "category": "core"},
            {"id": "cases", "title": "Cases", "category": "core"},
            {"id": "workspace", "title": "Workspace", "category": "core"},
        ]
        
        # Analyst and above: Review and Assembly
        if self.user_level >= self.ROLE_HIERARCHY["analyst"]:
            tabs.extend([
                {"id": "review", "title": "Review", "category": "analyst"},
                {"id": "assembly", "title": "Assembly", "category": "analyst"},
            ])
        
        # Supervisor and above: System monitoring
        if self.user_level >= self.ROLE_HIERARCHY["supervisor"]:
            # Only add if monitoring components available
            if self.is_component_available("system_health") or self.is_component_available("api_status"):
                tabs.append({"id": "system", "title": "System", "category": "supervisor"})
        
        # Admin only: Advanced settings
        if self.user_level >= self.ROLE_HIERARCHY["admin"]:
            tabs.append({"id": "settings", "title": "Settings", "category": "admin"})
        
        return tabs
    
    def lazy_create(self, component_id: str):
        """
        Return factory function for lazy component creation.
        
        This enables Section-framework-style lazy loading:
        initializer = loader.lazy_create("system_health")
        component = initializer(parent)
        
        Args:
            component_id: Component identifier
        
        Returns:
            Factory function that creates component when called
        """
        def factory(parent, **kwargs):
            return self.create_component(component_id, parent, **kwargs)
        return factory
    
    def get_initializers(self) -> Dict[str, Any]:
        """
        Return dict of lazy initializers (Section framework pattern).
        
        Returns dict like:
        {
            "system_health": <factory_function>,
            "api_status": <factory_function>,
            ...
        }
        
        This matches the Section framework pattern where:
        initializers = {
            "metadata_processor": init_metadata_processor,
            "section_renderer": init_section_renderer,
        }
        """
        return {
            comp_id: self.lazy_create(comp_id)
            for comp_id in self.available_components.keys()
        }
    
    def generate_summary_report(self) -> str:
        """Generate summary of available components"""
        lines = [
            f"Component Loader - Role: {self.user_role.upper()}",
            "=" * 60,
            f"Available Components: {len(self.available_components)}",
            ""
        ]
        
        for category in ["monitoring", "management", "advanced", "setup"]:
            comps = self.get_components_by_category(category)
            if comps:
                lines.append(f"{category.upper()}:")
                for comp in comps:
                    lines.append(f"  - {comp.display_name}")
                lines.append("")
        
        unavailable = [
            comp for comp in self.COMPONENT_REGISTRY.values()
            if not comp.available
        ]
        if unavailable:
            lines.append("UNAVAILABLE:")
            for comp in unavailable:
                reason = comp.load_error or "Insufficient role permissions"
                lines.append(f"  - {comp.display_name}: {reason}")
        
        return "\n".join(lines)


# Convenience function for GUI integration
def get_loader(user_role: str = "basic") -> ComponentLoader:
    """Get component loader instance for given role"""
    return ComponentLoader(user_role)

