import factory
from django.utils import timezone
from django.contrib.auth import get_user_model
from demo_app.models import BlogPost

class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = get_user_model()

    username = factory.Sequence(lambda n: f'user_{n}')
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@example.com')
    password = factory.PostGenerationMethodCall('set_password', 'testpass123')

class BlogPostFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = BlogPost

    title = factory.Sequence(lambda n: f'Blog Post {n}')
    slug = factory.LazyAttribute(lambda obj: f'blog-post-{obj.id}' if obj.id else 'blog-post')
    body = factory.Faker('paragraph', nb_sentences=5)
    author = factory.SubFactory(UserFactory)
    status = factory.Iterator(['draft', 'published', 'archived'])
    category = factory.Iterator(['Technology', 'Travel', 'Food', 'Science'])
    tags = factory.LazyAttribute(lambda _: ','.join(factory.Faker('words', nb=3).generate({})))
    view_count = factory.Faker('random_int', min=0, max=1000)
    likes = factory.Faker('random_int', min=0, max=500)
    published_at = factory.LazyFunction(timezone.now)
