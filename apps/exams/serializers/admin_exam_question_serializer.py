from rest_framework import serializers

from apps.exams.models.exam_question_model import ExamQuestion


class QuestionSerializer(serializers.ModelSerializer[ExamQuestion]):
    class Meta:
        model = ExamQuestion
        fields = [
            "id",
            "exam",
            "type",
            "question",
            "prompt",
            "options_json",
            "blank_count",
            "answer",
            "point",
            "explanation",
        ]

    def validate_point(self, value: int) -> int:
        if value < 0:
            raise serializers.ValidationError("배점은 양수여야 합니다.")
        return value


class BlankSerializer(QuestionSerializer):
    class Meta:
        model = ExamQuestion
        fields = [
            "id",
            "exam",
            "type",
            "question",
            "prompt",
            "blank_count",
            "answer",
            "point",
            "explanation",
        ]
        read_only_fields = ("id", "exam")
        extra_kwargs = {
            "prompt": {"required": True},
            "blank_count": {"required": True},
        }


class ChoiceAndSortSerializer(QuestionSerializer):
    class Meta:
        model = ExamQuestion
        fields = ["id", "exam", "type", "question", "options_json", "answer", "point", "explanation"]
        read_only_fields = ("id", "exam")
        extra_kwargs = {
            "options_json": {"required": True, "description": "지문은 필수 입니다."},
        }


class WordAndQuizSerializer(QuestionSerializer):
    class Meta:
        model = ExamQuestion
        fields = ["id", "exam", "type", "question", "answer", "point", "explanation"]
        read_only_fields = ("id", "exam")
