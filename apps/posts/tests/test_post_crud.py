from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.posts.models import Post, PostCategory
from apps.users.models import User


_test_user_counter = 0


def create_test_user(suffix: str) -> User:
    global _test_user_counter
    _test_user_counter += 1
    return User.objects.create_user(
        email=f"{suffix}@example.com",
        password="pw1234",
        name=f"{suffix} name",
        nickname=suffix[:10],
        phone_number=f"010{_test_user_counter:08d}",
    )


class PostListCreateViewCreateTest(APITestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = create_test_user("author")
        self.category = PostCategory.objects.create(name="자유")
        self.url = reverse("post_list_create")

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

    def test_create_post_unauthenticated_unauthorized(self) -> None:
        payload = {
            "category": self.category.id,
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
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]["id"], self.newer_post.id)
        self.assertEqual(response.data[1]["id"], self.older_post.id)


class PostDetailViewPatchTest(APITestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.author = create_test_user("author")
        self.other = create_test_user("other")
        self.category = PostCategory.objects.create(name="자유")
        self.post = Post.objects.create(
            author=self.author,
            category=self.category,
            title="원본 제목",
            content="원본 내용",
        )
        self.url = reverse("post_detail", kwargs={"post_id": self.post.id})

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

    def test_update_post_unauthenticated_unauthorized(self) -> None:
        payload = {"title": "비로그인 수정"}

        response = self.client.patch(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, "원본 제목")

    def test_update_post_not_found(self) -> None:
        self.client.force_authenticate(user=self.author)
        url = reverse("post_detail", kwargs={"post_id": 99999})

        response = self.client.patch(url, {"title": "없는 글"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


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

    def test_get_post_detail_not_found(self) -> None:
        url = reverse("post_detail", kwargs={"post_id": 99999})

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


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

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
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
