from rest_framework import serializers

from apps.categories.models import Category


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for Category."""

    icon = serializers.SerializerMethodField()
    color = serializers.SerializerMethodField()
    parent = serializers.SerializerMethodField()
    children = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = (
            "id",
            "name",
            "slug",
            "icon",
            "description",
            "color",
            "parent",
            "children",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")

    def get_icon(self, obj):
        return None

    def get_color(self, obj):
        return None

    def get_parent(self, obj):
        return None

    def get_children(self, obj):
        return []

