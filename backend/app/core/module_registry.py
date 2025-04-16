"""
Module registry for handling modular architecture components.
Allows modules to be registered and discovered at runtime.
"""

from typing import Dict, List, Optional, Callable, Any
from fastapi import APIRouter, FastAPI

class ModuleRegistry:
    """
    Registry for application modules in a modular monolith architecture.
    Handles module registration, initialization, and router mounting.
    """
    
    def __init__(self):
        self.modules: Dict[str, Any] = {}
        self.routers: Dict[str, APIRouter] = {}
        self.startup_handlers: List[Callable] = []
        self.shutdown_handlers: List[Callable] = []
    
    def register_module(self, name: str, module: Any) -> None:
        """Register a module with the registry"""
        if name in self.modules:
            raise ValueError(f"Module {name} is already registered")
        self.modules[name] = module
    
    def register_router(self, name: str, router: APIRouter, prefix: str = "") -> None:
        """Register a router for a module"""
        self.routers[name] = router
    
    def register_startup_handler(self, handler: Callable) -> None:
        """Register a function to be called on application startup"""
        self.startup_handlers.append(handler)
    
    def register_shutdown_handler(self, handler: Callable) -> None:
        """Register a function to be called on application shutdown"""
        self.shutdown_handlers.append(handler)
    
    def get_module(self, name: str) -> Optional[Any]:
        """Get a module by name"""
        return self.modules.get(name)
    
    def get_all_modules(self) -> Dict[str, Any]:
        """Get all registered modules"""
        return self.modules
    
    def mount_all_routers(self, app: FastAPI) -> None:
        """Mount all registered routers to the FastAPI application"""
        for name, router in self.routers.items():
            prefix = f"/{name}" if not name.startswith("/") else name
            app.include_router(router, prefix=prefix)
    
    def run_startup_handlers(self) -> None:
        """Run all registered startup handlers"""
        for handler in self.startup_handlers:
            handler()
    
    def run_shutdown_handlers(self) -> None:
        """Run all registered shutdown handlers"""
        for handler in self.shutdown_handlers:
            handler()

# Create a global registry instance
registry = ModuleRegistry() 