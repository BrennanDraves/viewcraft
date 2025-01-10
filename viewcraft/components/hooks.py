from dataclasses import dataclass
from typing import Callable, Union, cast

from ..enums import HookType, ViewMethod
from ..types import HookedCallable


@dataclass
class HookMetadata:
    """Metadata about a hook decoration on a component method."""
    view_method: ViewMethod
    hook_type: HookType
    method: HookedCallable

def _normalize_view_method(method: Union[str, ViewMethod]) -> ViewMethod:
    """Convert a string method name to a ViewMethod enum value."""
    if isinstance(method, ViewMethod):
        return method
    try:
        return ViewMethod(method)
    except ValueError:
        raise ValueError(
            f"Invalid view method name: {method}. "
            f"Must be one of: {', '.join(m.value for m in ViewMethod)}"
        ) from None

def _create_hook(hook_type: HookType) -> Callable:
    """Create a hook decorator for the given hook type."""
    def decorator(
            view_method: Union[str, ViewMethod]
        ) -> Callable[[Callable], HookedCallable]:
        def wrapper(method: Callable) -> HookedCallable:
            view_method_enum = _normalize_view_method(view_method)

            # Convert the method to our HookedCallable type
            hooked_method = cast(HookedCallable, method)

            # Store the hook metadata on the method itself
            if not hasattr(hooked_method, '_hooks'):
                hooked_method._hooks = []
            hooked_method._hooks.append(HookMetadata(
                view_method=view_method_enum,
                hook_type=hook_type,
                method=hooked_method
            ))

            return hooked_method
        return wrapper
    return decorator

# Create the three hook decorators
pre_hook = _create_hook(HookType.PRE)
around_hook = _create_hook(HookType.AROUND)
post_hook = _create_hook(HookType.POST)
