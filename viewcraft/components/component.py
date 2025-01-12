from typing import Any, Callable, Dict, Generic, Optional

from viewcraft.enums import HookMethod
from viewcraft.types import ViewT


class Component(Generic[ViewT]):
    _sequence: int = 0  # Lower is executed earlier.
    _view: ViewT

    def __init__(self, view: ViewT) -> None:
        self._view = view
        self._hook_data: Dict[str, Any] = {}

    def get_pre_hook(self, hook: HookMethod) -> Optional[Callable]:
        """Get pre hook if it exists. Pre hooks can return early."""
        method_name = f"pre_{hook.value}"
        return getattr(self, method_name, None)

    def get_process_hook(self, hook: HookMethod) -> Optional[Callable]:
        """Get process hook if it exists. Process hooks modify the result."""
        method_name = f"process_{hook.value}"
        return getattr(self, method_name, None)

    def get_post_hook(self, hook: HookMethod) -> Optional[Callable]:
        """Get post hook if it exists. Post hooks are for cleanup."""
        method_name = f"post_{hook.value}"
        return getattr(self, method_name, None)
