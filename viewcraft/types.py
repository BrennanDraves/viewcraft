from typing import TYPE_CHECKING, Any, Protocol, TypeVar

from django.views import View
from typing_extensions import TypeVarTuple

if TYPE_CHECKING:
    from .components.hooks import HookMetadata

ViewT = TypeVar("ViewT", bound=View)
ModelT = TypeVar("ModelT")
Ts = TypeVarTuple('Ts')

class HookedCallable(Protocol):
    """Protocol for methods that have been decorated with hooks."""
    _hooks: list["HookMetadata"]
    def __call__(self, *args: tuple[*Ts], **kwargs: Any) -> Any: ...

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
