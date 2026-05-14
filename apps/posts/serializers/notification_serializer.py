from rest_framework import serializers

from apps.posts.models.notification import Notification


class NotificationSerializer(serializers.ModelSerializer[Notification]):
    sender_nickname = serializers.CharField(source="sender.nickname", read_only=True)
    post_title = serializers.CharField(source="post.title", read_only=True)

    class Meta:
        model = Notification
        fields = (
            "id",
            "sender_nickname",
            "post_title",
            "comment_id",
            "is_read",
            "created_at",
        )