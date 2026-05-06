import json
from typing import Any, Dict

from rest_framework import serializers

from apps.exams.models.exam_question_model import ExamQuestion


class QuestionCreateSerializer(serializers.ModelSerializer[ExamQuestion]):
    options = serializers.JSONField(source="options_json", required=False)
    correct_answer = serializers.JSONField(source="answer")

    class Meta:
        model = ExamQuestion
        fields = ["type", "question", "prompt", "options", "blank_count", "correct_answer", "point", "explanation"]


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
