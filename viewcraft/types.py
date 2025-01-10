from typing import Any, Protocol, TypeVar

from django.views import View

ViewT = TypeVar("ViewT", bound=View)
ModelT = TypeVar("ModelT")

class ComponentProtocol(Protocol[ViewT]):
    """Protocol defining the interface that all components must implement."""

    view: ViewT

    def __init__(self, view: ViewT) -> None:
        ...

class ConfigProtocol(Protocol):
    """Protocol defining the interface that all component configs must implement."""

    sequence: int

    def build_component(self, view: ViewT) -> ComponentProtocol[Any]:
        """Build and return a component instance for the given view."""
        ...
