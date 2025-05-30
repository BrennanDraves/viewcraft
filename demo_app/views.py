from django.views.generic import ListView

from demo_app.models import BlogPost
from viewcraft import ComponentMixin, PaginationConfig, FilterConfig, BasicSearchConfig, SearchSpec

class BlogListView(ComponentMixin, ListView):
    model = BlogPost
    template_name = 'demo_app/list.html'
    components = [
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
        BasicSearchConfig(specs=[
            SearchSpec(
                field_name='title',
                lookup_types=['icontains', 'contains', 'exact', 'startswith']
            ),
            SearchSpec(
                field_name='body',
                lookup_types=['icontains', 'contains', 'exact']
            ),
            SearchSpec(
                field_name='published_at',
                lookup_types=['exact', 'gt', 'lt', 'range'],
                field_type='DateField'  # Specify this is a DateField
            )
        ])
    ]
