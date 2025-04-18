from dataclasses import dataclass
from typing import Optional

from viewcraft.types import ViewT

from ..config import ComponentConfig
from .component import PaginationComponent
from .exceptions import PaginationConfigurationError


@dataclass
class PaginationConfig(ComponentConfig):
    """Configuration for pagination component."""
    per_page: int = 10
    page_param: str = 'page'
    max_pages: Optional[int] = None
    visible_pages: int = 5  # Number of page numbers to show in navigation

    def __post_init__(self) -> None:
        if self.per_page < 1:
            raise PaginationConfigurationError("per_page must be positive")
        if self.max_pages is not None and self.max_pages < 1:
            raise PaginationConfigurationError("max_pages must be positive")
        if self.visible_pages < 1:
            raise PaginationConfigurationError("visible_pages must be positive")

    def build_component(self, view: ViewT) -> PaginationComponent:
        return PaginationComponent(view, self)
