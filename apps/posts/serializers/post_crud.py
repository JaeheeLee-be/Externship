from typing import Any

from rest_framework import serializers

from apps.posts.models import Post, PostCategory
from apps.users.models import User


class PostCreateRequestSerializer(serializers.ModelSerializer[Post]):
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=PostCategory.objects.all(),
        source="category",
    )

    class Meta:
        model = Post
        fields = ["title", "content", "category_id"]


class PostUpdateRequestSerializer(serializers.ModelSerializer[Post]):
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=PostCategory.objects.all(),
        source="category",
    )

    class Meta:
        model = Post
        fields = ["title", "content", "category_id"]


class PostCreateResponseSerializer(serializers.Serializer[Post]):
    detail = serializers.CharField()
    pk = serializers.IntegerField()


class PostUpdateResponseSerializer(serializers.ModelSerializer[Post]):
    class Meta:
        model = Post
        fields = ["id", "title", "content", "category_id"]


class PostDeleteResponseSerializer(serializers.Serializer[Post]):
    detail = serializers.CharField()


class ErrorResponseSerializer(serializers.Serializer[dict[str, Any]]):
    error_detail = serializers.CharField()


class ValidationErrorResponseSerializer(serializers.Serializer[dict[str, Any]]):
    error_detail = serializers.DictField()


class AuthorSerializer(serializers.ModelSerializer[User]):
    class Meta:
        model = User
        fields = ["id", "nickname", "profile_img_url"]


class CategoryInPostSerializer(serializers.ModelSerializer[PostCategory]):
    class Meta:
        model = PostCategory
        fields = ["id", "name"]


class PostDetailResponseSerializer(serializers.ModelSerializer[Post]):
    author = AuthorSerializer(read_only=True)
    category = CategoryInPostSerializer(read_only=True)
    thumbnail_img_url = serializers.SerializerMethodField()
    like_count = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            "id",
            "title",
            "content",
            "thumbnail_img_url",
            "author",
            "category",
            "view_count",
            "like_count",
            "comment_count",
            "created_at",
            "updated_at",
        ]

    def get_thumbnail_img_url(self, obj: Post) -> str | None:
        return None

    def get_like_count(self, obj: Post) -> int:
        return 0

    def get_comment_count(self, obj: Post) -> int:
        return 0
