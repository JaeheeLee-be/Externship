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


# ── 질문 상세 조회 ──────────────────────────────────────────────────


class QuestionDetailImageSerializer(serializers.Serializer[Any]):
    """질문 이미지"""

    id = serializers.IntegerField()
    img_url = serializers.CharField()


class QuestionDetailAuthorSerializer(serializers.Serializer[Any]):
    """질문/답변 작성자 (간단)"""

    id = serializers.IntegerField()
    nickname = serializers.CharField()
    profile_img_url = serializers.CharField(allow_null=True)


class AnswerCommentAuthorSerializer(serializers.Serializer[Any]):
    """댓글 작성자 (course/cohort 포함)"""

    id = serializers.IntegerField()
    nickname = serializers.CharField()
    profile_img_url = serializers.CharField(allow_null=True)
    course_name = serializers.CharField(allow_null=True)
    cohort_number = serializers.IntegerField(allow_null=True)


class AnswerCommentSerializer(serializers.Serializer[Any]):
    """답변 댓글"""

    id = serializers.IntegerField()
    content = serializers.CharField()
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    author = AnswerCommentAuthorSerializer()


class QuestionDetailAnswerSerializer(serializers.Serializer[Any]):
    """답변 (댓글 포함)"""

    id = serializers.IntegerField()
    content = serializers.CharField()
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    is_adopted = serializers.BooleanField()
    author = QuestionDetailAuthorSerializer()
    comments = AnswerCommentSerializer(many=True)


class QuestionDetailSerializer(serializers.Serializer[Any]):
    """질문 상세 조회 응답"""

    id = serializers.IntegerField()
    title = serializers.CharField()
    content = serializers.CharField()
    category = QuestionListCategorySerializer()  # 목록과 같은 구조 재사용
    images = QuestionDetailImageSerializer(many=True)
    view_count = serializers.IntegerField()
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    author = QuestionDetailAuthorSerializer()
    answers = QuestionDetailAnswerSerializer(many=True)


class QuestionUpdateSerializer(serializers.Serializer[Any]):
    """질문 수정 요청 데이터"""

    title = serializers.CharField(max_length=50)
    content = serializers.CharField()
    category_id = serializers.IntegerField()
    img_urls = serializers.ListField(
        child=serializers.URLField(),
        required=False,
        default=list,
    )

    def validate_category_id(self, value: int) -> int:
        try:
            category = QuestionCategory.objects.select_related("parent__parent").get(id=value)
        except QuestionCategory.DoesNotExist:
            raise serializers.ValidationError("존재하지 않는 카테고리입니다.")

        # 소분류 = parent가 있고, 그 parent도 parent가 있는 것
        if category.parent is None or category.parent.parent is None:
            raise serializers.ValidationError("소분류 카테고리만 선택할 수 있습니다.")

        return value


class QuestionUpdateResponseSerializer(serializers.Serializer[Any]):
    """질문 수정 응답 데이터"""

    question_id = serializers.IntegerField()
    updated_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
