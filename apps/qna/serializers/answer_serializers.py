from rest_framework import serializers

from apps.qna.models.answer_models import Answer, AnswerComment


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


class AnswerAcceptResponseSerializer(serializers.ModelSerializer[Answer]):
    """답변 채택 응답 serializer"""

    answer_id = serializers.IntegerField(source="id")

    class Meta:
        model = Answer
        fields = (
            "answer_id",
            "question_id",
            "is_adopted",
        )


class AnswerUpdateSerializer(serializers.ModelSerializer[Answer]):
    """답변 수정 했을떄 응답 serializer"""

    answer_id = serializers.IntegerField(source="id")
    updated_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")

    class Meta:
        model = Answer
        fields = (
            "answer_id",
            "updated_at",
        )


class AnswerCommentRequestSerializer(serializers.Serializer[AnswerComment]):
    """
    답변 댓글 작성 요청 serializer
    """

    content = serializers.CharField(
        required=True,
        min_length=1,
        max_length=500,
        error_messages={
            "min_length": "댓글 내용은 1자 이상 입력해야 합니다.",
            "max_length": "댓글 내용은 500자 이하로 입력해야 합니다.",
        },
    )


class AnswerCommentResponseSerializer(serializers.ModelSerializer[AnswerComment]):
    """
    답변 댓글 작성 응답 serializer
    """

    comment_id = serializers.IntegerField(source="id")
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")

    class Meta:
        model = AnswerComment
        fields = [
            "comment_id",
            "answer_id",
            "author_id",
            "created_at",
        ]
