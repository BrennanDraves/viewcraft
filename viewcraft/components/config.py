from dataclasses import dataclass

from ..types import ViewT
from .component import Component


@dataclass
class ComponentConfig:
    def build_component(self, view: ViewT) -> Component:
        raise NotImplementedError
