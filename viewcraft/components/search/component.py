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
        self._search_form: Optional[forms.Form] = None
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
            # Skip if no value for this field
            value = search_params.get(spec.field_name)
            if not value:
                continue

            # Special handling for ranges
            if spec.supports_range():
                # Get end value from parameters
                end_value = search_params.get(f"{spec.field_name}_end")
                if end_value:
                    # Create a range condition
                    range_q = Q(**{f"{spec.field_name}__gte": value}) & \
                              Q(**{f"{spec.field_name}__lte": end_value})

                    if filter_q is None:
                        filter_q = range_q
                    else:
                        # Combine based on the specified method
                        if self.config.combine_method == 'OR':
                            filter_q |= range_q
                        else:  # 'AND'
                            filter_q &= range_q
                    continue

            # Standard field handling
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
                # Range end value
                elif k.endswith('_end'):
                    field_name = k.replace('_end', '')
                    if field_name in field_names:
                        params[k] = v
        except Exception:
            # If decoding fails for any reason, fall back to empty params
            return {}

        return params

    def _get_search_form(self) -> forms.Form:
        """
        Get or create the search form with values from decoded query.

        Returns:
            forms.Form: Initialized search form with appropriate fields
        """
        if self._search_form is None:
            # Get values from encoded query
            form_data = self._get_search_params()

            # Create a dictionary of fields dynamically
            fields = {}

            # Generate fields for each search spec
            for spec in self.config.specs:
                field_name = spec.field_name

                # Get the model field if we have a model
                if self.config.model:
                    try:
                        model_field = self.config.model._meta.get_field(field_name)

                        # Special handling for fields with choices
                        if hasattr(model_field, 'choices') and model_field.choices:
                            choices = [('', '---------')] + list(model_field.choices)
                            form_field: Any = forms.ChoiceField(
                                choices=choices,
                                required=False,
                                label=field_name.replace('_', ' ').title()
                            )
                        else:
                            # Let Django create the appropriate form field
                            form_field = model_field.formfield(  # type: ignore
                                required=False,
                                label=field_name.replace('_', ' ').title()
                            )

                            # Add appropriate widget attributes based on field type
                            if isinstance(form_field, forms.DateField):
                                form_field.widget.attrs.update({'type': 'date'})
                            elif isinstance(form_field, (
                                forms.IntegerField, forms.DecimalField, forms.FloatField
                            )):
                                form_field.widget.attrs.update({'type': 'number'})

                        # Store the field
                        fields[field_name] = form_field

                        # If this field supports ranges, add a second field for the end
                        if spec.supports_range():
                            # Check if the field has a formfield method
                            if hasattr(model_field, 'formfield'):
                                end_field = model_field.formfield(
                                    required=False,
                                    label="",  # Empty label - template will handle
                                )
                            else:
                                # Fallback for fields without formfield method
                                end_field = forms.CharField(
                                    required=False,
                                    label=""
                                )

                            # Add appropriate widget attributes
                            if isinstance(end_field, forms.DateField):
                                end_field.widget.attrs.update({
                                    'type': 'date',
                                    'class': 'range-end',
                                    'data-field': field_name
                                })
                            elif isinstance(end_field, (
                                forms.IntegerField, forms.DecimalField, forms.FloatField
                            )):
                                end_field.widget.attrs.update({
                                    'type': 'number',
                                    'class': 'range-end',
                                    'data-field': field_name
                                })

                            fields[f"{field_name}_end"] = end_field

                    except Exception:
                        # Fallback to basic CharField if model field lookup fails
                        fields[field_name] = forms.CharField(
                            required=False,
                            label=field_name.replace('_', ' ').title()
                        )
                else:
                    # No model available, create basic field based on field_type
                    if spec.field_type == 'BooleanField':
                        fields[field_name] = forms.BooleanField(
                            required=False,
                            label=field_name.replace('_', ' ').title()
                        )
                    elif spec.field_type == 'DateField':
                        fields[field_name] = forms.DateField(
                            required=False,
                            label=field_name.replace('_', ' ').title(),
                            widget=forms.DateInput(attrs={'type': 'date'})
                        )
                    elif spec.field_type in (
                        'IntegerField', 'DecimalField', 'FloatField'
                    ):
                        field_class = getattr(forms, spec.field_type)
                        fields[field_name] = field_class(
                            required=False,
                            label=field_name.replace('_', ' ').title(),
                            widget=forms.NumberInput(attrs={'type': 'number'})
                        )
                    else:
                        fields[field_name] = forms.CharField(
                            required=False,
                            label=field_name.replace('_', ' ').title()
                        )

                    # Add range end field if needed
                    if spec.supports_range():
                        if spec.field_type == 'DateField':
                            fields[f"{field_name}_end"] = forms.DateField(
                                required=False,
                                label="",
                                widget=forms.DateInput(attrs={
                                    'type': 'date',
                                    'class': 'range-end',
                                    'data-field': field_name
                                })
                            )
                        elif spec.field_type in (
                            'IntegerField', 'DecimalField', 'FloatField'
                        ):
                            field_class = getattr(forms, spec.field_type)
                            fields[f"{field_name}_end"] = field_class(
                                required=False,
                                label="",
                                widget=forms.NumberInput(attrs={
                                    'type': 'number',
                                    'class': 'range-end',
                                    'data-field': field_name
                                })
                            )

                # Add lookup type selection if needed
                if len(spec.lookup_types) > 1:
                    lookup_choices = [
                        (lt, lt.replace('_', ' ').title()) for lt in spec.lookup_types
                    ]
                    fields[f"{field_name}_lookup"] = forms.ChoiceField(
                        choices=lookup_choices,
                        required=False,
                        initial=spec.current_lookup_type,
                        label=f"{field_name.replace('_', ' ').title()} Match Type"
                    )

            # Create a proper form class with our dynamically generated fields
            FormClass = type('DynamicSearchForm', (forms.Form,), fields)

            # Create form instance with initial data from the encoded query
            self._search_form = FormClass(data=form_data if form_data else None)

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
            if not v and v != False:
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
            # Handle range end values
            elif k.endswith('_end') and k.replace('_end', '') in field_names:
                field_name = k.replace('_end', '')
                # Only include end value if start value exists and this is a
                # range-supporting field
                for spec in self.config.specs:
                    if (
                        spec.field_name == field_name
                        and spec.supports_range()
                        and field_name in params
                    ):
                        filtered_params[k] = v

        if not filtered_params:
            return self.get_url_with_params({self.config.param_name: None})

        # Convert to JSON and then encode as URL-safe base64
        json_params = json.dumps(filtered_params)
        encoded = base64.urlsafe_b64encode(json_params.encode('utf-8')).decode('utf-8')

        return self.get_url_with_params({self.config.param_name: encoded})
