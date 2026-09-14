from rest_framework import serializers

from apps.categories.models import Category


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for Category."""

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

    def get_children(self, obj):
        children_by_parent_id = self.context.get("children_by_parent_id")

        if children_by_parent_id is not None:
            children = children_by_parent_id.get(obj.id, [])
        else:
            children = obj.children.filter(is_active=True)

        return CategorySerializer(children, many=True, context=self.context).data
