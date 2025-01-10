"""Base configuration class for viewcraft components."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from viewcraft import ComponentProtocol, ViewT


@dataclass
class ComponentConfig:
    """Base configuration class for components."""

    def build_component(self, view: "ViewT") -> "ComponentProtocol":
        """Build and return a component instance for the given view."""
        raise NotImplementedError
