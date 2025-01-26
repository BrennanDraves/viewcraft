import pytest
from django import forms
from django.db.models import Q
from django.test import RequestFactory
from django.views.generic import ListView
from viewcraft import ComponentMixin
from viewcraft.components.search import (
    SearchConfig,
    SearchComponent,
    SearchFieldConfig,
    SearchOperator,
    SearchForm
)
from demo_app.models import BlogPost

@pytest.fixture
def search_fields():
    return [
        SearchFieldConfig(
            name='title',
            alias='title',
            operators={SearchOperator.CONTAINS, SearchOperator.EXACT}
        ),
        SearchFieldConfig(
            name='status',
            alias='status',
            operators={SearchOperator.EXACT, SearchOperator.IN}
        ),
        SearchFieldConfig(
            name='view_count',
            alias='views',
            operators={SearchOperator.GT, SearchOperator.LT},
            field_class=forms.IntegerField
        )
    ]

@pytest.fixture
def search_config(search_fields):
    return SearchConfig(fields=search_fields)

@pytest.fixture
def search_view(search_config, rf):
    class TestView(ComponentMixin, ListView):
        model = BlogPost
        template_name = 'blog/list.html'
        components = [search_config]

        def get_queryset(self):
            return super().get_queryset().order_by('id')

        def get_context_data(self, **kwargs):
            if not hasattr(self, 'object_list'):
                self.object_list = self.get_queryset()
            return super().get_context_data(**kwargs)

    view = TestView()
    view.setup(rf.get('/'))
    return view

def test_basic_search(search_view, blog_posts):
    """Test basic search functionality with a single term."""
    request = RequestFactory().get('/?q=title:contains:Python')
    search_view.setup(request)

    queryset = search_view.get_queryset()
    assert str(queryset.query).find("title") >= 0

def test_multiple_search_terms(search_view, blog_posts):
    """Test searching with multiple terms."""
    query = 'title:contains:Python,status:exact:published'
    request = RequestFactory().get(f'/?q={query}')
    search_view.setup(request)

    queryset = search_view.get_queryset()
    query_str = str(queryset.query)
    assert 'title' in query_str and 'status' in query_str

def test_invalid_field(search_view, blog_posts):
    """Test that invalid fields are ignored."""
    request = RequestFactory().get('/?q=nonexistent:contains:test')
    search_view.setup(request)

    queryset = search_view.get_queryset()
    assert str(queryset.query) == str(BlogPost.objects.all().query)

def test_invalid_operator(search_view, blog_posts):
    """Test that invalid operators are ignored."""
    request = RequestFactory().get('/?q=title:invalid:test')
    search_view.setup(request)

    queryset = search_view.get_queryset()
    assert str(queryset.query) == str(BlogPost.objects.all().query)

def test_numeric_field_validation(search_view, blog_posts):
    """Test validation of numeric fields."""
    # Valid numeric query
    request = RequestFactory().get('/?q=views:gt:100')
    search_view.setup(request)
    queryset = search_view.get_queryset()
    assert "view_count\" > 100" in str(queryset.query)

    # Reset component state
    search_view._initialized_components = None

    # Invalid numeric value
    request = RequestFactory().get('/?q=views:gt:invalid')
    search_view.setup(request)
    queryset = search_view.get_queryset()
    assert str(queryset.query) == str(BlogPost.objects.all().query)

def test_search_form_generation(search_view):
    """Test that search form is correctly generated."""
    search_view.object_list = search_view.get_queryset()
    context = search_view.get_context_data()
    assert 'search' in context
    assert isinstance(context['search']['form'], SearchForm)

    form = context['search']['form']
    assert 'title' in form.fields
    assert 'status' in form.fields
    assert 'views' in form.fields

def test_operator_field_generation(search_view):
    """Test that operator fields are generated when multiple operators exist."""
    search_view.object_list = search_view.get_queryset()
    context = search_view.get_context_data()
    form = context['search']['form']

    assert 'title_operator' in form.fields
    assert 'status_operator' in form.fields
    assert isinstance(form.fields['title_operator'], forms.ChoiceField)

def test_form_initial_values(search_view):
    """Test that form is populated with initial values from query."""
    query = 'title:contains:Python'
    request = RequestFactory().get(f'/?q={query}')
    search_view.setup(request)

    search_view.object_list = search_view.get_queryset()
    context = search_view.get_context_data()
    form = context['search']['form']
    assert form.initial.get('title') == 'Python'
    assert form.initial.get('title_operator') == 'contains'

def test_malformed_query_handling(search_view, blog_posts):
    """Test handling of malformed queries."""
    malformed_queries = [
        'title',  # Missing operator and value
        'title:',  # Missing value
        'title:contains',  # Missing value
        ':contains:value',  # Missing field
        'title:contains:value:extra',  # Too many parts
    ]

    for query in malformed_queries:
        request = RequestFactory().get(f'/?q={query}')
        search_view.setup(request)
        queryset = search_view.get_queryset()
        assert str(queryset.query) == str(BlogPost.objects.all().query)

def test_quoted_values(search_view, blog_posts):
    """Test handling of quoted search values."""
    request = RequestFactory().get('/?q=title:contains:"Multiple Words"')
    search_view.setup(request)

    queryset = search_view.get_queryset()
    assert 'title' in str(queryset.query)

def test_special_characters(search_view, blog_posts):
    """Test handling of special characters in search values."""
    special_chars = ['&', '|', '(', ')', '[', ']', '{', '}', '*', '?', '+', '.']

    for char in special_chars:
        request = RequestFactory().get(f'/?q=title:contains:test{char}value')
        search_view.setup(request)
        queryset = search_view.get_queryset()
        # Should not raise any exceptions

def test_max_query_length(search_view, blog_posts):
    """Test enforcement of max query length."""
    long_query = 'title:contains:' + 'a' * 1000
    request = RequestFactory().get(f'/?q={long_query}')
    search_view.setup(request)

    queryset = search_view.get_queryset()
    assert str(queryset.query) == str(BlogPost.objects.all().query)

def test_in_operator(search_view, blog_posts):
    """Test the IN operator for multiple values."""
    request = RequestFactory().get('/?q=status:in:[published,draft]')
    search_view.setup(request)

    queryset = search_view.get_queryset()
    assert 'IN (' in str(queryset.query)

def test_url_generation(search_view):
    """Test search URL generation with updates."""
    component = search_view._initialized_components[0]
    assert isinstance(component, SearchComponent)

    # Test adding a search term
    url = component.get_search_url(title='Python')
    assert 'q=title%3APython' in url

    # Test updating existing term
    url = component.get_search_url(title='Django')
    assert 'q=title%3ADjango' in url

    # Test removing a term
    url = component.get_search_url(title='')
    assert 'title' not in url
