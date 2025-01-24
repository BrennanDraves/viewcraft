from typing import TYPE_CHECKING, Dict, List, Optional, Union

from django.db.models import Q, QuerySet

from viewcraft.types import ViewT
from viewcraft.utils import URLMixin

from .. import Component

if TYPE_CHECKING:
    from .config import FilterConfig

FilterValue = Union[str, List[str]]
FilterSpec = Dict[str, List[str]]


class FilterComponent(Component[ViewT], URLMixin):
    def __init__(self, view: ViewT, config: "FilterConfig") -> None:
        super().__init__(view)
        self.config = config
        self._parsed_filters: Optional[Dict[str, FilterValue]] = None

    def process_get_queryset(self, queryset: QuerySet) -> QuerySet:
        filters = self._parse_filters()
        if not filters:
            return queryset

        filter_q = Q()
        for field, value in filters.items():
            if isinstance(value, list):
                filter_q &= Q(**{f"{field}__in": value})
            else:
                filter_q &= Q(**{field: value})

        return queryset.filter(filter_q)

    def _parse_filters(self) -> Dict[str, FilterValue]:
        if self._parsed_filters is not None:
            return self._parsed_filters

        filter_str = self._view.request.GET.get(self.config.param_name, '')
        if not filter_str:
            return {}

        filters: Dict[str, FilterValue] = {}
        for filter_part in filter_str.split(','):
            if ':' not in filter_part:
                continue

            field, value = filter_part.split(':', 1)
            if field not in self.config.fields:
                continue

            if value.startswith('[') and value.endswith(']'):
                # Handle multiple values: field:[val1,val2]
                values = [v.strip() for v in value[1:-1].split(',')]
                filters[field] = values
            else:
                filters[field] = value

        self._parsed_filters = filters
        return filters
