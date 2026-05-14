from django.db import IntegrityError, transaction
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.core.utils.test_factories import create_test_user
from apps.posts.models import Like, Post, PostCategory


class PostLikeBaseTestCase(APITestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.author = create_test_user("author")
        self.liker = create_test_user("liker")
        self.category = PostCategory.objects.create(name="test-category")
        self.post = Post.objects.create(
            author=self.author,
            category=self.category,
            title="post like test title",
            content="post like test content",
        )
        kwargs = {"post_id": self.post.id}
        self.create_url = reverse("post-like-create", kwargs=kwargs)
        self.cancel_url = reverse("post-like-cancel", kwargs=kwargs)


class PostLikeViewUnauthenticatedTest(PostLikeBaseTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.expected_error = {
            "error_detail": "자격 인증 데이터가 제공되지 않았습니다.",
        }

    def test_create_like_unauthenticated_returns_401(self) -> None:
        response = self.client.post(self.create_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data, self.expected_error)

    def test_cancel_like_unauthenticated_returns_401(self) -> None:
        response = self.client.delete(self.cancel_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data, self.expected_error)


class PostLikeCreateTest(PostLikeBaseTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.client.force_authenticate(user=self.liker)

    def test_create_like_success(self) -> None:
        response = self.client.post(self.create_url)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["is_liked"], True)
        self.assertEqual(response.data["like_count"], 1)
        like = Like.objects.get(user=self.liker, post=self.post)
        self.assertTrue(like.is_liked)

    def test_create_like_already_liked_returns_409(self) -> None:
        Like.objects.create(user=self.liker, post=self.post, is_liked=True)

        response = self.client.post(self.create_url)

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.data, {"error_detail": "이미 좋아요를 누른 게시글입니다."})
        self.assertEqual(Like.objects.filter(user=self.liker, post=self.post).count(), 1)

    def test_create_like_reactivates_canceled_like(self) -> None:
        like = Like.objects.create(user=self.liker, post=self.post, is_liked=False)

        response = self.client.post(self.create_url)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["is_liked"], True)
        self.assertEqual(response.data["like_count"], 1)
        like.refresh_from_db()
        self.assertTrue(like.is_liked)
        self.assertEqual(Like.objects.filter(user=self.liker, post=self.post).count(), 1)

    def test_create_like_post_not_found_returns_404(self) -> None:
        url = reverse("post-like-create", kwargs={"post_id": 99999})

        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, {"error_detail": "해당 게시글을 찾을 수 없습니다."})
        self.assertFalse(Like.objects.filter(user=self.liker).exists())

    def test_create_like_hidden_post_returns_404(self) -> None:
        self.post.is_visible = False
        self.post.save(update_fields=["is_visible", "updated_at"])

        response = self.client.post(self.create_url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, {"error_detail": "해당 게시글을 찾을 수 없습니다."})
        self.assertFalse(Like.objects.filter(user=self.liker, post=self.post).exists())


class PostLikeCancelTest(PostLikeBaseTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.client.force_authenticate(user=self.liker)

    def test_cancel_like_success(self) -> None:
        like = Like.objects.create(user=self.liker, post=self.post, is_liked=True)

        response = self.client.delete(self.cancel_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["is_liked"], False)
        self.assertEqual(response.data["like_count"], 0)
        like.refresh_from_db()
        self.assertFalse(like.is_liked)

    def test_cancel_like_without_like_returns_404(self) -> None:
        response = self.client.delete(self.cancel_url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, {"error_detail": "좋아요 기록을 찾을 수 없습니다."})
        self.assertFalse(Like.objects.filter(user=self.liker, post=self.post).exists())

    def test_cancel_like_already_canceled_returns_404(self) -> None:
        like = Like.objects.create(user=self.liker, post=self.post, is_liked=False)

        response = self.client.delete(self.cancel_url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, {"error_detail": "좋아요 기록을 찾을 수 없습니다."})
        like.refresh_from_db()
        self.assertFalse(like.is_liked)

    def test_cancel_like_post_not_found_returns_404(self) -> None:
        url = reverse("post-like-cancel", kwargs={"post_id": 99999})

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, {"error_detail": "해당 게시글을 찾을 수 없습니다."})

    def test_cancel_like_hidden_post_returns_404_and_keeps_like_active(self) -> None:
        like = Like.objects.create(user=self.liker, post=self.post, is_liked=True)
        self.post.is_visible = False
        self.post.save(update_fields=["is_visible", "updated_at"])

        response = self.client.delete(self.cancel_url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, {"error_detail": "해당 게시글을 찾을 수 없습니다."})
        like.refresh_from_db()
        self.assertTrue(like.is_liked)


class PostLikeModelTest(PostLikeBaseTestCase):
    def test_user_post_like_unique_constraint(self) -> None:
        Like.objects.create(user=self.liker, post=self.post, is_liked=True)

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Like.objects.create(user=self.liker, post=self.post, is_liked=True)
