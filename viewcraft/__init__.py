from typing import TYPE_CHECKING

from .enums import HookMethod, HookPhase

# Cleanup namespaces
del TYPE_CHECKING

__all__ = [
    "HookMethod",
    "HookPhase",
]
