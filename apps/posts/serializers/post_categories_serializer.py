from rest_framework import serializers

from apps.posts.models import PostCategory


class PostCategoryListResponseSerializer(serializers.ModelSerializer[PostCategory]):
    class Meta:
        model = PostCategory
        fields = ["id", "name"]
