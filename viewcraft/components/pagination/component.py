from typing import TYPE_CHECKING, List, Optional

from django.core.cache import cache
from django.db.models import QuerySet

from viewcraft.types import ViewT
from viewcraft.utils import URLMixin

from ..component import Component
from .exceptions import InvalidPageError

if TYPE_CHECKING:
    from .config import PaginationConfig

class PaginationComponent(Component[ViewT], URLMixin):
    """Handles pagination of querysets."""

    def __init__(self, view: ViewT, config: "PaginationConfig") -> None:
        super().__init__(view)
        self.config = config
        self._total_count: Optional[int] = None
        self._current_page: Optional[int] = None

    def process_get_queryset(self, queryset: QuerySet) -> QuerySet:
        cache_key = f"pagination_count_{hash(str(queryset.query))}"
        self._total_count = cache.get(cache_key)

        if self._total_count is None:
            self._total_count = queryset.count()
            cache.set(cache_key, self._total_count, timeout=300)  # 5 min cache
        total_pages = self._get_total_pages()
        page = self._get_page_number()

        if page > total_pages:
            raise InvalidPageError(f"Page {page} does not exist. Last page is\
                                   {total_pages}.")

        start = (page - 1) * self.config.per_page
        end = start + self.config.per_page
        return queryset[start:end]

    def process_get_context_data(self, context: dict) -> dict:
        page = self._get_page_number()
        total_pages = self._get_total_pages()

        context['page_obj'] = {
            'number': page,
            'has_previous': page > 1,
            'has_next': page < total_pages,
            'previous_page_number': page - 1 if page > 1 else None,
            'next_page_number': page + 1 if page < total_pages else None,
            'start_index': ((page - 1) * self.config.per_page) + 1,
            'end_index': min(page * self.config.per_page, self._total_count or 0),
            'total_pages': total_pages,
            'total_count': self._total_count,
            'page_range': self._get_page_range(),
            'page_urls': self._get_page_urls()
        }
        return context

    def _get_page_number(self) -> int:
        try:
            page = int(self._view.request.GET.get(self.config.page_param, 1))
            if page < 1:
                raise InvalidPageError("Page numbers must be positive")
            self._current_page = page
        except ValueError:
            self._current_page = 1
        return self._current_page

    def _get_total_pages(self) -> int:
        if not self._total_count:
            return 1
        pages = (self._total_count + self.config.per_page - 1) // self.config.per_page
        if self.config.max_pages:
            return min(pages, self.config.max_pages)
        return pages

    def _get_page_range(self) -> List[int]:
        """Calculate visible page range centered on current page."""
        current = self._get_page_number()
        total = self._get_total_pages()
        visible = min(self.config.visible_pages, total)

        if visible <= 2:
            return list(range(1, total + 1))

        # Calculate the middle range
        left = max(1, current - (visible - 1) // 2)
        right = min(total, left + visible - 1)

        # Adjust left bound if right bound was limited
        if right == total:
            left = max(1, total - visible + 1)

        return list(range(left, right + 1))

    def _get_page_urls(self) -> dict:
        """Generate URLs for pagination navigation."""
        urls: dict = {}
        current = self._get_page_number()
        total = self._get_total_pages()

        # First and last - always provide URLs
        urls['first'] = self.get_url_with_params({self.config.page_param: 1})
        urls['last'] = self.get_url_with_params({self.config.page_param: total})

        # Previous and next
        urls['previous'] = (
            self.get_url_with_params({self.config.page_param: current - 1})
            if current > 1
            else None
        )
        urls['next'] = (
            self.get_url_with_params({self.config.page_param: current + 1})
            if current < total
            else None
        )

        # Numbered pages
        urls['pages'] = {
            page: self.get_url_with_params({self.config.page_param: page})
            for page in self._get_page_range()
        }

        return urls
