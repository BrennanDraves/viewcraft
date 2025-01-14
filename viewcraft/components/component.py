from typing import Any, Callable, Dict, Generic, Optional

from viewcraft.enums import HookMethod
from viewcraft.exceptions import HookError
from viewcraft.types import ViewT


class Component(Generic[ViewT]):
    _sequence: int = 0  # Lower is executed earlier.
    _view: ViewT

    def __init__(self, view: ViewT) -> None:
        self._view = view
        self._hook_data: Dict[str, Any] = {}

    def get_pre_hook(self, hook: HookMethod) -> Optional[Callable]:
        """Get pre hook if it exists. Pre hooks can return early."""
        try:
            method_name = f"pre_{hook.value}"
            return getattr(self, method_name, None)
        except AttributeError as e:
            raise HookError(f"Invalid pre-hook {method_name}: {str(e)}") from e

    def get_process_hook(self, hook: HookMethod) -> Optional[Callable]:
        """Get process hook if it exists. Process hooks modify the result."""
        try:
            method_name = f"process_{hook.value}"
            return getattr(self, method_name, None)
        except AttributeError as e:
            raise HookError(f"Invalid process-hook {method_name}: {str(e)}") from e

    def get_post_hook(self, hook: HookMethod) -> Optional[Callable]:
        """Get post hook if it exists. Post hooks are for cleanup."""
        try:
            method_name = f"post_{hook.value}"
            return getattr(self, method_name, None)
        except AttributeError as e:
            raise HookError(f"Invalid post-hook {method_name}: {str(e)}") from e
