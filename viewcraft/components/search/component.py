from typing import TYPE_CHECKING, Any, Dict, Optional

from django import forms
from django.db.models import Q, QuerySet

from viewcraft.types import ViewT
from viewcraft.utils import URLMixin

from ..component import Component

if TYPE_CHECKING:
    from .config import BasicSearchConfig


class SearchForm(forms.Form):
    """Dynamic form for basic search fields."""

    def __init__(self, *args, **kwargs):
        fields = kwargs.pop('fields', [])
        super().__init__(*args, **kwargs)

        # Add a field for each searchable field
        for field_name in fields:
            self.fields[field_name] = forms.CharField(
                required=False,
                label=field_name.replace('_', ' ').title()
            )


class BasicSearchComponent(Component[ViewT], URLMixin):
    """
    Search component that uses a single encoded query parameter for cleaner URLs.

    This component handles search queries in the format:
    ?q=field1:value1,field2:value2

    It requires a small JavaScript snippet to be included in the template
    to encode form fields before submission.
    """
    _sequence = -200

    def __init__(self, view: ViewT, config: "BasicSearchConfig") -> None:
        super().__init__(view)
        self.config = config
        self._search_form: Optional[SearchForm] = None
        self._search_params: Optional[Dict[str, Any]] = None

    def process_get_queryset(self, queryset: QuerySet) -> QuerySet:
        """Filter the queryset based on search parameters."""
        search_params = self._get_search_params()

        if not search_params:
            return queryset

        # Build a Q object for filtering
        filter_q = Q()
        for field, value in search_params.items():
            if value:  # Only add non-empty values
                filter_q &= Q(**{field: value})

        if filter_q:
            return queryset.filter(filter_q)
        return queryset

    def process_get_context_data(self, context: dict) -> dict:
        """Add search form and param name to the context."""
        context['search_form'] = self._get_search_form()
        context['search_param_name'] = self.config.param_name
        return context

    def _parse_encoded_query(self) -> Dict[str, Any]:
        """Parse an encoded search query into parameters.

        Format: field1:value1,field2:value2
        """
        params: Dict[str, Any] = {}
        encoded_query = self._view.request.GET.get(self.config.param_name, '')

        if not encoded_query:
            return params

        for part in encoded_query.split(','):
            if ':' not in part:
                continue

            field, value = part.split(':', 1)
            if field in self.config.fields:
                params[field] = value

        return params

    def _get_search_form(self) -> SearchForm:
        """Get or create the search form with values from encoded query."""
        if self._search_form is None:
            # Get values from encoded query
            form_data = self._parse_encoded_query()

            # Create form with fields from config
            self._search_form = SearchForm(
                data=form_data if form_data else None,
                fields=self.config.fields
            )

        return self._search_form

    def _get_search_params(self) -> Dict[str, Any]:
        """Get search parameters from the encoded query."""
        if self._search_params is None:
            self._search_params = self._parse_encoded_query()
        return self._search_params

    def get_encoded_search_url(self, params: Dict[str, Any]) -> str:
        """Generate a URL with encoded search parameters."""
        parts = []
        for field, value in params.items():
            if value and field in self.config.fields:
                parts.append(f"{field}:{value}")

        if not parts:
            return self.get_url_with_params({self.config.param_name: None})

        encoded = ",".join(parts)
        return self.get_url_with_params({self.config.param_name: encoded})
