from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .components import Component, ComponentConfig
    from .enums import HookType, ViewMethod
    from .types import ComponentProtocol, ConfigProtocol, ModelT, ViewT

# Public API
from .components import Component, ComponentConfig
from .enums import HookType, ViewMethod
from .types import ComponentProtocol, ConfigProtocol, ModelT, ViewT

# Clean namespace
del TYPE_CHECKING

__all__ = [
    'Component',
    'ComponentConfig',
    'ComponentProtocol'
    'ConfigProtocol',
    'HookType',
    'ModelT',
    'ViewMethod',
    'ViewT'
]
