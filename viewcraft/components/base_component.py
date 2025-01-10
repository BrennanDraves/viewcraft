from typing import Generic

from ..types import ViewT


class Component(Generic[ViewT]):
    """Base class for all view components.

    Components provide modular functionality to views by hooking into view methods
    and modifying their behavior.

    Args:
        view: The view instance this component is attached to
    """

    def __init__(self, view: "ViewT") -> None:
        self.view = view
        self._register_hooks()

    def _register_hooks(self) -> None:
        """Register all decorated hook methods on this component.

        This method is called during initialization and sets up all the hook
        decorators that were applied to methods on this component.
        """
        # To be implemented once we define our hook decorators
        pass
