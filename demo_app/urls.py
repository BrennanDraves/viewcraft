from django.urls import path, include

from demo_app import views

urlpatterns = [
    path('', views.BlogListView.as_view(), name='index'),
]
