from typing import Any

from rest_framework import serializers

from apps.qna.models.question_models import QuestionCategory, QuestionImage


class QuestionCreateSerializer(serializers.Serializer[Any]):
    title = serializers.CharField(max_length=50, allow_blank=False)
    content = serializers.CharField(allow_blank=False)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=QuestionCategory.objects.select_related("parent__parent").all(),
    )
    img_urls = serializers.ListField(
        child=serializers.URLField(),
        required=False,
        default=list,
    )

    def validate_category_id(self, value: QuestionCategory) -> QuestionCategory:
        if value.parent is None or value.parent.parent is None:
            raise serializers.ValidationError("소분류 카테고리만 선택할 수 있습니다.")
        return value


class QuestionCreateResponseSerializer(serializers.Serializer[Any]):
    message = serializers.CharField()
    question_id = serializers.IntegerField()


class QuestionListCategorySerializer(serializers.Serializer[Any]):
    id = serializers.IntegerField()
    depth = serializers.IntegerField()
    names = serializers.ListField(child=serializers.CharField())


class QuestionListAuthorSerializer(serializers.Serializer[Any]):
    id = serializers.IntegerField()
    nickname = serializers.CharField()
    profile_img_url = serializers.CharField(allow_null=True)
    course_name = serializers.CharField(allow_null=True)
    cohort_number = serializers.IntegerField(allow_null=True)


class QuestionListItemSerializer(serializers.Serializer[Any]):
    id = serializers.IntegerField()
    category = QuestionListCategorySerializer()
    author = QuestionListAuthorSerializer()
    title = serializers.CharField()
    content_preview = serializers.CharField()
    answer_count = serializers.IntegerField()
    view_count = serializers.IntegerField()
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    thumbnail_img_url = serializers.CharField(allow_null=True)
