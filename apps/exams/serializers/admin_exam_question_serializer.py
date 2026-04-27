from typing import Any

from rest_framework import serializers

from apps.exams.models.exam_question_model import ExamQuestion


class PointValidateMixin:
    def validate_point(self, value: Any) -> Any:
        if value <= 0:
            raise serializers.ValidationError("배점은 0보다 작거나 같을 수 없습니다.")
        return value


class QuestionCreateSerializer(PointValidateMixin, serializers.ModelSerializer[ExamQuestion]):
    class Meta:
        model = ExamQuestion
        fields = ["question", "type", "prompt", "blank_count", "options_json", "answer", "point", "explanation"]


class QuestionUpdateSerializer(PointValidateMixin, serializers.ModelSerializer[ExamQuestion]):
    question = serializers.CharField(required=False)
    type = serializers.CharField(required=False)
    prompt = serializers.CharField(required=False)
    blank_count = serializers.IntegerField(required=False)
    options_json = serializers.CharField(required=False)
    answer = serializers.JSONField(required=False)
    point = serializers.IntegerField(required=False)
    explanation = serializers.CharField(required=False)

    class Meta:
        model = ExamQuestion
        fields = [
            "question",
            "type",
            "prompt",
            "blank_count",
            "options_json",
            "answer",
            "point",
            "explanation",
        ]


class QuestionDeleteResponseSerializer(serializers.ModelSerializer[ExamQuestion]):
    class Meta:
        model = ExamQuestion
        fields = [
            "id",
            "exam_id",
        ]
        read_only_fields = ["id", "exam_id"]


class QuestionResponseSerializer(serializers.ModelSerializer[ExamQuestion]):
    class Meta:
        model = ExamQuestion
        fields = ["question", "type", "prompt", "blank_count", "options_json", "answer", "point", "explanation"]


class QuestionUpdateResponseSerializer(QuestionResponseSerializer):
    class Meta(QuestionResponseSerializer.Meta):
        fields = ["id"] + QuestionResponseSerializer.Meta.fields


class QuestionCreateResponseSerializer(QuestionResponseSerializer):
    class Meta(QuestionResponseSerializer.Meta):
        fields = ["exam_id"] + QuestionResponseSerializer.Meta.fields
