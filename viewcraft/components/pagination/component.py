from typing import List, Optional

from django.db.models import QuerySet

from viewcraft import Component, URLMixin
from viewcraft.exceptions import ViewcraftError
from viewcraft.types import ViewT

from .config import PaginationConfig
from .exceptions import InvalidPageError


class PaginationComponent(Component[ViewT], URLMixin):
    """Handles pagination of querysets."""

    def __init__(self, view: ViewT, config: PaginationConfig) -> None:
        super().__init__(view)
        self.config = config
        self._total_count: Optional[int] = None
        self._current_page: Optional[int] = None

    def process_get_queryset(self, queryset: QuerySet) -> QuerySet:
        page = self._get_page_number()
        self._total_count = queryset.count()
        if page > self._get_total_pages():
            raise InvalidPageError(f"Page {page} does not exist")
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
        if self._current_page is None:
            try:
                page = int(self._view.request.GET.get(self.config.page_param, 1))
                if page < 1:
                    raise InvalidPageError("Page numbers must be positive")
                self._current_page = page
            except ValueError:
                raise InvalidPageError("Invalid page number") from ViewcraftError
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
        visible = self.config.visible_pages

        # Calculate the range of pages to show
        half = visible // 2
        start = max(current - half, 1)
        end = min(start + visible - 1, total)

        # Adjust start if we're near the end
        if end - start + 1 < visible:
            start = max(end - visible + 1, 1)

        return list(range(start, end + 1))

    def _get_page_urls(self) -> dict:
        """Generate URLs for pagination navigation."""
        urls = {}
        current = self._get_page_number()
        total = self._get_total_pages()

        # First and last
        urls['first'] = (
            self.get_url_with_params({self.config.page_param: 1})
            if current > 1
            else None
        )
        urls['last'] = (
            self.get_url_with_params({self.config.page_param: total})
            if current < total
            else None
        )

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
        }  # type: ignore

        return urls
