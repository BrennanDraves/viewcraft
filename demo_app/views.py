from django.views.generic import ListView

from demo_app.models import BlogPost
from viewcraft import ComponentMixin, PaginationConfig, FilterConfig, SearchConfig, SearchFieldSpec, MatchType

class BlogListView(ComponentMixin, ListView):
    model = BlogPost
    template_name = 'demo_app/list.html'
    components = [
        SearchConfig(
            fields=[
                SearchFieldSpec(
                    field_name='title',
                    label='Post Title',
                    match_types=[
                        MatchType.CONTAINS,
                        MatchType.EXACT,
                        MatchType.STARTSWITH
                    ],
                    default_match_type=MatchType.CONTAINS,
                    case_sensitive=False,
                    weight=2.0  # Higher weight for title in relevance scoring
                ),
                SearchFieldSpec(
                    field_name='body',
                    label='Content',
                    match_types=[MatchType.CONTAINS, MatchType.ICONTAINS],
                    default_match_type=MatchType.ICONTAINS
                ),
                SearchFieldSpec(
                    field_name='status',
                    match_types=[MatchType.EXACT, MatchType.IN],
                    default_match_type=MatchType.EXACT
                ),
                SearchFieldSpec(
                    field_name='category',
                    match_types=[MatchType.EXACT, MatchType.IN],
                    default_match_type=MatchType.EXACT
                ),
                SearchFieldSpec(
                    field_name='published_at',
                    label='Publication Date',
                    match_types=[
                        MatchType.EXACT,
                        MatchType.GT,
                        MatchType.LT,
                        MatchType.BETWEEN
                    ],
                    default_match_type=MatchType.GT
                ),
                SearchFieldSpec(
                    field_name='view_count',
                    label='Views',
                    match_types=[
                        MatchType.GT,
                        MatchType.LT,
                        MatchType.BETWEEN
                    ],
                    default_match_type=MatchType.GT
                ),
            ],
            global_search_enabled=True,
            global_search_fields=['title', 'body', 'category', 'tags'],
            case_sensitive=False,
            auto_wildcards=True,
            min_length=2,
            param_name='q'
        ),

        PaginationConfig(
            per_page=5,
            visible_pages=3,
            max_pages=None
        ),
        FilterConfig(
            fields={
                'status': ['draft', 'published', 'archived'],
                'category': ['Technology', 'Travel', 'Food', 'Science']
            }
        ),
    ]
