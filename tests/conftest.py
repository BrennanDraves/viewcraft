import pytest
from django.views.generic import ListView
from viewcraft import ComponentMixin
from demo_app.models import BlogPost
from .factories import BlogPostFactory, UserFactory

@pytest.fixture
def user():
    return UserFactory()

@pytest.fixture
def blog_posts(db):
    return [BlogPostFactory() for _ in range(5)]

@pytest.fixture
def basic_view_class():
    """A basic view class for testing components."""
    class TestView(ComponentMixin, ListView):
        model = BlogPost
        template_name = 'blog/list.html'
    return TestView

@pytest.fixture
def basic_view(rf, basic_view_class):
    """An instantiated view for testing."""
    request = rf.get('/')
    view = basic_view_class()
    view.setup(request, args=[], kwargs={})  # Call setup explicitly
    view.request = request
    view.args = []
    view.kwargs = {}
    return view
