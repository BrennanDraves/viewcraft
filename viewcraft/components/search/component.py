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
            field_label = spec.field_name.replace('_', ' ').title()

            # Create the main search field
            self.fields[spec.field_name] = forms.CharField(
                required=False,
                label=field_label
            )

            # Add lookup type selection field if multiple types are available
            if len(spec.lookup_types) > 1:
                lookup_choices = [
                    (lt, lt.replace('_', ' ').title()) for lt in spec.lookup_types
                ]
                self.fields[f"{spec.field_name}_lookup"] = forms.ChoiceField(
                    choices=lookup_choices,
                    required=False,
                    initial=spec.current_lookup_type,
                    label=f"{field_label} Match Type"
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

        # Process lookup type selections first
        for key, value in search_params.items():
            if key.endswith('_lookup'):
                field_name = key.replace('_lookup', '')
                for spec in self.config.specs:
                    if spec.field_name == field_name and value in spec.lookup_types:
                        spec.set_lookup_type(value)

        # Build a complex Q object for all specified search conditions
        filter_q = None

        for spec in self.config.specs:
            value = search_params.get(spec.field_name)
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
            Dict[str, Any]: Decoded search parameters including lookup types
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
            query_data = json.loads(unquoted)

            # Process parameters and lookup types
            field_names = [spec.field_name for spec in self.config.specs]

            # Extract values and lookup types
            for k, v in query_data.items():
                # Regular search field value
                if k in field_names:
                    params[k] = v
                # Lookup type parameter
                elif k.endswith('_lookup'):
                    field_name = k.replace('_lookup', '')
                    if field_name in field_names:
                        params[k] = v  # Include it in the returned params
                        # Find the corresponding spec and update its current lookup type
                        for spec in self.config.specs:
                            if spec.field_name == field_name and v in spec.lookup_types:
                                spec.current_lookup_type = v
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

            # Create a dictionary for the form's initial data
            initial_data = {}

            if form_data:
                # Copy the regular search values
                for key, value in form_data.items():
                    initial_data[key] = value

                # Add lookup type selections based on the current state of specs
                for spec in self.config.specs:
                    lookup_field = f"{spec.field_name}_lookup"
                    # Only set the lookup field's initial value if not already in
                    if lookup_field not in initial_data and spec.current_lookup_type:
                        initial_data[lookup_field] = spec.current_lookup_type

            # Create form with specs from config
            self._search_form = SearchForm(
                data=initial_data if initial_data else None,
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
        Generate a URL with base64 encoded search parameters including lookup types.

        Args:
            params: Search parameters to encode

        Returns:
            str: URL with encoded search parameters
        """
        # Filter out empty values and invalid fields
        field_names = [spec.field_name for spec in self.config.specs]
        filtered_params = {}

        # Process regular field values
        for k, v in params.items():
            if not v:
                continue

            # Handle regular field values
            if k in field_names:
                filtered_params[k] = v
            # Handle lookup type selections
            elif k.endswith('_lookup') and k.replace('_lookup', '') in field_names:
                field_name = k.replace('_lookup', '')
                # Find the corresponding spec and validate the lookup type
                for spec in self.config.specs:
                    if spec.field_name == field_name and v in spec.lookup_types:
                        filtered_params[k] = v
                        # Update the current lookup type in the spec
                        spec.set_lookup_type(v)

        if not filtered_params:
            return self.get_url_with_params({self.config.param_name: None})

        # Convert to JSON and then encode as URL-safe base64
        json_params = json.dumps(filtered_params)
        encoded = base64.urlsafe_b64encode(json_params.encode('utf-8')).decode('utf-8')

        return self.get_url_with_params({self.config.param_name: encoded})
