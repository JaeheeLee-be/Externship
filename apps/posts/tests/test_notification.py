from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.core.utils.test_factories import create_test_user
from apps.posts.models import Notification, Post, PostCategory, PostComment
from apps.posts.services.notification_service import create_notification
from apps.users.models import User


class NotificationBaseTest(APITestCase):
    author: User
    commenter: User
    other_commenter: User
    post: Post

    @classmethod
    def setUpTestData(cls) -> None:
        cls.author = create_test_user("author")
        cls.commenter = create_test_user("commenter")
        cls.other_commenter = create_test_user("other")
        category = PostCategory.objects.create(name="자유")
        cls.post = Post.objects.create(
            author=cls.author,
            category=category,
            title="테스트 게시글",
            content="테스트 내용",
        )

    def _make_comment(self, author: User, content: str = "댓글") -> PostComment:
        return PostComment.objects.create(author=author, post=self.post, content=content)

    def _make_notification(
        self, recipient: User, sender: User, comment: PostComment, *, is_read: bool = False
    ) -> Notification:
        return Notification.objects.create(
            recipient=recipient,
            sender=sender,
            post=self.post,
            comment=comment,
            is_read=is_read,
        )

    def setUp(self) -> None:
        self.client = APIClient()
        self.url = reverse("post_notifications")


class CreateNotificationTest(NotificationBaseTest):

    def test_commenter_notifies_post_author(self) -> None:
        comment = self._make_comment(self.commenter)

        create_notification(sender=self.commenter, post=self.post, comment=comment)

        self.assertTrue(Notification.objects.filter(recipient=self.author, sender=self.commenter).exists())

    def test_author_self_comment_no_notification(self) -> None:
        comment = self._make_comment(self.author, content="내 글에 내가 댓글")

        create_notification(sender=self.author, post=self.post, comment=comment)

        self.assertFalse(Notification.objects.filter(post=self.post).exists())

    def test_new_commenter_notifies_existing_commenter(self) -> None:
        self._make_comment(self.other_commenter, content="기존 댓글")
        comment = self._make_comment(self.commenter, content="새 댓글")

        create_notification(sender=self.commenter, post=self.post, comment=comment)

        self.assertTrue(Notification.objects.filter(recipient=self.other_commenter, sender=self.commenter).exists())

    def test_sender_does_not_receive_own_notification(self) -> None:
        comment = self._make_comment(self.commenter)

        create_notification(sender=self.commenter, post=self.post, comment=comment)

        self.assertFalse(Notification.objects.filter(recipient=self.commenter).exists())

    def test_duplicate_commenter_notified_once(self) -> None:

        self._make_comment(self.other_commenter, content="댓글1")
        self._make_comment(self.other_commenter, content="댓글2")
        comment = self._make_comment(self.commenter, content="새 댓글")

        create_notification(sender=self.commenter, post=self.post, comment=comment)

        count = Notification.objects.filter(recipient=self.other_commenter, sender=self.commenter).count()
        self.assertEqual(count, 1)


class NotificationGetTest(NotificationBaseTest):

    def test_get_notifications_unauthenticated_returns_401(self) -> None:
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_notifications_empty(self) -> None:
        self.client.force_authenticate(user=self.author)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["unread_count"], 0)
        self.assertEqual(len(response.data["results"]), 0)

    def test_get_notifications_returns_unread_count(self) -> None:
        comment = self._make_comment(self.commenter)
        self._make_notification(self.author, self.commenter, comment, is_read=False)

        self.client.force_authenticate(user=self.author)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["unread_count"], 1)
        self.assertEqual(len(response.data["results"]), 1)

    def test_get_notifications_only_own(self) -> None:

        comment = self._make_comment(self.commenter)
        self._make_notification(self.other_commenter, self.commenter, comment)

        self.client.force_authenticate(user=self.author)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 0)

    def test_get_notifications_read_not_counted_as_unread(self) -> None:
        comment = self._make_comment(self.commenter)
        self._make_notification(self.author, self.commenter, comment, is_read=True)

        self.client.force_authenticate(user=self.author)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["unread_count"], 0)
        self.assertEqual(len(response.data["results"]), 1)


class NotificationMarkReadTest(NotificationBaseTest):

    def setUp(self) -> None:
        super().setUp()
        comment = self._make_comment(self.commenter)
        self.notification = self._make_notification(self.author, self.commenter, comment)

    def test_mark_read_unauthenticated_returns_401(self) -> None:
        response = self.client.patch(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_mark_all_read_success(self) -> None:
        self.client.force_authenticate(user=self.author)

        response = self.client.patch(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.notification.refresh_from_db()
        self.assertTrue(self.notification.is_read)

    def test_mark_all_read_unread_count_becomes_zero(self) -> None:
        self.client.force_authenticate(user=self.author)
        self.client.patch(self.url)

        response = self.client.get(self.url)

        self.assertEqual(response.data["unread_count"], 0)

    def test_mark_read_does_not_affect_other_users(self) -> None:
        comment2 = self._make_comment(self.author, content="댓글2")
        other_notification = self._make_notification(self.other_commenter, self.author, comment2)

        self.client.force_authenticate(user=self.author)

        self.client.patch(self.url)

        other_notification.refresh_from_db()
        self.assertFalse(other_notification.is_read)
