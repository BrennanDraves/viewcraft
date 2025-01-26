from django.views.generic import ListView

from demo_app.models import BlogPost
from viewcraft import ComponentMixin, PaginationConfig, FilterConfig, SearchConfig, SearchFieldConfig, SearchOperator

class BlogListView(ComponentMixin, ListView):
    model = BlogPost
    template_name = 'demo_app/list.html'
    components = [
        SearchConfig(
            fields=[
                SearchFieldConfig(
                    name='title',
                    alias='title',
                    display_text='Title',
                    operators={SearchOperator.CONTAINS, SearchOperator.EXACT}
                ),
                SearchFieldConfig(
                    name='body',
                    alias='content',
                    display_text='Content',
                    operators={SearchOperator.CONTAINS}
                ),
                SearchFieldConfig(
                    name='author__username',
                    alias='author',
                    display_text='Author',
                    operators={SearchOperator.EXACT}
                ),
                SearchFieldConfig(
                    name='view_count',
                    alias='views',
                    display_text='Views',
                    operators={SearchOperator.GT, SearchOperator.LT}
                )
            ]
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
