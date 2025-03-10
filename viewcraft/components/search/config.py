"""
Search component configuration for viewcraft.

Defines the configuration classes for the search component, including
field specifications and match type definitions.
"""
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, List, Optional, Type

from django.db.models import Field, Model
from django.db.models.fields import (
    BooleanField,
    CharField,
    DateField,
    DateTimeField,
    DecimalField,
    FloatField,
    IntegerField,
    TextField,
)

from viewcraft.components import ComponentConfig
from viewcraft.types import ViewT

from .component import SearchComponent
from .exceptions import SearchConfigError


class MatchType(Enum):
    """Supported match types for search fields."""
    EXACT = auto()
    CONTAINS = auto()
    ICONTAINS = auto()
    STARTSWITH = auto()
    ISTARTSWITH = auto()
    ENDSWITH = auto()
    IENDSWITH = auto()
    GT = auto()
    GTE = auto()
    LT = auto()
    LTE = auto()
    BETWEEN = auto()
    IN = auto()
    ISNULL = auto()

    @classmethod
    def text_matches(cls) -> List["MatchType"]:
        """Match types suitable for text fields."""
        return [
            cls.EXACT, cls.CONTAINS, cls.ICONTAINS,
            cls.STARTSWITH, cls.ISTARTSWITH,
            cls.ENDSWITH, cls.IENDSWITH
        ]

    @classmethod
    def numeric_matches(cls) -> List["MatchType"]:
        """Match types suitable for numeric fields."""
        return [
            cls.EXACT, cls.GT, cls.GTE, cls.LT, cls.LTE, cls.BETWEEN, cls.IN
        ]

    @classmethod
    def date_matches(cls) -> List["MatchType"]:
        """Match types suitable for date fields."""
        return [
            cls.EXACT, cls.GT, cls.GTE, cls.LT, cls.LTE, cls.BETWEEN
        ]

    @classmethod
    def boolean_matches(cls) -> List["MatchType"]:
        """Match types suitable for boolean fields."""
        return [cls.EXACT, cls.ISNULL]

    def __str__(self) -> str:
        return self.name.lower()


@dataclass
class SearchFieldSpec:
    """
    Specification for a searchable field.

    Defines how a specific model field should be searched, including
    the available match types and any special handling.
    """
    field_name: str
    label: Optional[str] = None
    match_types: List[MatchType] = field(default_factory=list)
    default_match_type: Optional[MatchType] = None
    case_sensitive: Optional[bool] = None  # None means use global setting
    weight: float = 1.0  # For relevance scoring

    def __post_init__(self) -> None:
        """Validate the field specification."""
        if not self.match_types:
            raise SearchConfigError(
                f"No match types specified for field {self.field_name}"
            )

        if self.default_match_type and self.default_match_type not in self.match_types:
            raise SearchConfigError(
                f"Default match type {self.default_match_type} not in allowed types "
                f"for field {self.field_name}"
            )

        # If no default is specified, use the first match type
        if not self.default_match_type and self.match_types:
            self.default_match_type = self.match_types[0]

        # Set label to field_name if not provided
        if not self.label:
            self.label = self.field_name.replace('_', ' ').capitalize()


@dataclass
class SearchConfig(ComponentConfig):
    """
    Configuration for the search component.

    Defines which fields are searchable, how they should be searched,
    and global settings for the search behavior.
    """
    param_name: str = 'q'
    case_sensitive: bool = False
    auto_wildcards: bool = True
    min_length: int = 2
    fields: List[SearchFieldSpec] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate the search configuration."""
        field_names = set()
        for field_spec in self.fields:
            if field_spec.field_name in field_names:
                raise SearchConfigError(
                    f"Duplicate field name: {field_spec.field_name}"
                )
            field_names.add(field_spec.field_name)

    @classmethod
    def from_model(
        cls,
        model: Type[Model],
        include_fields: Optional[List[str]] = None,
        exclude_fields: Optional[List[str]] = None,
        **kwargs: Any
    ) -> "SearchConfig":
        """
        Create a SearchConfig automatically from a Django model.

        Args:
            model: The Django model to create the config from
            include_fields: List of field names to include (if None, include all)
            exclude_fields: List of field names to exclude
            **kwargs: Additional arguments for the SearchConfig

        Returns:
            SearchConfig: A configured SearchConfig instance
        """
        exclude_fields = exclude_fields or []
        field_specs = []

        for f in model._meta.fields:
            # Skip excluded fields
            if f.name in exclude_fields:
                continue

            # Skip if include_fields is specified and this field isn't in it
            if include_fields and f.name not in include_fields:
                continue

            # Create field spec based on field type
            field_spec = cls._create_field_spec_for_field(f)
            if field_spec:
                field_specs.append(field_spec)

        return cls(fields=field_specs, **kwargs)

    @staticmethod
    def _create_field_spec_for_field(field: Field) -> Optional[SearchFieldSpec]:
        """Create a SearchFieldSpec instance for a model field."""
        # Handle text fields
        if isinstance(field, (CharField, TextField)):
            return SearchFieldSpec(
                field_name=field.name,
                match_types=MatchType.text_matches(),
                default_match_type=MatchType.ICONTAINS,
            )

        # Handle numeric fields
        elif isinstance(field, (IntegerField, FloatField, DecimalField)):
            return SearchFieldSpec(
                field_name=field.name,
                match_types=MatchType.numeric_matches(),
                default_match_type=MatchType.EXACT,
            )

        # Handle date fields
        elif isinstance(field, (DateField, DateTimeField)):
            return SearchFieldSpec(
                field_name=field.name,
                match_types=MatchType.date_matches(),
                default_match_type=MatchType.EXACT,
            )

        # Handle boolean fields
        elif isinstance(field, BooleanField):
            return SearchFieldSpec(
                field_name=field.name,
                match_types=MatchType.boolean_matches(),
                default_match_type=MatchType.EXACT,
            )

        # Skip unsupported field types
        return None

    def build_component(self, view: ViewT) -> SearchComponent:
        """Create a SearchComponent instance from this config."""
        return SearchComponent(view, self)
