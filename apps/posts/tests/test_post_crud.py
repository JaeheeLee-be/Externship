from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.core.utils.test_factories import create_test_user
from apps.posts.models import Post, PostCategory


class PostListCreateViewCreateTest(APITestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = create_test_user("author")
        self.category = PostCategory.objects.create(name="자유")
        self.url = reverse("post_list_create")

    def test_create_post_success(self) -> None:
        self.client.force_authenticate(user=self.user)
        payload = {
            "category_id": self.category.id,
            "title": "첫 글",
            "content": "내용입니다",
        }

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("detail", response.data)
        self.assertIn("pk", response.data)
        self.assertEqual(Post.objects.count(), 1)
        post = Post.objects.first()
        assert post is not None
        self.assertEqual(response.data["pk"], post.id)
        self.assertEqual(post.author, self.user)

    def test_create_post_missing_required_field(self) -> None:
        self.client.force_authenticate(user=self.user)
        payload = {"title": "제목만 있음"}

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error_detail", response.data)
        self.assertIn("content", response.data["error_detail"])
        self.assertEqual(Post.objects.count(), 0)

    def test_create_post_unauthenticated_unauthorized(self) -> None:
        payload = {
            "category_id": self.category.id,
            "title": "비로그인 글",
            "content": "내용입니다",
        }

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Post.objects.count(), 0)


class PostListCreateViewListTest(APITestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.author = create_test_user("author")
        self.category = PostCategory.objects.create(name="자유")
        self.older_post = Post.objects.create(
            author=self.author,
            category=self.category,
            title="첫 번째 글",
            content="첫 번째 내용",
        )
        self.newer_post = Post.objects.create(
            author=self.author,
            category=self.category,
            title="두 번째 글",
            content="두 번째 내용",
        )
        self.url = reverse("post_list_create")

    def test_list_posts_success(self) -> None:
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)
        self.assertEqual(len(response.data["results"]), 2)
        self.assertEqual(response.data["results"][0]["id"], self.newer_post.id)
        self.assertEqual(response.data["results"][1]["id"], self.older_post.id)


class PostDetailViewPutTest(APITestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.author = create_test_user("author")
        self.other = create_test_user("other")
        self.category = PostCategory.objects.create(name="자유")
        self.new_category = PostCategory.objects.create(name="공지")
        self.post = Post.objects.create(
            author=self.author,
            category=self.category,
            title="원본 제목",
            content="원본 내용",
        )
        self.url = reverse("post_detail", kwargs={"post_id": self.post.id})
        self.payload = {
            "title": "수정된 제목",
            "content": "수정된 내용",
            "category_id": self.new_category.id,
        }

    def test_update_post_success(self) -> None:
        self.client.force_authenticate(user=self.author)

        response = self.client.put(self.url, self.payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "수정된 제목")
        self.assertEqual(response.data["content"], "수정된 내용")
        self.assertEqual(response.data["category_id"], self.new_category.id)
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, "수정된 제목")

    def test_update_post_not_author_forbidden(self) -> None:
        self.client.force_authenticate(user=self.other)

        response = self.client.put(self.url, self.payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIsInstance(response.data["error_detail"], str)
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, "원본 제목")

    def test_update_post_unauthenticated_unauthorized(self) -> None:
        response = self.client.put(self.url, self.payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, "원본 제목")

    def test_update_post_not_found(self) -> None:
        self.client.force_authenticate(user=self.author)
        url = reverse("post_detail", kwargs={"post_id": 99999})

        response = self.client.put(url, self.payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error_detail"], "해당 게시글을 찾을 수 없습니다.")


class PostDetailViewTest(APITestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.author = create_test_user("author")
        self.category = PostCategory.objects.create(name="자유")
        self.post = Post.objects.create(
            author=self.author,
            category=self.category,
            title="상세 글",
            content="상세 내용",
        )
        self.url = reverse("post_detail", kwargs={"post_id": self.post.id})

    def test_get_post_detail_success(self) -> None:
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.post.id)
        self.assertEqual(response.data["title"], "상세 글")
        self.assertEqual(response.data["author"]["id"], self.author.id)
        self.assertEqual(response.data["author"]["nickname"], self.author.nickname)
        self.assertEqual(response.data["category"]["id"], self.category.id)
        self.assertEqual(response.data["category"]["name"], self.category.name)
        self.assertEqual(response.data["like_count"], 0)
        self.assertEqual(response.data["comment_count"], 0)

    def test_get_post_detail_not_found(self) -> None:
        url = reverse("post_detail", kwargs={"post_id": 99999})

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error_detail"], "해당 게시글을 찾을 수 없습니다.")


class PostDetailViewDeleteTest(APITestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.author = create_test_user("author")
        self.other = create_test_user("other")
        self.category = PostCategory.objects.create(name="자유")
        self.post = Post.objects.create(
            author=self.author,
            category=self.category,
            title="삭제될 글",
            content="내용",
        )
        self.url = reverse("post_detail", kwargs={"post_id": self.post.id})

    def test_delete_post_success(self) -> None:
        self.client.force_authenticate(user=self.author)

        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("detail", response.data)
        self.assertEqual(Post.objects.count(), 0)

    def test_delete_post_not_author_forbidden(self) -> None:
        self.client.force_authenticate(user=self.other)

        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Post.objects.count(), 1)

    def test_delete_post_unauthenticated_unauthorized(self) -> None:
        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Post.objects.count(), 1)

    def test_delete_post_not_found(self) -> None:
        self.client.force_authenticate(user=self.author)
        url = reverse("post_detail", kwargs={"post_id": 99999})

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error_detail"], "해당 게시글을 찾을 수 없습니다.")
