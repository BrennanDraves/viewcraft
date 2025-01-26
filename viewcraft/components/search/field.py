from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional, Set, Type

from django import forms
from django.core.exceptions import FieldDoesNotExist
from django.db.models import Q


class SearchOperator(str, Enum):
    CONTAINS = "contains"
    EXACT = "exact"
    STARTSWITH = "startswith"
    ENDSWITH = "endswith"
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"
    IN = "in"
    NOT_IN = "not_in"

    def __str__(self) -> str:
        return self.value


@dataclass
class SearchFieldConfig:
    """Configuration for a searchable field."""
    name: str  # Actual model field name
    alias: str  # URL parameter name
    display_text: Optional[str] = None  # Human readable name
    operators: Set[SearchOperator] = field(default_factory=(
        lambda: {SearchOperator.CONTAINS})
    )
    field_class: Type = forms.CharField  # Django form field class
    field_kwargs: Dict[str, Any] = field(default_factory=dict)
    _view: Any = None  # Will be set by component

    def __post_init__(self):
        if not self.display_text:
            self.display_text = self.alias.replace('_', ' ').title()

    def get_query_lookup(self, value: str, operator: SearchOperator) -> Q:
        from django.db.models.fields import Field
        from django.db.models.fields.related import RelatedField

        # Validate field name exists on model
        model_field = self._get_model_field()
        if not isinstance(model_field, (Field, RelatedField)):
            raise ValueError(f"Invalid field name: {self.name}")

        lookup = f"{self.name}__{operator}"
        return Q(**{lookup: value})

    def _get_model_field(self):
        model = self._view.model
        try:
            return model._meta.get_field(self.name)
        except FieldDoesNotExist:
            return None
