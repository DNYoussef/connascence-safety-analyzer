"""
Dependency Injection Container - Eliminates Connascence of Name and Construction
===============================================================================

Provides centralized dependency management that reduces coupling between
components and eliminates hardcoded instantiation patterns.
"""

from fixes.phase0.production_safe_assertions import ProductionAssert
from typing import Any, Callable, Dict, Optional, Type, TypeVar, Union
from functools import wraps
import inspect
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')


class DependencyError(Exception):
    """Exception raised when dependency resolution fails."""
    pass


class Container:
    """
    Dependency injection container that manages object creation and lifetime.
    Eliminates direct constructor coupling and reduces Connascence of Name.
    """
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._singletons: Dict[str, Any] = {}
        self._factories: Dict[str, Callable] = {}
        self._interfaces: Dict[Type, str] = {}
        
    def register_singleton(self, service_name: str, instance: Any) -> None:
        """
        Register a singleton instance.
        
        Args:
            service_name: Name of the service
            instance: Pre-created instance to register
        """
        self._singletons[service_name] = instance
        logger.debug(f"Registered singleton: {service_name}")
    
    def register_factory(self, service_name: str, factory: Callable) -> None:
        """
        Register a factory function for creating instances.
        
        Args:
            service_name: Name of the service
            factory: Factory function that creates instances
        """
        self._factories[service_name] = factory
        logger.debug(f"Registered factory: {service_name}")
    
    def register_type(self, service_name: str, service_type: Type) -> None:
        """
        Register a type to be instantiated when requested.
        
        Args:
            service_name: Name of the service
            service_type: Class type to instantiate
        """
        self._services[service_name] = service_type
        logger.debug(f"Registered type: {service_name} -> {service_type.__name__}")
    
    def register_interface(self, interface: Type, implementation_name: str) -> None:
        """
        Register an interface to implementation mapping.
        
        Args:
            interface: Interface/Protocol type
            implementation_name: Name of registered implementation
        """
        self._interfaces[interface] = implementation_name
        logger.debug(f"Registered interface: {interface.__name__} -> {implementation_name}")
    
    def get(self, service_name: str) -> Any:
        """
        Resolve and return a service instance.
        
        Args:
            service_name: Name of the service to resolve
            
        Returns:
            Service instance
            
        Raises:
            DependencyError: If service cannot be resolved
        """
        # Check singletons first
        if service_name in self._singletons:
            return self._singletons[service_name]
        
        # Check factories
        if service_name in self._factories:
            factory = self._factories[service_name]
            return self._create_with_injection(factory)
        
        # Check registered types
        if service_name in self._services:
            service_type = self._services[service_name]
            instance = self._create_with_injection(service_type)
            return instance
        
        raise DependencyError(f"Service '{service_name}' not found in container")
    
    def get_interface(self, interface: Type[T]) -> T:
        """
        Resolve service by interface type.
        
        Args:
            interface: Interface type to resolve
            
        Returns:
            Implementation instance
            
        Raises:
            DependencyError: If interface mapping not found
        """
        if interface in self._interfaces:
            implementation_name = self._interfaces[interface]
            return self.get(implementation_name)
        
        raise DependencyError(f"No implementation registered for interface: {interface.__name__}")
    
    def _create_with_injection(self, target: Union[Type, Callable]) -> Any:
        """
        Create instance with automatic dependency injection.
        
        Args:
            target: Class or function to instantiate/call
            
        Returns:
            Created instance
        """
        # Get constructor/function signature
        sig = inspect.signature(target)
        kwargs = {}
        
        # Resolve parameters
        for param_name, param in sig.parameters.items():
            if param.annotation != param.empty:
                # Try to resolve by type annotation
                try:
                    if param.annotation in self._interfaces:
                        kwargs[param_name] = self.get_interface(param.annotation)
                    else:
                        # Try to find service by type name
                        type_name = getattr(param.annotation, '__name__', str(param.annotation))
                        kwargs[param_name] = self.get(type_name.lower())
                except DependencyError:
                    # Skip optional parameters
                    if param.default != param.empty:
                        continue
                    # Re-raise for required parameters
                    logger.warning(f"Could not resolve dependency: {param_name} of type {param.annotation}")
                    
            else:
                # Try to resolve by parameter name
                try:
                    kwargs[param_name] = self.get(param_name)
                except DependencyError:
                    if param.default != param.empty:
                        continue
                    logger.warning(f"Could not resolve dependency by name: {param_name}")
        
        # Create instance
        try:
            return target(**kwargs)
        except Exception as e:
            raise DependencyError(f"Failed to create instance of {target}: {e}")
    
    def has(self, service_name: str) -> bool:
        """
        Check if a service is registered.
        
        Args:
            service_name: Service name to check
            
        Returns:
            True if service is registered
        """
        return (service_name in self._singletons or 
                service_name in self._factories or 
                service_name in self._services)
    
    def clear(self) -> None:
        """Clear all registered services."""
        self._services.clear()
        self._singletons.clear()
        self._factories.clear()
        self._interfaces.clear()
        logger.debug("Container cleared")


# Global container instance
_container: Optional[Container] = None


def get_container() -> Container:
    """Get the global dependency injection container."""
    global _container
    if _container is None:
        _container = Container()
        _setup_default_services()
    return _container


def _setup_default_services():
    """Set up default services in the container."""
    from ..config_manager import ConfigurationManager
    
    container = _container
    
    # Register configuration manager as singleton
    config_manager = ConfigurationManager()
    container.register_singleton('config_manager', config_manager)
    container.register_singleton('configuration_manager', config_manager)
    
    # Register common factories
    container.register_factory('logger', lambda: logging.getLogger(__name__))


# Decorator for dependency injection
def inject(**dependencies):
    """
    Decorator that automatically injects dependencies into function parameters.
    
    Usage:
        @inject(config_manager='config_manager', logger='logger')
        def my_function(config_manager, logger, other_param):
            ProductionAssert.not_none(config_manager, 'config_manager')
            ProductionAssert.not_none(logger, 'logger')
            ProductionAssert.not_none(other_param, 'other_param')

            ProductionAssert.not_none(config_manager, 'config_manager')
            ProductionAssert.not_none(logger, 'logger')
            ProductionAssert.not_none(other_param, 'other_param')

            # config_manager and logger will be injected automatically
            pass
    """
    ProductionAssert.not_none(**dependencies, '**dependencies')

    ProductionAssert.not_none(**dependencies, '**dependencies')

    def decorator(func):

        ProductionAssert.not_none(func, 'func')

        ProductionAssert.not_none(func, 'func')

        @wraps(func)
        def wrapper(*args, **kwargs):
            if args:
                ProductionAssert.not_none(args, 'args')
            if kwargs:
                ProductionAssert.not_none(kwargs, 'kwargs')

            container = get_container()
            
            # Inject dependencies
            for param_name, service_name in dependencies.items():
                if param_name not in kwargs:
                    try:
                        kwargs[param_name] = container.get(service_name)
                    except DependencyError as e:
                        logger.warning(f"Could not inject {param_name}: {e}")
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


class Injectable:
    """
    Base class that provides automatic dependency injection for subclasses.
    Eliminates manual dependency management in constructors.
    """
    
    def __init__(self, **kwargs):
        """Initialize with automatic dependency injection."""
        container = get_container()
        
        # Get constructor signature
        sig = inspect.signature(self.__class__.__init__)
        
        # Inject dependencies for parameters not provided
        for param_name, param in sig.parameters.items():
            if param_name in ['self', 'kwargs']:
                continue
                
            if param_name not in kwargs:
                try:
                    # Try to resolve by parameter name
                    kwargs[param_name] = container.get(param_name)
                except DependencyError:
                    # Try to resolve by type annotation
                    if param.annotation != param.empty:
                        try:
                            if param.annotation in container._interfaces:
                                kwargs[param_name] = container.get_interface(param.annotation)
                            else:
                                type_name = getattr(param.annotation, '__name__', str(param.annotation))
                                kwargs[param_name] = container.get(type_name.lower())
                        except DependencyError:
                            if param.default == param.empty:
                                logger.warning(f"Could not inject required dependency: {param_name}")
        
        # Set injected dependencies as instance attributes
        for name, value in kwargs.items():
            setattr(self, name, value)


# Service registration decorators
def singleton(name: Optional[str] = None):
    """
    Decorator to register a class as a singleton service.
    
    Args:
        name: Optional service name (defaults to lowercase class name)
    """
    ProductionAssert.not_none(name, 'name')

    ProductionAssert.not_none(name, 'name')

    def decorator(cls):
        service_name = name or cls.__name__.lower()
        instance = cls()
        get_container().register_singleton(service_name, instance)
        return cls
    return decorator


def service(name: Optional[str] = None):
    """
    Decorator to register a class as a transient service.
    
    Args:
        name: Optional service name (defaults to lowercase class name)
    """


    ProductionAssert.not_none(name, 'name')



    ProductionAssert.not_none(name, 'name')

    def decorator(cls):
        service_name = name or cls.__name__.lower()
        get_container().register_type(service_name, cls)
        return cls
    return decorator


def factory(name: str):
    """
    Decorator to register a function as a service factory.
    
    Args:
        name: Service name
    """


    ProductionAssert.not_none(name, 'name')



    ProductionAssert.not_none(name, 'name')

    def decorator(func):

        ProductionAssert.not_none(func, 'func')

        ProductionAssert.not_none(func, 'func')

        get_container().register_factory(name, func)
        return func
    return decorator


# Context manager for scoped containers
class ContainerScope:
    """
    Context manager that creates a scoped container for testing
    or isolated operations.
    """
    
    def __init__(self):
        self.original_container = None
        self.scoped_container = None
    
    def __enter__(self) -> Container:
        global _container
        self.original_container = _container
        self.scoped_container = Container()
        _container = self.scoped_container
        _setup_default_services()
        return self.scoped_container
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        global _container
        _container = self.original_container


# Utility functions for common patterns
def resolve(service_name: str) -> Any:
    """Resolve a service by name."""
    return get_container().get(service_name)


def resolve_interface(interface: Type[T]) -> T:
    """Resolve a service by interface type."""
    return get_container().get_interface(interface)