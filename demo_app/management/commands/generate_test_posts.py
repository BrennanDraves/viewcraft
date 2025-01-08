"""Script to generate test blog posts for the demo project."""

import random
from datetime import timedelta
from typing import Any

from django.core.management.base import BaseCommand, CommandParser
from django.utils import timezone
from django.utils.text import slugify
from faker import Faker

from demo_app.models import BlogPost
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    """Django management command to generate test blog posts."""

    help = 'Generate test blog posts with authors'

    def add_arguments(self, parser: CommandParser) -> None:
        """Add command arguments."""
        parser.add_argument(
            '--authors',
            type=int,
            default=10,
            help='Number of authors to generate'
        )
        parser.add_argument(
            '--posts',
            type=int,
            default=50,
            help='Number of blog posts to generate'
        )

    def handle(self, *args: Any, **options: Any) -> None:
        """Execute the command."""
        author_count = options['authors']
        post_count = options['posts']
        fake = Faker()

        self.stdout.write("Generating test authors and blog posts...")
        width = 40  # Progress bar width

        # Track statistics
        stats = {
            'authors_created': 0,
            'posts_created': 0,
            'posts_by_status': {'draft': 0, 'published': 0, 'archived': 0},
            'posts_by_category': {}
        }

        # Create authors
        authors = []
        for i in range(author_count):
            username = f"{fake.user_name()}_{i}"[:30]
            author = User.objects.create_user(
                username=username,
                email=fake.email(),
                password='testpass123'
            )
            authors.append(author)
            stats['authors_created'] += 1

        # Categories for posts
        categories = ['Technology', 'Travel', 'Food', 'Science', 'Art', 'Music']

        # Create posts
        for i in range(post_count):
            # Generate realistic dates within the last year
            created = timezone.now() - timedelta(days=random.randint(0, 365))

            status = random.choices(
                ['draft', 'published', 'archived'],
                weights=[0.2, 0.7, 0.1],  # Mostly published
                k=1
            )[0]

            category = random.choice(categories)
            title = fake.sentence(nb_words=6)[:-1]  # Remove trailing period

            post = BlogPost.objects.create(
                title=title,
                slug=slugify(title),
                body='\n\n'.join(fake.paragraphs(nb=random.randint(3, 7))),
                author=random.choice(authors),
                status=status,
                category=category,
                tags=','.join(fake.words(nb=random.randint(2, 5))),
                view_count=random.randint(0, 1000),
                likes=random.randint(0, 500),
                created_at=created,
                published_at=created if status == 'published' else None
            )

            # Update statistics
            stats['posts_created'] += 1
            stats['posts_by_status'][status] += 1
            stats['posts_by_category'][category] = \
                stats['posts_by_category'].get(category, 0) + 1

            # Update progress bar
            progress = stats['posts_created'] / post_count
            filled = int(width * progress)
            bar = '=' * filled + '-' * (width - filled)
            percentage = int(progress * 100)

            self.stdout.write(
                f"\r[{bar}] {percentage}% | {stats['posts_created']}/{post_count} posts created",
                ending=''
            )
            self.stdout.flush()

        # Print final report
        self.stdout.write('\n')  # New line after progress bar
        self.stdout.write(
            self.style.SUCCESS(
                f"\nSuccessfully created test data:"
                f"\n - Authors created: {stats['authors_created']}"
                f"\n - Total posts: {stats['posts_created']}"
                f"\n - Posts by status:"
            )
        )
        for status, count in stats['posts_by_status'].items():
            self.stdout.write(f"   - {status}: {count}")

        self.stdout.write("\n - Posts by category:")
        for category, count in stats['posts_by_category'].items():
            self.stdout.write(f"   - {category}: {count}")
