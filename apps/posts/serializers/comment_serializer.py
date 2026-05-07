from typing import Any

from rest_framework import serializers

from apps.posts.models.comment import PostComment


class CommentAuthorSerializer(serializers.Serializer[Any]):
    id = serializers.IntegerField()
    nickname = serializers.CharField()
    profile_img_url = serializers.CharField(allow_null=True)


class TaggedUserSerializer(serializers.Serializer[Any]):
    id = serializers.IntegerField()
    nickname = serializers.CharField()


class PostCommentSerializer(serializers.ModelSerializer[PostComment]):
    author = CommentAuthorSerializer(read_only=True)
    tagged_users = serializers.SerializerMethodField()

    class Meta:
        model = PostComment
        fields = ["id", "author", "tagged_users", "content", "created_at"]

    def get_tagged_users(self, obj: PostComment) -> Any:
        tags = obj.tags.all()
        return TaggedUserSerializer([tag.tagged_user for tag in tags], many=True).data


class CommentCreateSerializer(serializers.ModelSerializer[PostComment]):
    tagged_user_ids = serializers.ListField(
        child=serializers.IntegerField(), required=False, default=list, write_only=True
    )

    class Meta:
        model = PostComment
        fields = ["content", "tagged_user_ids"]

    def validate_content(self, value: str) -> str:
        if not value.strip():
            raise serializers.ValidationError("댓글 내용을 입력해주세요.")
        return value


class CommentQuerySerializer(serializers.Serializer[Any]):
    page = serializers.IntegerField(required=False, default=1, min_value=1)
    page_size = serializers.IntegerField(required=False, default=10, min_value=1)
