from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.core.utils.test_factories import create_test_user
from apps.posts.models import Post, PostCategory, PostComment, PostCommentTag
from apps.users.models import User


class CommentBaseTest(APITestCase):
    author: User
    other: User
    post: Post

    @classmethod
    def setUpTestData(cls) -> None:
        cls.author = create_test_user("author")
        cls.other = create_test_user("other")
        category = PostCategory.objects.create(name="자유")
        cls.post = Post.objects.create(
            author=cls.author,
            category=category,
            title="테스트 게시글",
            content="테스트 내용",
        )

    def setUp(self) -> None:
        self.client = APIClient()


class CommentListCreateViewGetTest(CommentBaseTest):
    url: str

    @classmethod
    def setUpTestData(cls) -> None:
        super().setUpTestData()
        cls.url = reverse("comment_list_create", kwargs={"post_id": cls.post.id})
        for i in range(1, 16):
            PostComment.objects.create(author=cls.author, post=cls.post, content=f"댓글{i}")

    def test_get_comments_success(self) -> None:
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 15)
        self.assertIn("next", response.data)
        self.assertIn("previous", response.data)
        self.assertEqual(len(response.data["results"]), 10)

    def test_get_comments_post_not_found(self) -> None:
        url = reverse("comment_list_create", kwargs={"post_id": 99999})

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error_detail"], "해당 게시글을 찾을 수 없습니다.")

    def test_get_comments_pagination(self) -> None:
        response = self.client.get(self.url, {"page": 1, "page_size": 10})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 15)
        self.assertEqual(len(response.data["results"]), 10)
        self.assertIsNotNone(response.data["next"])
        self.assertIsNone(response.data["previous"])

    def test_get_comments_unauthenticated_success(self) -> None:
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)


class CommentListCreateViewGetEmptyTest(CommentBaseTest):
    url: str

    @classmethod
    def setUpTestData(cls) -> None:
        super().setUpTestData()
        cls.url = reverse("comment_list_create", kwargs={"post_id": cls.post.id})

    def test_get_comments_empty(self) -> None:
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 0)
        self.assertEqual(len(response.data["results"]), 0)


class CommentListCreateViewPostTest(CommentBaseTest):
    url: str

    @classmethod
    def setUpTestData(cls) -> None:
        super().setUpTestData()
        cls.url = reverse("comment_list_create", kwargs={"post_id": cls.post.id})

    def test_create_comment_success(self) -> None:
        self.client.force_authenticate(user=self.author)
        payload = {"content": "테스트 댓글"}

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["detail"], "댓글이 등록되었습니다.")
        comment = PostComment.objects.filter(post=self.post).first()
        assert comment is not None
        self.assertEqual(comment.author, self.author)
        self.assertEqual(comment.content, "테스트 댓글")

    def test_create_comment_with_tag_success(self) -> None:
        self.client.force_authenticate(user=self.author)
        tagged_user = create_test_user("tagged")
        payload = {
            "content": f"@{tagged_user.nickname} 태그 테스트",
            "tagged_user_ids": [tagged_user.id],
        }

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        tag = PostCommentTag.objects.filter(tagged_user=tagged_user).first()
        assert tag is not None
        self.assertEqual(tag.tagged_user, tagged_user)

    def test_create_comment_missing_content(self) -> None:
        self.client.force_authenticate(user=self.author)
        payload: dict[str, object] = {}

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error_detail", response.data)
        self.assertIn("content", response.data["error_detail"])

    def test_create_comment_blank_content(self) -> None:
        self.client.force_authenticate(user=self.author)
        payload = {"content": "  "}

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error_detail", response.data)

    def test_create_comment_unauthenticated_unauthorized(self) -> None:
        payload = {"content": "테스트 댓글"}

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_comment_post_not_found(self) -> None:
        self.client.force_authenticate(user=self.author)
        url = reverse("comment_list_create", kwargs={"post_id": 99999})
        payload = {"content": "테스트 댓글"}

        response = self.client.post(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error_detail"], "해당 게시글을 찾을 수 없습니다.")


class CommentDetailViewDeleteTest(CommentBaseTest):
    comment: PostComment
    url: str

    def setUp(self) -> None:
        super().setUp()
        self.comment = PostComment.objects.create(
            author=self.author,
            post=self.post,
            content="삭제될 댓글",
        )
        self.url = reverse("comment_detail", kwargs={"post_id": self.post.id, "comment_id": self.comment.id})

    def test_delete_comment_success(self) -> None:
        self.client.force_authenticate(user=self.author)

        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["detail"], "댓글이 삭제되었습니다.")
        self.assertFalse(PostComment.objects.filter(id=self.comment.id).exists())

    def test_delete_comment_not_author_forbidden(self) -> None:
        self.client.force_authenticate(user=self.other)

        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data["error_detail"], "권한이 없습니다.")
        self.assertTrue(PostComment.objects.filter(id=self.comment.id).exists())

    def test_delete_comment_unauthenticated_unauthorized(self) -> None:
        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertTrue(PostComment.objects.filter(id=self.comment.id).exists())

    def test_delete_comment_not_found(self) -> None:
        self.client.force_authenticate(user=self.author)
        url = reverse("comment_detail", kwargs={"post_id": self.post.id, "comment_id": 99999})

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error_detail"], "해당 댓글을 찾을 수 없습니다.")
