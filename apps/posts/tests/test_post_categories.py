from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.posts.models import PostCategory


class PostCategoryListTest(APITestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.url = reverse("post_category_list")

    def test_list_categories_returns_200(self) -> None:
        PostCategory.objects.create(name="전체")

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_categories_response_shape(self) -> None:
        category = PostCategory.objects.create(name="전체")

        response = self.client.get(self.url)

        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0], {"id": category.id, "name": "전체"})

    def test_list_categories_returns_all(self) -> None:
        names = ["전체", "인기글", "공지사항"]
        for name in names:
            PostCategory.objects.create(name=name)

        response = self.client.get(self.url)

        self.assertEqual(len(response.data), 3)
