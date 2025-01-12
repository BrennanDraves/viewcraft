from dataclasses import dataclass

from viewcraft.types import ViewT

from .component import Component


@dataclass
class ComponentConfig:
    def build_component(self, view: ViewT) -> Component:
        raise NotImplementedError
