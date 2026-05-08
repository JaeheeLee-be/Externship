from typing import Any

from rest_framework import serializers


class AdminQuestionListQuerySerializer(serializers.Serializer[Any]):
    page = serializers.IntegerField(required=False, default=1, min_value=1)
    page_size = serializers.IntegerField(required=False, default=20, min_value=1, max_value=100)
    search_keyword = serializers.CharField(required=False, allow_blank=True)
    category_id = serializers.IntegerField(required=False, allow_null=True)
    answer_status = serializers.ChoiceField(
        choices=["Y", "N"],
        required=False,
        allow_null=True,
    )
    sort = serializers.ChoiceField(
        choices=["latest", "oldest", "views"],
        required=False,
        default="latest",
    )


class AdminQuestionListItemSerializer(serializers.Serializer[Any]):
    question_id = serializers.IntegerField()
    title = serializers.CharField()
    category_path = serializers.CharField()
    content_preview = serializers.CharField()
    nickname = serializers.CharField()
    view_count = serializers.IntegerField()
    has_answer = serializers.BooleanField()
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    updated_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")


# ── 어드민 질문 삭제 ──────────────────────────────────────────────────


class AdminQuestionDeleteResponseSerializer(serializers.Serializer[Any]):
    """어드민 질문 삭제 응답"""

    question_id = serializers.IntegerField()
    deleted_answer_count = serializers.IntegerField()
    deleted_comment_count = serializers.IntegerField()

 #── 어드민 질문 상세 조회 ────────────────────────────────────────────


class AdminQuestionDetailAuthorSerializer(serializers.Serializer[Any]):
    """어드민 질문 상세 - 작성자 정보"""

    profile_img_url = serializers.CharField(allow_null=True)
    nickname = serializers.CharField()
    course_generation = serializers.CharField(allow_null=True)


class AdminQuestionDetailAnswerAuthorSerializer(serializers.Serializer[Any]):
    """어드민 질문 상세 - 답변 작성자 정보"""

    profile_img_url = serializers.CharField(allow_null=True)
    nickname = serializers.CharField()
    role_title = serializers.CharField(allow_null=True)
    course_generation = serializers.CharField(allow_null=True)


class AdminQuestionDetailAnswerSerializer(serializers.Serializer[Any]):
    """어드민 질문 상세 - 답변"""

    answer_id = serializers.IntegerField()
    author = AdminQuestionDetailAnswerAuthorSerializer()
    content = serializers.CharField()
    is_adopted = serializers.BooleanField()
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    updated_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")


class AdminQuestionDetailSerializer(serializers.Serializer[Any]):
    """어드민 질문 상세 조회 응답"""

    question_id = serializers.IntegerField()
    title = serializers.CharField()
    content = serializers.CharField()
    images = serializers.ListField(child=serializers.CharField())
    author = AdminQuestionDetailAuthorSerializer()
    view_count = serializers.IntegerField()
    has_answer = serializers.BooleanField()
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    updated_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    answers = AdminQuestionDetailAnswerSerializer(many=True)
