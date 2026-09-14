from django.urls import path

from .views.categories import (
    CategoryListView,
)

app_name = "categories"

urlpatterns = [
    path("api/v1/categories/", CategoryListView.as_view(), name="category-list"),
]
