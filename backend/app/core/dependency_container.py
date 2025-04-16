import logging
from typing import Dict, Any, Callable, Optional, Type, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar('T')

class DependencyContainer:
    """
    Container for managing service dependencies in the modular monolith architecture.
    Responsible for storing service instances and factory functions.
    """
    
    def __init__(self):
        self._instances: Dict[str, Any] = {}
        self._factories: Dict[str, Callable[[], Any]] = {}
    
    def register_instance(self, name: str, instance: Any) -> None:
        """
        Register an instance with the container
        
        Args:
            name: Name to register the instance under
            instance: The instance to register
            
        Raises:
            ValueError: If an instance with the same name is already registered
        """
        if name in self._instances:
            raise ValueError(f"Instance '{name}' is already registered")
        
        self._instances[name] = instance
        logger.debug(f"Instance '{name}' registered")
    
    def register_factory(self, name: str, factory: Callable[[], Any]) -> None:
        """
        Register a factory function with the container
        
        Args:
            name: Name to register the factory under
            factory: Factory function that creates the instance
            
        Raises:
            ValueError: If a factory with the same name is already registered
        """
        if name in self._factories:
            raise ValueError(f"Factory '{name}' is already registered")
        
        self._factories[name] = factory
        logger.debug(f"Factory '{name}' registered")
    
    def get(self, name: str) -> Any:
        """
        Get an instance by name
        
        Args:
            name: Name of the instance
            
        Returns:
            The instance
            
        Raises:
            KeyError: If the instance is not found
        """
        # Check if instance exists
        if name in self._instances:
            return self._instances[name]
        
        # Check if factory exists
        if name in self._factories:
            # Create instance using factory
            instance = self._factories[name]()
            # Cache instance
            self._instances[name] = instance
            # Remove factory to avoid duplicate instantiation
            del self._factories[name]
            logger.debug(f"Instance '{name}' created using factory")
            return instance
        
        raise KeyError(f"No instance or factory registered for '{name}'")
    
    def get_typed(self, name: str, expected_type: Type[T]) -> T:
        """
        Get an instance by name with type checking
        
        Args:
            name: Name of the instance
            expected_type: Expected type of the instance
            
        Returns:
            The instance
            
        Raises:
            KeyError: If the instance is not found
            TypeError: If the instance is not of the expected type
        """
        instance = self.get(name)
        
        if not isinstance(instance, expected_type):
            raise TypeError(f"Instance '{name}' is not of type {expected_type.__name__}")
        
        return instance
    
    def has(self, name: str) -> bool:
        """
        Check if an instance or factory is registered
        
        Args:
            name: Name of the instance or factory
            
        Returns:
            True if the instance or factory is registered, False otherwise
        """
        return name in self._instances or name in self._factories
    
    def has_instance(self, name: str) -> bool:
        """
        Check if an instance is registered
        
        Args:
            name: Name of the instance
            
        Returns:
            True if the instance is registered, False otherwise
        """
        return name in self._instances
    
    def has_factory(self, name: str) -> bool:
        """
        Check if a factory is registered
        
        Args:
            name: Name of the factory
            
        Returns:
            True if the factory is registered, False otherwise
        """
        return name in self._factories
    
    def clear(self) -> None:
        """
        Clear all instances and factories
        """
        self._instances.clear()
        self._factories.clear()
        logger.debug("Dependency container cleared")
    
    def get_all_registered_names(self) -> Dict[str, str]:
        """
        Get all registered names
        
        Returns:
            Dictionary mapping names to their type (instance or factory)
        """
        result = {}
        
        for name in self._instances:
            result[name] = "instance"
        
        for name in self._factories:
            result[name] = "factory"
        
        return result

# Create global dependency container
container = DependencyContainer() 