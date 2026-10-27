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

        qs = Category.objects.filter(is_active=True)
        cached_ids = list(qs.values_list("id", flat=True))
        cache.set(
            CATEGORY_LIST_CACHE_KEY,
            cached_ids,
            timeout=CATEGORY_LIST_CACHE_TIMEOUT,
        )
        return qs
