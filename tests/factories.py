import factory
from django.contrib.auth import get_user_model
from django.utils import timezone

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
        skip_postgeneration_save = True

    title = factory.Sequence(lambda n: f'Blog Post {n}')
    slug = factory.Sequence(lambda n: f'blog-post-{n}')
    body = factory.Faker('paragraph', nb_sentences=5)
    author = factory.SubFactory(UserFactory)
    status = factory.Iterator(['draft', 'published', 'archived'])
    category = factory.Iterator(['Technology', 'Travel', 'Food', 'Science'])
    tags = factory.LazyFunction(lambda: ','.join(factory.Faker._get_faker().words(nb=3)))
    view_count = factory.Faker('random_int', min=0, max=1000)
    likes = factory.Faker('random_int', min=0, max=500)
    published_at = factory.LazyFunction(timezone.now)
