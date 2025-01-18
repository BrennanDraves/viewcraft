"""
Core component implementation for viewcraft.

Defines the base Component class that all viewcraft components inherit from,
providing the foundation for the component system including hook management
and view interaction.
"""

from typing import Any, Callable, Dict, Generic, Optional

from viewcraft.enums import HookMethod
from viewcraft.exceptions import HookError
from viewcraft.types import ViewT


class Component(Generic[ViewT]):
    """
    Base class for all viewcraft components.

    Components are reusable pieces of view logic that can be composed together
    to build complex view behaviors. Each component can implement various hooks
    that intercept and modify view behavior at different points in the request
    lifecycle.

    Components maintain their own state through the _hook_data dictionary and
    have access to their parent view through the _view reference.

    Attributes:
        _sequence (int): Order in which the component is processed (lower is earlier)
        _view (ViewT): Reference to the parent view instance
        _hook_data (Dict[str, Any]): Storage for component-specific state

    Example:
        >>> class FilterComponent(Component):
        ...     def process_get_queryset(self, queryset):
        ...         return queryset.filter(active=True)
    """
    _sequence: int = 0
    _view: ViewT

    def __init__(self, view: ViewT) -> None:
        self._view = view
        self._hook_data: Dict[str, Any] = {}

    def get_pre_hook(self, hook: HookMethod) -> Optional[Callable]:
        """
        Retrieve the pre-execution hook for a given method if it exists.

        Pre-hooks run before the main view method and can short-circuit execution
        by returning a value.

        Args:
            hook: The hook method to look for

        Returns:
            Optional[Callable]: The pre-hook method if it exists, None otherwise

        Raises:
            HookError: If the hook method name is invalid or malformed
        """
        try:
            method_name = f"pre_{hook.value}"
            return getattr(self, method_name, None)
        except AttributeError as e:
            raise HookError(f"Invalid pre-hook {method_name}: {str(e)}") from e

    def get_process_hook(self, hook: HookMethod) -> Optional[Callable]:
        """
        Retrieve the processing hook for a given method if it exists.

        Process hooks run after the main view method and can modify its result.
        They must accept and return the appropriate type for the hooked method.

        Args:
            hook: The hook method to look for

        Returns:
            Optional[Callable]: The process hook method if it exists, None otherwise

        Raises:
            HookError: If the hook method name is invalid or malformed
        """
        try:
            method_name = f"process_{hook.value}"
            return getattr(self, method_name, None)
        except AttributeError as e:
            raise HookError(f"Invalid process-hook {method_name}: {str(e)}") from e

    def get_post_hook(self, hook: HookMethod) -> Optional[Callable]:
        """
        Retrieve the post-execution hook for a given method if it exists.

        Post-hooks run after processing is complete and are typically used
        for cleanup or logging. They cannot modify the method result.

        Args:
            hook: The hook method to look for

        Returns:
            Optional[Callable]: The post-hook method if it exists, None otherwise

        Raises:
            HookError: If the hook method name is invalid or malformed
        """
        try:
            method_name = f"post_{hook.value}"
            return getattr(self, method_name, None)
        except AttributeError as e:
            raise HookError(f"Invalid post-hook {method_name}: {str(e)}") from e
