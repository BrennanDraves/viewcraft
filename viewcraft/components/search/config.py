from dataclasses import dataclass, field
from typing import Dict, List, Optional, Type

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
        default_lookup_types: Default lookup types to use for auto-generated specs
    """
    specs: List[SearchSpec] = field(default_factory=list)
    param_name: str = 'q'
    model: Optional[Type[models.Model]] = None
    combine_method: str = 'OR'  # 'OR' or 'AND'
    default_lookup_types: Dict[str, List[str]] = field(default_factory=lambda: {
        'CharField': ['contains', 'icontains', 'exact'],
        'TextField': ['contains', 'icontains', 'exact'],
        'IntegerField': ['exact', 'gt', 'lt', 'gte', 'lte', 'range'],
        'FloatField': ['exact', 'gt', 'lt', 'gte', 'lte', 'range'],
        'DecimalField': ['exact', 'gt', 'lt', 'gte', 'lte', 'range'],
        'DateField': ['exact', 'gt', 'lt', 'gte', 'lte', 'range'],
        'DateTimeField': ['exact', 'gt', 'lt', 'gte', 'lte', 'range'],
        'BooleanField': ['exact'],
        'ForeignKey': ['exact'],
        'OneToOneField': ['exact'],
        'ManyToManyField': ['exact'],
        'default': ['contains', 'exact']
    })

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

        Creates a spec with appropriate lookup types for each field type.
        """
        if not self.model:
            return

        for f in self.model._meta.fields:
            field_type = f.__class__.__name__

            # Skip some common fields we don't typically want to search on
            if f.name in ('id', 'pk', 'created_at', 'updated_at'):
                continue

            # Skip non-searchable field types
            if field_type in ('AutoField', 'OneToOneField', 'ManyToManyField'):
                continue

            # Determine which lookup types to use for this field
            lookup_types = self.default_lookup_types.get(
                field_type,
                self.default_lookup_types['default']
            )

            # Create spec
            self.specs.append(SearchSpec(
                field_name=f.name,
                lookup_types=lookup_types,
                current_lookup_type=lookup_types[0] if lookup_types else None,
                field_type=field_type
            ))

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
