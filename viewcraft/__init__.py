from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .components import Component, ComponentConfig, around_hook, post_hook, pre_hook
    from .enums import HookType, ViewMethod
    from .types import ComponentProtocol, ConfigProtocol, ModelT, ViewT

# Public API
from .components import Component, ComponentConfig, around_hook, post_hook, pre_hook
from .enums import HookType, ViewMethod
from .types import ComponentProtocol, ConfigProtocol, ModelT, ViewT

# Clean namespace
del TYPE_CHECKING

__all__ = [
    'around_hook',
    'Component',
    'ComponentConfig',
    'ComponentProtocol'
    'ConfigProtocol',
    'HookType',
    'ModelT',
    'post_hook',
    'pre_hook',
    'ViewMethod',
    'ViewT'
]
