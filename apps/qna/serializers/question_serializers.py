from typing import Any

from rest_framework import serializers

from apps.qna.models.question_models import QuestionCategory, QuestionImage


class QuestionCreateSerializer(serializers.Serializer[Any]):
    title = serializers.CharField(max_length=50)
    content = serializers.CharField()
    category_id = serializers.IntegerField()
    img_urls = serializers.ListField(
        child=serializers.URLField(),
        required=False,
        default=list,
    )

    def validate_category_id(self, value: int) -> int:
        if not QuestionCategory.objects.filter(id=value).exists():
            raise serializers.ValidationError("존재하지 않는 카테고리입니다.")
        return value


class QuestionCreateResponseSerializer(serializers.Serializer[Any]):
    message = serializers.CharField()
    question_id = serializers.IntegerField()
