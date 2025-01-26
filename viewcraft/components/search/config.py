from dataclasses import dataclass
from typing import List, Optional, Type

from django.db.models import Model

from viewcraft.types import ViewT

from ..config import ComponentConfig
from .component import SearchComponent
from .field import SearchFieldConfig


@dataclass
class SearchConfig(ComponentConfig):
    """Configuration for search component."""
    fields: List[SearchFieldConfig]
    model: Optional[Type[Model]] = None  # Optional model to query against
    param_name: str = 'q'
    max_query_length: int = 1000
    case_sensitive: bool = False

    def build_component(self, view: ViewT) -> SearchComponent:
        return SearchComponent(view, self)
