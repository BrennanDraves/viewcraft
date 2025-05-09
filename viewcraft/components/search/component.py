import base64
import json
from typing import TYPE_CHECKING, Any, Dict, Optional
from urllib.parse import unquote

from django import forms
from django.db.models import Q, QuerySet

from viewcraft.types import ViewT
from viewcraft.utils import URLMixin

from ..component import Component

if TYPE_CHECKING:
    from .config import BasicSearchConfig


class SearchForm(forms.Form):
    """
    Dynamic form for search fields based on SearchSpecs.

    Generates appropriate form fields for each search specification.
    """
    def __init__(self, *args, **kwargs):
        specs = kwargs.pop('specs', [])
        super().__init__(*args, **kwargs)

        # Add fields based on search specs
        for spec in specs:
            field_label = spec.field.replace('_', ' ').title()

            # Create appropriate field type based on lookup
            if spec.lookup_type in ('exact', 'in'):
                # For exact matches, could potentially use select fields
                self.fields[spec.field] = forms.CharField(
                    required=False,
                    label=field_label
                )
            else:
                # For text search fields
                self.fields[spec.field] = forms.CharField(
                    required=False,
                    label=field_label
                )


class BasicSearchComponent(Component[ViewT], URLMixin):
    """
    Enhanced search component with support for field-specific lookup types.

    Uses a base64 encoded JSON query parameter for clean URLs while
    supporting different search methods per field.
    """
    _sequence = -200

    def __init__(self, view: ViewT, config: "BasicSearchConfig") -> None:
        """
        Initialize the search component.

        Args:
            view: The view instance
            config: Search component configuration
        """
        super().__init__(view)
        self.config = config
        self._search_form: Optional[SearchForm] = None
        self._search_params: Optional[Dict[str, Any]] = None

    def process_get_queryset(self, queryset: QuerySet) -> QuerySet:
        """
        Filter the queryset based on search parameters and specs.

        Args:
            queryset: Original queryset

        Returns:
            QuerySet: Filtered queryset based on search parameters
        """
        search_params = self._get_search_params()

        if not search_params:
            return queryset

        # Build a complex Q object for all specified search conditions
        filter_q = None

        for spec in self.config.specs:
            value = search_params.get(spec.field)
            if not value:
                continue  # Skip empty values

            lookup_param = {spec.get_lookup_string(): value}

            if filter_q is None:
                filter_q = Q(**lookup_param)
            else:
                # Combine based on the specified method
                if self.config.combine_method == 'OR':
                    filter_q |= Q(**lookup_param)
                else:  # 'AND'
                    filter_q &= Q(**lookup_param)

        if filter_q:
            return queryset.filter(filter_q)
        return queryset

    def process_get_context_data(self, context: dict) -> dict:
        """
        Add search form and parameters to the context.

        Args:
            context: Original template context

        Returns:
            dict: Enhanced context with search form and parameters
        """
        context['search_form'] = self._get_search_form()
        context['search_param_name'] = self.config.param_name
        context['search_specs'] = self.config.specs
        return context

    def _decode_base64_query(self) -> Dict[str, Any]:
        """
        Decode a base64 encoded search query into parameters.

        Returns:
            Dict[str, Any]: Decoded search parameters
        """
        params: Dict[str, Any] = {}
        encoded_query = self._view.request.GET.get(self.config.param_name, '')

        if not encoded_query:
            return params

        try:
            # Handle URL encoding of the base64 string
            encoded_query = encoded_query.replace('%3D', '=')
            # Decode from base64 and parse as JSON
            decoded = base64.urlsafe_b64decode(encoded_query).decode('utf-8')
            unquoted = unquote(decoded)  # Handle URL encoding
            params = json.loads(unquoted)

            # Filter to only include valid fields
            field_names = [spec.field for spec in self.config.specs]
            params = {k: v for k, v in params.items() if k in field_names}
        except Exception:
            # If decoding fails for any reason, fall back to empty params
            return {}

        return params

    def _get_search_form(self) -> SearchForm:
        """
        Get or create the search form with values from decoded query.

        Returns:
            SearchForm: Initialized search form
        """
        if self._search_form is None:
            # Get values from encoded query
            form_data = self._get_search_params()

            # Create form with specs from config
            self._search_form = SearchForm(
                data=form_data if form_data else None,
                specs=self.config.specs
            )

        return self._search_form

    def _get_search_params(self) -> Dict[str, Any]:
        """
        Get search parameters from the encoded query.

        Returns:
            Dict[str, Any]: Search parameters from query
        """
        if self._search_params is None:
            self._search_params = self._decode_base64_query()
        return self._search_params

    def get_encoded_search_url(self, params: Dict[str, Any]) -> str:
        """
        Generate a URL with base64 encoded search parameters.

        Args:
            params: Search parameters to encode

        Returns:
            str: URL with encoded search parameters
        """
        # Filter out empty values and invalid fields
        field_names = [spec.field for spec in self.config.specs]
        filtered_params = {
            k: v for k, v in params.items()
            if v and k in field_names
        }

        if not filtered_params:
            return self.get_url_with_params({self.config.param_name: None})

        # Convert to JSON and then encode as URL-safe base64
        json_params = json.dumps(filtered_params)
        encoded = base64.urlsafe_b64encode(json_params.encode('utf-8')).decode('utf-8')

        return self.get_url_with_params({self.config.param_name: encoded})
