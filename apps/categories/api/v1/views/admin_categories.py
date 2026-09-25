"""
Admin views for Category CRUD.
GET    (all) — already exists via CategoryListView
POST   /api/v1/categories/admin/          — create
PATCH  /api/v1/categories/admin/{id}/     — update
DELETE /api/v1/categories/admin/{id}/     — soft-delete (is_active=False)
"""
from django.core.cache import cache
from rest_framework import generics, serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.categories.models import Category
from apps.common.permissions import IsSuperAdminOrReadOnly

CATEGORY_LIST_CACHE_KEY = "categories:active:list"


class AdminCategorySerializer(serializers.ModelSerializer):
    """
    Serializer scoped to fields that actually exist on the Category model.
    (The public CategorySerializer references icon/color/parent/children
    which may not exist in this project's migration state.)
    """

    class Meta:
        model = Category
        fields = (
            "id",
            "name",
            "slug",
            "description",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "slug", "created_at", "updated_at")


class AdminCategoryListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/v1/categories/admin/   — list all categories (including inactive)
    POST /api/v1/categories/admin/   — create new category
    """

    permission_classes = [IsSuperAdminOrReadOnly]
    serializer_class = AdminCategorySerializer

    def get_queryset(self):
        return Category.objects.all()

    def perform_create(self, serializer):
        serializer.save()
        cache.delete(CATEGORY_LIST_CACHE_KEY)


class AdminCategoryDetailView(APIView):
    """
    GET    /api/v1/categories/admin/{id}/   — retrieve single
    PATCH  /api/v1/categories/admin/{id}/   — partial update
    DELETE /api/v1/categories/admin/{id}/   — soft-delete (is_active=False)
    """

    permission_classes = [IsSuperAdminOrReadOnly]

    def _get_obj(self, pk):
        try:
            return Category.objects.get(pk=pk)
        except Category.DoesNotExist:
            return None

    def get(self, request, pk):
        obj = self._get_obj(pk)
        if obj is None:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(AdminCategorySerializer(obj).data)

    def patch(self, request, pk):
        obj = self._get_obj(pk)
        if obj is None:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = AdminCategorySerializer(obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        cache.delete(CATEGORY_LIST_CACHE_KEY)
        return Response(serializer.data)

    def delete(self, request, pk):
        obj = self._get_obj(pk)
        if obj is None:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        obj.is_active = False
        obj.save(update_fields=["is_active"])
        cache.delete(CATEGORY_LIST_CACHE_KEY)
        return Response(status=status.HTTP_204_NO_CONTENT)
