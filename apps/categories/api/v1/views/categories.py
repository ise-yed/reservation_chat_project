from collections import defaultdict

from django.core.cache import cache
from rest_framework import filters, generics, permissions

from apps.categories.models import Category

from ..serializers import CategorySerializer

CATEGORY_LIST_CACHE_KEY = "categories:active:list"
CATEGORY_LIST_CACHE_TIMEOUT = 60 * 60


class CategoryListView(generics.ListAPIView):
    """List all active categories."""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CategorySerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "description"]
    ordering_fields = ["name", "created_at"]
    ordering = ["name"]

    def get_queryset(self):
        if self.request.query_params:
            return Category.objects.filter(is_active=True)

        cached_ids = cache.get(CATEGORY_LIST_CACHE_KEY)

        if cached_ids is not None:
            return Category.objects.filter(id__in=cached_ids, is_active=True)

        queryset = list(Category.objects.filter(is_active=True))
        cache.set(
            CATEGORY_LIST_CACHE_KEY,
            [category.id for category in queryset],
            timeout=CATEGORY_LIST_CACHE_TIMEOUT,
        )
        return queryset

    def get_serializer_context(self):
        context = super().get_serializer_context()

        all_active = Category.objects.filter(is_active=True).only("id", "parent_id")

        children_by_parent_id = defaultdict(list)
        for category in all_active:
            if category.parent_id is not None:
                children_by_parent_id[category.parent_id].append(category)

        context["children_by_parent_id"] = children_by_parent_id
        return context