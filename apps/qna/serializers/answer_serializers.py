from rest_framework import serializers

from apps.qna.models.answer_models import Answer


class AnswerRequestSerializer(serializers.Serializer[Answer]):
    content = serializers.CharField(required=True)
    img_urls = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list,
    )


class AnswerResponseSerializer(serializers.ModelSerializer[Answer]):
    answer_id = serializers.IntegerField(source="id")
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")

    class Meta:
        model = Answer
        fields = (
            "answer_id",
            "question_id",
            "author_id",
            "created_at",
        )
