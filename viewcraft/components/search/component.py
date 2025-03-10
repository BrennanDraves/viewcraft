"""
Search component implementation for viewcraft.

Provides a component for filtering querysets based on user search criteria,
with support for different match types and field-specific searching.
"""

import base64
import json
from typing import TYPE_CHECKING, Any, Dict, Optional
from urllib.parse import unquote

from django.db.models import Q, QuerySet
from django.forms import (
    CharField,
    ChoiceField,
    Form,
    RadioSelect,
)

from viewcraft.components import Component
from viewcraft.types import ViewT
from viewcraft.utils import URLMixin

from .exceptions import SearchEncodingError

if TYPE_CHECKING:
    from .config import SearchConfig, SearchFieldSpec


class SearchComponent(Component[ViewT], URLMixin):
    """
    Component for searching and filtering querysets.

    Provides search functionality with support for different match types,
    field-specific searching, and global search across multiple fields.
    """
    # Set sequence to run before other filters
    _sequence = -100

    def __init__(self, view: ViewT, config: "SearchConfig") -> None:
        super().__init__(view)
        self.config = config
        self._search_form: Optional[Form] = None
        self._search_params: Optional[Dict[str, Any]] = None

    def process_get_queryset(self, queryset: QuerySet) -> QuerySet:
        """
        Filter the queryset based on search parameters.

        Applies search filters to the queryset based on the decoded search parameters.

        Args:
            queryset: The original queryset from the view

        Returns:
            QuerySet: The filtered queryset
        """
        params = self._get_search_params()
        if not params:
            return queryset

        search_q = Q()

        # Handle field-specific searches
        for field_spec in self.config.fields:
            field_name = field_spec.field_name
            if field_name not in params:
                continue

            field_params = params[field_name]
            if not field_params:
                continue

            # Extract match type and value
            match_type = field_params.get('match_type')
            value = field_params.get('value')

            if not match_type or value is None:
                continue

            # Create field query
            field_q = self._create_field_query(field_spec, match_type, value)
            if field_q:
                search_q &= field_q

        if search_q:
            queryset = queryset.filter(search_q).distinct()

        return queryset

    def process_get_context_data(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add search form and parameters to the template context.

        Args:
            context: The original context from the view

        Returns:
            Dict[str, Any]: The updated context
        """
        context['search_form'] = self._get_search_form()
        context['search_params'] = self._get_search_params()
        context['search_encoded'] = self._view.request.GET.get(
            self.config.param_name, ''
        )
        context['search_url'] = self.get_search_url()

        return context

    def get_search_url(self, search_params: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate a URL with the encoded search parameters.

        Args:
            search_params: Search parameters to encode (uses current params if None)

        Returns:
            str: URL with encoded search parameters
        """
        params = (
            search_params if search_params is not None
            else self._get_search_params()
        )

        if not params:
            return self.get_url_with_params({self.config.param_name: None})

        try:
            encoded = self._encode_search_params(params)
            return self.get_url_with_params({self.config.param_name: encoded})
        except Exception as e:
            raise SearchEncodingError(f"Failed to generate search URL: {str(e)}") from e

    def _get_search_params(self) -> Dict[str, Any]:
        """
        Get the decoded search parameters.

        Decodes the search parameters from the query string. If the parameters
        have already been decoded, returns the cached result.

        Returns:
            Dict[str, Any]: The decoded search parameters
        """
        if self._search_params is not None:
            return self._search_params

        encoded = self._view.request.GET.get(self.config.param_name, '')
        if not encoded:
            self._search_params = {}
            return {}

        try:
            self._search_params = self._decode_search_params(encoded)
            return self._search_params
        except Exception as e:
            # Log the error but don't crash
            import logging
            logging.error(f"Failed to decode search parameters: {str(e)}")
            self._search_params = {}
            return {}

    def _encode_search_params(self, params: Dict[str, Any]) -> str:
        """
        Encode search parameters for URL embedding.

        Args:
            params: Search parameters to encode

        Returns:
            str: Base64 encoded search parameters
        """
        json_data = json.dumps(params)
        return base64.urlsafe_b64encode(json_data.encode('utf-8')).decode('ascii')

    def _decode_search_params(self, encoded: str) -> Any:
        """
        Decode search parameters from URL.

        Args:
            encoded: Base64 encoded search parameters

        Returns:
            Dict[str, Any]: Decoded search parameters

        Raises:
            SearchEncodingError: If decoding fails
        """
        try:
            # URL unquote in case it was URL encoded
            encoded = unquote(encoded)
            json_data = base64.urlsafe_b64decode(
                encoded.encode('ascii')).decode('utf-8'
            )
            return json.loads(json_data)
        except Exception as e:
            raise SearchEncodingError(
                f"Failed to decode search parameters: {str(e)}"
            ) from e

    def _create_field_query(
        self,
        field_spec: "SearchFieldSpec",
        match_type: str,
        value: Any
    ) -> Optional[Q]:
        """
        Create a Q object for field-specific search.

        Args:
            field_spec: The field specification
            match_type: The match type to use
            value: The search value

        Returns:
            Optional[Q]: Q object for the search, or None if invalid
        """
        from .config import MatchType

        field_name = field_spec.field_name

        # Convert match_type string to enum
        try:
            match_enum = MatchType[match_type.upper()]
        except (KeyError, AttributeError):
            return None

        # Ensure this match type is allowed for this field
        if match_enum not in field_spec.match_types:
            return None

        # Handle case sensitivity
        case_sensitive = (
            field_spec.case_sensitive
            if field_spec.case_sensitive is not None
            else self.config.case_sensitive
        )

        # Special handling for BETWEEN
        if(
            match_enum == MatchType.BETWEEN
            and isinstance(value, list)
            and len(value) >= 2
        ):
            min_val, max_val = value[0], value[1]
            return Q(
                **{f"{field_name}__gte": min_val}) & Q(**{f"{field_name}__lte": max_val}
            )

        # Handle IN match type
        if match_enum == MatchType.IN and isinstance(value, list):
            return Q(**{f"{field_name}__in": value})

        # Handle ISNULL match type
        if match_enum == MatchType.ISNULL:
            return Q(**{f"{field_name}__isnull": bool(value)})

        # Handle text match types with case sensitivity
        if match_enum in MatchType.text_matches() and not case_sensitive:
            # Switch to case-insensitive variant if not already
            if match_enum == MatchType.CONTAINS:
                match_enum = MatchType.ICONTAINS
            elif match_enum == MatchType.STARTSWITH:
                match_enum = MatchType.ISTARTSWITH
            elif match_enum == MatchType.ENDSWITH:
                match_enum = MatchType.IENDSWITH

        # Add wildcards for text searches if configured
        if self.config.auto_wildcards and match_enum == MatchType.CONTAINS:
            if isinstance(value, str) and '*' not in value:
                value = f"*{value}*"

        # Create the lookup
        lookup = f"{field_name}__{match_enum}".lower()
        return Q(**{lookup: value})

    def _get_search_form(self) -> Form:
        """
        Get or create the search form.

        Creates a dynamic form based on the search configuration and current search
        parameters. If the form has already been created, returns the cached form.

        Returns:
            Form: The search form
        """
        if self._search_form is not None:
            return self._search_form

        from .config import MatchType

        # Create dynamic form class
        form_fields: Dict[str, Any] = {}

        for field_spec in self.config.fields:
            field_name = field_spec.field_name

            # Add match type field
            match_choices = [(str(mt), str(mt).replace('_', ' ').title())
                            for mt in field_spec.match_types]

            form_fields[f"{field_name}_match"] = ChoiceField(
                choices=match_choices,
                initial=str(field_spec.default_match_type),
                required=False,
                widget=RadioSelect(),
                label=f"{field_spec.label} Match Type"
            )

            # Add value field based on match types
            if MatchType.BETWEEN in field_spec.match_types:
                form_fields[f"{field_name}_min"] = CharField(
                    required=False,
                    label=f"{field_spec.label} Min",
                )
                form_fields[f"{field_name}_max"] = CharField(
                    required=False,
                    label=f"{field_spec.label} Max",
                )
            else:
                form_fields[field_name] = CharField(
                    required=False,
                    label=field_spec.label,
                )

        # Create the form class
        FormClass = type('SearchForm', (Form,), {'base_fields': form_fields})

        # Instantiate the form
        search_params = self._get_search_params()
        form_data = {}

        # Populate form data from search params
        if search_params:
            # Global search
            if 'global_search' in search_params:
                form_data['global'] = search_params['global_search']

            # Field-specific searches
            for field_spec in self.config.fields:
                field_name = field_spec.field_name
                field_params = search_params.get(field_name, {})

                if field_params:
                    match_type = field_params.get('match_type')
                    value = field_params.get('value')

                    if match_type:
                        form_data[f"{field_name}_match"] = match_type

                    if value is not None:
                        if isinstance(value, list) and len(value) >= 2:
                            form_data[f"{field_name}_min"] = value[0]
                            form_data[f"{field_name}_max"] = value[1]
                        else:
                            form_data[field_name] = value

        # Create the form instance
        self._search_form = FormClass(form_data or None)
        return self._search_form
