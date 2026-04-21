from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.posts.models import Post, PostCategory

User = get_user_model()


class PostCreateViewTest(APITestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = User.objects.create_user(username="author", password="pw1234")
        self.category = PostCategory.objects.create(name="자유")
        self.url = reverse("create_post")

    def test_create_post_success(self) -> None:
        self.client.force_authenticate(user=self.user)
        payload = {
            "category": self.category.id,
            "title": "첫 글",
            "content": "내용입니다",
        }

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["title"], "첫 글")
        self.assertEqual(Post.objects.count(), 1)
        post = Post.objects.first()
        assert post is not None
        self.assertEqual(post.author, self.user)

    def test_create_post_missing_required_field(self) -> None:
        self.client.force_authenticate(user=self.user)
        payload = {"title": "제목만 있음"}

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Post.objects.count(), 0)


class PostUpdateViewTest(APITestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.author = User.objects.create_user(username="author", password="pw1234")
        self.other = User.objects.create_user(username="other", password="pw1234")
        self.category = PostCategory.objects.create(name="자유")
        self.post = Post.objects.create(
            author=self.author,
            category=self.category,
            title="원본 제목",
            content="원본 내용",
        )
        self.url = reverse("update_post", kwargs={"post_id": self.post.id})

    def test_update_post_success(self) -> None:
        self.client.force_authenticate(user=self.author)
        payload = {"title": "수정된 제목"}

        response = self.client.patch(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "수정된 제목")
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, "수정된 제목")

    def test_update_post_not_author_forbidden(self) -> None:
        self.client.force_authenticate(user=self.other)
        payload = {"title": "남이 수정"}

        response = self.client.patch(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, "원본 제목")


class PostDeleteViewTest(APITestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.author = User.objects.create_user(username="author", password="pw1234")
        self.other = User.objects.create_user(username="other", password="pw1234")
        self.category = PostCategory.objects.create(name="자유")
        self.post = Post.objects.create(
            author=self.author,
            category=self.category,
            title="삭제될 글",
            content="내용",
        )
        self.url = reverse("delete_post", kwargs={"post_id": self.post.id})

    def test_delete_post_success(self) -> None:
        self.client.force_authenticate(user=self.author)

        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Post.objects.count(), 0)

    def test_delete_post_not_author_forbidden(self) -> None:
        self.client.force_authenticate(user=self.other)

        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Post.objects.count(), 1)
