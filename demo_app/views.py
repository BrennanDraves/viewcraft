from django.views.generic import ListView

from demo_app.models import BlogPost

from viewcraft import ComponentMixin, PaginationConfig, PaginationComponent

class BlogListView(ComponentMixin, ListView):
    model = BlogPost
    template_name = 'demo_app/list.html'
    components = [
        PaginationConfig(
            per_page=5,
            visible_pages=3,
            max_pages=None  # No limit
        )
    ]
