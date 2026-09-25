from django.urls import path

from .views.admin_categories import AdminCategoryDetailView, AdminCategoryListCreateView
from .views.categories import CategoryListView

app_name = "categories"

urlpatterns = [
    path("", CategoryListView.as_view(), name="category-list"),
    # Admin CRUD
    path("admin/", AdminCategoryListCreateView.as_view(), name="admin-list-create"),
    path("admin/<uuid:pk>/", AdminCategoryDetailView.as_view(), name="admin-detail"),
]
