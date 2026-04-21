from rest_framework import serializers

from apps.posts.models import Post


class PostCreateRequestSerializer(serializers.ModelSerializer[Post]):
    class Meta:
        model = Post
        fields = ["category", "title", "content", "is_visible"]


class PostUpdateRequestSerializer(serializers.ModelSerializer[Post]):
    class Meta:
        model = Post
        fields = ["category", "title", "content", "is_visible"]


class PostCUDResponseSerializer(serializers.ModelSerializer[Post]):
    class Meta:
        model = Post
        fields = [
            "id",
            "author",
            "category",
            "title",
            "content",
            "view_count",
            "is_visible",
            "is_notice",
            "created_at",
            "updated_at",
        ]
