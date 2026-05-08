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
