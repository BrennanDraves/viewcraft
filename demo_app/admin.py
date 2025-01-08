from django.contrib import admin
from demo_app.models import BlogPost

@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    # Display all fields.
    list_display = ('title', 'slug', 'author', 'status', 'category', 'tags', 'view_count', 'likes', 'created_at', 'updated_at', 'published_at')
