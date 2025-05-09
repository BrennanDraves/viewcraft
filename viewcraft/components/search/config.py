from dataclasses import dataclass, field
from typing import List, Optional, Type

from django.db import models

from viewcraft.exceptions import ConfigurationError
from viewcraft.types import ViewT

from ..config import ComponentConfig
from .component import BasicSearchComponent
from .spec import SearchSpec


@dataclass
class BasicSearchConfig(ComponentConfig):
    """
    Configuration for enhanced search component with field-specific lookups.

    Attributes:
        specs: List of search specifications
        param_name: URL parameter name for the encoded search query
        model: Optional model to auto-generate specs from
        combine_method: How to combine conditions ('OR' or 'AND')
    """
    specs: List[SearchSpec] = field(default_factory=list)
    param_name: str = 'q'
    model: Optional[Type[models.Model]] = None
    combine_method: str = 'OR'  # 'OR' or 'AND'

    def __post_init__(self) -> None:
        """
        Validate configuration and auto-generate specs from model if needed.

        Raises:
            ConfigurationError: If configuration is invalid
        """
        if not self.specs and not self.model:
            raise ConfigurationError("Either specs or model must be provided")

        # Validate combine_method
        if self.combine_method not in ('OR', 'AND'):
            raise ConfigurationError("combine_method must be 'OR' or 'AND'")

        # Auto-generate specs from model if not provided
        if not self.specs and self.model:
            self._auto_generate_specs()

    def _auto_generate_specs(self) -> None:
        """
        Auto-generate search specs from model fields.

        Creates a spec with icontains lookup for each text field.
        """
        if not self.model:
            return

        for f in self.model._meta.fields:
            # For now, only include CharField and TextField
            if isinstance(f, (models.CharField, models.TextField)):
                self.specs.append(SearchSpec(f.name, 'icontains'))

    def build_component(self, view: ViewT) -> BasicSearchComponent:
        """
        Create a search component instance from this configuration.

        Args:
            view: The view instance

        Returns:
            SearchComponent: Initialized search component

        Raises:
            ConfigurationError: If no searchable specs are available
        """
        if not self.specs:
            raise ConfigurationError("No searchable fields available")

        return BasicSearchComponent(view, self)
