from django.urls import path

from .views.categories import (
    CategoryListView,
)

app_name = "categories"

urlpatterns = [
    path("", CategoryListView.as_view(), name="category-list"),
]
