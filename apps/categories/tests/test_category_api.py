import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.categories.models import Category
from apps.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


def get_client(user=None):
    client = APIClient()
    if user:
        client.force_authenticate(user=user)
    return client


class TestCategoryListAPI:
    def test_authenticated_user_can_list_active_categories(self):
        user = UserFactory()
        cat1 = Category.objects.create(name="Cardiology", slug="cardio", is_active=True)
        Category.objects.create(name="Inactive Spec", slug="inactive", is_active=False)

        client = get_client(user)
        url = reverse("categories:category-list")

        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        # Check that it returns active category with compatible fields
        results = response.data.get("results", response.data)
        assert len(results) == 1
        item = results[0]
        assert item["id"] == str(cat1.id)
        assert item["name"] == "Cardiology"
        assert item["slug"] == "cardio"
        assert item["icon"] is None
        assert item["color"] is None
        assert item["parent"] is None
        assert item["children"] == []
        assert item["is_active"] is True

    def test_unauthenticated_user_cannot_list_categories(self):
        client = get_client()
        url = reverse("categories:category-list")

        response = client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
