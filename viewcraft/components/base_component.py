from inspect import getmembers, ismethod
from typing import Generic, cast

from ..enums import ViewMethod
from ..types import HookedCallable, ViewT


class Component(Generic[ViewT]):
    """Base class for all view components.

    Components provide modular functionality to views by hooking into view methods
    and modifying their behavior.

    Args:
        view: The view instance this component is attached to
    """

    def __init__(self, view: ViewT) -> None:
        self.view = view
        self._hooks: dict[ViewMethod, list[HookedCallable]] = {}
        self._register_hooks()

    def _register_hooks(self) -> None:
        """Register all decorated hook methods on this component.

        This method is called during initialization and sets up all the hook
        decorators that were applied to methods on this component.
        """
        # Find all methods that have been decorated with hooks
        for _, method in getmembers(self, predicate=ismethod):
            if hasattr(method, '_hooks'):
                hooked_method = cast(HookedCallable, method)

                # Register each hook on this method
                for hook in hooked_method._hooks:
                    if hook.view_method not in self._hooks:
                        self._hooks[hook.view_method] = []
                    self._hooks[hook.view_method].append(hooked_method)

                # Sort hooks by type (pre -> around -> post)
                self._hooks[hook.view_method].sort(
                    key=lambda m: [
                        h.hook_type.value for h in m._hooks
                    ][0]
                )
