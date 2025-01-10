from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .types import ComponentProtocol, ViewT

from .views import ComponentMixin

# API exports
from .types import ComponentProtocol, ViewT
from .views import ComponentMixin
from .components import ComponentConfig, BaseComponent

# Cleanup namespace
del(TYPE_CHECKING)


__all__ = ['ComponentProtocol', 'ViewT', 'ComponentMixin', 'ComponentConfig', 'BaseComponent']
