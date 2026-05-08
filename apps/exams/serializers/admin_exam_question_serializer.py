import json
from typing import Any, Dict

from rest_framework import serializers

from apps.exams.models.exam_question_model import ExamQuestion


class ExamQuestionSwaggerSerializer(serializers.ModelSerializer[ExamQuestion]):
    options = serializers.JSONField(source="options_json")
    correct_answer = serializers.JSONField(source="answer")

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


class BlankRequestSerializer(serializers.ModelSerializer[ExamQuestion]):
    correct_answer = serializers.JSONField(source="answer")

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
            "question": {"required": True},
            "prompt": {"required": True},
            "blank_count": {"required": True},
            "point": {"required": True},
            "type": {"required": True},
        }


class OrderRequestSerializer(serializers.ModelSerializer[ExamQuestion]):
    options = serializers.JSONField(source="options_json")
    correct_answer = serializers.JSONField(source="answer")

    class Meta:
        model = ExamQuestion
        fields = ["question", "options", "correct_answer", "point", "type", "explanation"]
        extra_kwargs = {"question": {"required": True}, "point": {"required": True}, "type": {"required": True}}


class MulAndSingleRequestSerializer(serializers.ModelSerializer[ExamQuestion]):
    options = serializers.JSONField(required=True)
    correct_answer = serializers.JSONField(required=True)

    class Meta:
        model = ExamQuestion
        fields = ["question", "options", "correct_answer", "point", "type", "explanation"]
        extra_kwargs = {"question": {"required": True}, "point": {"required": True}, "type": {"required": True}}


class OXAndShortRequestSerializer(serializers.ModelSerializer[ExamQuestion]):
    correct_answer = serializers.JSONField(required=True)

    class Meta:
        model = ExamQuestion
        fields = ["question", "correct_answer", "point", "type", "explanation"]
        extra_kwargs = {"question": {"required": True}, "point": {"required": True}, "type": {"required": True}}


class QuestionUpdateSerializer(serializers.ModelSerializer[ExamQuestion]):
    options = serializers.JSONField(source="options_json", required=False)
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
