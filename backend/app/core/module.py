import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Set, Optional
from fastapi import APIRouter

from backend.app.core.dependency_container import container

logger = logging.getLogger(__name__)

class Module(ABC):
    """
    Base class for modules in the modular monolith architecture.
    Each module encapsulates a specific business domain with its own routes,
    services, and dependencies.
    """
    
    def __init__(self, container: DependencyContainer):
        """
        Initialize a module with the shared dependency container
        
        Args:
            container: The shared dependency container
        """
        self.container = container
        self.initialized = False
        self.name = self.__class__.__name__
        self._router: Optional[APIRouter] = None
        logger.debug(f"Module '{self.name}' created")
    
    @property
    def router(self) -> APIRouter:
        """
        Get the router for this module
        
        Returns:
            The module's APIRouter
        
        Raises:
            RuntimeError: If the module is not initialized
        """
        if not self.initialized:
            raise RuntimeError(f"Module '{self.name}' is not initialized")
        
        if self._router is None:
            raise RuntimeError(f"Module '{self.name}' does not have a router")
        
        return self._router
    
    @abstractmethod
    def get_dependencies(self) -> List[str]:
        """
        Get the list of module names this module depends on
        
        Returns:
            List of module names
        """
        return []
    
    @abstractmethod
    def register_dependencies(self) -> None:
        """
        Register the module's dependencies in the container
        """
        pass
    
    @abstractmethod
    def initialize(self) -> None:
        """
        Initialize the module
        
        Raises:
            RuntimeError: If initialization fails
        """
        pass
    
    def shutdown(self) -> None:
        """
        Shut down the module and clean up resources
        """
        self.initialized = False
        logger.info(f"Module '{self.name}' shut down")
    
    def _create_router(self, prefix: str = "", tags: List[str] = None) -> APIRouter:
        """
        Create an API router for this module
        
        Args:
            prefix: URL prefix for all routes in this module
            tags: OpenAPI tags for this module
            
        Returns:
            The created APIRouter
        """
        if tags is None:
            tags = [self.name]
            
        return APIRouter(prefix=prefix, tags=tags)

    def register_dependency(self, module_name: str) -> None:
        """
        Register a dependency on another module
        
        Args:
            module_name: Name of the module this module depends on
        """
        if module_name != self.name:  # Prevent self-dependency
            self.dependencies.add(module_name)
            logger.info(f"Module '{self.name}' depends on '{module_name}'")
    
    def register_service(self, service_class: Any, instance: Any) -> None:
        """
        Register a service with the dependency container
        
        Args:
            service_class: The class/type of the service
            instance: The service instance
        """
        container.register_service(service_class, instance)
    
    def register_factory(self, service_name: str, factory_func: callable) -> None:
        """
        Register a factory function for lazy service initialization
        
        Args:
            service_name: Name of the service
            factory_func: Factory function that returns a service instance
        """
        container.register_factory(service_name, factory_func)
    
    def get_service(self, service_class) -> Any:
        """
        Get a service instance from the dependency container
        
        Args:
            service_class: The class/type of the service
            
        Returns:
            The service instance
        """
        return container.get_service(service_class)
    
    def has_service(self, service_class) -> bool:
        """
        Check if a service is registered with the dependency container
        
        Args:
            service_class: The class/type of the service
            
        Returns:
            True if service is registered, False otherwise
        """
        return container.has_service(service_class)
    
    def get_router(self) -> APIRouter:
        """
        Get the module's router for API endpoints
        
        Returns:
            FastAPI router with the module's API endpoints
        """
        if not self.initialized:
            self.initialize()
        
        return self.router
    
    def is_initialized(self) -> bool:
        """
        Check if the module has been initialized
        
        Returns:
            True if the module is initialized, False otherwise
        """
        return self.initialized
    
    def __str__(self) -> str:
        """
        Get string representation of the module
        """
        status = "initialized" if self.initialized else "not initialized"
        return f"Module '{self.name}' ({status}) with {len(self.dependencies)} dependencies" 