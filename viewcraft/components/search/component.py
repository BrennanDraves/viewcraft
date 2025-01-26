import shlex
from typing import TYPE_CHECKING, List, Optional, Tuple
from urllib.parse import urlencode

from django.db.models import Q, QuerySet

from viewcraft.types import ViewT
from viewcraft.utils import URLMixin

from ..component import Component
from .field import SearchFieldConfig, SearchOperator
from .form import SearchForm

if TYPE_CHECKING:
    from .config import SearchConfig

class SearchComponent(Component[ViewT], URLMixin):
    """Handles complex field-based searching."""

    def __init__(self, view: ViewT, config: "SearchConfig") -> None:
        super().__init__(view)
        self.config = config
        for field in config.fields:
            field._view = view
        self._field_map = {field.alias: field for field in config.fields}
        self._parsed_query: Optional[
            List[Tuple[SearchFieldConfig, str, SearchOperator]]
        ] = None

    def process_get_queryset(self, queryset: QuerySet) -> QuerySet:
        """Apply search filtering to the queryset."""
        query = self._parse_query()
        if not query:
            return queryset

        q_objects = Q()
        for field, value, operator in query:
            q_objects &= field.get_query_lookup(value, operator)

        return queryset.filter(q_objects)

    def _parse_query(self) -> List[Tuple[SearchFieldConfig, str, SearchOperator]]:
        if self._parsed_query is not None:
            return self._parsed_query

        query_str = self._view.request.GET.get(self.config.param_name, '')
        if not query_str or len(query_str) > self.config.max_query_length:
            return []

        parsed = []
        for term in shlex.split(query_str):
            if ':' not in term:
                continue

            parts = term.split(':')
            if len(parts) not in (2, 3):
                continue

            field_alias = parts[0].strip()
            field_config = self._field_map.get(field_alias)
            if not field_config:
                continue

            if len(parts) == 2:
                operator = SearchOperator.CONTAINS
                value = parts[1]
            else:
                try:
                    operator = SearchOperator(parts[1])
                    value = parts[2]
                except ValueError:
                    continue

            if operator not in field_config.operators:
                continue

            # Handle IN operator lists
            if operator == SearchOperator.IN and value.startswith('[') and value.endswith(']'):
                value = [v.strip() for v in value[1:-1].split(',')]

            # Validate value type
            try:
                if isinstance(value, list):
                    cleaned_value = [field_config.field_class().clean(v) for v in value]
                else:
                    cleaned_value = field_config.field_class().clean(value)
            except Exception:
                continue

            parsed.append((field_config, cleaned_value, operator))

        self._parsed_query = parsed
        return parsed

    def get_form(self) -> SearchForm:
        """Get initialized search form."""
        initial = {}
        for field_config, value, operator in self._parse_query():
            initial[field_config.alias] = value
            if len(field_config.operators) > 1:
                initial[f"{field_config.alias}_operator"] = operator.value

        return SearchForm(
            data=self._view.request.GET if self._view.request.GET else None,
            component=self,
            initial=initial
        )

    def process_get_context_data(self, context: dict) -> dict:
        """Add search info and form to template context."""
        context['search'] = {
            'fields': {
                field.alias: {
                    'display_text': field.display_text,
                    'operators': [op.value for op in field.operators]
                }
                for field in self.config.fields
            },
            'active_search': self._parse_query(),
            'param_name': self.config.param_name,
            'form': self.get_form()
        }
        return context

    def get_search_url(self, **updates: str) -> str:
        """Generate a search URL with updated parameters."""
        current_params = dict(self._view.request.GET.items())

        # Handle search param updates
        if updates:
            current_search = self._view.request.GET.get(self.config.param_name, '')
            search_parts = {
                part.split(':')[0]: part
                for part in current_search.split(',')
                if ':' in part
            }

            # Update or add new search terms
            for field, value in updates.items():
                if value:
                    search_parts[field] = f"{field}:{value}"
                else:
                    search_parts.pop(field, None)

            new_search = ','.join(search_parts.values())
            if new_search:
                current_params[self.config.param_name] = new_search
            else:
                current_params.pop(self.config.param_name, None)

        return f"{self._view.request.path}?{urlencode(current_params)}"
