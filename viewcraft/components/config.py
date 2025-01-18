"""
Component configuration system for viewcraft.

Defines the base configuration class used to initialize and configure
components with type-safe parameters and validation.
"""

from dataclasses import dataclass

from viewcraft.types import ViewT

from .component import Component


@dataclass
class ComponentConfig:
    """
    Base configuration class for viewcraft components.

    ComponentConfig classes define the initialization parameters and validation
    rules for components. Each component type typically has its own corresponding
    config class that inherits from this base class.

    The config pattern separates component configuration from component logic,
    allowing for validation and type checking of parameters before component
    initialization.

    Example:
        >>> @dataclass
        ... class FilterConfig(ComponentConfig):
        ...     field_name: str
        ...     value: Any
        ...
        ...     def build_component(self, view: ViewT) -> Component:
        ...         return FilterComponent(view, self.field_name, self.value)

    Notes:
        - Config classes should be implemented as dataclasses
        - All configuration parameters should be type-hinted
        - Validation should be performed in build_component or __post_init__
    """

    def build_component(self, view: ViewT) -> Component:
        """
        Create and initialize a component instance using this configuration.

        This method must be implemented by subclasses to define how their
        corresponding component type should be instantiated.

        Args:
            view: The view instance that will own this component

        Returns:
            Component: A newly initialized component instance

        Raises:
            NotImplementedError: If the subclass doesn't implement this method
            ConfigurationError: If the configuration is invalid
        """
        raise NotImplementedError
