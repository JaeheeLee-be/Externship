import json
from typing import Any, Dict

from rest_framework import serializers

from apps.exams.models.exam_question_model import ExamQuestion


class QuestionValidateMixin:
    def validate_correct_answer(self, correct_answer: Dict[str, Any]) -> Dict[str, Any]:
        if not correct_answer:
            raise serializers.ValidationError()
        return correct_answer


class ExamQuestionSwaggerSerializer(serializers.ModelSerializer[ExamQuestion]):
    options = serializers.JSONField(source="options_json")
    correct_answer = serializers.JSONField(source="answer")
    explanation = serializers.CharField(required=False, default="")

    class Meta:
        model = ExamQuestion
        fields = [
            "type",
            "question",
            "prompt",
            "options",
            "blank_count",
            "correct_answer",
            "point",
            "explanation",
        ]


class BlankRequestSerializer(QuestionValidateMixin, serializers.ModelSerializer[ExamQuestion]):
    correct_answer = serializers.JSONField(source="answer", required=True, allow_null=False)
    explanation = serializers.CharField(required=False, allow_null=True, allow_blank=True, default="")

    class Meta:
        model = ExamQuestion
        fields = [
            "question",
            "prompt",
            "blank_count",
            "correct_answer",
            "point",
            "type",
            "explanation",
        ]
        extra_kwargs = {
            "question": {"required": True, "allow_blank": False},
            "prompt": {"required": True, "allow_blank": False},
            "blank_count": {"required": True, "allow_null": False},
            "point": {"required": True, "allow_null": False},
            "type": {"required": True, "allow_blank": False, "allow_null": False},
        }


class OrderRequestSerializer(QuestionValidateMixin, serializers.ModelSerializer[ExamQuestion]):
    options = serializers.JSONField(required=True, allow_null=False)
    correct_answer = serializers.JSONField(source="answer", required=True, allow_null=False)
    explanation = serializers.CharField(required=False, allow_null=True, allow_blank=True, default="")

    class Meta:
        model = ExamQuestion
        fields = ["question", "options", "correct_answer", "point", "type", "explanation"]
        extra_kwargs = {
            "question": {"required": True, "allow_blank": False},
            "point": {"required": True, "allow_null": False},
            "type": {"required": True, "allow_blank": False, "allow_null": False},
        }


class MulAndSingleRequestSerializer(QuestionValidateMixin, serializers.ModelSerializer[ExamQuestion]):
    options = serializers.JSONField(required=True, allow_null=False)
    correct_answer = serializers.JSONField(required=True, allow_null=False)
    explanation = serializers.CharField(required=False, allow_null=True, allow_blank=True, default="")

    class Meta:
        model = ExamQuestion
        fields = ["question", "options", "correct_answer", "point", "type", "explanation"]
        extra_kwargs = {
            "question": {"required": True, "allow_blank": False},
            "point": {"required": True, "allow_null": False},
            "type": {"required": True, "allow_blank": False, "allow_null": False},
        }


class OXAndShortRequestSerializer(QuestionValidateMixin, serializers.ModelSerializer[ExamQuestion]):
    correct_answer = serializers.JSONField(required=True)
    explanation = serializers.CharField(required=False, allow_null=True, allow_blank=True, default="")

    class Meta:
        model = ExamQuestion
        fields = ["question", "correct_answer", "point", "type", "explanation"]
        extra_kwargs = {
            "question": {"required": True, "allow_blank": False},
            "point": {"required": True, "allow_null": False},
            "type": {"required": True, "allow_blank": False, "allow_null": False},
        }


class QuestionUpdateSerializer(QuestionValidateMixin, serializers.ModelSerializer[ExamQuestion]):
    options = serializers.JSONField(required=False)
    correct_answer = serializers.JSONField(source="answer", required=False)

    class Meta:
        model = ExamQuestion
        fields = [
            "type",
            "question",
            "prompt",
            "options",
            "blank_count",
            "correct_answer",
            "point",
            "explanation",
        ]
        extra_kwargs = {field: {"required": False} for field in fields}


class QuestionDeleteResponseSerializer(serializers.Serializer[Dict[str, int]]):
    question_id = serializers.IntegerField()
    exam_id = serializers.IntegerField()


class QuestionResponseSerializer(serializers.ModelSerializer[ExamQuestion]):
    options = serializers.SerializerMethodField()
    correct_answer = serializers.JSONField(source="answer")

    class Meta:
        model = ExamQuestion
        fields = ["type", "question", "prompt", "options", "blank_count", "correct_answer", "point", "explanation"]

    def get_options(self, obj: ExamQuestion) -> Any:
        if obj.options_json:
            return json.loads(obj.options_json)
        return None


class QuestionUpdateResponseSerializer(QuestionResponseSerializer):
    question_id = serializers.IntegerField(source="id")

    class Meta(QuestionResponseSerializer.Meta):
        fields = ["question_id"] + QuestionResponseSerializer.Meta.fields


class QuestionCreateResponseSerializer(QuestionResponseSerializer):
    class Meta(QuestionResponseSerializer.Meta):
        fields = ["exam_id"] + QuestionResponseSerializer.Meta.fields
