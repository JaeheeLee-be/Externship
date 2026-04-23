from rest_framework import serializers

from apps.qna.models.answer_models import Answer


class AnswerRequestSerializer(serializers.Serializer[Answer]):
    """답변 생성/수정 요청 데이터 serializer"""

    content = serializers.CharField(required=True)
    img_urls = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list,
    )


class AnswerResponseSerializer(serializers.ModelSerializer[Answer]):
    """테이터 응답에 대한 serializer"""

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


<<<<<<< HEAD
class AnswerAcceptResponseSerializer(serializers.ModelSerializer[Answer]):
    """답변 채택 응답 serializer"""

    answer_id = serializers.IntegerField(source="id")
=======
class AnswerUpdateSerializer(serializers.ModelSerializer[Answer]):
    """답변 수정 했을떄 응답 serializer"""

    answer_id = serializers.IntegerField(source="id")
    updated_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
>>>>>>> 6809492 (feat:답변 수정 기능구현 및 테스트 코드 작성)

    class Meta:
        model = Answer
        fields = (
            "answer_id",
<<<<<<< HEAD
            "question_id",
            "is_adopted",
=======
            "updated_at",
>>>>>>> 6809492 (feat:답변 수정 기능구현 및 테스트 코드 작성)
        )
