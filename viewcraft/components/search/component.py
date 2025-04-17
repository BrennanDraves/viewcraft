import binascii
from typing import TYPE_CHECKING, Any, Dict, Optional
import json
import base64
from urllib.parse import unquote, quote

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
    Search component that uses a base64 encoded JSON query parameter for cleaner URLs.

    This component handles search queries by encoding them as base64 strings:
    ?q=eyJ0aXRsZSI6IlRlc3QiLCJjYXRlZ29yeSI6IlRlY2hub2xvZ3kifQ==

    It requires the included JavaScript snippet to be included in the template
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
            if value and field in self.config.fields:  # Only add non-empty values for valid fields
                filter_q &= Q(**{field: value})

        if filter_q:
            return queryset.filter(filter_q)
        return queryset

    def process_get_context_data(self, context: dict) -> dict:
        """Add search form and param name to the context."""
        context['search_form'] = self._get_search_form()
        context['search_param_name'] = self.config.param_name
        return context

    def _decode_base64_query(self) -> Dict[str, Any]:
        """Decode a base64 encoded search query into parameters."""
        params: Dict[str, Any] = {}
        encoded_query = self._view.request.GET.get(self.config.param_name, '')

        if not encoded_query:
            return params

        try:
            # First handle URL encoding of the base64 string
            encoded_query = encoded_query.replace('%3D', '=')
            # Decode from base64 and parse as JSON
            decoded = base64.urlsafe_b64decode(encoded_query).decode('utf-8')
            unquoted = unquote(decoded)  # Handle URL encoding
            params = json.loads(unquoted)

            # Filter to only include valid fields
            params = {k: v for k, v in params.items() if k in self.config.fields}
        except (ValueError, json.JSONDecodeError, binascii.Error):
            # If decoding fails, fall back to empty params
            return {}

        return params

    def _get_search_form(self) -> SearchForm:
        """Get or create the search form with values from decoded query."""
        if self._search_form is None:
            # Get values from encoded query
            form_data = self._get_search_params()

            # Create form with fields from config
            self._search_form = SearchForm(
                data=form_data if form_data else None,
                fields=self.config.fields
            )

        return self._search_form

    def _get_search_params(self) -> Dict[str, Any]:
        """Get search parameters from the encoded query."""
        if self._search_params is None:
            self._search_params = self._decode_base64_query()
        return self._search_params

    def get_encoded_search_url(self, params: Dict[str, Any]) -> str:
        """Generate a URL with base64 encoded search parameters."""
        # Filter out empty values and invalid fields
        filtered_params = {
            k: v for k, v in params.items()
            if v and k in self.config.fields
        }

        if not filtered_params:
            return self.get_url_with_params({self.config.param_name: None})

        # Convert to JSON and then encode as URL-safe base64
        json_params = json.dumps(filtered_params)
        encoded = base64.urlsafe_b64encode(json_params.encode('utf-8')).decode('utf-8')

        return self.get_url_with_params({self.config.param_name: encoded})
