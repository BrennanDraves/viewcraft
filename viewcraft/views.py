from functools import wraps
from typing import Any, Callable, ClassVar

from .components import Component, ComponentConfig
from .enums import HookType, ViewMethod


def wrap_method_with_hooks(
    view: "ComponentMixin",
    method_name: str,
    original_method: Callable[..., Any]
) -> Callable[..., Any]:
    """Wrap a view method with pre/around/post hooks from components.

    Args:
        view: The view instance
        method_name: Name of the method being wrapped
        original_method: The original view method

    Returns:
        A wrapped version of the method that executes component hooks
    """
    try:
        view_method = ViewMethod(method_name)
    except ValueError:
        # Not a hookable method, return unchanged
        return original_method

    @wraps(original_method)
    def wrapped(*args: Any, **kwargs: Any) -> Any:
        # Get all components that have hooks for this method
        hooked_components = [
            comp for comp in view._components
            if view_method in comp._hooks
        ]

        # Sort components by sequence number
        hooked_components.sort(
            key=lambda c: getattr(c, 'sequence', 0)
        )

        result = None

        # Execute pre hooks
        for component in hooked_components:
            for hook in component._hooks[view_method]:
                if any(h.hook_type == HookType.PRE for h in hook._hooks):
                    result = hook(*args, **kwargs)
                    if result is not None:
                        args = (result,) + args[1:]

        # Execute around hooks or original
        around_executed = False
        for component in hooked_components:
            for hook in component._hooks[view_method]:
                if any(h.hook_type == HookType.AROUND for h in hook._hooks):
                    result = hook(*args, **kwargs)
                    around_executed = True
                    break
            if around_executed:
                break

        if not around_executed:
            result = original_method(*args, **kwargs)

        # Execute post hooks
        for component in hooked_components:
            for hook in component._hooks[view_method]:
                if any(h.hook_type == HookType.POST for h in hook._hooks):
                    post_result = hook(result, *args[1:], **kwargs)  # type: ignore
                    if post_result is not None:
                        result = post_result

        return result

    return wrapped

class ComponentMixin:
    """Mixin that adds component support to views.

    To use, define a components class variable with a list of ComponentConfigs:

    class MyView(ComponentMixin, ListView):
        components = [
            PaginationConfig(per_page=20),
            SearchConfig(fields=['name']),
        ]
    """

    components: ClassVar[list[ComponentConfig]] = []

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        # Initialize parent classes first
        super().__init__(*args, **kwargs)  # type: ignore

        # Initialize components
        self._components: list[Component] = []
        for config in self.components:
            component = config.build_component(self)  # type: ignore
            self._components.append(component)  # type: ignore

        # Sort components by sequence number
        self._components.sort(key=lambda c: getattr(c, 'sequence', 0))

        # Wrap methods that might have hooks
        self._wrap_methods()

    def _wrap_methods(self) -> None:
        """Find all methods that might have hooks and wrap them."""
        for method_name in [m.value for m in ViewMethod]:
            if hasattr(self, method_name):
                original_method = getattr(self, method_name)
                if callable(original_method):
                    wrapped = wrap_method_with_hooks(
                        self, method_name, original_method
                    )
                    setattr(self, method_name, wrapped)
