from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from ..types import ViewT

if TYPE_CHECKING:
    from viewcraft import ComponentProtocol

@dataclass
class ComponentConfig:
    """Base configuration class for view components.

    All component configurations should inherit from this class.
    """
    sequence: int = 0

    def build_component(self, view: ViewT) -> "ComponentProtocol[Any]":
        """Build and return a component instance for the given view.

        This method should be overridden by subclasses to return their specific
        component type.

        Args:
            view: The view instance this component will be attached to

        Returns:
            An instance of the component
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement build_component()"
        )
