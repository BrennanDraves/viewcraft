from dataclasses import dataclass, field
from typing import List, Optional, Type

from django.db import models

from viewcraft.exceptions import ConfigurationError
from viewcraft.types import ViewT

from ..config import ComponentConfig
from .component import BasicSearchComponent


@dataclass
class BasicSearchConfig(ComponentConfig):
    """Simple configuration for basic search component."""
    model: Optional[Type[models.Model]] = None
    fields: List[str] = field(default_factory=list)
    param_name: str = 'q'

    def __post_init__(self) -> None:
        """Validate configuration."""
        if not self.model and not self.fields:
            raise ConfigurationError("Either model or fields must be provided")

        # If we have a model but no fields, we'll use all text fields from the model
        if self.model and not self.fields:
            self.fields = self._get_searchable_fields()

    def _get_searchable_fields(self) -> List[str]:
        """Get all searchable (text) fields from the model."""
        if not self.model:
            return []

        fields = []
        for f in self.model._meta.fields:
            # For now, only include CharField and TextField
            if isinstance(f, (models.CharField, models.TextField)):
                fields.append(f.name)

        return fields

    def build_component(self, view: ViewT) -> BasicSearchComponent:
        """Create a search component from this configuration."""
        if not self.fields:
            raise ConfigurationError("No searchable fields available")

        return BasicSearchComponent(view, self)
