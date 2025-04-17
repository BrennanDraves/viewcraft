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
    Basic search component that filters a queryset based on form input.

    Provides a simple search form with exact match filtering on specified fields.
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
        """Add search form to the context."""
        context['search_form'] = self._get_search_form()
        return context

    def _get_search_form(self) -> SearchForm:
        """Get or create the search form."""
        if self._search_form is None:
            # Get search parameters from request
            form_data = {}
            for field in self.config.fields:
                value = self._view.request.GET.get(field, '')
                if value:
                    form_data[field] = value

            # Create form with fields from config
            self._search_form = SearchForm(
                data=form_data if form_data else None,
                fields=self.config.fields
            )

        return self._search_form

    def _get_search_params(self) -> Dict[str, Any]:
        """Get search parameters from the request."""
        if self._search_params is None:
            params = {}
            for field in self.config.fields:
                value = self._view.request.GET.get(field, '')
                if value:
                    params[field] = value

            self._search_params = params

        return self._search_params

    def get_search_url(self, params: Dict[str, Any]) -> str:
        """Generate a URL with the given search parameters."""
        return self.get_url_with_params(params)
