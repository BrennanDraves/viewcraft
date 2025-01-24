from dataclasses import dataclass
from typing import Dict, List, Union

from viewcraft.types import ViewT

from .. import ComponentConfig
from .component import FilterComponent

FilterValue = Union[str, List[str]]
FilterSpec = Dict[str, List[str]]

@dataclass
class FilterConfig(ComponentConfig):
    fields: FilterSpec
    param_name: str = 'filter'

    def build_component(self, view: ViewT) -> FilterComponent:
        return FilterComponent(view, self)
