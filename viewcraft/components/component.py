from typing import Callable, Generic

from viewcraft.enums import HookMethod, HookPhase

from ..types import ViewT


class Component(Generic[ViewT]):
    _sequence: int = 0
    _hooks: dict[HookMethod, list[tuple[HookPhase, Callable]]]
    _view: ViewT

    def __init__(self, view: ViewT) -> None:
        self._view = view
