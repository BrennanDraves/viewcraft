from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .components import Component, ComponentConfig, around_hook, post_hook, pre_hook
    from .enums import HookType, ViewMethod
    from .types import ComponentProtocol, ConfigProtocol, ModelT, ViewT
    from .views import ComponentMixin

# Public API
from .components import Component, ComponentConfig, around_hook, post_hook, pre_hook
from .enums import HookType, ViewMethod
from .types import ComponentProtocol, ConfigProtocol, ModelT, ViewT
from .views import ComponentMixin

# Clean namespace
del TYPE_CHECKING

__all__ = [
    'around_hook',
    'Component',
    'ComponentConfig',
    'ComponentMixin',
    'ComponentProtocol'
    'ConfigProtocol',
    'HookType',
    'ModelT',
    'post_hook',
    'pre_hook',
    'ViewMethod',
    'ViewT'
]
