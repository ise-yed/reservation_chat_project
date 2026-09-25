"""
Admin API views for User management.
Accessible by: staff, org_admin, super_admin, Django superusers.
"""
from rest_framework import filters, generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.permissions import IsSuperAdminUser
from apps.users.api.v1.serializers.admin_users import (
    AdminUserCreateSerializer,
    AdminUserReadSerializer,
    AdminUserWriteSerializer,
)
from apps.users.models import User


class AdminUserListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/v1/admin/users/          — list + search + filter
    POST /api/v1/admin/users/          — create a new user directly
    """

    permission_classes = [IsSuperAdminUser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["email", "first_name", "last_name", "phone_number"]
    ordering_fields = ["email", "role", "created_at", "is_active"]
    ordering = ["-created_at"]

    def get_queryset(self):
        qs = User.objects.all()
        role = self.request.query_params.get("role")
        is_active = self.request.query_params.get("is_active")
        is_verified = self.request.query_params.get("is_verified")
        if role:
            qs = qs.filter(role=role)
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() == "true")
        if is_verified is not None:
            qs = qs.filter(is_verified=is_verified.lower() == "true")
        return qs

    def get_serializer_class(self):
        if self.request.method == "POST":
            return AdminUserCreateSerializer
        return AdminUserReadSerializer

    def create(self, request, *args, **kwargs):
        serializer = AdminUserCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            AdminUserReadSerializer(user).data, status=status.HTTP_201_CREATED
        )


class AdminUserDetailView(APIView):
    """
    GET   /api/v1/admin/users/{id}/   — retrieve single user
    PATCH /api/v1/admin/users/{id}/   — update role / is_active / is_verified
    """

    permission_classes = [IsSuperAdminUser]

    def _get_user(self, pk):
        try:
            return User.objects.get(pk=pk)
        except User.DoesNotExist:
            return None

    def get(self, request, pk):
        user = self._get_user(pk)
        if user is None:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(AdminUserReadSerializer(user).data)

    def patch(self, request, pk):
        user = self._get_user(pk)
        if user is None:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = AdminUserWriteSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(AdminUserReadSerializer(user).data)
